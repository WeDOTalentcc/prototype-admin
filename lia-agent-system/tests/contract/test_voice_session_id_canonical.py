"""
Phone test físico 2026-05-23 — Bug #102 regression sensor.

Discovery context:
- Phone call placed via /api/v1/twilio-voice/initiate
- Twilio call connected, LIA spoke successfully
- BUT wsi_session registration failed with:
    asyncpg.exceptions.DataError: invalid input for query argument $1:
    'system:7e159d26-...' (invalid UUID 'system:UUID': length must be
    between 32..36 characters, got 43)

Root cause:
- voice_screening_orchestrator.py:967 generated session_id as
  f"system:{uuid4()}" (43 chars total, vs UUID 36 chars)
- The 'system:' prefix is NEVER consumed anywhere (only assigned)
- wsi_sessions.id is PostgreSQL UUID column → asyncpg DataError on INSERT

Fix canonical:
- Generate plain UUID via str(uuid4()) — no 'system:' namespace prefix
- session_id is internal-only; namespacing UUIDs serves no purpose
  (collision space is 2^122 — no risk of mixing with externally-provided)

This sensor pins the invariant: session.session_id MUST be valid UUID (36 chars).
"""
from __future__ import annotations

import re
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.domains.voice.services.voice_screening_orchestrator import (
    VoiceScreeningOrchestrator,
)


UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class TestSessionIdCanonicalFormat:
    """Bug #102: session_id MUST be plain UUID, not 'system:UUID'."""

    @pytest.mark.asyncio
    async def test_initiate_screening_generates_plain_uuid_session_id(
        self, monkeypatch
    ):
        """initiate_screening_call MUST NOT prepend 'system:' to session_id."""
        from app.domains.voice.services import voice_screening_orchestrator as mod

        orch = VoiceScreeningOrchestrator()
        # Drop installed plugins to isolate the test from WSI hook side effects
        orch._plugins = []

        # Bypass consent + twilio dependencies
        orch.verify_consent = AsyncMock(return_value=None)
        orch.persist_session_state = AsyncMock()
        orch._store_session = AsyncMock()
        orch._log_initiate_call_audit = AsyncMock()

        async def _fake_circuit_call(fn, **kwargs):
            return {"success": True, "call_sid": "CA_TEST_FAKE"}

        monkeypatch.setattr(
            mod.TWILIO_VOICE_CIRCUIT, "call", _fake_circuit_call
        )
        monkeypatch.setattr(
            mod, "_twilio_voice_service", MagicMock()
        )

        session = await orch.initiate_call(
            candidate_id="74ef1007-fdc0-5b2a-ba07-da8c33815f2f",
            candidate_name="Bug Fix Smoke",
            phone_number="+5511941425115",
            job_title="Re-test post fix",
            company_id="00000000-0000-4000-a000-000000000001",
            db=None,
        )

        # CORE INVARIANT: session_id must NOT have 'system:' prefix
        assert not session.session_id.startswith("system:"), (
            f"Bug #102 regression: session_id has 'system:' prefix: "
            f"{session.session_id!r} (43 chars breaks UUID columns)"
        )

        # CORE INVARIANT: session_id must be valid UUID (36 chars)
        assert len(session.session_id) == 36, (
            f"session_id must be 36 chars (UUID format), got "
            f"{len(session.session_id)} chars: {session.session_id!r}"
        )
        assert UUID_REGEX.match(session.session_id), (
            f"session_id must match UUID regex: {session.session_id!r}"
        )

        # Parsing as UUID must succeed (will raise if format wrong)
        UUID(session.session_id)

    def test_orchestrator_source_does_not_contain_system_prefix_assignment(self):
        """Static guard: code does not reintroduce f'system:{uuid4()}'.

        Defense-in-depth: even if behavior test passes via mocking, this
        protects against accidental re-add via copy-paste from history.
        """
        import inspect
        from app.domains.voice.services import voice_screening_orchestrator

        src = inspect.getsource(voice_screening_orchestrator)
        # The pattern that caused Bug #102:
        assert 'f"system:{uuid4()}"' not in src, (
            "Bug #102 regression: source contains f'system:{uuid4()}' — "
            "session_id must be plain UUID without 'system:' prefix"
        )
        assert "f'system:{uuid4()}'" not in src, (
            "Bug #102 regression: source contains f'system:{uuid4()}' — "
            "session_id must be plain UUID without 'system:' prefix"
        )
