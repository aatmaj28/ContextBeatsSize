"""Models, prices, paths, conditions and prompts. Single source of truth for the experiment."""
import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# ---------------------------------------------------------------- paths
SCENES_FILE = ROOT / "scenes.json"
CHEATSHEET_FILE = ROOT / "cheatsheet.md"
RESULTS_DIR = ROOT / "results"
RUNS_LOG = RESULTS_DIR / "runs.jsonl"
SCRIPTS_DIR = RESULTS_DIR / "scripts"
RENDERS_DIR = RESULTS_DIR / "renders"
SELFTEST_DIR = ROOT / "selftest_scripts"
WRAPPER = ROOT / "harness" / "wrapper_blender.py"

BLENDER_PATH = os.environ.get("BLENDER_PATH") or "/Applications/Blender.app/Contents/MacOS/Blender"
MAX_SPEND_USD = float(os.environ.get("MAX_SPEND_USD") or 35)

# ---------------------------------------------------------------- limits
MAX_TOKENS = 16000
BLENDER_TIMEOUT_S = 180
MAX_BLENDER_PROCS = 2
API_MAX_RETRIES = 5
HARNESS_MAX_ATTEMPTS = 4  # 1 attempt + up to 3 repairs
TRACEBACK_LINES = 40
HAIKU_PRICE_TIER_LIMIT = 100_000  # Haiku price is higher above this; we assert far below it
PROMPT_TOKEN_ASSERT = 50_000      # "far below" 100k

ALLOWED_IMPORTS = {"bpy", "bmesh", "mathutils", "math", "random", "colorsys", "bpy_extras"}
BANNED_CALLS = {"exec", "eval", "open", "compile", "__import__"}

# Columns in comparison_grid.png (8 scenes across categories). Override with --grid-scenes.
GRID_SCENES = [1, 5, 11, 12, 13, 21, 23, 27]


# ---------------------------------------------------------------- models
@dataclass(frozen=True)
class Model:
    key: str
    provider: str          # "anthropic" | "groq"
    model_id: str
    price_in: float        # USD per million input tokens
    price_out: float       # USD per million output tokens (thinking/reasoning billed as output)


MODELS = {
    "opus": Model("opus", "anthropic", "claude-opus-5-5", 4.00, 20.00),
    "haiku": Model("haiku", "anthropic", "claude-haiku-5-5", 0.10, 0.50),
    "gptoss120b": Model("gptoss120b", "groq", "openai/gpt-oss-120b", 0.15, 0.60),
}


@dataclass(frozen=True)
class Condition:
    id: str
    model: Model
    harness: bool

    @property
    def max_attempts(self) -> int:
        return HARNESS_MAX_ATTEMPTS if self.harness else 1


CONDITIONS = {
    c.id: c
    for c in [
        Condition("opus_bare", MODELS["opus"], False),
        Condition("opus_harness", MODELS["opus"], True),
        Condition("haiku_bare", MODELS["haiku"], False),
        Condition("haiku_harness", MODELS["haiku"], True),
        Condition("gptoss120b_bare", MODELS["gptoss120b"], False),
        Condition("gptoss120b_harness", MODELS["gptoss120b"], True),
    ]
}
CORE_CONDITIONS = ["opus_bare", "opus_harness", "haiku_bare", "haiku_harness"]
GROQ_CONDITIONS = ["gptoss120b_bare", "gptoss120b_harness"]

LABELS = {
    "opus_bare": "Opus 5.5 bare",
    "opus_harness": "Opus 5.5 + harness",
    "haiku_bare": "Haiku 5.5 bare",
    "haiku_harness": "Haiku 5.5 + harness",
    "gptoss120b_bare": "gpt-oss-120b bare",
    "gptoss120b_harness": "gpt-oss-120b + harness",
}


def cost_usd(model: Model, input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * model.price_in + output_tokens * model.price_out) / 1_000_000


def worst_case_cost(model: Model, prompt_chars: int) -> float:
    """Upper bound for one call, used by the budget guard before spending."""
    est_in = prompt_chars // 2 + 500  # deliberately pessimistic (real ratio is ~3.5-4 chars/token)
    return cost_usd(model, est_in, MAX_TOKENS)


# ---------------------------------------------------------------- prompts
SYSTEM_PROMPT = """You write Python scripts for Blender 5.2 (bpy).
The script runs in background mode in an empty scene.
Build the complete scene: geometry, materials, lighting, and a camera.
Set bpy.context.scene.camera to a camera that frames the subject well.
For animations, set scene.frame_start and scene.frame_end.
Do not render, save, or export anything.
Only import: bpy, bmesh, mathutils, math, random, colorsys, bpy_extras.
Reply with exactly one ```python code block and nothing else."""

HARNESS_PREFIX = """Blender 5.x API notes. Your training data may contain older Blender API patterns. When they conflict, follow these notes over your memory."""


def system_prompt(harness: bool) -> str:
    if not harness:
        return SYSTEM_PROMPT
    cheatsheet = CHEATSHEET_FILE.read_text().strip()
    return f"{SYSTEM_PROMPT}\n\n{HARNESS_PREFIX}\n\n{cheatsheet}"


def task_message(scene_prompt: str) -> str:
    return f"Scene: {scene_prompt}"


def repair_message(scene_prompt: str, previous_script: str, error: str) -> str:
    return (
        f"Scene: {scene_prompt}\n\n"
        "Your previous script failed in Blender 5.2.\n\n"
        f"Script:\n```python\n{previous_script}\n```\n\n"
        f"Error:\n{error}\n\n"
        "Return the full corrected script."
    )


def load_scenes() -> list:
    return json.loads(SCENES_FILE.read_text())
