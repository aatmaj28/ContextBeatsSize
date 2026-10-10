"""Code block extraction and static AST safety check."""
import ast
from typing import NamedTuple, Optional

from .config import ALLOWED_IMPORTS, BANNED_CALLS

PYTHON_LANGS = {"python", "python3", "py"}


class Extracted(NamedTuple):
    code: Optional[str]       # first complete ```python block, else first complete unlabeled ``` block
    partial: Optional[str]    # body of an unclosed block (reply cut off by max_tokens); repair context only
    unlabeled: Optional[bool] # True if the block had no language tag; None when there is no block


def _fenced_blocks(reply: str):
    """Yield (lang, body, closed) for each ``` fenced block, scanning line by line."""
    blocks, lang, lines = [], None, []
    for line in (reply or "").splitlines():
        s = line.strip()
        if lang is None:
            if s.startswith("```"):
                info = s[3:].strip().split()
                lang, lines = (info[0].lower() if info else ""), []
        elif s == "```":
            blocks.append((lang, "\n".join(lines), True))
            lang = None
        else:
            lines.append(line)
    if lang is not None:
        blocks.append((lang, "\n".join(lines), False))
    return blocks


def extract_code(reply: str) -> Extracted:
    blocks = [b for b in _fenced_blocks(reply) if b[0] in PYTHON_LANGS or b[0] == ""]
    for want_unlabeled in (False, True):
        for lang, body, closed in blocks:
            if closed and (lang == "") == want_unlabeled:
                return Extracted(body.rstrip() + "\n", None, want_unlabeled)
    open_blocks = [b for b in blocks if not b[2]]
    if open_blocks:
        return Extracted(None, open_blocks[-1][1], open_blocks[-1][0] == "")
    return Extracted(None, None, None)


def safety_check(code: str) -> Optional[str]:
    """Return None if the script is allowed, else a one-line reason (fail type unsafe_code)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None  # not a safety problem; Blender reports the SyntaxError with a traceback
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in ALLOWED_IMPORTS:
                    return f"line {node.lineno}: import of '{alias.name}' is not allowed (allowed: {', '.join(sorted(ALLOWED_IMPORTS))})"
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                return f"line {node.lineno}: relative imports are not allowed"
            top = (node.module or "").split(".")[0]
            if top not in ALLOWED_IMPORTS:
                return f"line {node.lineno}: import from '{node.module}' is not allowed (allowed: {', '.join(sorted(ALLOWED_IMPORTS))})"
        elif isinstance(node, ast.Name) and node.id in BANNED_CALLS | {"__builtins__"}:
            return f"line {node.lineno}: use of '{node.id}' is not allowed"
    return None
