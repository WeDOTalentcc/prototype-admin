"""
api-agentes — Micro-app de Agent Studio, chat SSE, LLM e governança.

Domínio: Agent Studio, chat SSE, AI config, LLM config,
         digital twins, HITL, guardrails, custom agents.
Porta padrão: 8003
"""
from contextlib import asynccontextmanager
import logging
import os

import sentry_sdk
from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.sentry import init_sentry  # MONOLITH-IMPORT: needs lib extraction (no lia-config equiv yet)
init_sentry()

from lia_config import settings
from app.core.database import init_db  # MONOLITH-IMPORT: lia_config.database has get_db but not init_db
from app.core.logging_config import configure_logging  # MONOLITH-IMPORT: needs lib extraction (no lia-utils equiv yet)
from lia_pii import install_global_pii_masking
from app.config.langsmith import configure_langsmith  # MONOLITH-IMPORT: needs lib extraction
from app.middleware.rate_limiter import RateLimitMiddleware  # MONOLITH-IMPORT: needs lib extraction
from app.middleware.request_id import RequestIdMiddleware  # MONOLITH-IMPORT: needs lib extraction
from app.core.logging_middleware import StructuredLoggingMiddleware  # MONOLITH-IMPORT: needs lib extraction

configure_langsmith()
configure_logging()
install_global_pii_masking()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting api-agentes...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-agentes ready!")
    yield
    logger.info("Shutting down api-agentes...")


app = FastAPI(
    title="LIA api-agentes",
    description="Agent Studio, chat SSE, LLM config, digital twins, HITL e guardrails",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(StructuredLoggingMiddleware)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: FastAPIRequest, exc: StarletteHTTPException):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "status_code": exc.status_code, "message": exc.detail, "request_id": request_id},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: FastAPIRequest, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception: {exc}", exc_info=True, extra={"request_id": request_id})
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"error": True, "status_code": 500, "message": "Internal server error", "request_id": request_id},
    )


# --- Routers do domínio Agentes ---

# Chat SSE
from app.api.v1.agent_chat_sse import router as agent_chat_sse_router

# Agent deployments e memória
from app.api.v1.agent_deployments import router as agent_deployments_base_router
from app.api.v1.agent_deployments import target_router as agent_deployments_router
from app.api.v1.agent_memory import router as agent_memory_router

# Monitoramento e qualidade
from app.api.v1.agent_monitoring import router as agent_monitoring_router
from app.api.v1.agent_quality import router as agent_quality_router
from app.api.v1.agent_quality_dashboard import router as agent_quality_dashboard_router

# Agent Studio
from app.api.v1.agent_studio_channels import router as agent_studio_channels_router
from app.api.v1.agent_studio_quality import router as agent_studio_quality_router
from app.api.v1.agent_studio_triagem_invite import router as agent_studio_triagem_invite_router
from app.api.v1.agent_studio_voice import router as agent_studio_voice_router
from app.api.v1.agent_studio_whatsapp import router as agent_studio_whatsapp_router

# Templates de agente
from app.api.v1.agent_template_catalog import router as agent_template_catalog_router
from app.api.v1.agent_templates import router as agent_templates_router

# Governance
from app.api.v1.agent_approvals import agent_router as agent_approvals_custom_router
from app.api.v1.agent_approvals import approvals_router as agent_approvals_router
from app.api.v1.agent_explainability import router as agent_explainability_router

# AI config e métricas
from app.api.v1.ai_config import router as ai_config_router
from app.api.v1.ai_consumption import router as ai_consumption_router
from app.api.v1.ai_performance import router as ai_performance_router
from app.api.v1.ai_transparency import router as ai_transparency_router

# Custom agents (com marketplace)
from app.api.v1.custom_agents import router as custom_agents_router
from app.api.v1.custom_agents import marketplace_router as agent_marketplace_router
from app.api.v1.custom_agents import admin_marketplace_router as agent_admin_marketplace_router

# Digital Twins
from app.api.v1.digital_twins import router as digital_twins_router

# LLM config
from app.api.v1.llm_config import router as llm_config_router
from app.api.v1.internal_llm import router as internal_llm_router

# HITL e Guardrails
from app.api.v1.hitl import router as hitl_router
from app.api.v1.guardrails import router as guardrails_router

# --- Registro de routers ---

# Chat SSE
app.include_router(agent_chat_sse_router, prefix="/api/v1", tags=["chat-sse"])

# Agent deployments e memória
app.include_router(agent_deployments_base_router, prefix="/api/v1", tags=["agent_deployments"])
app.include_router(agent_deployments_router, prefix="/api/v1", tags=["agent_deployments"])
app.include_router(agent_memory_router, prefix="/api/v1", tags=["agent_memory"])

# Monitoramento e qualidade
app.include_router(agent_monitoring_router, prefix="/api/v1", tags=["agent_monitoring"])
app.include_router(agent_quality_router, prefix="/api/v1", tags=["agent_quality"])
app.include_router(agent_quality_dashboard_router, prefix="/api/v1", tags=["agent_quality_dashboard"])

# Agent Studio
app.include_router(agent_studio_channels_router, prefix="/api/v1", tags=["agent_studio_channels"])
app.include_router(agent_studio_quality_router, prefix="/api/v1", tags=["agent_studio_quality"])
app.include_router(agent_studio_triagem_invite_router, prefix="/api/v1", tags=["agent_studio_triagem_invite"])
app.include_router(agent_studio_voice_router, prefix="/api/v1", tags=["agent_studio_voice"])
app.include_router(agent_studio_whatsapp_router, prefix="/api/v1", tags=["agent_studio_whatsapp"])

# Templates de agente
app.include_router(agent_template_catalog_router, prefix="/api/v1", tags=["agent_template_catalog"])
app.include_router(agent_templates_router, prefix="/api/v1", tags=["agent_templates"])

# Governance
app.include_router(agent_approvals_custom_router, prefix="/api/v1", tags=["agent_approvals"])
app.include_router(agent_approvals_router, prefix="/api/v1", tags=["agent_approvals"])
app.include_router(agent_explainability_router, prefix="/api/v1", tags=["agent_explainability"])

# AI config e métricas
app.include_router(ai_config_router, prefix="/api/v1", tags=["ai_config"])
app.include_router(ai_consumption_router, prefix="/api/v1", tags=["ai_consumption"])
app.include_router(ai_performance_router, prefix="/api/v1", tags=["ai_performance"])
app.include_router(ai_transparency_router, prefix="/api/v1", tags=["ai_transparency"])

# Custom agents com marketplace
app.include_router(custom_agents_router, prefix="/api/v1", tags=["custom_agents"])
app.include_router(agent_marketplace_router, prefix="/api/v1", tags=["agent_marketplace"])
app.include_router(agent_admin_marketplace_router, prefix="/api/v1", tags=["agent_admin_marketplace"])

# Digital Twins
app.include_router(digital_twins_router, prefix="/api/v1", tags=["digital_twins"])

# LLM config
app.include_router(llm_config_router, prefix="/api/v1", tags=["llm_config"])
app.include_router(internal_llm_router, prefix="/api/v1", tags=["internal_llm"])

# HITL e Guardrails
app.include_router(hitl_router, prefix="/api/v1", tags=["hitl"])
app.include_router(guardrails_router, prefix="/api/v1", tags=["guardrails"])
