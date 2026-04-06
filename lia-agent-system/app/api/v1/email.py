"""
Email API endpoints for sending emails and viewing history.
Funcional - Aguardando Configuração SMTP/Calendar

This endpoint provides a simpler interface for email operations:
- Direct email sending (logged/simulated for now)
- Email history by candidate
- Ready for Mailgun/Resend integration
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime
import logging
import uuid

from app.core.database import get_db
from app.models.email_template import EmailLog
from app.models.candidate import Candidate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


class DirectEmailRequest(BaseModel):
    """Request for sending a direct email (without template)."""
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    candidate_id: Optional[str] = None
    vacancy_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


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
    body_preview: Optional[str] = None
    template_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None


class EmailHistoryResponse(BaseModel):
    """Response for email history."""
    total: int
    candidate_id: Optional[str] = None
    items: List[EmailHistoryItem]


@router.post("/send", response_model=DirectEmailResponse)
async def send_direct_email(
    request: DirectEmailRequest,
    db: AsyncSession = Depends(get_db)
):
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
            result = await db.execute(
                select(Candidate).where(Candidate.id == request.candidate_id)
            )
            candidate = result.scalar_one_or_none()
            if not candidate:
                logger.warning(f"Candidate {request.candidate_id} not found, proceeding anyway")
        
        email_log = EmailLog(
            id=uuid.uuid4(),
            template_id=None,
            candidate_id=request.candidate_id,
            recipient_email=request.recipient_email,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            status="queued",
            variables_used=request.metadata or {},
            created_at=datetime.utcnow(),
            created_by="api"
        )
        
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)
        
        logger.info(f"📧 Email queued: {email_log.id} (recipient omitted — LGPD)")
        logger.info(f"   Subject: {request.subject}")
        logger.info(f"   Status: QUEUED (SMTP not configured - Funcional - Aguardando Configuração SMTP)")
        
        return DirectEmailResponse(
            success=True,
            email_id=str(email_log.id),
            status="queued",
            message="Email enfileirado com sucesso. Aguardando configuração SMTP para envio.",
            recipient_email=request.recipient_email,
            subject=request.subject,
            queued_at=email_log.created_at,
            smtp_configured=False
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to queue email: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{candidate_id}", response_model=EmailHistoryResponse)
async def get_email_history_by_candidate(
    candidate_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get email history for a specific candidate.
    
    Returns all emails sent to this candidate, including:
    - Direct emails
    - Template-based emails
    - Status of each email
    """
    try:
        query = select(EmailLog).where(
            EmailLog.candidate_id == candidate_id
        ).order_by(desc(EmailLog.created_at))
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
        items = []
        for log in logs:
            body_preview = None
            if log.body_text:
                body_preview = log.body_text[:150] + "..." if len(log.body_text) > 150 else log.body_text
            elif log.body_html:
                import re
                text = re.sub(r'<[^>]+>', '', log.body_html)
                body_preview = text[:150] + "..." if len(text) > 150 else text
            
            items.append(EmailHistoryItem(
                id=str(log.id),
                recipient_email=log.recipient_email,
                subject=log.subject,
                status=log.status,
                body_preview=body_preview,
                template_id=str(log.template_id) if log.template_id else None,
                sent_at=log.sent_at,
                created_at=log.created_at,
                error_message=log.error_message
            ))
        
        return EmailHistoryResponse(
            total=total,
            candidate_id=candidate_id,
            items=items
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get email history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=EmailHistoryResponse)
async def get_all_email_history(
    recipient_email: Optional[str] = Query(None, description="Filter by recipient email"),
    status: Optional[str] = Query(None, description="Filter by status: queued, sent, failed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all email history with optional filters.
    """
    try:
        query = select(EmailLog)
        
        if recipient_email:
            query = query.where(EmailLog.recipient_email.ilike(f"%{recipient_email}%"))
        if status:
            query = query.where(EmailLog.status == status)
        
        query = query.order_by(desc(EmailLog.created_at))
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        logs = result.scalars().all()
        
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
                error_message=log.error_message
            ))
        
        return EmailHistoryResponse(
            total=total,
            items=items
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get email history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_email_system_status():
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
        "status": "Funcional - Aguardando Configuração SMTP/Mailgun",
        "mode": "live" if any_configured else "simulated",
        "providers": {
            "smtp": {
                "configured": smtp_configured,
                "host": smtp_host if smtp_configured else None
            },
            "mailgun": {
                "configured": mailgun_configured
            },
            "resend": {
                "configured": resend_configured
            }
        },
        "message": (
            "Sistema de email operacional. Emails são armazenados no banco de dados."
            if any_configured else
            "Sistema de email em modo simulado. Configure SMTP_HOST, MAILGUN_API_KEY+MAILGUN_DOMAIN ou RESEND_API_KEY para habilitar envio real."
        ),
        "database_logging": True,
        "audit_trail": True
    }
