#!/usr/bin/env python3
"""Sensor: alembic migrations + service SQL MUST NOT join UUID vs VARCHAR without CAST.

Canonical-fix harness (registered 2026-05-22 after migration 161 P0)
====================================================================

PostgreSQL has NO implicit cast between UUID and varchar/text. A JOIN like
``WHERE varchar_col = uuid_col`` fails with::

    operator does not exist: character varying = uuid

This sensor detects the anti-pattern in:

- ``alembic/versions/*.py`` (migration backfills joining ID columns)
- ``app/domains/**/repositories/**/*.py`` (queries cross-FK)
- ``app/domains/**/services/**/*.py`` (any raw SQL inline; ADR-001
  technically forbids this but Caminho C exemptions exist)

Canonical fix patterns (always-safe):

1. ``<varchar_col> = <uuid_col>::text`` (cast UUID → text; matches if
   varchar stores valid UUID string).
2. ``<varchar_col> ~ '^[0-9a-fA-F-]{36}$' AND <varchar_col>::uuid =
   <uuid_col>`` (format-validate varchar before casting; rejects
   malformed values safely).

Both patterns appear in migrations 161 (post-fix), 166. Pattern 1 is
simpler; pattern 2 is more defensive for legacy data.

Heuristic detection (regex-based — fast, low false-positive rate for
this specific anti-pattern):

- Looks for ``=`` comparisons in JOINs where one side ends in ``_id``
  or is ``id`` (likely UUID) and the other side is a *_id column AND
  NEITHER side has ``::uuid``, ``::text``, ``::varchar``, or a
  ``~ '^[0-9a-fA-F`` format-validation pattern in the same WHERE clause.

Allowlist:
- Files marked ``# CANONICAL-FIX-EXEMPT: <reason>`` on the same line.
- Tests directory (``tests/``).

Mode:
- Default: WARN-ONLY (exit 0; reports violations to stdout).
  Reason: regex-based detection cannot distinguish UUID-vs-UUID joins
  (safe) from VARCHAR-vs-UUID joins (the bug). Baseline of legitimate
  FK joins (~75 hits on 2026-05-22) needs triage before promoting to
  BLOCKING. Cross-reference DB schema via ``information_schema.columns``
  is the canonical follow-up — sprint dedicated.
- Use ``--block`` to enforce in CI (exit 1 on any violation). Recommended
  for migrations-only scope (``--scope=migrations``).

Usage::

    python scripts/check_no_uuid_varchar_join.py                # warn-only
    python scripts/check_no_uuid_varchar_join.py --block        # blocking
    python scripts/check_no_uuid_varchar_join.py --scope=migrations --block

"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (
    ROOT / "alembic" / "versions",
    ROOT / "app" / "domains",
)
EXCLUDE_DIRS = ("__pycache__", "tests", ".venv", "node_modules")

# Anti-pattern: `<table>.<col_ending_in_id> = <table>.<col_ending_in_id>`
# without nearby cast or format validation marker.
#
# Column name regex matches:
#  - exact "id" (3-letter form: `t.id`)
#  - any *_id form (`related_job_id`, `candidate_id`, `user_id`)
#
JOIN_PATTERN = re.compile(
    r"""
    (?P<lhs>
        \b[a-zA-Z_][a-zA-Z0-9_]*       # table alias / name
        \.
        (?:id|[a-zA-Z_][a-zA-Z0-9_]*_id)\b
    )
    \s*=\s*
    (?P<rhs>
        \b[a-zA-Z_][a-zA-Z0-9_]*
        \.
        (?:id|[a-zA-Z_][a-zA-Z0-9_]*_id)\b
    )
    """,
    re.VERBOSE,
)

# Safe cast / validation markers (presence anywhere in the same SQL text block
# suppresses the warning for that block)
SAFE_MARKERS = (
    "::text",
    "::uuid",
    "::varchar",
    "::character varying",
    "~ '^[0-9a-fA-F",        # format validation regex (UUID-like)
    "CANONICAL-FIX-EXEMPT",
    # PostgreSQL system catalog tables — all use `oid` type, intra-catalog
    # joins are always same-type-safe. If present anywhere in the block,
    # treat as catalog query (false-positive prone).
    "pg_constraint",
    "pg_class",
    "pg_namespace",
    "pg_attribute",
    "pg_index",
    "pg_indexes",
    "pg_catalog",
    "information_schema",
)

# Patterns that, in JOIN context, are confidently same-type (skip).
# Either both sides reference the same column name (typical FK join with
# matching types) OR both sides are clearly non-tenant ID joins.
SAME_COL_NAME_RE = re.compile(
    r"\b\w+\.(?P<col>\w+id)\s*=\s*\w+\.(?P=col)\b"
)


def _iter_python_files(roots: tuple[Path, ...]) -> Iterator[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            yield path


def _find_sql_blocks(source: str) -> list[tuple[int, str, str]]:
    """Return list of (start_line, block_text, context_window) for each
    triple-quoted SQL block.

    ``context_window`` is the surrounding source text (up to 5 lines before
    and after the block) — used to detect ``# CANONICAL-FIX-EXEMPT`` Python
    comments that suppress the check for an adjacent SQL string.

    We only check triple-quoted strings because that's where multi-line SQL
    lives. Single-line SQL like ``conn.execute(sa.text("SELECT 1"))`` is rare
    and usually doesn't have JOIN patterns.
    """
    blocks: list[tuple[int, str, str]] = []
    source_lines = source.splitlines()
    # Find triple-quoted strings (either """ or ''')
    triple_re = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)
    for match in triple_re.finditer(source):
        block_text = match.group(2)
        # Heuristic: only consider blocks that look like SQL
        if not re.search(r"\b(SELECT|UPDATE|INSERT|DELETE|FROM|JOIN|WHERE)\b",
                         block_text, re.IGNORECASE):
            continue
        start_line = source[: match.start()].count("\n") + 1
        # Build context window: 5 lines before + block lines + 2 after
        end_line = start_line + block_text.count("\n")
        ctx_start = max(0, start_line - 6)
        ctx_end = min(len(source_lines), end_line + 2)
        context_window = "\n".join(source_lines[ctx_start:ctx_end])
        blocks.append((start_line, block_text, context_window))
    return blocks


def _check_block(block: str, context_window: str = "") -> list[str]:
    """Return list of suspicious join patterns in this block.

    If block (or surrounding ``context_window`` of Python source) contains
    any SAFE_MARKER, skip detection.
    """
    # Check both the SQL block itself AND the surrounding Python context
    # (for ``# CANONICAL-FIX-EXEMPT: <reason>`` comments adjacent to the
    # ``op.execute(sa.text("""...""")`` call).
    haystacks = (block, context_window)
    if any(marker in hay for hay in haystacks for marker in SAFE_MARKERS):
        return []
    findings: list[str] = []
    for match in JOIN_PATTERN.finditer(block):
        # Skip self-joins on the same column (e.g., t.id = t.id rare but)
        if match.group("lhs") == match.group("rhs"):
            continue
        # Skip if both sides share the same final column name (typical
        # same-type FK join — e.g., vc.candidate_id = ws.candidate_id).
        # The dangerous case is asymmetric: t.related_job_id = jv.id
        # where varchar meets uuid.
        full_match = match.group(0)
        if SAME_COL_NAME_RE.search(full_match):
            continue
        findings.append(f"{match.group('lhs')} = {match.group('rhs')}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--block",
        action="store_true",
        help="Exit 1 on any violation (CI/pre-commit enforce). "
             "Default is warn-only because heuristic has false positives "
             "on UUID-vs-UUID FK joins.",
    )
    parser.add_argument(
        "--scope",
        choices=("all", "migrations"),
        default="all",
        help="Restrict scan to a directory subset. ``migrations`` = "
             "alembic/versions only (recommended for --block).",
    )
    args = parser.parse_args()

    if args.scope == "migrations":
        scan_dirs = (ROOT / "alembic" / "versions",)
    else:
        scan_dirs = SCAN_DIRS

    total_files = 0
    total_violations = 0
    violation_files: dict[Path, list[str]] = {}

    for path in _iter_python_files(scan_dirs):
        total_files += 1
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        blocks = _find_sql_blocks(source)
        for start_line, block, context_window in blocks:
            findings = _check_block(block, context_window)
            if findings:
                rel = path.relative_to(ROOT)
                key = path
                violation_files.setdefault(key, [])
                for finding in findings:
                    violation_files[key].append(
                        f"  line ~{start_line}: {finding}"
                    )
                    total_violations += 1

    if not violation_files:
        print(f"[check_no_uuid_varchar_join] OK — {total_files} files scanned, "
              f"0 suspicious joins.")
        return 0

    print(f"[check_no_uuid_varchar_join] FAIL — {total_violations} suspicious "
          f"JOIN(s) without cast in {len(violation_files)} file(s):")
    print()
    for path, findings in sorted(violation_files.items()):
        rel = path.relative_to(ROOT)
        print(f"  {rel}")
        for f in findings:
            print(f"  {f}")
        print()
    print("Canonical fix patterns:")
    print("  1. Cast UUID side to text:")
    print("       WHERE varchar_col = uuid_col::text")
    print("  2. Format-validate + cast varchar:")
    print("       WHERE varchar_col ~ '^[0-9a-fA-F-]{36}$'")
    print("         AND varchar_col::uuid = uuid_col")
    print()
    print("To suppress a known-safe line:")
    print("  -- CANONICAL-FIX-EXEMPT: <reason>")
    print()
    print("Reference: migration 161 (post-fix 2026-05-22), 166_planned_task_company_id_not_null.")

    if not args.block:
        print()
        print("Mode: warn-only (exit 0). Run with ``--block`` after triaging "
              "false positives.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
