"""
api-funil — Micro-app de pipeline e funil de candidatos da LIA.

Domínio: Pipeline, Candidates, Applications, Sourcing, Kanban.
Porta padrão: 8002
"""
from contextlib import asynccontextmanager
import logging
import os

import sentry_sdk
from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from lia_config.sentry import init_sentry
init_sentry()

from lia_config import settings
from app.core.database import init_db  # ACCEPTED-MONOLITH: init_db orquestra 30+ migration helpers em database.py — extração deferida
from lia_config.logging_config import configure_logging
from lia_pii import install_global_pii_masking
from lia_config.langsmith import configure_langsmith
from lia_config.rate_limiter import RateLimitMiddleware
from lia_config.request_id import RequestIdMiddleware
from lia_config.logging_middleware import StructuredLoggingMiddleware

configure_langsmith()
configure_logging()
install_global_pii_masking()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting api-funil...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-funil ready!")
    yield
    logger.info("Shutting down api-funil...")


app = FastAPI(
    title="LIA api-funil",
    description="Pipeline, funil de candidatos, sourcing e kanban",
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


# --- Routers do domínio Funil ---
from app.api.v1 import (
    system_health,
    pipeline,
    pipeline_templates,
    pipeline_velocity,
    pipeline_prediction,
    candidates,
    candidate_search,
    candidate_lists,
    applications,
    sourcing,
    sourcing_pipeline,
    kanban_assistant,
    recruitment_stages,
    screening,
    screening_questions,
    talent_funnel,
    calibration,
    affirmative,
    early_warning,
    journey_intelligence,
    interview_analysis,
    interviews,
    cv_parser,
    bulk_actions,
    activities,
)
from app.api.v1.pipeline_policy import router as pipeline_policy_router
from app.api.v1.pipeline_orchestrator import router as pipeline_orchestrator_router
from app.api.v1.sourcing_orchestrator import router as sourcing_orchestrator_router
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.health_langgraph import router as health_langgraph_router
from app.api.v1 import stage_transition_automation, predictive_analytics

app.include_router(system_health.router, prefix="/api/v1")
app.include_router(health_langgraph_router, prefix="/api/v1")
app.include_router(audit_timeline_router, prefix="/api/v1")
app.include_router(pipeline.router, prefix="/api/v1/pipeline", tags=["pipeline"])
app.include_router(pipeline_templates.router, prefix="/api/v1", tags=["pipeline-templates"])
app.include_router(pipeline_velocity.router, prefix="/api/v1", tags=["pipeline-velocity"])
app.include_router(pipeline_prediction.router, prefix="/api/v1", tags=["pipeline-prediction"])
app.include_router(pipeline_policy_router, prefix="/api/v1", tags=["pipeline-policy"])
app.include_router(pipeline_orchestrator_router, prefix="/api/v1", tags=["pipeline-orchestrator"])
app.include_router(stage_transition_automation.router, prefix="/api/v1/stage-automation", tags=["stage-transition-automation"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(candidate_search.router, prefix="/api/v1", tags=["candidate-search"])
app.include_router(candidate_lists.router, prefix="/api/v1/candidate-lists", tags=["candidate-lists"])
app.include_router(applications.router, prefix="/api/v1", tags=["applications"])
app.include_router(sourcing.router, prefix="/api/v1", tags=["sourcing"])
app.include_router(sourcing_pipeline.router, prefix="/api/v1", tags=["sourcing-pipeline"])
app.include_router(sourcing_orchestrator_router, prefix="/api/v1", tags=["sourcing-orchestrator"])
app.include_router(kanban_assistant.router, prefix="/api/v1", tags=["kanban-assistant"])
app.include_router(recruitment_stages.router, prefix="/api/v1/recruitment-stages", tags=["recruitment-stages"])
app.include_router(recruitment_stages.screening_questions_router, prefix="/api/v1", tags=["screening-questions"])
app.include_router(screening.router, prefix="/api/v1", tags=["screening"])
app.include_router(screening_questions.router, prefix="/api/v1", tags=["company-screening-questions"])
app.include_router(talent_funnel.router, prefix="/api/v1", tags=["talent-funnel"])
app.include_router(calibration.router, prefix="/api/v1", tags=["calibration"])
app.include_router(affirmative.router, prefix="/api/v1", tags=["affirmative"])
app.include_router(early_warning.router, prefix="/api/v1", tags=["early-warning"])
app.include_router(journey_intelligence.router, prefix="/api/v1", tags=["journey-intelligence"])
app.include_router(predictive_analytics.router, prefix="/api/v1", tags=["predictive-analytics"])
app.include_router(interview_analysis.router, prefix="/api/v1", tags=["interview-analysis"])
app.include_router(interviews.router, prefix="/api/v1", tags=["interviews"])
app.include_router(cv_parser.router, prefix="/api/v1", tags=["cv-parser"])
app.include_router(bulk_actions.router, prefix="/api/v1", tags=["bulk-actions"])
app.include_router(activities.router, prefix="/api/v1", tags=["activities"])
