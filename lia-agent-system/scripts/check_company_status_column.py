#!/usr/bin/env python3
"""Sensor 7 — bloqueia queries `companies.status = 'active'` (coluna não existe).

REGRESSÃO 2026-05-24: `app/jobs/tasks/ml.py:197` tinha
    SELECT DISTINCT id FROM companies WHERE status = 'active'
mas a tabela `companies` tem coluna `is_active boolean` (não `status`).
Resultado: `UndefinedColumnError: column "status" does not exist` falhava
a query de tenant list inteira, abortava `routing.recompute_adjustments`.

Canonical: usar `WHERE is_active = true` (mesma semântica).

Detection: regex match em SQL strings dentro de Python files. Substring
"companies" + ("status =" ou ".status").

Honra `# COMPANIES-COLUMN-OK: <reason>` na linha acima.

Pattern: BLOCKING.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXEMPT_MARKER = "COMPANIES-COLUMN-OK:"

# Anti-patterns — regex (case-insensitive)
ANTIPATTERNS = [
    (re.compile(r"FROM\s+companies[^.]*?\bstatus\s*=", re.IGNORECASE | re.DOTALL),
     "Use `is_active = true` (column 'status' does not exist on companies table)"),
    (re.compile(r"\bcompanies?\.status\b", re.IGNORECASE),
     "Use `companies.is_active` (column 'status' does not exist)"),
]


def _scan_file(path: Path) -> list[dict]:
    if not path.exists() or path.suffix != ".py":
        return []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    src_lines = text.splitlines()
    violations: list[dict] = []
    for i, line in enumerate(src_lines, start=1):
        # Skip comments
        if line.lstrip().startswith("#"):
            continue
        for regex, advice in ANTIPATTERNS:
            if regex.search(line):
                window = [src_lines[max(0, i-2)], src_lines[max(0, i-3)]]
                if any(EXEMPT_MARKER in w for w in window):
                    continue
                violations.append({
                    "file": str(path.relative_to(REPO_ROOT)),
                    "line": i,
                    "raw": line.rstrip(),
                    "advice": advice,
                })
                break
    return violations


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--blocking", action="store_true")
    args = parser.parse_args(argv)

    violations = []
    for path in (REPO_ROOT / "app").rglob("*.py"):
        violations.extend(_scan_file(path))

    if args.json:
        print(json.dumps({"violations": violations}, indent=2))
    else:
        if violations:
            print(f"❌ {len(violations)} reference(s) to non-existent companies.status:\n")
            for v in violations:
                print(f"  {v['file']}:{v['line']}")
                print(f"    {v['raw']}")
                print(f"    → {v['advice']}. EXEMPT: `# {EXEMPT_MARKER} <reason>`\n")
        else:
            print("✅ No references to non-existent companies.status column.")

    if args.blocking and violations:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
