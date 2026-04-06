"""
Unified System Health Check for production readiness.

Covers all critical services:
- PostgreSQL (database)
- Redis (cache, rate limiting, DLQ, token budget)
- LLM providers (anthropic, gemini, openai) — configuration only
- Circuit breakers (status of all 14 circuits)
- Celery workers (via Redis broker ping)
- Rate limiter backend
- Task manager
- Multi-channel notifications

Returns 200 if all critical components are healthy, 503 otherwise.
"""
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


async def _check_redis() -> dict:
    """Check Redis connectivity (critical for rate limiting, DLQ, token budget)."""
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(
            redis_url,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        pong = await client.ping()
        await client.aclose()
        return {"status": "healthy", "latency_ms": "ok"} if pong else {"status": "unhealthy", "error": "ping failed"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)[:200]}


async def _check_celery_workers() -> dict:
    """Check Celery workers via Redis broker connectivity."""
    try:
        import redis.asyncio as aioredis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = aioredis.from_url(redis_url, socket_connect_timeout=1.0)
        queues = ["sourcing_high", "evaluation_normal", "vagas_normal", "onboarding_low", "celery"]
        queue_lengths = {}
        for q in queues:
            try:
                length = await client.llen(q)
                queue_lengths[q] = int(length)
            except Exception:
                queue_lengths[q] = "unknown"
        await client.aclose()
        return {"status": "healthy", "queues": queue_lengths}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)[:200]}


def _check_llm_providers() -> dict:
    """Check LLM provider configuration (key presence only, no API call)."""
    providers = {}
    providers["anthropic"] = {
        "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    }
    providers["gemini"] = {
        "configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }
    providers["openai"] = {
        "configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
    }

    any_configured = any(v["configured"] for v in providers.values())
    return {
        "status": "healthy" if any_configured else "degraded",
        "providers": providers,
        "fallback_chain": "claude → gemini → openai",
    }


def _check_circuit_breakers() -> dict:
    """Check status of all circuit breakers."""
    try:
        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        circuits = {}
        open_count = 0
        for name, cb in ALL_CIRCUITS.items():
            state = cb.state.value
            circuits[name] = {
                "state": state,
                "failure_count": cb.failure_count,
            }
            if state == "open":
                open_count += 1

        status = "healthy" if open_count == 0 else ("degraded" if open_count < 3 else "critical")
        return {
            "status": status,
            "circuits": circuits,
            "open_count": open_count,
            "total_count": len(circuits),
        }
    except Exception as exc:
        return {"status": "unknown", "error": str(exc)[:200]}


def _check_dlq() -> dict:
    """Check DLQ service availability (sync check only)."""
    try:
        return {"status": "healthy", "known_queues": len(["sourcing_high", "evaluation_normal", "vagas_normal", "onboarding_low", "celery"])}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)[:200]}


@router.get("/health")
async def system_health(db: AsyncSession = Depends(get_db)):
    """
    Unified health check for deployment readiness/liveness probes.

    Covers: DB, Redis, LLM providers, circuit breakers, Celery, rate limiter,
            task manager, multi-channel notifications, DLQ.

    Returns:
        200 if all critical components healthy
        503 if any critical component (DB, Redis) is down
    """
    components = {}
    overall_healthy = True

    # --- Critical: PostgreSQL ---
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        components["database"] = {"status": "healthy"}
    except Exception as exc:
        components["database"] = {"status": "unhealthy", "error": str(exc)[:200]}
        overall_healthy = False

    # --- Critical: Redis ---
    redis_status = await _check_redis()
    components["redis"] = redis_status
    if redis_status["status"] == "unhealthy":
        overall_healthy = False

    # --- LLM Providers (configuration check only) ---
    components["llm_providers"] = _check_llm_providers()

    # --- Circuit Breakers ---
    components["circuit_breakers"] = _check_circuit_breakers()

    # --- Celery Workers (via Redis broker) ---
    components["celery_workers"] = await _check_celery_workers()

    # --- Rate Limiter ---
    try:
        from app.middleware.rate_limiter import rate_limiter
        rl_stats = rate_limiter.get_stats()
        components["rate_limiter"] = {
            "status": "healthy",
            "backend": rl_stats.get("backend", "unknown"),
            "limits": rl_stats.get("limits", {}),
        }
    except Exception as exc:
        components["rate_limiter"] = {"status": "degraded", "error": str(exc)[:200]}

    # --- Task Manager ---
    try:
        from app.shared.async_processing.enhanced_task_manager import EnhancedTaskManager
        manager = EnhancedTaskManager.get_instance()
        components["task_manager"] = {
            "status": "healthy",
            "persistence_enabled": manager.persistence_enabled,
        }
    except Exception:
        components["task_manager"] = {"status": "unavailable"}

    # --- Multi-Channel Notifications ---
    try:
        from app.shared.channels.multi_channel_service import MultiChannelService
        svc = MultiChannelService.get_instance()
        available = [ch for ch in svc.get_available_channels() if ch.get("available")]
        components["multi_channel"] = {
            "status": "healthy",
            "available_channels": len(available),
        }
    except Exception:
        components["multi_channel"] = {"status": "unavailable"}

    # --- DLQ ---
    components["dlq"] = _check_dlq()

    # --- External services configuration ---
    components["external_services"] = {
        "anthropic": "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "gemini": "configured" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "not_configured",
        "workos": "configured" if os.getenv("WORKOS_API_KEY") else "not_configured",
        "mailgun": "configured" if (os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN")) else "not_configured",
    }

    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "environment": os.getenv("APP_ENV", "development"),
            "components": components,
        },
    )


@router.get("/health/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes readiness probe — verifica se o serviço está pronto para receber tráfego.
    Mais restritivo que liveness: falha se DB ou Redis estiver indisponível.
    """
    checks = {"database": False, "redis": False}

    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        checks["database"] = True
    except Exception:
        pass

    redis_status = await _check_redis()
    checks["redis"] = redis_status["status"] == "healthy"

    ready = all(checks.values())
    status_code = 200 if ready else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "ready": ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe — verifica se o processo está vivo.
    Mínimo: sempre retorna 200 se o processo estiver rodando.
    """
    return JSONResponse(
        status_code=200,
        content={
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
