#!/usr/bin/env python3
"""
P2.5b: External Webhooks for Studio Events

Allows clients to subscribe to Studio events (execution.completed, deployment.created,
approval.requested/reviewed) and receive HTTP POSTs with HMAC-signed payloads.

Components:
  1. Migration 074 + Webhook model (lia_models)
  2. Pydantic schemas
  3. WebhookDispatcher service + Celery task with HMAC + retry
  4. 5 endpoints: CRUD + test
  5. Hook into existing event publishers (execute, deployment, approvals)
  6. Frontend: Webhooks management UI in Configuracoes > Integracoes
"""
import os

BASE_BE = "/home/runner/workspace/lia-agent-system"
BASE_FE = "/home/runner/workspace/plataforma-lia/src"


def write_file(base, rel, content):
    full = os.path.join(base, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)
    print(f"  CREATED: {rel}")


def read_file(base, rel):
    with open(os.path.join(base, rel)) as f:
        return f.read()


def patch_file(base, rel, old, new, label=""):
    full = os.path.join(base, rel)
    content = read_file(base, rel)
    if old not in content:
        print(f"  SKIP: {label}")
        return False
    content = content.replace(old, new, 1)
    with open(full, "w") as f:
        f.write(content)
    print(f"  OK: {label}")
    return True


# ============================================================
# 1. Webhook model
# ============================================================
print("\n=== 1. Webhook model ===")
write_file(BASE_BE, "libs/models/lia_models/webhook.py", '''"""
Webhook — Subscriptions a eventos do Studio para integracoes externas.

Cada webhook subscreve a um conjunto de eventos. Quando um evento ocorre,
um POST e enviado ao URL com payload assinado via HMAC-SHA256.

Eventos suportados:
  - agent.execution.completed
  - agent.execution.failed
  - agent.deployment.created
  - agent.deployment.paused
  - agent.approval.requested
  - agent.approval.reviewed
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

from lia_config.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(64), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    url = Column(String(2048), nullable=False)
    events = Column(ARRAY(String), nullable=False)
    secret = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Stats
    total_deliveries = Column(Integer, default=0, nullable=False)
    total_failures = Column(Integer, default=0, nullable=False)
    last_delivery_at = Column(DateTime(timezone=True), nullable=True)
    last_status_code = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)

    # Audit
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self, include_secret: bool = False):
        result = {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "url": self.url,
            "events": self.events or [],
            "is_active": self.is_active,
            "total_deliveries": self.total_deliveries,
            "total_failures": self.total_failures,
            "last_delivery_at": self.last_delivery_at.isoformat() if self.last_delivery_at else None,
            "last_status_code": self.last_status_code,
            "last_error": self.last_error,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_secret:
            result["secret"] = self.secret
        return result
''')

write_file(BASE_BE, "app/models/webhook.py", "from lia_models.webhook import *  # noqa: F401,F403\n")


# ============================================================
# 2. Migration 074
# ============================================================
print("\n=== 2. Migration 074 ===")
write_file(BASE_BE, "alembic/versions/074_webhooks.py", '''"""Create webhooks table.

Revision ID: 074_webhooks
Revises: 073_agent_version_snapshots
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

revision = "074_webhooks"
down_revision = "073_agent_version_snapshots"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "webhooks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("company_id", sa.String(64), nullable=False, index=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("events", ARRAY(sa.String()), nullable=False),
        sa.Column("secret", sa.String(256), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("total_deliveries", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status_code", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("webhooks")
''')


# ============================================================
# 3. Schemas
# ============================================================
print("\n=== 3. Schemas ===")
write_file(BASE_BE, "app/schemas/webhook.py", '''"""Pydantic schemas for webhook management."""
from typing import Optional

from pydantic import BaseModel, Field, validator


ALLOWED_EVENTS = [
    "agent.execution.completed",
    "agent.execution.failed",
    "agent.deployment.created",
    "agent.deployment.paused",
    "agent.approval.requested",
    "agent.approval.reviewed",
]


class CreateWebhookRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    url: str = Field(..., min_length=10, max_length=2048)
    events: list[str] = Field(..., min_length=1)

    @validator("url")
    def validate_url(cls, v):
        if not v.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return v

    @validator("events")
    def validate_events(cls, v):
        invalid = [e for e in v if e not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}. Allowed: {ALLOWED_EVENTS}")
        return list(set(v))  # dedupe


class UpdateWebhookRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=256)
    url: Optional[str] = Field(None, min_length=10, max_length=2048)
    events: Optional[list[str]] = None
    is_active: Optional[bool] = None

    @validator("url")
    def validate_url(cls, v):
        if v is not None and not v.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        return v

    @validator("events")
    def validate_events(cls, v):
        if v is None:
            return None
        invalid = [e for e in v if e not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(f"Invalid events: {invalid}")
        return list(set(v))


class WebhookResponse(BaseModel):
    id: str
    company_id: str
    name: str
    url: str
    events: list[str] = []
    is_active: bool
    total_deliveries: int = 0
    total_failures: int = 0
    last_delivery_at: Optional[str] = None
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None
    created_by: str = ""
    created_at: Optional[str] = None
    secret: Optional[str] = None  # only on create response


class WebhookListResponse(BaseModel):
    webhooks: list[WebhookResponse]
    total: int
''')


# ============================================================
# 4. Service + Celery task
# ============================================================
print("\n=== 4. WebhookDispatcher + Celery task ===")
write_file(BASE_BE, "app/services/webhook_dispatcher.py", '''"""
WebhookDispatcher — Async dispatch of Studio events to external webhooks.

Each delivery is queued as a Celery task with HMAC-SHA256 signing and
automatic retry on 4xx/5xx responses.

Flow:
  1. Studio event occurs (execute, deployment, approval)
  2. dispatch(company_id, event, payload) called
  3. Service finds active webhooks subscribed to event
  4. For each webhook, queues deliver_webhook Celery task
  5. Task POSTs payload with X-WeDO-Signature + X-WeDO-Event headers
  6. Updates webhook stats (total_deliveries, total_failures, last_*)
"""
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.webhook import Webhook

logger = logging.getLogger(__name__)

MAX_WEBHOOKS_PER_COMPANY = 10


def generate_secret() -> str:
    """Generate a cryptographically secure 64-char secret."""
    return secrets.token_urlsafe(48)[:64]


def sign_payload(secret: str, body: str) -> str:
    """Compute HMAC-SHA256 signature of body using secret."""
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()


class WebhookService:
    """CRUD operations for webhooks."""

    async def create(
        self,
        db: AsyncSession,
        company_id: str,
        created_by: str,
        data: dict,
    ) -> Webhook:
        # Check max per company
        existing_count = await db.scalar(
            select(Webhook).where(Webhook.company_id == company_id).with_only_columns(
                Webhook.id
            )
        )
        # Use count via subquery for accuracy
        from sqlalchemy import func as _func
        count = await db.scalar(
            select(_func.count(Webhook.id)).where(Webhook.company_id == company_id)
        )
        if (count or 0) >= MAX_WEBHOOKS_PER_COMPANY:
            raise ValueError(
                f"Maximum {MAX_WEBHOOKS_PER_COMPANY} webhooks per company exceeded"
            )

        webhook = Webhook(
            id=uuid4(),
            company_id=company_id,
            name=data["name"],
            url=data["url"],
            events=data["events"],
            secret=generate_secret(),
            created_by=created_by,
        )
        db.add(webhook)
        logger.info(
            "[Webhook] created: company=%s name=%s events=%s",
            company_id, data["name"], data["events"],
        )
        return webhook

    async def list_for_company(self, db: AsyncSession, company_id: str) -> list[Webhook]:
        result = await db.execute(
            select(Webhook).where(Webhook.company_id == company_id).order_by(
                Webhook.created_at.desc()
            )
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, webhook_id: str, company_id: str) -> Optional[Webhook]:
        result = await db.execute(
            select(Webhook).where(
                and_(Webhook.id == webhook_id, Webhook.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self, db: AsyncSession, webhook_id: str, company_id: str, data: dict
    ) -> Optional[Webhook]:
        webhook = await self.get(db, webhook_id, company_id)
        if not webhook:
            return None
        for k, v in data.items():
            if v is not None and hasattr(webhook, k):
                setattr(webhook, k, v)
        return webhook

    async def delete(self, db: AsyncSession, webhook_id: str, company_id: str) -> bool:
        webhook = await self.get(db, webhook_id, company_id)
        if not webhook:
            return False
        await db.delete(webhook)
        return True

    async def find_subscribers(
        self, db: AsyncSession, company_id: str, event: str
    ) -> list[Webhook]:
        """Find all active webhooks subscribed to an event for a company."""
        result = await db.execute(
            select(Webhook).where(
                and_(
                    Webhook.company_id == company_id,
                    Webhook.is_active == True,
                    Webhook.events.any(event),
                )
            )
        )
        return list(result.scalars().all())

    async def dispatch(
        self, db: AsyncSession, company_id: str, event: str, payload: dict
    ) -> int:
        """Dispatch event to all subscribed webhooks. Returns count of queued deliveries."""
        webhooks = await self.find_subscribers(db, company_id, event)
        queued = 0
        for wh in webhooks:
            try:
                # Lazy import to avoid circular dep
                from app.jobs.webhook_tasks import deliver_webhook_task
                deliver_webhook_task.delay(
                    webhook_id=str(wh.id),
                    url=wh.url,
                    secret=wh.secret,
                    event=event,
                    payload=payload,
                )
                queued += 1
            except Exception as exc:
                logger.warning("[Webhook] dispatch enqueue failed: %s", exc)
        if queued > 0:
            logger.info(
                "[Webhook] dispatched event=%s to %d webhook(s) for company=%s",
                event, queued, company_id,
            )
        return queued


webhook_service = WebhookService()
''')

# Celery task
write_file(BASE_BE, "app/jobs/webhook_tasks.py", '''"""
Celery tasks for webhook delivery.

deliver_webhook_task: posts payload to webhook URL with HMAC signature.
On 4xx/5xx, retries up to 3 times with exponential backoff.
"""
import asyncio
import json
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="webhooks.deliver",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 60s, then 120s, 240s
)
def deliver_webhook_task(
    self,
    webhook_id: str,
    url: str,
    secret: str,
    event: str,
    payload: dict,
):
    """Deliver a webhook payload with HMAC-SHA256 signature.

    Retries on 4xx/5xx (max 3 retries). Updates webhook stats after each attempt.
    """
    import requests
    from app.services.webhook_dispatcher import sign_payload

    body_dict = {
        "event": event,
        "data": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "delivery_id": self.request.id,
    }
    body = json.dumps(body_dict, sort_keys=True)
    signature = sign_payload(secret, body)

    headers = {
        "Content-Type": "application/json",
        "X-WeDO-Event": event,
        "X-WeDO-Signature": signature,
        "X-WeDO-Delivery-Id": str(self.request.id),
        "User-Agent": "WeDOTalent-Webhook/1.0",
    }

    error_msg = None
    status_code = None
    success = False

    try:
        response = requests.post(url, data=body, headers=headers, timeout=10)
        status_code = response.status_code
        if 200 <= status_code < 300:
            success = True
            logger.info(
                "[Webhook] delivered: webhook=%s event=%s status=%s",
                webhook_id, event, status_code,
            )
        else:
            error_msg = f"HTTP {status_code}: {response.text[:200]}"
            logger.warning(
                "[Webhook] delivery failed: webhook=%s event=%s status=%s",
                webhook_id, event, status_code,
            )
    except requests.RequestException as exc:
        error_msg = str(exc)[:500]
        logger.warning("[Webhook] delivery exception: webhook=%s err=%s", webhook_id, error_msg)

    # Update stats (best-effort, async)
    try:
        async def _update_stats():
            from lia_config.database import AsyncSessionLocal
            from sqlalchemy import select
            from lia_models.webhook import Webhook

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
                wh = result.scalar_one_or_none()
                if wh:
                    wh.total_deliveries = (wh.total_deliveries or 0) + 1
                    if not success:
                        wh.total_failures = (wh.total_failures or 0) + 1
                    wh.last_delivery_at = datetime.now(timezone.utc)
                    wh.last_status_code = status_code
                    wh.last_error = error_msg if not success else None
                    await db.commit()

        asyncio.run(_update_stats())
    except Exception as stats_exc:
        logger.warning("[Webhook] stats update failed: %s", stats_exc)

    # Retry on failure
    if not success:
        try:
            countdown = 60 * (2 ** self.request.retries)  # 60, 120, 240
            raise self.retry(countdown=countdown)
        except self.MaxRetriesExceededError:
            logger.error("[Webhook] max retries exceeded: webhook=%s", webhook_id)

    return {"success": success, "status_code": status_code, "error": error_msg}
''')


# ============================================================
# 5. Endpoints
# ============================================================
print("\n=== 5. Endpoints ===")
write_file(BASE_BE, "app/api/v1/webhooks.py", '''"""
REST API for webhook management.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.auth.models import UserRole
from app.core.database import get_db
from app.schemas.webhook import (
    ALLOWED_EVENTS,
    CreateWebhookRequest,
    UpdateWebhookRequest,
    WebhookListResponse,
    WebhookResponse,
)
from app.services.webhook_dispatcher import webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.get("/events", summary="List allowed webhook event types")
async def list_allowed_events():
    """Return the catalog of webhook event types clients can subscribe to."""
    return {"events": ALLOWED_EVENTS}


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    body: CreateWebhookRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
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
    except Exception as e:
        await db.rollback()
        logger.error("Error creating webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create webhook")


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """List all webhooks for the current company."""
    webhooks = await webhook_service.list_for_company(db, current_user.company_id)
    return WebhookListResponse(
        webhooks=[WebhookResponse(**w.to_dict()) for w in webhooks],
        total=len(webhooks),
    )


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    body: UpdateWebhookRequest,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
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
    webhook_id: str,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook subscription."""
    deleted = await webhook_service.delete(
        db=db, webhook_id=webhook_id, company_id=current_user.company_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.commit()


@router.post("/{webhook_id}/test", summary="Send test event to webhook")
async def test_webhook(
    webhook_id: str,
    current_user=Depends(require_role([UserRole.admin])),
    db: AsyncSession = Depends(get_db),
):
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
    except Exception as e:
        logger.error("Error queueing test webhook: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to queue test event")
''')


# ============================================================
# 6. Register router
# ============================================================
print("\n=== 6. Register router ===")
patch_file(
    BASE_BE,
    "app/api/routes.py",
    "from app.api.v1.agent_approvals import approvals_router as agent_approvals_approvals_router",
    "from app.api.v1.agent_approvals import approvals_router as agent_approvals_approvals_router\n"
    "from app.api.v1.webhooks import router as webhooks_router",
    "import webhooks router",
)

patch_file(
    BASE_BE,
    "app/api/routes.py",
    'app.include_router(agent_approvals_approvals_router, prefix="/api/v1")',
    'app.include_router(agent_approvals_approvals_router, prefix="/api/v1")\n'
    '    app.include_router(webhooks_router, prefix="/api/v1")',
    "register webhooks router",
)


# ============================================================
# 7. Hook dispatch in event publishers
# ============================================================
print("\n=== 7. Hook dispatch in event publishers ===")

# Hook in execute_custom_agent (after notification dispatch)
patch_file(
    BASE_BE,
    "app/api/v1/custom_agents.py",
    '''        # P2.5a: Internal notification (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            await studio_notification_service.notify_execution_completed(
                db=db,
                user_id=str(current_user.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                candidates_processed=1,
                execution_time_ms=elapsed_ms,
            )
            await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] execute notify failed: %s", _notif_err)''',
    '''        # P2.5a: Internal notification (non-blocking)
        try:
            from app.services.studio_notification_service import studio_notification_service
            await studio_notification_service.notify_execution_completed(
                db=db,
                user_id=str(current_user.id),
                agent_id=str(agent.id),
                agent_name=agent.name,
                candidates_processed=1,
                execution_time_ms=elapsed_ms,
            )
            await db.commit()
        except Exception as _notif_err:
            logger.warning("[StudioNotif] execute notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.execution.completed",
                payload={
                    "agent_id": str(agent.id),
                    "agent_name": agent.name,
                    "execution_time_ms": elapsed_ms,
                    "tokens_input": _meta.get("tokens_input", 0) if "_meta" in dir() else 0,
                    "tokens_output": _meta.get("tokens_output", 0) if "_meta" in dir() else 0,
                    "confidence": output.confidence,
                    "user_id": str(current_user.id),
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] execute dispatch failed: %s", _wh_err)''',
    "hook webhook dispatch on execute",
)

# Hook in deployment created
patch_file(
    BASE_BE,
    "app/api/v1/agent_deployments.py",
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] deployment notify failed: %s", _notif_err)

        return DeploymentResponse(**deployment.to_dict())''',
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] deployment notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.deployment.created",
                payload={
                    "deployment_id": str(deployment.id),
                    "agent_id": str(deployment.agent_id),
                    "target_type": deployment.target_type,
                    "target_id": str(deployment.target_id),
                    "target_name": deployment.target_name,
                    "trigger_mode": deployment.trigger_mode,
                    "user_id": str(current_user.id),
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] deployment dispatch failed: %s", _wh_err)

        return DeploymentResponse(**deployment.to_dict())''',
    "hook webhook dispatch on deployment created",
)

# Hook in approval requested
patch_file(
    BASE_BE,
    "app/api/v1/agent_approvals.py",
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval request notify failed: %s", _notif_err)

        return ApprovalResponse(**approval.to_dict())''',
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval request notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.approval.requested",
                payload={
                    "approval_id": str(approval.id),
                    "agent_id": str(approval.agent_id),
                    "requested_by": approval.requested_by,
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] approval request dispatch failed: %s", _wh_err)

        return ApprovalResponse(**approval.to_dict())''',
    "hook webhook dispatch on approval request",
)

# Hook in approval reviewed
patch_file(
    BASE_BE,
    "app/api/v1/agent_approvals.py",
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval review notify failed: %s", _notif_err)

        return ApprovalResponse(**approval.to_dict())''',
    '''        except Exception as _notif_err:
            logger.warning("[StudioNotif] approval review notify failed: %s", _notif_err)

        # P2.5b: External webhook dispatch (non-blocking)
        try:
            from app.services.webhook_dispatcher import webhook_service
            await webhook_service.dispatch(
                db=db,
                company_id=current_user.company_id,
                event="agent.approval.reviewed",
                payload={
                    "approval_id": str(approval.id),
                    "agent_id": str(approval.agent_id),
                    "action": body.action,
                    "reviewer_id": str(current_user.id),
                    "review_notes": body.notes,
                },
            )
        except Exception as _wh_err:
            logger.warning("[Webhook] approval review dispatch failed: %s", _wh_err)

        return ApprovalResponse(**approval.to_dict())''',
    "hook webhook dispatch on approval review",
)


# ============================================================
# 8. Frontend: types + hook + proxy + UI
# ============================================================
print("\n=== 8. Frontend ===")
write_file(BASE_FE, "components/pages-agent-studio/custom-agents/webhook-types.ts", '''/**
 * Webhook types — mirror backend schemas.
 */

export const WEBHOOK_EVENTS = [
  "agent.execution.completed",
  "agent.execution.failed",
  "agent.deployment.created",
  "agent.deployment.paused",
  "agent.approval.requested",
  "agent.approval.reviewed",
] as const

export type WebhookEvent = typeof WEBHOOK_EVENTS[number]

export interface Webhook {
  id: string
  company_id: string
  name: string
  url: string
  events: string[]
  is_active: boolean
  total_deliveries: number
  total_failures: number
  last_delivery_at: string | null
  last_status_code: number | null
  last_error: string | null
  created_by: string
  created_at: string | null
  secret?: string  // present only on create response
}
''')

write_file(BASE_FE, "hooks/agents/use-webhooks.ts", '''"use client"

import useSWR from "swr"
import type { Webhook } from "@/components/pages-agent-studio/custom-agents/webhook-types"

const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null
  const res = await fetch(url, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  if (!res.ok) throw new Error(`Failed: ${res.status}`)
  return res.json()
}

export function useWebhooks() {
  const { data, error, isLoading, mutate } = useSWR<{ webhooks: Webhook[]; total: number }>(
    "/api/backend-proxy/webhooks",
    fetcher,
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
  return {
    webhooks: data?.webhooks ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError: !!error,
    mutate,
  }
}
''')

patch_file(
    BASE_FE,
    "hooks/agents/index.ts",
    'export { useAgentVersions } from "./use-agent-versions"',
    'export { useAgentVersions } from "./use-agent-versions"\nexport { useWebhooks } from "./use-webhooks"',
    "export webhooks hook",
)

# Proxy routes
write_file(BASE_FE, "app/api/backend-proxy/webhooks/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function GET(req: NextRequest) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/webhooks`, { headers: getAuthHeaders(req) })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/webhooks`, {
      method: "POST", headers: getAuthHeaders(req), body,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')

write_file(BASE_FE, "app/api/backend-proxy/webhooks/[id]/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const body = await req.text()
    const res = await fetch(`${BACKEND_URL}/api/v1/webhooks/${id}`, {
      method: "PATCH", headers: getAuthHeaders(req), body,
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const res = await fetch(`${BACKEND_URL}/api/v1/webhooks/${id}`, {
      method: "DELETE", headers: getAuthHeaders(req),
    })
    return new NextResponse(null, { status: res.status })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')

write_file(BASE_FE, "app/api/backend-proxy/webhooks/[id]/test/route.ts", '''import { NextRequest, NextResponse } from "next/server"

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8001"

function getAuthHeaders(req: NextRequest): Record<string, string> {
  const headers: Record<string, string> = { "Content-Type": "application/json" }
  const auth = req.headers.get("authorization")
  if (auth) headers["Authorization"] = auth
  return headers
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params
    const res = await fetch(`${BACKEND_URL}/api/v1/webhooks/${id}/test`, {
      method: "POST", headers: getAuthHeaders(req),
    })
    return new NextResponse(await res.text(), { status: res.status, headers: { "Content-Type": "application/json" } })
  } catch {
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
''')


# ============================================================
# 9. Frontend: WebhooksManager component
# ============================================================
print("\n=== 9. WebhooksManager ===")
write_file(BASE_FE, "components/settings/WebhooksManager.tsx", '''"use client"

import React, { useState } from "react"
import { Webhook as WebhookIcon, Plus, Trash2, Send, Loader2, Copy, CheckCircle2, AlertCircle, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { textStyles, cardStyles, buttonStyles, badgeStyles } from "@/lib/design-tokens"
import { toast } from "@/lib/toast"
import { useWebhooks } from "@/hooks/agents"
import { WEBHOOK_EVENTS, type Webhook } from "@/components/pages-agent-studio/custom-agents/webhook-types"

const EVENT_LABELS: Record<string, string> = {
  "agent.execution.completed": "Execucao concluida",
  "agent.execution.failed": "Execucao falhou",
  "agent.deployment.created": "Vinculo criado",
  "agent.deployment.paused": "Vinculo pausado",
  "agent.approval.requested": "Aprovacao solicitada",
  "agent.approval.reviewed": "Aprovacao revisada",
}

export function WebhooksManager() {
  const { webhooks, isLoading, mutate } = useWebhooks()
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState("")
  const [newUrl, setNewUrl] = useState("")
  const [newEvents, setNewEvents] = useState<string[]>([])
  const [submitting, setSubmitting] = useState(false)
  const [showSecret, setShowSecret] = useState<{ id: string; secret: string } | null>(null)
  const [testingId, setTestingId] = useState<string | null>(null)

  const handleCreate = async () => {
    if (!newName.trim() || !newUrl.trim() || newEvents.length === 0) return
    setSubmitting(true)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch("/api/backend-proxy/webhooks", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ name: newName, url: newUrl, events: newEvents }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Erro" }))
        throw new Error(err.detail || "Erro ao criar")
      }
      const created: Webhook = await res.json()
      toast.success(`Webhook "${newName}" criado!`, "Copie o secret abaixo (so e exibido uma vez)")
      if (created.secret) {
        setShowSecret({ id: created.id, secret: created.secret })
      }
      setCreating(false)
      setNewName("")
      setNewUrl("")
      setNewEvents([])
      mutate()
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Erro ao criar webhook")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Remover webhook "${name}"?`)) return
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/webhooks/${id}`, {
        method: "DELETE",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok && res.status !== 204) throw new Error("Erro")
      toast.success("Webhook removido")
      mutate()
    } catch {
      toast.error("Erro ao remover")
    }
  }

  const handleTest = async (id: string) => {
    setTestingId(id)
    try {
      const token = localStorage.getItem("auth_token")
      const res = await fetch(`/api/backend-proxy/webhooks/${id}/test`, {
        method: "POST",
        headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      })
      if (!res.ok) throw new Error("Erro")
      toast.success("Evento de teste enviado", "Verifique seu endpoint receptor")
      setTimeout(() => mutate(), 3000)
    } catch {
      toast.error("Erro ao enviar teste")
    } finally {
      setTestingId(null)
    }
  }

  const toggleEvent = (event: string) => {
    setNewEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event],
    )
  }

  const copySecret = async (secret: string) => {
    try {
      await navigator.clipboard.writeText(secret)
      toast.success("Secret copiado")
    } catch {
      toast.error("Erro ao copiar")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <WebhookIcon className="w-5 h-5 text-wedo-cyan-dark" />
          <h2 className={textStyles.title}>Webhooks externos</h2>
        </div>
        <Button onClick={() => setCreating(true)} className={buttonStyles.primary}>
          <Plus className="w-4 h-4 mr-1" /> Novo webhook
        </Button>
      </div>

      <p className={textStyles.description}>
        Receba eventos do Agent Studio em sistemas externos (Zapier, Slack, seu CRM).
        Cada delivery e assinada com HMAC-SHA256 via header X-WeDO-Signature.
      </p>

      {isLoading && (
        <div className="flex items-center gap-2 py-8 justify-center text-xs text-lia-text-disabled">
          <Loader2 className="w-3.5 h-3.5 animate-spin" /> Carregando webhooks...
        </div>
      )}

      {!isLoading && webhooks.length === 0 && (
        <Card className={cardStyles.default}>
          <CardContent className="py-8 text-center">
            <WebhookIcon className="w-10 h-10 text-lia-text-disabled mx-auto mb-2" />
            <p className={textStyles.subtitle}>Nenhum webhook configurado</p>
            <p className="text-xs text-lia-text-disabled mt-1">
              Crie um webhook para receber eventos dos seus agents em sistemas externos
            </p>
          </CardContent>
        </Card>
      )}

      <div className="space-y-2">
        {webhooks.map((wh) => (
          <Card key={wh.id} className={cardStyles.default}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-lia-text-primary">{wh.name}</span>
                    <Badge className={wh.is_active ? badgeStyles.success : badgeStyles.default}>
                      {wh.is_active ? "Ativo" : "Pausado"}
                    </Badge>
                    {wh.last_status_code && (
                      <Badge
                        className={
                          wh.last_status_code >= 200 && wh.last_status_code < 300
                            ? badgeStyles.success
                            : badgeStyles.error
                        }
                      >
                        Ultimo: {wh.last_status_code}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-lia-text-secondary truncate font-mono">{wh.url}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {wh.events.map((e) => (
                      <span key={e} className={cn(badgeStyles.default, "text-[10px]")}>
                        {EVENT_LABELS[e] || e}
                      </span>
                    ))}
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-[10px] text-lia-text-disabled">
                    <span>{wh.total_deliveries} entrega(s)</span>
                    {wh.total_failures > 0 && <span className="text-status-error">{wh.total_failures} falha(s)</span>}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleTest(wh.id)}
                    disabled={testingId === wh.id}
                  >
                    {testingId === wh.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(wh.id, wh.name)}>
                    <Trash2 className="w-3.5 h-3.5 text-status-error" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create dialog */}
      <Dialog open={creating} onOpenChange={(v) => !v && setCreating(false)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Novo webhook</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Nome</label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Ex: Slack notifications"
                className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">URL (HTTPS obrigatorio)</label>
              <input
                type="text"
                value={newUrl}
                onChange={(e) => setNewUrl(e.target.value)}
                placeholder="https://hooks.zapier.com/..."
                className="w-full border border-lia-border-subtle rounded-md px-3 py-2 text-sm bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-2 focus:ring-wedo-cyan/30 font-mono"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-2 block">Eventos</label>
              <div className="space-y-1.5">
                {WEBHOOK_EVENTS.map((event) => (
                  <label key={event} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newEvents.includes(event)}
                      onChange={() => toggleEvent(event)}
                      className="rounded"
                    />
                    <span className="text-lia-text-primary">{EVENT_LABELS[event]}</span>
                    <span className="text-lia-text-disabled font-mono text-[10px]">({event})</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setCreating(false)}>Cancelar</Button>
            <Button
              onClick={handleCreate}
              disabled={submitting || !newName || !newUrl || newEvents.length === 0}
              className={buttonStyles.primary}
            >
              {submitting ? "Criando..." : "Criar webhook"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show secret dialog (one-time display) */}
      <Dialog open={!!showSecret} onOpenChange={(v) => !v && setShowSecret(null)}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              Webhook criado!
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <div className={cn(cardStyles.flat, "p-3 border border-status-warning/30")}>
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-status-warning mt-0.5" />
                <div className="text-xs">
                  <p className="font-semibold text-lia-text-primary mb-1">Guarde este secret agora</p>
                  <p className="text-lia-text-secondary">
                    Por seguranca, ele NAO sera exibido novamente. Use para validar a assinatura HMAC-SHA256.
                  </p>
                </div>
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-lia-text-primary mb-1 block">Secret</label>
              <div className="flex gap-1">
                <input
                  type="text"
                  readOnly
                  value={showSecret?.secret || ""}
                  className="flex-1 border border-lia-border-subtle rounded-md px-3 py-2 text-xs bg-lia-bg-tertiary text-lia-text-primary font-mono"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => showSecret && copySecret(showSecret.secret)}
                >
                  <Copy className="w-3.5 h-3.5" />
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowSecret(null)} className={buttonStyles.primary}>
              Entendi
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
''')


# ============================================================
# 10. Wire into IntegrationsHub (existing settings)
# ============================================================
print("\n=== 10. Verify IntegrationsHub exists ===")
# Just verify the file exists for documentation
ihub = os.path.join(BASE_FE, "components/settings/IntegrationsHub.tsx")
if os.path.exists(ihub):
    print(f"  OK: IntegrationsHub exists at {ihub}")
    print("  NOTE: WebhooksManager NAO foi auto-wired no IntegrationsHub")
    print("        Pode ser renderizado standalone via /configuracoes/webhooks ou")
    print("        adicionado como tab/section dentro de IntegrationsHub manualmente")
else:
    print("  WARNING: IntegrationsHub not found")


# ============================================================
# VERIFY
# ============================================================
import ast
print("\n=== Verify ===")
for f in [
    "libs/models/lia_models/webhook.py",
    "app/schemas/webhook.py",
    "app/services/webhook_dispatcher.py",
    "app/jobs/webhook_tasks.py",
    "app/api/v1/webhooks.py",
    "app/api/routes.py",
    "app/api/v1/custom_agents.py",
    "app/api/v1/agent_deployments.py",
    "app/api/v1/agent_approvals.py",
    "alembic/versions/074_webhooks.py",
]:
    try:
        ast.parse(read_file(BASE_BE, f))
        print(f"  OK: {f}")
    except SyntaxError as e:
        print(f"  ERROR: {f}: {e}")

print("\nP2.5b Webhooks complete!")
