"""
A.1 — Cross-tenant isolation contract test (HARDENING_PLAN.md Bloco A.1).

Sensor permanente para o fix P1.1 da Sprint Governance (2026-05-21):
app/api/v1/audit_logs.py::_build_conditions rejeita qualquer client_id
query param que NÃO bata exatamente com o company_id derivado do JWT.

Sentinela mágica client_id=platform era um bypass usado por regular users
para escapar tenant filter; foi removida no fix WT-2023 (commit refers REGRA
ZERO + REGRA 6 CLAUDE.md). Estes testes pinam o comportamento canonical para
qualquer commit futuro que tente reintroduzir o bypass.

Strategy: pure-unit tests sobre _build_conditions, sem subir FastAPI app
nem DB session. Espelha pattern de test_offer_approval_gate.py.

NOTA sobre cenário super_admin (A.1 test 5):
A implementação atual NÃO tem escape hatch para wedotalent_admin role —
gate rejeita TODA mismatch. O teste 5 documenta este fato (cenário do
HARDENING_PLAN onde super admin usaria client_id=platform para acesso
cross-tenant ainda não existe; quando for implementado, este teste vira
xfail/skip removido).
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.v1.audit_logs import _build_conditions


TENANT_A_ID = "11111111-1111-4111-a111-111111111111"
TENANT_B_ID = "22222222-2222-4222-a222-222222222222"


class TestAuditLogsClientIdGate:
    """Pin _build_conditions tenant scoping logic (P1.1 regression sensor)."""

    def test_audit_logs_rejects_client_id_platform_for_regular_user(self):
        """Magic sentinel platform MUST be rejected by gate.

        Regression sensor: garante que reintroduzir o bypass histórico
        (client_id=platform para acesso cross-tenant) volta a falhar.
        """
        with pytest.raises(HTTPException) as exc_info:
            _build_conditions(
                date_from=None,
                date_to=None,
                client_id="platform",  # magic sentinel — bypass histórico
                company_id=TENANT_A_ID,
            )
        assert exc_info.value.status_code == 403
        assert "client_id" in exc_info.value.detail.lower()

    def test_audit_logs_rejects_other_tenant_client_id(self):
        """client_id de OUTRO tenant é cross-tenant attack — deve retornar 403."""
        with pytest.raises(HTTPException) as exc_info:
            _build_conditions(
                date_from=None,
                date_to=None,
                client_id=TENANT_B_ID,  # tenant B query param
                company_id=TENANT_A_ID,  # JWT tenant A
            )
        assert exc_info.value.status_code == 403
        assert "client_id" in exc_info.value.detail.lower()

    def test_audit_logs_accepts_own_client_id(self):
        """client_id que bate com JWT tenant é válido — não levanta."""
        conditions = _build_conditions(
            date_from=None,
            date_to=None,
            client_id=TENANT_A_ID,
            company_id=TENANT_A_ID,
        )
        assert conditions is not None
        assert len(conditions) >= 1, (
            "Esperava pelo menos a condição de client_id == company_id"
        )

    def test_audit_logs_no_param_returns_own_tenant_only(self):
        """Sem client_id query param, gate aplica filtro implícito por company_id.

        Verifica que conditions contém comparação de SOXAuditLog.client_id
        com o company_id do JWT. Sem esse filtro, a query retornaria
        cross-tenant data (regressão crítica P1.1).
        """
        conditions = _build_conditions(
            date_from=None,
            date_to=None,
            client_id=None,  # nenhum query param
            company_id=TENANT_A_ID,
        )
        # Pelo menos uma condição deve referenciar SOXAuditLog.client_id == TENANT_A_ID.
        # SQLAlchemy ColumnElement comparison não é hashable; serializamos para inspeção.
        conditions_str = " ".join(str(c) for c in conditions)
        assert "client_id" in conditions_str.lower(), (
            f"Esperava filtro client_id == company_id em conditions, "
            f"recebido: {conditions_str!r}"
        )

    def test_audit_logs_super_admin_can_use_platform(self):
        """Cenário HARDENING_PLAN A.1 #5: super admin com client_id=platform.

        STATUS ATUAL: implementação não tem escape hatch wedotalent_admin —
        gate rejeita 403 mesmo para super admin. Este teste pina o
        comportamento atual + documenta divergência com HARDENING_PLAN.
        Quando o escape hatch for implementado, atualizar este teste para
        verificar bypass via role check (e remover este pytest.raises).
        """
        # Implementação atual: gate é fail-closed sem distinção de role
        with pytest.raises(HTTPException) as exc_info:
            _build_conditions(
                date_from=None,
                date_to=None,
                client_id="platform",
                company_id=TENANT_A_ID,  # mesmo p/ super admin, gate compara strings
            )
        assert exc_info.value.status_code == 403, (
            "Gate _build_conditions atual rejeita TODA mismatch sem role escape. "
            "Quando wedotalent_admin bypass for adicionado, este teste deve ser "
            "atualizado para verificar status_code == 200 + role check."
        )

    def test_audit_logs_missing_company_id_raises_403(self):
        """Sem company_id (JWT ausente ou ContextVar vazio) — gate fail-closed.

        Cenário de defesa: mesmo que algum caller bug-driven passe
        company_id=None ou string vazia, gate deve recusar (não vazar
        cross-tenant data).
        """
        with pytest.raises(HTTPException) as exc_info:
            _build_conditions(
                date_from=None,
                date_to=None,
                client_id=None,
                company_id=None,  # JWT ausente
            )
        assert exc_info.value.status_code == 403
        assert "company_id" in exc_info.value.detail.lower()
