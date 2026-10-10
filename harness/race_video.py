"""Race replay video of run 1, built only from results/ (runs.jsonl, run 1 renders, summary.md).

python -m harness.race_video --compare           # middle still in style A and B, side by side
python -m harness.race_video --stills [--style A] # start, middle and end card frames
python -m harness.race_video [--style A]          # writes results/race_replay.mp4

Each setup replays its run 1 scenes in id order. A scene takes its real time
(api_latency_s + blender_time_s, summed over its attempts). The clock is sped up so the
slowest setup finishes at RACE_S seconds, and the factor is shown on screen.

Styles change typography only: A (Editorial) = Fraunces title + Inter, B (Modern) = Avenir Next.
Fraunces and Inter are Google Fonts under the SIL OFL (assets/fonts/*/OFL.txt).
"""
import argparse
import json
import math
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config

W = H = 1080
FPS = 30
LEAD_S, RACE_S, HOLD_S, FADE_S, END_S = 0.4, 20.0, 0.6, 0.4, 4.0
TOTAL_S = LEAD_S + RACE_S + HOLD_S + FADE_S + END_S
TITLE = "30 Blender 5.2 scenes, 4 AI setups"
FOOTER = "Every script ran in real Blender 5.2.2. Numbers are measured, not simulated."
ORDER = ["opus_bare", "opus_harness", "haiku_bare", "haiku_harness"]
DEFAULT_STYLE = "A"

# Warm neutrals; the setup colors, amber and red keep the same meaning as chart.png / comparison_grid.png.
BG, CARD, INK, INK_2, INK_3 = "#f6f2ec", "#fffdf9", "#1e1c19", "#5c574f", "#9a948a"
PENDING, TRACK, CHIP, PILL_BG = "#efeae2", "#ebe5dc", "#f1ece4", "#24211d"
FAIL_RED, AMBER = "#bf5049", "#fab219"   # white on FAIL_RED: 4.7:1 contrast
MODEL_COLOR = {"opus": "#2a78d6", "haiku": "#eb6834"}

# Layout (same arrangement as before, a little more room)
MARGIN, GAP = 36, 24
PANEL_TOP, PANEL_BOTTOM = 156, 1000
PANEL_W = (W - 2 * MARGIN - GAP) // 2
PANEL_H = (PANEL_BOTTOM - PANEL_TOP - GAP) // 2
PANEL_R, TILE_R = 20, 6
COLS, ROWS, TILE_GAP = 6, 5, 5
TILE_W = (PANEL_W - 2 * 18 - (COLS - 1) * TILE_GAP) // COLS
TILE_H = round(TILE_W * 9 / 16)
GRID_W = COLS * TILE_W + (COLS - 1) * TILE_GAP
GRID_X = (PANEL_W - GRID_W) // 2          # content inset inside a panel
GRID_TOP = 62
BADGE_MIN_S = 0.4   # an "attempt N" badge stays at least this long on screen
POP_S = 0.3         # tile pop-in
COUNT_S = 0.35      # the cost counter eases to its new value
ROLL_S = 0.22       # the working count rolls to its new value
FINISH_S = 0.3


# ---------------------------------------------------------------- fonts
ASSETS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
INTER = ASSETS / "inter" / "Inter[opsz,wght].ttf"
FRAUNCES = ASSETS / "fraunces" / "Fraunces[SOFT,WONK,opsz,wght].ttf"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
AVENIR_INDEX = {400: 7, 500: 5, 600: 2, 700: 0, 800: 8}  # Regular, Medium, Demi Bold, Bold, Heavy


def inter(size, weight):
    f = ImageFont.truetype(str(INTER), size)
    f.set_variation_by_axes([max(14, min(32, size)), weight])
    return f


def fraunces(size, weight):
    f = ImageFont.truetype(str(FRAUNCES), size)
    f.set_variation_by_axes([min(144, size * 1.2), weight, 30, 0])  # opsz, wght, SOFT, WONK
    return f


def avenir(size, weight):
    return ImageFont.truetype(AVENIR, size, index=AVENIR_INDEX[weight])


STYLES = {
    "A": {"name": "Editorial", "title": lambda: fraunces(54, 600), "ui": inter},
    "B": {"name": "Modern", "title": lambda: avenir(52, 700), "ui": avenir},
}


def load_fonts(style):
    s, ui = STYLES[style], STYLES[style]["ui"]
    return {"title": s["title"](), "pill": ui(19, 600), "label": ui(23, 600), "caps": ui(13, 600),
            "value": ui(34, 600), "tile": ui(12, 700), "badge": ui(12, 600), "status": ui(11, 700),
            "footer": ui(17, 400), "end_label": ui(29, 600), "end_pct": ui(56, 600), "end_cost": ui(24, 400),
            "end_caps": ui(14, 600)}


# ---------------------------------------------------------------- data
def load_timelines(results: Path):
    """Per condition: real-time events for run 1, scenes in id order, attempts back to back."""
    rows = [json.loads(l) for l in (results / "runs.jsonl").read_text().splitlines() if l.strip()]
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["run"] == 1:
            by[r["condition"]][r["scene_id"]].append(r)
    timelines = {}
    for cond in ORDER:
        clock, scenes, costs = 0.0, [], []
        for sid in sorted(by[cond]):
            attempts = sorted(by[cond][sid], key=lambda r: r["attempt"])
            if not attempts[-1].get("final"):
                raise SystemExit(f"run 1 {cond} scene {sid} is incomplete")
            start, ends = clock, []
            for a in attempts:
                clock += a["api_latency_s"] + a["blender_time_s"]
                ends.append(clock)
                costs.append((clock, a["cost_usd"]))
            last = attempts[-1]
            scenes.append({"id": sid, "start": start, "ends": ends, "passed": bool(last["passed"]),
                           "render": results / last["render"] if last.get("render") else None})
        if len(scenes) != 30:
            raise SystemExit(f"run 1 {cond}: expected 30 scenes, found {len(scenes)}")
        timelines[cond] = {"scenes": scenes, "costs": costs, "total": clock,
                           "cost_total": sum(c for _, c in costs)}
    return timelines


def load_end_card(results: Path):
    """Pass rate (mean of the runs) and total API cost (all runs) straight from summary.md's Overall table."""
    text = (results / "summary.md").read_text()
    table = text.split("## Overall", 1)[1].split("\n## ", 1)[0]
    lines = [l for l in table.splitlines() if l.startswith("|")]
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    label_to_cond = {config.LABELS[c]: c for c in ORDER}
    runs = re.search(r"Runs: ([\d, ]+)", text).group(1)
    out = {}
    for line in lines[2:]:
        cells = dict(zip(header, (c.strip() for c in line.strip("|").split("|"))))
        cond = label_to_cond.get(cells["condition"])
        if cond:
            out[cond] = {"pass": cells["final pass rate"].split()[0],
                         "cost": float(cells["total cost (all runs)"].split()[0].lstrip("$"))}
    return out, len(runs.split(","))


# ---------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out_cubic(x):
    return 1 - (1 - clamp01(x)) ** 3


def ease_out_back(x, k=1.6):
    x = clamp01(x) - 1
    return 1 + (k + 1) * x ** 3 + k * x ** 2


# ---------------------------------------------------------------- drawing helpers
SS = 4  # supersampling for smooth rounded shapes


def rounded_mask(w, h, r):
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, fill=255)
    return m.resize((w, h), Image.Resampling.LANCZOS)


def rounded(w, h, r, fill):
    img = Image.new("RGBA", (w, h), fill)
    img.putalpha(rounded_mask(w, h, r))
    return img


def rounded_outline(w, h, r, color, width):
    m = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], radius=r * SS, outline=255, width=width * SS)
    img = Image.new("RGBA", (w, h), color)
    img.putalpha(m.resize((w, h), Image.Resampling.LANCZOS))
    return img


def hatch_patch(w, h, color, spacing=7, width=2):
    """Solid fill with a 45° texture in the background color: the chart's 'bare' encoding."""
    patch = Image.new("RGB", (w, h), color)
    d = ImageDraw.Draw(patch)
    for off in range(-h, w + h, spacing):
        d.line([(off, h), (off + h, 0)], fill=CARD, width=width)
    return patch


def with_mask(patch, mask):
    img = patch.convert("RGBA")
    img.putalpha(mask)
    return img


def composite_at(base, layer, x, y):
    """alpha_composite that accepts negative offsets (crops the part outside the image)."""
    x, y = round(x), round(y)
    cx, cy = max(0, -x), max(0, -y)
    if cx or cy:
        layer = layer.crop((cx, cy, layer.width, layer.height))
        x, y = x + cx, y + cy
    base.alpha_composite(layer, (x, y))


def shadow(base, box, r, blur, offset, alpha):
    x0, y0, x1, y1 = box
    pad = blur * 3
    layer = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([pad, pad, pad + x1 - x0, pad + y1 - y0], radius=r,
                                            fill=(60, 42, 20, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    composite_at(base, layer, x0 - pad, y0 - pad + offset)


def draw_spaced(d, xy, text, fnt, fill, tracking, anchor="l"):
    """Letter-spaced text (Pillow has no tracking). anchor: l, m or r on the x axis; y is the top."""
    widths = [d.textlength(c, font=fnt) for c in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    x -= {"l": 0, "m": total / 2, "r": total}[anchor]
    for c, w in zip(text, widths):
        d.text((x, y), c, font=fnt, fill=fill)
        x += w + tracking
    return total


def digit_cell(d, fnt):
    return max(d.textlength(c, font=fnt) for c in "0123456789")


def tabular_width(d, text, fnt):
    cell = digit_cell(d, fnt)
    return sum(cell if c.isdigit() else d.textlength(c, font=fnt) for c in text)


def draw_tabular(d, xy, text, fnt, fill, anchor="l"):
    """Fixed-width digits, so a counter keeps its width as it ticks."""
    cell = digit_cell(d, fnt)
    x, y = xy
    x -= {"l": 0, "m": tabular_width(d, text, fnt) / 2, "r": tabular_width(d, text, fnt)}[anchor]
    for c in text:
        if c.isdigit():
            w = d.textlength(c, font=fnt)
            d.text((x + (cell - w) / 2, y), c, font=fnt, fill=fill)
            x += cell
        else:
            d.text((x, y), c, font=fnt, fill=fill)
            x += d.textlength(c, font=fnt)


def money(v, small):
    return f"${v:.3f}" if small else f"${v:.2f}"


def clock_text(seconds):
    s = int(seconds)
    return f"{s // 60}:{s % 60:02d}"


def panel_origin(i):
    return MARGIN + (i % 2) * (PANEL_W + GAP), PANEL_TOP + (i // 2) * (PANEL_H + GAP)


def tile_pos(px, py, k):
    col, row = k % COLS, k // COLS
    return px + GRID_X + col * (TILE_W + TILE_GAP), py + GRID_TOP + row * (TILE_H + TILE_GAP)


def paste_scaled(frame, sprite, center, scale, alpha):
    if alpha <= 0 or scale <= 0:
        return
    w, h = max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale))
    s = sprite if (w, h) == sprite.size else sprite.resize((w, h), Image.Resampling.BILINEAR)
    if alpha < 1:
        s = s.copy()
        s.putalpha(s.getchannel("A").point(lambda v: round(v * alpha)))
    composite_at(frame, s, center[0] - w / 2, center[1] - h / 2)


# ---------------------------------------------------------------- frames
class Renderer:
    def __init__(self, results: Path, style: str = DEFAULT_STYLE):
        self.style = style
        self.F = load_fonts(style)
        self.tl = load_timelines(results)
        self.end, self.n_runs = load_end_card(results)
        self.slowest = max(t["total"] for t in self.tl.values())
        self.factor = self.slowest / RACE_S
        self._scratch = ImageDraw.Draw(Image.new("RGB", (8, 8)))
        self._sprites()
        self.race_base = self._race_base()
        self.end_frame = self._end_card()

    # sprites ----------------------------------------------------------
    def _sprites(self):
        mask = rounded_mask(TILE_W, TILE_H, TILE_R)
        self.thumbs = {}
        for cond, t in self.tl.items():
            for s in t["scenes"]:
                if s["passed"] and s["render"] and s["render"].exists():
                    im = Image.open(s["render"]).convert("RGB").resize((TILE_W, TILE_H), Image.Resampling.LANCZOS)
                    self.thumbs[(cond, s["id"])] = with_mask(im, mask)
        self.fail = rounded(TILE_W, TILE_H, TILE_R, FAIL_RED)
        d = ImageDraw.Draw(self.fail)
        f = self.F["tile"]
        draw_spaced(d, (TILE_W / 2, TILE_H / 2 - f.size * 0.62), "FAIL", f, "#ffffff", 1.5, anchor="m")
        self.outline = {k: rounded_outline(TILE_W + 8, TILE_H + 8, TILE_R + 3, c, 2) for k, c in MODEL_COLOR.items()}
        self.badges = {}
        for n in (2, 3, 4):
            text = f"attempt {n}"
            f = self.F["badge"]
            tw = self._scratch.textlength(text, font=f)
            w, h = round(tw + 16), 22
            b = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
            shadow(b, (4, 4, 4 + w, 4 + h), 11, 2, 1, 70)
            b.alpha_composite(rounded(w, h, 11, AMBER), (4, 4))
            ImageDraw.Draw(b).text((4 + w / 2, 4 + h / 2), text, font=f, fill=INK, anchor="mm")
            self.badges[n] = b
        f = self.F["status"]
        tw = sum(self._scratch.textlength(c, font=f) for c in "FINISHED") + 1.4 * 7
        w, h = round(tw + 20), 22
        self.finished = rounded(w, h, 11, CHIP)
        draw_spaced(ImageDraw.Draw(self.finished), (w / 2, h / 2 - f.size * 0.62), "FINISHED", f, INK_2, 1.4,
                    anchor="m")

    def _swatch(self, base, x, y, size, cond, r=5):
        c = config.CONDITIONS[cond]
        color = MODEL_COLOR[c.model.key]
        mask = rounded_mask(size, size, r)
        sw = rounded(size, size, r, color) if c.harness else with_mask(hatch_patch(size, size, color), mask)
        base.alpha_composite(sw, (x, y))

    def _header(self, img, subtitle):
        d = ImageDraw.Draw(img)
        d.text((W / 2, 64), TITLE, font=self.F["title"], fill=INK, anchor="mm")
        f = self.F["pill"]
        tw = d.textlength(subtitle, font=f)
        w, h = round(tw + 34), 34
        img.alpha_composite(rounded(w, h, h // 2, PILL_BG), (round(W / 2 - w / 2), 102))
        d.text((W / 2, 102 + h / 2), subtitle, font=f, fill="#ffffff", anchor="mm")
        d.text((W / 2, 1040), FOOTER, font=self.F["footer"], fill=INK_2, anchor="mm")

    def _race_base(self):
        img = Image.new("RGBA", (W, H), BG)
        for i in range(4):
            px, py = panel_origin(i)
            box = (px, py, px + PANEL_W, py + PANEL_H)
            shadow(img, box, PANEL_R, 14, 8, 34)
            shadow(img, box, PANEL_R, 2, 1, 22)
            img.alpha_composite(rounded(PANEL_W, PANEL_H, PANEL_R, CARD), (px, py))
        self._header(img, f"Run 1, replayed at {self.factor:.0f}x")
        d = ImageDraw.Draw(img)
        pending = rounded(TILE_W, TILE_H, TILE_R, PENDING)
        for i, cond in enumerate(ORDER):
            px, py = panel_origin(i)
            self._swatch(img, px + GRID_X, py + 20, 22, cond)
            d.text((px + GRID_X + 34, py + 31), config.LABELS[cond], font=self.F["label"], fill=INK, anchor="lm")
            for k in range(30):
                img.alpha_composite(pending, tile_pos(px, py, k))
            cy = py + GRID_TOP + ROWS * (TILE_H + TILE_GAP) + 18
            for j, cap in enumerate(("TIME", "WORKING", "COST")):
                draw_spaced(d, (px + GRID_X + j * GRID_W / 3, cy), cap, self.F["caps"], INK_3, 1.6)
            ty = py + PANEL_H - 26
            d.rounded_rectangle([px + GRID_X, ty, px + GRID_X + GRID_W, ty + 6], radius=3, fill=TRACK)
        return img

    # one race frame -----------------------------------------------------
    def race_frame(self, t):
        img = self.race_base.copy()
        d = ImageDraw.Draw(img)
        real = max(0.0, t - LEAD_S) * self.factor
        vid = lambda real_s: real_s / self.factor  # real seconds -> video seconds
        for i, cond in enumerate(ORDER):
            px, py = panel_origin(i)
            tl = self.tl[cond]
            key = config.CONDITIONS[cond].model.key
            color = MODEL_COLOR[key]
            now = min(real, tl["total"])
            badges, working_events = [], []
            for k, s in enumerate(tl["scenes"]):
                x, y = tile_pos(px, py, k)
                center = (x + TILE_W / 2, y + TILE_H / 2)
                end = s["ends"][-1]
                if real >= end:
                    if s["passed"]:
                        working_events.append(end)
                    sprite = self.thumbs.get((cond, s["id"])) if s["passed"] else self.fail
                    if sprite is not None:
                        a = vid(real - end) / POP_S
                        paste_scaled(img, sprite, center, 0.82 + 0.18 * ease_out_back(a), ease_out_cubic(a * 1.8))
                elif s["start"] <= real:  # the scene this setup is working on now
                    pulse = 0.75 + 0.25 * math.sin(t * 2 * math.pi * 1.2)
                    paste_scaled(img, self.outline[key], center, 1.0, pulse)
                # repair badge: "attempt N" from the end of attempt N-1 until the scene finishes
                for n, prev_end in enumerate(s["ends"][:-1], start=2):
                    stop = max(s["ends"][n - 1], prev_end + BADGE_MIN_S * self.factor)
                    if prev_end <= real < stop:
                        age, left = vid(real - prev_end), vid(stop - real)
                        badges.append((center, n, 0.6 + 0.4 * ease_out_back(age / 0.18),
                                       min(ease_out_cubic(age / 0.12), clamp01(left / 0.08))))
            for center, n, scale, alpha in badges:
                paste_scaled(img, self.badges[n], center, scale, alpha)

            # counters
            vy = py + GRID_TOP + ROWS * (TILE_H + TILE_GAP) + 38
            col = GRID_W / 3
            fv = self.F["value"]
            draw_tabular(d, (px + GRID_X, vy), clock_text(now), fv, INK)
            self._working(img, (px + GRID_X + col, vy), working_events, real)
            cost = sum(c * ease_out_cubic(vid(real - at) / COUNT_S) for at, c in tl["costs"] if at <= real)
            draw_tabular(d, (px + GRID_X + 2 * col, vy), money(cost, tl["cost_total"] < 1), fv, INK)

            ty = py + PANEL_H - 26
            frac = now / tl["total"]
            if frac > 0:
                d.rounded_rectangle([px + GRID_X, ty, px + GRID_X + max(6, frac * GRID_W), ty + 6], radius=3,
                                    fill=color)
            if real >= tl["total"]:
                a = vid(real - tl["total"]) / FINISH_S
                cx = px + GRID_X + GRID_W - self.finished.width / 2
                paste_scaled(img, self.finished, (cx, py + 31), 0.85 + 0.15 * ease_out_back(a), ease_out_cubic(a))
        return img

    def number_box(self, x, y, text):
        """The box a counter's digits occupy (digit top to digit bottom). Rolls are clipped to it."""
        fv = self.F["value"]
        _, top, _, bottom = fv.getbbox("0")
        return round(x), round(y + top), round(x + tabular_width(self._scratch, text, fv)) + 1, round(y + bottom) + 1

    def _working(self, img, xy, events, real):
        """'X/30' where the count rolls up like an odometer, clipped to the number's own box."""
        fv = self.F["value"]
        n = len(events)
        age = (real - events[-1]) / self.factor if events else 1e9
        p = ease_out_cubic(age / ROLL_S)
        d = ImageDraw.Draw(img)
        x, y = xy
        old, new = str(max(0, n - 1)), str(n)
        shown = new if p >= 1 or len(new) >= len(old) else old
        if p >= 1:
            draw_tabular(d, (x, y), new, fv, INK)
        else:
            bx0, by0, bx1, by1 = self.number_box(x, y, shown)
            patch = Image.new("RGBA", (bx1 - bx0, by1 - by0), (0, 0, 0, 0))
            pd = ImageDraw.Draw(patch)
            ink = tuple(int(INK[i:i + 2], 16) for i in (1, 3, 5))
            shift = (by1 - by0) + 2
            oy = y - by0  # text origin inside the patch
            draw_tabular(pd, (x - bx0, oy - shift * p), old, fv, ink + (round(255 * (1 - p)),))
            draw_tabular(pd, (x - bx0, oy + shift * (1 - p)), new, fv, ink + (round(255 * p),))
            img.alpha_composite(patch, (bx0, by0))  # the patch is the clip: nothing lands outside the box
        draw_tabular(d, (x + tabular_width(d, shown, fv), y), "/30", fv, INK)

    # end card -----------------------------------------------------------
    def _end_card(self):
        img = Image.new("RGBA", (W, H), BG)
        x0, x1 = 84, W - 84
        box = (x0 - 36, 168, x1 + 36, 990)
        shadow(img, box, 24, 16, 8, 30)
        img.alpha_composite(rounded(box[2] - box[0], box[3] - box[1], 24, CARD), box[:2])
        self._header(img, f"All {self.n_runs} runs")
        d = ImageDraw.Draw(img)
        draw_spaced(d, (x1, 196), f"WORKING SCRIPTS, MEAN OF {self.n_runs} RUNS", self.F["end_caps"], INK_3, 1.6,
                    anchor="r")
        row_h, top = 190, 224
        for i, cond in enumerate(ORDER):
            y = top + i * row_h
            e = self.end[cond]
            pct = int(e["pass"].rstrip("%"))
            self._swatch(img, x0, y + 9, 28, cond, r=6)
            d.text((x0 + 44, y + 23), config.LABELS[cond], font=self.F["end_label"], fill=INK, anchor="lm")
            draw_tabular(d, (x1, y - 8), e["pass"], self.F["end_pct"], INK, anchor="r")
            by, bh = y + 66, 16
            img.alpha_composite(rounded(x1 - x0, bh, bh // 2, TRACK), (x0, by))
            bw = round((x1 - x0) * pct / 100)
            c = config.CONDITIONS[cond]
            color = MODEL_COLOR[c.model.key]
            mask = rounded_mask(bw, bh, bh // 2)
            bar = rounded(bw, bh, bh // 2, color) if c.harness else with_mask(hatch_patch(bw, bh, color), mask)
            img.alpha_composite(bar, (x0, by))
            d.text((x0, by + 48), f"Total API cost, {self.n_runs} runs: ${e['cost']:.2f}", font=self.F["end_cost"],
                   fill=INK_2, anchor="lm")
        d.text((W / 2, 958), f"30 scenes per run · pass rate is the mean of {self.n_runs} runs · cost is the total",
               font=self.F["footer"], fill=INK_3, anchor="mm")
        return img

    def frame(self, t):
        race_end = LEAD_S + RACE_S + HOLD_S
        if t < race_end:
            out = self.race_frame(t)
        elif t < race_end + FADE_S:
            out = Image.blend(self.race_frame(race_end), self.end_frame, ease_out_cubic((t - race_end) / FADE_S))
        else:
            out = self.end_frame
        return out.convert("RGB")


def middle_time(r):
    """First repair badge near the midpoint, so the badge style shows in the preview."""
    mid = LEAD_S + RACE_S / 2
    starts = sorted(LEAD_S + e / r.factor for t in r.tl.values() for s in t["scenes"] for e in s["ends"][:-1])
    return next((b + 0.15 for b in starts if b >= mid - 0.5), mid)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness.race_video")
    p.add_argument("--results", default=str(config.RESULTS_DIR))
    p.add_argument("--style", choices=sorted(STYLES), default=DEFAULT_STYLE)
    p.add_argument("--stills", action="store_true", help="write start, middle and end card frames only")
    p.add_argument("--compare", action="store_true", help="middle still in every style, side by side")
    args = p.parse_args(argv)
    results = Path(args.results)
    out = results / "race_preview"
    if args.compare:
        out.mkdir(exist_ok=True)
        frames = []
        for style in sorted(STYLES):
            r = Renderer(results, style)
            t = middle_time(r)
            f = r.frame(t)
            f.save(out / f"middle_{style}.png")
            frames.append((style, f))
        label_h = 64
        sheet = Image.new("RGB", (W * len(frames) + 24 * (len(frames) - 1), H + label_h), "#ffffff")
        d = ImageDraw.Draw(sheet)
        for i, (style, f) in enumerate(frames):
            x = i * (W + 24)
            d.text((x + 8, label_h / 2), f"{style}) {STYLES[style]['name']}", font=inter(30, 700), fill=INK,
                   anchor="lm")
            sheet.paste(f, (x, label_h))
        sheet.save(out / "style_compare.png")
        print(out / "style_compare.png", f"(t={t:.2f}s)")
        return
    r = Renderer(results, args.style)
    print(f"style {args.style} ({STYLES[args.style]['name']}); slowest setup {r.slowest:.1f}s real -> "
          f"replay factor {r.factor:.2f}x, video {TOTAL_S:.1f}s")
    if args.stills:
        out.mkdir(exist_ok=True)
        for name, t in (("1_start", 0.0), ("2_middle", middle_time(r)), ("3_end_card", TOTAL_S - 1.0)):
            r.frame(t).save(out / f"{name}.png")
            print(f"{out / (name + '.png')}  (t={t:.2f}s)")
        return
    import imageio_ffmpeg
    path = results / "race_replay.mp4"
    writer = imageio_ffmpeg.write_frames(
        str(path), (W, H), fps=FPS, codec="libx264", pix_fmt_out="yuv420p", quality=None, macro_block_size=8,
        output_params=["-crf", "18", "-preset", "slow", "-profile:v", "high", "-movflags", "+faststart"])
    writer.send(None)
    n = round(TOTAL_S * FPS)
    for i in range(n):
        writer.send(r.frame(i / FPS).tobytes())
    writer.close()
    print(f"{path} ({n} frames, {n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
