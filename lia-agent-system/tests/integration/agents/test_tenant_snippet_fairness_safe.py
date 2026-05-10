"""Smoke test — Tenant snippet não dispara FairnessGuard.

T-E (Task #972): Garante que o snippet de tenant injetado pelo
TenantAwareAgentMixin (nome da empresa, setor, plano, timezone, headcount)
passa pelo FairnessGuard L1 sem ser bloqueado como bias indicator.

Sem essa garantia, o injetor de tenant poderia ser silenciado pela camada
de compliance e o bug "LIA pergunta company_id" voltaria por outro caminho.
LGPD Art. 5 V: o snippet só carrega Pessoa Jurídica (não PII de candidato).
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_tenant_snippet_passes_fairness_guard_l1():
    """Snippet canônico Demo Company T-E não é flagged como discriminatório."""
    from app.shared.compliance.fairness_guard import FairnessGuard

    snippet = (
        "Empresa: Demo Company T-E (Tecnologia)\n"
        "Plano: enterprise\n"
        "Timezone: America/Sao_Paulo\n"
        "Headcount: 51-200"
    )
    guard = FairnessGuard()

    result = guard.check(snippet)
    is_blocked = getattr(result, "is_blocked", getattr(result, "blocked", False))
    assert not is_blocked, (
        f"FairnessGuard bloqueou o snippet de tenant — quebrar isso silenciaria "
        f"o injetor de contexto e reabriria o bug 'LIA pergunta company_id'. "
        f"Result: {result}"
    )

    implicit = guard.check_implicit_bias(snippet)
    assert not implicit, (
        f"FairnessGuard implicit bias warnings no snippet de tenant: {implicit}. "
        f"Snippet só carrega dados de PJ; nenhum termo deveria casar."
    )
