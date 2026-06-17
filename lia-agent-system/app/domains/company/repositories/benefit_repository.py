"""BenefitRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Benefit

logger = logging.getLogger(__name__)


class BenefitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[Benefit]:
        result = await self.db.execute(
            select(Benefit).where(Benefit.company_id == company_id)
        )
        return list(result.scalars().all())

    async def list_active_for_company(self, company_id: UUID) -> list[Benefit]:
        """Active benefits for a company, ordered by category and order."""
        result = await self.db.execute(
            select(Benefit)
            .where(
                Benefit.company_id == company_id,
                Benefit.is_active,
            )
            .order_by(Benefit.category, Benefit.order)
        )
        return list(result.scalars().all())

    async def list_optional_company(
        self, company_id: UUID | None = None
    ) -> list[Benefit]:
        """List benefits; if company_id provided, scope to that company.

        Used by AI summary endpoint that may aggregate across companies.
        """
        # TENANT-EXEMPT: dynamic builder — Benefit.company_id == company_id é
        # appended conditionally below quando company_id passado. AI summary
        # caller pode legitimamente aggregate across companies.
        query = select(Benefit)
        if company_id is not None:
            query = query.where(Benefit.company_id == company_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        benefit_id: UUID,
        company_id: UUID | None = None,
    ) -> Benefit | None:
        """Get benefit by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Benefit.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Benefit).where(Benefit.id == benefit_id)
        if company_id:
            query = query.where(Benefit.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Benefit:
        benefit = Benefit(**data)
        self.db.add(benefit)
        await self.db.commit()
        await self.db.refresh(benefit)
        return benefit

    async def update(self, benefit_id: UUID, data: dict) -> Benefit | None:
        benefit = await self.get_by_id(benefit_id)
        if not benefit:
            return None
        for key, value in data.items():
            if hasattr(benefit, key):
                setattr(benefit, key, value)
        await self.db.commit()
        await self.db.refresh(benefit)
        return benefit

    async def delete(self, benefit_id: UUID) -> bool:
        benefit = await self.get_by_id(benefit_id)
        if not benefit:
            return False
        benefit.is_active = False
        await self.db.commit()
        return True
    # ── Extensions for benefits_service (ADR-001 cleanup, Sprint Q2) ──────

    async def list_active_ordered(self, company_id) -> list[Benefit]:
        """Active benefits for a company, ordered by order/category/name.

        Used by BenefitsService.get_active_benefits.
        """
        result = await self.db.execute(
            select(Benefit)
            .where(
                Benefit.company_id == company_id,
                Benefit.is_active,
            )
            .order_by(Benefit.order, Benefit.category, Benefit.name)
        )
        return list(result.scalars().all())

    async def list_highlighted(self, company_id) -> list[Benefit]:
        """Highlighted active benefits, ordered by order/name."""
        result = await self.db.execute(
            select(Benefit)
            .where(
                Benefit.company_id == company_id,
                Benefit.is_active,
                Benefit.is_highlighted,
            )
            .order_by(Benefit.order, Benefit.name)
        )
        return list(result.scalars().all())

    async def list_by_category(
        self, company_id, category: str
    ) -> list[Benefit]:
        """Active benefits in a specific category, ordered by order/name."""
        result = await self.db.execute(
            select(Benefit)
            .where(
                Benefit.company_id == company_id,
                Benefit.is_active,
                Benefit.category == category,
            )
            .order_by(Benefit.order, Benefit.name)
        )
        return list(result.scalars().all())
