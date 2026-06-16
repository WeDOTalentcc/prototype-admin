#!/usr/bin/env python3
"""Banir uso de classe Tailwind font-inter (DESIGN.md mandate: Open Sans via font-sans).

Permite definicoes de variavel CSS (--font-inter) e referencias var(--font-inter)
em globals.css/components.css/layout.tsx (next/font infra canonical).
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# Match font-inter as Tailwind class (not as CSS var --font-inter)
# Negative lookbehind: not preceded by -- (CSS var) or by ( (function arg in var())
PATTERN = re.compile(r"(?<!-)\bfont-inter\b")

violations = []
for ext in ("*.tsx", "*.ts", "*.css"):
    for path in SRC.rglob(ext):
        if ".bak." in str(path):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            # Skip lines that only mention font-inter as CSS variable definition or var() ref
            if "--font-inter" in line and "font-inter" not in re.sub(r"--font-inter", "", line):
                continue
            if "var(--font-inter)" in line:
                continue
            if PATTERN.search(line):
                rel = path.relative_to(ROOT).as_posix()
                violations.append(f"{rel}:{i}: font-inter banido. Use font-sans (Open Sans canonical).")

if violations:
    print("\n".join(violations))
    print(f"\nTotal: {len(violations)} violations")
    sys.exit(1)
print("OK: 0 font-inter violations")
sys.exit(0)
