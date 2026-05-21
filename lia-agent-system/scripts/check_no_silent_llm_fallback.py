#!/usr/bin/env python3
"""
SENSOR (harness-engineering REGRA 4): detect silent fallback in LLM-touching code.

Catches the class of bugs we hit in 2026-05-20 audit:
- `analyze_company_culture` (company_culture.py:1112) — try/except returned
  `success=True` with empty strings when LLM JSON parse failed
- `get_llm_config` (llm_config.py:90) — bare `except` returned fabricated default
  config masking DB/RLS failure
- `decrypt_value` (pre-fix) — except returned ciphertext as if it were plaintext

REGRA 4 (CLAUDE.md): handlers tocando LLM/encryption/critical IO MUST fail-loud.
Returning a "success" envelope or the input value masks broken flows for days.

This sensor finds suspect patterns via AST so they can be reviewed:

  Pattern A:    try: ... except: return {"success": True, ...}
  Pattern B:    try: ... except Exception: return some_value  (in IA/LLM file)
  Pattern C:    try: llm_call() except: return template_default

Run modes:
  warn-only (default): exit 0, lists hits
  --blocking: exit 1 if any hit (use in CI to gate PRs)

Exit codes:
  0 = no hits, or hits exist but warn-only mode
  1 = hits exist + blocking mode
  2 = usage error
"""
from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


# Glob patterns identifying files that touch LLM/IA critical paths.
LLM_PATH_HINTS = (
    "llm",
    "/ai/",
    "claude",
    "gpt",
    "gemini",
    "openai",
    "anthropic",
    "wsi_question",
    "wsi_response",
    "company_culture",
    "screening",
    "wizard",
    "agent",
    "encryption",
    "decrypt",
)

# Files to skip even if they match LLM_PATH_HINTS (tests, fixtures, scripts).
SKIP_PATH_HINTS = (
    "/tests/",
    "/test_",
    "/__pycache__/",
    ".bak",
    "/scripts/check_",  # don't lint the sensors themselves
    "/migrations/",
    "/alembic/versions/",
)


@dataclass
class Violation:
    file: str
    line: int
    function: str
    pattern: str
    snippet: str


def _file_is_in_scope(path: Path) -> bool:
    s = str(path).lower()
    if any(skip in s for skip in SKIP_PATH_HINTS):
        return False
    return any(hint in s for hint in LLM_PATH_HINTS)


def _dict_declares_fallback_used(v: ast.Dict) -> bool:
    """Return True if dict literal has `"fallback_used": True` key.

    This is the canonical opt-out marker for graceful degradation that is
    NOT silent. The sensor ignores returns that declare it explicitly.
    """
    for k, val in zip(v.keys, v.values):
        if (
            isinstance(k, ast.Constant)
            and isinstance(k.value, str)
            and k.value == "fallback_used"
            and isinstance(val, ast.Constant)
            and val.value is True
        ):
            return True
    return False


def _call_declares_fallback_used(v: ast.Call) -> bool:
    """Same opt-out, but for Call(success=True, fallback_used=True, ...)."""
    for kw in getattr(v, "keywords", []):
        if kw.arg == "fallback_used" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            return True
    return False


def _node_is_success_envelope(node: ast.AST) -> bool:
    """Detect return of dict-like envelope with success=True / similar.

    Ignores returns that explicitly declare `fallback_used=True` (canonical
    opt-out for graceful degradation — not a silent fallback).
    """
    if isinstance(node, ast.Return) and node.value is not None:
        v = node.value
        # Pattern: return {"success": True, ...}
        if isinstance(v, ast.Dict):
            if _dict_declares_fallback_used(v):
                return False  # canonical declared graceful degradation
            for k, val in zip(v.keys, v.values):
                if (
                    isinstance(k, ast.Constant)
                    and isinstance(k.value, str)
                    and k.value in ("success", "ok", "status")
                ):
                    if (
                        isinstance(val, ast.Constant)
                        and val.value in (True, "success", "ok")
                    ):
                        return True
        # Pattern: return Response(success=True, ...) or similar call
        if isinstance(v, ast.Call):
            if _call_declares_fallback_used(v):
                return False  # canonical declared graceful degradation
            for kw in getattr(v, "keywords", []):
                if kw.arg in ("success", "ok") and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
    return False


def _excepthandler_is_bare(handler: ast.ExceptHandler) -> bool:
    """Bare except: or except Exception: (catches everything)."""
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name) and handler.type.id in ("Exception", "BaseException"):
        return True
    return False


def _find_violations_in_file(path: Path) -> list[Violation]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations: list[Violation] = []
    source_lines = source.splitlines()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Inspect Try blocks inside this function
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Try):
                continue
            for handler in inner.handlers:
                if not _excepthandler_is_bare(handler):
                    continue
                # Look at returns inside the handler body
                for stmt in ast.walk(handler):
                    if _node_is_success_envelope(stmt):
                        line_no = getattr(stmt, "lineno", handler.lineno)
                        snippet = source_lines[line_no - 1].strip() if 0 < line_no <= len(source_lines) else "<n/a>"
                        violations.append(
                            Violation(
                                file=str(path),
                                line=line_no,
                                function=node.name,
                                pattern="bare-except-returns-success-envelope",
                                snippet=snippet[:120],
                            )
                        )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect silent LLM fallback patterns (REGRA 4)."
    )
    parser.add_argument(
        "--root",
        default="app",
        help="Root dir to scan (default: app/).",
    )
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 if violations found (use in CI). Default: warn-only.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Error: --root {root} does not exist", file=sys.stderr)
        return 2

    all_violations: list[Violation] = []
    for py_file in root.rglob("*.py"):
        if not _file_is_in_scope(py_file):
            continue
        all_violations.extend(_find_violations_in_file(py_file))

    if not all_violations:
        print("✅ No silent LLM-fallback patterns detected (REGRA 4 holds).")
        return 0

    print(
        f"⚠️  {len(all_violations)} silent-fallback pattern(s) detected in "
        f"LLM-touching code.\n\n"
        f"REGRA 4 (CLAUDE.md): handlers tocando LLM MUST fail-loud. Returning\n"
        f"a 'success' envelope on except masks broken flows for days.\n"
        f"\n"
        f"How to fix each hit:\n"
        f"  1. Use app.shared.llm.safe_response.safe_llm_with_flag() helper\n"
        f"     which returns an explicit envelope WITH fallback_used flag.\n"
        f"  2. OR raise an explicit HTTPException(503, 'LLM service unavailable').\n"
        f"  3. OR log + return None/empty list (so caller's None-check handles it).\n"
        f"\n"
        f"Violations:\n"
    )
    for v in all_violations:
        print(f"── {v.file}:{v.line} in {v.function}()")
        print(f"   pattern: {v.pattern}")
        print(f"   snippet: {v.snippet}")
        print()

    return 1 if args.blocking else 0


if __name__ == "__main__":
    sys.exit(main())
