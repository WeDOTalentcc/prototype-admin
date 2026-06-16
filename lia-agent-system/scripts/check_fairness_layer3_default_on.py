#!/usr/bin/env python3
"""Sensor canonical: FairnessGuard L3 default ON cross-sector (ADR-031-v3).

Rejeita config setorial com `fairness_layer3_enabled: False` sem comment
`# ADR-EXEMPT: <reason>` explicito.

Compliance: LGPD Art. 6/11 + EU AI Act Annex III item 4 (high-risk recruitment).
Decisao canonical: L3 LLM semantic check DEVE disparar para TODOS setores.

Exceptions permitidas APENAS com:
- Comment explicito `# ADR-EXEMPT: <reason canonical>`
- ADR aprovado documentando trade-off custo x risco

Modo: WARN-ONLY inicial. Promover para BLOCKING em T-14 apos Sprint 1 estabilizar.

Uso:
    python scripts/check_fairness_layer3_default_on.py [--block]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


SECTOR_RULES_FILE = "app/domains/policy/services/policy_engine_service.py"
TARGET_KEY = "fairness_layer3_enabled"
EXEMPT_MARKER = "ADR-EXEMPT"


def check(file_path: str, block: bool = False) -> int:
    """Returns exit code: 0 if no violations, 1 if violations + block mode."""
    repo_root = Path(__file__).resolve().parent.parent
    target = repo_root / file_path

    if not target.exists():
        print(f"[WARN] {file_path} nao existe (sensor skip)", file=sys.stderr)
        return 0

    source = target.read_text(encoding="utf-8")
    source_lines = source.splitlines()
    tree = ast.parse(source)

    violations: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        for key_node, value_node in zip(node.keys, node.values):
            if not (isinstance(key_node, ast.Constant) and key_node.value == TARGET_KEY):
                continue
            if isinstance(value_node, ast.Constant) and value_node.value is False:
                line_no = value_node.lineno
                line_text = source_lines[line_no - 1] if line_no <= len(source_lines) else ""
                prev_line = source_lines[line_no - 2] if line_no >= 2 else ""
                if EXEMPT_MARKER in line_text or EXEMPT_MARKER in prev_line:
                    continue
                violations.append((line_no, line_text.strip()))

    if violations:
        print(f"[ADR-031-v3] {len(violations)} violations em {file_path}:")
        for line_no, line_text in violations:
            print(f"  line {line_no}: {line_text}")
        print()
        print("CORRECAO:")
        print(f"  Mudar para `\"{TARGET_KEY}\": True` (ADR-031-v3 default safe)")
        print(f"  OU adicionar comment `# ADR-EXEMPT: <reason canonical>` antes/depois")
        print()
        mode = "BLOCKING" if block else "WARN-ONLY"
        print(f"Mode: {mode}")
        return 1 if block else 0

    print(f"[ADR-031-v3] OK -- {file_path}: 0 violations (L3 ON cross-sector enforced)")
    return 0


if __name__ == "__main__":
    block_mode = "--block" in sys.argv
    exit_code = check(SECTOR_RULES_FILE, block=block_mode)
    sys.exit(exit_code)
