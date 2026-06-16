"""
REST API for webhook management.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import UserRole
from app.core.database import get_db, get_tenant_db
from app.schemas.webhook import (
    ALLOWED_EVENTS,
    CreateWebhookRequest,
    UpdateWebhookRequest,
    WebhookListResponse,
    WebhookResponse,
)
from app.services.webhook_dispatcher import webhook_service
from app.shared.security.require_company_id import require_company_id
from typing import Annotated
from fastapi import Path
from app.api.v1._path_patterns import DUAL_ID_PATH_PATTERN, reorder_collection_before_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/events", summary="List allowed webhook event types")
async def list_allowed_events(company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """Return the catalog of webhook event types clients can subscribe to."""
    return {"events": ALLOWED_EVENTS}


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: CreateWebhookRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Create a new webhook subscription. Returns secret ONCE on creation."""
    try:
        webhook = await webhook_service.create(
            db=db,
            company_id=current_user.company_id,
            created_by=str(current_user.id),
            data=body.model_dump(),
        )
        await db.commit()
        # Include secret only on create
        return WebhookResponse(**webhook.to_dict(include_secret=True))
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error("Error creating webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create webhook")


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """List all webhooks for the current company."""
    webhooks = await webhook_service.list_for_company(db, current_user.company_id)
    return WebhookListResponse(
        webhooks=[WebhookResponse(**w.to_dict()) for w in webhooks],
        total=len(webhooks),
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    body: UpdateWebhookRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Update webhook (URL, events, active state)."""
    webhook = await webhook_service.update(
        db=db,
        webhook_id=webhook_id,
        company_id=current_user.company_id,
        data=body.model_dump(exclude_none=True),
    )
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()
    return WebhookResponse(**webhook.to_dict())


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_tenant_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Delete a webhook subscription."""
    deleted = await webhook_service.delete(
        db=db, webhook_id=webhook_id, company_id=current_user.company_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()


@router.post("/{webhook_id}/test", summary="Send test event to webhook")
async def test_webhook(
    webhook_id: Annotated[str, Path(pattern=DUAL_ID_PATH_PATTERN)],
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """Send a test event to verify webhook URL is reachable and responding."""
    webhook = await webhook_service.get(db, webhook_id, current_user.company_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    test_payload = {
        "test": True,
        "webhook_id": str(webhook.id),
        "company_id": current_user.company_id,
        "message": "This is a test event from WeDOTalent Studio webhooks",
    }

    try:
        from app.jobs.webhook_tasks import deliver_webhook_task
        deliver_webhook_task.delay(
            webhook_id=str(webhook.id),
            url=webhook.url,
            secret=webhook.secret,
            event="webhook.test",
            payload=test_payload,
        )
        return {"queued": True, "message": "Test event queued for delivery"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error queueing test webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue test event")

reorder_collection_before_item(router)
