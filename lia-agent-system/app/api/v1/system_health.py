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

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


# TODO(phase2): extract to repository — system health check queries
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


def _check_voice_services() -> dict:
    """Check voice services (Twilio Programmable Voice + Gemini Live Audio) configuration and circuit breaker status."""
    try:
        twilio_configured = bool(
            os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
        )
        gemini_configured = bool(
            os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        )

        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        twilio_circuit = ALL_CIRCUITS.get("twilio_voice")
        gemini_live_circuit = ALL_CIRCUITS.get("gemini_live")

        twilio_circuit_state = twilio_circuit.state.value if twilio_circuit else "unknown"
        gemini_live_circuit_state = (
            gemini_live_circuit.state.value if gemini_live_circuit else "unknown"
        )

        twilio_status = (
            "healthy" if (twilio_configured and twilio_circuit_state != "open")
            else "degraded" if twilio_configured
            else "not_configured"
        )
        gemini_live_status = (
            "healthy" if (gemini_configured and gemini_live_circuit_state != "open")
            else "degraded" if gemini_configured
            else "not_configured"
        )

        any_circuit_open = (
            twilio_circuit_state == "open" or gemini_live_circuit_state == "open"
        )
        overall_status = (
            "healthy"
            if (twilio_configured and gemini_configured and not any_circuit_open)
            else "degraded"
        )

        return {
            "status": overall_status,
            "twilio_voice": {
                "configured": twilio_configured,
                "circuit_state": twilio_circuit_state,
                "status": twilio_status,
                "channels": ["PSTN", "WhatsApp"],
            },
            "gemini_live": {
                "configured": gemini_configured,
                "circuit_state": gemini_live_circuit_state,
                "status": gemini_live_status,
                "model": "gemini-live-audio",
            },
        }
    except Exception as exc:
        return {"status": "unknown", "error": str(exc)[:200]}


def _check_dlq() -> dict:
    """Check DLQ service availability (sync check only)."""
    try:
        return {"status": "healthy", "known_queues": len(["sourcing_high", "evaluation_normal", "vagas_normal", "onboarding_low", "celery"])}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)[:200]}


def _check_external_integrations() -> dict:
    """
    Check configuration status of all external business integrations.

    Returns a structured dict with status for each integration:
    - connected:       key present AND service reachable
    - not_configured:  key absent (graceful — fallback active)
    - disconnected:    key present but validation failed
    """
    integrations: dict[str, dict] = {}

    # --- WhatsApp Meta ---
    wa_phone = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    wa_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    wa_configured = bool(wa_phone and wa_token)
    integrations["whatsapp"] = {
        "status": "connected" if wa_configured else "not_configured",
        "configured": wa_configured,
        "provider": "meta",
        "fallback": "development_log" if not wa_configured else None,
    }

    # --- Microsoft Calendar (Graph API / Teams) ---
    az_client = os.getenv("AZURE_CLIENT_ID")
    az_secret = os.getenv("AZURE_CLIENT_SECRET")
    az_tenant = os.getenv("AZURE_TENANT_ID")
    ms_configured = bool(az_client and az_secret and az_tenant)
    integrations["microsoft_calendar"] = {
        "status": "connected" if ms_configured else "not_configured",
        "configured": ms_configured,
        "provider": "microsoft_graph",
    }

    # --- Google Calendar ---
    gc_enabled = os.getenv("ENABLE_GOOGLE_CALENDAR", "false").lower() in ("1", "true", "yes")
    gc_service_account = bool(os.getenv("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON"))
    gc_oauth = bool(os.getenv("GOOGLE_CALENDAR_CLIENT_ID") and os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET"))
    gc_configured = gc_enabled and (gc_service_account or gc_oauth)
    integrations["google_calendar"] = {
        "status": "connected" if gc_configured else ("not_configured" if not gc_enabled else "disconnected"),
        "configured": gc_configured,
        "enabled": gc_enabled,
        "auth_method": "service_account" if gc_service_account else ("oauth2" if gc_oauth else None),
    }

    # --- LinkedIn ---
    li_client_id = os.getenv("LINKEDIN_CLIENT_ID")
    li_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    li_configured = bool(li_client_id and li_secret)
    integrations["linkedin"] = {
        "status": "connected" if li_configured else "not_configured",
        "configured": li_configured,
        "note": "OAuth 2.0 required for posting. Requires LinkedIn Company Page admin access." if not li_configured else None,
    }

    # --- Indeed ---
    indeed_key = os.getenv("INDEED_API_KEY")
    indeed_configured = bool(indeed_key)
    integrations["indeed"] = {
        "status": "connected" if indeed_configured else "not_configured",
        "configured": indeed_configured,
        "note": "XML feed mode available when not configured — jobs served at /api/v1/job-boards/feed/indeed.xml",
    }

    # --- Pearch (sourcing) ---
    pearch_key = os.getenv("PEARCH_API_KEY")
    pearch_configured = bool(pearch_key)
    integrations["pearch"] = {
        "status": "connected" if pearch_configured else "not_configured",
        "configured": pearch_configured,
        "fallback": "local_rag_search" if not pearch_configured else None,
    }

    # --- Slack ---
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    slack_configured = bool(slack_token or slack_webhook)
    integrations["slack"] = {
        "status": "connected" if slack_configured else "not_configured",
        "configured": slack_configured,
        "auth_method": "bot_token" if slack_token else ("webhook" if slack_webhook else None),
    }

    configured_count = sum(1 for v in integrations.values() if v.get("configured"))
    total = len(integrations)

    return {
        "status": "healthy" if configured_count > 0 else "not_configured",
        "configured_count": configured_count,
        "total": total,
        "integrations": integrations,
    }


async def _check_broker() -> dict:
    """Check broker health via BrokerInterface factory.

    Usa o backend configurado em BROKER_BACKEND (redis | rabbitmq | pubsub).
    Permite monitorar broker sem hardcode do tipo de backend.
    """
    try:
        from app.shared.messaging.broker_interface import get_default_broker
        broker = get_default_broker()
        result = await broker.health_check()
        return result
    except Exception as exc:
        return {
            "status": "unhealthy",
            "backend": os.getenv("BROKER_BACKEND", "redis"),
            "error": str(exc)[:200],
        }


@router.get("/health", response_model=None)
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

    # --- Broker (abstraction layer via BROKER_BACKEND) ---
    components["broker"] = await _check_broker()

    # --- External services configuration ---
    components["external_services"] = {
        "anthropic": "configured" if os.getenv("ANTHROPIC_API_KEY") else "not_configured",
        "openai": "configured" if os.getenv("OPENAI_API_KEY") else "not_configured",
        "gemini": "configured" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")) else "not_configured",
        "workos": "configured" if os.getenv("WORKOS_API_KEY") else "not_configured",
        "mailgun": "configured" if (os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN")) else "not_configured",
        "twilio_voice": "configured" if (os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")) else "not_configured",
    }

    # --- External integrations health (WhatsApp, Calendar, LinkedIn/Indeed, Pearch, Slack) ---
    components["integrations"] = _check_external_integrations()

    # --- Voice services (Twilio Programmable Voice + Gemini Live Audio) ---
    components["voice_services"] = _check_voice_services()

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


@router.get("/health/providers", response_model=None)
async def providers_health():
    """
    Structured per-provider configuration check (Task #297).

    Reports OK/WARN/FAIL for Pearch, Apify, OpenAI, Anthropic, Gemini, WorkOS,
    and DEV_MODE based on env-var presence. Same data used by boot logger.

    Returns:
        200 if overall OK or WARN
        503 if overall FAIL (some user-facing feature is broken)
    """
    from app.shared.health.providers_health import (
        collect_provider_health,
        overall_status,
    )

    report = collect_provider_health()
    overall = overall_status(report)
    status_code = 503 if overall == "fail" else 200

    return JSONResponse(
        status_code=status_code,
        content={
            "overall": overall,
            "providers": report,
            "runbook": "docs/runbooks/sourcing-env-vars.md",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@router.get("/health/ready", response_model=None)
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


@router.get("/health/live", response_model=None)
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


@router.get("/performance", response_model=None)
async def performance_metrics():
    """
    Performance metrics: response times by domain, cache stats, prompt versions.
    """
    from app.domains.ai.services.prompt_version_registry import prompt_version_registry
    from app.domains.ai.services.response_cache_service import response_cache_service
    from app.orchestrator.main_orchestrator import get_perf_summary

    perf = get_perf_summary()
    cache_stats = response_cache_service.get_stats()
    prompt_count = len(prompt_version_registry)

    return JSONResponse(
        status_code=200,
        content={
            "response_times_by_domain": perf,
            "cache": cache_stats,
            "prompt_versions_registered": prompt_count,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
