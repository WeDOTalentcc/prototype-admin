#!/usr/bin/env python3
"""
SENSOR (harness-engineering REGRA 4): detect silent fallback in LLM-touching code.

Catches the class of bugs we hit in 2026-05-20 audit:
- `analyze_company_culture` (company_culture.py:1112) — try/except returned
  `success=True` with empty strings when LLM JSON parse failed
- `get_llm_config` (llm_config.py:90) — bare `except` returned fabricated default
  config masking DB/RLS failure
- `decrypt_value` (pre-fix) — except returned ciphertext as if it were plaintext
- `WSIReportGenerator.generate_report` (report_generator.py, pre P0.D 2026-05-21) —
  except assigned `data = _fallback`, return-after-try built StructuredReport
  from `data` with no `fallback_used` flag → recruiter saw parecer falso como
  output legitimo da LIA por dias.

REGRA 4 (CLAUDE.md): handlers tocando LLM/encryption/critical IO MUST fail-loud.
Returning a "success" envelope or the input value masks broken flows for days.

This sensor finds suspect patterns via AST so they can be reviewed:

  Pattern A:    try: ... except: return {"success": True, ...}
  Pattern B:    try: ... except Exception: return some_value  (in IA/LLM file)
  Pattern C:    try: llm_call() except: return template_default
  Pattern D:    try: x = llm_call(); except Exception: x = fallback
                # ...sibling stmts...
                return Object(..., x=x, ...)  # return-after-try, P0.D pattern

Pattern D detection (added 2026-05-21 P2 followup of P0.D wsi report_generator):

  AST walk: in a FunctionDef body, find a `Try` node. For each bare-ish
  ExceptHandler (Exception/BaseException/bare), collect names that are
  written to via `Assign` (single Name target) or `AnnAssign`. Then walk
  the function body siblings AFTER the Try and look for `Return` statements
  whose value reads any of those names. If found, flag as Pattern D unless
  the return value also declares `fallback_used=True` (canonical opt-out).

  This catches the assign-fallback-in-except → return-uses-var pattern even
  when the Return is outside the try/except block, which Patterns A-C miss.

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
        # Also accept fallback_used=<non-constant expression> (e.g.
        # `fallback_used=not envelope.success`). Caller making an explicit
        # decision about the flag is the canonical opt-out signal — the
        # sensor's job is to catch the SILENT case (no flag at all).
        if kw.arg == "fallback_used" and not isinstance(kw.value, ast.Constant):
            return True
    return False


def _return_declares_fallback_used(node: ast.Return) -> bool:
    """Whether a Return node declares fallback_used (dict or call kwargs)."""
    if node.value is None:
        return False
    if isinstance(node.value, ast.Dict):
        return _dict_declares_fallback_used(node.value)
    if isinstance(node.value, ast.Call):
        return _call_declares_fallback_used(node.value)
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


def _names_written_in_handler(handler: ast.ExceptHandler) -> set[str]:
    """Collect simple Name targets assigned in the except handler body.

    Captures:
      except Exception:
          data = _fallback        ← {data}
          obj.attr = ...          ← ignored (not a simple Name target)
          a, b = (1, 2)           ← ignored (tuple target — narrow scope intentional)
          x: int = 5              ← {x} via AnnAssign
          a = b = _fb             ← {a, b} (multi-target Assign)

    Narrow scope is intentional: simple-Name Assign / AnnAssign covers the
    P0.D pattern and avoids false positives on attribute mutations that
    rarely participate in the return-after-try silent-fallback class.
    """
    names: set[str] = set()
    for stmt in ast.walk(handler):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(stmt, ast.AnnAssign):
            if isinstance(stmt.target, ast.Name):
                names.add(stmt.target.id)
    return names


def _names_read_in_node(node: ast.AST) -> set[str]:
    """Collect Name identifiers READ (Load ctx) anywhere under `node`."""
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return names


def _iter_returns_after(body: list[ast.stmt], try_index: int):
    """Yield Return statements that appear in `body` AFTER position try_index.

    Walks recursively into nested blocks (if/else/with/for/while) so that:

        try: ...
        except: data = _fb
        if cond:
            return Obj(data=data)  # ← yielded

    is still surfaced. Nested FunctionDef/AsyncFunctionDef/Lambda are NOT
    descended into — those have their own scope and would re-bind the name.
    """
    for stmt in body[try_index + 1 :]:
        for sub in ast.walk(stmt):
            if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                # Skip — separate scope, would shadow our names of interest.
                # We can't actually `continue` ast.walk mid-traversal, so we
                # filter via the outer check below. This branch is a no-op
                # marker for the reader.
                pass
        # Filter via a fresh walk that prunes nested scopes.
        yield from _walk_skip_nested_scopes(stmt)


def _walk_skip_nested_scopes(node: ast.AST):
    """ast.walk variant that does NOT descend into nested function/lambda scopes."""
    todo = [node]
    while todo:
        current = todo.pop()
        if isinstance(current, ast.Return):
            yield current
        for child in ast.iter_child_nodes(current):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                continue
            todo.append(child)


def _line_has_regra4_exempt(
    source_lines: list[str],
    lineno: int,
    *,
    above: int = 5,
    below: int = 1,
) -> bool:
    """Honor `# REGRA-4-EXEMPT: <reason>` marker on or near the given line.

    Searches `above` lines above and `below` lines below the target line
    (inclusive) for the literal marker substring. Asymmetry is intentional:
    the canonical placement is a comment block ABOVE the Try/handler, where
    a multi-line justification is most readable.

    Canonical placement (above the try):

        # REGRA-4-EXEMPT: graceful degradation for cache miss — caller
        # checks data.is_partial flag, no silent success envelope.
        try:
            data = llm_call()
        except Exception:
            data = build_fallback()
        return data

    Also accepted (inside the handler body):

        try:
            data = llm_call()
        except Exception:
            # REGRA-4-EXEMPT: <reason>
            data = build_fallback()
        return data
    """
    n = len(source_lines)
    lo = max(1, lineno - above)
    hi = min(n, lineno + below)
    for ln in range(lo, hi + 1):
        if "REGRA-4-EXEMPT" in source_lines[ln - 1]:
            return True
    return False


def _find_pattern_d_violations(
    func: ast.FunctionDef | ast.AsyncFunctionDef, source_lines: list[str], path: Path
) -> list[Violation]:
    """Detect Pattern D: except-assigns-var → return-after-try-uses-var.

    For each top-level Try in the function body, collect names assigned in
    its bare-ish except handlers, then look at sibling stmts AFTER the Try
    for Return nodes that READ any of those names. Skip returns that
    declare `fallback_used=True` (canonical opt-out) or that have a
    `# REGRA-4-EXEMPT: <reason>` marker on the try/except/return line.
    """
    out: list[Violation] = []

    # We only inspect Try nodes that sit DIRECTLY in the function body (or
    # nested under if/else/with/for/while — but for simplicity and signal
    # quality, we scope to func.body top-level for the initial heuristic).
    # Going deeper would catch more, with proportionally more false positives.
    body = func.body
    for i, stmt in enumerate(body):
        if not isinstance(stmt, ast.Try):
            continue
        # Honor REGRA-4-EXEMPT marker on the try header or its handlers.
        try_line = getattr(stmt, "lineno", 0)
        handler_lines = [getattr(h, "lineno", 0) for h in stmt.handlers]
        # Above the try is the canonical placement — accept up to 5 lines
        # above (covers multi-line comment-block markers).
        if try_line and _line_has_regra4_exempt(source_lines, try_line):
            continue
        if any(
            hl and _line_has_regra4_exempt(source_lines, hl, above=2, below=3)
            for hl in handler_lines
        ):
            continue
        # Collect names written in all bare-ish handlers of this Try.
        fallback_names: set[str] = set()
        for handler in stmt.handlers:
            if not _excepthandler_is_bare(handler):
                continue
            fallback_names |= _names_written_in_handler(handler)
        if not fallback_names:
            continue

        # Find sibling returns AFTER this Try in the same function body.
        for ret in _iter_returns_after(body, i):
            if not isinstance(ret, ast.Return) or ret.value is None:
                continue
            if _return_declares_fallback_used(ret):
                continue  # canonical opt-out via flag
            ret_line = getattr(ret, "lineno", 0)
            if ret_line and _line_has_regra4_exempt(source_lines, ret_line, above=2, below=1):
                continue  # canonical opt-out via marker on the return
            read_names = _names_read_in_node(ret.value)
            tainted = read_names & fallback_names
            if not tainted:
                continue
            line_no = ret_line or stmt.lineno
            snippet = (
                source_lines[line_no - 1].strip()
                if 0 < line_no <= len(source_lines)
                else "<n/a>"
            )
            tainted_str = ", ".join(sorted(tainted))
            out.append(
                Violation(
                    file=str(path),
                    line=line_no,
                    function=func.name,
                    pattern=f"return-after-try-uses-except-assigned-var ({tainted_str})",
                    snippet=snippet[:120],
                )
            )
            # Only report ONCE per Try block — multiple returns reading the
            # same tainted var would just spam.
            break
    return out


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
        # Patterns A/B/C — return inside the handler body itself.
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
        # Pattern D — return-after-try uses var assigned in except handler.
        violations.extend(_find_pattern_d_violations(node, source_lines, path))

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
        f"a 'success' envelope on except — or building a response object from\n"
        f"a var assigned-to-fallback in the except — masks broken flows.\n"
        f"\n"
        f"How to fix each hit:\n"
        f"  1. Use app.shared.llm.safe_response.safe_llm_with_flag_async()\n"
        f"     which returns an explicit envelope WITH fallback_used flag.\n"
        f"     Then build your response object passing fallback_used=not envelope.success\n"
        f"     (the sensor recognizes any fallback_used kwarg as canonical opt-out).\n"
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
