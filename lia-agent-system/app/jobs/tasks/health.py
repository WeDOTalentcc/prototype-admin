"""Celery tasks: DLQ health check (R-024)."""

from app.jobs.tenant_aware_task import TenantAwareTask
from app.jobs.tasks._utils import (
    celery_app, logger,
    _celery_span, _finish_celery_success, _finish_celery_failure,
)

# Thresholds for DLQ health alerts
_DLQ_ALERT_TOTAL = 100      # alert if total DLQ entries exceed this
_DLQ_ALERT_PER_QUEUE = 30   # alert if any single queue exceeds this


@celery_app.task(base=TenantAwareTask, name="health.check_dlq_health", bind=True, max_retries=1)
def check_dlq_health_task(self) -> dict:
    """
    Inspect DLQ summary and emit alerts if thresholds exceeded.

    R-024: Run hourly via Celery beat schedule (dlq-health-check-hourly).
    Results logged at INFO; threshold breaches at WARNING + Sentry.
    """
    import asyncio

    span = _celery_span("celery.task_start", "health.check_dlq_health")

    try:
        from app.shared.resilience.dlq_service import DLQService
        dlq = DLQService()

        async def _get_summary():
            return await dlq.summary()

        summary = asyncio.run(_get_summary())
        total = summary.get("total_entries", 0)
        queues = summary.get("queues", {})

        logger.info("[DLQ-Health] total=%d queues=%s", total, queues)

        alerts = []
        if total > _DLQ_ALERT_TOTAL:
            alerts.append(
                "total_entries={} exceeds threshold={}".format(total, _DLQ_ALERT_TOTAL)
            )
        for queue_name, count in queues.items():
            if count > _DLQ_ALERT_PER_QUEUE:
                alerts.append(
                    "queue={} count={} exceeds threshold={}".format(queue_name, count, _DLQ_ALERT_PER_QUEUE)
                )

        if alerts:
            logger.warning("[DLQ-Health] ALERT: %s", " | ".join(alerts))
            try:
                import sentry_sdk
                sentry_sdk.capture_message(
                    "DLQ health alert: {}".format("; ".join(alerts)),
                    level="warning",
                    tags={
                        "alert_type": "dlq_backlog",
                        "total_entries": str(total),
                    },
                )
            except Exception:
                pass  # Sentry unavailable -- log is sufficient

        result = {
            "total_entries": total,
            "queues": queues,
            "alerts": alerts,
            "status": "healthy" if not alerts else "degraded",
        }

        _finish_celery_success(span, "health.check_dlq_health")
        from app.shared.resilience.cron_health import record_cron_run
        record_cron_run("health.check_dlq_health")
        return result

    except Exception as exc:
        _finish_celery_failure(span, "health.check_dlq_health", exc)
        logger.error("[DLQ-Health] Failed to read DLQ summary: %s", exc, exc_info=True)
        return {"error": str(exc), "status": "error"}
