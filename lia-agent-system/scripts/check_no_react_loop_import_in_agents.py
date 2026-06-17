#!/usr/bin/env python3
"""
R-014 harness sensor -- blocks `from lia_agents_core.react_loop import` in agent/registry files.

react_loop is a deprecated shim (see libs/agents-core/lia_agents_core/react_loop.py).
All agents and tool registries must import directly from lia_agents_core.tool_adapter.

Exit 0 = clean. Exit 1 = violations found.
"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCAN_DIRS = [
    ROOT / "app" / "domains",
    ROOT / "libs" / "agents-core",
]
PATTERN = re.compile(r"from lia_agents_core\.react_loop import")
EXCLUDE_FILES = {"react_loop.py"}  # the shim itself is allowed to exist

violations = []
for scan_dir in SCAN_DIRS:
    if not scan_dir.exists():
        continue
    for py_file in scan_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        if py_file.name in EXCLUDE_FILES:
            continue
        text = py_file.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line):
                violations.append(f"{py_file.relative_to(ROOT)}:{i}: {line.strip()}")

if violations:
    print("[R-014] ❌ Legacy react_loop imports found (use lia_agents_core.tool_adapter instead):")
    for v in violations:
        print(f"  {v}")
    sys.exit(1)

total = len(list(ROOT.rglob("*.py")))
print(f"[R-014] ✅ No react_loop imports in agents/registries ({total} files scanned)")
sys.exit(0)
