"""Main loop: interleaved (run, condition, scene) jobs, repair loop, logging, resume, budget guard.

python -m harness.run --runs 3 [--scenes 1,12,21,23] [--conditions opus_bare,haiku_harness]
                      [--include-groq] [--concurrency 4] [--yes]
"""
import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import threading
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from . import config, llm
from .blender_runner import run_blender
from .extract import extract_code, safety_check


def first_line(text, limit=300):
    if not text:
        return None
    lines = str(text).strip().splitlines()
    return lines[0][:limit] if lines else None


def last_lines(text, n=config.TRACEBACK_LINES):
    return "\n".join(str(text).rstrip().splitlines()[-n:])


def read_rows(log_path: Path) -> list:
    if not log_path.exists():
        return []
    rows = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


class Experiment:
    def __init__(self, results_dir: Path, budget: llm.Budget, call_model=llm.call_model):
        self.results_dir = Path(results_dir)
        self.log_path = self.results_dir / "runs.jsonl"
        self.scripts_dir = self.results_dir / "scripts"
        self.renders_dir = self.results_dir / "renders"
        self.budget = budget
        self.call_model = call_model
        self.stop = threading.Event()
        self.halt_reason = None
        self._log_lock = threading.Lock()

    def halt(self, reason: str) -> bool:
        """Stop all workers. Returns True only for the call that actually triggered the stop."""
        with self._log_lock:
            if self.stop.is_set():
                return False
            self.halt_reason = reason
            self.stop.set()
        print(f"\n*** stopping: {reason}\n    finished combos are logged; rerun the same command to resume.", flush=True)
        return True

    def log(self, row: dict) -> None:
        with self._log_lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a") as f:
                f.write(json.dumps(row) + "\n")

    def run_combo(self, run: int, cond: config.Condition, scene: dict, prior: list) -> None:
        try:
            self._run_combo(run, cond, scene, prior)
        except Exception as exc:  # non-retryable API error, auth error, bug: stop everything cleanly
            if self.halt(f"{type(exc).__name__} in run {run} {cond.id} scene {scene['id']}: {exc}"):
                traceback.print_exc()  # once, from the worker that stopped the run

    def _run_combo(self, run, cond, scene, prior):
        sid, category, prompt = scene["id"], scene["category"], scene["prompt"]
        system = config.system_prompt(cond.harness)
        out_dir = self.scripts_dir / str(run) / cond.id
        out_dir.mkdir(parents=True, exist_ok=True)

        start, prev_script, prev_error = 1, "", ""
        if prior:  # resume a combo that was interrupted between repair attempts
            last = prior[-1]["attempt"]
            start = last + 1
            stem = out_dir / f"{sid}_a{last}"
            for candidate in (stem.with_suffix(".py"), Path(f"{stem}.partial.py")):
                if candidate.exists():
                    prev_script = candidate.read_text()
                    break
            err_file = Path(f"{stem}.error.txt")
            prev_error = err_file.read_text() if err_file.exists() else (prior[-1].get("error_message") or "")

        for attempt in range(start, cond.max_attempts + 1):
            if self.stop.is_set():
                return
            user = (config.task_message(prompt) if attempt == 1
                    else config.repair_message(prompt, prev_script.rstrip(), prev_error))
            try:
                resp = self.call_model(cond.model, system, user, self.budget)
            except llm.BudgetExceeded as exc:
                self.halt(f"budget guard: {exc}")
                return

            stem = out_dir / f"{sid}_a{attempt}"
            extracted = extract_code(resp.text)
            code, partial = extracted.code, extracted.partial
            passed, blender_time, render, render_error, error_type, error_message = False, 0.0, None, None, None, None

            if code is None:
                Path(f"{stem}.reply.txt").write_text(resp.text or "")
                if partial:
                    Path(f"{stem}.partial.py").write_text(partial)
                error_type = "no_code"
                error_message = "No ```python code block (or unlabeled ``` code block) was found in the reply."
                if resp.stop_reason == "max_tokens":
                    error_message += f" The reply was cut off at the max_tokens limit ({config.MAX_TOKENS})."
                elif resp.stop_reason == "refusal":
                    error_message += " The request was declined (stop_reason refusal)."
                error_text = error_message
                script_for_repair = partial or ""
            else:
                script_path = stem.with_suffix(".py")
                script_path.write_text(code)
                script_for_repair = code
                unsafe = safety_check(code)
                if unsafe:
                    error_type = "unsafe_code"
                    error_message = f"Unsafe code rejected by the static check: {unsafe}"
                    error_text = error_message
                else:
                    res = run_blender(script_path, category, Path(f"{stem}.result.json"))
                    blender_time = res["blender_time_s"]
                    passed = bool(res.get("passed"))
                    error_type, error_message = res.get("error_type"), res.get("error_message")
                    tb = res.get("traceback")
                    error_text = last_lines(tb) if tb else (error_message or "")
                    if passed and run == 1:  # render in run 1 only; separate call so check timing is comparable
                        png = self.renders_dir / cond.id / f"{sid}.png"
                        png.unlink(missing_ok=True)
                        rres = run_blender(script_path, category, Path(f"{stem}.render.json"), render_png=png)
                        if rres.get("render") and png.exists():
                            render = str(png.relative_to(self.results_dir))
                        else:
                            render_error = rres.get("render_error") or rres.get("error_message") or "no image written"

            final = passed or attempt == cond.max_attempts
            if not passed:
                Path(f"{stem}.error.txt").write_text(error_text)
            self.log({
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "run": run,
                "condition": cond.id,
                "model": cond.model.model_id,
                "scene_id": sid,
                "category": category,
                "attempt": attempt,
                "input_tokens": resp.input_tokens,
                "output_tokens": resp.output_tokens,
                "cost_usd": round(resp.cost_usd, 6),
                "api_latency_s": resp.api_latency_s,
                "blender_time_s": blender_time,
                "stop_reason": resp.stop_reason,
                "passed": passed,
                "error_type": error_type,
                "error_message": first_line(error_message),
                "final": final,
                "code_block_unlabeled": extracted.unlabeled,  # True: block had no language tag; None: no block
                "api_retries": resp.api_retries,
                "render": render,
                "render_error": render_error,
            })
            status = "PASS" if passed else f"fail {error_type}"
            print(f"[run {run}] {cond.id:<19} scene {sid:>2} a{attempt}  {status:<24} ${resp.cost_usd:.4f}  "
                  f"api {resp.api_latency_s:5.1f}s  blender {blender_time:5.1f}s  spent ${self.budget.spent:.2f}",
                  flush=True)
            if final:
                return
            prev_script, prev_error = script_for_repair, error_text


def interleaved_jobs(runs, condition_ids, scenes):
    """Per run, per scene, every condition; the condition order rotates per scene. Never one condition first."""
    jobs = []
    for run in range(1, runs + 1):
        for i, scene in enumerate(scenes):
            k = i % len(condition_ids)
            for cid in condition_ids[k:] + condition_ids[:k]:
                jobs.append((run, cid, scene))
    return jobs


def combo_state(rows):
    finished, partial = set(), defaultdict(list)
    for r in rows:
        key = (r["run"], r["condition"], r["scene_id"])
        if r.get("final"):
            finished.add(key)
        partial[key].append(r)
    for key in finished:
        partial.pop(key, None)
    for key in partial:
        partial[key].sort(key=lambda r: r["attempt"])
    return finished, partial


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def write_meta(results_dir: Path, args, condition_ids, scene_ids):
    try:
        blender = subprocess.run([config.BLENDER_PATH, "--version"], capture_output=True, text=True,
                                 timeout=60).stdout.splitlines()[0].strip()
    except Exception as exc:
        blender = f"unknown ({exc})"
    import anthropic
    meta = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "argv": sys.argv[1:],
        "conditions": condition_ids,
        "scenes": scene_ids,
        "runs": args.runs,
        "system_prompt_sha": _sha(config.SYSTEM_PROMPT),
        "cheatsheet_sha": _sha(config.CHEATSHEET_FILE.read_text()) if config.CHEATSHEET_FILE.exists() else None,
        "blender": blender,
        "python": platform.python_version(),
        "anthropic_sdk": anthropic.__version__,
        "max_tokens": config.MAX_TOKENS,
        "max_spend_usd": config.MAX_SPEND_USD,
    }
    try:
        import groq
        meta["groq_sdk"] = groq.__version__
    except ImportError:
        pass
    with (results_dir / "meta.jsonl").open("a") as f:
        f.write(json.dumps(meta) + "\n")


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness.run")
    p.add_argument("--runs", type=int, default=3)
    p.add_argument("--scenes", help="comma separated scene ids (default: all 30)")
    p.add_argument("--conditions", help="comma separated condition ids (default: the 4 core conditions)")
    p.add_argument("--include-groq", action="store_true", help="add gptoss120b_bare and gptoss120b_harness")
    p.add_argument("--concurrency", type=int, default=4, help="parallel combos (Blender is capped at 2 processes)")
    p.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    args = p.parse_args(argv)

    condition_ids = args.conditions.split(",") if args.conditions else list(config.CORE_CONDITIONS)
    if args.include_groq:
        condition_ids += [c for c in config.GROQ_CONDITIONS if c not in condition_ids]
    unknown = [c for c in condition_ids if c not in config.CONDITIONS]
    if unknown:
        p.error(f"unknown conditions: {unknown}")
    if any(c in config.GROQ_CONDITIONS for c in condition_ids) and not args.include_groq:
        p.error("Groq conditions need --include-groq")

    all_scenes = config.load_scenes()
    if args.scenes:
        wanted = [int(s) for s in args.scenes.split(",")]
        scenes = [s for s in all_scenes if s["id"] in wanted]
        missing = set(wanted) - {s["id"] for s in scenes}
        if missing:
            p.error(f"unknown scene ids: {sorted(missing)}")
    else:
        scenes = all_scenes

    conds = [config.CONDITIONS[c] for c in condition_ids]
    if any(c.harness for c in conds) and not config.CHEATSHEET_FILE.exists():
        sys.exit("cheatsheet.md is missing; harness conditions need it.")
    for provider, key in (("anthropic", "ANTHROPIC_API_KEY"), ("groq", "GROQ_API_KEY")):
        if any(c.model.provider == provider for c in conds) and not os.environ.get(key):
            sys.exit(f"{key} is not set (.env)")

    results_dir = config.RESULTS_DIR
    rows = read_rows(results_dir / "runs.jsonl")
    spent = sum(r.get("cost_usd") or 0 for r in rows)
    finished, partial = combo_state(rows)
    jobs = [j for j in interleaved_jobs(args.runs, condition_ids, scenes) if (j[0], j[1], j[2]["id"]) not in finished]

    worst = 0.0
    for run, cid, scene in jobs:
        c = config.CONDITIONS[cid]
        chars = len(config.system_prompt(c.harness)) + len(scene["prompt"]) + 60000 * c.harness
        worst += c.max_attempts * config.worst_case_cost(c.model, chars)
    print(f"conditions: {', '.join(condition_ids)}")
    print(f"scenes:     {', '.join(str(s['id']) for s in scenes)}   runs: {args.runs}")
    print(f"combos:     {len(jobs)} to run ({len(finished)} already finished, {len(partial)} partial to resume)")
    print(f"spend:      ${spent:.4f} so far, MAX_SPEND_USD=${config.MAX_SPEND_USD:.2f}, "
          f"theoretical worst case for this plan ${worst:.2f} (every call maxing 16k output tokens)")
    if not jobs:
        print("nothing to do.")
        return
    if not args.yes:
        if not sys.stdin.isatty() or input("This calls paid APIs. Proceed? [y/N] ").strip().lower() != "y":
            print("aborted.")
            return

    results_dir.mkdir(parents=True, exist_ok=True)
    write_meta(results_dir, args, condition_ids, [s["id"] for s in scenes])
    exp = Experiment(results_dir, llm.Budget(config.MAX_SPEND_USD, spent))
    ex = ThreadPoolExecutor(max_workers=max(1, args.concurrency))
    try:
        futures = [ex.submit(exp.run_combo, run, config.CONDITIONS[cid], scene,
                             partial.get((run, cid, scene["id"]), []))
                   for run, cid, scene in jobs]
        for f in as_completed(futures):
            f.result()
    except KeyboardInterrupt:
        exp.halt("interrupted (Ctrl-C)")
        ex.shutdown(wait=True, cancel_futures=True)
    finally:
        ex.shutdown(wait=True)
    print(f"\ndone. total spend in runs.jsonl: ${exp.budget.spent:.4f}"
          + (f"  (stopped early: {exp.halt_reason})" if exp.halt_reason else ""))


if __name__ == "__main__":
    main()
