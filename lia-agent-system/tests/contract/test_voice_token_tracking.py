"""
Tests for P1 ticket: VoiceScreeningSession LLM token tracking for billing.

F-19 + W4-4 compute_voice_credits recebia tokens_input=0, tokens_output=0
porque VoiceScreeningSession nao trackeava metadados de tokens do Gemini.
Custo LLM voice era billing ghost no marketplace.

Fix:
- VoiceScreeningSession ganha llm_tokens_input + llm_tokens_output fields
- generate_lia_response acumula tokens do response.usage_metadata por turn
- Redis state serialization preserva (backward compat: defaults 0)
- finalize/Studio plugin passa tokens reais para compute_voice_credits

Audit ref: F-19 P1 backlog + Sprint 3.7 ticket #1
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_session(**overrides):
    """Build a minimal VoiceScreeningSession for state-shape tests."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningSession,
    )

    defaults = {
        "session_id": "sess-tok-1",
        "candidate_id": "cand-1",
        "candidate_name": "Test Candidate",
        "job_title": "Engineer",
        "company_id": "comp-1",
        "phone_number": "+5511999998888",
    }
    defaults.update(overrides)
    return VoiceScreeningSession(**defaults)


# ─── Schema: dataclass fields ─────────────────────────────────────────────────

def test_voice_session_has_token_tracking_fields():
    """P1 #1: VoiceScreeningSession exposes llm_tokens_input/llm_tokens_output."""
    session = _make_session()
    assert hasattr(session, "llm_tokens_input"), (
        "VoiceScreeningSession must expose llm_tokens_input for canonical billing."
    )
    assert hasattr(session, "llm_tokens_output"), (
        "VoiceScreeningSession must expose llm_tokens_output for canonical billing."
    )


def test_voice_session_token_defaults_zero():
    """P1 #1: new sessions start with 0 tokens (backward-compat baseline)."""
    session = _make_session()
    assert session.llm_tokens_input == 0
    assert session.llm_tokens_output == 0


def test_voice_session_tokens_are_mutable_int():
    """P1 #1: tokens accumulate (counter pattern, not immutable)."""
    session = _make_session()
    session.llm_tokens_input += 150
    session.llm_tokens_output += 75
    assert session.llm_tokens_input == 150
    assert session.llm_tokens_output == 75


# ─── Schema: Redis state serialization round-trip ─────────────────────────────

def test_session_state_serialization_preserves_tokens():
    """P1 #1: _session_to_state + _state_to_session preserves token counts."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    session = _make_session()
    session.llm_tokens_input = 4200
    session.llm_tokens_output = 1800

    orch = VoiceScreeningOrchestrator()
    state = orch._session_to_state(session)
    assert state["llm_tokens_input"] == 4200, (
        f"_session_to_state must serialize llm_tokens_input. Got: {state}"
    )
    assert state["llm_tokens_output"] == 1800

    revived = orch._state_to_session(state)
    assert revived.llm_tokens_input == 4200
    assert revived.llm_tokens_output == 1800


def test_legacy_state_without_tokens_defaults_zero():
    """P1 #1: backward-compat — legacy sessions in Redis (pre-token field)
    deserialize cleanly with defaults 0."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    orch = VoiceScreeningOrchestrator()
    # Legacy state — no llm_tokens_* keys
    legacy_state = {
        "session_id": "legacy-sess",
        "candidate_id": "cand-legacy",
        "candidate_name": "Legacy",
        "job_title": "Eng",
        "company_id": "comp-1",
        "phone_number": "+5511999998888",
        "job_id": None,
        "call_sid": None,
        "status": "pending",
        "language": "pt-BR",
        "transcript_segments": [],
        "questions_asked": [],
        "started_at": None,
        "ended_at": None,
        "wsi_result": None,
        "error": None,
        "consent_verified": False,
        "job_context": None,
        "presentation_done": False,
        "voice_provider": "twilio",
    }
    revived = orch._state_to_session(legacy_state)
    assert revived.llm_tokens_input == 0
    assert revived.llm_tokens_output == 0


# ─── Billing wiring: finalize passes real tokens ──────────────────────────────

@pytest.mark.asyncio
async def test_record_voice_billing_uses_session_tokens():
    """P1 #1: _record_voice_billing reads session.llm_tokens_* and passes to
    compute_voice_credits (not hardcoded 0)."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    orch = VoiceScreeningOrchestrator()
    session = _make_session()
    session.llm_tokens_input = 3000
    session.llm_tokens_output = 1200

    # Stub _resolve_pricing_tier so we don't need DB
    async def _fake_resolve_tier(*a, **kw):
        return "pro"
    orch._resolve_pricing_tier = _fake_resolve_tier  # type: ignore[method-assign]

    captured = {}

    def _fake_compute(*, total_audio_seconds, tokens_input, tokens_output, tier):
        captured.update(
            total_audio_seconds=total_audio_seconds,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tier=tier,
        )
        return 99  # credits

    # Mock marketplace record_execution (it's imported inside the method)
    from unittest.mock import AsyncMock
    fake_marketplace = MagicMock()
    fake_marketplace.record_execution = AsyncMock()
    fake_db = MagicMock()

    with patch(
        "app.services.agent_pricing.compute_voice_credits", _fake_compute
    ), patch(
        "app.services.agent_marketplace_service.agent_marketplace_service",
        fake_marketplace,
    ):
        await orch._record_voice_billing(
            session=session, duration_seconds=120, db=fake_db
        )

    assert captured.get("tokens_input") == 3000, (
        f"compute_voice_credits must receive real tokens_input from session. "
        f"Got: {captured}"
    )
    assert captured.get("tokens_output") == 1200, (
        f"compute_voice_credits must receive real tokens_output from session. "
        f"Got: {captured}"
    )


@pytest.mark.asyncio
async def test_record_voice_billing_zero_tokens_legacy_session():
    """P1 #1: legacy sessions (no token tracking) still bill audio + Twilio."""
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    orch = VoiceScreeningOrchestrator()
    session = _make_session()  # defaults: tokens=0

    async def _fake_resolve_tier(*a, **kw):
        return "pro"
    orch._resolve_pricing_tier = _fake_resolve_tier  # type: ignore[method-assign]

    captured = {}

    def _fake_compute(*, total_audio_seconds, tokens_input, tokens_output, tier):
        captured.update(
            total_audio_seconds=total_audio_seconds,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tier=tier,
        )
        return 5

    from unittest.mock import AsyncMock
    fake_marketplace = MagicMock()
    fake_marketplace.record_execution = AsyncMock()
    fake_db = MagicMock()

    with patch(
        "app.services.agent_pricing.compute_voice_credits", _fake_compute
    ), patch(
        "app.services.agent_marketplace_service.agent_marketplace_service",
        fake_marketplace,
    ):
        await orch._record_voice_billing(
            session=session, duration_seconds=60, db=fake_db
        )

    # No regression: zero tokens still emit billing call w/ correct audio
    assert captured["tokens_input"] == 0
    assert captured["tokens_output"] == 0
    assert captured["total_audio_seconds"] == 60
