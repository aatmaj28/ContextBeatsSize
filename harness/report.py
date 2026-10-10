"""Metrics and figures from results/runs.jsonl.

python -m harness.report [--results results] [--grid-scenes 1,5,11,12,13,21,23,27]

Writes summary.md, chart.png, comparison_grid.png and post_numbers.md into the results folder.
"""
import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from . import config

CATEGORIES = ["basic", "materials", "world", "compositor", "anim", "gn"]

# Reference data-viz palette (validated categorical slots 1-3) and text/surface tokens.
SURFACE, INK, INK_2, INK_3, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
MODEL_COLOR = {"opus": "#2a78d6", "haiku": "#eb6834", "gptoss120b": "#1baf7a"}
FAIL_RED = "#d03b3b"


def load_combos(results_dir: Path):
    log = results_dir / "runs.jsonl"
    rows = [json.loads(l) for l in log.read_text().splitlines() if l.strip()] if log.exists() else []
    combos = defaultdict(list)
    for r in rows:
        combos[(r["run"], r["condition"], r["scene_id"])].append(r)
    complete, incomplete = {}, []
    for key, attempts in combos.items():
        attempts.sort(key=lambda r: r["attempt"])
        if attempts[-1].get("final"):
            complete[key] = attempts
        else:
            incomplete.append(key)
    return rows, complete, incomplete


def combo_metrics(attempts):
    last = attempts[-1]
    return {
        "category": last["category"],
        "passed": bool(last["passed"]),
        "first_pass": bool(attempts[0]["passed"]) and attempts[0]["attempt"] == 1,
        "attempts": len(attempts),
        "cost": sum(a["cost_usd"] for a in attempts),
        "time": sum(a["api_latency_s"] + a["blender_time_s"] for a in attempts),
    }


def per_run_stats(complete):
    """{condition: {run: {...aggregates for that run...}}}"""
    grouped = defaultdict(lambda: defaultdict(list))
    for (run, cond, _sid), attempts in complete.items():
        grouped[cond][run].append(combo_metrics(attempts))
    out = defaultdict(dict)
    for cond, runs in grouped.items():
        for run, ms in runs.items():
            n = len(ms)
            passed = sum(m["passed"] for m in ms)
            cost = sum(m["cost"] for m in ms)
            by_cat = {}
            for cat in CATEGORIES:
                cm = [m for m in ms if m["category"] == cat]
                if cm:
                    by_cat[cat] = sum(m["passed"] for m in cm) / len(cm)
            out[cond][run] = {
                "n": n,
                "pass_rate": passed / n,
                "first_pass_rate": sum(m["first_pass"] for m in ms) / n,
                "avg_attempts": statistics.mean(m["attempts"] for m in ms),
                "cost": cost,
                "cost_per_working": cost / passed if passed else None,
                "avg_time": statistics.mean(m["time"] for m in ms),
                "by_cat": by_cat,
            }
    return out


def spread(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return statistics.mean(vals), min(vals), max(vals)


def fmt(s, kind):
    if s is None:
        return "n/a"
    mean, lo, hi = s
    f = {"pct": lambda v: f"{v * 100:.0f}%", "usd": lambda v: f"${v:.4f}" if v < 1 else f"${v:.2f}",
         "num": lambda v: f"{v:.2f}", "sec": lambda v: f"{v:.1f}s"}[kind]
    return f(mean) if lo == hi else f"{f(mean)} ({f(lo)}–{f(hi)})"


# Quoted data-block names after these words are replaced, so the same error on different objects groups.
_NAMED = r"(Object|object|Collection|collection|Mesh|mesh|Material|material|Camera|camera|Light|light|" \
         r"World|world|Scene|scene|Image|image|Curve|curve|Text|text|Action|action|NodeTree|node group)"


def error_label(error_type, message) -> str:
    """Readable, groupable label: 'KeyError: bpy_prop_collection[key]: key "W" not found'."""
    msg = (message or "").strip()
    m = re.match(r"^(KeyError): '(.*)'$", msg)  # str(KeyError) wraps the whole message in quotes
    if m:
        msg = f"{m.group(1)}: {m.group(2)}"
    msg = re.sub(r"0x[0-9a-fA-F]+", "<addr>", msg)
    msg = re.sub(_NAMED + r"""\s+(["'])[^"']*\2""", r"\1 <name>", msg)
    msg = re.sub(r"""\b(objects|meshes|materials|collections)\[(["'])[^"']*\2\]""", r"\1[<name>]", msg)
    msg = re.sub(r"(?<![\w.])\d+(\.\d+)?(?![\w.])", "N", msg)  # numbers, not parts of names like Socket_2
    if error_type and not msg.startswith(error_type):
        msg = f"[{error_type}] {msg}"
    return msg


def conditions_present(stats):
    order = config.CORE_CONDITIONS + config.GROQ_CONDITIONS
    return [c for c in order if c in stats]


# ---------------------------------------------------------------- summary.md
def write_summary(results_dir, rows, complete, incomplete, stats):
    conds = conditions_present(stats)
    runs = sorted({k[0] for k in complete})
    scenes = sorted({k[2] for k in complete})
    L = ["# Blender AI Race: results", ""]
    L.append(f"Runs: {', '.join(map(str, runs)) or 'none'} · scenes: {len(scenes)} "
             f"({', '.join(map(str, scenes))}) · attempts logged: {len(rows)} · "
             f"total spend: ${sum(r['cost_usd'] for r in rows):.4f}")
    L.append("")
    L.append("Each cell is the mean across runs, with the min to max range in parentheses when runs differ.")
    if incomplete:
        L += ["", f"**Incomplete combos (excluded): {len(incomplete)}** — "
              + ", ".join(f"run {r} {c} scene {s}" for r, c, s in sorted(incomplete))]
    L += ["", "## Overall", "",
          "| condition | final pass rate | first attempt pass rate | avg attempts | total cost per run | "
          "total cost (all runs) | cost per working scene | avg time per scene |",
          "|---|---|---|---|---|---|---|---|"]
    for c in conds:
        rs = stats[c].values()
        L.append(f"| {config.LABELS[c]} | {fmt(spread(r['pass_rate'] for r in rs), 'pct')} | "
                 f"{fmt(spread(r['first_pass_rate'] for r in rs), 'pct')} | "
                 f"{fmt(spread(r['avg_attempts'] for r in rs), 'num')} | "
                 f"{fmt(spread(r['cost'] for r in rs), 'usd')} | ${sum(r['cost'] for r in rs):.4f} | "
                 f"{fmt(spread(r['cost_per_working'] for r in rs), 'usd')} | "
                 f"{fmt(spread(r['avg_time'] for r in rs), 'sec')} |")
    cats = [cat for cat in CATEGORIES if any(cat in r["by_cat"] for c in conds for r in stats[c].values())]
    L += ["", "## Final pass rate by category", "",
          "| condition | " + " | ".join(cats) + " |", "|---|" + "---|" * len(cats)]
    for c in conds:
        cells = [fmt(spread(r["by_cat"].get(cat) for r in stats[c].values()), "pct") for cat in cats]
        L.append(f"| {config.LABELS[c]} | " + " | ".join(cells) + " |")
    L += ["", "## Top 5 error messages per condition (all failed attempts, normalized)", ""]
    for c in conds:
        errs = Counter(error_label(r['error_type'], r['error_message'])
                       for r in rows if r["condition"] == c and not r["passed"])
        L += [f"### {config.LABELS[c]}", ""]
        if not errs:
            L += ["No failed attempts.", ""]
            continue
        L += ["| count | error |", "|---|---|"]
        for msg, n in errs.most_common(5):
            L.append(f"| {n} | `{msg.replace('|', '/')}` |")
        L.append("")
    (results_dir / "summary.md").write_text("\n".join(L) + "\n")


# ---------------------------------------------------------------- chart.png
def write_chart(results_dir, stats):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    conds = conditions_present(stats)
    if not conds:
        return
    means, los, his, costs = [], [], [], []
    for c in conds:
        rs = list(stats[c].values())
        m, lo, hi = spread(r["pass_rate"] for r in rs)
        means.append(m * 100); los.append((m - lo) * 100); his.append((hi - m) * 100)
        costs.append(sum(r["cost"] for r in rs))
    plt.rcParams.update({"font.family": "Helvetica", "font.size": 13})
    fig, ax = plt.subplots(figsize=(13, 7), dpi=150)
    fig.patch.set_facecolor(SURFACE); ax.set_facecolor(SURFACE)
    x = range(len(conds))
    for i, c in enumerate(conds):
        cond = config.CONDITIONS[c]
        color = MODEL_COLOR[cond.model.key]
        # 45° texture (hatch drawn in the surface color) is the second channel for bare vs harness
        ax.bar(i, means[i], width=0.62, color=color, edgecolor=SURFACE, linewidth=0, zorder=2,
               hatch=None if cond.harness else "///")
    n_runs = max(len(stats[c]) for c in conds)
    if n_runs > 1:
        ax.errorbar(list(x), means, yerr=[los, his], fmt="none", ecolor=INK_2, elinewidth=2, capsize=6, zorder=4)
    for i in x:
        ax.text(i, means[i] + his[i] + 2.5, f"{means[i]:.0f}%", ha="center", va="bottom", fontsize=17,
                fontweight="bold", color=INK, zorder=5)
        ax.text(i, means[i] + his[i] + 9.5, f"${costs[i]:.2f} total", ha="center", va="bottom", fontsize=12.5,
                color=INK_2, zorder=5)
    ax.set_xticks(list(x))
    ax.set_xticklabels([config.LABELS[c].replace(" + ", "\n+ ") for c in conds], color=INK, fontsize=13)
    ax.set_ylim(0, 118)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels([f"{v}%" for v in [0, 25, 50, 75, 100]], color=INK_3)
    ax.yaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK_3)
    ax.tick_params(axis="both", length=0, pad=8)
    ax.set_ylabel("Working Blender 5.2 scripts (final pass rate)", color=INK_2, fontsize=13, labelpad=10)
    runs_note = f"mean of {n_runs} runs, whiskers show min to max" if n_runs > 1 else "1 run"
    fig.suptitle("Small model + harness vs frontier model cold", x=0.07, ha="left", fontsize=20,
                 fontweight="bold", color=INK, y=0.97)
    ax.set_title(f"Pass rate per condition, total API cost on each bar ({runs_note}). Hatched = bare (no harness).",
                 loc="left", color=INK_2, fontsize=13, pad=14)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.14)
    fig.savefig(results_dir / "chart.png", facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------- comparison_grid.png
def _font(size, bold=False):
    from PIL import ImageFont
    candidates = (["/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Bold.ttf"] if bold else
                  ["/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"])
    candidates += ["/System/Library/Fonts/Helvetica.ttc"]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _wrap(draw, text, font, width, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
            while draw.textlength(cur, font=font) > width and len(cur) > 1:  # hard-break long tokens
                cut = len(cur)
                while cut > 1 and draw.textlength(cur[:cut], font=font) > width:
                    cut -= 1
                lines.append(cur[:cut]); cur = cur[cut:]
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip()[: max(0, len(lines[-1]) - 1)] + "…"
    return lines


def write_grid(results_dir, complete, grid_scenes):
    from PIL import Image, ImageDraw

    scenes = {s["id"]: s for s in config.load_scenes()}
    conds = [c for c in config.CORE_CONDITIONS + config.GROQ_CONDITIONS if any(k[1] == c for k in complete)]
    run1 = {(k[1], k[2]): v for k, v in complete.items() if k[0] == 1}
    cols = [sid for sid in grid_scenes if any((c, sid) in run1 for c in conds)]
    if not conds or not cols:
        return
    label_w, head_h, gap, min_width = 250, 96, 6, 1600
    tile_w = max(320, (min_width - label_w - gap * (len(cols) + 1)) // len(cols) + 1)
    tile_h = tile_w * 9 // 16
    W = label_w + len(cols) * (tile_w + gap) + gap
    H = head_h + len(conds) * (tile_h + gap) + gap + 44
    img = Image.new("RGB", (W, H), SURFACE)
    d = ImageDraw.Draw(img)
    f_head, f_sub, f_label, f_err, f_badge = _font(20, True), _font(15), _font(19, True), _font(15), _font(14, True)

    for j, sid in enumerate(cols):
        x0 = label_w + gap + j * (tile_w + gap)
        sc = scenes[sid]
        d.text((x0 + 2, 14), f"#{sid} · {sc['category']}", font=f_head, fill=INK)
        for k, line in enumerate(_wrap(d, sc["prompt"], f_sub, tile_w - 4, 3)):
            d.text((x0 + 2, 42 + k * 17), line, font=f_sub, fill=INK_2)

    for i, c in enumerate(conds):
        y0 = head_h + gap + i * (tile_h + gap)
        cond = config.CONDITIONS[c]
        d.rectangle([14, y0 + tile_h // 2 - 26, 20, y0 + tile_h // 2 + 26], fill=MODEL_COLOR[cond.model.key])
        for k, line in enumerate(config.LABELS[c].replace(" + ", "\n+ ").split("\n")):
            d.text((32, y0 + tile_h // 2 - 24 + k * 26), line, font=f_label, fill=INK)
        for j, sid in enumerate(cols):
            x0 = label_w + gap + j * (tile_w + gap)
            box = [x0, y0, x0 + tile_w - 1, y0 + tile_h - 1]
            attempts = run1.get((c, sid))
            if attempts is None:
                d.rectangle(box, fill="#ecebe7")
                d.text((x0 + 14, y0 + 12), "not run", font=f_err, fill=INK_3)
                continue
            last = attempts[-1]
            if last["passed"]:
                png = results_dir / last["render"] if last.get("render") else None
                if png is not None and png.exists():
                    tile = Image.open(png).convert("RGBA").resize((tile_w, tile_h), Image.Resampling.LANCZOS)
                    bg = Image.new("RGBA", tile.size, (20, 20, 20, 255))
                    img.paste(Image.alpha_composite(bg, tile).convert("RGB"), (x0, y0))
                else:
                    d.rectangle(box, fill="#d9d8d3")
                    d.text((x0 + 14, y0 + 12), "passed (render missing)", font=f_err, fill=INK_2)
                badge = f"PASS · attempt {last['attempt']}"
                bw = d.textlength(badge, font=f_badge) + 16
                d.rounded_rectangle([x0 + 8, y0 + 8, x0 + 8 + bw, y0 + 32], radius=4, fill=(11, 11, 11))
                d.text((x0 + 16, y0 + 12), badge, font=f_badge, fill="#ffffff")
            else:
                d.rectangle(box, fill=FAIL_RED)
                d.text((x0 + 14, y0 + 12), f"FAILED · {last['error_type']}", font=f_badge, fill="#ffffff")
                msg = last.get("error_message") or ""
                for k, line in enumerate(_wrap(d, msg, f_err, tile_w - 28, max(1, (tile_h - 70) // 19))):
                    d.text((x0 + 14, y0 + 40 + k * 19), line, font=f_err, fill="#ffffff")
                if len(attempts) > 1:
                    d.text((x0 + 14, y0 + tile_h - 26), f"after {len(attempts)} attempts", font=f_err, fill="#ffe9e9")
    d.text((label_w + gap, H - 34), "Run 1 renders (Cycles, 640×360). PASS badge shows the attempt that passed. "
           "Red = failed after the last allowed attempt.", font=f_sub, fill=INK_3)
    img.save(results_dir / "comparison_grid.png")


# ---------------------------------------------------------------- post_numbers.md
def write_post_numbers(results_dir, stats):
    L = []
    totals = {}
    for c in conditions_present(stats):
        rs = list(stats[c].values())
        rate = spread(r["pass_rate"] for r in rs)[0]
        cost = sum(r["cost"] for r in rs)
        t = spread(r["avg_time"] for r in rs)[0]
        totals[c] = (rate, cost, t)
        L.append(f"{config.LABELS[c]}: {rate * 100:.0f}% working scripts, ${cost:.2f} total")
    L.append("")
    if "haiku_harness" in totals and "opus_bare" in totals:
        (hr, hc, ht), (orate, oc, ot) = totals["haiku_harness"], totals["opus_bare"]
        n = len(stats["opus_bare"])
        L.append(f"Cost ratio: Opus bare cost {oc / hc:.1f}x as much as Haiku + harness (${oc:.2f} vs ${hc:.2f})"
                 if hc else "Cost ratio: n/a")
        L.append(f"Speed ratio: Opus bare took {ot / ht:.2f}x as long per scene as Haiku + harness "
                 f"({ot:.1f}s vs {ht:.1f}s, API latency + Blender time across all attempts)" if ht else "Speed ratio: n/a")
        L.append(f"Pass rate gap: Haiku + harness minus Opus bare = {(hr - orate) * 100:+.0f} percentage points "
                 f"({hr * 100:.0f}% vs {orate * 100:.0f}%)")
        L.append("")
        L.append(f"Based on {n} run(s); pass rates are the mean across runs, costs are totals across runs.")
    else:
        L.append("Ratios need both haiku_harness and opus_bare results.")
    (results_dir / "post_numbers.md").write_text("\n".join(L) + "\n")


def build(results_dir: Path, grid_scenes=None):
    rows, complete, incomplete = load_combos(results_dir)
    if not rows:
        raise SystemExit(f"no rows in {results_dir / 'runs.jsonl'}")
    stats = per_run_stats(complete)
    write_summary(results_dir, rows, complete, incomplete, stats)
    write_chart(results_dir, stats)
    write_grid(results_dir, complete, grid_scenes or config.GRID_SCENES)
    write_post_numbers(results_dir, stats)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness.report")
    p.add_argument("--results", default=str(config.RESULTS_DIR))
    p.add_argument("--grid-scenes", help=f"comma separated scene ids (default {config.GRID_SCENES})")
    args = p.parse_args(argv)
    grid = [int(s) for s in args.grid_scenes.split(",")] if args.grid_scenes else None
    results_dir = Path(args.results)
    build(results_dir, grid)
    for name in ("summary.md", "chart.png", "comparison_grid.png", "post_numbers.md"):
        print(results_dir / name)


if __name__ == "__main__":
    main()
