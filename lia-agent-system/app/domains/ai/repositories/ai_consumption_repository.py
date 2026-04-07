"""
AiConsumption Repository — data access layer for AI token consumption tracking.
Extracted from app/api/v1/ai_consumption.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_consumption import AiConsumption

logger = logging.getLogger(__name__)


class AiConsumptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        conditions: list | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AiConsumption], int]:
        q = select(AiConsumption).where(AiConsumption.company_id == company_id)
        if conditions:
            q = q.where(and_(*conditions))
        q = q.order_by(AiConsumption.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(AiConsumption.id)).where(AiConsumption.company_id == company_id)
        if conditions:
            cq = cq.where(and_(*conditions))
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, record_id: UUID) -> AiConsumption | None:
        result = await self.db.execute(
            select(AiConsumption).where(AiConsumption.id == record_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> AiConsumption:
        rec = AiConsumption(**data)
        self.db.add(rec)
        await self.db.flush()
        await self.db.refresh(rec)
        return rec

    async def get_usage_summary(self, company_id: str, conditions: list | None = None) -> dict:
        base = select(func.sum(AiConsumption.tokens_used), func.count(AiConsumption.id)).where(
            AiConsumption.company_id == company_id
        )
        if conditions:
            base = base.where(and_(*conditions))
        row = (await self.db.execute(base)).one()
        return {"total_tokens": row[0] or 0, "total_calls": row[1] or 0}
