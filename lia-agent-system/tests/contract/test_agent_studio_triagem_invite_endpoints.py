"""
Workstream A 2026-05-23 — Agent Studio triagem_invite REST endpoints contract tests.

Pin canonical behaviour for:
- PATCH /api/v1/agent-studio/agents/{agent_id}/triagem-invite/enabled
- POST  /api/v1/agent-studio/agents/{agent_id}/triagem-invite/initiate

Coverage areas:
1. Schema discipline: WeDoBaseModel (extra='forbid') rejects extra fields.
2. Multi-tenancy: company_id NEVER from payload (REGRA 2).
3. Per-agent capability gate: returns 403 when triagem_invite_enabled=False.
4. Delegation: initiate calls TriagemSessionService.create_session canonical.
5. Toggle endpoint: updates DB via repository + logs audit canonical.
6. Response shape: invite_url + triagem_url + token populated.

Pattern reference: test_agent_studio_voice_endpoints.py (Sprint 3.7 W4-1).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError


# ───────────────────────────── Helpers / Fixtures ──────────────────────────────


COMPANY_ID = "11111111-1111-1111-1111-111111111111"
OTHER_COMPANY = "22222222-2222-2222-2222-222222222222"
AGENT_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


def _make_fake_agent(*, triagem_invite_enabled: bool = False, company_id: str = COMPANY_ID):
    """Build a stand-in CustomAgent without hitting the DB."""
    return SimpleNamespace(
        id=AGENT_ID,
        company_id=company_id,
        name="TriagemInviteTestAgent",
        role="Recruiter",
        description="Custom recruiter agent for triagem_invite tests",
        system_prompt="You are LIA, a friendly recruiter assistant.",
        allowed_tools=[],
        excluded_tools=[],
        model_override=None,
        max_steps=8,
        temperature=0.7,
        enable_memory=True,
        context_level="full",
        config={"persona": {"tone": "friendly"}},
        voice_enabled=False,
        voip_enabled=False,
        whatsapp_enabled=False,
        triagem_invite_enabled=triagem_invite_enabled,
    )


def _make_fake_user(company_id: str = COMPANY_ID):
    return SimpleNamespace(id=uuid4(), company_id=company_id, role="admin")


def _make_app_with_overrides(*, agent, user=None) -> FastAPI:
    """Build a minimal FastAPI app with the triagem_invite router + overrides."""
    from app.api.v1 import agent_studio_triagem_invite
    from app.auth.dependencies import get_current_user
    from app.core.database import get_tenant_db
    from app.shared.security.require_company_id import require_company_id

    user = user or _make_fake_user(company_id=agent.company_id)

    app = FastAPI()
    app.include_router(agent_studio_triagem_invite.router, prefix="/api/v1")

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

    def test_enable_request_rejects_extra_fields(self):
        from app.api.v1.agent_studio_triagem_invite import TriagemInviteEnableRequest

        with pytest.raises(ValidationError):
            TriagemInviteEnableRequest(
                triagem_invite_enabled=True,
                ghost_field="should_be_rejected",
            )

    def test_initiate_request_rejects_extra_fields(self):
        from app.api.v1.agent_studio_triagem_invite import TriagemInviteInitiateRequest

        with pytest.raises(ValidationError):
            TriagemInviteInitiateRequest(
                candidate_id="cand-1",
                job_id="job-1",
                sneaky="bad",
            )

    def test_enable_request_rejects_company_id(self):
        """REGRA 2 Pydantic — company_id NEVER from payload."""
        from app.api.v1.agent_studio_triagem_invite import TriagemInviteEnableRequest

        with pytest.raises(ValidationError):
            TriagemInviteEnableRequest(
                triagem_invite_enabled=True,
                company_id=OTHER_COMPANY,
            )

    def test_initiate_request_rejects_company_id(self):
        from app.api.v1.agent_studio_triagem_invite import TriagemInviteInitiateRequest

        with pytest.raises(ValidationError):
            TriagemInviteInitiateRequest(
                candidate_id="cand-1",
                job_id="job-1",
                company_id=OTHER_COMPANY,
            )


# ───────────────────── PATCH /triagem-invite/enabled — toggle ─────────────────────


class TestToggleEnabled:
    def test_patch_enables_flag_via_repository(self):
        agent = _make_fake_agent(triagem_invite_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        with patch(
            "app.domains.agent_studio.repositories.custom_agent_repository.CustomAgentRepository.update_channel_flag",
            new_callable=AsyncMock,
        ) as mock_update:
            resp = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/enabled",
                json={"triagem_invite_enabled": True},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["agent_id"] == AGENT_ID
        assert body["triagem_invite_enabled"] is True
        # Repository called with canonical channel='triagem_invite'
        mock_update.assert_awaited_once()
        kwargs = mock_update.call_args.kwargs
        assert kwargs["channel"] == "triagem_invite"
        assert kwargs["enabled"] is True
        assert kwargs["agent_id"] == AGENT_ID
        assert kwargs["company_id"] == COMPANY_ID

    def test_patch_disables_flag(self):
        agent = _make_fake_agent(triagem_invite_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        with patch(
            "app.domains.agent_studio.repositories.custom_agent_repository.CustomAgentRepository.update_channel_flag",
            new_callable=AsyncMock,
        ) as mock_update:
            resp = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/enabled",
                json={"triagem_invite_enabled": False},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["triagem_invite_enabled"] is False
        mock_update.assert_awaited_once()

    def test_patch_skips_db_write_when_value_unchanged(self):
        """Idempotency: if flag already matches payload, skip update_channel_flag."""
        agent = _make_fake_agent(triagem_invite_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        with patch(
            "app.domains.agent_studio.repositories.custom_agent_repository.CustomAgentRepository.update_channel_flag",
            new_callable=AsyncMock,
        ) as mock_update:
            resp = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/enabled",
                json={"triagem_invite_enabled": True},  # same as agent state
            )

        assert resp.status_code == 200, resp.text
        mock_update.assert_not_awaited()

    def test_patch_returns_404_when_agent_not_found(self):
        # Build app where _load_agent_for_company returns None
        from app.api.v1 import agent_studio_triagem_invite
        from app.auth.dependencies import get_current_user
        from app.core.database import get_tenant_db
        from app.shared.security.require_company_id import require_company_id

        user = _make_fake_user()
        app = FastAPI()
        app.include_router(agent_studio_triagem_invite.router, prefix="/api/v1")

        async def _empty_db():
            db = MagicMock()
            scalar = MagicMock()
            scalar.scalar_one_or_none = MagicMock(return_value=None)
            db.execute = AsyncMock(return_value=scalar)
            yield db

        app.dependency_overrides[get_tenant_db] = _empty_db
        app.dependency_overrides[get_current_user] = lambda: user
        app.dependency_overrides[require_company_id] = lambda: COMPANY_ID

        client = TestClient(app)
        resp = client.patch(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/enabled",
            json={"triagem_invite_enabled": True},
        )
        assert resp.status_code == 404, resp.text


# ───────────────────── POST /triagem-invite/initiate — capability gate ───────────


class TestInitiateRespectsCapabilityGate:
    def test_returns_403_when_capability_disabled(self):
        agent = _make_fake_agent(triagem_invite_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        resp = client.post(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/initiate",
            json={"candidate_id": "cand-1", "job_id": "job-1"},
        )

        assert resp.status_code == 403, resp.text
        detail = resp.json()["detail"]
        assert detail["error"] == "agent_triagem_invite_disabled"

    def test_returns_invite_when_capability_enabled(self):
        agent = _make_fake_agent(triagem_invite_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        # Mock the canonical TriagemSessionService.create_session
        fake_session = SimpleNamespace(
            id=uuid4(),
            token="11111111-2222-3333-4444-555555555555",
            expires_at=None,
        )
        fake_svc = MagicMock()
        fake_svc.create_session = AsyncMock(return_value=fake_session)

        with patch(
            "app.domains.recruitment.services.triagem_session_service.get_triagem_service",
            return_value=fake_svc,
        ):
            resp = client.post(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/initiate",
                json={
                    "candidate_id": "cand-1",
                    "job_id": "job-1",
                    "candidate_email": "cand@example.com",
                    "invite_channel": "email",
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "invite_created"
        assert body["token"] == "11111111-2222-3333-4444-555555555555"
        assert body["triagem_url"] == "/triagem/11111111-2222-3333-4444-555555555555"
        assert body["invite_url"].endswith("/pt/triagem/11111111-2222-3333-4444-555555555555")
        assert body["agent_id"] == AGENT_ID

        # Verifica que delegou para TriagemSessionService.create_session com
        # company_id do JWT (NUNCA do payload — REGRA 2)
        fake_svc.create_session.assert_awaited_once()
        kwargs = fake_svc.create_session.call_args.kwargs
        assert kwargs["company_id"] == COMPANY_ID
        assert kwargs["candidate_id"] == "cand-1"
        assert kwargs["job_id"] == "job-1"
        assert kwargs["invite_channel"] == "email"

    def test_initiate_returns_503_when_service_fails(self):
        agent = _make_fake_agent(triagem_invite_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        fake_svc = MagicMock()
        fake_svc.create_session = AsyncMock(side_effect=RuntimeError("DB exploded"))

        with patch(
            "app.domains.recruitment.services.triagem_session_service.get_triagem_service",
            return_value=fake_svc,
        ):
            resp = client.post(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/triagem-invite/initiate",
                json={"candidate_id": "cand-1", "job_id": "job-1"},
            )

        assert resp.status_code == 503, resp.text
        detail = resp.json()["detail"]
        assert detail["error"] == "triagem_invite_failed"


# ───────────────────────── Repository channel mapping ──────────────────────────


class TestRepositoryChannelMapping:
    """C.5 + Workstream A canonical: triagem_invite ∈ _CHANNEL_COLUMN_MAP."""

    def test_triagem_invite_channel_registered(self):
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            _CHANNEL_COLUMN_MAP,
        )
        assert "triagem_invite" in _CHANNEL_COLUMN_MAP
        assert _CHANNEL_COLUMN_MAP["triagem_invite"] == "triagem_invite_enabled"

    @pytest.mark.asyncio
    async def test_update_channel_flag_accepts_triagem_invite(self):
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        db.execute = AsyncMock(return_value=MagicMock())
        db.commit = AsyncMock(return_value=None)
        repo = CustomAgentRepository(db)

        # Should not raise ValueError
        await repo.update_channel_flag(
            agent_id="agent-x",
            company_id="company-1",
            channel="triagem_invite",
            enabled=True,
        )
        db.execute.assert_awaited_once()
        db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_channel_flag_rejects_empty_company_id(self):
        from app.domains.agent_studio.repositories.custom_agent_repository import (
            CustomAgentRepository,
        )
        db = MagicMock()
        repo = CustomAgentRepository(db)

        with pytest.raises(ValueError):
            await repo.update_channel_flag(
                agent_id="agent-x",
                company_id="",
                channel="triagem_invite",
                enabled=True,
            )
