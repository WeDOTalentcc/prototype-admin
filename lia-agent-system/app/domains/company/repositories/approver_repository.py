"""ApproverRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company import Approver

logger = logging.getLogger(__name__)


class ApproverRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(self, company_id: UUID) -> list[Approver]:
        result = await self.db.execute(
            select(Approver)
            .where(Approver.company_id == company_id, Approver.is_active)
            .order_by(Approver.level)
        )
        return list(result.scalars().all())

    async def get_by_id(self, approver_id: UUID) -> Approver | None:
        result = await self.db.execute(
            select(Approver).where(Approver.id == approver_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> Approver:
        approver = Approver(**data)
        self.db.add(approver)
        await self.db.commit()
        await self.db.refresh(approver)
        return approver

    async def update(self, approver_id: UUID, data: dict) -> Approver | None:
        approver = await self.get_by_id(approver_id)
        if not approver:
            return None
        for key, value in data.items():
            if hasattr(approver, key):
                setattr(approver, key, value)
        await self.db.commit()
        await self.db.refresh(approver)
        return approver

    async def delete(self, approver_id: UUID) -> bool:
        approver = await self.get_by_id(approver_id)
        if not approver:
            return False
        approver.is_active = False
        await self.db.commit()
        return True
