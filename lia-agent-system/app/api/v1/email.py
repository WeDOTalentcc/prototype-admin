"""
Email API endpoints for sending emails and viewing history.
Funcional - Aguardando Configuração SMTP/Calendar

This endpoint provides a simpler interface for email operations:
- Direct email sending (logged/simulated for now)
- Email history by candidate
- Ready for Mailgun/Resend integration
"""
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.domains.communication.dependencies import get_email_repo
from app.domains.communication.repositories.email_repository import EmailRepository
from app.shared.security.require_company_id import require_company_id
from app.shared.types import WeDoBaseModel
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


class DirectEmailRequest(WeDoBaseModel):
    """Request for sending a direct email (without template)."""
    recipient_email: EmailStr
    recipient_name: str | None = None
    subject: str
    body_html: str
    body_text: str | None = None
    candidate_id: str | None = None
    vacancy_id: str | None = None
    metadata: dict[str, Any] | None = None


class DirectEmailResponse(BaseModel):
    """Response after sending/queueing an email."""
    success: bool
    email_id: str
    status: str
    message: str
    recipient_email: str
    subject: str
    queued_at: datetime
    smtp_configured: bool = False


class EmailHistoryItem(BaseModel):
    """Single email history item."""
    id: str
    recipient_email: str
    subject: str
    status: str
    body_preview: str | None = None
    template_id: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    error_message: str | None = None


class EmailHistoryResponse(BaseModel):
    """Response for email history."""
    total: int
    candidate_id: str | None = None
    items: list[EmailHistoryItem]


@router.post("/send", response_model=DirectEmailResponse)
async def send_direct_email(
    request: DirectEmailRequest,
    repo: EmailRepository = Depends(get_email_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Send an email directly without using a template.

    Current Status: SIMULATED/LOGGED
    - Emails are stored in the database for audit trail
    - Actual sending requires Mailgun/Resend configuration
    - Status will be 'queued' until provider is configured

    Integration:
    - Mailgun API (primary)
    - Resend (automatic fallback via circuit breaker)
    - Amazon SES
    - Direct SMTP
    """
    try:
        if request.candidate_id:
            candidate = await repo.find_candidate_by_id(request.candidate_id)
            if not candidate:
                logger.warning(f"Candidate {request.candidate_id} not found, proceeding anyway")

        email_log = await repo.create_email_log(
            recipient_email=request.recipient_email,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            candidate_id=request.candidate_id,
            metadata=request.metadata,
        )

        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Email queued: {email_log.id} (recipient omitted - LGPD)")
        logger.info(f"   Subject: {request.subject}")
        logger.info("   Status: QUEUED (SMTP not configured - Funcional - Aguardando Configuracao SMTP)")

        return DirectEmailResponse(
            success=True,
            email_id=str(email_log.id),
            status="queued",
            message="Email enfileirado com sucesso. Aguardando configuracao SMTP para envio.",
            recipient_email=request.recipient_email,
            subject=request.subject,
            queued_at=email_log.created_at,
            smtp_configured=False,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history/{candidate_id}", response_model=EmailHistoryResponse)
async def get_email_history_by_candidate(
    candidate_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: EmailRepository = Depends(get_email_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get email history for a specific candidate.

    Returns all emails sent to this candidate, including:
    - Direct emails
    - Template-based emails
    - Status of each email
    """
    try:
        total, logs = await repo.get_logs_by_candidate(
            candidate_id=candidate_id,
            skip=skip,
            limit=limit,
        )

        items = []
        for log in logs:
            items.append(EmailHistoryItem(
                id=str(log.id),
                recipient_email=log.recipient_email,
                subject=log.subject,
                status=log.status,
                body_preview=repo.extract_body_preview(log),
                template_id=str(log.template_id) if log.template_id else None,
                sent_at=log.sent_at,
                created_at=log.created_at,
                error_message=log.error_message,
            ))

        return EmailHistoryResponse(
            total=total,
            candidate_id=candidate_id,
            items=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/history", response_model=EmailHistoryResponse)
async def get_all_email_history(
    recipient_email: str | None = Query(None, description="Filter by recipient email"),
    status: str | None = Query(None, description="Filter by status: queued, sent, failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: EmailRepository = Depends(get_email_repo),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get all email history with optional filters.
    """
    try:
        total, logs = await repo.get_all_logs(
            recipient_email=recipient_email,
            status=status,
            skip=skip,
            limit=limit,
        )

        items = []
        for log in logs:
            items.append(EmailHistoryItem(
                id=str(log.id),
                recipient_email=log.recipient_email,
                subject=log.subject,
                status=log.status,
                template_id=str(log.template_id) if log.template_id else None,
                sent_at=log.sent_at,
                created_at=log.created_at,
                error_message=log.error_message,
            ))

        return EmailHistoryResponse(
            total=total,
            items=items,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get email history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status", response_model=None)
async def get_email_system_status(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get the current status of the email system.

    Returns information about:
    - Whether SMTP is configured
    - Available email providers
    - Current mode (simulated/live)
    """
    import os

    smtp_host = os.getenv("SMTP_HOST")
    mailgun_key = os.getenv("MAILGUN_API_KEY")
    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    resend_key = os.getenv("RESEND_API_KEY")

    smtp_configured = bool(smtp_host)
    mailgun_configured = bool(mailgun_key) and bool(mailgun_domain)
    resend_configured = bool(resend_key)
    any_configured = smtp_configured or mailgun_configured or resend_configured

    return {
        "status": "Funcional - Aguardando Configuracao SMTP/Mailgun",
        "mode": "live" if any_configured else "simulated",
        "providers": {
            "smtp": {
                "configured": smtp_configured,
                "host": smtp_host if smtp_configured else None,
            },
            "mailgun": {
                "configured": mailgun_configured,
            },
            "resend": {
                "configured": resend_configured,
            },
        },
        "message": (
            "Sistema de email operacional. Emails sao armazenados no banco de dados."
            if any_configured else
            "Sistema de email em modo simulado. Configure SMTP_HOST, MAILGUN_API_KEY+MAILGUN_DOMAIN ou RESEND_API_KEY para habilitar envio real."
        ),
        "database_logging": True,
        "audit_trail": True,
    }

reorder_collection_before_item(router)
