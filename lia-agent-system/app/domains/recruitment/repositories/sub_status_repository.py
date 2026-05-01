"""
SubStatusRepository — persistence layer for recruitment sub-statuses.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_stages import RecruitmentSubStatus

logger = logging.getLogger(__name__)


class SubStatusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_stage(
        self,
        stage_id: UUID | str,
        include_inactive: bool = False,
    ) -> list[RecruitmentSubStatus]:
        query = select(RecruitmentSubStatus).where(
            RecruitmentSubStatus.stage_id == stage_id
        )
        if not include_inactive:
            query = query.where(RecruitmentSubStatus.is_active)
        query = query.order_by(RecruitmentSubStatus.sub_status_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_for_company(
        self,
        company_id: str,
        include_inactive: bool = False,
    ) -> list[RecruitmentSubStatus]:
        query = select(RecruitmentSubStatus).where(
            RecruitmentSubStatus.company_id == company_id
        )
        if not include_inactive:
            query = query.where(RecruitmentSubStatus.is_active)
        query = query.order_by(RecruitmentSubStatus.sub_status_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, ss_id: UUID) -> RecruitmentSubStatus | None:
        result = await self.db.execute(
            select(RecruitmentSubStatus).where(RecruitmentSubStatus.id == ss_id)
        )
        return result.scalar_one_or_none()

    async def get_existing_names_for_stage(self, stage_id: UUID | str) -> set[str]:
        result = await self.db.execute(
            select(RecruitmentSubStatus.name).where(
                RecruitmentSubStatus.stage_id == stage_id
            )
        )
        return {row[0] for row in result.fetchall()}

    async def get_max_order_for_stage(self, stage_id: UUID | str) -> int:
        result = await self.db.execute(
            select(RecruitmentSubStatus.sub_status_order)
            .where(RecruitmentSubStatus.stage_id == stage_id)
            .order_by(RecruitmentSubStatus.sub_status_order.desc())
            .limit(1)
        )
        row = result.fetchone()
        return (row[0] + 1) if row else 0

    async def create(self, data: dict) -> RecruitmentSubStatus:
        sub = RecruitmentSubStatus(**data)
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def create_no_commit(self, data: dict) -> RecruitmentSubStatus:
        """Create and add to session without committing. Caller must commit."""
        sub = RecruitmentSubStatus(**data)
        self.db.add(sub)
        return sub

    async def update(self, ss_id: UUID, data: dict) -> RecruitmentSubStatus | None:
        sub = await self.get_by_id(ss_id)
        if not sub:
            return None
        for key, value in data.items():
            setattr(sub, key, value)
        sub.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def patch(self, ss_id: UUID, allowed_fields: set, data: dict) -> RecruitmentSubStatus | None:
        sub = await self.get_by_id(ss_id)
        if not sub:
            return None
        for key, value in data.items():
            if key in allowed_fields:
                setattr(sub, key, value)
        sub.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def soft_delete(self, ss_id: UUID) -> bool:
        sub = await self.get_by_id(ss_id)
        if not sub:
            return False
        sub.is_active = False  # type: ignore[assignment]
        sub.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def commit(self) -> None:
        await self.db.commit()
