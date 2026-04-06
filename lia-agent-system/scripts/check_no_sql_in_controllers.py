#!/usr/bin/env python3
"""
CI Guard: Zero SQLAlchemy calls allowed in app/api/ files.

Usage:
    python3 scripts/check_no_sql_in_controllers.py

Exits 1 if any direct DB calls are found in controller files.
This enforces Golden Rule G1: Controllers call services/repos, NEVER the DB directly.
"""
import sys
import re
from pathlib import Path

SQL_PATTERNS = [
    (r"await\s+db\.(execute|scalar|scalars|query|get|merge|delete|flush|refresh)", "direct db method call"),
    (r"\bsa\.(select|insert|update|delete|text)\(", "SQLAlchemy expression in controller"),
    (r"from sqlalchemy.*import", "SQLAlchemy import in controller"),
    (r"AsyncSession.*=.*Depends\(get_db\)", "AsyncSession directly in route handler"),
]

EXCLUDE_PATTERNS = [
    r"^\s*#",           # commented lines
    r"response_model",   # not SQL
]

errors = []
checked = 0

for path in Path("app/api").rglob("*.py"):
    if "__pycache__" in str(path):
        continue
    checked += 1
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith("#"):
            continue
        for pattern, description in SQL_PATTERNS:
            if re.search(pattern, line):
                errors.append(f"{path}:{i}: {description}\n  > {line.strip()[:100]}")

if errors:
    print(f"\n[FAIL] SQL/DB calls found in {len(errors)} locations in app/api/:")
    print()
    for e in errors:
        print(f"  {e}")
    print()
    print("Fix: Move DB calls to app/domains/*/repositories/ and call them from services.")
    print("See ARCHITECTURE.md ADR-001 for the repository pattern.")
    sys.exit(1)

print(f"[PASS] No SQL in controllers ({checked} files checked)")
sys.exit(0)
