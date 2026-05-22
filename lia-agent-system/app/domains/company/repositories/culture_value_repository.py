"""CultureValueRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CultureValue

logger = logging.getLogger(__name__)


class CultureValueRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[CultureValue]:
        result = await self.db.execute(
            select(CultureValue).where(CultureValue.company_id == company_id)
        )
        return list(result.scalars().all())

    async def list_active_for_company(
        self, company_id: UUID
    ) -> list[CultureValue]:
        """Active culture values for a company, ordered by display order."""
        result = await self.db.execute(
            select(CultureValue)
            .where(
                CultureValue.company_id == company_id,
                CultureValue.is_active,
            )
            .order_by(CultureValue.order)
        )
        return list(result.scalars().all())

    async def get_by_id(
        self,
        cv_id: UUID,
        company_id: UUID | None = None,
    ) -> CultureValue | None:
        """Get culture value by id. Multi-tenancy defense-in-depth via
        company_id filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — CultureValue.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(CultureValue).where(CultureValue.id == cv_id)
        if company_id:
            query = query.where(CultureValue.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> CultureValue:
        cv = CultureValue(**data)
        self.db.add(cv)
        await self.db.commit()
        await self.db.refresh(cv)
        return cv

    async def update(self, cv_id: UUID, data: dict) -> CultureValue | None:
        cv = await self.get_by_id(cv_id)
        if not cv:
            return None
        for key, value in data.items():
            if hasattr(cv, key):
                setattr(cv, key, value)
        await self.db.commit()
        await self.db.refresh(cv)
        return cv

    async def delete(self, cv_id: UUID) -> bool:
        cv = await self.get_by_id(cv_id)
        if not cv:
            return False
        cv.is_active = False
        await self.db.commit()
        return True
