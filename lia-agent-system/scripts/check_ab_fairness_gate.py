#!/usr/bin/env python3
"""Sensor canonical T-19: auto_promote_winner DEVE ter FairnessGuard gate.

Regra canonical (ADR-AB-001):
- auto_promote_winner em ab_testing_service.py DEVE chamar FairnessGuard
  antes de promover winner variant.
- Modo INICIAL: WARN-ONLY. Promover BLOCKING após T-19 Fase 2 (UI integration).

Uso:
    python scripts/check_ab_fairness_gate.py [--strict]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def check(strict: bool = True) -> int:  # [PROMOTED BLOCKING Sprint 7]
    repo_root = Path(__file__).resolve().parent.parent
    target = repo_root / "app/shared/learning/ab_testing_service.py"

    if not target.exists():
        print("[T-19 AB FAIRNESS GATE] target file não existe — skip")
        return 0

    content = target.read_text(encoding="utf-8")
    tree = ast.parse(content)

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if node.name != "auto_promote_winner":
            continue

        func_source = ast.unparse(node)
        if (
            "FairnessGuard" not in func_source
            and "fairness_gate_blocked" not in func_source
            and "FAIRNESS-GATE-EXEMPT" not in func_source
        ):
            violations.append(
                f"auto_promote_winner ({node.lineno}) NÃO chama FairnessGuard "
                "antes de promover — discriminação indireta risk"
            )

    if not violations:
        print(
            "[T-19 AB FAIRNESS GATE] OK -- auto_promote_winner tem fairness gate canonical"
        )
        return 0

    print(f"[T-19 AB FAIRNESS GATE] {len(violations)} violations:")
    for v in violations:
        print(f"  ❌ {v}")
    print()
    print("CORRECAO canonical:")
    print("  Importar: from app.shared.compliance.fairness_guard import FairnessGuard")
    print("  Aplicar:  guard.check(winner_prompt, action_type='ab_test_winner_promotion')")
    print("  Se is_blocked=True: NÃO promover, retornar reason='fairness_gate_blocked'")
    print("  OU comment: # FAIRNESS-GATE-EXEMPT: <reason canonical>")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    strict = "--warn-only" not in sys.argv  # [PROMOTED BLOCKING Sprint 7]
    sys.exit(check(strict=strict))
