"""
LIA Agent System - Main FastAPI application.
"""
# === LLM Bootstrap: monkey-patch SDK constructors for PII + audit + tenant ===
# MUST be first import — before anything instantiates Anthropic/OpenAI/GenAI
from app.shared.llm_bootstrap import install_llm_guards

install_llm_guards()

import logging
import os
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.sentry import init_sentry

init_sentry()

from app.api import orchestrator_routes
from app.config.langsmith import configure_langsmith
from app.core.config import settings
from app.core.database import AsyncSessionLocal, init_db
from app.core.logging_middleware import StructuredLoggingMiddleware
from app.domains.automation.services.automation_handlers import register_all_handlers
from app.domains.automation.services.automation_scheduler import automation_scheduler
from app.middleware.auth_enforcement import AuthEnforcementMiddleware
from app.middleware.rate_limiter import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.response_envelope import ResponseEnvelopeMiddleware
from app.shared.services.embedding_cache_service import embedding_cache
from app.domains.ai.services.llm import LLMService
from app.tools import initialize_tools

# Configure LangSmith tracing BEFORE logging
configure_langsmith()

from app.core.logging_config import configure_logging
from app.shared.pii_masking import install_global_pii_masking

configure_logging()
install_global_pii_masking()  # L7: LGPD — mascara CPF, e-mail, telefone e nomes em todos os logs
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events.
    """
    # Startup
    logger.info("🚀 Starting LIA Agent System...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Validate Microsoft Teams configuration
    if settings.MICROSOFT_APP_ID and settings.MICROSOFT_APP_PASSWORD:
        logger.info("✅ Microsoft Teams Bot configured")
    else:
        logger.warning("⚠️  Microsoft Teams Bot NOT configured (MICROSOFT_APP_ID/PASSWORD missing)")
        logger.warning("   Teams integration will not work until credentials are added")
    
    # Validate Microsoft Graph configuration
    if settings.AZURE_CLIENT_ID and settings.AZURE_CLIENT_SECRET and settings.AZURE_TENANT_ID:
        logger.info("✅ Microsoft Graph API configured (Outlook Calendar access enabled)")
    else:
        logger.warning("⚠️  Microsoft Graph API NOT configured (AZURE_CLIENT_ID/SECRET/TENANT_ID missing)")
        logger.warning("   Calendar/scheduling features will not work until credentials are added")
    
    # Structured provider healthcheck — Task #297
    # Reports OK/WARN/FAIL for Pearch, Apify, OpenAI, Anthropic, Gemini,
    # WorkOS, DEV_MODE based on env-var presence. Non-blocking in dev.
    try:
        from app.shared.health.providers_health import (
            collect_provider_health,
            log_boot_report,
        )
        _provider_report = collect_provider_health()
        log_boot_report(_provider_report)
    except Exception as exc:
        logger.warning("⚠️  Provider healthcheck error (non-blocking): %s", exc)

    # ─── Validate global LLM provider keys ────────────────────────────────────
    # The platform uses a hybrid LLM provisioning strategy:
    #   1. Per-tenant config in `tenant_llm_configs` table (encrypted, set via
    #      menu Configurações > Integrações > LLM)
    #   2. Global env vars as fallback for tenants without their own config
    # Without at least ONE provider key, agents will fail at runtime when the
    # first chat message arrives — silent outage. Warn loudly here.
    # Source-of-truth for key detection lives in providers_health so /health/providers
    # and the boot LLM gate never disagree (Task #297 code-review follow-up).
    _llm_report = _provider_report if "_provider_report" in dir() else {}
    has_anthropic = _llm_report.get("anthropic", {}).get("status") == "ok"
    has_gemini = _llm_report.get("gemini", {}).get("status") == "ok"
    has_openai = _llm_report.get("openai", {}).get("status") == "ok"
    if has_anthropic or has_gemini or has_openai:
        providers = [
            name
            for name, ok in (("anthropic", has_anthropic), ("gemini", has_gemini), ("openai", has_openai))
            if ok
        ]
        logger.info(f"✅ LLM provider(s) configured globally: {', '.join(providers)}")
        logger.info(
            "   Tenants without entries in `tenant_llm_configs` will use these as fallback."
        )
    else:
        logger.warning(
            "⚠️  NO LLM provider configured globally (AI_INTEGRATIONS_ANTHROPIC_API_KEY, "
            "ANTHROPIC_API_KEY, AI_INTEGRATIONS_GEMINI_API_KEY, OPENAI_API_KEY all empty)."
        )
        logger.warning(
            "   Agents will fail at runtime unless every tenant has its own entry "
            "in `tenant_llm_configs`. In production this is almost certainly a misconfiguration."
        )
        # In production environments, refuse to start with no LLM key at all.
        if os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging"):
            raise RuntimeError(
                "No LLM provider key configured globally and APP_ENV is production. "
                "Set AI_INTEGRATIONS_ANTHROPIC_API_KEY (or another provider) before deploying."
            )

    # Production safety guard: OPENMIC_ALLOW_UNSIGNED_WEBHOOK must never be true in prod
    _allow_unsigned = os.getenv("OPENMIC_ALLOW_UNSIGNED_WEBHOOK", "false").lower()
    _is_production = os.getenv("APP_ENV", "development").lower() in ("production", "prod", "staging")
    if _allow_unsigned == "true" and _is_production:
        logger.critical(
            "🚨 SECURITY: OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true is set in a production environment! "
            "This disables webhook signature verification. Remove this env var immediately."
        )
        raise RuntimeError(
            "OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true is not permitted in production. "
            "This bypasses webhook HMAC validation and must only be used in local development."
        )
    elif _allow_unsigned == "true":
        logger.warning(
            "⚠️  OPENMIC_ALLOW_UNSIGNED_WEBHOOK=true — webhook signature check bypassed "
            "(dev mode only). Remove before deploying to production."
        )
    elif not os.getenv("OPENMIC_WEBHOOK_SECRET"):
        logger.warning(
            "⚠️  OPENMIC_WEBHOOK_SECRET not set — OpenMic webhook endpoint will return 503 "
            "for all incoming requests. Set OPENMIC_WEBHOOK_SECRET to enable the endpoint."
        )
    else:
        logger.info("✅ OpenMic webhook configured (HMAC-SHA256 signature validation enabled)")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Seed dev demo user (idempotent) so dev auto-login can succeed on first request
    try:
        if os.getenv("APP_ENV", "development").lower() in ("development", "dev", "local"):
            from app.auth.dependencies import ensure_demo_user
            async with AsyncSessionLocal() as db:
                await ensure_demo_user(db)
            logger.info("✅ Dev demo user ensured (demo@wedotalent.com)")
    except Exception as e:
        logger.warning(f"⚠️ Dev demo user seed failed: {e}")

    # Domain auto-discovery
    from app.domains.registry import DomainRegistry
    domain_registry = DomainRegistry()
    registered = domain_registry.list_domains()
    logger.info(f"✅ Domain registry: {len(registered)} domains registered: {registered}")
    
    # Warm-up embedding cache
    try:
        async with AsyncSessionLocal() as db:
            await embedding_cache.warm_up(db)
    except Exception as e:
        logger.warning(f"⚠️ Embedding cache warm-up failed: {e}")
    
    try:
        from app.core.prompt_version_loader import register_all_prompts_at_startup
        _prompt_count = register_all_prompts_at_startup()
        logger.info(f"✅ PromptVersionRegistry: {_prompt_count} YAML prompts registered")
    except Exception as e:
        logger.warning(f"⚠️ Prompt version registration failed: {e}")

    try:
        from app.core.prompt_version_loader import bootstrap_experiments_from_yaml
        _exp_count = bootstrap_experiments_from_yaml()
        if _exp_count:
            logger.info(f"✅ A/B experiments: {_exp_count} loaded from YAML")
    except Exception as e:
        logger.warning(f"⚠️ A/B experiment bootstrap failed: {e}")

    # Initialize Orchestrator
    try:
        llm_service = LLMService()
        orchestrator_routes.initialize_orchestrator(llm_service)
        logger.info("✅ Multi-Agent Orchestrator initialized")
    except Exception as e:
        logger.error(f"❌ Orchestrator initialization failed: {e}")
        logger.warning("   Orchestrator endpoints will not work until initialization succeeds")
    
    # Start Automation Scheduler
    try:
        automation_scheduler.start()
        logger.info("✅ Automation Scheduler started")
    except Exception as e:
        logger.warning(f"⚠️ Automation Scheduler não iniciou: {e} — jobs periódicos inativos")
    
    # Initialize Stage Automation Engine and register handlers
    try:
        register_all_handlers()
        logger.info("✅ Stage Automation Engine initialized with handlers")
    except Exception as e:
        logger.error(f"❌ Stage Automation Engine initialization failed: {e}")
        logger.warning("   Automation triggers will not work until handlers are registered")
    
    # Initialize Tool Registry for function calling
    try:
        initialize_tools()
        logger.info("✅ Tool Registry initialized")
    except Exception as e:
        logger.error(f"❌ Tool Registry initialization failed: {e}")
        logger.warning("   Function calling tools will not work until registry is initialized")

    # Validate LLM circuit breaker configuration (timeouts, thresholds, fallbacks)
    try:
        from app.shared.resilience.circuit_breaker import validate_llm_circuit_configs
        _cb_validation = validate_llm_circuit_configs()
        if _cb_validation.get("_all_ok"):
            logger.info(
                "✅ LLM circuit breakers validated: anthropic=%.0fs/threshold=%d, "
                "openai=%.0fs/threshold=%d, gemini=%.0fs/threshold=%d",
                _cb_validation["anthropic"]["timeout_s"], _cb_validation["anthropic"]["failure_threshold"],
                _cb_validation["openai"]["timeout_s"], _cb_validation["openai"]["failure_threshold"],
                _cb_validation["gemini"]["timeout_s"], _cb_validation["gemini"]["failure_threshold"],
            )
        else:
            _issues = {k: v["issues"] for k, v in _cb_validation.items() if isinstance(v, dict) and not v.get("ok")}
            logger.error("❌ LLM circuit breaker validation failed: %s", _issues)
    except Exception as e:
        logger.warning("⚠️  LLM circuit breaker validation error (non-blocking): %s", e)

    try:
        from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
        await monitoring_loop.start()
        logger.info("✅ MonitoringLoop started (proactive pipeline checks every hour)")
    except Exception as e:
        logger.warning("⚠️  MonitoringLoop não iniciou: %s — alertas proativos inativos", e)

    # Seed PolicyEngine default rules (idempotente — skip-if-exists)
    try:
        from app.shared.services.policy_engine_service import PolicyEngineService
        _pe_stats = await PolicyEngineService().load_default_rules()
        logger.info(
            f"✅ PolicyEngine rules seeded: "
            f"{_pe_stats.get('business_rules_created', 0)} business, "
            f"{_pe_stats.get('rate_limit_rules_created', 0)} rate-limit, "
            f"{_pe_stats.get('escalation_rules_created', 0)} escalation criadas; "
            f"{_pe_stats.get('business_rules_skipped', 0) + _pe_stats.get('rate_limit_rules_skipped', 0) + _pe_stats.get('escalation_rules_skipped', 0)} já existiam"
        )
    except Exception as e:
        logger.warning(f"⚠️  PolicyEngine seed failed (non-blocking): {e}")

    # Initialize ReAct Agent Registry (7 domains: wizard, pipeline, sourcing, talent, jobs_management, kanban, policy)
    try:
        from lia_agents_core.react_agent_registry import register_react_agents
        register_react_agents()
        logger.info("✅ ReAct Agent Registry inicializado")
    except Exception as e:
        logger.error(f"❌ ReAct Agent Registry initialization failed: {e}")
        logger.warning("   ReAct agents will not be available via main chat flow")

    # Initialize RabbitMQ Consumer (Phase 4 — WS async response forwarding)
    try:
        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
        await rabbitmq_consumer.start()
        if rabbitmq_consumer._running:
            logger.info("✅ RabbitMQ Consumer iniciado")
        else:
            logger.info("ℹ️  RabbitMQ Consumer inativo (RABBITMQ_URL não configurado)")
    except Exception as e:
        logger.warning(f"⚠️  RabbitMQ Consumer não iniciado: {e}")

    # Register Platform Event Handlers (inter-API async communication via RabbitMQ)
    try:
        from app.api.v1.platform_event_handlers import register_all_handlers as register_platform_handlers
        register_platform_handlers()
        logger.info("✅ Platform Event Handlers registrados")
    except Exception as e:
        logger.warning(f"⚠️  Platform Event Handlers não registrados: {e}")

    # Seed A/B Testing email template variants (Fase 5 / A5 — idempotent)
    try:
        from app.shared.intelligence.ab_testing import seed_email_ab_tests
        async with AsyncSessionLocal() as _ab_db:
            _ab_result = await seed_email_ab_tests(_ab_db)
            logger.info(
                "✅ A/B Testing seeded: created=%d, skipped=%d",
                len(_ab_result.get("created", [])),
                len(_ab_result.get("skipped", [])),
            )
    except Exception as e:
        logger.warning(f"⚠️  A/B Testing seed failed (non-blocking): {e}")

    # Validate OpenAPI schema generation (pre-flight check — catch Pydantic schema errors at startup)
    try:
        schema = app.openapi()
        path_count = len(schema.get("paths", {}))
        schema_count = len(schema.get("components", {}).get("schemas", {}))
        logger.info(
            "✅ OpenAPI schema generated successfully: %d endpoints, %d schemas",
            path_count, schema_count,
        )
    except Exception as e:
        logger.error(
            "❌ OpenAPI schema generation failed — /openapi.json will return 500: %s", e,
            exc_info=True,
        )

    logger.info("🎯 LIA Agent System ready!")

    yield

    # Shutdown
    # Parar RabbitMQ Consumer
    try:
        from app.shared.messaging.rabbitmq_consumer import rabbitmq_consumer
        await rabbitmq_consumer.stop()
    except Exception:
        pass
    logger.info("🛑 Shutting down LIA Agent System...")
    
    try:
        from app.domains.recruiter_assistant.services.monitoring_loop import monitoring_loop
        await monitoring_loop.stop()
    except Exception:
        pass

    # Stop WebSocket manager (Redis pub/sub cleanup)
    try:
        from app.shared.websocket.ws_manager import ws_manager
        await ws_manager.shutdown()
    except Exception:
        pass

    # Stop Automation Scheduler
    try:
        automation_scheduler.stop()
    except Exception as e:
        logger.error(f"Error stopping Automation Scheduler: {e}")


# ---------------------------------------------------------------------------
# OpenAPI tags — categorias de endpoints para documentação automática
# ---------------------------------------------------------------------------
_OPENAPI_TAGS = [
    {"name": "agents", "description": "Agentes ReAct de recrutamento (chat WebSocket, HITL, orquestrador)"},
    {"name": "candidates", "description": "Gestão de candidatos, busca RAG híbrida, TOON cards"},
    {"name": "jobs", "description": "Vagas, descrições de cargo, wizard, importação JD"},
    {"name": "rag-search", "description": "Busca semântica híbrida BM25 + pgvector (Sprint G6)"},
    {"name": "hitl", "description": "Human-in-the-Loop: aprovar/rejeitar ações de agentes"},
    {"name": "guardrails", "description": "Guardrails de agentes: CRUD + seed-defaults + toggle"},
    {"name": "pipeline", "description": "Pipeline de candidatos, stages, transições, kanban"},
    {"name": "sourcing", "description": "Busca ativa, boolean strings, abordagem WhatsApp"},
    {"name": "cv-screening", "description": "Triagem curricular, rubrica WSI, scores, red flags"},
    {"name": "compliance", "description": "LGPD, bias audit, fairness guard, DSR, consentimento"},
    {"name": "analytics", "description": "KPIs, funil, previsões ML, relatórios, model drift"},
    {"name": "communication", "description": "Email, WhatsApp, Teams, notificações, templates"},
    {"name": "scheduling", "description": "Agendamento de entrevistas, calendário, convites"},
    {"name": "auth", "description": "Autenticação, WorkOS SSO, permissões"},
    {"name": "admin", "description": "Administração, monitoramento, circuit breakers, tokens"},
    {"name": "health", "description": "Health check, observabilidade, métricas"},
    {"name": "toon", "description": "TOON cards — perfil visual de candidato por vaga (Sprint G7)"},
    {"name": "drift", "description": "Model drift detection e alertas automáticos"},
    {"name": "bias-audit", "description": "Auditoria de bias Four-Fifths Rule por vaga"},
    {"name": "wsi", "description": "WSI — entrevista estruturada por WhatsApp/voz"},
    {"name": "policy-engine", "description": "Motor de políticas de recrutamento por setor"},
    {"name": "short-lists", "description": "Short lists de candidatos por vaga (Sprint F4)"},
]

# Create FastAPI app
app = FastAPI(
    title="LIA Agent System — WeDOTalent",
    summary="Plataforma B2B SaaS de recrutamento inteligente com IA (LangGraph + Claude Sonnet 4.5)",
    description="""
## LIA — Learning Intelligence Assistant

API REST + WebSocket da plataforma de recrutamento inteligente **WeDOTalent**.

### Arquitetura
- **7 agentes ReAct** (LangGraph): Wizard, Pipeline, Sourcing, Talent, JobsManagement, Kanban, Policy
- **362 endpoints REST** + WebSocket chat
- **Multi-tenant**: `company_id` obrigatório em todos os recursos
- **Compliance**: LGPD, BCB 498, SOX, ISO 27001, EU AI Act

### Autenticação
Bearer token via WorkOS SSO:
```
Authorization: Bearer <token>
```

### Convenções
- Datas em ISO 8601 UTC (`2026-03-15T10:00:00Z`)
- UUIDs para todos os IDs
- Paginação: `?page=1&page_size=20`
- Multi-tenant: `?company_id=<uuid>` ou header `X-Company-ID`

### Links úteis
- [Documentação de referência](/docs/redoc)
- [OpenAPI JSON](/openapi.json)
    """,
    version="3.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
    openapi_tags=_OPENAPI_TAGS,
    contact={
        "name": "WeDOTalent Engineering",
        "url": "https://wedotalent.com",
        "email": "tech@wedotalent.com",
    },
    license_info={
        "name": "Proprietary — WeDOTalent",
        "url": "https://wedotalent.com/terms",
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/docs/redoc",
    redirect_slashes=False,
)

# Auth enforcement — validates JWT and injects company_id (multi-tenancy)
app.add_middleware(AuthEnforcementMiddleware)

# Response envelope — auto-wraps 2xx JSON into {"ok": true, "data": ...}
app.add_middleware(ResponseEnvelopeMiddleware)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS must be added AFTER RateLimitMiddleware so it executes BEFORE it
# (FastAPI processes add_middleware in reverse order).
# This ensures 429 responses include CORS headers for browser clients.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
app.add_middleware(RequestIdMiddleware)

# Structured logging — outermost so it captures final status code
app.add_middleware(StructuredLoggingMiddleware)

from fastapi import Request as FastAPIRequest
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# LIAError handler — unified error hierarchy (P35-060)
# ---------------------------------------------------------------------------
from app.shared.errors import LIAError, LIAComplianceError


from app.shared.compliance.scoring_safeguards import FairnessBlockedError


@app.exception_handler(FairnessBlockedError)
async def fairness_blocked_error_handler(request: FastAPIRequest, exc: FairnessBlockedError):
    """Fairness-block from candidate-scoring services. Returns 451 with controlled payload."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"FairnessGuard blocked scoring decision: category={exc.result.category} "
        f"blocked_terms={exc.result.blocked_terms} request_id={request_id}"
    )
    return JSONResponse(
        status_code=451,
        content={
            "error": {
                "code": "fairness_blocked",
                "message": exc.result.educational_message
                or "Solicitação bloqueada por verificação de fairness.",
                "category": exc.result.category,
                "request_id": request_id,
            }
        },
    )


@app.exception_handler(LIAComplianceError)
async def lia_compliance_error_handler(request: FastAPIRequest, exc: LIAComplianceError):
    """Compliance errors return 451 (Unavailable For Legal Reasons). Never silenced."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "LIAComplianceError: code=%s message=%s [request_id=%s]",
        exc.code, exc.message, request_id,
    )
    return JSONResponse(
        status_code=451,
        content={**exc.to_dict(), "request_id": request_id},
    )


@app.exception_handler(LIAError)
async def lia_error_handler(request: FastAPIRequest, exc: LIAError):
    """LIA platform errors return structured JSON with appropriate status code."""
    request_id = getattr(request.state, "request_id", "unknown")
    status = 400 if exc.recoverable else 500
    logger.warning(
        "LIAError: code=%s recoverable=%s [request_id=%s]",
        exc.code, exc.recoverable, request_id,
    )
    return JSONResponse(
        status_code=status,
        content={**exc.to_dict(), "request_id": request_id},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: FastAPIRequest, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    # 5xx: log real detail internally, never expose to client (OWASP A05)
    if exc.status_code >= 500:
        logger.error(
            "HTTP %d raised explicitly: %s [request_id=%s]",
            exc.status_code, exc.detail, request_id,
        )
    safe_message = exc.detail if exc.status_code < 500 else "Internal server error"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "message": safe_message,
            "request_id": request_id,
        }
    )


from app.domains.credits.services.token_budget_service import RequestBudgetExceededError


@app.exception_handler(RequestBudgetExceededError)
async def request_budget_exceeded_handler(request: FastAPIRequest, exc: RequestBudgetExceededError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "[RequestBudget] Request bloqueado por ceiling: "
        "company_id=%s agent_type=%s estimated=%d ceiling=%d plan=%s request_id=%s",
        exc.company_id, exc.agent_type, exc.estimated_tokens,
        exc.ceiling, exc.plan_code, request_id,
    )
    return JSONResponse(
        status_code=413,
        content={
            "error": "request_too_large",
            "message": (
                f"Request excede o limite de tokens por chamada "
                f"({exc.estimated_tokens:,} estimados / {exc.ceiling:,} permitidos). "
                "Reduza o tamanho do prompt ou contexto."
            ),
            "estimated_tokens": exc.estimated_tokens,
            "ceiling": exc.ceiling,
            "agent_type": exc.agent_type,
            "plan_code": exc.plan_code,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: FastAPIRequest, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "status_code": 500,
            "message": "Internal server error",
            "request_id": request_id,
        }
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_error_handler(request: FastAPIRequest, exc: PydanticValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "Pydantic validation error: %d errors on %s %s",
        len(exc.errors()), request.method, request.url.path,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "code": "VALIDATION_ERROR",
            "message": "Validation error",
            "errors": exc.errors(include_url=False),
            "request_id": request_id,
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: FastAPIRequest, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        "Request validation error: %d errors on %s %s",
        len(exc.errors()), request.method, request.url.path,
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "status_code": 422,
            "code": "REQUEST_VALIDATION_ERROR",
            "message": "Request validation failed",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


# Register all API routers
from app.api.routes import register_all_routes

register_all_routes(app)  # includes: admin_dlq_router, health, sourcing, etc.

# Serve Teams icons from the Next.js public folder (or a local fallback).
# Required so Teams can fetch color/outline icons when validating the app manifest.
try:
    import os as _os
    from fastapi.staticfiles import StaticFiles
    _teams_icons_candidates = [
        _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "plataforma-lia", "public", "teams-icons"),
        _os.path.join(_os.path.dirname(__file__), "static", "teams-icons"),
    ]
    for _icons_dir in _teams_icons_candidates:
        _icons_dir = _os.path.normpath(_icons_dir)
        if _os.path.isdir(_icons_dir):
            app.mount("/teams-icons", StaticFiles(directory=_icons_dir), name="teams-icons")
            logger.info(f"✅ Teams icons served at /teams-icons from {_icons_dir}")
            break
    else:
        logger.warning("⚠️  Teams icons directory not found — /teams-icons/ will return 404")
except Exception as _e:
    logger.warning(f"⚠️  Could not mount Teams icons static files: {_e}")


# Root-level health check redirects to comprehensive system health
from fastapi.responses import RedirectResponse


@app.get("/health")
async def app_health_check():
    """Root health check - redirects to comprehensive system health endpoint."""
    return RedirectResponse(url="/api/v1/health", status_code=307)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "message": "LIA Agent System API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
