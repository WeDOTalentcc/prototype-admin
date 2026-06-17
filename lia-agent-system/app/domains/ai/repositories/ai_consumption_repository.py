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

    async def get_by_id(
        self,
        record_id: UUID,
        company_id: str | None = None,
    ) -> AiConsumption | None:
        """Lookup AiConsumption por id.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        """
        # TENANT-EXEMPT: defense-in-depth — caller eh tenant-gated; company_id opcional desde Sprint B.1 tail
        if company_id is not None:
            result = await self.db.execute(
                select(AiConsumption).where(
                    AiConsumption.id == record_id,
                    AiConsumption.company_id == company_id,
                )
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller validates record.company_id post-fetch
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

    async def list_history(
        self,
        company_id: str,
        *,
        start_date=None,
        end_date=None,
        agent_type: str | None = None,
        model: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AiConsumption], int]:
        from uuid import UUID as _UUID
        from sqlalchemy import and_, desc
        company_uuid = _UUID(company_id) if isinstance(company_id, str) else company_id
        conditions = [AiConsumption.company_id == company_uuid]
        if start_date:
            conditions.append(AiConsumption.created_at >= start_date)
        if end_date:
            conditions.append(AiConsumption.created_at <= end_date)
        if agent_type:
            conditions.append(AiConsumption.agent_type == agent_type)
        if model:
            conditions.append(AiConsumption.model == model)

        # TENANT-EXEMPT: dynamic builder — conditions[0] is AiConsumption.company_id == company_uuid (L73 acima); sensor AST não traça dynamic conditions list
        q = (
            select(AiConsumption)
            .where(and_(*conditions))
            .order_by(desc(AiConsumption.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(q)
        records = list(result.scalars().all())

        cq = select(func.count(AiConsumption.id)).where(and_(*conditions))
        total = (await self.db.execute(cq)).scalar() or 0
        return records, total

    async def get_usage_by_agent(
        self,
        company_id: str,
        *,
        start_date=None,
        end_date=None,
        studio_agent_id: str | None = None,
    ) -> list:
        """Agrega consumo AI por agent_type.

        Wave 0 Fix 5 (2026-05-27): aceita studio_agent_id opcional pra filtrar
        consumo de **um agente individual** (Studio canonical), além do agregado
        por agent_type. Backward-compat: sem o param, comportamento original.
        """
        from uuid import UUID as _UUID
        from sqlalchemy import and_
        company_uuid = _UUID(company_id) if isinstance(company_id, str) else company_id
        conditions = [AiConsumption.company_id == company_uuid]
        if start_date:
            conditions.append(AiConsumption.created_at >= start_date)
        if end_date:
            conditions.append(AiConsumption.created_at <= end_date)
        if studio_agent_id:
            conditions.append(AiConsumption.studio_agent_id == studio_agent_id)

        q = (
            select(
                AiConsumption.agent_type,
                func.sum(AiConsumption.total_tokens).label("total_tokens"),
                func.count(AiConsumption.id).label("total_ops"),
                func.sum(AiConsumption.cost_cents).label("total_cost"),
            )
            .where(and_(*conditions))
            .group_by(AiConsumption.agent_type)
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_usage_by_day(
        self,
        company_id: str,
        *,
        days: int = 30,
    ) -> list:
        from uuid import UUID as _UUID
        from datetime import datetime, timedelta
        from sqlalchemy import Date, and_, cast as sa_cast
        company_uuid = _UUID(company_id) if isinstance(company_id, str) else company_id
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            AiConsumption.company_id == company_uuid,
            AiConsumption.created_at >= start_date,
        ]
        q = (
            select(
                sa_cast(AiConsumption.created_at, Date).label("date"),
                func.sum(AiConsumption.total_tokens).label("total_tokens"),
                func.count(AiConsumption.id).label("total_ops"),
                func.sum(AiConsumption.cost_cents).label("total_cost"),
            )
            .where(and_(*conditions))
            .group_by(sa_cast(AiConsumption.created_at, Date))
            .order_by(sa_cast(AiConsumption.created_at, Date))
        )
        result = await self.db.execute(q)
        return result.all()

    async def get_usage_by_agent_and_day(
        self,
        company_id: str,
        *,
        days: int = 30,
    ) -> list:
        from uuid import UUID as _UUID
        from datetime import datetime, timedelta
        from sqlalchemy import Date, and_, cast as sa_cast
        company_uuid = _UUID(company_id) if isinstance(company_id, str) else company_id
        start_date = datetime.now() - timedelta(days=days)
        conditions = [
            AiConsumption.company_id == company_uuid,
            AiConsumption.created_at >= start_date,
        ]
        q = (
            select(
                sa_cast(AiConsumption.created_at, Date).label("date"),
                AiConsumption.agent_type,
                func.sum(AiConsumption.total_tokens).label("total_tokens"),
                func.count(AiConsumption.id).label("total_ops"),
                func.sum(AiConsumption.cost_cents).label("total_cost"),
            )
            .where(and_(*conditions))
            .group_by(sa_cast(AiConsumption.created_at, Date), AiConsumption.agent_type)
            .order_by(sa_cast(AiConsumption.created_at, Date))
        )
        result = await self.db.execute(q)
        return result.all()

    async def record(self, data: dict) -> AiConsumption:
        rec = AiConsumption(**data)
        self.db.add(rec)
        await self.db.flush()
        await self.db.refresh(rec)
        return rec
