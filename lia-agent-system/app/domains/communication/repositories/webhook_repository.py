"""WebhookRepository — DB access for Webhook and WebhookLog records.

Extracted from app/domains/communication/services/webhook_service.py per ADR-001.
All queries scoped by company_id (multi-tenancy invariant).
"""
from __future__ import annotations

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.webhook import Webhook, WebhookLog


class WebhookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id_and_company(
        self,
        *,
        webhook_id: str,
        company_id: str,
    ) -> Webhook | None:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.id == webhook_id,
                    Webhook.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_for_company(
        self,
        *,
        company_id: str,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Webhook]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        conditions = [Webhook.company_id == company_id]
        if is_active is not None:
            conditions.append(Webhook.is_active == is_active)
        # TENANT-EXEMPT: dynamic builder — conditions seeded with
        # Webhook.company_id == company_id above. Sensor cannot trace company_id
        # through and_(*conditions) spread.
        result = await self.db.execute(
            select(Webhook)
            .where(and_(*conditions))
            .order_by(desc(Webhook.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def list_active_for_company(
        self,
        *,
        company_id: str,
    ) -> list[Webhook]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.company_id == company_id,
                    Webhook.is_active,
                )
            )
        )
        return list(result.scalars())

    async def list_logs_for_webhook(
        self,
        *,
        webhook_id: str,
        company_id: str,
        status_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WebhookLog]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        conditions = [
            WebhookLog.webhook_id == webhook_id,
            WebhookLog.company_id == company_id,
        ]
        if status_filter:
            conditions.append(WebhookLog.status == status_filter)
        # TENANT-EXEMPT: dynamic builder — conditions seeded with
        # WebhookLog.company_id == company_id above. Sensor cannot trace
        # company_id through and_(*conditions) spread.
        result = await self.db.execute(
            select(WebhookLog)
            .where(and_(*conditions))
            .order_by(desc(WebhookLog.triggered_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())
