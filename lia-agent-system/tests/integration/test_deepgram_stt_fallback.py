"""
Tests for Deepgram STT fallback in the voice screening orchestrator.

Validates:
- Gemini STT is attempted first; Deepgram is only called on Gemini failure
- Deepgram returns transcript when Gemini is unavailable
- Both providers failing returns None without raising
- DeepgramUnconfiguredError is handled gracefully (no crash)
- Transcript segment is appended to session on success
"""

import struct
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mulaw_bytes(n: int = 200) -> bytes:
    """Create enough μ-law bytes to pass the len >= 160 guard."""
    return b"\x7f" * n


def _make_wav_header(num_samples: int = 200, sample_rate: int = 8000) -> bytes:
    """Minimal 44-byte RIFF/WAV header + PCM data."""
    data_size = num_samples * 2
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        1,
        sample_rate,
        sample_rate * 2,
        2,
        16,
        b"data",
        data_size,
    )
    return header + (b"\x00" * data_size)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def orchestrator():
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningOrchestrator,
    )

    orch = VoiceScreeningOrchestrator()
    return orch


@pytest.fixture()
def session_id(orchestrator):
    sid = "test-session-001"
    from app.domains.voice.services.voice_screening_orchestrator import (
        VoiceScreeningSession,
    )

    session = VoiceScreeningSession(
        session_id=sid,
        candidate_id="cand-001",
        candidate_name="Test Candidate",
        job_title="Desenvolvedor Backend",
        company_id="company-001",
        phone_number="+5511999999999",
    )
    orchestrator._sessions[sid] = session
    return sid


# ---------------------------------------------------------------------------
# STT fallback tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gemini_primary_used_when_available(orchestrator, session_id):
    """Gemini is attempted first when the service is available."""
    mock_gemini_svc = MagicMock()
    mock_gemini_svc.transcribe_audio = AsyncMock(
        return_value={"text": "Gemini transcript"}
    )
    mock_get_svc = MagicMock(return_value=mock_gemini_svc)

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            mock_get_svc,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            None,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    assert result == "Gemini transcript"
    mock_gemini_svc.transcribe_audio.assert_called_once()


@pytest.mark.asyncio
async def test_deepgram_fallback_on_gemini_failure(orchestrator, session_id):
    """Deepgram is used when Gemini raises an exception."""
    mock_gemini_svc = MagicMock()
    mock_gemini_svc.transcribe_audio = AsyncMock(
        side_effect=RuntimeError("Gemini unavailable")
    )
    mock_get_svc = MagicMock(return_value=mock_gemini_svc)

    mock_dg = MagicMock()
    mock_dg.is_configured = MagicMock(return_value=True)
    mock_dg.transcribe = AsyncMock(
        return_value={"transcript": "Deepgram fallback text"}
    )

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            mock_get_svc,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            mock_dg,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    assert result == "Deepgram fallback text"
    mock_dg.transcribe.assert_called_once()


@pytest.mark.asyncio
async def test_deepgram_used_when_gemini_absent(orchestrator, session_id):
    """Deepgram is used directly when _get_voice_service is None."""
    mock_dg = MagicMock()
    mock_dg.is_configured = MagicMock(return_value=True)
    mock_dg.transcribe = AsyncMock(
        return_value={"transcript": "Only Deepgram available"}
    )

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            None,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            mock_dg,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    assert result == "Only Deepgram available"


@pytest.mark.asyncio
async def test_returns_none_when_both_providers_fail(orchestrator, session_id):
    """Returns None without raising when both Gemini and Deepgram fail."""
    mock_gemini_svc = MagicMock()
    mock_gemini_svc.transcribe_audio = AsyncMock(side_effect=RuntimeError("Gemini down"))
    mock_get_svc = MagicMock(return_value=mock_gemini_svc)

    mock_dg = MagicMock()
    mock_dg.is_configured = MagicMock(return_value=True)
    mock_dg.transcribe = AsyncMock(side_effect=RuntimeError("Deepgram down"))

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            mock_get_svc,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            mock_dg,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    assert result is None


@pytest.mark.asyncio
async def test_deepgram_unconfigured_error_handled_gracefully(orchestrator, session_id):
    """DeepgramUnconfiguredError is silently caught — returns None without crash."""
    from app.services.voice.deepgram_service import DeepgramUnconfiguredError

    mock_dg = MagicMock()
    mock_dg.is_configured = MagicMock(return_value=True)
    mock_dg.transcribe = AsyncMock(side_effect=DeepgramUnconfiguredError("no key"))

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            None,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            mock_dg,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._DeepgramUnconfiguredError",
            DeepgramUnconfiguredError,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    assert result is None


@pytest.mark.asyncio
async def test_transcript_segment_appended_on_success(orchestrator, session_id):
    """Successful transcription appends a segment to session.transcript_segments."""
    mock_gemini_svc = MagicMock()
    mock_gemini_svc.transcribe_audio = AsyncMock(
        return_value={"text": "Hello world"}
    )
    mock_get_svc = MagicMock(return_value=mock_gemini_svc)

    with (
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._get_voice_service",
            mock_get_svc,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator._deepgram_service",
            None,
        ),
        patch(
            "app.domains.voice.services.voice_screening_orchestrator.mulaw_to_wav",
            return_value=_make_wav_header(),
        ),
    ):
        result = await orchestrator.process_audio_chunk(session_id, _make_mulaw_bytes())

    session = orchestrator._sessions[session_id]
    assert len(session.transcript_segments) == 1
    assert session.transcript_segments[0]["text"] == "Hello world"
    assert session.transcript_segments[0]["role"] == "candidate"


@pytest.mark.asyncio
async def test_short_audio_returns_none_immediately(orchestrator, session_id):
    """Audio shorter than 160 bytes is rejected before any STT call."""
    result = await orchestrator.process_audio_chunk(session_id, b"\x00" * 10)
    assert result is None
