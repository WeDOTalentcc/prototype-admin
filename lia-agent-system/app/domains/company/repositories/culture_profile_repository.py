"""CultureProfileRepository - for CompanyCultureProfile model."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_culture import CompanyCultureProfile

logger = logging.getLogger(__name__)


class CultureProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_company(self, company_id: UUID) -> CompanyCultureProfile | None:
        result = await self.db.execute(
            select(CompanyCultureProfile).where(CompanyCultureProfile.company_id == company_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CompanyCultureProfile:
        cp = CompanyCultureProfile(**data)
        self.db.add(cp)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def update(self, company_id: UUID, data: dict) -> CompanyCultureProfile | None:
        cp = await self.get_for_company(company_id)
        if not cp:
            return None
        for key, value in data.items():
            if hasattr(cp, key):
                setattr(cp, key, value)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp

    async def create_or_update(self, company_id: UUID, data: dict) -> CompanyCultureProfile:
        cp = await self.get_for_company(company_id)
        if cp:
            for key, value in data.items():
                if hasattr(cp, key):
                    setattr(cp, key, value)
        else:
            cp = CompanyCultureProfile(company_id=company_id, **data)
            self.db.add(cp)
        await self.db.commit()
        await self.db.refresh(cp)
        return cp
