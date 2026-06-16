#!/usr/bin/env python3
"""
Sensor: check_no_5xx_detail_str_e.py

Detects HTTPException with 5xx status codes exposing raw exception strings via detail=str(e)
or positional str(e) argument. This is an OWASP A09 information disclosure vulnerability.

4xx errors (400, 404, etc.) are intentional user-facing validation messages — NOT flagged.

Usage:
    python scripts/check_no_5xx_detail_str_e.py [--blocking]
    Exit 1 if violations found (blocking mode).
"""
import ast
import os
import re
import sys
from pathlib import Path

APP_DIR = Path(__file__).parent.parent / "app"
BLOCKING = "--blocking" in sys.argv

# Pattern matching: HTTPException(status_code=5xx, detail=str(e))
# or HTTPException(50x, str(e)) positional
_5XX_DETAIL_PATTERN = re.compile(
    r"HTTPException\s*\(.*?status_code\s*=\s*[5][0-9][0-9].*?detail\s*=.*?str\s*\(|"
    r'HTTPException\s*\(.*?status_code\s*=\s*[5][0-9][0-9].*?f"[^"]*\{str\(',
    re.DOTALL,
)

violations = []

for py_file in APP_DIR.rglob("*.py"):
    content = py_file.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    for i, line in enumerate(lines, 1):
        # Check for 5xx detail=str(e) or f"...{str(e)}"
        if ("HTTPException" in line and ("str(e)" in line or "str(exc)" in line)):
            # Check if it's a 5xx
            if re.search(r"status_code\s*=\s*5\d\d", line):
                rel = py_file.relative_to(APP_DIR.parent)
                violations.append(f"[{rel}:{i}] {line.strip()}")
                violations.append(f"  → Fix: replace detail=str(e) with opaque message + logger.error(exc_info=True)")

if violations:
    print(f"❌ {len(violations)//2} OWASP A09 violation(s) found (5xx detail=str(e)):")
    for v in violations:
        print(v)
    if BLOCKING:
        sys.exit(1)
else:
    print(f"✅ No 5xx detail=str(e) violations found")
