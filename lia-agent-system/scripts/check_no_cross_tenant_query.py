#!/usr/bin/env python3
"""SENSOR (harness-engineering: cross-tenant data leak prevention).

Detect SELECT queries against tenant-scoped tables (candidates,
vacancy_candidates, candidate_list_members) that DO NOT include a
company_id filter in the WHERE clause.

This is a P0 LGPD class of bug. Recruiter authenticated to Company A
calls an LLM tool with candidate_id from Company B and gets PII back
(including email + phone in some sites). Confirmed via audit
2026-05-21: ~69 such sites in 10 tool_registry files.

This sensor pins the baseline + blocks new offenders. Promoting to
BLOCKING baseline 0 once all known offenders are fixed.

REGRA canonical: every SQL block touching a tenant-scoped table MUST
include company_id in WHERE / JOIN ON, or be explicitly EXEMPT
via inline comment '# CROSS-TENANT-EXEMPT: <justification>'.

Run modes:
  warn-only (default): exit 0, lists hits
  --blocking --baseline N: exit 1 if hits > N
  --json: machine-readable output

Exit codes:
  0 = no hits, or hits <= baseline in blocking mode
  1 = hits > baseline in blocking mode
  2 = usage error
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


# Tables that ARE always tenant-scoped (must have company_id in queries
# OR EXEMPT with justification).
TENANT_SCOPED_TABLES = (
    "candidates",
    "vacancy_candidates",
    "candidate_list_members",
)

# Glob patterns of files to scan. tool_registry.py is the agent layer
# entry point most exposed to cross-tenant via LLM-provided IDs.
SCAN_GLOBS = (
    "app/domains/*/agents/*tool_registry.py",
)

# Inline exempt marker (comment before or inside the SQL block).
EXEMPT_MARKER = "CROSS-TENANT-EXEMPT"


@dataclass
class Hit:
    file: str
    line: int
    table: str
    sql_snippet: str
    reason: str
    fix_suggestion: str = field(default="")


def find_sql_blocks(content: str) -> list[tuple[int, str]]:
    """Return list of (line_number, sql_text) for each text(...) block.

    Catches three forms:
      - text(\"\"\"...\"\"\") multi-line triple-double-quoted
      - text(\"...\") single-line double-quoted (must contain FROM or JOIN)
      - text(f\"...\") f-string variant
    Line number is the line where text(...) starts (1-based).
    """
    blocks = []
    for m in re.finditer(r'text\(\s*"""(.*?)"""\s*\)', content, re.DOTALL):
        line = content[: m.start()].count("\n") + 1
        blocks.append((line, m.group(1)))
    for m in re.finditer(
        r'text\(\s*"([^"]*?(?:FROM|JOIN)[^"]*?)"\s*[),]',
        content,
        re.IGNORECASE,
    ):
        line = content[: m.start()].count("\n") + 1
        blocks.append((line, m.group(1)))
    for m in re.finditer(
        r'text\(\s*f"([^"]*?(?:FROM|JOIN)[^"]*?)"\s*[),]',
        content,
        re.IGNORECASE,
    ):
        line = content[: m.start()].count("\n") + 1
        blocks.append((line, m.group(1)))
    return blocks


def detect_offending_block(sql: str) -> tuple[str | None, str]:
    """Return (offending_table, reason) or (None, '') if SQL is safe.

    A block 'offends' if:
      - It touches a tenant-scoped table (in FROM/JOIN), AND
      - It does NOT mention company_id anywhere in the SQL.
    """
    sql_lower = sql.lower()
    for table in TENANT_SCOPED_TABLES:
        pattern = rf"(?:from|join)\s+{re.escape(table)}\b"
        if not re.search(pattern, sql_lower):
            continue
        if "company_id" in sql_lower:
            return None, ""
        return table, f"SELECT/JOIN against tenant-scoped table {table!r} without company_id filter"
    return None, ""


def check_exempt_marker(content: str, block_start_line: int) -> bool:
    """Check if a CROSS-TENANT-EXEMPT comment appears in the 5 lines
    immediately preceding the block start."""
    lines = content.splitlines()
    start_idx = max(0, block_start_line - 6)
    end_idx = block_start_line
    window = "\n".join(lines[start_idx:end_idx])
    return EXEMPT_MARKER in window


def fix_suggestion_for(table: str) -> str:
    if table == "candidates":
        return (
            "Add company_id tenant gate. Pattern:\n"
            "  WHERE id = :cid\n"
            "    AND (company_id IS NULL OR company_id = :company_id)\n"
            "  -- company_id IS NULL preserves global talent pool sharing.\n"
            "  -- Required params: {'company_id': company_id_from_kwargs}"
        )
    if table == "vacancy_candidates":
        return (
            "Add company_id tenant gate. Pattern:\n"
            "  WHERE vc.vacancy_id = :vid\n"
            "    AND vc.company_id = :company_id\n"
            "  -- vacancy_candidates.company_id is NOT NULL"
        )
    if table == "candidate_list_members":
        return (
            "Add JOIN + tenant gate via parent list:\n"
            "  JOIN candidate_lists cl ON cl.id = clm.list_id\n"
            "  WHERE clm.list_id = :lid\n"
            "    AND cl.company_id = :company_id\n"
            "  -- candidate_list_members has no company_id; filter via parent"
        )
    return "Add company_id filter to the WHERE clause."


def scan_file(filepath: Path) -> list[Hit]:
    try:
        content = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    hits = []
    for line, sql in find_sql_blocks(content):
        table, reason = detect_offending_block(sql)
        if not table:
            continue
        if check_exempt_marker(content, line):
            continue
        snippet = sql.strip().split("\n")[0][:120]
        hits.append(
            Hit(
                file=str(filepath),
                line=line,
                table=table,
                sql_snippet=snippet,
                reason=reason,
                fix_suggestion=fix_suggestion_for(table),
            )
        )
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect cross-tenant SQL leaks in agent layer."
    )
    parser.add_argument("--blocking", action="store_true", help="Exit 1 if hits > baseline")
    parser.add_argument("--baseline", type=int, default=0, help="Allowed offenders (warn-baseline-N mode)")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repo root")
    args = parser.parse_args(argv)

    root = args.root
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}", file=sys.stderr)
        return 2

    files: list[Path] = []
    for pattern in SCAN_GLOBS:
        files.extend(root.glob(pattern))
    files = sorted(set(files))

    all_hits: list[Hit] = []
    for f in files:
        all_hits.extend(scan_file(f))

    count = len(all_hits)
    if args.json:
        print(json.dumps([asdict(h) for h in all_hits], indent=2))
    else:
        if not all_hits:
            print("No cross-tenant SQL leaks detected. Baseline 0 held.")
        else:
            print(f"WARN {count} cross-tenant SQL leak(s) detected (baseline allowed: {args.baseline})")
            print()
            for h in all_hits:
                try:
                    rel = Path(h.file).relative_to(root)
                except ValueError:
                    rel = Path(h.file)
                print(f"  {rel}:{h.line}  [{h.table}]")
                print(f"    SQL: {h.sql_snippet}")
                fix_lines = h.fix_suggestion.splitlines()
                if fix_lines:
                    print(f"    FIX: {fix_lines[0]}")
                    for fix_line in fix_lines[1:]:
                        print(f"         {fix_line}")
                print()
            print(f"TOTAL: {count} offender(s).")
            print(
                "Add CROSS-TENANT-EXEMPT comment above the SQL block "
                "with justification, OR fix per FIX."
            )

    if args.blocking and count > args.baseline:
        print(
            f"FAILED: {count} offenders > baseline {args.baseline} (blocking mode).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
