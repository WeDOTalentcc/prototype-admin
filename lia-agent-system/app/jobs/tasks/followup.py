"""Celery tasks: followup (Fase 7)."""
import asyncio
import re
from datetime import UTC

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
    _emit_celery_retry, _emit_dlq_push,
)

@celery_app.task(base=TenantAwareTask, name="followup.process_pending", bind=True, max_retries=2)
def followup_process_pending_task(self) -> dict:
    """
    Reenvia convites WSI não abertos.

    Agendado a cada hora via Celery Beat (beat_schedule: followup-check-hourly).
    Após 7 reenvios sem resposta: marca candidato como 'sem_resposta' e notifica recruiter.

    Returns:
        Dict com { sent, skipped, errors, marked_no_response }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.jobs.followup_service import process_email_followups

        async with AsyncSessionLocal() as db:
            return await process_email_followups(db)

    span = _celery_span("celery.task_start", "followup.process_pending")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "followup.process_pending")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "followup.process_pending", exc)
        logger.error("followup.process_pending falhou: %s", exc)
        _emit_celery_retry("followup.process_pending", exc, self.request.retries, self.max_retries, 120)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("followup.process_pending", exc)
        raise self.retry(exc=exc, countdown=120)

@celery_app.task(base=TenantAwareTask, name="wsi.check_abandoned", bind=True, max_retries=2)
def wsi_check_abandoned_task(self) -> dict:
    """
    Detecta sessões WSI abandonadas e envia lembretes.

    Agendado a cada 4h via Celery Beat (beat_schedule: wsi-abandoned-check).
    1º lembrete (48h): email ao candidato.
    2º lembrete (96h): email ao candidato + Bell+Teams ao recruiter.

    Returns:
        Dict com { first_reminders, second_reminders, errors }
    """
    async def _run() -> dict:
        from app.core.database import AsyncSessionLocal
        from app.jobs.wsi_abandoned_service import check_abandoned_sessions

        async with AsyncSessionLocal() as db:
            return await check_abandoned_sessions(db)

    span = _celery_span("celery.task_start", "wsi.check_abandoned")

    try:
        result = asyncio.run(_run())
        _finish_celery_success(span, "wsi.check_abandoned")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "wsi.check_abandoned", exc)
        logger.error("wsi.check_abandoned falhou: %s", exc)
        _emit_celery_retry("wsi.check_abandoned", exc, self.request.retries, self.max_retries, 300)

        if self.request.retries >= self.max_retries:

            _emit_dlq_push("wsi.check_abandoned", exc)
        raise self.retry(exc=exc, countdown=300)

