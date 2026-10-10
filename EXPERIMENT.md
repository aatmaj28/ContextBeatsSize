# Blender AI Race: cheat sheet vs bigger model

## Goal
Test whether a small model inside a good harness (an API cheat sheet plus an error repair loop) writes working Blender 5.2 scripts more reliably and far more cheaply than a frontier model working cold. The results go into a LinkedIn post, so every number must be logged and reproducible.

## Why Blender 5.2
- Claude Opus 5.5 and Claude Haiku 5.5 both have a June 2026 knowledge cutoff. Blender 5.2 LTS shipped in July 2026.
- Blender 5.0 made many breaking Python API changes (for example `scene.node_tree` and `action.fcurves` were removed, and `use_nodes` was deprecated on scene, world and material). Blender 5.2 changed how Geometry Nodes modifier properties are accessed.
- Most bpy code online predates these changes, so models tend to write code for an older Blender ("version blending").

## Contestants (2x2)
| id | model | harness |
|---|---|---|
| opus_bare | claude-opus-5-5 | none: one attempt, no cheat sheet |
| opus_harness | claude-opus-5-5 | cheat sheet + up to 3 repair attempts (4 attempts max) |
| haiku_bare | claude-haiku-5-5 | none: one attempt, no cheat sheet |
| haiku_harness | claude-haiku-5-5 | cheat sheet + up to 3 repair attempts (4 attempts max) |

Optional, behind `--include-groq`: `gptoss120b_bare` and `gptoss120b_harness` using `openai/gpt-oss-120b` on Groq.

## Fairness rules
- Identical system prompt and task message for every condition. Harness conditions only add the cheat sheet (appended to the system prompt) and repair requests.
- Every condition is told the target is Blender 5.2.
- The cheat sheet comes only from the official Blender 5.0, 5.1 and 5.2 release notes, using these pages for each version: Python API, Compositor, Rendering, Animation & Rigging, and Geometry Nodes. General API changes only, never scene specific solutions. Every statement must be true on Blender 5.2.2. Stating a change is fine (for example, Glare options are now input sockets), but code examples must never be a working setup that matches a scene in scenes.json: they use neutral nodes and names (for example Blur, MyGroup, Value, Cube). Keep it under about 2,500 words. List the source URLs at the top.
- Same `max_tokens` (16000) for every call. No prompt caching. Do not set temperature, top_p, top_k, thinking or tool_choice. Defaults only.
- Interleave conditions per scene. Never run all of one condition first.
- 3 independent runs per condition. Report the mean and the min to max range.

## API notes (verified Oct 9, 2026; your own training data may predate these, so follow this section)
- Model IDs: `claude-opus-5-5`, `claude-haiku-5-5`. Use the `anthropic` Python SDK and `client.messages.create`.
- Opus 5.5: thinking is always on and cannot be disabled, forced tool use returns an error, and thinking blocks are tied to the model and conversation. So: no tools, no thinking parameter, and read only content blocks whose type is `text`.
- Thinking tokens are billed as output tokens. Compute cost from `response.usage`.
- Prices per million tokens (standard API): Opus 5.5 is $4 input and $20 output. Haiku 5.5 is $0.10 input and $0.50 output for prompts up to 100,000 tokens (higher above that; assert every prompt is far below 100,000 tokens).
- Groq (optional): `groq` SDK, OpenAI style chat completions. `openai/gpt-oss-120b` is $0.15 input and $0.60 output per million tokens. Developer plan limits are about 1K requests and 250K tokens per minute; the free tier is lower, so back off on 429.
- Repair attempts are fresh, stateless requests (task + previous script + error). Not multi turn conversations. This avoids passing thinking blocks around and keeps cost predictable.
- Retry API errors (429, 5xx, overloaded) with exponential backoff, max 5 retries. These retries do not count as attempts, and their latency is not counted.

## Prompts
System prompt (all conditions):
~~~
You write Python scripts for Blender 5.2 (bpy).
The script runs in background mode in an empty scene.
Build the complete scene: geometry, materials, lighting, and a camera.
Set bpy.context.scene.camera to a camera that frames the subject well.
For animations, set scene.frame_start and scene.frame_end.
Do not render, save, or export anything.
Only import: bpy, bmesh, mathutils, math, random, colorsys, bpy_extras.
Reply with exactly one ```python code block and nothing else.
~~~

Harness addition (appended to the system prompt):
~~~
Blender 5.x API notes. Your training data may contain older Blender API patterns. When they conflict, follow these notes over your memory.

<full contents of cheatsheet.md>
~~~

Task message:
~~~
Scene: <prompt from scenes.json>
~~~

Repair message (harness conditions only):
~~~
Scene: <prompt from scenes.json>

Your previous script failed in Blender 5.2.

Script:
```python
<previous script>
```

Error:
<last 40 lines of the traceback, or the failed check message>

Return the full corrected script.
~~~

## Running scripts in Blender
- Blender path comes from env `BLENDER_PATH`.
- Command: `<BLENDER_PATH> --background --factory-startup --python harness/wrapper_blender.py -- --script <file> --result <json> --category <cat> [--render <png>]`
- `wrapper_blender.py` (runs inside Blender): reset to an empty scene, exec the generated script inside try/except, capture the traceback, run the pass checks, optionally render, and write a result JSON: `passed, stage, error_type, error_message, traceback`.
- Timeout: 180 seconds per Blender call. A timeout is a fail with error_type `timeout`.
- At most 2 Blender processes at once.
- Before running: static AST check. Reject imports outside the allowlist and calls to exec, eval, open, compile or `__import__`. Fail type `unsafe_code`, fed back like any other error.
- No python code block in the reply is a fail with type `no_code` (also record when `stop_reason` is `max_tokens`). An unlabeled ``` code block is accepted when there is no ```python block, and logged with `code_block_unlabeled: true`.

## Pass checks
Every scene: the script ran without an exception, `scene.camera` is set, and there is at least one visible geometry object (MESH, CURVE, FONT, SURFACE or META).

Extra checks by category (from scenes.json):
- `anim`: something actually animates. Compare object world matrices and light energies between `frame_start` and the middle frame using `scene.frame_set`. If those match, also compare the quarter and three-quarter frames, so periodic motion that lines up at the middle frame is not a false fail.
- `gn`: at least one object has a Geometry Nodes modifier with a node group assigned, and that group has at least one input besides Geometry.
- `compositor`: the scene has a compositor node tree containing at least one effect node beyond input and output nodes.
- `world`: the scene world has a node setup with at least one node beyond the default background and output.
- `materials`: at least one geometry object has a material assigned.
- `basic`: no extra checks.

Important: the checks and the wrapper must themselves use the correct Blender 5.2 API. Look up the 5.2 docs for how compositor node trees attach to a scene and how world and material nodes work after the 5.0 changes. Do not trust memory. The selftest proves the checks work.

## Rendering
- Render only in run 1, and only for passing attempts. Runs 2 and 3 are pass or fail only.
- The wrapper applies render settings after the script runs (overriding the script): Cycles, CPU, 640x360, 32 samples, denoising on. For `anim` scenes render the middle frame.
- Save to `results/renders/<condition>/<scene_id>.png`.

## Logging
- Append one JSON line per attempt to `results/runs.jsonl`: timestamp, run, condition, model, scene_id, category, attempt, input_tokens, output_tokens, cost_usd, api_latency_s, blender_time_s, stop_reason, passed, error_type, error_message (first line only).
- Save every script to `results/scripts/<run>/<condition>/<scene_id>_a<attempt>.py`.
- Resume: skip (run, condition, scene) combos already finished in runs.jsonl, so a crash never wastes money.
- Budget guard: env `MAX_SPEND_USD` (default 35). Track cumulative spend from runs.jsonl and stop cleanly before going over.

## Metrics (`harness/report.py`)
Per condition, mean and min to max across runs:
- final pass rate, first attempt pass rate, average attempts used
- total cost, cost per working scene
- average time per scene (API latency + Blender check time, across all attempts)
- pass rate by category
- top 5 error messages (normalize numbers and object names so similar errors group together)

Outputs in `results/`:
- `summary.md`: all the tables above
- `chart.png`: pass rate bar per condition, with total cost labeled on each bar
- `comparison_grid.png`: rows are the 4 conditions, columns are 8 scenes picked across categories (configurable). Render tile for passes, red tile with a short error text for fails. At least 1600 px wide so it reads well on LinkedIn.
- `post_numbers.md`: plain lines like "Haiku + harness: X% working scripts, $Y total", plus the cost ratio, speed ratio and pass rate gap between `haiku_harness` and `opus_bare`

## CLI
- `python -m harness.selftest`: no API calls. Runs the wrapper and checks on hand written, known good Blender 5.2 scripts in `selftest_scripts/` (one per category). If one fails, fix it using the 5.2 docs until all pass.
- `python -m harness.run --runs 3 [--scenes 1,12,21,23] [--conditions opus_bare,haiku_harness] [--include-groq] [--concurrency 4]`
- `python -m harness.report`

## Project layout
~~~
blender-ai-race/
  EXPERIMENT.md
  scenes.json
  cheatsheet.md          generated, then reviewed by a human
  .env                   never commit
  .gitignore             .env and .venv
  requirements.txt       anthropic, groq, python-dotenv, pillow, matplotlib
  harness/
    __init__.py
    config.py            models, prices, paths, conditions
    llm.py               Anthropic + Groq calls, retries, cost, budget guard
    extract.py           code block extraction + AST safety check
    blender_runner.py    subprocess call, timeout, parallel limit
    wrapper_blender.py   runs inside Blender: reset, exec, checks, render
    run.py               main loop, resume, logging
    selftest.py
    report.py
  selftest_scripts/
  results/
~~~

## Ground rules for Claude Code
- This is a Mac (zsh). Use pathlib. Create the venv with `python3 -m venv .venv` and call `.venv/bin/python` directly. Blender lives at `/Applications/Blender.app/Contents/MacOS/Blender` unless `.env` says otherwise. If macOS blocks anything (for example a Gatekeeper prompt on first Blender launch), stop and tell me.
- Read `ANTHROPIC_API_KEY`, `GROQ_API_KEY`, `BLENDER_PATH` and `MAX_SPEND_USD` from `.env`. Never print or log keys.
- Write `cheatsheet.md` yourself by fetching the official Blender 5.0, 5.1 and 5.2 release notes pages listed in the fairness rules (for example https://developer.blender.org/docs/release_notes/5.0/python_api/ and https://developer.blender.org/docs/release_notes/5.2/compositor/). If you can't fetch them, tell me and I'll save the pages into the folder.
- Do not commit or push. I handle git.
- Ask me before any step that spends API money.
- Order of work, stopping at each checkpoint:
  1. Setup and project layout, then `selftest` (free).
  2. Write `cheatsheet.md`, then stop for my review.
  3. Smoke test: scenes 1, 12, 21 and 23, all 4 conditions, 1 run (about $1 to $2). Run `report`, show me `summary.md` and `comparison_grid.png`, then stop.
  4. I run the full experiment myself in a terminal.
