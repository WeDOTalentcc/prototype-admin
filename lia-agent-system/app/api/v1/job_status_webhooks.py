"""
Job Status Webhooks API endpoints.

Manages webhook registrations for job vacancy status change notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
import logging

from app.core.database import get_db
from app.models.webhook_registration import (
    WebhookRegistration,
    WebhookDeliveryLog,
    JOB_STATUS_WEBHOOK_EVENTS
)
from app.domains.job_management.services.job_status_webhook_service import job_status_webhook_service
from app.auth.dependencies import (
    get_current_user,
    get_current_active_user,
    get_user_company_id
)
from app.auth.models import User

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


class WebhookRegisterRequest(BaseModel):
    """Request to register a new webhook."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2000)
    event_types: List[str] = Field(default=["job.status_changed"])
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    retry_count: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=120)


class WebhookRegisterResponse(BaseModel):
    """Response after registering a webhook."""
    success: bool
    webhook_id: str
    name: str
    secret_key: str
    message: str


class WebhookResponse(BaseModel):
    """Webhook data response."""
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    url: str
    event_types: List[str]
    is_active: bool
    retry_count: int
    timeout_seconds: int
    last_triggered_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_failure_reason: Optional[str] = None
    total_triggers: int
    total_successes: int
    total_failures: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WebhookListResponse(BaseModel):
    """Response for listing webhooks."""
    success: bool
    webhooks: List[WebhookResponse]
    total: int


class WebhookUpdateRequest(BaseModel):
    """Request to update a webhook."""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    event_types: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    retry_count: Optional[int] = Field(default=None, ge=1, le=10)
    timeout_seconds: Optional[int] = Field(default=None, ge=5, le=120)


class WebhookTestResponse(BaseModel):
    """Response after testing a webhook."""
    success: bool
    status_code: Optional[int] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    message: str


class WebhookLogResponse(BaseModel):
    """Webhook delivery log entry."""
    id: str
    event_type: str
    status: str
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    attempt_number: int
    triggered_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None


class WebhookLogsResponse(BaseModel):
    """Response for webhook logs."""
    success: bool
    logs: List[WebhookLogResponse]
    total: int


class WebhookEventResponse(BaseModel):
    """Webhook event type info."""
    event: str
    description: str
    payload_example: Dict[str, Any]


@router.post("/register", response_model=WebhookRegisterResponse)
async def register_webhook(
    request: WebhookRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Register a new webhook for job status change notifications.
    
    The returned secret_key should be stored securely and used to verify
    webhook signatures using HMAC-SHA256.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        valid_events = [e["event"] for e in JOB_STATUS_WEBHOOK_EVENTS]
        for event in request.event_types:
            if event not in valid_events and event != "*":
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid event type: {event}. Valid events: {valid_events}"
                )
        
        secret_key = WebhookRegistration.generate_secret_key()
        
        webhook = WebhookRegistration(
            company_id=company_id,
            name=request.name,
            description=request.description,
            url=request.url,
            event_types=request.event_types,
            secret_key=secret_key,
            headers=request.headers or {},
            retry_count=request.retry_count,
            timeout_seconds=request.timeout_seconds,
            created_by=str(current_user.id),
            is_active=True
        )
        
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Webhook registered: {request.name} for company {company_id}")
        
        return WebhookRegisterResponse(
            success=True,
            webhook_id=str(webhook.id),
            name=webhook.name,
            secret_key=secret_key,
            message="Webhook registered successfully. Store the secret_key securely for signature verification."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    is_active: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all registered webhooks for the current company.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        conditions = [WebhookRegistration.company_id == company_id]
        
        if is_active is not None:
            conditions.append(WebhookRegistration.is_active == is_active)
        
        count_result = await db.execute(
            select(func.count(WebhookRegistration.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0
        
        result = await db.execute(
            select(WebhookRegistration)
            .where(and_(*conditions))
            .order_by(desc(WebhookRegistration.created_at))
            .limit(limit)
            .offset(offset)
        )
        webhooks = list(result.scalars())
        
        webhook_responses = []
        for w in webhooks:
            webhook_responses.append(WebhookResponse(
                id=str(w.id),
                company_id=w.company_id,
                name=w.name,
                description=w.description,
                url=w.url,
                event_types=w.event_types or [],
                is_active=w.is_active,
                retry_count=w.retry_count,
                timeout_seconds=w.timeout_seconds,
                last_triggered_at=w.last_triggered_at.isoformat() if w.last_triggered_at else None,
                last_success_at=w.last_success_at.isoformat() if w.last_success_at else None,
                last_failure_at=w.last_failure_at.isoformat() if w.last_failure_at else None,
                last_failure_reason=w.last_failure_reason,
                total_triggers=w.total_triggers,
                total_successes=w.total_successes,
                total_failures=w.total_failures,
                created_at=w.created_at.isoformat() if w.created_at else None,
                updated_at=w.updated_at.isoformat() if w.updated_at else None
            ))
        
        return WebhookListResponse(
            success=True,
            webhooks=webhook_responses,
            total=total
        )
        
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific webhook by ID.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(WebhookRegistration).where(
                and_(
                    WebhookRegistration.id == webhook_id,
                    WebhookRegistration.company_id == company_id
                )
            )
        )
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return WebhookResponse(
            id=str(webhook.id),
            company_id=webhook.company_id,
            name=webhook.name,
            description=webhook.description,
            url=webhook.url,
            event_types=webhook.event_types or [],
            is_active=webhook.is_active,
            retry_count=webhook.retry_count,
            timeout_seconds=webhook.timeout_seconds,
            last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
            last_success_at=webhook.last_success_at.isoformat() if webhook.last_success_at else None,
            last_failure_at=webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
            last_failure_reason=webhook.last_failure_reason,
            total_triggers=webhook.total_triggers,
            total_successes=webhook.total_successes,
            total_failures=webhook.total_failures,
            created_at=webhook.created_at.isoformat() if webhook.created_at else None,
            updated_at=webhook.updated_at.isoformat() if webhook.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    request: WebhookUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a webhook configuration.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(WebhookRegistration).where(
                and_(
                    WebhookRegistration.id == webhook_id,
                    WebhookRegistration.company_id == company_id
                )
            )
        )
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        if request.event_types:
            valid_events = [e["event"] for e in JOB_STATUS_WEBHOOK_EVENTS]
            for event in request.event_types:
                if event not in valid_events and event != "*":
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid event type: {event}. Valid events: {valid_events}"
                    )
        
        update_fields = request.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            if hasattr(webhook, field):
                setattr(webhook, field, value)
        
        webhook.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Webhook updated: {webhook_id}")
        
        return WebhookResponse(
            id=str(webhook.id),
            company_id=webhook.company_id,
            name=webhook.name,
            description=webhook.description,
            url=webhook.url,
            event_types=webhook.event_types or [],
            is_active=webhook.is_active,
            retry_count=webhook.retry_count,
            timeout_seconds=webhook.timeout_seconds,
            last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None,
            last_success_at=webhook.last_success_at.isoformat() if webhook.last_success_at else None,
            last_failure_at=webhook.last_failure_at.isoformat() if webhook.last_failure_at else None,
            last_failure_reason=webhook.last_failure_reason,
            total_triggers=webhook.total_triggers,
            total_successes=webhook.total_successes,
            total_failures=webhook.total_failures,
            created_at=webhook.created_at.isoformat() if webhook.created_at else None,
            updated_at=webhook.updated_at.isoformat() if webhook.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a webhook.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await db.execute(
            select(WebhookRegistration).where(
                and_(
                    WebhookRegistration.id == webhook_id,
                    WebhookRegistration.company_id == company_id
                )
            )
        )
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        await db.delete(webhook)
        await db.commit()
        
        logger.info(f"Webhook deleted: {webhook_id}")
        
        return {
            "success": True,
            "message": "Webhook deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a test payload to verify webhook configuration.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        result = await job_status_webhook_service.send_test_webhook(
            webhook_id=str(webhook_id),
            company_id=company_id,
            db=db
        )
        
        if result.get("success"):
            return WebhookTestResponse(
                success=True,
                status_code=result.get("status_code"),
                duration_ms=result.get("duration_ms"),
                error=None,
                message="Test webhook delivered successfully"
            )
        else:
            return WebhookTestResponse(
                success=False,
                status_code=result.get("status_code"),
                duration_ms=result.get("duration_ms"),
                error=result.get("error"),
                message=f"Test webhook failed: {result.get('error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}/logs", response_model=WebhookLogsResponse)
async def get_webhook_logs(
    webhook_id: UUID,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get delivery logs for a webhook.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        webhook_result = await db.execute(
            select(WebhookRegistration).where(
                and_(
                    WebhookRegistration.id == webhook_id,
                    WebhookRegistration.company_id == company_id
                )
            )
        )
        webhook = webhook_result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        conditions = [WebhookDeliveryLog.webhook_id == webhook_id]
        
        if status:
            conditions.append(WebhookDeliveryLog.status == status)
        
        count_result = await db.execute(
            select(func.count(WebhookDeliveryLog.id)).where(and_(*conditions))
        )
        total = count_result.scalar() or 0
        
        result = await db.execute(
            select(WebhookDeliveryLog)
            .where(and_(*conditions))
            .order_by(desc(WebhookDeliveryLog.triggered_at))
            .limit(limit)
            .offset(offset)
        )
        logs = list(result.scalars())
        
        log_responses = []
        for log in logs:
            log_responses.append(WebhookLogResponse(
                id=str(log.id),
                event_type=log.event_type,
                status=log.status,
                status_code=log.status_code,
                error_message=log.error_message,
                attempt_number=log.attempt_number,
                triggered_at=log.triggered_at.isoformat() if log.triggered_at else "",
                completed_at=log.completed_at.isoformat() if log.completed_at else None,
                duration_ms=log.duration_ms
            ))
        
        return WebhookLogsResponse(
            success=True,
            logs=log_responses,
            total=total
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/available", response_model=List[WebhookEventResponse])
async def get_available_events(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of available webhook event types.
    """
    events = await job_status_webhook_service.get_available_events()
    return [
        WebhookEventResponse(
            event=e["event"],
            description=e["description"],
            payload_example=e["payload_example"]
        )
        for e in events
    ]
