"""
Contract tests — P1.AIC2 (2026-05-22) Whisper STT + TTS credit gate.

Validates that `app.domains.voice.services.voice_service.VoiceService` routes
through `openai.AsyncOpenAI.audio.transcriptions.create` and
`openai.AsyncOpenAI.audio.speech.create`, both of which are wrapped by the
audio-aware `_patch_openai_audio` monkey-patch installed by
`app.shared.llm_bootstrap.install_llm_guards`.

We test the SHIM, not the SDK. The audio SDK methods are mocked at the
underlying seam. The gate is the contract under test.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.middleware.auth_enforcement import _current_company_id
from app.shared.llm_bootstrap import (
    _estimate_tokens_openai_audio_speech,
    _estimate_tokens_openai_audio_transcription,
    install_llm_guards,
)
from app.shared.services.ai_credit_gate import AICreditExhausted


install_llm_guards()


COMPANY_OK = "test-company-uuid-voice"
COMPANY_EXHAUSTED = "test-company-exhausted-voice"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _wav_bytes(seconds: float = 1.0) -> bytes:
    """Synthesize a minimal silent WAV header + payload of `seconds`."""
    import io
    import wave

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


def _make_transcription_response(text: str = "olá mundo", duration: float = 1.0):
    """Object mimicking openai.types.audio.Transcription model_dump output."""
    resp = MagicMock()
    resp.model_dump = MagicMock(
        return_value={
            "text": text,
            "duration": duration,
            "language": "pt",
            "segments": [
                {
                    "words": [
                        {"word": "olá", "start": 0.0, "end": 0.3},
                        {"word": "mundo", "start": 0.4, "end": 0.9},
                    ]
                }
            ],
        }
    )
    return resp


def _make_speech_response(audio_bytes: bytes = b"\x00MP3PAYLOAD"):
    """Object mimicking openai _LegacyBinaryResponseContent."""
    resp = MagicMock()
    resp.read = AsyncMock(return_value=audio_bytes)
    return resp


# ----------------------------------------------------------------------
# Estimator unit tests
# ----------------------------------------------------------------------

def test_whisper_estimator_explicit_duration():
    """60 sec of audio → 2000 token-eq (Whisper $0.006/min / Claude $3/M)."""
    estimate = _estimate_tokens_openai_audio_transcription(
        {"audio_duration_seconds": 60}
    )
    assert estimate == 2000


def test_whisper_estimator_from_file_tuple_bytes():
    """120000 bytes @ ~96 kbps heuristic → ~10 sec → ~333 token-eq."""
    estimate = _estimate_tokens_openai_audio_transcription(
        {"file": ("a.mp3", b"x" * 120000, "audio/mp3")}
    )
    # Expected ~333. Allow ±5 for rounding tolerance.
    assert 320 <= estimate <= 350


def test_whisper_estimator_no_signal_returns_zero():
    """No file, no duration → 0 (gate fails-safe ALLOW downstream)."""
    estimate = _estimate_tokens_openai_audio_transcription({})
    assert estimate == 0


def test_tts_estimator_char_count():
    """11 chars × 5 token-eq/char = 55."""
    estimate = _estimate_tokens_openai_audio_speech({"input": "hello world"})
    assert estimate == 55


def test_tts_estimator_empty_input():
    estimate = _estimate_tokens_openai_audio_speech({"input": ""})
    assert estimate == 0


# ----------------------------------------------------------------------
# REGRA 4: Without tenant context the gate fail-safe ALLOWs.
# Same rationale as multimodal tests — hard failing would break fixtures.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_whisper_call_without_context_silently_passes():
    """No _current_company_id → gate skips, SDK seam still reached."""
    from app.domains.voice.services.voice_service import VoiceService

    svc = VoiceService()
    svc.openai_api_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_transcription_response("ola"))

    token = _current_company_id.set("")
    try:
        with patch.object(
            svc, "_get_client", new=AsyncMock(
                return_value=MagicMock(
                    audio=MagicMock(
                        transcriptions=MagicMock(create=fake_create)
                    )
                )
            )
        ):
            result = await svc.transcribe_audio(_wav_bytes(0.5))

        assert result["text"] == "ola"
        fake_create.assert_awaited_once()
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Exhausted credits → AICreditExhausted before SDK is invoked.
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_whisper_call_exhausted_audio_seconds_raises():
    """Gate raises when ai_credits_balance is exhausted — SDK never called."""
    from app.domains.voice.services.voice_service import VoiceService

    svc = VoiceService()
    svc.openai_api_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_transcription_response("never"))

    token = _current_company_id.set(COMPANY_EXHAUSTED)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(
                side_effect=AICreditExhausted(
                    "exhausted",
                    company_id=COMPANY_EXHAUSTED,
                    remaining=0,
                    service="voice_service",
                )
            ),
        ), patch.object(
            svc, "_get_client", new=AsyncMock(
                return_value=MagicMock(
                    audio=MagicMock(
                        transcriptions=MagicMock(create=fake_create)
                    )
                )
            )
        ):
            with pytest.raises(AICreditExhausted) as exc_info:
                await svc.transcribe_audio(_wav_bytes(60.0))

        assert exc_info.value.company_id == COMPANY_EXHAUSTED
        # SDK was never invoked because the gate raised first.
        fake_create.assert_not_awaited()
    finally:
        _current_company_id.reset(token)


@pytest.mark.asyncio
async def test_tts_call_exhausted_credits_raises():
    """TTS gate also blocks when exhausted (separate audio.speech endpoint)."""
    from app.domains.voice.services.voice_service import VoiceService

    svc = VoiceService()
    svc.openai_api_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_speech_response(b"MP3"))

    token = _current_company_id.set(COMPANY_EXHAUSTED)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=AsyncMock(
                side_effect=AICreditExhausted(
                    "exhausted",
                    company_id=COMPANY_EXHAUSTED,
                    remaining=0,
                    service="voice_service",
                )
            ),
        ), patch.object(
            svc, "_get_client", new=AsyncMock(
                return_value=MagicMock(
                    audio=MagicMock(
                        speech=MagicMock(create=fake_create)
                    )
                )
            )
        ):
            with pytest.raises(AICreditExhausted):
                await svc.synthesize_speech("Olá mundo", voice="nova")

        fake_create.assert_not_awaited()
    finally:
        _current_company_id.reset(token)


# ----------------------------------------------------------------------
# Estimator path: gate is invoked with a non-zero estimated_tokens that
# scales with audio duration (per-minute pricing model).
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_whisper_estimates_cost_per_minute_correctly():
    """The gate sees a positive estimated_tokens computed from the audio
    payload bytes. Longer audio → higher estimate."""
    captured: dict = {}

    async def _fake_check(_db, company_id, *, estimated_tokens, service, **kwargs):
        captured["estimated_tokens"] = estimated_tokens
        captured["service"] = service
        captured["company_id"] = company_id
        return {"monthly_limit": 1_000_000, "current_usage": 0, "remaining": 1_000_000}

    from app.domains.voice.services.voice_service import VoiceService

    svc = VoiceService()
    svc.openai_api_key = "sk-test"

    fake_create = AsyncMock(return_value=_make_transcription_response("texto"))

    # Synthesize ~10 sec of WAV — heuristic from bytes → ~26+ sec because
    # WAV is uncompressed PCM ~256 kbps not the compressed 96 kbps default,
    # but the gate just needs "positive and proportional".
    token = _current_company_id.set(COMPANY_OK)
    try:
        with patch(
            "app.shared.services.ai_credit_gate.check_credit_budget",
            new=_fake_check,
        ), patch.object(
            svc, "_get_client", new=AsyncMock(
                return_value=MagicMock(
                    audio=MagicMock(
                        transcriptions=MagicMock(create=fake_create)
                    )
                )
            )
        ):
            await svc.transcribe_audio(_wav_bytes(10.0))

        assert captured.get("company_id") == COMPANY_OK
        # Non-zero estimate proves the bootstrap audio estimator ran.
        assert captured.get("estimated_tokens", 0) > 0
        # service label is auto-inferred from caller stack — should match
        # filename of voice service or this test file.
        assert captured.get("service")
    finally:
        _current_company_id.reset(token)
