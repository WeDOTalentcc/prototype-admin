"""
ATSMappingRepository — persistence layer for ATS stage mappings.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_stages import ATSStageMapping

logger = logging.getLogger(__name__)


class ATSMappingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        ats_type: str | None = None,
        include_inactive: bool = False,
    ) -> list[ATSStageMapping]:
        query = select(ATSStageMapping).where(
            ATSStageMapping.company_id == company_id
        )
        if not include_inactive:
            query = query.where(ATSStageMapping.is_active)
        if ats_type:
            query = query.where(ATSStageMapping.ats_type == ats_type)
        query = query.order_by(ATSStageMapping.ats_type, ATSStageMapping.priority.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_id(self, mapping_id: UUID) -> ATSStageMapping | None:
        result = await self.db.execute(
            select(ATSStageMapping).where(ATSStageMapping.id == mapping_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> ATSStageMapping:
        mapping = ATSStageMapping(**data)
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def create_no_commit(self, data: dict) -> ATSStageMapping:
        """Create and add to session without committing. Caller must commit."""
        mapping = ATSStageMapping(**data)
        self.db.add(mapping)
        return mapping

    async def upsert(
        self,
        company_id: str,
        stage_id: UUID,
        ats_type: str,
        ats_stage_id: str,
    ) -> ATSStageMapping:
        result = await self.db.execute(
            select(ATSStageMapping).where(
                and_(
                    ATSStageMapping.company_id == company_id,
                    ATSStageMapping.wedotalent_stage_id == stage_id,
                    ATSStageMapping.ats_type == ats_type,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.ats_stage_id = ats_stage_id  # type: ignore[assignment]
            existing.updated_at = datetime.utcnow()  # type: ignore[assignment]
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        new_mapping = ATSStageMapping(
            company_id=company_id,
            wedotalent_stage_id=stage_id,
            ats_type=ats_type,
            ats_stage_id=ats_stage_id,
        )
        self.db.add(new_mapping)
        await self.db.commit()
        await self.db.refresh(new_mapping)
        return new_mapping

    async def soft_delete(self, mapping_id: UUID) -> bool:
        mapping = await self.get_by_id(mapping_id)
        if not mapping:
            return False
        mapping.is_active = False  # type: ignore[assignment]
        mapping.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def commit(self) -> None:
        await self.db.commit()
