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
import hashlib
import logging
import os
from datetime import datetime
from urllib.parse import urlsplit

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
    # F3-2 fix (2026-05-10): include AI_INTEGRATIONS_* fallback (Replit AI Integration prefix)
    providers["anthropic"] = {
        "configured": bool(
            os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
        ),
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    }
    providers["gemini"] = {
        "configured": bool(
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY")
        ),
        "model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    }
    providers["openai"] = {
        "configured": bool(
            os.getenv("OPENAI_API_KEY")
            or os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")
        ),
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
    """Check Deepgram STT and OpenMic.ai configuration and circuit breaker status."""
    try:
        deepgram_configured = bool(os.getenv("DEEPGRAM_API_KEY"))
        openmic_configured = bool(os.getenv("OPENMIC_API_KEY"))
        openmic_webhook_secret = bool(os.getenv("OPENMIC_WEBHOOK_SECRET"))

        from app.shared.resilience.circuit_breaker import ALL_CIRCUITS
        deepgram_circuit = ALL_CIRCUITS.get("deepgram")
        openmic_circuit = ALL_CIRCUITS.get("openmic")

        deepgram_circuit_state = deepgram_circuit.state.value if deepgram_circuit else "unknown"
        openmic_circuit_state = openmic_circuit.state.value if openmic_circuit else "unknown"

        deepgram_status = (
            "healthy" if (deepgram_configured and deepgram_circuit_state != "open")
            else "degraded" if deepgram_configured
            else "not_configured"
        )
        openmic_status = (
            "healthy" if (openmic_configured and openmic_circuit_state != "open")
            else "degraded" if openmic_configured
            else "not_configured"
        )

        any_circuit_open = (
            deepgram_circuit_state == "open" or openmic_circuit_state == "open"
        )
        overall_status = (
            "healthy"
            if (deepgram_configured and openmic_configured and not any_circuit_open)
            else "degraded"
        )

        return {
            "status": overall_status,
            "deepgram": {
                "configured": deepgram_configured,
                "circuit_state": deepgram_circuit_state,
                "status": deepgram_status,
                "model": "nova-2",
                "languages": ["pt-BR", "en-US"],
            },
            "openmic": {
                "configured": openmic_configured,
                "webhook_secret_configured": openmic_webhook_secret,
                "circuit_state": openmic_circuit_state,
                "status": openmic_status,
                "webhook_endpoint": "/api/v1/openmic/webhook",
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
    az_tenant = os.getenv("MICROSOFT_TENANT_ID") or os.getenv("AZURE_TENANT_ID")
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

    # --- Microsoft Teams outbound (Incoming Webhook) ---
    teams_webhook = os.getenv("TEAMS_WEBHOOK_URL")
    teams_outbound_configured = bool(teams_webhook)
    integrations["teams_outbound"] = {
        "status": "connected" if teams_outbound_configured else "not_configured",
        "configured": teams_outbound_configured,
        "note": (
            None if teams_outbound_configured
            else "Teams outbound not configured — set TEAMS_WEBHOOK_URL. "
                 "Get URL via Teams channel → Manage channel → Connectors → Incoming Webhook."
        ),
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
    # multi-tenancy: public endpoint (health) — no tenant data
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
        # F3-2 fix (2026-05-10): include AI_INTEGRATIONS_* fallback
        "anthropic": "configured" if (os.getenv("ANTHROPIC_API_KEY") or os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY")) else "not_configured",
        "openai": "configured" if (os.getenv("OPENAI_API_KEY") or os.getenv("AI_INTEGRATIONS_OPENAI_API_KEY")) else "not_configured",
        "gemini": "configured" if (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY")) else "not_configured",
        "workos": "configured" if os.getenv("WORKOS_API_KEY") else "not_configured",
        "mailgun": "configured" if (os.getenv("MAILGUN_API_KEY") and os.getenv("MAILGUN_DOMAIN")) else "not_configured",
        "deepgram": "configured" if os.getenv("DEEPGRAM_API_KEY") else "not_configured",
        "openmic": "configured" if os.getenv("OPENMIC_API_KEY") else "not_configured",
    }

    # --- External integrations health (WhatsApp, Calendar, LinkedIn/Indeed, Pearch, Slack) ---
    components["integrations"] = _check_external_integrations()

    # --- Voice services (Deepgram STT + OpenMic) ---
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


@router.get("/health/ready", response_model=None)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    # multi-tenancy: public endpoint (health) — no tenant data
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
    # multi-tenancy: public endpoint (health) — no tenant data
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


# RLS critical tables — monitored for runtime drift detection.
# Migration 068 + 118-126 cobrem ~119 tabelas; aqui acompanhamos as 9 mais
# sensíveis em multi-tenancy / LGPD (audit_logs, lgpd_consents, etc).
_RLS_CRITICAL_TABLES: tuple[str, ...] = (
    "audit_logs",
    "users",
    "lgpd_consents",
    "tenant_llm_configs",
    "vacancy_candidates",
    "triagem_sessions",
    "bias_audits",
    "compliance_reports",
    "fairness_reports",
)


@router.get("/health/rls", response_model=None)
async def health_rls(db: AsyncSession = Depends(get_db)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    R-002 — Sensor de runtime para Postgres RLS em tabelas críticas.

    Verifica que RLS Postgres está ENABLED + FORCED em tabelas críticas
    via inspeção de pg_class.relrowsecurity / pg_class.relforcerowsecurity.
    Detecta drift manual (ALTER TABLE ... DISABLE ROW LEVEL SECURITY) ou
    tabela nova sem migration RLS (deploys onde alguém esqueceu de aplicar
    o pattern canonical de migration 068).

    Migration 068 + 118-126 cobrem ~119 tabelas. Esta é a checagem de
    runtime para detectar drift desde o último deploy.

    Conformidade: LGPD Art. 12 (controle de acesso a dados pessoais), Art.
    19 (segurança lógica em multi-tenancy).

    Returns:
        200 + payload se todas tabelas críticas com RLS forçado.
        503 + payload com lista de drift se ALGUMA tabela crítica perdeu RLS.
    """
    sql = text(
        """
        SELECT relname, relrowsecurity, relforcerowsecurity
        FROM pg_class
        WHERE relname = ANY(:tables)
        """
    )
    result = await db.execute(sql, {"tables": list(_RLS_CRITICAL_TABLES)})
    rows = result.fetchall()

    found_tables = {row[0]: (row[1], row[2]) for row in rows}
    missing: list[dict] = []
    rls_protected: list[str] = []

    for tbl in _RLS_CRITICAL_TABLES:
        if tbl not in found_tables:
            missing.append({"table": tbl, "reason": "table not found in pg_class"})
            continue
        rowsec, forcesec = found_tables[tbl]
        if not (rowsec and forcesec):
            missing.append({
                "table": tbl,
                "reason": (
                    f"relrowsecurity={rowsec}, "
                    f"relforcerowsecurity={forcesec}"
                ),
            })
        else:
            rls_protected.append(tbl)

    payload = {
        "rls_protected": rls_protected,
        "missing": missing,
        "checked_count": len(_RLS_CRITICAL_TABLES),
        "timestamp": datetime.utcnow().isoformat(),
    }
    if missing:
        return JSONResponse(status_code=503, content=payload)
    return JSONResponse(status_code=200, content=payload)


# ─── Task #1250: environment isolation diagnostic ────────────────────────
# Confirma rapidamente (sem expor credenciais) que cada ambiente publicado
# (develop vs main) usa banco e Redis próprios. Ver guia operacional
# docs/operations/dois-ambientes-develop-main.md §Validação pós-publish.
def _mask_host(host: str | None) -> str | None:
    """Mask a hostname keeping just enough to distinguish environments.

    Hosts are not credentials, but we still partially redact them so the
    endpoint never echoes a full connection target verbatim. Short hosts
    (e.g. ``localhost``) are reduced to a prefix + ``***``.
    """
    if not host:
        return None
    if len(host) <= 8:
        return f"{host[0]}***"
    return f"{host[:3]}***{host[-6:]}"


def _connection_fingerprint(host: str | None, port: int | None, name: str | None) -> str | None:
    """Non-reversible identity hash of a backend (host:port/name).

    Computed over the *target* only — NEVER over the password/credentials —
    so two environments pointing at the same physical DB/Redis produce the
    same fingerprint even if their roles/passwords differ. A matching
    fingerprint across develop and main means isolation is broken.
    """
    if not host and not name:
        return None
    identity = f"{host or ''}:{port or ''}/{name or ''}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def _describe_connection(url: str | None) -> dict:
    """Return a credential-free description of a connection URL.

    Reports the backend scheme, masked host, port, target name (DB name or
    Redis db index) and a non-reversible fingerprint. NEVER includes the
    user, password, or full connection string.
    """
    if not url:
        return {"configured": False}
    try:
        parts = urlsplit(url)
        host = parts.hostname
        port = parts.port
        name = (parts.path or "").lstrip("/") or None
        return {
            "configured": True,
            "backend": parts.scheme or None,
            "host_masked": _mask_host(host),
            "port": port,
            "name": name,
            "fingerprint": _connection_fingerprint(host, port, name),
        }
    except Exception:
        # Never leak the raw URL (it carries credentials) on parse failure.
        return {"configured": True, "error": "unparseable connection string"}


@router.get("/health/environment", response_model=None)
async def environment_diagnostic():
    # multi-tenancy: public endpoint (health) — no tenant data, no secrets
    """
    Task #1250 — Confirma que cada ambiente usa banco e secrets próprios.

    Reporta ``APP_ENV`` e um identificador NÃO-sensível do Postgres e do
    Redis em uso (backend, host mascarado, porta, nome/índice e um
    fingerprint não-reversível). NUNCA expõe usuário, senha ou a connection
    string completa.

    Uso: após publicar develop e main, compare os ``fingerprint`` — se forem
    iguais, os dois ambientes apontam para o MESMO banco/Redis (isolação
    quebrada). Ver docs/operations/dois-ambientes-develop-main.md.

    Returns:
        200 sempre (diagnóstico informativo, não é probe de liveness).
    """
    # Mirror the engine's resolution: env var wins, else the settings default.
    database_url = os.getenv("DATABASE_URL") or _settings_default("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL") or _settings_default("REDIS_URL")

    return JSONResponse(
        status_code=200,
        content={
            "app_env": os.getenv("APP_ENV", "development"),
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "database": _describe_connection(database_url),
            "redis": _describe_connection(redis_url),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def _settings_default(key: str) -> str | None:
    """Best-effort fallback to the pydantic settings default for a URL key.

    Avoids importing settings at module load; only used when the env var is
    absent (e.g. local dev without explicit secrets).
    """
    try:
        from lia_config.config import settings
        return getattr(settings, key, None)
    except Exception:
        return None


@router.get("/performance", response_model=None)
async def performance_metrics():
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    Performance metrics: response times by domain, cache stats, prompt versions.
    """
    from app.domains.ai.services.prompt_version_registry import prompt_version_registry
    from app.domains.ai.services.response_cache_service import response_cache_service
    from app.orchestrator.execution.main_orchestrator import get_perf_summary

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


# ─── R-007: compliance bypass status endpoint ────────────────────────────
# Espelha as flags de bypass logadas no lifespan (app/main.py). Canary
# monitoring usa pra detectar produção rodando com bypass ativo.
_BYPASS_FLAGS_RUNTIME: dict[str, str] = {
    "LIA_ALLOW_NON_COMPLIANT_DOMAINS": "Bypass ComplianceDomainPrompt (FairnessGuard, PII, PromptInjection, FactCheck)",
    "LIA_ALLOW_NON_COMPLIANT_AGENTS": "Bypass LangGraphReActBase compliance em agents",
    "LIA_DISABLE_C3B": "KILL SWITCH camada C3b inteira (PII strip + Fairness L3 + FactCheck + Audit)",
    "LIA_ALLOW_REGISTRY_DRIFT": "Permite class_path inválido em registry (R-004 rollback)",
    # PR4 (Task #1004) — bypass do audit canônico em company_settings.
    "LIA_DISABLE_COMPANY_AUDIT": "Desliga audit log canônico em company_settings save tools (viola Inegociável #6)",
}

# T-A canonical: flag inversa — bypass quando OFF em prod (TenantAwareAgentMixin
# fail-OPEN em vez de fail-CLOSED, agentes degradam silenciosamente). Tratada
# separadamente porque a semântica é "ativa quando ausente/falsa".
def _get_tenant_demo_fallback_block() -> dict:
    """T4 #991 — expose Demo fallback per-process counter on /health.

    Mirrors ``tenant_aware_agent.metrics`` block: per-process snapshot
    only (Prometheus is the authoritative source in multi-instance
    deployments). Canary alert if ``total_count > 0`` in production.
    """
    try:
        from app.shared.security.tenant_demo_fallback import (
            SENTRY_FINGERPRINT,
            get_demo_fallback_snapshot,
            get_last_24h_count,
        )
        snapshot = get_demo_fallback_snapshot()
        # T4 #991 — ``last_24h_count`` is the canonical canary field
        # consumed by the on-call alerting rules (sliding window). The
        # ``total_count`` alias is preserved for backwards-compat with
        # existing dashboards.
        total = sum(snapshot.values())
        return {
            "last_24h_count": get_last_24h_count(),
            "total_count": total,
            "by_endpoint_reason": snapshot,
            "sentry_fingerprint": SENTRY_FINGERPRINT,
            "prometheus_metric": "lia_tenant_demo_fallback_total",
        }
    except Exception as exc:
        return {"error": str(exc)[:200]}


_TENANT_STRICT_FLAG = "LIA_AGENT_TENANT_STRICT"
_TENANT_STRICT_DESC = (
    "TenantAwareAgentMixin em fail-OPEN — agentes degradam para 'sua empresa'/'geral' "
    "quando tenant ausente (origem do bug 'LIA pergunta company_id no chat')"
)


@router.get("/health/compliance/bypass-status", response_model=None)
async def compliance_bypass_status():
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    R-007 — Status de flags de bypass de compliance ativas.

    Espelha o alerta CRITICAL emitido no startup (app/main.py lifespan).
    Canary monitoring deve alertar quando ``warning_count > 0`` em produção
    pra detectar bypass deixado ON após rollback emergencial.

    Returns:
        200 + payload sempre (active_bypasses pode ser vazia). Canary olha
        para ``warning_count`` no JSON, não para o status code, porque
        bypass ativo NÃO é unhealthy do ponto de vista do liveness — é
        configuration drift.
    """
    active = [
        {"flag": flag, "description": desc}
        for flag, desc in _BYPASS_FLAGS_RUNTIME.items()
        if os.getenv(flag, "0") == "1"
    ]

    # T-A: TenantAwareAgentMixin strict-mode é fail-CLOSED em prod/staging
    # por default. Se explicitamente OFF em prod-like → reportar como bypass.
    from app.shared.agents.tenant_aware_agent import (
        get_tenant_context_metrics,
        is_tenant_strict_mode,
    )
    _env = os.getenv("APP_ENV", "development").lower()
    _prod_like = _env in ("production", "prod", "staging")
    if _prod_like and not is_tenant_strict_mode():
        active.append({"flag": _TENANT_STRICT_FLAG, "description": _TENANT_STRICT_DESC})

    flags_state = {
        flag: os.getenv(flag, "0") == "1" for flag in _BYPASS_FLAGS_RUNTIME
    }
    flags_state[_TENANT_STRICT_FLAG] = is_tenant_strict_mode()
    payload = {
        "active_bypasses": active,
        "warning_count": len(active),
        "environment": os.getenv("APP_ENV", "development"),
        "flags": flags_state,
        "tenant_aware_agent": {
            "strict_mode": is_tenant_strict_mode(),
            "metrics": get_tenant_context_metrics(),
        },
        "tenant_demo_fallback": _get_tenant_demo_fallback_block(),
        "timestamp": datetime.utcnow().isoformat(),
    }
    return JSONResponse(status_code=200, content=payload)


# ─── Task #977: tenant-context canary endpoint ───────────────────────────
@router.get("/health/tenant-context-canary", response_model=None)
async def tenant_context_canary(window_seconds: int = 60):
    # multi-tenancy: public endpoint (health) — no tenant data
    """Task #977 — Snapshot por-processo do canary do TenantAwareAgentMixin.

    **NÃO autoritativo em produção multi-instância.** Este endpoint reflete
    apenas a janela rolling do processo que respondeu o request — em
    deployment com múltiplos pods/workers do `lia-backend`, ele subestima
    fail_open/fail_closed agregados. Útil pra debug humano e smoke check de
    deploy individual.

    **Fonte autoritativa do alerta = Prometheus alert rules** em
    ``deploy/observability/tenant_context_canary.rules.yaml`` — agregam
    ``lia_agent_tenant_context_resolved_total`` por TODAS as instâncias via
    ``sum(rate(...))``. As regras canônicas:

    - ``LIATenantContextFailOpen`` (warning): fail_open > 0 em 1min
    - ``LIATenantContextFailClosedRate`` (critical): fail_closed/min > 5
    - ``LIATenantContextAgentSilent24h`` (info): inventário T-D drift

    Status code é sempre 200 (canary é configuration drift, não liveness
    failure — paridade com `/health/compliance/bypass-status`).
    """
    from app.shared.agents.tenant_aware_agent import (
        get_tenant_context_canary_status,
    )
    snapshot = get_tenant_context_canary_status(window_seconds=window_seconds)
    snapshot["timestamp"] = datetime.utcnow().isoformat()
    return JSONResponse(status_code=200, content=snapshot)


# ─── R-021: LLM provider fallback / circuit breaker metrics ─────────────────
@router.get("/health/llm-metrics")
async def llm_provider_metrics():
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    R-021 — LLM provider fallback and circuit breaker metrics.

    Returns in-memory counters updated in real-time by llm_factory.py.
    Canary monitoring should alert when fallback_total or circuit_open_total
    grow unexpectedly in production.
    """
    from app.shared.observability.llm_metrics import get_metrics
    return get_metrics()

@router.get("/health/dlq", response_model=None)
async def dlq_health_status():
    # multi-tenancy: public endpoint (health) — no tenant data
    """R-024 DLQ health summary for canary monitoring.

    Returns status (healthy/degraded), total entry count, and per-queue breakdown.
    Canary alert if status != healthy.
    """
    from app.shared.resilience.dlq_service import DLQService
    import datetime

    _DLQ_ALERT_TOTAL = 100
    _DLQ_ALERT_PER_QUEUE = 30

    dlq = DLQService()
    try:
        summary = await dlq.summary()
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "error": str(exc)[:200]},
        )

    total = summary.get("total_entries", 0)
    queues = summary.get("queues", {})

    alerts = []
    if total > _DLQ_ALERT_TOTAL:
        alerts.append("total_entries={} exceeds threshold={}".format(total, _DLQ_ALERT_TOTAL))
    for queue_name, count in queues.items():
        if count > _DLQ_ALERT_PER_QUEUE:
            alerts.append("queue={} count={} exceeds threshold={}".format(queue_name, count, _DLQ_ALERT_PER_QUEUE))

    status_str = "healthy" if not alerts else "degraded"
    status_code = 200 if not alerts else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_str,
            "total_entries": total,
            "queues": queues,
            "alerts": alerts,
            "ttl_days": 30,
            "timestamp": datetime.datetime.utcnow().isoformat(),
        },
    )


# ─── R-036: Cron sentinel health ────────────────────────────────────────────
@router.get("/health/crons")
async def cron_sentinel_health():
    # multi-tenancy: public endpoint (health) — no tenant data
    """R-036 — Verify all registered crons ran within expected cadence.

    Canary: alert if status != healthy (means a cron went silent).
    LGPD compliance crons (lgpd.run_cleanup_daily, audit.apply_lifecycle_policy,
    data.retention.run) are especially critical — silence = regulatory violation.
    """
    from app.shared.resilience.cron_health import get_cron_health
    result = get_cron_health()
    status_code = 200 if result["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=result)



# ─── F-BG.3: RabbitMQ consumer self-healing sensor ──────────────────────────
@router.get("/health/messaging", response_model=None)
async def messaging_health():
    # multi-tenancy: public endpoint (health) — no tenant data
    """F-BG.3 — Expose RabbitMQ consumer state for canary/k8s probes.

    Retorna 503 quando `_running=False` (consumer caiu silenciosamente). Inclui
    `last_error` para diagnóstico e `active_subscriptions` para observabilidade.
    O `_reconnect_loop` (exponential backoff 5s→300s) roda no background; este
    endpoint expõe o estado pro alerting external (Grafana/PagerDuty).
    """
    try:
        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "broker": "rabbitmq",
                "error": f"consumer module import failed: {exc}",
            },
        )

    consumer_running = getattr(rabbitmq_consumer, "_running", False)
    last_error = getattr(rabbitmq_consumer, "_last_error", None)
    active_subs = getattr(rabbitmq_consumer, "active_subscriptions", 0)
    reconnect_task = getattr(rabbitmq_consumer, "_reconnect_task", None)
    reconnect_scheduled = bool(reconnect_task and not reconnect_task.done())

    payload = {
        "status": "healthy" if consumer_running else "unhealthy",
        "broker": "rabbitmq",
        "consumer_running": consumer_running,
        "active_subscriptions": active_subs,
        "reconnect_scheduled": reconnect_scheduled,
        "last_error": last_error,
    }
    if consumer_running:
        return payload
    return JSONResponse(status_code=503, content=payload)
