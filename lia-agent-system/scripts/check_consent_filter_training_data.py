#!/usr/bin/env python3
"""Sensor canonical T-11 B.1.4: list_quality_feedback DEVE chamar CompanyTrainingConsent gate.

Regra canonical (ADR-RLHF-001):
- FeedbackRepository.list_quality_feedback em feedback_repository.py DEVE
  chamar CompanyTrainingConsentRepository.is_active(company_id) ANTES
  de retornar feedback samples.
- Fail-CLOSED: no consent = empty list.

Modo: BLOCKING por default (T-11 B.1 post-wire). Use --warn-only para opt-out.

Uso:
    python scripts/check_consent_filter_training_data.py [--warn-only]
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path


def check(strict: bool = True) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    target = (
        repo_root / "app/domains/analytics/repositories/feedback_repository.py"
    )

    if not target.exists():
        print("[T-11 B.1.4 CONSENT GATE] target file não existe — skip")
        return 0

    content = target.read_text(encoding="utf-8")
    tree = ast.parse(content)

    violations = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        if node.name != "list_quality_feedback":
            continue

        func_source = ast.unparse(node)
        if (
            "CompanyTrainingConsentRepository" not in func_source
            and "is_active" not in func_source
            and "CONSENT-GATE-EXEMPT" not in func_source
        ):
            violations.append(
                f"list_quality_feedback ({node.lineno}) NÃO chama "
                "CompanyTrainingConsentRepository.is_active gate "
                "— LGPD Art. 7 explicit consent risk"
            )

    if not violations:
        print(
            "[T-11 B.1.4 CONSENT GATE] OK -- list_quality_feedback tem consent gate canonical"
        )
        return 0

    print(f"[T-11 B.1.4 CONSENT GATE] {len(violations)} violations:")
    for v in violations:
        print(f"  ❌ {v}")
    print()
    print("CORRECAO canonical:")
    print("  Importar: from app.domains.lgpd.repositories.company_training_consent_repository")
    print("            import CompanyTrainingConsentRepository")
    print("  Aplicar:  consent_repo = CompanyTrainingConsentRepository(self.db)")
    print("            if not await consent_repo.is_active(company_id): return []")
    print("  OU comment: # CONSENT-GATE-EXEMPT: <reason canonical>")
    print()
    mode = "BLOCKING" if strict else "WARN-ONLY"
    print(f"Mode: {mode}")
    return 1 if strict else 0


if __name__ == "__main__":
    # T-11 B.1.4: BLOCKING by default. --warn-only opt-out canonical.
    strict = "--warn-only" not in sys.argv
    sys.exit(check(strict=strict))
