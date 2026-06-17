"""
T5a UX Transformação 5 — Agent Studio WhatsApp REST endpoints contract tests.

Pin canonical behaviour for:
- POST   /api/v1/agent-studio/agents/{agent_id}/whatsapp/initiate
- PATCH  /api/v1/agent-studio/agents/{agent_id}/whatsapp/enabled

Coverage areas:
1. Schema discipline: WeDoBaseModel (extra='forbid') rejects extra fields.
2. Per-agent toggle: returns ``agent_whatsapp_disabled`` when whatsapp_enabled=False.
3. Multi-tenancy: company_id ALWAYS from JWT, NEVER from payload (REGRA 2).
4. Runtime wiring: initiate delegates to CustomAgentRuntime channel='whatsapp'.
5. Toggle endpoint: updates DB + logs audit canonical.
6. Canonical Pydantic: response models declared, request bodies use extra='forbid'.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


COMPANY_ID = "11111111-1111-1111-1111-111111111111"
OTHER_COMPANY = "22222222-2222-2222-2222-222222222222"
AGENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _make_fake_agent(*, whatsapp_enabled: bool = False, company_id: str = COMPANY_ID):
    return SimpleNamespace(
        id=AGENT_ID,
        company_id=company_id,
        name="WhatsAppTestAgent",
        role="Recruiter",
        description="Custom recruiter agent for whatsapp tests",
        system_prompt="You are LIA.",
        allowed_tools=[],
        excluded_tools=[],
        model_override=None,
        max_steps=8,
        temperature=0.7,
        enable_memory=True,
        context_level="full",
        config={"persona": {"tone": "friendly"}},
        whatsapp_enabled=whatsapp_enabled,
        voice_enabled=False,
    )


def _make_fake_user(company_id: str = COMPANY_ID):
    return SimpleNamespace(id=uuid4(), company_id=company_id, role="admin")


def _make_app_with_overrides(*, agent, user=None) -> FastAPI:
    """Build a minimal FastAPI app with the whatsapp router + auth/db overrides."""
    from app.api.v1 import agent_studio_whatsapp
    from app.auth.dependencies import get_current_user
    from app.core.database import get_tenant_db
    from app.shared.security.require_company_id import require_company_id

    user = user or _make_fake_user(company_id=agent.company_id)

    app = FastAPI()
    app.include_router(agent_studio_whatsapp.router, prefix="/api/v1")

    async def _fake_db():
        db = MagicMock()
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=agent)
        db.execute = AsyncMock(return_value=scalar)
        db.commit = AsyncMock(return_value=None)
        db.refresh = AsyncMock(return_value=None)
        yield db

    app.dependency_overrides[get_tenant_db] = _fake_db
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[require_company_id] = lambda: agent.company_id

    return app


# ───────────────────────────── Schema discipline ───────────────────────────────


class TestSchemaDiscipline:
    """REGRA 1 Pydantic — request bodies use extra='forbid' (via WeDoBaseModel)."""

    def test_initiate_request_rejects_extra_fields(self):
        from app.api.v1.agent_studio_whatsapp import WhatsAppInitiateRequest

        with pytest.raises(ValidationError):
            WhatsAppInitiateRequest(
                candidate_id="cand-1",
                candidate_phone="+5511999999999",
                message="Olá",
                ghost_field="should_be_rejected",
            )

    def test_enable_request_rejects_extra_fields(self):
        from app.api.v1.agent_studio_whatsapp import WhatsAppEnableRequest

        with pytest.raises(ValidationError):
            WhatsAppEnableRequest(whatsapp_enabled=True, sneaky="bad")

    def test_initiate_request_rejects_company_id_field(self):
        """REGRA 2 Pydantic — company_id NEVER from payload."""
        from app.api.v1.agent_studio_whatsapp import WhatsAppInitiateRequest

        with pytest.raises(ValidationError):
            WhatsAppInitiateRequest(
                candidate_id="cand-1",
                candidate_phone="+5511999999999",
                message="Olá",
                company_id=OTHER_COMPANY,
            )

    def test_enable_request_rejects_company_id_field(self):
        from app.api.v1.agent_studio_whatsapp import WhatsAppEnableRequest

        with pytest.raises(ValidationError):
            WhatsAppEnableRequest(whatsapp_enabled=True, company_id=OTHER_COMPANY)


# ──────────────── POST /whatsapp/initiate — whatsapp_enabled gate ─────────────


class TestInitiateRespectsPerAgentToggle:
    def test_returns_agent_whatsapp_disabled_when_flag_off(self):
        agent = _make_fake_agent(whatsapp_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        response = client.post(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/whatsapp/initiate",
            json={
                "candidate_id": "cand-1",
                "candidate_phone": "+5511999999999",
                "message": "Olá",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "agent_whatsapp_disabled"
        assert body["agent_id"] == AGENT_ID

    def test_delegates_to_runtime_when_enabled(self):
        agent = _make_fake_agent(whatsapp_enabled=True)
        app = _make_app_with_overrides(agent=agent)

        fake_output = SimpleNamespace(
            message="response",
            metadata={
                "status": "message_sent",
                "agent_id": AGENT_ID,
                "plugin_name": "whatsapp_custom_agent",
                "delivery_status": "sent",
                "delivery_message_id": "wamid.123",
                "response_text": "Ola candidato!",
            },
        )

        with patch(
            "app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime"
        ) as mock_get:
            mock_runtime = MagicMock()
            mock_runtime.execute = AsyncMock(return_value=fake_output)
            mock_get.return_value = mock_runtime

            client = TestClient(app)
            response = client.post(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/whatsapp/initiate",
                json={
                    "candidate_id": "cand-1",
                    "candidate_phone": "+5511999999999",
                    "candidate_name": "João",
                    "message": "Olá, sobre a vaga",
                    "job_title": "Engenheiro",
                },
            )
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "message_sent"
            assert body["delivery_message_id"] == "wamid.123"
            # Verify runtime called with channel="whatsapp"
            mock_runtime.execute.assert_called_once()
            call_kwargs = mock_runtime.execute.call_args.kwargs
            assert call_kwargs["channel"] == "whatsapp"
            assert call_kwargs["sender_phone"] == "+5511999999999"
            assert call_kwargs["company_id"] == COMPANY_ID


class TestNotFoundContract:
    def test_returns_404_when_agent_missing(self):
        agent = _make_fake_agent(whatsapp_enabled=True)
        app = _make_app_with_overrides(agent=agent)

        # Override DB to return None
        from app.core.database import get_tenant_db

        async def _fake_db_empty():
            db = MagicMock()
            scalar = MagicMock()
            scalar.scalar_one_or_none = MagicMock(return_value=None)
            db.execute = AsyncMock(return_value=scalar)
            yield db

        app.dependency_overrides[get_tenant_db] = _fake_db_empty
        client = TestClient(app)

        response = client.post(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/whatsapp/initiate",
            json={
                "candidate_id": "cand-1",
                "candidate_phone": "+5511999999999",
                "message": "oi",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"]["error"] == "agent_not_found"


# ─────────────── PATCH /whatsapp/enabled — toggle endpoint ──────────────────


class TestPatchWhatsAppEnabled:
    def test_toggle_updates_agent_and_returns_new_state(self):
        agent = _make_fake_agent(whatsapp_enabled=False)
        app = _make_app_with_overrides(agent=agent)

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as mock_audit_cls:
            instance = MagicMock()
            instance.log_decision = AsyncMock(return_value=None)
            mock_audit_cls.return_value = instance

            client = TestClient(app)
            response = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/whatsapp/enabled",
                json={"whatsapp_enabled": True},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["whatsapp_enabled"] is True
            assert body["agent_id"] == AGENT_ID

    def test_audit_log_called_on_toggle(self):
        agent = _make_fake_agent(whatsapp_enabled=False)
        app = _make_app_with_overrides(agent=agent)

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as mock_audit_cls:
            instance = MagicMock()
            instance.log_decision = AsyncMock(return_value=None)
            mock_audit_cls.return_value = instance

            client = TestClient(app)
            client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/whatsapp/enabled",
                json={"whatsapp_enabled": True},
            )
            instance.log_decision.assert_called_once()
            kwargs = instance.log_decision.call_args.kwargs
            assert kwargs["decision_type"] == "custom_agent_whatsapp_toggled"
            assert kwargs["action"] == "whatsapp_enabled_set"
            assert kwargs["company_id"] == COMPANY_ID
