"""
api-vagas — Micro-app de gerenciamento de vagas da LIA.

Domínio: Job Vacancies, JD Generation, WSI, Wizard.
Porta padrão: 8001
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
    logger.info("Starting api-vagas...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-vagas ready!")
    yield
    logger.info("Shutting down api-vagas...")


app = FastAPI(
    title="LIA api-vagas",
    description="Gerenciamento de vagas, JD generation, WSI e Wizard",
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


# --- Routers do domínio Vagas ---
from app.api.v1 import (
    system_health,
    job_vacancies,
    job_drafts,
    job_board,
    job_status_webhooks,
    job_analytics,
    job_learning,
    job_templates,
    job_embeddings,
    job_qualification,
    jobs_ws,
    jd_import,
    jd_generation,
    wizard_analytics,
    wizard_suggestions,
    wizard_smart_orchestrator,
    wsi_questions,
    wsi_question_adjust,
    wsi_observability,
    wsi_screening_pipeline_endpoint,
    orchestrated_job_chat,
    orchestrated_jobs_management,
    briefing,
    hiring_policy,
)
from app.api.v1 import wsi as wsi_v1
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.health_langgraph import router as health_langgraph_router

app.include_router(system_health.router, prefix="/api/v1")
app.include_router(health_langgraph_router, prefix="/api/v1")
app.include_router(audit_timeline_router, prefix="/api/v1")
app.include_router(job_vacancies.router, prefix="/api/v1", tags=["job_vacancies"])
app.include_router(job_vacancies.router_public, prefix="/api/v1/public-vacancies", tags=["public_vacancies"])
app.include_router(job_drafts.router, prefix="/api/v1", tags=["job_drafts"])
app.include_router(job_board.router, prefix="/api/v1", tags=["job_board"])
app.include_router(job_status_webhooks.router, prefix="/api/v1", tags=["job_status_webhooks"])
app.include_router(job_analytics.router, prefix="/api/v1", tags=["job_analytics"])
app.include_router(job_learning.router, prefix="/api/v1", tags=["job_learning"])
app.include_router(job_templates.router, prefix="/api/v1", tags=["job_templates"])
app.include_router(job_embeddings.router, prefix="/api/v1", tags=["job_embeddings"])
app.include_router(job_qualification.router, prefix="/api/v1", tags=["job_qualification"])
app.include_router(jobs_ws.router, prefix="/api/v1", tags=["jobs_ws"])
app.include_router(jd_import.router, prefix="/api/v1", tags=["jd_import"])
app.include_router(jd_generation.router, prefix="/api/v1", tags=["jd_generation"])
app.include_router(wizard_analytics.router, prefix="/api/v1", tags=["wizard_analytics"])
app.include_router(wizard_suggestions.router, prefix="/api/v1", tags=["wizard_suggestions"])
app.include_router(wizard_smart_orchestrator.router, prefix="/api/v1", tags=["wizard_smart_orchestrator"])
app.include_router(wsi_v1.router, tags=["wsi"])
app.include_router(wsi_questions.router, prefix="/api/v1", tags=["wsi_questions"])
app.include_router(wsi_question_adjust.router, prefix="/api/v1", tags=["wsi_question_adjust"])
app.include_router(wsi_observability.router, prefix="/api/v1", tags=["wsi_observability"])
app.include_router(wsi_screening_pipeline_endpoint.router, prefix="/api/v1", tags=["wsi_pipeline"])
app.include_router(orchestrated_job_chat.router, prefix="/api/v1", tags=["orchestrated_job_chat"])
app.include_router(orchestrated_jobs_management.router, prefix="/api/v1", tags=["orchestrated_jobs_management"])
app.include_router(briefing.router, prefix="/api/v1", tags=["briefing"])
app.include_router(hiring_policy.router, prefix="/api/v1", tags=["hiring_policy"])
