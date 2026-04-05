"""
Webhooks API endpoints.

Provides CRUD operations for external webhook management.
"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl
import logging

from app.core.database import get_db
from app.domains.communication.services.webhook_service import webhook_service, WEBHOOK_EVENTS

logger = logging.getLogger(__name__)


def get_user_from_headers(
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID"),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role")
) -> Dict[str, Any]:
    """
    Get user context from request headers.
    Used for development and internal API calls.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company ID required. Please provide X-Company-ID header."
        )
    
    return {
        "company_id": x_company_id,
        "user_id": x_user_id or "system",
        "role": x_user_role or "user",
        "is_admin": x_user_role == "admin"
    }

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookCreate(BaseModel):
    """Request model for creating a webhook."""
    name: str
    description: Optional[str] = None
    url: str
    events: List[str]
    secret_key: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    retry_count: int = 3
    timeout_seconds: int = 30


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook."""
    name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout_seconds: Optional[int] = None


@router.get("")
async def list_webhooks(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    event: Optional[str] = Query(None, description="Filter by subscribed event"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    List all webhooks for the company.
    
    Returns webhooks with their configuration and statistics.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    result = await webhook_service.list_webhooks(
        company_id=company_id,
        is_active=is_active,
        event_filter=event,
        limit=limit,
        offset=offset,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.get("/events")
async def list_available_events():
    """
    List all available webhook events.
    
    Returns event types with descriptions and payload examples.
    """
    return {
        "events": webhook_service.get_available_events()
    }


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific webhook by ID.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    result = await webhook_service.get_webhook(
        webhook_id=webhook_id,
        company_id=company_id,
        db=db
    )
    
    if not result.get("success"):
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("")
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook.
    
    The webhook will be triggered when subscribed events occur.
    A secret key is generated if not provided for signing payloads.
    """
    company_id = current_user.get("company_id", "demo_company")
    user_id = current_user.get("id", current_user.get("user_id"))
    
    result = await webhook_service.register_webhook(
        company_id=company_id,
        name=webhook_data.name,
        url=webhook_data.url,
        events=webhook_data.events,
        description=webhook_data.description,
        secret_key=webhook_data.secret_key,
        headers=webhook_data.headers,
        retry_count=webhook_data.retry_count,
        timeout_seconds=webhook_data.timeout_seconds,
        created_by=user_id,
        db=db
    )
    
    if not result.get("success"):
        if "Invalid event" in result.get("error", ""):
            raise HTTPException(status_code=400, detail=result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    webhook_data: WebhookUpdate,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing webhook.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    updates = webhook_data.model_dump(exclude_none=True)
    
    result = await webhook_service.update_webhook(
        webhook_id=webhook_id,
        company_id=company_id,
        updates=updates,
        db=db
    )
    
    if not result.get("success"):
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a webhook.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    result = await webhook_service.delete_webhook(
        webhook_id=webhook_id,
        company_id=company_id,
        db=db
    )
    
    if not result.get("success"):
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result.get("error"))
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a test event to a webhook.
    
    This sends a test payload to verify the webhook endpoint is working correctly.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    result = await webhook_service.test_webhook(
        webhook_id=webhook_id,
        company_id=company_id,
        db=db
    )
    
    if not result.get("success"):
        if "not found" in result.get("error", "").lower():
            raise HTTPException(status_code=404, detail=result.get("error"))
    
    return result


@router.get("/{webhook_id}/logs")
async def get_webhook_logs(
    webhook_id: str,
    status: Optional[str] = Query(None, description="Filter by status (success, failed, pending)"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: Dict[str, Any] = Depends(get_user_from_headers),
    db: AsyncSession = Depends(get_db)
):
    """
    Get delivery logs for a webhook.
    
    Shows history of webhook delivery attempts with status and response details.
    """
    company_id = current_user.get("company_id", "demo_company")
    
    result = await webhook_service.get_webhook_logs(
        webhook_id=webhook_id,
        company_id=company_id,
        status_filter=status,
        limit=limit,
        offset=offset,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    
    return result
