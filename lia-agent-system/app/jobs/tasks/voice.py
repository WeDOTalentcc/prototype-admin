"""Celery tasks: voice (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="voice.openmic.wsi_pipeline", bind=True, max_retries=3, queue="evaluation_normal")
def run_openmic_wsi_pipeline_task(self, task_data: dict) -> dict:
    """
    Process OpenMic voice screening result through the WSI scoring pipeline.

    Triggered by the OpenMic webhook after a call completes. Delegates to
    `app.services.voice.wsi_pipeline.run_voice_wsi_pipeline` which handles:
    1. (Optional) Deepgram re-transcription if transcript is missing/short.
    2. WSI deterministic scoring from transcript.
    3. Persist result to `voice_wsi_results` table.
    4. Notify recruiter via Bell notification.

    Args:
        task_data: Dict with call_id, candidate_id, job_id, company_id,
                   transcript, audio_url, duration_seconds, source.

    Returns:
        Dict with wsi_score, classification, candidate_id, job_id, status.
    """
    from app.services.voice.wsi_pipeline import run_voice_wsi_pipeline

    span = _celery_span("celery.task_start", "voice.openmic.wsi_pipeline")
    span.set_attribute("call_id", task_data.get("call_id", "unknown"))
    span.set_attribute("candidate_id", task_data.get("candidate_id", "unknown"))

    try:
        result = asyncio.run(run_voice_wsi_pipeline(task_data))
        _finish_celery_success(span, "voice.openmic.wsi_pipeline")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "voice.openmic.wsi_pipeline", exc)
        logger.error(
            "voice.openmic.wsi_pipeline falhou call_id=%s candidate_id=%s: %s",
            task_data.get("call_id", "unknown"),
            task_data.get("candidate_id", "unknown"),
            exc,
        )
        _emit_celery_retry("voice.openmic.wsi_pipeline", exc, self.request.retries, self.max_retries, 60)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("voice.openmic.wsi_pipeline", exc)
        raise self.retry(exc=exc, countdown=60)

