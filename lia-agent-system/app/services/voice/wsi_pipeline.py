"""
Shared WSI pipeline for OpenMic voice screening results.

Centralises the four-step pipeline used by both the Celery task
(`voice.openmic.wsi_pipeline`) and the inline fallback in the webhook handler,
preventing logic divergence over time.

Steps:
  1. (Optional) Deepgram re-transcription when transcript is too short.
  2. WSI deterministic scoring.
  3. Persist result to `voice_wsi_results` table (upsert on call_id).
  4. Recruiter Bell notification.

Usage:
    from app.services.voice.wsi_pipeline import run_voice_wsi_pipeline

    result = await run_voice_wsi_pipeline(task_data)
"""

import logging
from typing import Any

from app.shared.pii_masking import mask_pii

logger = logging.getLogger(__name__)

_MIN_TRANSCRIPT_CHARS = 50


async def _fetch_audio_safe(audio_url: str) -> bytes | None:
    """
    Download audio from a pre-validated HTTPS URL.

    audio_url MUST already be validated via _validate_audio_url() before
    calling this function. Returns None on any network/HTTP error.
    """
    if not audio_url:
        return None
    try:
        import httpx
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(audio_url)
        if response.status_code == 200:
            return response.content
        logger.warning("[WSI Pipeline] Audio fetch returned HTTP %d", response.status_code)
        return None
    except Exception as exc:
        logger.warning("[WSI Pipeline] Audio fetch failed (non-blocking): %s", exc)
        return None


async def _try_deepgram_retranscribe(transcript: str, audio_url: str, call_id: str) -> str:
    """
    Attempt Deepgram re-transcription when the existing transcript is too short.

    Returns the improved transcript, or the original transcript unchanged on
    any error (non-blocking).
    """
    if len(transcript.strip()) >= _MIN_TRANSCRIPT_CHARS or not audio_url:
        return transcript

    logger.info(
        "[WSI Pipeline] Transcript too short (%d chars) — attempting Deepgram re-transcription call_id=%s",
        len(transcript.strip()),
        call_id,
    )
    try:
        from app.services.voice.deepgram_service import deepgram_service
        audio_bytes = await _fetch_audio_safe(audio_url)
        if audio_bytes:
            result = await deepgram_service.transcribe(
                audio_data=audio_bytes,
                mime_type="audio/mp3",
                language="pt-BR",
            )
            if result.get("transcript"):
                improved = result["transcript"]
                logger.info(
                    "[WSI Pipeline] Deepgram re-transcription complete — chars=%d confidence=%.2f call_id=%s",
                    len(improved),
                    result.get("confidence", 0.0),
                    call_id,
                )
                return improved
    except Exception as exc:
        logger.warning("[WSI Pipeline] Deepgram re-transcription failed (non-blocking): %s", exc)

    return transcript


def _score_wsi(transcript: str, call_id: str) -> dict[str, Any]:
    """
    Run WSI deterministic scoring on a voice transcript.

    Returns a result dict with final_score, classification, bloom_level,
    context_score, and source. On error, returns a zero-score fallback.
    """
    try:
        from app.domains.cv_screening.services.wsi_deterministic_scorer import (
            calculate_wsi_deterministic,
            classify_wsi_score,
        )
        raw = calculate_wsi_deterministic(
            response_text=transcript,
            competency_name="voice_screening",
            question_framework="CBI",
            question_type="behavioral",
            bloom_expected=3,
        )
        final_score = raw.final_score
        classification = classify_wsi_score(final_score)
        return {
            "final_score": final_score,
            "classification": classification,
            "bloom_level": raw.bloom_level,
            "context_score": raw.context_score,
            "source": "openmic_voice",
        }
    except Exception as exc:
        logger.error("[WSI Pipeline] WSI scoring failed — call_id=%s error=%s", call_id, exc)
        return {"final_score": 0.0, "classification": "regular", "bloom_level": 0, "context_score": 0.0, "source": "openmic_voice"}


async def _persist_wsi_result(
    wsi_result: dict[str, Any],
    candidate_id: str,
    job_id: str,
    company_id: str,
    call_id: str,
    transcript_length: int,
) -> None:
    """
    Upsert WSI result into the `voice_wsi_results` table.

    ON CONFLICT (call_id) updates score and classification.
    Non-blocking: logs error and continues on DB failure.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO voice_wsi_results
                        (candidate_id, job_id, company_id, call_id, source,
                         final_score, classification, bloom_level, context_score,
                         transcript_length, created_at)
                    VALUES
                        (:candidate_id, :job_id, :company_id, :call_id, :source,
                         :final_score, :classification, :bloom_level, :context_score,
                         :transcript_length, NOW())
                    ON CONFLICT (call_id) DO UPDATE SET
                        final_score = EXCLUDED.final_score,
                        classification = EXCLUDED.classification,
                        updated_at = NOW()
                """),
                {
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "company_id": company_id,
                    "call_id": call_id,
                    "source": "openmic_voice",
                    "final_score": wsi_result.get("final_score", 0.0),
                    "classification": wsi_result.get("classification", "regular"),
                    "bloom_level": wsi_result.get("bloom_level", 0),
                    "context_score": wsi_result.get("context_score", 0.0),
                    "transcript_length": transcript_length,
                },
            )
            await db.commit()
            logger.info(
                "[WSI Pipeline] WSI result persisted — call_id=%s candidate_id=%s",
                call_id,
                mask_pii(candidate_id),
            )
    except Exception as exc:
        logger.error("[WSI Pipeline] DB persistence failed (non-blocking) — call_id=%s error=%s", call_id, exc)


async def _notify_recruiter(
    wsi_result: dict[str, Any],
    candidate_id: str,
    job_id: str,
    company_id: str,
    call_id: str,
) -> None:
    """
    Send Bell notification to recruiter with WSI result summary.

    Non-blocking: logs warning and continues on notification failure.
    """
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.notification_service import notification_service
        score = wsi_result.get("final_score", 0.0)
        classification = wsi_result.get("classification", "unknown")
        async with AsyncSessionLocal() as db:
            await notification_service.send_system_alert(
                db=db,
                title=f"Triagem de voz concluída — Score WSI: {score:.1f}/5.0",
                message=(
                    f"A triagem automatizada por voz foi concluída para o candidato. "
                    f"Score WSI: {score:.1f}/5.0 ({classification}). "
                    f"Acesse o pipeline para ver os detalhes completos."
                ),
                severity="info",
                channels=["bell"],
                metadata={
                    "candidate_id": candidate_id,
                    "job_id": job_id,
                    "company_id": company_id,
                    "call_id": call_id,
                    "wsi_score": score,
                    "wsi_classification": classification,
                    "source": "openmic_voice",
                },
            )
    except Exception as exc:
        logger.warning("[WSI Pipeline] Recruiter notification failed (non-blocking): %s", exc)


async def run_voice_wsi_pipeline(task_data: dict[str, Any]) -> dict[str, Any]:
    """
    Execute the full OpenMic voice WSI pipeline.

    Args:
        task_data: Dict containing:
            - call_id: OpenMic call identifier
            - candidate_id: LIA candidate ID
            - job_id: Job vacancy ID
            - company_id: Company ID
            - transcript: Raw transcript text (may be empty)
            - audio_url: Pre-validated HTTPS audio URL (SSRF-safe)
            - duration_seconds: Call duration

    Returns:
        Dict with wsi_score, classification, candidate_id, job_id, status.
    """
    candidate_id = task_data.get("candidate_id", "unknown")
    job_id = task_data.get("job_id", "unknown")
    company_id = task_data.get("company_id", "unknown")
    call_id = task_data.get("call_id", "unknown")
    transcript = task_data.get("transcript", "")
    audio_url = task_data.get("audio_url", "")

    logger.info(
        "[WSI Pipeline] Starting pipeline — call_id=%s candidate_id=%s job_id=%s",
        call_id,
        mask_pii(candidate_id),
        job_id,
    )

    # Step 1: Deepgram re-transcription if needed
    transcript = await _try_deepgram_retranscribe(transcript, audio_url, call_id)

    # Step 2: WSI scoring
    wsi_result = _score_wsi(transcript, call_id)
    logger.info(
        "[WSI Pipeline] Scoring complete — candidate_id=%s score=%.2f classification=%s",
        mask_pii(candidate_id),
        wsi_result["final_score"],
        wsi_result["classification"],
    )

    # Step 3: Persist to DB (non-blocking)
    try:
        await _persist_wsi_result(
            wsi_result=wsi_result,
            candidate_id=candidate_id,
            job_id=job_id,
            company_id=company_id,
            call_id=call_id,
            transcript_length=len(transcript),
        )
    except Exception as exc:
        logger.error("[WSI Pipeline] DB persistence failed (non-blocking) — call_id=%s: %s", call_id, exc)

    # Step 4: Notify recruiter (non-blocking)
    try:
        await _notify_recruiter(wsi_result, candidate_id, job_id, company_id, call_id)
    except Exception as exc:
        logger.warning("[WSI Pipeline] Recruiter notification failed (non-blocking): %s", exc)

    return {
        "status": "completed",
        "call_id": call_id,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "wsi_score": wsi_result["final_score"],
        "classification": wsi_result["classification"],
    }
