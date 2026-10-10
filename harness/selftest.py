"""Selftest. No API calls.

python -m harness.selftest [--no-render]

1. extract.py: code block extraction and the AST safety check.
2. selftest_scripts/<category>.py: known good Blender 5.2 scripts, one per category, must pass (and render).
3. selftest_scripts/cases/*.py: edge cases with an expected outcome in their header
   (old pre-5.x API must fail, broken checks must fail, periodic animation must pass, timeout must time out).
4. Offline pipeline: run.py + llm.py + report.py with the Anthropic call replaced by a fake,
   covering the repair loop, logging, renders, resume, API retry and the budget guard.
"""
import argparse
import json
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import config, llm, report
from .blender_runner import run_blender
from .extract import extract_code, safety_check
from .run import Experiment, combo_state, read_rows

OUT = config.RESULTS_DIR / "selftest"
GOOD = ["basic", "materials", "world", "compositor", "anim", "gn"]
results = []  # (section, name, ok, detail)


def record(section, name, ok, detail=""):
    results.append((section, name, ok, detail))
    print(f"  {'ok  ' if ok else 'FAIL'} {section:<9} {name:<22} {detail}", flush=True)


# ---------------------------------------------------------------- 1. extract
def test_extract():
    e = extract_code("Here:\n```python\nimport bpy\nprint(1)\n```\n")
    record("extract", "python block", e.code == "import bpy\nprint(1)\n" and e.partial is None and e.unlabeled is False)
    e = extract_code("```py\nimport bpy\n```")
    record("extract", "py block", e.code == "import bpy\n" and e.unlabeled is False)
    e = extract_code("No code here, sorry.")
    record("extract", "no block", e.code is None and e.partial is None and e.unlabeled is None)
    e = extract_code("```python\nimport bpy\nbpy.ops.mesh.prim")
    record("extract", "truncated block", e.code is None and e.partial.startswith("import bpy"))
    e = extract_code("```\nimport bpy\n```")
    record("extract", "unlabeled block", e.code == "import bpy\n" and e.unlabeled is True, "accepted, flagged")
    e = extract_code("```\nimport math\n```\nthen\n```python\nimport bpy\n```")
    record("extract", "python preferred", e.code == "import bpy\n" and e.unlabeled is False)
    e = extract_code("```bash\nls\n```\nsome text\n```\nimport bpy\n```")
    record("extract", "other lang skipped", e.code == "import bpy\n" and e.unlabeled is True,
           "a closing fence is never read as an opening one")
    e = extract_code("```bash\nls -la\n```")
    record("extract", "other lang only", e.code is None)
    cases = {
        "import bpy\nimport bmesh, math, random, colorsys\nfrom mathutils import Vector\n"
        "import bpy_extras.anim_utils\nfrom bpy_extras import anim_utils\n": None,
        "import os\n": "os",
        "import subprocess as sp\n": "subprocess",
        "from pathlib import Path\n": "pathlib",
        "from . import x\n": "relative",
        "eval('1+1')\n": "eval",
        "exec('x=1')\n": "exec",
        "f = open('/tmp/x', 'w')\n": "open",
        "compile('1', 'f', 'eval')\n": "compile",
        "m = __import__('os')\n": "__import__",
        "g = eval\n": "eval",
    }
    for src, expect in cases.items():
        reason = safety_check(src)
        ok = reason is None if expect is None else (reason is not None and expect in reason)
        record("ast", (expect or "allowed imports"), ok, reason or "")


# ---------------------------------------------------------------- 2/3. Blender
def parse_header(path: Path) -> dict:
    meta = {}
    for line in path.read_text().splitlines():
        m = re.match(r"#\s*(category|expect|expect_message|timeout):\s*(.+)", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def blender_job(section, name, script, category, expect="pass", expect_message=None, timeout=None, render=None):
    t0 = time.time()
    res = run_blender(script, category, OUT / "results" / f"{name}.json", render_png=render,
                      timeout=float(timeout) if timeout else config.BLENDER_TIMEOUT_S)
    if expect == "pass":
        ok = bool(res.get("passed"))
        if ok and render is not None:
            ok = res.get("render") is not None and Path(render).exists()
            if not ok:
                res["error_message"] = f"render failed: {res.get('render_error')}"
    else:
        ok = not res.get("passed") and res.get("error_type") == expect
        if ok and expect_message:
            ok = expect_message.lower() in (res.get("error_message") or "").lower()
    detail = (f"{res.get('error_type')}: {res.get('error_message')}" if not res.get("passed") else "passed")
    if render is not None and res.get("render_time_s") is not None:
        detail += f", rendered in {res['render_time_s']:.1f}s"
    detail += f"  [{time.time() - t0:.1f}s]"
    return section, name, ok, detail.replace("\n", " ")[:160]


def test_blender(do_render):
    jobs = []
    for cat in GOOD:
        render = OUT / "renders" / f"{cat}.png" if do_render else None
        jobs.append(("known", cat, config.SELFTEST_DIR / f"{cat}.py", cat, "pass", None, None, render))
    for path in sorted((config.SELFTEST_DIR / "cases").glob("*.py")):
        h = parse_header(path)
        jobs.append(("case", path.stem, path, h["category"], h["expect"], h.get("expect_message"), h.get("timeout"), None))
    with ThreadPoolExecutor(max_workers=config.MAX_BLENDER_PROCS) as ex:
        for out in ex.map(lambda j: blender_job(*j), jobs):
            record(*out)


# ---------------------------------------------------------------- 4. pipeline
class FakeOverloaded(Exception):
    status_code = 529


def fence(code):
    return f"```python\n{code.rstrip()}\n```"


def test_pipeline():
    pdir = OUT / "pipeline"
    shutil.rmtree(pdir, ignore_errors=True)
    pdir.mkdir(parents=True)
    scenes = {s["id"]: s for s in config.load_scenes()}
    good = {cat: (config.SELFTEST_DIR / f"{cat}.py").read_text() for cat in GOOD}
    old_comp = (config.SELFTEST_DIR / "cases" / "old_compositor.py").read_text()
    calls = {"n": 0, "repair_saw_error": False}

    def fake_call_anthropic(model, system, user):
        calls["n"] += 1
        if calls["n"] == 1:
            raise FakeOverloaded("overloaded")  # retried by llm.call_model, not counted as an attempt
        harness = config.HARNESS_PREFIX in system
        if "Scene: " + scenes[12]["prompt"] in user:
            if not harness:
                return "I would build the sign with a text object.", 1000, 2000, "end_turn"
            if "Your previous script failed in Blender 5.2." in user:
                error_part = user.split("\nError:\n", 1)[-1]
                calls["repair_saw_error"] = "AttributeError" in error_part and "node_tree" in error_part
                return fence(good["compositor"]), 1000, 2000, "end_turn"
            return fence(old_comp), 1000, 2000, "end_turn"
        if not harness:
            return f"```\n{good['anim'].rstrip()}\n```", 1000, 2000, "end_turn"  # unlabeled block
        return fence(good["anim"]), 1000, 2000, "end_turn"

    saved = (llm._call_anthropic, llm.time.sleep, config.CHEATSHEET_FILE)
    llm._call_anthropic = fake_call_anthropic
    llm.time.sleep = lambda s: None
    if not config.CHEATSHEET_FILE.exists():
        placeholder = pdir / "cheatsheet_placeholder.md"
        placeholder.write_text("(placeholder cheat sheet used by the selftest)")
        config.CHEATSHEET_FILE = placeholder
    try:
        conds = [config.CONDITIONS["opus_bare"], config.CONDITIONS["opus_harness"]]
        exp = Experiment(pdir, llm.Budget(10.0))
        for sid in (12, 21):
            for c in conds:
                exp.run_combo(1, c, scenes[sid], [])
        rows = read_rows(pdir / "runs.jsonl")
        by = {(r["condition"], r["scene_id"], r["attempt"]): r for r in rows}
        record("pipeline", "rows logged", len(rows) == 5, f"{len(rows)} rows")
        r = by.get(("opus_harness", 12, 1), {})
        record("pipeline", "old API caught", r.get("error_type") == "AttributeError" and not r.get("final"),
               str(r.get("error_message")))
        record("pipeline", "repair has traceback", calls["repair_saw_error"])
        r = by.get(("opus_harness", 12, 2), {})
        record("pipeline", "repair passes", bool(r.get("passed") and r.get("final")), f"render={r.get('render')}")
        record("pipeline", "render written", bool(r.get("render")) and (pdir / r["render"]).exists())
        r = by.get(("opus_bare", 12, 1), {})
        record("pipeline", "no_code", r.get("error_type") == "no_code" and r.get("final") is True,
               str(r.get("error_message")))
        first = rows[0]
        record("pipeline", "api retry uncounted", first["api_retries"] == 1 and first["attempt"] == 1)
        record("pipeline", "cost from usage", all(abs(r["cost_usd"] - 0.044) < 1e-9 for r in rows),
               "1000 in + 2000 out on Opus = $0.044")
        fields = ["timestamp", "run", "condition", "model", "scene_id", "category", "attempt", "input_tokens",
                  "output_tokens", "cost_usd", "api_latency_s", "blender_time_s", "stop_reason", "passed",
                  "error_type", "error_message"]
        record("pipeline", "log fields", all(all(f in r for f in fields) for r in rows))
        record("pipeline", "unlabeled flag logged",
               by[("opus_bare", 21, 1)].get("code_block_unlabeled") is True
               and by[("opus_harness", 21, 1)].get("code_block_unlabeled") is False
               and by[("opus_bare", 12, 1)].get("code_block_unlabeled") is None)
        record("pipeline", "scripts saved",
               (pdir / "scripts/1/opus_harness/12_a1.py").exists() and (pdir / "scripts/1/opus_harness/12_a2.py").exists())

        finished, partial = combo_state(rows)
        record("pipeline", "resume skips finished", len(finished) == 4 and not partial)

        # resume an interrupted combo: keep only attempt 1 of opus_harness/12
        rdir = OUT / "pipeline_resume"
        shutil.rmtree(rdir, ignore_errors=True)
        (rdir / "scripts/1/opus_harness").mkdir(parents=True)
        for suffix in (".py", ".error.txt"):
            shutil.copy(pdir / f"scripts/1/opus_harness/12_a1{suffix}", rdir / f"scripts/1/opus_harness/12_a1{suffix}")
        (rdir / "runs.jsonl").write_text(json.dumps(by[("opus_harness", 12, 1)]) + "\n")
        _, partial = combo_state(read_rows(rdir / "runs.jsonl"))
        calls["repair_saw_error"] = False
        Experiment(rdir, llm.Budget(10.0)).run_combo(1, config.CONDITIONS["opus_harness"], scenes[12],
                                                     partial[(1, "opus_harness", 12)])
        rrows = read_rows(rdir / "runs.jsonl")
        record("pipeline", "resume partial", len(rrows) == 2 and rrows[1]["attempt"] == 2 and rrows[1]["passed"]
               and calls["repair_saw_error"], "continued at attempt 2 with the saved script and error")

        # budget guard: an Opus call can cost up to ~$0.33, so a $0.05 limit must stop before calling
        bdir = OUT / "pipeline_budget"
        shutil.rmtree(bdir, ignore_errors=True)
        before = calls["n"]
        bexp = Experiment(bdir, llm.Budget(0.05))
        bexp.run_combo(1, config.CONDITIONS["opus_bare"], scenes[21], [])
        record("pipeline", "budget guard", bexp.stop.is_set() and calls["n"] == before
               and not (bdir / "runs.jsonl").exists(), bexp.halt_reason or "")

        cases = {
            ("KeyError", "KeyError: 'bpy_prop_collection[key]: key \"W\" not found'"):
                'KeyError: bpy_prop_collection[key]: key "W" not found',
            ("RuntimeError", 'RuntimeError: Error: Object "Pot.001" already in collection "Scene Collection"'):
                "RuntimeError: Error: Object <name> already in collection <name>",
            ("TypeError", "TypeError: bpy_struct: item.attr = val: enum \"NISHITA\" not found in ('A', 'B')"):
                "TypeError: bpy_struct: item.attr = val: enum \"NISHITA\" not found in ('A', 'B')",
            ("AttributeError", "AttributeError: 'Collection' object has no attribute 'link'"):
                "AttributeError: 'Collection' object has no attribute 'link'",
            ("check_failed", "Check failed: frame_end (1) must be greater than frame_start (1)."):
                "[check_failed] Check failed: frame_end (N) must be greater than frame_start (N).",
        }
        bad = [(k, report.error_label(*k)) for k, want in cases.items() if report.error_label(*k) != want]
        record("report", "error labels", not bad, str(bad) if bad else "nested quotes and names handled")
        report.build(pdir, grid_scenes=[12, 21])
        outs = ["summary.md", "chart.png", "comparison_grid.png", "post_numbers.md"]
        record("report", "outputs written", all((pdir / o).exists() for o in outs), str(pdir))
        from PIL import Image
        w = Image.open(pdir / "comparison_grid.png").size[0]
        record("report", "grid >= 1600 px", w >= 1600, f"{w} px wide")
    finally:
        llm._call_anthropic, llm.time.sleep, config.CHEATSHEET_FILE = saved


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness.selftest")
    p.add_argument("--no-render", action="store_true", help="skip rendering the known good scripts")
    args = p.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    print(f"Blender: {config.BLENDER_PATH}")
    print("1. extract + AST check"); test_extract()
    print("2-3. Blender: known good scripts and edge cases"); test_blender(not args.no_render)
    print("4. offline pipeline (fake API)"); test_pipeline()
    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed in {time.time() - t0:.0f}s"
          + (f"; FAILED: {', '.join(f'{s}/{n}' for s, n, _, _ in failed)}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
