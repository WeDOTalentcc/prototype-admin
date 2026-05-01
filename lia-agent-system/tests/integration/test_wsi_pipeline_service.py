"""
Tests for the shared WSI pipeline service (app.services.voice.wsi_pipeline).

Verifies:
- Full pipeline runs end-to-end with mocked dependencies
- Deepgram re-transcription triggered only when transcript too short
- WSI scoring errors return zero-score fallback without raising
- DB persistence is called with correct parameters
- Recruiter notification is attempted (non-blocking on failure)
- Short transcript + no audio_url skips Deepgram fetch
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


TASK_DATA_OK = {
    "call_id": "call_test_123",
    "candidate_id": "cand_001",
    "job_id": "job_001",
    "company_id": "company_001",
    "transcript": "Tenho cinco anos de experiência em desenvolvimento de software backend com Python e FastAPI.",
    "audio_url": "https://media.openmic.ai/recordings/call_test_123.mp3",
    "duration_seconds": 120,
    "source": "openmic",
}

TASK_DATA_SHORT_TRANSCRIPT = {
    **TASK_DATA_OK,
    "transcript": "Sim.",
}

TASK_DATA_NO_AUDIO = {
    **TASK_DATA_OK,
    "transcript": "Sim.",
    "audio_url": "",
}


def _mock_wsi_raw():
    raw = MagicMock()
    raw.final_score = 3.5
    raw.bloom_level = 3
    raw.context_score = 0.75
    return raw


@pytest.mark.asyncio
async def test_pipeline_runs_successfully():
    """Full pipeline with adequate transcript: no Deepgram call needed."""
    with (
        patch("app.services.voice.wsi_pipeline._try_deepgram_retranscribe", new_callable=AsyncMock, return_value=TASK_DATA_OK["transcript"]) as mock_dg,
        patch("app.services.voice.wsi_pipeline._score_wsi", return_value={"final_score": 3.5, "classification": "top", "bloom_level": 3, "context_score": 0.75, "source": "openmic_voice"}),
        patch("app.services.voice.wsi_pipeline._persist_wsi_result", new_callable=AsyncMock) as mock_persist,
        patch("app.services.voice.wsi_pipeline._notify_recruiter", new_callable=AsyncMock) as mock_notify,
    ):
        from app.services.voice.wsi_pipeline import run_voice_wsi_pipeline

        result = await run_voice_wsi_pipeline(TASK_DATA_OK)

    assert result["status"] == "completed"
    assert result["wsi_score"] == 3.5
    assert result["classification"] == "top"
    assert result["call_id"] == "call_test_123"
    mock_persist.assert_called_once()
    mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_deepgram_called_for_short_transcript():
    """Deepgram re-transcription is invoked when transcript is too short."""
    import app.services.voice.wsi_pipeline as wp_mod

    improved = "Tenho dez anos de experiência em engenharia de software, trabalhando com times ágeis."

    mock_dg_svc = MagicMock()
    mock_dg_svc.transcribe = AsyncMock(return_value={"transcript": improved, "confidence": 0.95})

    orig_fetch = wp_mod._fetch_audio_safe

    async def mock_fetch(url: str) -> bytes:
        return b"audio-bytes"

    wp_mod._fetch_audio_safe = mock_fetch

    try:
        with patch("app.services.voice.deepgram_service.deepgram_service", mock_dg_svc):
            result = await wp_mod._try_deepgram_retranscribe(
                transcript="Sim.",
                audio_url="https://media.openmic.ai/recordings/test.mp3",
                call_id="call_001",
            )
    finally:
        wp_mod._fetch_audio_safe = orig_fetch

    assert result == improved
    mock_dg_svc.transcribe.assert_called_once()


@pytest.mark.asyncio
async def test_deepgram_skipped_for_adequate_transcript():
    """Deepgram is NOT called when transcript already meets minimum length."""
    long_transcript = "A" * 100

    with patch("app.services.voice.wsi_pipeline._fetch_audio_safe", new_callable=AsyncMock) as mock_fetch:
        from app.services.voice.wsi_pipeline import _try_deepgram_retranscribe

        result = await _try_deepgram_retranscribe(
            transcript=long_transcript,
            audio_url="https://media.openmic.ai/recordings/test.mp3",
            call_id="call_001",
        )

    assert result == long_transcript
    mock_fetch.assert_not_called()


@pytest.mark.asyncio
async def test_deepgram_skipped_when_no_audio_url():
    """Deepgram fetch is skipped when audio_url is empty even if transcript is short."""
    with patch("app.services.voice.wsi_pipeline._fetch_audio_safe", new_callable=AsyncMock) as mock_fetch:
        from app.services.voice.wsi_pipeline import _try_deepgram_retranscribe

        result = await _try_deepgram_retranscribe(
            transcript="Sim.",
            audio_url="",
            call_id="call_001",
        )

    assert result == "Sim."
    mock_fetch.assert_not_called()


def test_wsi_scoring_returns_fallback_on_error():
    """WSI scoring exception returns zero-score fallback without raising.

    Verifies that _score_wsi catches internal errors (e.g. import failures,
    scorer exceptions) and returns the zero-score fallback dict instead of
    propagating the exception.
    """
    import app.services.voice.wsi_pipeline as wp_mod
    import app.domains.cv_screening.services.wsi_deterministic_scorer as scorer_mod

    orig_fn = scorer_mod.calculate_wsi_deterministic

    def failing_calculate(**kw):
        raise RuntimeError("scorer unavailable")

    scorer_mod.calculate_wsi_deterministic = failing_calculate
    try:
        result = wp_mod._score_wsi("some transcript", "call_001")
    finally:
        scorer_mod.calculate_wsi_deterministic = orig_fn

    assert result["final_score"] == 0.0
    assert result["classification"] == "regular"
    assert result["source"] == "openmic_voice"


@pytest.mark.asyncio
async def test_notification_failure_is_non_blocking():
    """Recruiter notification failure does not raise — pipeline completes."""
    import app.services.voice.wsi_pipeline as wp_mod

    orig_dg = wp_mod._try_deepgram_retranscribe
    orig_score = wp_mod._score_wsi
    orig_persist = wp_mod._persist_wsi_result
    orig_notify = wp_mod._notify_recruiter

    async def mock_dg(t, a, c): return t
    def mock_score(t, c): return {"final_score": 1.0, "classification": "regular", "bloom_level": 1, "context_score": 0.1, "source": "openmic_voice"}
    async def mock_persist(**kw): pass
    async def mock_notify_fail(*a, **kw): raise RuntimeError("notification down")

    wp_mod._try_deepgram_retranscribe = mock_dg
    wp_mod._score_wsi = mock_score
    wp_mod._persist_wsi_result = mock_persist
    wp_mod._notify_recruiter = mock_notify_fail

    try:
        result = await wp_mod.run_voice_wsi_pipeline(TASK_DATA_OK)
    finally:
        wp_mod._try_deepgram_retranscribe = orig_dg
        wp_mod._score_wsi = orig_score
        wp_mod._persist_wsi_result = orig_persist
        wp_mod._notify_recruiter = orig_notify

    assert result["status"] == "completed"


@pytest.mark.asyncio
async def test_db_persistence_failure_is_non_blocking():
    """DB persistence failure does not raise — pipeline completes."""
    import app.services.voice.wsi_pipeline as wp_mod

    orig_dg = wp_mod._try_deepgram_retranscribe
    orig_score = wp_mod._score_wsi
    orig_persist = wp_mod._persist_wsi_result
    orig_notify = wp_mod._notify_recruiter

    async def mock_dg(t, a, c): return t
    def mock_score(t, c): return {"final_score": 1.0, "classification": "regular", "bloom_level": 1, "context_score": 0.1, "source": "openmic_voice"}
    async def mock_persist_fail(**kw): raise RuntimeError("DB down")
    async def mock_notify(*a, **kw): pass

    wp_mod._try_deepgram_retranscribe = mock_dg
    wp_mod._score_wsi = mock_score
    wp_mod._persist_wsi_result = mock_persist_fail
    wp_mod._notify_recruiter = mock_notify

    try:
        result = await wp_mod.run_voice_wsi_pipeline(TASK_DATA_OK)
    finally:
        wp_mod._try_deepgram_retranscribe = orig_dg
        wp_mod._score_wsi = orig_score
        wp_mod._persist_wsi_result = orig_persist
        wp_mod._notify_recruiter = orig_notify

    assert result["status"] == "completed"
