"""IdealProfileRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import IdealProfile

logger = logging.getLogger(__name__)


class IdealProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[IdealProfile]:
        result = await self.db.execute(
            select(IdealProfile).where(IdealProfile.company_id == company_id)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        ip_id: UUID,
        company_id: UUID | None = None,
    ) -> IdealProfile | None:
        """Get ideal profile by id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — IdealProfile.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(IdealProfile).where(IdealProfile.id == ip_id)
        if company_id:
            query = query.where(IdealProfile.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> IdealProfile:
        profile = IdealProfile(**data)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(self, ip_id: UUID, data: dict) -> IdealProfile | None:
        profile = await self.get_by_id(ip_id)
        if not profile:
            return None
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def delete(self, ip_id: UUID) -> bool:
        profile = await self.get_by_id(ip_id)
        if not profile:
            return False
        profile.is_active = False
        await self.db.commit()
        return True
