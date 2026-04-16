"""
WebhookRegistration Repository — data access layer for job status webhooks.
Extracted from app/api/v1/job_status_webhooks.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.webhook_registration import WebhookDeliveryLog, WebhookRegistration

logger = logging.getLogger(__name__)


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self, company_id: str, *, event_type: str | None = None, is_active: bool | None = None,
        limit: int = 50, offset: int = 0,
    ) -> tuple[list[WebhookRegistration], int]:
        q = select(WebhookRegistration).where(WebhookRegistration.company_id == company_id)
        if event_type:
            q = q.where(WebhookRegistration.event_types.contains([event_type]))
        if is_active is not None:
            q = q.where(WebhookRegistration.is_active == is_active)
        q = q.order_by(desc(WebhookRegistration.created_at)).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(WebhookRegistration.id)).where(
            WebhookRegistration.company_id == company_id
        )
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, webhook_id: UUID, company_id: str) -> WebhookRegistration | None:
        result = await self.db.execute(
            select(WebhookRegistration).where(
                WebhookRegistration.id == webhook_id,
                WebhookRegistration.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> WebhookRegistration:
        wh = WebhookRegistration(**data)
        self.db.add(wh)
        await self.db.flush()
        await self.db.refresh(wh)
        return wh

    async def update(self, webhook: WebhookRegistration, data: dict) -> WebhookRegistration:
        for key, value in data.items():
            setattr(webhook, key, value)
        await self.db.flush()
        await self.db.refresh(webhook)
        return webhook

    async def delete(self, webhook: WebhookRegistration) -> None:
        await self.db.delete(webhook)

    async def list_delivery_logs(
        self, webhook_id: UUID, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[WebhookDeliveryLog], int]:
        q = (
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.webhook_id == webhook_id)
            .order_by(desc(WebhookDeliveryLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(q)
        logs = list(result.scalars().all())

        cq = select(func.count(WebhookDeliveryLog.id)).where(
            WebhookDeliveryLog.webhook_id == webhook_id
        )
        total = (await self.db.execute(cq)).scalar() or 0
        return logs, total

    async def get_all_active_for_event(
        self, event_type: str, company_id: str | None = None
    ) -> list[WebhookRegistration]:
        q = select(WebhookRegistration).where(
            WebhookRegistration.is_active.is_(True),
            WebhookRegistration.event_types.contains([event_type]),
        )
        if company_id:
            q = q.where(WebhookRegistration.company_id == company_id)
        result = await self.db.execute(q)
        return list(result.scalars().all())
