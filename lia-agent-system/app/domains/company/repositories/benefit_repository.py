"""BenefitRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company import Benefit

logger = logging.getLogger(__name__)


class BenefitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[Benefit]:
        result = await self.db.execute(
            select(Benefit).where(Benefit.company_id == company_id)
        )
        return list(result.scalars().all())

    async def get_by_id(self, benefit_id: UUID) -> Benefit | None:
        result = await self.db.execute(
            select(Benefit).where(Benefit.id == benefit_id)
        )
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
