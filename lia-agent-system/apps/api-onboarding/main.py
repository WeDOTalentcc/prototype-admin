"""
api-onboarding — Micro-app de onboarding de empresas e configuração da LIA.

Domínio: Company setup, Auth/SSO, Integrações, Admin, Billing, Compliance.
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
    logger.info("Starting api-onboarding...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-onboarding ready!")
    yield
    logger.info("Shutting down api-onboarding...")


app = FastAPI(
    title="LIA api-onboarding",
    description="Onboarding de empresas, auth/SSO, integrações, admin e billing",
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


# --- Routers do domínio Onboarding ---
from app.api.v1 import (
    system_health,
    auth,
    workos,
    company,
    company_culture,
    company_benefits,
    workforce,
    goals,
    benefits,
    admin,
    admin_settings,
    admin_templates,
    settings_progress,
    integrations_hub,
    integrations,
    billing,
    clients,
    client_users,
    notifications,
    communication_settings,
    email_templates,
    default_templates,
    global_policies,
    lgpd_compliance,
    compliance_controls,
    trust_center,
    audit_logs,
    data_subject_requests,
    consent_management,
    data_request,
    microsoft_graph,
    merge_webhooks,
    external_webhooks,
    saas_metrics,
    ai_consumption,
    observability,
)
from app.api.v1.audit_timeline import router as audit_timeline_router
from app.api.v1.health_langgraph import router as health_langgraph_router

app.include_router(system_health.router, prefix="/api/v1")
app.include_router(health_langgraph_router, prefix="/api/v1")
app.include_router(audit_timeline_router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(workos.router, prefix="/api/v1", tags=["workos"])
app.include_router(company.router, prefix="/api/v1", tags=["company"])
app.include_router(company_culture.router, prefix="/api/v1", tags=["company-culture"])
app.include_router(company_benefits.router, prefix="/api/v1", tags=["company-benefits"])
app.include_router(workforce.router, prefix="/api/v1", tags=["workforce"])
app.include_router(goals.router, prefix="/api/v1", tags=["goals"])
app.include_router(benefits.router, prefix="/api/v1", tags=["benefits"])
app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
app.include_router(admin_settings.router, prefix="/api/v1", tags=["admin-settings"])
app.include_router(admin_templates.router, prefix="/api/v1", tags=["admin-templates"])
app.include_router(settings_progress.router, prefix="/api/v1", tags=["settings-progress"])
app.include_router(integrations_hub.router, prefix="/api/v1", tags=["integration-hub"])
app.include_router(integrations.router, prefix="/api/v1", tags=["integrations"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(clients.router, prefix="/api/v1", tags=["clients"])
app.include_router(client_users.router, prefix="/api/v1", tags=["client-users"])
app.include_router(client_users.invitation_router, prefix="/api/v1", tags=["invitations"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
app.include_router(communication_settings.router, prefix="/api/v1", tags=["company"])
app.include_router(email_templates.router, prefix="/api/v1", tags=["email-templates"])
app.include_router(default_templates.router, prefix="/api/v1", tags=["default-templates"])
app.include_router(global_policies.router, prefix="/api/v1", tags=["global-policies"])
app.include_router(lgpd_compliance.router, prefix="/api/v1", tags=["lgpd"])
app.include_router(compliance_controls.router, prefix="/api/v1", tags=["compliance"])
app.include_router(trust_center.router, prefix="/api/v1", tags=["trust-center"])
app.include_router(audit_logs.router, prefix="/api/v1", tags=["audit-logs"])
app.include_router(data_subject_requests.router, prefix="/api/v1", tags=["data-subject-requests"])
app.include_router(consent_management.router, prefix="/api/v1", tags=["consent-management"])
app.include_router(data_request.router, prefix="/api/v1", tags=["data-request"])
app.include_router(microsoft_graph.router, prefix="/api/v1", tags=["microsoft-graph"])
app.include_router(merge_webhooks.router, prefix="/api/v1", tags=["merge-webhooks"])
app.include_router(external_webhooks.router, prefix="/api/v1", tags=["external-webhooks"])
app.include_router(saas_metrics.router, prefix="/api/v1", tags=["saas-metrics"])
app.include_router(ai_consumption.router, prefix="/api/v1", tags=["ai-consumption"])
app.include_router(observability.router, prefix="/api/v1", tags=["observability"])
