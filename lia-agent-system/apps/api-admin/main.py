"""
api-admin — Micro-app de administração da plataforma WeDOTalent.

Domínio: Admin Platform, Billing, Compliance, Global Policies,
         WorkOS, SaaS Metrics, Trust Center, Incident Response.
Porta padrão: 8005

Acesso: APENAS wedotalent_admin. Jamais expor para roles de tenant.
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
    logger.info("Starting api-admin...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-admin ready!")
    yield
    logger.info("Shutting down api-admin...")


app = FastAPI(
    title="LIA api-admin",
    description="Administração da plataforma WeDOTalent: billing, compliance, global policies",
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


# --- Routers do domínio Admin ---
from app.api.v1 import (
    system_health,
    admin,
    admin_agents,
    admin_audit_decisions,
    admin_bias_audit,
    admin_circuit_breakers,
    admin_compliance_fairness,
    admin_consent,
    admin_dlq,
    admin_expurgo_audit,
    admin_external,
    admin_lgpd,
    admin_persona,
    admin_platform,
    admin_prompts,
    admin_settings,
    admin_templates,
    admin_token_budget,
    billing,
    credits,
    saas_metrics,
    upgrade_requests,
    trust_center,
    compliance_controls,
    compliance_report,
    compliance_status,
    workos,
    global_policies,
    policy_engine,
    incident_response,
)

app.include_router(system_health.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(admin_agents.router, prefix="/api/v1", tags=["admin_agents"])
app.include_router(admin_audit_decisions.router, prefix="/api/v1", tags=["admin_audit_decisions"])
app.include_router(admin_bias_audit.router, prefix="/api/v1", tags=["admin_bias_audit"])
app.include_router(admin_circuit_breakers.router, prefix="/api/v1", tags=["admin_circuit_breakers"])
app.include_router(admin_compliance_fairness.router, prefix="/api/v1", tags=["admin_compliance_fairness"])
app.include_router(admin_consent.router, prefix="/api/v1", tags=["admin_consent"])
app.include_router(admin_dlq.router, prefix="/api/v1", tags=["admin_dlq"])
app.include_router(admin_expurgo_audit.router, prefix="/api/v1", tags=["admin_expurgo_audit"])
app.include_router(admin_external.router, prefix="/api/v1", tags=["admin_external"])
app.include_router(admin_lgpd.router, prefix="/api/v1", tags=["admin_lgpd"])
app.include_router(admin_persona.router, prefix="/api/v1", tags=["admin_persona"])
app.include_router(admin_platform.router, prefix="/api/v1", tags=["admin_platform"])
app.include_router(admin_prompts.router, prefix="/api/v1", tags=["admin_prompts"])
app.include_router(admin_settings.router, prefix="/api/v1", tags=["admin_settings"])
app.include_router(admin_templates.router, prefix="/api/v1", tags=["admin_templates"])
app.include_router(admin_token_budget.router, prefix="/api/v1", tags=["admin_token_budget"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(credits.router, prefix="/api/v1", tags=["credits"])
app.include_router(saas_metrics.router, prefix="/api/v1", tags=["saas_metrics"])
app.include_router(upgrade_requests.router, prefix="/api/v1", tags=["upgrade_requests"])
app.include_router(trust_center.router, prefix="/api/v1", tags=["trust_center"])
app.include_router(compliance_controls.router, prefix="/api/v1", tags=["compliance_controls"])
app.include_router(compliance_report.router, prefix="/api/v1", tags=["compliance_report"])
app.include_router(compliance_status.router, prefix="/api/v1", tags=["compliance_status"])
app.include_router(workos.router, prefix="/api/v1", tags=["workos"])
app.include_router(global_policies.router, prefix="/api/v1", tags=["global_policies"])
app.include_router(policy_engine.router, prefix="/api/v1", tags=["policy_engine"])
app.include_router(incident_response.router, prefix="/api/v1", tags=["incident_response"])
