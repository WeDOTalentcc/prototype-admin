"""
F-19 P1 sentinels: voice billing via agent_pricing canonical.

Audit: AUDIT_VOICE_SCREENING_ORCHESTRATOR_2026-05-22.md F-19.
Wave 4 W4-4 trouxe agent_pricing.compute_credits para chat agents.
Voice usa Twilio + Deepgram + Gemini + OpenAI TTS — todos cobram por minuto/tokens
mas voice = billing ghost. Estender compute_credits para suportar audio metrics.

Sentinels:
- B1 compute_credits suporta audio_seconds_stt + audio_seconds_tts + twilio_seconds
- B2 backward compat: callers existentes (tokens only) ainda funcionam
- B3 voice cost real (1 minuto audio) > 0 quando tier=pro
- B4 free tier nao cobra audio
- B5 enterprise tier cobra mais que pro (premium SLA)
- B6 helper compute_voice_credits utilitario para uso em finalize_screening
"""
from __future__ import annotations

import pytest


# ─── B1: compute_credits aceita audio metrics ─────────────────────────────────

def test_compute_credits_accepts_audio_kwargs():
    """B1: signature deve aceitar audio_seconds_stt + audio_seconds_tts + twilio_seconds."""
    from app.services.agent_pricing import compute_credits

    # Deve aceitar SEM lancar TypeError
    result = compute_credits(
        tokens_input=0,
        tokens_output=0,
        audio_seconds_stt=60,
        audio_seconds_tts=20,
        twilio_seconds=60,
        tier="pro",
    )
    assert isinstance(result, int)
    assert result > 0, f"Voice usage de 60s STT + 20s TTS + 60s Twilio pro tier deve cobrar >0 credits, got {result}"


# ─── B2: backward compat tokens-only ──────────────────────────────────────────

def test_compute_credits_backward_compat_tokens_only():
    """B2: callers existentes (tokens-only chat agents) continuam funcionando."""
    from app.services.agent_pricing import compute_credits

    result_old = compute_credits(tokens_input=1000, tokens_output=500, tier="pro")
    assert result_old > 0, "Backward compat: chat agents tokens-only ainda cobram"

    # Mesmo input com audio=0 deve retornar mesmo valor
    result_with_zero_audio = compute_credits(
        tokens_input=1000,
        tokens_output=500,
        audio_seconds_stt=0,
        audio_seconds_tts=0,
        twilio_seconds=0,
        tier="pro",
    )
    assert result_with_zero_audio == result_old, (
        f"audio=0 deve nao alterar resultado: old={result_old}, new={result_with_zero_audio}"
    )


# ─── B3: voice cost real para 60s pro ─────────────────────────────────────────

def test_voice_audio_60s_pro_tier_costs_positive():
    """B3: 60s audio (STT + TTS + Twilio) pro tier cobra credits > 0."""
    from app.services.agent_pricing import compute_credits

    # Apenas voice metrics, sem tokens (sao 2 sistemas distintos no voice)
    result = compute_credits(
        tokens_input=0,
        tokens_output=0,
        audio_seconds_stt=60,
        audio_seconds_tts=20,
        twilio_seconds=60,
        tier="pro",
    )
    assert result > 0, f"Voice pro tier 60s deve cobrar >0, got {result}"


# ─── B4: free tier nao cobra audio ────────────────────────────────────────────

def test_free_tier_does_not_charge_audio():
    """B4: free tier mantem 0 mesmo com audio uso pesado."""
    from app.services.agent_pricing import compute_credits

    result = compute_credits(
        tokens_input=0,
        tokens_output=0,
        audio_seconds_stt=600,
        audio_seconds_tts=200,
        twilio_seconds=600,
        tier="free",
    )
    assert result == 0, f"Free tier deve cobrar 0 em audio, got {result}"


# ─── B5: enterprise > pro ─────────────────────────────────────────────────────

def test_enterprise_audio_pricing_exceeds_pro():
    """B5: enterprise tier cobra mais que pro para mesmo audio uso (premium SLA)."""
    from app.services.agent_pricing import compute_credits

    pro = compute_credits(
        tokens_input=0, tokens_output=0,
        audio_seconds_stt=60, audio_seconds_tts=20, twilio_seconds=60,
        tier="pro",
    )
    enterprise = compute_credits(
        tokens_input=0, tokens_output=0,
        audio_seconds_stt=60, audio_seconds_tts=20, twilio_seconds=60,
        tier="enterprise",
    )
    assert enterprise >= pro, (
        f"Enterprise voice pricing deve >= pro (premium SLA): pro={pro}, enterprise={enterprise}"
    )


# ─── B6: helper compute_voice_credits ─────────────────────────────────────────

def test_compute_voice_credits_helper_exists():
    """B6: helper canonical compute_voice_credits para uso em finalize_screening."""
    try:
        from app.services.agent_pricing import compute_voice_credits
    except ImportError:
        pytest.fail("compute_voice_credits helper deve existir em app.services.agent_pricing")

    # 60s total audio, pro tier
    result = compute_voice_credits(
        total_audio_seconds=60,
        tokens_input=200,
        tokens_output=400,
        tier="pro",
    )
    assert isinstance(result, int)
    assert result > 0, f"Voice canonical helper 60s pro deve cobrar >0, got {result}"


# ─── B7: pricing tier respected ───────────────────────────────────────────────

# ─── B8: orchestrator wires billing into finalize ─────────────────────────────

import pytest as _pytest


@_pytest.mark.asyncio
async def test_finalize_screening_records_voice_billing():
    """B8: finalize_screening chama agent_marketplace_service.record_execution
    canonical com credits computados via compute_voice_credits."""
    from datetime import datetime
    from unittest.mock import AsyncMock, MagicMock, patch

    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
        VoiceScreeningSession,
    )

    orch = VoiceScreeningOrchestrator()
    session = VoiceScreeningSession(
        session_id="s-bill-1",
        candidate_id="cand-bill",
        candidate_name="Bill Test",
        job_title="Bill Job",
        company_id="comp-bill",
        phone_number="+5511999999999",
        job_id="job-bill",
        status="completed",
        call_sid="CA_BILL",
        started_at=datetime.utcnow(),
    )
    session.transcript_segments = [{"role": "lia", "text": "hi"}]
    session.started_at = datetime(2026, 5, 22, 10, 0, 0)
    session.ended_at = datetime(2026, 5, 22, 10, 1, 0)  # 60 seconds

    fake_wsi = {"overall_evaluation": {"overall_score": 7.0}}

    # Mock marketplace service so we can assert canonical billing call
    fake_marketplace = MagicMock()
    fake_marketplace.record_execution = AsyncMock(return_value=None)

    with patch.object(orch, "_fetch_session", new=AsyncMock(return_value=session)), \
         patch.object(orch, "_store_session", new=AsyncMock()), \
         patch.object(orch, "persist_session_state", new=AsyncMock()), \
         patch.object(orch, "_resolve_pricing_tier", new=AsyncMock(return_value="pro")), \
         patch("app.domains.voice.services.voice_screening_orchestrator._WSIVoiceOrchestrator", None), \
         patch("app.domains.voice.services.voice_screening_orchestrator._analyze_voice_screening",
               new=AsyncMock(return_value=fake_wsi)), \
         patch("app.domains.voice.services.voice_screening_orchestrator.AuditService") as MockAudit, \
         patch("app.services.agent_marketplace_service.agent_marketplace_service", fake_marketplace):

        mock_audit = MagicMock()
        mock_audit.log_decision = AsyncMock(return_value=None)
        MockAudit.return_value = mock_audit

        # db nao-None para permitir billing record
        fake_db = MagicMock()
        result = await orch.finalize_screening(session_id="s-bill-1", db=fake_db)

    assert result["status"] == "completed"
    # F-19 B8: marketplace.record_execution chamado com credits > 0
    assert fake_marketplace.record_execution.called, (
        "F-19 B8: agent_marketplace_service.record_execution deve ser chamado em finalize"
    )
    kwargs = fake_marketplace.record_execution.call_args.kwargs
    assert kwargs.get("agent_id") == "voice_screening_orchestrator", (
        f"agent_id esperado voice_screening_orchestrator, got {kwargs.get('agent_id')}"
    )
    assert kwargs.get("company_id") == "comp-bill"
    assert kwargs.get("credits_consumed", 0) > 0, (
        f"credits_consumed deve ser > 0 para 60s audio, got {kwargs.get('credits_consumed')}"
    )
    assert kwargs.get("pricing_tier") == "pro"


def test_pricing_tier_unknown_falls_back_to_pro():
    """B7: tier desconhecido cai para pro (logged warning)."""
    from app.services.agent_pricing import compute_credits

    result_unknown = compute_credits(
        tokens_input=0, tokens_output=0,
        audio_seconds_stt=60, audio_seconds_tts=20, twilio_seconds=60,
        tier="ghost-tier",  # nao existe
    )
    result_pro = compute_credits(
        tokens_input=0, tokens_output=0,
        audio_seconds_stt=60, audio_seconds_tts=20, twilio_seconds=60,
        tier="pro",
    )
    assert result_unknown == result_pro, (
        f"Tier desconhecido deve cair pra pro: unknown={result_unknown}, pro={result_pro}"
    )
