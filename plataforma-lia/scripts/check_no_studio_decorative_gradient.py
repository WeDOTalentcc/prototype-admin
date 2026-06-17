#!/usr/bin/env python3
"""Banir gradient cyan/violet decorativo em pages-agent-studio.
DESIGN.md "Quiet Operator" / 90/10 Rule rejeita gradient decorativo.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "src" / "components" / "pages-agent-studio"

# Match "from-{cyan|violet|...} ... to-{cyan|violet|...}" gradient patterns including to-transparent
COLOR_GROUP = r"(?:cyan|wedo-cyan|violet|wedo-purple|purple)"
PATTERN = re.compile(
    rf"from-{COLOR_GROUP}-\d+(?:/\d+)?\s+to-(?:{COLOR_GROUP}-\d+(?:/\d+)?|transparent)"
)

violations = []
for path in TARGET.rglob("*.tsx"):
    if ".bak." in str(path):
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for i, line in enumerate(text.splitlines(), 1):
        if PATTERN.search(line):
            rel = path.relative_to(ROOT).as_posix()
            violations.append(
                f"{rel}:{i}: gradient decorativo cyan/violet banido em Studio. "
                "DS Quiet Operator (90/10 Rule). Use bg-powder/bg-paper neutro."
            )

if violations:
    print("\n".join(violations))
    print(f"\nTotal: {len(violations)} violations")
    sys.exit(1)
print("OK: 0 studio gradient violations")
sys.exit(0)
