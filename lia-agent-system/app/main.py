"""
LIA Agent System - Main FastAPI application.
"""
# === LLM Bootstrap: monkey-patch SDK constructors for PII + audit + tenant ===
# MUST be first import — before anything instantiates Anthropic/OpenAI/GenAI
from app.shared.llm_bootstrap import install_llm_guards
install_llm_guards()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

import sentry_sdk
from app.core.sentry import init_sentry

init_sentry()

from app.core.config import settings
from app.core.database import init_db
from app.domains.communication.services.communication_service import (
    PendingApproval, CommunicationLog, CandidateOptOut, CandidateQuarantine
)
from app.domains.cv_screening.services.personalized_feedback_service import PersonalizedFeedbackRecord
from app.api import orchestrator_routes
from app.services.llm import LLMService
from app.middleware.rate_limiter import RateLimitMiddleware, rate_limiter
from app.middleware.auth_enforcement import AuthEnforcementMiddleware
from app.api.v1.llm_config import router as llm_config_router
from app.middleware.request_id import RequestIdMiddleware
from app.core.logging_middleware import StructuredLoggingMiddleware
from app.domains.automation.services.automation_scheduler import automation_scheduler
from app.domains.automation.services.automation_handlers import register_all_handlers
from app.config.langsmith import configure_langsmith
from app.tools import initialize_tools
from app.services.embedding_cache_service import embedding_cache
from app.core.database import AsyncSessionLocal

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
    
    # Validate Pearch AI configuration
    pearch_api_key = os.getenv("PEARCH_API_KEY")
    if pearch_api_key:
        logger.info("✅ Pearch AI configured (candidate search in 190M+ profiles enabled)")
    else:
        logger.warning("⚠️  Pearch AI NOT configured (PEARCH_API_KEY missing)")
        logger.warning("   Candidate search features will not work until API key is added")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

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
        logger.error(f"❌ Automation Scheduler failed to start: {e}")
        logger.warning("   Scheduled automation jobs will not run until scheduler is fixed")
    
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

    # Seed PolicyEngine default rules (idempotente — skip-if-exists)
    try:
        from app.services.policy_engine_service import PolicyEngineService
        _pe_stats = await PolicyEngineService().load_default_rules()
        logger.info(
            f"✅ PolicyEngine rules seeded: "
            f"{_pe_stats[business_rules_created]} business, "
            f"{_pe_stats[rate_limit_rules_created]} rate-limit, "
            f"{_pe_stats[escalation_rules_created]} escalation criadas; "
            f"{_pe_stats[business_rules_skipped] + _pe_stats[rate_limit_rules_skipped] + _pe_stats[escalation_rules_skipped]} já existiam"
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
)

# Auth enforcement — validates JWT and injects company_id (multi-tenancy)
app.add_middleware(AuthEnforcementMiddleware)

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
register_all_routes(app)


# Root-level health check redirects to comprehensive system health
from fastapi.responses import RedirectResponse, Response as FastAPIResponse

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
