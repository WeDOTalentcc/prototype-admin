#!/usr/bin/env python3
"""
Sensor canonical-fix: detecta drift na taxonomia de beneficios.

Aplica:
- canonical-fix: 1 producer (benefits_service.BENEFIT_CATEGORIES). Falha se
  algum outro arquivo Python definir uma segunda lista divergente.
- harness-engineering: sensor computacional (AST), falso-positivo ~0%.
  Honra marker `# TAXONOMY-EXEMPT: <reason>` para casos legitimos
  (ex: tests, migrations, seed data).

Detecta padroes:
1. Atribuicao a `BENEFIT_CATEGORIES`, `BENEFIT_VALUE_TYPES`, ou
   `BENEFIT_WAITING_PERIODS` fora do canonical (benefits_service.py).
2. Lista/dict literal contendo >=3 keys/values do conjunto canonical
   suspeito de hardcoded taxonomy duplicada.

Exit codes:
  0 = ok ou warn-only mode
  1 = blocking mode + violations encontradas

Uso:
  python3 scripts/check_no_duplicate_benefit_taxonomy.py            # warn
  python3 scripts/check_no_duplicate_benefit_taxonomy.py --blocking # block
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_FILE = REPO_ROOT / "app/domains/company/services/benefits_service.py"

CANONICAL_SYMBOL_NAMES = {
    "BENEFIT_CATEGORIES",
    "BENEFIT_CATEGORY_ICONS",
    "BENEFIT_CATEGORY_LEGACY_ALIASES",
    "BENEFIT_VALUE_TYPES",
    "BENEFIT_VALUE_TYPE_ICONS",
    "BENEFIT_WAITING_PERIODS",
}

# Set de chaves canonical da v2 — se um literal contem >=3 dessas chaves,
# eh suspeito de drift (hardcoded taxonomy duplicada).
CANONICAL_CATEGORY_KEYS = {
    "health", "wellness", "food", "transport", "education",
    "financial", "retirement", "family", "parental", "flexibility",
    "equipment", "culture", "recognition",
}
EXEMPT_MARKER = "TAXONOMY-EXEMPT"


def has_exempt_marker(source_lines: list[str], lineno: int) -> bool:
    """Procura `# TAXONOMY-EXEMPT: <reason>` na linha ou linha anterior."""
    for delta in (0, -1, -2):
        idx = lineno - 1 + delta
        if 0 <= idx < len(source_lines):
            if EXEMPT_MARKER in source_lines[idx]:
                return True
    return False


def find_violations(file_path: Path) -> list[dict]:
    """Retorna lista de violacoes. Cada item: {file, line, kind, name, fix}."""
    if file_path.resolve() == CANONICAL_FILE.resolve():
        return []  # arquivo canonical — pode definir simbolos

    try:
        source = file_path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    source_lines = source.split("\n")
    violations: list[dict] = []

    for node in ast.walk(tree):
        # Pattern 1: atribuicao a simbolo canonical
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in CANONICAL_SYMBOL_NAMES:
                    if not has_exempt_marker(source_lines, node.lineno):
                        violations.append({
                            "file": str(file_path.relative_to(REPO_ROOT)),
                            "line": node.lineno,
                            "kind": "duplicate-canonical-symbol",
                            "name": target.id,
                            "fix": (
                                f"NAO redefina '{target.id}' fora do canonical. "
                                f"Importe: from app.domains.company.services.benefits_service "
                                f"import {target.id}. Se for legitimo (seed/test), "
                                f"marque com '# {EXEMPT_MARKER}: <motivo>'."
                            ),
                        })

        # Pattern 2: AnnAssign (BENEFIT_CATEGORIES: dict[str, str] = ...)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in CANONICAL_SYMBOL_NAMES:
                if not has_exempt_marker(source_lines, node.lineno):
                    violations.append({
                        "file": str(file_path.relative_to(REPO_ROOT)),
                        "line": node.lineno,
                        "kind": "duplicate-canonical-symbol",
                        "name": node.target.id,
                        "fix": (
                            f"NAO redefina '{node.target.id}' fora do canonical. "
                            f"Importe ou marque com '# {EXEMPT_MARKER}: <motivo>'."
                        ),
                    })

        # Pattern 3: dict literal com >=3 chaves canonical (suspeito de drift)
        if isinstance(node, ast.Dict):
            literal_keys = {
                k.value
                for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
            overlap = literal_keys & CANONICAL_CATEGORY_KEYS
            if len(overlap) >= 3:
                if not has_exempt_marker(source_lines, node.lineno):
                    violations.append({
                        "file": str(file_path.relative_to(REPO_ROOT)),
                        "line": node.lineno,
                        "kind": "suspected-taxonomy-drift",
                        "name": f"dict-literal with {len(overlap)} canonical keys",
                        "fix": (
                            f"Dict literal contem {len(overlap)} chaves de "
                            f"BENEFIT_CATEGORIES: {sorted(overlap)}. Suspeito de "
                            f"taxonomy hardcoded. Use o canonical "
                            f"BENEFIT_CATEGORIES de benefits_service ou marque "
                            f"com '# {EXEMPT_MARKER}: <motivo>'."
                        ),
                    })

    return violations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--blocking",
        action="store_true",
        help="Exit 1 em violacoes (CI/pre-commit). Default = warn-only.",
    )
    parser.add_argument(
        "--max-violations",
        type=int,
        default=0,
        help="Ratchet baseline (warn-only quando total <= max).",
    )
    args = parser.parse_args()

    targets = sorted(REPO_ROOT.glob("app/**/*.py")) + sorted(REPO_ROOT.glob("scripts/**/*.py"))
    all_violations: list[dict] = []
    for f in targets:
        all_violations.extend(find_violations(f))

    if not all_violations:
        print("OK no benefit taxonomy drift detected.")
        return 0

    print(f"\nWARN  detected {len(all_violations)} benefit taxonomy drift(s):\n")
    for v in all_violations:
        print(f"  [{v['file']}:{v['line']}] {v['kind']}  → {v['name']}")
        print(f"    Fix: {v['fix']}\n")

    if args.blocking and len(all_violations) > args.max_violations:
        print(
            f"\nBLOCK  {len(all_violations)} > max_violations={args.max_violations}. "
            f"Refatore para usar o canonical em benefits_service.py."
        )
        return 1

    print("\nNote: warn-only mode. Promote to --blocking when baseline reaches 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
