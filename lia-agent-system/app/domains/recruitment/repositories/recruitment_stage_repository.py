"""
RecruitmentStageRepository — persistence layer for recruitment pipeline stages.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, delete, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_stages import RecruitmentStage

logger = logging.getLogger(__name__)


class RecruitmentStageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        include_inactive: bool = False,
    ) -> list[RecruitmentStage]:
        query = select(RecruitmentStage).where(
            RecruitmentStage.company_id == company_id
        )
        if not include_inactive:
            query = query.where(RecruitmentStage.is_active)
        query = query.order_by(RecruitmentStage.stage_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, stage_id: UUID) -> RecruitmentStage | None:
        result = await self.db.execute(
            select(RecruitmentStage).where(RecruitmentStage.id == stage_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_str(self, stage_id: str) -> RecruitmentStage | None:
        result = await self.db.execute(
            select(RecruitmentStage).where(RecruitmentStage.id == stage_id)
        )
        return result.scalars().first()

    async def get_by_name(self, company_id: str, name: str) -> RecruitmentStage | None:
        result = await self.db.execute(
            select(RecruitmentStage).where(
                and_(
                    RecruitmentStage.company_id == company_id,
                    RecruitmentStage.name == name,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_default_stages(self, company_id: str) -> list[RecruitmentStage]:
        result = await self.db.execute(
            select(RecruitmentStage).where(
                and_(
                    RecruitmentStage.company_id == company_id,
                    RecruitmentStage.is_active,
                )
            ).order_by(RecruitmentStage.stage_order)
        )
        return list(result.scalars().all())

    async def create(self, data: dict) -> RecruitmentStage:
        stage = RecruitmentStage(**data)
        self.db.add(stage)
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def create_bulk(self, stages: list[dict]) -> list[RecruitmentStage]:
        objects = [RecruitmentStage(**s) for s in stages]
        for obj in objects:
            self.db.add(obj)
        await self.db.flush()
        await self.db.commit()
        for obj in objects:
            await self.db.refresh(obj)
        return objects

    async def update(self, stage_id: UUID, data: dict) -> RecruitmentStage | None:
        stage = await self.get_by_id(stage_id)
        if not stage:
            return None
        for key, value in data.items():
            setattr(stage, key, value)
        stage.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        await self.db.refresh(stage)
        return stage

    async def update_fields(self, stage_id: str, updates: dict) -> bool:
        """Bulk-update specific fields via UPDATE statement (no object fetch)."""
        updates["updated_at"] = datetime.utcnow()
        stmt = (
            sa_update(RecruitmentStage)
            .where(RecruitmentStage.id == stage_id)
            .values(**updates)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def update_fields_uuid(self, stage_id: UUID, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow()
        stmt = (
            sa_update(RecruitmentStage)
            .where(RecruitmentStage.id == stage_id)
            .values(**updates)
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return True

    async def delete(self, stage_id: UUID) -> bool:
        stage = await self.get_by_id(stage_id)
        if not stage:
            return False
        await self.db.delete(stage)
        await self.db.commit()
        return True

    async def hard_delete_by_id_str(self, stage_id: str) -> bool:
        stmt = delete(RecruitmentStage).where(RecruitmentStage.id == stage_id)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0

    async def soft_delete(self, stage_id: UUID) -> bool:
        stage = await self.get_by_id(stage_id)
        if not stage:
            return False
        stage.is_active = False  # type: ignore[assignment]
        stage.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def soft_delete_str(self, stage_id: str) -> bool:
        stage = await self.get_by_id_str(stage_id)
        if not stage:
            return False
        stage.is_active = False  # type: ignore[assignment]
        stage.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def delete_for_company(self, company_id: str) -> int:
        stmt = delete(RecruitmentStage).where(
            RecruitmentStage.company_id == company_id
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount

    async def reorder(self, reorder_items: list[dict]) -> bool:
        """Update stage_order for each item. Items are dicts with stage_id + new_order."""
        for item in reorder_items:
            stmt = (
                sa_update(RecruitmentStage)
                .where(RecruitmentStage.id == item["stage_id"])
                .values(stage_order=item["new_order"], updated_at=datetime.utcnow())
            )
            await self.db.execute(stmt)
        await self.db.commit()
        return True
