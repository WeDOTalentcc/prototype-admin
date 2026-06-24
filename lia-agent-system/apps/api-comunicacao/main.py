"""
api-comunicacao — Micro-app de comunicação outbound da LIA.

Domínio: Email, WhatsApp, Voz (Twilio/Gemini), Multi-canal,
         Digest, Notificações, Alertas, Webhooks.
Porta padrão: 8004

Scaling: alto volume, async-heavy, dependências externas
         (Twilio, Mailgun, WhatsApp Business API).
LGPD: todo envio outbound requer consent gate via ConsentCheckerService.
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
    logger.info("Starting api-comunicacao...")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    logger.info("api-comunicacao ready!")
    yield
    logger.info("Shutting down api-comunicacao...")


app = FastAPI(
    title="LIA api-comunicacao",
    description="Comunicação outbound: email, WhatsApp, voz, notificações, alertas",
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


# --- Routers do domínio Comunicação ---
from app.api.v1 import (
    system_health,
    # Comunicação geral
    communication,
    communications,
    communication_settings,
    communication_matrix,
    communication_optout,
    # Email
    email,
    email_templates,
    email_tracking,
    # WhatsApp
    whatsapp,
    whatsapp_webhook,
    # Voz
    voice,
    lia_voice,
    twilio_voice,
    gemini_voice,
    voice_stream,
    voice_screening,
    # Multi-canal
    multi_channel,
    # Digest
    digest,
    digest_schedule,
    # Notificações
    notifications,
    # Alertas
    alerts,
    alert_rule_templates,
    # Conversas
    conversations,
    # Webhooks de comunicação externos
    mailgun_webhooks,
    openmic_webhook,
)

app.include_router(system_health.router, prefix="/api/v1")
# Comunicação geral
app.include_router(communication.router, prefix="/api/v1", tags=["communication"])
app.include_router(communications.router, prefix="/api/v1", tags=["communications"])
app.include_router(communication_settings.router, prefix="/api/v1", tags=["communication_settings"])
app.include_router(communication_matrix.router, prefix="/api/v1", tags=["communication_matrix"])
app.include_router(communication_optout.router, prefix="/api/v1", tags=["communication_optout"])
# Email
app.include_router(email.router, prefix="/api/v1", tags=["email"])
app.include_router(email_templates.router, prefix="/api/v1", tags=["email_templates"])
app.include_router(email_tracking.router, prefix="/api/v1", tags=["email_tracking"])
# WhatsApp
app.include_router(whatsapp.router, prefix="/api/v1", tags=["whatsapp"])
app.include_router(whatsapp_webhook.router, prefix="/api/v1", tags=["whatsapp_webhook"])
# Voz
app.include_router(voice.router, prefix="/api/v1", tags=["voice"])
app.include_router(lia_voice.router, prefix="/api/v1", tags=["lia_voice"])
app.include_router(twilio_voice.router, prefix="/api/v1", tags=["twilio_voice"])
app.include_router(gemini_voice.router, prefix="/api/v1", tags=["gemini_voice"])
app.include_router(voice_stream.router, prefix="/api/v1", tags=["voice_stream"])
app.include_router(voice_screening.router, prefix="/api/v1", tags=["voice_screening"])
# Multi-canal
app.include_router(multi_channel.router, prefix="/api/v1", tags=["multi_channel"])
# Digest
app.include_router(digest.router, prefix="/api/v1", tags=["digest"])
app.include_router(digest_schedule.router, prefix="/api/v1", tags=["digest_schedule"])
# Notificações
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])
# Alertas
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(alert_rule_templates.router, prefix="/api/v1", tags=["alert_rule_templates"])
# Conversas
app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])
# Webhooks externos de comunicação
app.include_router(mailgun_webhooks.router, prefix="/api/v1", tags=["mailgun_webhooks"])
app.include_router(openmic_webhook.router, prefix="/api/v1", tags=["openmic_webhook"])
