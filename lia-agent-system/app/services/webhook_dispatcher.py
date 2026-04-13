"""
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
