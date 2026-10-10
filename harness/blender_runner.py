"""Run a generated script through wrapper_blender.py in a Blender subprocess."""
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

from .config import BLENDER_PATH, BLENDER_TIMEOUT_S, MAX_BLENDER_PROCS, WRAPPER

_BLENDER_SLOTS = threading.BoundedSemaphore(MAX_BLENDER_PROCS)
_SECRET_ENV = {"ANTHROPIC_API_KEY", "GROQ_API_KEY"}


def _child_env() -> dict:
    # Generated code runs in this process; keep API keys out of its environment.
    return {k: v for k, v in os.environ.items() if k not in _SECRET_ENV}


def _tail(text: str, n: int = 20) -> str:
    return "\n".join((text or "").strip().splitlines()[-n:])


def run_blender(script: Path, category: str, result_json: Path, render_png: Optional[Path] = None,
                timeout: float = BLENDER_TIMEOUT_S) -> dict:
    """Returns the wrapper's result dict plus blender_time_s (wall time of the Blender process)."""
    result_json = Path(result_json)
    result_json.parent.mkdir(parents=True, exist_ok=True)
    result_json.unlink(missing_ok=True)
    cmd = [BLENDER_PATH, "--background", "--factory-startup", "--python", str(WRAPPER), "--",
           "--script", str(Path(script).resolve()), "--result", str(result_json.resolve()), "--category", category]
    if render_png is not None:
        cmd += ["--render", str(Path(render_png).resolve())]

    with _BLENDER_SLOTS:
        t0 = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout,
                                  text=True, errors="replace", env=_child_env())
            output, returncode = proc.stdout, proc.returncode
        except subprocess.TimeoutExpired as exc:  # subprocess.run kills the child before raising
            timed_out = True
            output = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            returncode = None
        wall = time.monotonic() - t0

    try:
        result = json.loads(result_json.read_text())
    except (OSError, ValueError):
        result = {"passed": False, "stage": "startup", "error_type": None, "error_message": None, "traceback": None}

    if timed_out:
        if result.get("passed"):
            # Checks already passed; only the optional render ran out of time.
            result["render_error"] = f"timeout after {timeout:.0f}s"
            result["render"] = None
        else:
            result.update(passed=False, error_type="timeout", traceback=None,
                          error_message=f"Timeout: the script did not finish within {timeout:.0f} seconds "
                                        f"(stage: {result.get('stage')}).")
    elif result.get("error_type") is None and not result.get("passed"):
        result.update(error_type="blender_crash", traceback=_tail(output, 40),
                      error_message=f"Blender exited with code {returncode} before writing a result "
                                    f"(stage: {result.get('stage')}).")
    result["blender_time_s"] = round(wall, 3)
    return result
