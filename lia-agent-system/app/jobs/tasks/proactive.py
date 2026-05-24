"""WT-2022 Camada IA Proativa: Celery beat task (scheduler-driven).

Cron 1x/hora (minuto 5 para nao colidir com followup-check-hourly em :00).
Itera todas companies ativas + roda ProactiveDetectorService.

Beat schedule recomendado (a registrar em libs/config/lia_config/celery_app.py):

    "proactive-detect-hints-hourly": {
        "task": "proactive.detect_hints_hourly",
        "schedule": crontab(minute=5),
        "options": {"expires": 3500, "queue": "onboarding_low"},
    },

Filas: onboarding_low (baixa prioridade, batch).

Telemetria:
- Span celery.task_start + celery.task_success / failure
- Log estruturado com totais (companies_checked, total_hints, errors[])
- Retry: max 3 tentativas com countdown=300 (5min)
"""
from __future__ import annotations

import asyncio

from app.jobs.tasks._utils import (
    _celery_span,
    _emit_celery_retry,
    _emit_dlq_push,
    _finish_celery_failure,
    _finish_celery_success,
    celery_app,
    logger,
)


@celery_app.task(
    name="proactive.detect_hints_hourly",
    bind=True,
    max_retries=3,
    queue="onboarding_low",
)
def proactive_detect_hints_hourly(self) -> dict:
    """Detecta proactive hints para todas companies ativas a cada hora.

    Returns:
        dict com {companies_checked, total_hints, errors[]}.
    """

    async def _run() -> dict:
        from sqlalchemy import select

        from app.core.database import AsyncSessionLocal
        from app.shared.services.proactive_detector_service import (
            proactive_detector_service,
        )
        from lia_models.company import Company

        summary: dict = {
            "companies_checked": 0,
            "total_hints": 0,
            "total_persisted": 0,
            "errors": [],
        }

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(Company).where(Company.is_active.is_(True))
                )
                companies = list(result.scalars().all())
            except Exception as exc:
                logger.error(
                    "[proactive.detect_hints_hourly] Failed to list companies: %s",
                    exc,
                )
                raise

            for company in companies:
                cid = str(company.id)
                try:
                    detector_summary = (
                        await proactive_detector_service.run_for_company(db, cid)
                    )
                    summary["companies_checked"] += 1
                    summary["total_hints"] += detector_summary.get("hints_count", 0)
                    summary["total_persisted"] += detector_summary.get(
                        "hints_persisted", 0
                    )
                except Exception as exc:
                    summary["errors"].append(
                        {"company_id": cid, "error": str(exc)[:200]}
                    )

            # Commit em batch no fim para reduzir contention.
            try:
                await db.commit()
            except Exception as exc:
                logger.error(
                    "[proactive.detect_hints_hourly] DB commit failed: %s", exc
                )
                await db.rollback()
                raise

        return summary

    span = _celery_span("celery.task_start", "proactive.detect_hints_hourly")

    try:
        result = asyncio.run(_run())
        logger.info("[proactive.detect_hints_hourly] %s", result)
        _finish_celery_success(span, "proactive.detect_hints_hourly")
        return result
    except Exception as exc:
        _finish_celery_failure(span, "proactive.detect_hints_hourly", exc)
        logger.error("proactive.detect_hints_hourly failed: %s", exc)
        _emit_celery_retry(
            "proactive.detect_hints_hourly",
            exc,
            self.request.retries,
            self.max_retries,
            300,
        )
        if self.request.retries >= self.max_retries:
            _emit_dlq_push("proactive.detect_hints_hourly", exc)
        raise self.retry(exc=exc, countdown=300)


__all__ = ["proactive_detect_hints_hourly"]
