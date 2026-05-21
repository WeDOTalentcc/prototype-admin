#!/usr/bin/env python3
"""Sensor canonical T-21: training data exports DEVEM passar por anonymizer.

Regra: `training_data_service.export_*` métodos DEVEM chamar
`TrainingDataAnonymizer.process_batch()` ou `anonymize_sample()` antes do return.

Modo: BLOCKING por default (T-21b POST-WIRE: BLOCKING by default).
Use --warn-only para opt-out (legacy ratchet em branches atrasadas).

Uso:
    python scripts/check_training_data_anonymized.py [--warn-only]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    target = (
        repo_root / "app/domains/analytics/services/training_data_service.py"
    )

    if not target.exists():
        print("[T-21] training_data_service.py não existe — skip")
        return 0

    content = target.read_text(encoding="utf-8")
    tree = ast.parse(content)

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if not node.name.startswith("export_"):
            continue

        # Verifica se função chama anonymizer
        func_source = ast.unparse(node)
        if (
            "TrainingDataAnonymizer" not in func_source
            and "anonymize_sample" not in func_source
            and "process_batch" not in func_source
            and "ANONYMIZER-EXEMPT" not in func_source
        ):
            violations.append(
                f"export_{node.name[7:]} ({node.lineno}) NÃO chama "
                f"TrainingDataAnonymizer.process_batch — LGPD Art. 33 risk"
            )

    if not violations:
        print(
            "[T-21 LGPD ANONYMIZER] OK -- todos export_* chamam anonymizer"
        )
        return 0

    print(f"[T-21 LGPD ANONYMIZER] {len(violations)} violations:")
    for v in violations:
        print(f"  ❌ {v}")
    print()
    print("CORRECAO canonical:")
    print("  Importar: from app.domains.analytics.services.training_data_anonymizer")
    print("            import TrainingDataAnonymizer")
    print("  Aplicar:  anonymizer = TrainingDataAnonymizer()")
    print("            clean = await anonymizer.process_batch(samples, company_id=company_id)")
    print("  OU comment: # ANONYMIZER-EXEMPT: <reason canonical>")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    # T-21b POST-WIRE: BLOCKING by default. --warn-only opt-out for legacy ratchet.
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
