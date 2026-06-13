"""
api-triagem — Micro-app de triagem de candidatos da LIA.

Domínio: Screening, WSI (text + async + voz), Big Five, CV Parser,
         Calibração, Elegibilidade, Portal do Candidato, Ações Afirmativas.
Porta padrão: 8003

PII WARNING: Este sub-app concentra o maior fluxo de PII de candidatos.
Todo endpoint que lê/escreve dados de candidato usa require_company_id do JWT.
Ver ADR-LGPD-001 e ADR-LGPD-002 em CLAUDE.md raiz.
"""
from contextlib import asynccontextmanager
import logging

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
    logger.info("Starting api-triagem...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-triagem ready!")
    yield
    logger.info("Shutting down api-triagem...")


app = FastAPI(
    title="LIA api-triagem",
    description="Triagem, WSI, Big Five, CV Parser, voz e calibração",
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


# --- Routers do domínio Triagem ---
from app.api.v1 import (
    system_health,
    triagem,
    screening,
    screening_questions,
    wsi_async,
    wsi_observability,
    wsi_question_adjust,
    wsi_questions,
    wsi_screening_pipeline_endpoint,
    cv_parser,
    big_five,
    voice_screening,
    calibration,
    calibration_dashboard_v2,
    eligibility_question_templates,
    candidate_portal,
    candidate_portal_explanation,
    applications,
    affirmative,
)
from app.api.v1 import wsi as wsi_v1  # MONOLITH-IMPORT: wsi package aggregates sub-routers (questions/evaluation/sessions/reports)
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.health_langgraph import router as health_langgraph_router

app.include_router(system_health.router, prefix="/api/v1")
app.include_router(health_langgraph_router, prefix="/api/v1")
app.include_router(audit_timeline_router, prefix="/api/v1")

# Triagem principal
app.include_router(triagem.router, prefix="/api/v1", tags=["triagem"])

# Screening
app.include_router(screening.router, prefix="/api/v1", tags=["screening"])
app.include_router(screening_questions.router, prefix="/api/v1", tags=["company-screening-questions"])

# WSI — pacote completo (questions/evaluation/sessions/reports)
app.include_router(wsi_v1.router, tags=["WSI Text Screening"])
# WSI — endpoints standalone adicionais
app.include_router(wsi_questions.router, prefix="/api/v1", tags=["wsi_questions"])
app.include_router(wsi_question_adjust.router, prefix="/api/v1", tags=["wsi_question_adjust"])
app.include_router(wsi_observability.router, prefix="/api/v1", tags=["wsi_observability"])
app.include_router(wsi_screening_pipeline_endpoint.router, prefix="/api/v1", tags=["wsi_pipeline"])
app.include_router(wsi_async.router, prefix="/api/v1", tags=["wsi_async"])

# CV e Big Five
app.include_router(cv_parser.router, prefix="/api/v1", tags=["cv-parser"])
app.include_router(big_five.router, prefix="/api/v1", tags=["big-five"])

# Triagem por voz
app.include_router(voice_screening.router, prefix="/api/v1", tags=["voice-screening"])

# Calibração
app.include_router(calibration.router, prefix="/api/v1", tags=["calibration"])
app.include_router(calibration_dashboard_v2.router, prefix="/api/v1", tags=["calibration-dashboard-v2"])

# Templates de perguntas de elegibilidade
app.include_router(eligibility_question_templates.router, prefix="/api/v1", tags=["eligibility-question-templates"])

# Portal do candidato
app.include_router(candidate_portal.router, prefix="/api/v1", tags=["candidate-portal"])
app.include_router(candidate_portal_explanation.router, prefix="/api/v1", tags=["candidate-portal-explanation"])

# Candidaturas
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])

# Ações afirmativas
app.include_router(affirmative.router, prefix="/api/v1", tags=["affirmative"])
