#!/usr/bin/env python3
"""Sensor: alembic migrations MUST NOT use MIN/MAX aggregates on UUID columns.

Canonical-fix harness (registered 2026-05-22 after migration 162 P0)
====================================================================

PostgreSQL has no aggregate ``MIN(uuid)`` / ``MAX(uuid)``. UUIDs are not
ordered by PG default — there's simply no aggregate function defined for
the type. A query like::

    SELECT name, MIN(company_id) FROM unique_departments GROUP BY name

fails at parse/plan time with::

    function min(uuid) does not exist
    No function matches the given name and argument types.

Discovered in migration 162 (workforce_entries.company_id backfill) on
2026-05-22, blocking the entire alembic chain 162-173.

Canonical fix patterns
----------------------

1. ``(array_agg(<col>))[1]`` — pick first element. Safe when an
   accompanying ``HAVING COUNT(*) = 1`` already proves uniqueness (the
   "first" is the only one). Preferred pattern in migration 162.

2. ``MIN(<col>::text)::uuid`` — cast to text for the aggregate, then
   cast back. Performance cost: each row materializes a text copy.
   Avoid in hot paths; OK for one-shot backfills.

3. ``SELECT DISTINCT ON (<group_key>) <group_key>, <col>`` — window-like
   pattern. More explicit but reshapes the query.

Detection heuristic
-------------------

Regex match for ``MIN(`` or ``MAX(`` followed by a column name ending in
``_id`` (or literal ``id``), with NO accompanying ``::text`` cast in the
same SQL block. False-positive note: bigint or integer id columns also
match — those are SAFE (the aggregate is well-defined). The sensor
deliberately over-reports and lets reviewers grep for the schema type;
mistakes are cheap (one comment, one explicit allowlist) and the bug it
catches is a hard production blocker.

Allowlist
---------

Mark a line ``# CANONICAL-FIX-EXEMPT: <reason>`` to suppress detection
for that block. The reason should reference the column's actual type
(e.g., ``# CANONICAL-FIX-EXEMPT: bigint id, MIN is well-defined``).

Modes
-----

- Default: BLOCKING (exit 1 on any violation). Reason: the regression
  cost is catastrophic — entire chain blocks, partial migrations leave
  DB in inconsistent state. No baseline of "legitimate" violations
  exists; the only legitimate use is the allowlisted exempt.
- Use ``--warn-only`` to opt out (e.g., when triaging a freshly-imported
  migration directory).

Usage
-----
::

    python scripts/check_no_uuid_aggregate_bug.py            # blocking
    python scripts/check_no_uuid_aggregate_bug.py --warn-only

Reference: migration 162 fix commit 2026-05-22.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
SCAN_DIRS = (ROOT / "alembic" / "versions",)
EXCLUDE_DIRS = ("__pycache__", "tests", ".venv", "node_modules")

# Anti-pattern: MIN(<col_with_id_suffix>) / MAX(<col_with_id_suffix>)
# without ``::text`` cast on the same column in the same SQL block.
#
# Column name regex: matches `id`, `_id`, or anything ending in
# `_id` (typical UUID FK columns).
AGGREGATE_PATTERN = re.compile(
    r"""
    \b(?P<func>MIN|MAX)
    \s*\(
    \s*
    (?P<col>
        [a-zA-Z_][a-zA-Z0-9_]*\.?    # optional table prefix `t.`
        (?:id|[a-zA-Z_][a-zA-Z0-9_]*_id)
    )
    (?P<cast>\s*::\s*text)?           # optional ::text suppression
    \s*\)
    """,
    re.VERBOSE | re.IGNORECASE,
)

SAFE_MARKERS = (
    "CANONICAL-FIX-EXEMPT",
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
    triple-quoted SQL block. Mirror of pattern in
    check_no_uuid_varchar_join.py.
    """
    blocks: list[tuple[int, str, str]] = []
    source_lines = source.splitlines()
    triple_re = re.compile(r'("""|\'\'\')(.*?)\1', re.DOTALL)
    for match in triple_re.finditer(source):
        block_text = match.group(2)
        if not re.search(r"\b(SELECT|UPDATE|INSERT|DELETE|FROM|JOIN|WHERE|GROUP)\b",
                         block_text, re.IGNORECASE):
            continue
        start_line = source[: match.start()].count("\n") + 1
        end_line = start_line + block_text.count("\n")
        ctx_start = max(0, start_line - 6)
        ctx_end = min(len(source_lines), end_line + 2)
        context_window = "\n".join(source_lines[ctx_start:ctx_end])
        blocks.append((start_line, block_text, context_window))
    return blocks


def _check_block(block: str, context_window: str = "") -> list[str]:
    """Return list of suspicious MIN/MAX patterns in this SQL block."""
    haystacks = (block, context_window)
    if any(marker in hay for hay in haystacks for marker in SAFE_MARKERS):
        return []
    findings: list[str] = []
    for match in AGGREGATE_PATTERN.finditer(block):
        if match.group("cast"):
            continue  # already has ::text cast — safe
        findings.append(f"{match.group('func')}({match.group('col')})")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Report findings but exit 0 (opt-out). Default is BLOCKING.",
    )
    args = parser.parse_args()

    total_files = 0
    total_violations = 0
    violation_files: dict[Path, list[str]] = {}

    for path in _iter_python_files(SCAN_DIRS):
        total_files += 1
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        blocks = _find_sql_blocks(source)
        for start_line, block, context_window in blocks:
            findings = _check_block(block, context_window)
            if findings:
                violation_files.setdefault(path, [])
                for finding in findings:
                    violation_files[path].append(
                        f"  line ~{start_line}: {finding}"
                    )
                    total_violations += 1

    if not violation_files:
        print(f"[check_no_uuid_aggregate_bug] OK — {total_files} files scanned, "
              f"0 MIN/MAX-on-uuid violations.")
        return 0

    print(f"[check_no_uuid_aggregate_bug] FAIL — {total_violations} suspicious "
          f"aggregate(s) on *id column(s) in {len(violation_files)} file(s):")
    print()
    for path, findings in sorted(violation_files.items()):
        rel = path.relative_to(ROOT)
        print(f"  {rel}")
        for f in findings:
            print(f"  {f}")
        print()
    print("PostgreSQL has NO aggregate function for the UUID type.")
    print("Canonical fix patterns:")
    print("  1. (array_agg(<col>))[1]              # pick first; safe when HAVING COUNT(*)=1")
    print("  2. MIN(<col>::text)::uuid             # cast to text + back (slower)")
    print("  3. SELECT DISTINCT ON (<key>) ...     # window-like reshape")
    print()
    print("If column is bigint/integer (NOT uuid), suppress with:")
    print("  # CANONICAL-FIX-EXEMPT: bigint id, MIN is well-defined")
    print()
    print("Reference: migration 162 fix (2026-05-22).")

    if args.warn_only:
        print()
        print("Mode: warn-only (exit 0). Default is blocking — use without "
              "--warn-only to enforce.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
