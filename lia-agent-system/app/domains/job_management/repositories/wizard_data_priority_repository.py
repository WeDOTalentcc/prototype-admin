"""
WizardDataPriority Repository — consolidates cross-domain reads used by
WizardDataPriorityService for source-prioritized suggestions.

Per ADR-001 extracted from
app/domains/job_management/services/wizard_data_priority_service.py.

Cross-domain reads include Department, Benefit, CompanySkill,
CompanyResponsibility, ImportedJobDescription, ClientSkillCatalog,
JobPattern. All run in tenant context (caller passes company_id explicitly).
"""
from typing import Any
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company import Benefit, Department
from lia_models.company_learning import CompanyResponsibility, CompanySkill
from lia_models.imported_job_description import (
    ClientSkillCatalog,
    ImportedJobDescription,
)
from lia_models.job_pattern import JobPattern


class WizardDataPriorityRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_departments(self, company_id: str) -> list[Department]:
        result = await self.db.execute(
            select(Department).where(Department.company_id == company_id)
        )
        return list(result.scalars().all())

    async def list_benefits(self, company_id: str) -> list[Benefit]:
        result = await self.db.execute(
            select(Benefit).where(Benefit.company_id == company_id)
        )
        return list(result.scalars().all())

    async def list_promoted_technical_skills(
        self, company_id: str, *, limit: int = 20
    ) -> list[CompanySkill]:
        result = await self.db.execute(
            select(CompanySkill)
            .where(
                and_(
                    CompanySkill.company_id == company_id,
                    CompanySkill.is_promoted,
                    CompanySkill.skill_type == "technical",
                )
            )
            .order_by(desc(CompanySkill.times_confirmed))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_promoted_responsibilities(
        self, company_id: str, *, limit: int = 10
    ) -> list[CompanyResponsibility]:
        result = await self.db.execute(
            select(CompanyResponsibility)
            .where(
                and_(
                    CompanyResponsibility.company_id == company_id,
                    CompanyResponsibility.is_promoted,
                )
            )
            .order_by(desc(CompanyResponsibility.times_confirmed))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_top_job_pattern_by_title(
        self, *, company_id: UUID, job_title: str, min_samples: int = 2
    ) -> JobPattern | None:
        result = await self.db.execute(
            select(JobPattern)
            .where(
                and_(
                    JobPattern.company_id == company_id,
                    JobPattern.job_title_normalized.ilike(f"%{job_title}%"),
                    JobPattern.sample_count >= min_samples,
                )
            )
            .order_by(desc(JobPattern.sample_count))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_imported_jds(
        self, filters: list[Any], *, limit: int = 10
    ) -> list[ImportedJobDescription]:
        # TENANT-EXEMPT: dynamic builder — caller (wizard_data_priority_service)
        # composes ``filters`` always starting with
        # ImportedJobDescription.company_id == X; AST sensor cannot trace.
        result = await self.db.execute(
            select(ImportedJobDescription)
            .where(and_(*filters))
            .order_by(desc(ImportedJobDescription.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def coverage_counts(self, company_id: UUID) -> dict[str, int]:
        imported = await self.db.execute(
            select(func.count())
            .select_from(ImportedJobDescription)
            .where(ImportedJobDescription.company_id == company_id)
        )
        skills = await self.db.execute(
            select(func.count())
            .select_from(ClientSkillCatalog)
            .where(ClientSkillCatalog.company_id == company_id)
        )
        patterns = await self.db.execute(
            select(func.count())
            .select_from(JobPattern)
            .where(JobPattern.company_id == company_id)
        )
        return {
            "imported": imported.scalar() or 0,
            "skills": skills.scalar() or 0,
            "patterns": patterns.scalar() or 0,
        }
