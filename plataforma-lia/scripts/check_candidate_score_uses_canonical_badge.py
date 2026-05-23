#!/usr/bin/env python3
"""
check_candidate_score_uses_canonical_badge.py

Sensor canonical (Task #512 / F1 building blocks): bloqueia escala WSI 0-100
legacy em arquivos do domínio "candidate-*" no frontend.

Detecção:
- String literal "/100" em arquivos sob:
  - src/components/candidate-preview/
  - src/components/candidate-page/
  - src/components/candidate-profile/
  - src/app/**/funil-de-talentos/candidato/

Ignora:
- comentários (// ou /* */ ou docstring)
- linhas marcadas com  (escape hatch documentada)
- imports e type-only references

Modo: warn-only por default. Use --blocking para exit 1.

Output otimizado pra consumo de LLM:
  [path:line] suspect line snippet
    → Fix: trocar /100 por /10 (WSI canonical) OU usar <CandidateScoreBadge format=\"wsi\">
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # plataforma-lia/
SRC = ROOT / "src"

SCAN_DIRS = [
    SRC / "components" / "candidate-preview",
    SRC / "components" / "candidate-page",
    SRC / "components" / "candidate-profile",
]
# Plus the standalone route
ROUTE_GLOB = SRC.glob("app/**/funil-de-talentos/candidato/**/*.tsx")

ALLOW_MARKER = "@canonical-allow-100"
PATTERN_100 = re.compile(r"/100\b")
# Skip comment-only matches and import lines
SKIP_LINE = re.compile(r"^\s*(//|\*|/\*|import |export type )")


def scan_file(path: Path) -> list[tuple[int, str]]:
    violations: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return violations

    in_block_comment = False
    prev_line = ""
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        stripped = line.strip()

        # crude block-comment tracking
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            prev_line = line
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            prev_line = line
            continue

        if SKIP_LINE.match(line):
            prev_line = line
            continue
        # Marker can be inline OR on the preceding non-empty line (lookback)
        if ALLOW_MARKER in line or ALLOW_MARKER in prev_line:
            prev_line = line
            continue
        if PATTERN_100.search(line):
            violations.append((lineno, stripped))
        prev_line = line
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocking", action="store_true", help="Exit 1 on violations.")
    args = parser.parse_args()

    files: list[Path] = []
    for d in SCAN_DIRS:
        if d.exists():
            files.extend(d.rglob("*.tsx"))
            files.extend(d.rglob("*.ts"))
    files.extend(ROUTE_GLOB)

    total_violations = 0
    print("check_candidate_score_uses_canonical_badge.py")
    print(f"Scanning {len(files)} files in candidate-* domains...\n")

    for path in sorted(set(files)):
        # skip __tests__ (testing legacy + canonical fine there)
        if "__tests__" in path.parts:
            continue
        vios = scan_file(path)
        if not vios:
            continue
        rel = path.relative_to(ROOT)
        for lineno, snippet in vios:
            total_violations += 1
            print(f"  [{rel}:{lineno}] {snippet}")
            print(f"    → Fix: trocar /100 por /10 (WSI canonical Task #512) OU usar <CandidateScoreBadge format=\"wsi\">")
            print(f"    → Escape: adicionar marker  se realmente necessário\n")

    if total_violations == 0:
        print("✅ 0 violations — WSI canonical 0-10 em todas as candidate-* surfaces.")
        return 0

    print(f"\nTotal: {total_violations} violation(s).")
    if args.blocking:
        print("Modo: BLOCKING (exit 1)")
        return 1
    print("Modo: WARN-ONLY (exit 0). Use --blocking pra falhar CI.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
