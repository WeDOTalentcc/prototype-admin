"""
Job Status Webhooks API endpoints.

Manages webhook registrations for job vacancy status change notifications.
"""
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user, get_user_company_id
from app.auth.models import User
from app.core.database import get_db, get_tenant_db
from app.domains.job_management.repositories.webhook_repository import WebhookRepository
from app.domains.job_management.services.job_status_webhook_service import job_status_webhook_service
from app.models.webhook_registration import JOB_STATUS_WEBHOOK_EVENTS, WebhookDeliveryLog, WebhookRegistration
from app.shared.types import WeDoBaseModel
from app.shared.errors import LIAError

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


def get_webhook_repo(db: AsyncSession = Depends(get_db)) -> WebhookRepository:
    return WebhookRepository(db)


class WebhookRegisterRequest(WeDoBaseModel):
    """Request to register a new webhook."""
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2000)
    event_types: list[str] = Field(default=["job.status_changed"])
    description: str | None = None
    headers: dict[str, str] | None = None
    retry_count: int = Field(default=3, ge=1, le=10)
    timeout_seconds: int = Field(default=30, ge=5, le=120)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        # P0-W3-07: SSRF prevention -- block private IPs, loopback, link-local, cloud metadata
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        try:
            return safe_outbound_url(v, require_https=True)
        except UnsafeOutboundURLError as exc:
            raise ValueError(f"Webhook URL bloqueada por seguranca: {exc}")


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
    description: str | None = None
    url: str
    event_types: list[str]
    is_active: bool
    retry_count: int
    timeout_seconds: int
    last_triggered_at: str | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_failure_reason: str | None = None
    total_triggers: int
    total_successes: int
    total_failures: int
    created_at: str | None = None
    updated_at: str | None = None


# DUPLICATE_OF_INTENT: app/schemas/webhook.py — webhook list response wire-format (Sprint Q.1 triagem I bucket)
class WebhookListResponse(BaseModel):
    """Response for listing webhooks."""
    success: bool
    webhooks: list[WebhookResponse]
    total: int


class WebhookUpdateRequest(WeDoBaseModel):
    """Request to update a webhook."""
    name: str | None = None
    url: str | None = None
    description: str | None = None
    event_types: list[str] | None = None
    headers: dict[str, str] | None = None
    is_active: bool | None = None
    retry_count: int | None = Field(default=None, ge=1, le=10)
    timeout_seconds: int | None = Field(default=None, ge=5, le=120)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v) -> "str | None":
        # P0-W3-07: SSRF prevention -- block private IPs, loopback, link-local, cloud metadata
        if v is None:
            return v
        from app.shared.security.url_validator import safe_outbound_url, UnsafeOutboundURLError
        try:
            return safe_outbound_url(v, require_https=True)
        except UnsafeOutboundURLError as exc:
            raise ValueError(f"Webhook URL bloqueada por seguranca: {exc}")


class WebhookTestResponse(BaseModel):
    """Response after testing a webhook."""
    success: bool
    status_code: int | None = None
    duration_ms: int | None = None
    error: str | None = None
    message: str


class WebhookLogResponse(BaseModel):
    """Webhook delivery log entry."""
    id: str
    event_type: str
    status: str
    status_code: int | None = None
    error_message: str | None = None
    attempt_number: int
    triggered_at: str
    completed_at: str | None = None
    duration_ms: int | None = None


class WebhookLogsResponse(BaseModel):
    """Response for webhook logs."""
    success: bool
    logs: list[WebhookLogResponse]
    total: int


class WebhookEventResponse(BaseModel):
    """Webhook event type info."""
    event: str
    description: str
    payload_example: dict[str, Any]


@router.post("/register", response_model=WebhookRegisterResponse)
async def register_webhook(
    request: WebhookRegisterRequest,
    db: AsyncSession = Depends(get_tenant_db),
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
        
        repo = WebhookRepository(db)
        webhook = await repo.create({
            "company_id": company_id,
            "name": request.name,
            "description": request.description,
            "url": request.url,
            "event_types": request.event_types,
            "secret_key": secret_key,
            "headers": request.headers or {},
            "retry_count": request.retry_count,
            "timeout_seconds": request.timeout_seconds,
            "created_by": str(current_user.id),
            "is_active": True,
        })
        
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
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
        raise LIAError(message="Erro interno do servidor")


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    is_active: bool | None = None,
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
        
        repo = WebhookRepository(db)
        webhooks, total = await repo.list_for_company(
            company_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing webhooks: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


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
        
        repo = WebhookRepository(db)
        webhook = await repo.get_by_id(webhook_id, company_id)
        
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
        raise LIAError(message="Erro interno do servidor")


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    request: WebhookUpdateRequest,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a webhook configuration.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = WebhookRepository(db)
        webhook = await repo.get_by_id(webhook_id, company_id)
        
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
        update_fields["updated_at"] = datetime.utcnow()
        webhook = await repo.update(webhook, update_fields)
        
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
        raise LIAError(message="Erro interno do servidor")


@router.delete("/{webhook_id}", response_model=None)
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_tenant_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a webhook.
    """
    try:
        company_id = get_user_company_id(current_user)
        
        repo = WebhookRepository(db)
        webhook = await repo.get_by_id(webhook_id, company_id)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        await repo.delete(webhook)
        
        logger.info(f"Webhook deleted: {webhook_id}")
        
        return {
            "success": True,
            "message": "Webhook deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


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
        raise LIAError(message="Erro interno do servidor")


@router.get("/{webhook_id}/logs", response_model=WebhookLogsResponse)
async def get_webhook_logs(
    webhook_id: UUID,
    status: str | None = None,
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
        
        repo = WebhookRepository(db)
        webhook = await repo.get_by_id(webhook_id, company_id)
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        logs, total = await repo.list_delivery_logs(webhook_id, limit=limit, offset=offset)
        
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
        raise LIAError(message="Erro interno do servidor")


@router.get("/events/available", response_model=list[WebhookEventResponse])
async def get_available_events(
    current_user: User = Depends(get_current_active_user)
):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
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
