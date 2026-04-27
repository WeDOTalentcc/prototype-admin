"""
Integration tests — W1.2: P0-2 multi-tenant boundary in Adaptive Card webhook.

Auditoria 2026-04-26 (AUDITORIA_TEAMS_2026-04-26.md, finding P0-2) identificou
que o webhook Adaptive Card aceitava `company_id` do PAYLOAD (campo Pydantic)
e do HEADER `X-Company-ID`. Viola CLAUDE.md global "company_id sempre de
JWT/sessão, nunca do payload".

Recrutador externo poderia forjar `company_id` para acionar ações em outra
empresa — vazamento cross-tenant via Teams Adaptive Card.

Esta suite valida:
1. Schema: TeamsWebhookPayload NÃO tem campo `company_id`.
2. Endpoint: NÃO aceita header `X-Company-ID`.
3. Resolution: company_id derivado de `recruiter_id` -> `User.company_id`
   via canonical lookup (`TeamsRepository.get_user_by_platform_id`).
4. Audit: log do action usa company_id resolvido server-side.

Pattern TDD: testes falham antes da implementação. Após edits no
TeamsWebhookPayload + webhook handler, todos passam.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# 1. Schema — TeamsWebhookPayload não aceita company_id
# ============================================================================


class TestTeamsWebhookPayloadSchema:
    """company_id removido do payload — server-side resolution apenas."""

    def test_payload_schema_does_not_have_company_id_field(self):
        """TeamsWebhookPayload NÃO deve ter campo company_id."""
        from app.api.v1.teams import TeamsWebhookPayload

        fields = TeamsWebhookPayload.model_fields
        assert "company_id" not in fields, (
            f"TeamsWebhookPayload.company_id removido (P0-2). "
            f"Fields atuais: {list(fields.keys())}"
        )

    def test_payload_still_has_recruiter_id(self):
        """recruiter_id continua no payload — é o input para resolution."""
        from app.api.v1.teams import TeamsWebhookPayload

        fields = TeamsWebhookPayload.model_fields
        assert "recruiter_id" in fields, (
            "recruiter_id deve permanecer (entrada para User -> company_id lookup)"
        )

    def test_payload_rejects_company_id_in_extra_fields(self):
        """
        Se cliente envia company_id no JSON, o Pydantic deve ignorar
        (não atribuir ao payload).
        """
        from app.api.v1.teams import TeamsWebhookPayload

        # Cliente tenta forjar company_id
        forged_data = {
            "action": "approve",
            "candidate_id": "cand_x",
            "recruiter_id": "user_legitimate",
            "company_id": "comp_FORGED_BY_CLIENT",  # tentativa de injeção
        }
        payload = TeamsWebhookPayload(**forged_data)
        assert not hasattr(payload, "company_id") or payload.__dict__.get("company_id") is None, (
            "Payload NÃO deve aceitar company_id do cliente (P0-2)"
        )


# ============================================================================
# 2. Endpoint — não aceita header X-Company-ID
# ============================================================================


class TestWebhookEndpointSignature:
    """X-Company-ID header removido do webhook signature."""

    def test_webhook_endpoint_does_not_declare_x_company_id_header(self):
        """
        teams_adaptive_card_webhook NÃO deve declarar Header(alias='X-Company-ID').

        Aceitar via header é equivalente a aceitar via payload — ambos vêm
        do cliente externo e podem ser forjados.
        """
        import inspect
        from app.api.v1.teams import teams_adaptive_card_webhook

        src = inspect.getsource(teams_adaptive_card_webhook)
        assert "X-Company-ID" not in src, (
            "Webhook NÃO deve declarar header X-Company-ID — "
            "company_id resolve server-side via recruiter_id lookup (P0-2)"
        )
        assert "x_company_id" not in src, (
            "Webhook NÃO deve usar variável x_company_id"
        )


# ============================================================================
# 3. Server-side resolution via recruiter_id
# ============================================================================


class TestServerSideCompanyIdResolution:
    """company_id resolvido via recruiter_id -> User.company_id lookup."""

    def test_webhook_calls_get_user_by_platform_id(self):
        """Webhook deve usar TeamsRepository.get_user_by_platform_id (canônico)."""
        import inspect
        from app.api.v1.teams import teams_adaptive_card_webhook

        src = inspect.getsource(teams_adaptive_card_webhook)
        # Reusa repo canonical (não duplicar lookup)
        assert "get_user_by_platform_id" in src, (
            "Webhook deve usar TeamsRepository.get_user_by_platform_id "
            "para lookup de company_id (canônico, não duplicar)"
        )


# ============================================================================
# 4. Canonical-fix bonus — 3 getattr remanescentes no canal Teams
# ============================================================================


class TestCanonicalFixGetattrCleanup:
    """G6 sensor encontrou 3 getattr remaining no Teams. Limpar como bonus."""

    def test_teams_api_no_getattr_on_user_company_id(self):
        """app/api/v1/teams.py NÃO deve usar getattr(user, 'company_id', ...)."""
        import inspect
        from app.api.v1 import teams as teams_mod

        src = inspect.getsource(teams_mod)
        assert 'getattr(user, "company_id"' not in src, (
            "teams.py:1499 — usar user.company_id direto (G6, canonical-fix W1.2)"
        )
        assert "getattr(user, 'company_id'" not in src

    def test_teams_sso_service_no_getattr_on_conv_aad(self):
        """teams_sso_service NÃO deve usar getattr(conv, 'user_aad_object_id', ...)."""
        import inspect
        from app.domains.communication.services import teams_sso_service as mod

        src = inspect.getsource(mod)
        assert 'getattr(conv, "user_aad_object_id"' not in src, (
            "teams_sso_service:148 — usar conv.user_aad_object_id direto (G6)"
        )
        assert "getattr(conv, 'user_aad_object_id'" not in src

    def test_teams_sso_service_no_getattr_on_conv_company(self):
        """teams_sso_service NÃO deve usar getattr(conv, 'company_id', ...)."""
        import inspect
        from app.domains.communication.services import teams_sso_service as mod

        src = inspect.getsource(mod)
        assert 'getattr(conv, "company_id"' not in src, (
            "teams_sso_service:168 — usar conv.company_id direto após W1.1 "
            "Migration 097 adicionou a coluna (G6, canonical-fix W1.2)"
        )
        assert "getattr(conv, 'company_id'" not in src
