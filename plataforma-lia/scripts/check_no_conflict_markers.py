#!/usr/bin/env python3
"""Sensor canonical: nenhum merge conflict marker pode atravessar para commit.
SSOT: pre-commit hook + CI.
Fix: resolver manualmente o conflict antes de commit (escolher um dos lados).
"""
import re
import sys
from pathlib import Path

EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".md", ".yml", ".yaml", ".sql"}
ROOTS = [Path("plataforma-lia/src"), Path("lia-agent-system/app"), Path("lia-agent-system/tests")]
PATTERN = re.compile(r"^(<{7}|={7}|>{7})($|\s)")
violations = []

for root in ROOTS:
    if not root.exists():
        continue
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in EXTENSIONS:
            continue
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if PATTERN.match(line):
                violations.append(f"{path}:{i}: merge conflict marker -> {line[:60]}")

if violations:
    print("\n".join(violations))
    print(f"\n{len(violations)} merge conflict markers detected.")
    print("Fix: resolver conflict manualmente (escolher um lado), depois git add + commit.")
    sys.exit(1)
print("OK")
sys.exit(0)
