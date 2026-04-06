"""
Email Templates API endpoints for managing email communications.
"""
from uuid import UUID
import html
import logging
import re
import uuid as uuid_module
from datetime import datetime, timedelta
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.database import get_db
from app.core.template_channels import ALL_CHANNELS, CHANNEL_DESCRIPTIONS, CHANNEL_LABELS
from app.domains.communication.services.email_service import email_service
from app.domains.job_management.services.template_seeder import clone_templates_for_client as clone_for_client_service
from app.domains.job_management.services.template_seeder import seed_default_templates as seed_system_templates
from app.models.candidate import Candidate
from app.models.email_template import EmailLog, EmailTemplate
from app.schemas.email_template import (
    DefaultTemplatesResponse,
    EmailLogListResponse,
    EmailLogResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
    EmailSendRequest,
    EmailSendResponse,
    EmailTemplateCreate,
    EmailTemplateListResponse,
    EmailTemplateResponse,
    EmailTemplateUpdate,
    TemplateAdjustData,
    TemplateAdjustRequest,
    TemplateAdjustResponse,
    TemplateGenerateData,
    TemplateGenerateRequest,
    TemplateGenerateResponse,
    TemplatePreviewByIdData,
    TemplatePreviewByIdRequest,
    TemplatePreviewByIdResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-templates", tags=["email-templates"])

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
RATE_LIMIT_EMAILS_PER_MINUTE = 10


def validate_email_format(email: str) -> bool:
    """Validate email format using regex."""
    return bool(EMAIL_REGEX.match(email))


def sanitize_variable_value(value: str) -> str:
    """Sanitize template variable values to prevent XSS and injection attacks."""
    if not isinstance(value, str):
        return str(value)
    sanitized = html.escape(value)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'on\w+\s*=', '', sanitized, flags=re.IGNORECASE)
    return sanitized


def sanitize_variables(variables: dict[str, str]) -> dict[str, str]:
    """Sanitize all template variables."""
    return {key: sanitize_variable_value(value) for key, value in variables.items()}


async def check_email_rate_limit(db: AsyncSession, user_id: uuid_module.UUID) -> bool:
    """
    Check if user has exceeded email rate limit (10 emails per minute).
    Returns True if within limits, False if exceeded.
    """
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    result = await db.execute(
        select(func.count(EmailLog.id)).where(
            EmailLog.created_at >= one_minute_ago,
            EmailLog.created_by == str(user_id)
        )
    )
    recent_count = result.scalar() or 0
    
    return recent_count < RATE_LIMIT_EMAILS_PER_MINUTE


async def validate_recipient_is_known_candidate(db: AsyncSession, email: str) -> bool:
    """Validate that the recipient email belongs to a known candidate."""
    result = await db.execute(
        select(Candidate.id).where(
            Candidate.email == email,
            Candidate.is_active == True
        )
    )
    return result.scalar_one_or_none() is not None


@router.get("", response_model=EmailTemplateListResponse)
async def list_email_templates(
    category: str | None = Query(None, description="Filter by category"),
    channel: str | None = Query(None, description="Filter by channel: email or whatsapp"),
    situation: str | None = Query(None, description="Filter by situation/context"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    search: str | None = Query(None, description="Search in name and subject"),
    company_id: str | None = Query(None, description="Filter by company ID (includes system templates)"),
    visibility: str | None = Query(None, description="Filter by visibility: 'recruiter', 'admin', or 'all'"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List all email templates with optional filtering.
    If company_id is provided, returns templates for that company plus system templates (company_id IS NULL).
    If company_id is not provided, returns all templates (global admin behavior).
    
    Security: Visibility filter with safe default
    - If visibility is not specified (None), defaults to 'recruiter' (defense-in-depth)
    - 'recruiter': Returns templates with visibility in ('recruiter', 'all'), excludes bell/teams channels
    - 'admin': Returns templates with visibility in ('admin', 'all') - requires explicit specification
    """
    try:
        # SECURITY: Default visibility to 'recruiter' if not specified
        # This ensures that even if a client forgets to pass visibility,
        # they won't accidentally receive admin templates
        if visibility is None:
            visibility = "recruiter"
        
        query = select(EmailTemplate)
        
        if company_id:
            query = query.where(
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None)
                )
            )
        
        if visibility == "recruiter":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "recruiter",
                    EmailTemplate.visibility == "all"
                )
            )
            query = query.where(
                ~EmailTemplate.channel.in_(["bell", "teams"])
            )
        elif visibility == "admin":
            query = query.where(
                or_(
                    EmailTemplate.visibility == "admin",
                    EmailTemplate.visibility == "all"
                )
            )
        
        if category:
            query = query.where(EmailTemplate.category == category)
        
        if channel:
            query = query.where(EmailTemplate.channel == channel)
        
        if situation:
            query = query.where(EmailTemplate.situation == situation)
        
        if is_active is not None:
            query = query.where(EmailTemplate.is_active == is_active)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    EmailTemplate.name.ilike(search_term),
                    EmailTemplate.subject.ilike(search_term)
                )
            )
        
        count_query = select(EmailTemplate)
        if company_id:
            count_query = count_query.where(
                or_(
                    EmailTemplate.company_id == company_id,
                    EmailTemplate.company_id.is_(None)
                )
            )
        if visibility == "recruiter":
            count_query = count_query.where(
                or_(
                    EmailTemplate.visibility == "recruiter",
                    EmailTemplate.visibility == "all"
                )
            )
            count_query = count_query.where(
                ~EmailTemplate.channel.in_(["bell", "teams"])
            )
        elif visibility == "admin":
            count_query = count_query.where(
                or_(
                    EmailTemplate.visibility == "admin",
                    EmailTemplate.visibility == "all"
                )
            )
        if category:
            count_query = count_query.where(EmailTemplate.category == category)
        if channel:
            count_query = count_query.where(EmailTemplate.channel == channel)
        if situation:
            count_query = count_query.where(EmailTemplate.situation == situation)
        if is_active is not None:
            count_query = count_query.where(EmailTemplate.is_active == is_active)
        
        result = await db.execute(count_query)
        total = len(result.scalars().all())
        
        query = query.offset(skip).limit(limit).order_by(EmailTemplate.created_at.desc())
        result = await db.execute(query)
        templates = result.scalars().all()
        
        return EmailTemplateListResponse(
            total=total,
            items=[
                EmailTemplateResponse(
                    id=cast(uuid_module.UUID, t.id),
                    name=cast(str, t.name),
                    subject=cast(str | None, t.subject),
                    body_html=cast(str, t.body_html),
                    body_text=cast(str | None, t.body_text),
                    category=cast(str | None, t.category),
                    channel=cast(str, t.channel) if t.channel else "email",
                    situation=cast(str | None, t.situation),
                    trigger_type=cast(str | None, t.trigger_type) if t.trigger_type else "manual",
                    used_in=cast(list[str], t.used_in) if t.used_in else [],
                    priority=cast(str | None, t.priority) if t.priority else "medium",
                    variables=cast(list[str], t.variables) if t.variables else [],
                    is_active=cast(bool, t.is_active),
                    created_by=cast(str | None, t.created_by),
                    created_at=cast(datetime, t.created_at),
                    updated_at=cast(datetime, t.updated_at) if t.updated_at else cast(datetime, t.created_at)
                )
                for t in templates
            ]
        )
        
    except Exception as e:
        logger.error(f"Error listing email templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=EmailTemplateResponse)
async def get_email_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific email template by ID.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == uuid_module.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        return EmailTemplateResponse(
            id=cast(uuid_module.UUID, template.id),
            name=cast(str, template.name),
            subject=cast(str | None, template.subject),
            body_html=cast(str, template.body_html),
            body_text=cast(str | None, template.body_text),
            category=cast(str | None, template.category),
            channel=cast(str, template.channel) if template.channel else "email",
            situation=cast(str | None, template.situation),
            trigger_type=cast(str | None, template.trigger_type) if template.trigger_type else "manual",
            used_in=cast(list[str], template.used_in) if template.used_in else [],
            priority=cast(str | None, template.priority) if template.priority else "medium",
            variables=cast(list[str], template.variables) if template.variables else [],
            is_active=cast(bool, template.is_active),
            created_by=cast(str | None, template.created_by),
            created_at=cast(datetime, template.created_at),
            updated_at=cast(datetime, template.updated_at) if template.updated_at else cast(datetime, template.created_at)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=EmailTemplateResponse, status_code=201)
async def create_email_template(
    template_data: EmailTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new email template.
    """
    try:
        logger.info(f"Creating email template: {template_data.name}")
        
        detected_vars = email_service.extract_variables(
            (template_data.subject or "") + " " + template_data.body_html + " " + (template_data.body_text or "")
        )
        variables = list(set(template_data.variables + detected_vars))
        
        template = EmailTemplate(
            id=uuid_module.uuid4(),
            name=template_data.name,
            subject=template_data.subject,
            body_html=template_data.body_html,
            body_text=template_data.body_text,
            category=template_data.category,
            channel=template_data.channel,
            situation=template_data.situation,
            trigger_type=template_data.trigger_type,
            used_in=template_data.used_in,
            priority=template_data.priority,
            variables=variables,
            is_active=True,
            created_by=template_data.created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Email template created: {template.id}")
        
        return EmailTemplateResponse(
            id=cast(uuid_module.UUID, template.id),
            name=cast(str, template.name),
            subject=cast(str | None, template.subject),
            body_html=cast(str, template.body_html),
            body_text=cast(str | None, template.body_text),
            category=cast(str | None, template.category),
            channel=cast(str, template.channel) if template.channel else "email",
            situation=cast(str | None, template.situation),
            trigger_type=cast(str | None, template.trigger_type) if template.trigger_type else "manual",
            used_in=cast(list[str], template.used_in) if template.used_in else [],
            priority=cast(str | None, template.priority) if template.priority else "medium",
            variables=cast(list[str], template.variables) if template.variables else [],
            is_active=cast(bool, template.is_active),
            created_by=cast(str | None, template.created_by),
            created_at=cast(datetime, template.created_at),
            updated_at=cast(datetime, template.updated_at) if template.updated_at else datetime.utcnow()
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating email template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}", response_model=EmailTemplateResponse)
async def update_email_template(
    template_id: str,
    template_data: EmailTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing email template.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == uuid_module.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        update_data = template_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        if any(k in update_data for k in ['subject', 'body_html', 'body_text']):
            subject_str = cast(str | None, template.subject) or ""
            body_html_str = cast(str, template.body_html)
            body_text_str = cast(str | None, template.body_text) or ""
            detected_vars = email_service.extract_variables(
                subject_str + " " + body_html_str + " " + body_text_str
            )
            template.variables = list(set(detected_vars))  # type: ignore[assignment]
        
        template.updated_at = datetime.utcnow()  # type: ignore[assignment]
        
        await db.commit()
        await db.refresh(template)
        
        logger.info(f"Email template updated: {template_id}")
        
        return EmailTemplateResponse(
            id=cast(uuid_module.UUID, template.id),
            name=cast(str, template.name),
            subject=cast(str | None, template.subject),
            body_html=cast(str, template.body_html),
            body_text=cast(str | None, template.body_text),
            category=cast(str | None, template.category),
            channel=cast(str, template.channel) if template.channel else "email",
            situation=cast(str | None, template.situation),
            trigger_type=cast(str | None, template.trigger_type) if template.trigger_type else "manual",
            used_in=cast(list[str], template.used_in) if template.used_in else [],
            priority=cast(str | None, template.priority) if template.priority else "medium",
            variables=cast(list[str], template.variables) if template.variables else [],
            is_active=cast(bool, template.is_active),
            created_by=cast(str | None, template.created_by),
            created_at=cast(datetime, template.created_at),
            updated_at=cast(datetime, template.updated_at) if template.updated_at else datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating email template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}", response_model=None)
async def delete_email_template(
    template_id: str,
    hard_delete: bool = Query(False, description="If True, permanently delete. If False, soft delete (deactivate)."),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete an email template (soft delete by default).
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == uuid_module.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        if hard_delete:
            await db.delete(template)
            message = "Email template permanently deleted"
        else:
            template.is_active = False  # type: ignore[assignment]
            template.updated_at = datetime.utcnow()  # type: ignore[assignment]
            message = "Email template deactivated"
        
        await db.commit()
        
        logger.info(f"Email template {'deleted' if hard_delete else 'deactivated'}: {template_id}")
        
        return {"message": message, "id": template_id}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting email template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview", response_model=EmailPreviewResponse)
async def preview_email(
    request: EmailPreviewRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Preview an email with variables substituted.
    Can use an existing template or provide custom subject/body.
    """
    try:
        result = await email_service.preview_email(
            db=db,
            template_id=request.template_id,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            variables=request.variables
        )
        
        return EmailPreviewResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/preview", response_model=TemplatePreviewByIdResponse)
async def preview_template_by_id(
    template_id: str,
    request: TemplatePreviewByIdRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Preview a template by ID with variables substituted.
    
    Fetches the template by ID and replaces all {{variable}} placeholders
    with the provided values.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.id == uuid_module.UUID(template_id))
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        sanitized_variables = sanitize_variables(request.variables)
        
        subject = cast(str | None, template.subject) or ""
        body_html = cast(str, template.body_html)
        body_text = cast(str | None, template.body_text) or ""
        
        for var_name, var_value in sanitized_variables.items():
            placeholder = "{{" + var_name + "}}"
            subject = subject.replace(placeholder, var_value)
            body_html = body_html.replace(placeholder, var_value)
            body_text = body_text.replace(placeholder, var_value)
        
        return TemplatePreviewByIdResponse(
            success=True,
            data=TemplatePreviewByIdData(
                subject=subject,
                body_html=body_html,
                body_text=body_text if body_text else None
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{template_id}/send", response_model=EmailSendResponse)
async def send_email(
    template_id: str,
    request: EmailSendRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send an email using a template.
    
    Security features:
    - Requires authentication
    - Validates email format
    - Sanitizes template variables to prevent injection
    - Rate limited to 10 emails per minute per user
    - Validates recipient is a known candidate
    """
    try:
        if not validate_email_format(request.recipient_email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format for recipient_email"
            )
        
        if not await check_email_rate_limit(db, cast(uuid_module.UUID, current_user.id)):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_EMAILS_PER_MINUTE} emails per minute allowed."
            )
        
        is_known_candidate = await validate_recipient_is_known_candidate(db, request.recipient_email)
        if not is_known_candidate:
            raise HTTPException(
                status_code=400,
                detail="Recipient email must belong to a known active candidate in the system"
            )
        
        variables = sanitize_variables(request.variables.copy())
        if request.recipient_name and "candidate_name" not in variables:
            variables["candidate_name"] = sanitize_variable_value(request.recipient_name)
        
        logger.info(f"Email send using template {template_id}")
        
        email_log = await email_service.send_email(
            db=db,
            template_id=uuid_module.UUID(template_id),
            recipient_email=request.recipient_email,
            variables=variables,
            candidate_id=request.candidate_id,
            send_immediately=request.send_immediately,
            created_by=str(current_user.id),
            subject_override=request.subject_override,
            body_override=request.body_override
        )
        
        status_val = cast(str, email_log.status)
        return EmailSendResponse(
            success=status_val == "sent",
            email_log_id=cast(uuid_module.UUID, email_log.id),
            status=status_val,
            message=f"Email {'sent' if status_val == 'sent' else 'queued'} successfully" if status_val != "failed" else f"Failed: {email_log.error_message}",
            recipient_email=cast(str, email_log.recipient_email),
            subject=cast(str, email_log.subject)
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error sending email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs/all", response_model=EmailLogListResponse)
async def list_email_logs(
    template_id: str | None = Query(None, description="Filter by template ID"),
    candidate_id: str | None = Query(None, description="Filter by candidate ID"),
    status: str | None = Query(None, description="Filter by status: sent, failed, pending"),
    recipient_email: str | None = Query(None, description="Filter by recipient email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List email logs with optional filtering.
    """
    try:
        query = select(EmailLog)
        
        if template_id:
            query = query.where(EmailLog.template_id == uuid_module.UUID(template_id))
        
        if candidate_id:
            query = query.where(EmailLog.candidate_id == candidate_id)
        
        if status:
            query = query.where(EmailLog.status == status)
        
        if recipient_email:
            query = query.where(EmailLog.recipient_email.ilike(f"%{recipient_email}%"))
        
        count_result = await db.execute(query)
        total = len(count_result.scalars().all())
        
        query = query.offset(skip).limit(limit).order_by(EmailLog.created_at.desc())
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return EmailLogListResponse(
            total=total,
            items=[
                EmailLogResponse(
                    id=cast(uuid_module.UUID, log.id),
                    template_id=cast(uuid_module.UUID | None, log.template_id),
                    candidate_id=cast(str | None, log.candidate_id),
                    recipient_email=cast(str, log.recipient_email),
                    subject=cast(str, log.subject),
                    status=cast(str, log.status),
                    sent_at=cast(datetime | None, log.sent_at),
                    error_message=cast(str | None, log.error_message),
                    variables_used=cast(dict[str, Any], log.variables_used) if log.variables_used else {},
                    created_at=cast(datetime, log.created_at)
                )
                for log in logs
            ]
        )
        
    except Exception as e:
        logger.error(f"Error listing email logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-defaults", response_model=DefaultTemplatesResponse)
async def seed_default_templates(
    created_by: str = Query("system", description="User creating the templates"),
    db: AsyncSession = Depends(get_db)
):
    """
    Seed the database with default email templates.
    Only creates templates that don't already exist (by name).
    """
    try:
        created_templates = await email_service.seed_default_templates(db, created_by)
        
        return DefaultTemplatesResponse(
            created=len(created_templates),
            templates=[
                EmailTemplateResponse(
                    id=cast(uuid_module.UUID, t.id),
                    name=cast(str, t.name),
                    subject=cast(str | None, t.subject),
                    body_html=cast(str, t.body_html),
                    body_text=cast(str | None, t.body_text),
                    category=cast(str | None, t.category),
                    channel=cast(str, t.channel) if t.channel else "email",
                    situation=cast(str | None, t.situation),
                    variables=cast(list[str], t.variables) if t.variables else [],
                    is_active=cast(bool, t.is_active),
                    created_by=cast(str | None, t.created_by),
                    created_at=cast(datetime, t.created_at),
                    updated_at=cast(datetime, t.updated_at) if t.updated_at else cast(datetime, t.created_at)
                )
                for t in created_templates
            ],
            message=f"Created {len(created_templates)} default templates" if created_templates else "All default templates already exist"
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding default templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list", response_model=None)
async def list_categories():
    """
    List available email template categories, channels, and situations.
    """
    return {
        "categories": [
            {"value": "interview", "label": "Entrevistas", "description": "Templates para convites e lembretes de entrevista"},
            {"value": "rejection", "label": "Feedback Negativo", "description": "Templates para comunicar rejeições de forma humanizada"},
            {"value": "offer", "label": "Propostas", "description": "Templates para envio de ofertas de trabalho"},
            {"value": "followup", "label": "Acompanhamento", "description": "Templates para acompanhamento do processo seletivo"},
            {"value": "alerts", "label": "Alertas", "description": "Templates para alertas e notificações"},
            {"value": "reports", "label": "Relatórios", "description": "Templates para relatórios periódicos"},
            {"value": "workflow", "label": "Fluxos de Trabalho", "description": "Templates para aprovações e fluxos"},
            {"value": "integrations", "label": "Integrações", "description": "Templates para notificações de integração"},
            {"value": "billing", "label": "Faturamento", "description": "Templates para créditos e faturamento"},
            {"value": "jobs", "label": "Vagas", "description": "Templates sobre status de vagas"},
            {"value": "workforce", "label": "Workforce", "description": "Templates de planejamento de workforce"},
            {"value": "onboarding", "label": "Onboarding", "description": "Templates de boas-vindas"},
            {"value": "screening", "label": "Triagem", "description": "Templates de triagem de candidatos"},
            {"value": "briefings", "label": "Briefings", "description": "Templates de briefings diários"},
            {"value": "parecer", "label": "Pareceres", "description": "Templates de pareceres da LIA"},
        ],
        "channels": [
            {"value": channel, "label": CHANNEL_LABELS.get(channel, channel), "description": CHANNEL_DESCRIPTIONS.get(channel, "")}
            for channel in ALL_CHANNELS
        ],
        "situations": [
            {"value": "triagem", "label": "Triagem", "description": "Primeira abordagem e triagem inicial"},
            {"value": "wsi_screening", "label": "Triagem WSI", "description": "Avaliação prática Work Sample Interview"},
            {"value": "entrevista", "label": "Entrevista", "description": "Convites e lembretes de entrevista"},
            {"value": "agendamento", "label": "Agendamento", "description": "Confirmação e lembretes de agenda"},
            {"value": "follow_up", "label": "Follow-up", "description": "Acompanhamento do processo"},
            {"value": "rejeicao", "label": "Rejeição", "description": "Feedback negativo humanizado"},
            {"value": "proposta", "label": "Proposta", "description": "Envio de ofertas de trabalho"},
            {"value": "feedback", "label": "Feedback", "description": "Solicitação de feedback sobre o processo"},
            {"value": "goal_at_risk", "label": "Meta em Risco", "description": "Alerta de meta em risco"},
            {"value": "goal_missed", "label": "Meta Não Atingida", "description": "Notificação de meta não atingida"},
            {"value": "sla_violated", "label": "SLA Violado", "description": "Alerta de SLA violado"},
            {"value": "approval_pending", "label": "Aprovação Pendente", "description": "Solicitação de aprovação"},
            {"value": "offer_accepted", "label": "Proposta Aceita", "description": "Notificação de proposta aceita"},
            {"value": "offer_rejected", "label": "Proposta Recusada", "description": "Notificação de proposta recusada"},
            {"value": "screening_completed", "label": "Triagem Concluída", "description": "Notificação de triagem finalizada"},
            {"value": "daily_briefing", "label": "Briefing Diário", "description": "Briefing matinal"},
            {"value": "end_of_day_summary", "label": "Resumo de Fim de Dia", "description": "Resumo do dia de trabalho"},
        ]
    }


@router.post("/clone-for-client/{client_id}", response_model=None)
async def clone_templates_for_client(
    client_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Clone all system templates for a new client.
    
    Creates copies of all system templates (company_id=NULL, is_system_template=True)
    with the specified client_id and origin_template_id pointing to the original.
    """
    try:
        result = await clone_for_client_service(db, client_id)
        
        return {
            "success": True,
            "client_id": result["client_id"],
            "cloned_count": result["cloned_count"],
            "cloned_templates": result["cloned_templates"],
            "message": f"Successfully cloned {result['cloned_count']} templates for client {client_id}"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error cloning templates for client {client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/seed-system-templates", response_model=None)
async def seed_system_templates_endpoint(
    db: AsyncSession = Depends(get_db)
):
    """
    Seed all system default templates.
    
    Creates templates with company_id=NULL and is_system_template=True.
    Includes templates for all channels: email, bell, briefing, parecer, report.
    """
    try:
        result = await seed_system_templates(db)
        
        return {
            "success": True,
            "created": result["created"],
            "skipped": result["skipped"],
            "created_templates": result["created_templates"],
            "skipped_templates": result["skipped_templates"],
            "message": f"Created {result['created']} templates, skipped {result['skipped']} (already exist)"
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error seeding system templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=TemplateGenerateResponse)
async def generate_template_with_ai(
    request: TemplateGenerateRequest
):
    """
    Generate email template content using AI (Anthropic Claude).
    
    Uses the python_anthropic_ai_integrations to generate professional
    recruitment email templates in Portuguese (Brazilian).
    
    Template types supported:
    - initial_contact: First contact with candidate
    - screening_reminder: Reminder for screening process
    - offer_letter: Job offer communication
    - rejection: Polite rejection message
    - interview_invitation: Interview scheduling
    - follow_up: Process follow-up
    
    Context options:
    - job_title: Position title
    - company_name: Company name
    - tone: formal or casual
    - candidate_name: Candidate name (optional)
    - recruiter_name: Recruiter name (optional)
    """
    import os

    from anthropic import Anthropic
    
    try:
        AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
        AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        
        if not AI_INTEGRATIONS_ANTHROPIC_API_KEY or not AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
            raise HTTPException(
                status_code=500,
                detail="Anthropic AI integration not configured"
            )
        
        client = Anthropic(
            api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
            base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
        )
        
        template_type = request.template_type
        context = request.context
        language = request.language
        
        tone = context.get("tone", "formal")
        job_title = context.get("job_title", "{{job_title}}")
        company_name = context.get("company_name", "{{company_name}}")
        
        template_descriptions = {
            "initial_contact": "Primeiro contato com um candidato identificado para uma vaga",
            "screening_reminder": "Lembrete para o candidato completar a triagem ou avaliação",
            "offer_letter": "Carta de proposta de trabalho/oferta de emprego",
            "rejection": "Comunicação educada de que o candidato não foi selecionado",
            "interview_invitation": "Convite para entrevista com detalhes de agendamento",
            "follow_up": "Acompanhamento do processo seletivo"
        }
        
        template_desc = template_descriptions.get(
            template_type, 
            f"Email de recrutamento do tipo: {template_type}"
        )
        
        tone_instruction = (
            "Use um tom formal e profissional." if tone == "formal" 
            else "Use um tom casual e amigável, mas ainda profissional."
        )
        
        prompt = f"""Você é um especialista em comunicação corporativa de RH no Brasil.
Gere um template de email para recrutamento com as seguintes características:

**Tipo de template:** {template_desc}
**Tom:** {tone_instruction}
**Idioma:** Português Brasileiro ({language})
**Cargo mencionado:** {job_title}
**Empresa:** {company_name}

**Regras importantes:**
1. Use placeholders com duplas chaves para variáveis dinâmicas. Exemplos:
   - {{{{candidate_name}}}} para nome do candidato
   - {{{{job_title}}}} para título da vaga
   - {{{{company_name}}}} para nome da empresa
   - {{{{recruiter_name}}}} para nome do recrutador
   - {{{{interview_date}}}} para data da entrevista
   - {{{{interview_time}}}} para horário da entrevista
   - {{{{interview_link}}}} para link da entrevista
   - {{{{deadline}}}} para prazo
   
2. O conteúdo deve ser profissional e adequado para recrutamento no Brasil
3. Evite clichês e seja autêntico
4. Inclua uma saudação e despedida apropriadas

**Formato de resposta (JSON):**
{{
    "subject": "Assunto do email aqui",
    "body_html": "<p>Corpo do email em HTML aqui...</p>",
    "variables_used": ["{{{{candidate_name}}}}", "{{{{job_title}}}}"]
}}

Responda APENAS com o JSON, sem texto adicional."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        content_block = message.content[0]
        response_text = getattr(content_block, 'text', None)
        if response_text is None:
            raise HTTPException(
                status_code=500,
                detail="AI response did not contain expected text content"
            )
        response_text = response_text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        import json
        try:
            generated_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(e)}"
            )
        
        return TemplateGenerateResponse(
            success=True,
            data=TemplateGenerateData(
                subject=generated_data.get("subject", ""),
                body_html=generated_data.get("body_html", ""),
                variables_used=generated_data.get("variables_used", [])
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating template with AI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adjust", response_model=TemplateAdjustResponse)
async def adjust_template_with_ai(
    request: TemplateAdjustRequest
):
    """
    Adjust an existing email template using AI with a free-form prompt.
    
    This endpoint allows users to describe desired changes in natural language,
    and the AI will modify the template accordingly while preserving variables.
    
    Example prompts:
    - "Deixe o tom mais informal e amigável"
    - "Adicione uma seção sobre benefícios da empresa"
    - "Resuma o conteúdo para ficar mais direto"
    - "Traduza para inglês mantendo as variáveis"
    """
    import os

    from anthropic import Anthropic
    
    try:
        AI_INTEGRATIONS_ANTHROPIC_API_KEY = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
        AI_INTEGRATIONS_ANTHROPIC_BASE_URL = os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        
        if not AI_INTEGRATIONS_ANTHROPIC_API_KEY or not AI_INTEGRATIONS_ANTHROPIC_BASE_URL:
            raise HTTPException(
                status_code=500,
                detail="Anthropic AI integration not configured. Please configure the AI integration."
            )
        
        client = Anthropic(
            api_key=AI_INTEGRATIONS_ANTHROPIC_API_KEY,
            base_url=AI_INTEGRATIONS_ANTHROPIC_BASE_URL
        )
        
        channel_type = "WhatsApp" if request.channel == "whatsapp" else "email"
        
        prompt = f"""Você é um especialista em comunicação corporativa de RH no Brasil.

Você vai ajustar um template de {channel_type} de recrutamento seguindo as instruções do usuário.

**Template atual:**
{f"Assunto: {request.current_subject}" if request.current_subject else ""}
Corpo:
{request.current_body}

**Instrução do usuário:**
{request.prompt}

**Regras importantes:**
1. MANTENHA todas as variáveis com duplas chaves {{{{variavel}}}} intactas
2. Preserve a estrutura básica do template (saudação, corpo, despedida)
3. Aplique APENAS as alterações solicitadas pelo usuário
4. Mantenha o conteúdo profissional e adequado para recrutamento
5. Se for WhatsApp, use formatação compatível (negrito com *, emojis moderados)
6. Se for email, pode usar HTML básico

**Formato de resposta (JSON):**
{{
    "subject": "{request.current_subject if request.current_subject else 'null se não aplicável'}",
    "body": "Corpo ajustado aqui...",
    "changes_made": ["Alteração 1", "Alteração 2"]
}}

Responda APENAS com o JSON, sem texto adicional."""

        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        content_block = message.content[0]
        response_text = getattr(content_block, 'text', None)
        if response_text is None:
            raise HTTPException(
                status_code=500,
                detail="AI response did not contain expected text content"
            )
        response_text = response_text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        import json
        try:
            adjusted_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {response_text}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse AI response: {str(e)}"
            )
        
        subject = adjusted_data.get("subject")
        if subject == "null se não aplicável" or subject == "null":
            subject = None
        
        return TemplateAdjustResponse(
            success=True,
            data=TemplateAdjustData(
                subject=subject,
                body=adjusted_data.get("body", request.current_body),
                changes_made=adjusted_data.get("changes_made", [])
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adjusting template with AI: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
