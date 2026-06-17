"""
Sprint 3.7 W4-1 — Agent Studio voice REST endpoints contract tests.

Pin canonical behaviour for:
- POST   /api/v1/agent-studio/agents/{agent_id}/voice/initiate
- GET    /api/v1/agent-studio/agents/{agent_id}/voice/sessions/{session_id}
- PATCH  /api/v1/agent-studio/agents/{agent_id}/voice/enabled

Coverage areas:
1. Schema discipline: WeDoBaseModel (extra='forbid') rejects extra fields.
2. Per-agent toggle: returns ``agent_voice_disabled`` when voice_enabled=False.
3. Multi-tenancy: company_id always from JWT, never from payload.
4. Runtime wiring: initiate delegates to CustomAgentRuntime channel='voice'.
5. Session status: 404 when expired, 200 with state when present.
6. Toggle endpoint: updates DB + logs audit canonical.
7. Canonical Pydantic: response models declared, request bodies use extra='forbid'.
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


def _make_fake_agent(*, voice_enabled: bool = False, company_id: str = COMPANY_ID):
    """Build a stand-in CustomAgent without hitting the DB."""
    return SimpleNamespace(
        id=AGENT_ID,
        company_id=company_id,
        name="VoiceTestAgent",
        role="Recruiter",
        description="Custom recruiter agent for voice screening tests",
        system_prompt="You are LIA, a friendly recruiter assistant.",
        allowed_tools=[],
        excluded_tools=[],
        model_override=None,
        max_steps=8,
        temperature=0.7,
        enable_memory=True,
        context_level="full",
        config={"persona": {"tone": "friendly"}},
        voice_enabled=voice_enabled,
    )


def _make_fake_user(company_id: str = COMPANY_ID):
    return SimpleNamespace(id=uuid4(), company_id=company_id, role="admin")


def _make_app_with_overrides(*, agent, user=None) -> FastAPI:
    """Build a minimal FastAPI app with the voice router + auth/db overrides."""
    from app.api.v1 import agent_studio_voice
    from app.auth.dependencies import get_current_user
    from app.core.database import get_tenant_db
    from app.shared.security.require_company_id import require_company_id

    user = user or _make_fake_user(company_id=agent.company_id)

    app = FastAPI()
    app.include_router(agent_studio_voice.router, prefix="/api/v1")

    async def _fake_db():
        db = MagicMock()
        # Build async-compatible execute() returning result with .scalar_one_or_none()
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
        from app.api.v1.agent_studio_voice import VoiceInitiateRequest

        with pytest.raises(ValidationError):
            VoiceInitiateRequest(
                candidate_id="cand-1",
                ghost_field="should_be_rejected",
            )

    def test_enable_request_rejects_extra_fields(self):
        from app.api.v1.agent_studio_voice import VoiceEnableRequest

        with pytest.raises(ValidationError):
            VoiceEnableRequest(voice_enabled=True, sneaky="bad")

    def test_initiate_request_rejects_company_id_field(self):
        """REGRA 2 Pydantic — company_id NEVER from payload."""
        from app.api.v1.agent_studio_voice import VoiceInitiateRequest

        with pytest.raises(ValidationError):
            VoiceInitiateRequest(candidate_id="cand-1", company_id=OTHER_COMPANY)

    def test_enable_request_rejects_company_id_field(self):
        from app.api.v1.agent_studio_voice import VoiceEnableRequest

        with pytest.raises(ValidationError):
            VoiceEnableRequest(voice_enabled=True, company_id=OTHER_COMPANY)


# ───────────────────── POST /voice/initiate — voice_enabled gate ────────────────────


class TestInitiateRespectsPerAgentToggle:
    def test_returns_agent_voice_disabled_when_flag_off(self):
        agent = _make_fake_agent(voice_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        resp = client.post(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/initiate",
            json={"candidate_id": "cand-1", "candidate_phone": "+5511999999999"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "agent_voice_disabled"
        assert body["session_id"] == ""
        assert body["agent_id"] == AGENT_ID

    def test_returns_session_initiated_when_flag_on(self):
        """When voice_enabled=True, runtime is invoked and metadata is reflected."""
        agent = _make_fake_agent(voice_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        fake_runtime = MagicMock()
        fake_output = SimpleNamespace(
            message="ok",
            confidence=1.0,
            metadata={
                "status": "session_initiated",
                "voice_session_id": "vs-abc-123",
                "call_sid": "CA0000",
                "is_voip": False,
                "plugin_name": "StudioVoicePlugin",
                "session_id": "vs-abc-123",
            },
        )
        fake_runtime.execute = AsyncMock(return_value=fake_output)

        with patch(
            "app.domains.agent_studio.custom_agent_runtime.get_or_create_runtime",
            return_value=fake_runtime,
        ):
            resp = client.post(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/initiate",
                json={
                    "candidate_id": "cand-1",
                    "candidate_phone": "+5511999999999",
                    "job_id": "job-x",
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "session_initiated"
        assert body["session_id"] == "vs-abc-123"
        assert body["call_sid"] == "CA0000"
        assert body["is_voip"] is False
        assert body["plugin_name"] == "StudioVoicePlugin"

        # Verify runtime was called with channel='voice' + context carrying candidate
        call_kwargs = fake_runtime.execute.call_args.kwargs
        assert call_kwargs.get("channel") == "voice"
        assert call_kwargs.get("company_id") == COMPANY_ID
        ctx = call_kwargs.get("context") or {}
        assert ctx.get("candidate_id") == "cand-1"
        assert ctx.get("candidate_phone") == "+5511999999999"
        assert ctx.get("job_id") == "job-x"


# ───────────────────────── 404 contract ─────────────────────────────────────


class TestNotFoundContract:
    def test_initiate_returns_404_when_agent_missing(self):
        """Loading missing agent → 404. Tenant isolation enforced via where(company_id=...)."""
        app = _make_app_with_overrides(agent=None) if False else None  # use special override
        from app.api.v1 import agent_studio_voice
        from app.auth.dependencies import get_current_user
        from app.core.database import get_tenant_db
        from app.shared.security.require_company_id import require_company_id

        app = FastAPI()
        app.include_router(agent_studio_voice.router, prefix="/api/v1")

        async def _empty_db():
            db = MagicMock()
            scalar = MagicMock()
            scalar.scalar_one_or_none = MagicMock(return_value=None)
            db.execute = AsyncMock(return_value=scalar)
            yield db

        app.dependency_overrides[get_tenant_db] = _empty_db
        app.dependency_overrides[get_current_user] = lambda: _make_fake_user()
        app.dependency_overrides[require_company_id] = lambda: COMPANY_ID

        client = TestClient(app)
        resp = client.post(
            f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/initiate",
            json={"candidate_id": "cand-1"},
        )
        assert resp.status_code == 404
        assert "agent_not_found" in resp.text


# ───────────────────────── GET /voice/sessions ────────────────────────────────


class TestGetSessionStatus:
    def test_returns_404_when_session_expired(self):
        agent = _make_fake_agent(voice_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        fake_repo = MagicMock()
        fake_repo.load_session_state = AsyncMock(return_value=None)

        with patch(
            "app.domains.voice.repositories.voice_session_redis_repository.get_voice_session_repository",
            return_value=fake_repo,
        ):
            resp = client.get(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/sessions/vs-missing"
            )

        assert resp.status_code == 404
        assert "session_not_found" in resp.text

    def test_returns_state_when_present(self):
        agent = _make_fake_agent(voice_enabled=True)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        fake_repo = MagicMock()
        fake_repo.load_session_state = AsyncMock(
            return_value={
                "status": "in_progress",
                "duration_seconds": 42,
                "transcript_segments": [
                    {"role": "lia", "text": "Olá"},
                    {"role": "candidate", "text": "Oi"},
                ],
                "summary": None,
            }
        )

        with patch(
            "app.domains.voice.repositories.voice_session_redis_repository.get_voice_session_repository",
            return_value=fake_repo,
        ):
            resp = client.get(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/sessions/vs-abc"
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "in_progress"
        assert body["duration_seconds"] == 42
        assert body["transcript_segments_count"] == 2
        assert body["has_transcript"] is True

        # Confirm load_session_state was called with company_id from JWT
        _, kwargs = fake_repo.load_session_state.call_args
        assert kwargs.get("company_id") == COMPANY_ID
        assert kwargs.get("session_id") == "vs-abc"


# ───────────────────────── PATCH /voice/enabled ───────────────────────────────


class TestPatchVoiceEnabled:
    def test_toggle_updates_value_and_returns_new_state(self):
        agent = _make_fake_agent(voice_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAuditSvc:
            instance = MockAuditSvc.return_value
            instance.log_decision = AsyncMock(return_value=None)

            resp = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/enabled",
                json={"voice_enabled": True},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["voice_enabled"] is True
        assert body["agent_id"] == AGENT_ID
        # Agent state was mutated in-place (SimpleNamespace acts like SQLAlchemy obj)
        assert agent.voice_enabled is True

    def test_toggle_logs_audit_canonical(self):
        agent = _make_fake_agent(voice_enabled=False)
        app = _make_app_with_overrides(agent=agent)
        client = TestClient(app)

        with patch(
            "app.shared.compliance.audit_service.AuditService"
        ) as MockAuditSvc:
            instance = MockAuditSvc.return_value
            instance.log_decision = AsyncMock(return_value=None)

            resp = client.patch(
                f"/api/v1/agent-studio/agents/{AGENT_ID}/voice/enabled",
                json={"voice_enabled": True},
            )

        assert resp.status_code == 200
        instance.log_decision.assert_awaited_once()
        call_kwargs = instance.log_decision.call_args.kwargs
        assert call_kwargs.get("company_id") == COMPANY_ID
        assert call_kwargs.get("decision_type") == "custom_agent_voice_toggled"
        assert call_kwargs.get("action") == "voice_enabled_set"
        assert call_kwargs.get("decision") == "approved"
        reasoning = call_kwargs.get("reasoning") or []
        assert any(f"agent_id={AGENT_ID}" in r for r in reasoning)


# ───────────────────────── Canonical Pydantic discipline ───────────────────────


class TestCanonicalPydanticConventions:
    def test_request_models_use_wedobasemodel(self):
        """REGRA 1: request bodies inherit WeDoBaseModel (extra='forbid')."""
        from app.api.v1.agent_studio_voice import (
            VoiceInitiateRequest,
            VoiceEnableRequest,
        )
        from app.shared.types import WeDoBaseModel

        assert issubclass(VoiceInitiateRequest, WeDoBaseModel)
        assert issubclass(VoiceEnableRequest, WeDoBaseModel)

    def test_response_models_inherit_wedobasemodel(self):
        """Response models also use canonical base."""
        from app.api.v1.agent_studio_voice import (
            VoiceInitiateResponse,
            VoiceSessionStatusResponse,
            VoiceEnableResponse,
        )
        from app.shared.types import WeDoBaseModel

        assert issubclass(VoiceInitiateResponse, WeDoBaseModel)
        assert issubclass(VoiceSessionStatusResponse, WeDoBaseModel)
        assert issubclass(VoiceEnableResponse, WeDoBaseModel)
