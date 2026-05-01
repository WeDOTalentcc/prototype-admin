"""
LearningPatternsRepository — data access for correction patterns, company skills,
and success profiles.
Extracted from app/api/v1/learning_patterns.py as part of Phase 2 refactor.
"""
from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession


class LearningPatternsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_correction_patterns(
        self,
        company_id: str,
        field: str | None = None,
        seniority: str | None = None,
    ) -> list:
        """Return CorrectionPattern rows for a company, ordered by confidence desc."""
        from app.models.intelligence_layer import CorrectionPattern

        conditions = [CorrectionPattern.company_id == company_id]
        if field:
            conditions.append(CorrectionPattern.field == field)
        if seniority:
            conditions.append(CorrectionPattern.seniority == seniority.lower())

        result = await self.db.execute(
            select(CorrectionPattern)
            .where(and_(*conditions))
            .order_by(CorrectionPattern.confidence.desc())
        )
        return list(result.scalars().all())

    async def get_promoted_skills(
        self,
        company_id: str,
    ) -> list:
        """Return promoted CompanySkill rows for a company, ordered by times_confirmed desc."""
        from app.models.company_learning import CompanySkill

        result = await self.db.execute(
            select(CompanySkill)
            .where(
                and_(
                    CompanySkill.company_id == company_id,
                    CompanySkill.is_promoted,
                )
            )
            .order_by(CompanySkill.times_confirmed.desc())
        )
        return list(result.scalars().all())

    async def get_success_profiles(
        self,
        company_id: str,
        role: str | None = None,
        seniority: str | None = None,
    ) -> list:
        """Return SuccessProfile rows for a company, ordered by sample_size desc."""
        from app.models.intelligence_layer import SuccessProfile

        conditions = [SuccessProfile.company_id == company_id]
        if seniority:
            conditions.append(SuccessProfile.seniority == seniority.lower())
        if role:
            conditions.append(SuccessProfile.role_family.ilike(f"%{role}%"))

        result = await self.db.execute(
            select(SuccessProfile)
            .where(and_(*conditions))
            .order_by(SuccessProfile.sample_size.desc())
        )
        return list(result.scalars().all())
