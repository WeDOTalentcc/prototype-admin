#!/usr/bin/env python3
"""Sensor: Realtime voice provider MUST NOT reference deprecated model literal.

The string ``gpt-4o-realtime-preview`` was the OpenAI Realtime preview model
GA'd on 2024-10-01 and DEPRECATED on 2026-05-12. Any code referencing it in
a non-comment context (e.g., as a config default, env override default, test
input, or model arg) will silently 404 in production once the OpenAI runtime
removes the alias.

Canonical replacement: ``gpt-realtime`` (GA since 2025-09-08).
(``gpt-realtime-2`` is a cheaper newer iteration — also acceptable if cited
explicitly with a comment.)

Detection strategy:
- Scan all .py files under ``app/`` for the literal ``gpt-4o-realtime-preview``.
- IGNORE comment-only mentions (the canonical file documents the deprecation
  in a leading comment block; that's permitted).
- IGNORE this sensor file itself.

Mode: BLOCKING (exit 1 on any non-comment hit). Baseline 0.

Usage:
  python scripts/check_realtime_uses_canonical_model.py        # full scan
  python scripts/check_realtime_uses_canonical_model.py --json # CI machine-readable
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "app"

DEPRECATED_LITERAL = "gpt-4o-realtime-preview"
CANONICAL_LITERAL = "gpt-realtime"

# Skip this sensor file itself (it documents the deprecated literal as a target).
SELF_PATH = Path(__file__).resolve()


def _is_violation_line(line: str) -> bool:
    """Return True if line contains the deprecated literal OUTSIDE a comment.

    Strategy: find the first '#' that is not inside a string literal. Anything
    after that is comment. If the deprecated literal appears before that '#',
    it's code → violation.

    For lines without a '#' at all: any occurrence is a violation.
    """
    if DEPRECATED_LITERAL not in line:
        return False

    # Cheap heuristic: if the line, stripped of leading whitespace, starts with
    # '#', it's a pure comment line → safe.
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return False

    # If '#' appears later and the literal is to its right, it's in a comment.
    # We need to be careful about '#' inside string literals — full lexer is
    # overkill, so use a simple rule: any '#' preceded by an even count of '"'
    # and "'" is treated as comment start.
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            # Comment starts here; deprecated literal must be BEFORE i.
            return DEPRECATED_LITERAL in line[:i]
    # No comment marker → any presence is a violation.
    return True


def scan() -> list[tuple[Path, int, str]]:
    """Return list of (path, line_no, line) violations."""
    violations: list[tuple[Path, int, str]] = []
    if not APP_DIR.is_dir():
        return violations

    for py in APP_DIR.rglob("*.py"):
        if py.resolve() == SELF_PATH:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if DEPRECATED_LITERAL not in text:
            continue  # cheap skip
        for line_no, line in enumerate(text.splitlines(), start=1):
            if _is_violation_line(line):
                violations.append((py.relative_to(ROOT), line_no, line.rstrip()))
    return violations


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    violations = scan()
    if not violations:
        if as_json:
            print("[]")
        else:
            print(
                f"OK: no references to deprecated {DEPRECATED_LITERAL!r} "
                f"(canonical is {CANONICAL_LITERAL!r})."
            )
        return 0

    if as_json:
        import json

        print(
            json.dumps(
                [
                    {"path": str(p), "line": ln, "text": txt}
                    for (p, ln, txt) in violations
                ]
            )
        )
    else:
        print(
            f"FAIL: {len(violations)} reference(s) to DEPRECATED model "
            f"{DEPRECATED_LITERAL!r}.\n"
            f"OpenAI deprecated this model on 2026-05-12. Use "
            f"{CANONICAL_LITERAL!r} (GA since 2025-09-08).\n"
        )
        for path, line_no, line in violations:
            print(f"  {path}:{line_no}: {line}")
        print(
            "\nFix: replace the literal with the canonical value. "
            "If the file needs to MENTION the deprecated name (e.g., a "
            "migration note), put it in a comment line (start the line "
            "with `#`)."
        )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
