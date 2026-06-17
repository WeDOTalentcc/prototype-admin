"""
R-036 — Cron sentinel: every task writes last-run timestamp to Redis.
Endpoint /health/crons verifies all registered crons ran within their expected cadence.
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Expected max interval in seconds (with 2x safety margin).
# If a cron is overdue by this much, it is considered failed.
CRON_EXPECTED_MAX_SECONDS: dict[str, int] = {
    # hourly cron: alert if >2h
    "health.check_dlq_health": 2 * 3600,
    # daily crons: alert if >26h
    "lgpd.run_cleanup_daily": 26 * 3600,
    "audit.apply_lifecycle_policy": 26 * 3600,
    "data.retention.run": 26 * 3600,
    "rls.health_check": 26 * 3600,
    "ragas.evaluate_daily": 26 * 3600,
    # weekly: alert if >8 days
    "platform.saas_metrics_weekly": 8 * 24 * 3600,
}

_SENTINEL_KEY_PREFIX = "cron:last_run:"
_SENTINEL_TTL_SECONDS = 90 * 24 * 3600  # 90 days — outlives any cadence


def _get_sync_redis():
    """Return a synchronous redis.Redis client using REDIS_URL from settings.

    Uses the same sync redis pattern as wsi_async_session_service and
    jd_template_cache_service — both call redis.from_url(settings.REDIS_URL, socket_connect_timeout=5, socket_timeout=5).
    """
    import redis as redis_lib
    from lia_config.config import settings
    return redis_lib.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=5, socket_timeout=5)


def record_cron_run(task_name: str, redis_client=None) -> None:
    """Called by each cron task to record its last successful run.

    Args:
        task_name: must match a key in CRON_EXPECTED_MAX_SECONDS.
        redis_client: optional pre-built Redis client (for testing).
    """
    try:
        rc = redis_client if redis_client is not None else _get_sync_redis()
        key = f"{_SENTINEL_KEY_PREFIX}{task_name}"
        rc.setex(key, _SENTINEL_TTL_SECONDS, str(int(time.time())))
        logger.debug("[CronHealth] Recorded sentinel for %s", task_name)
    except Exception as exc:
        # Non-fatal: cron runs successfully even if sentinel write fails.
        # The health endpoint will surface this as overdue.
        logger.warning("[CronHealth] Could not write sentinel for %s: %s", task_name, exc)


def get_cron_health(redis_client=None) -> dict:
    """Return health status of all registered crons.

    Returns:
        {
            "status": "healthy" | "degraded" | "error",
            "unhealthy_crons": [...],
            "crons": {
                "<task_name>": {
                    "status": "healthy" | "overdue" | "never_run",
                    "last_run_ago_seconds": int | None,
                    "threshold_seconds": int,
                }
            }
        }
    """
    try:
        rc = redis_client if redis_client is not None else _get_sync_redis()
    except Exception as exc:
        return {"status": "error", "error": str(exc), "crons": {}}

    now = int(time.time())
    results: dict = {}
    unhealthy: list[str] = []

    for task_name, max_seconds in CRON_EXPECTED_MAX_SECONDS.items():
        key = f"{_SENTINEL_KEY_PREFIX}{task_name}"
        try:
            last_run_raw = rc.get(key)
        except Exception as exc:
            logger.warning("[CronHealth] Redis error reading %s: %s", key, exc)
            results[task_name] = {
                "status": "error",
                "last_run_ago_seconds": None,
                "threshold_seconds": max_seconds,
            }
            unhealthy.append(task_name)
            continue

        if last_run_raw is None:
            results[task_name] = {
                "status": "never_run",
                "last_run_ago_seconds": None,
                "threshold_seconds": max_seconds,
            }
            unhealthy.append(task_name)
        else:
            try:
                last_run = int(last_run_raw)
            except (ValueError, TypeError):
                results[task_name] = {
                    "status": "invalid_data",
                    "last_run_ago_seconds": None,
                    "threshold_seconds": max_seconds,
                }
                unhealthy.append(task_name)
                continue

            ago = now - last_run
            status = "healthy" if ago <= max_seconds else "overdue"
            results[task_name] = {
                "status": status,
                "last_run_ago_seconds": ago,
                "threshold_seconds": max_seconds,
            }
            if status == "overdue":
                unhealthy.append(task_name)

    overall = "healthy" if not unhealthy else "degraded"
    return {"status": overall, "unhealthy_crons": unhealthy, "crons": results}
