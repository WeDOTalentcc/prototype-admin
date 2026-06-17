"""
RecruitmentEmailTemplate Repository — data access for recruitment email templates.

Per ADR-001 extracted from app/domains/job_management/services/recruitment_email_templates.py.
"""
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.recruitment_email_template import RecruitmentEmailTemplate


class RecruitmentEmailTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_stage_type_company(
        self,
        *,
        stage_name: str,
        template_type: str,
        company_id: str | None,
    ) -> RecruitmentEmailTemplate | None:
        clauses = [
            RecruitmentEmailTemplate.stage_name == stage_name,
            RecruitmentEmailTemplate.template_type == template_type,
        ]
        if company_id:
            clauses.append(RecruitmentEmailTemplate.company_id == company_id)
        else:
            clauses.append(RecruitmentEmailTemplate.company_id.is_(None))
        result = await self.db.execute(
            # TENANT-EXEMPT: query uses dynamic conditions=[Model.company_id==X, ...] builder; AST sensor cannot trace upstream tenant gate
            select(RecruitmentEmailTemplate).where(and_(*clauses))
        )
        return result.scalar_one_or_none()

    async def find_active_for_stage(
        self,
        *,
        stage_name: str,
        template_type: str,
        company_id: str,
    ) -> RecruitmentEmailTemplate | None:
        result = await self.db.execute(
            select(RecruitmentEmailTemplate).where(
                and_(
                    RecruitmentEmailTemplate.stage_name == stage_name,
                    RecruitmentEmailTemplate.template_type == template_type,
                    RecruitmentEmailTemplate.company_id == company_id,
                    RecruitmentEmailTemplate.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def find_active_system_for_stage(
        self,
        *,
        stage_name: str,
        template_type: str,
    ) -> RecruitmentEmailTemplate | None:
        result = await self.db.execute(
            select(RecruitmentEmailTemplate).where(
                and_(
                    RecruitmentEmailTemplate.stage_name == stage_name,
                    RecruitmentEmailTemplate.template_type == template_type,
                    RecruitmentEmailTemplate.company_id.is_(None),
                    RecruitmentEmailTemplate.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        *,
        company_id: str | None = None,
        stage_name: str | None = None,
        template_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[RecruitmentEmailTemplate]:
        # TENANT-EXEMPT: dynamic builder — RecruitmentEmailTemplate.company_id
        # filtering composed conditionally below (system templates vs scoped).
        query = select(RecruitmentEmailTemplate)
        if company_id:
            query = query.where(
                or_(
                    RecruitmentEmailTemplate.company_id == company_id,
                    RecruitmentEmailTemplate.company_id.is_(None),
                )
            )
        if stage_name:
            query = query.where(RecruitmentEmailTemplate.stage_name == stage_name)
        if template_type:
            query = query.where(RecruitmentEmailTemplate.template_type == template_type)
        if is_active is not None:
            query = query.where(RecruitmentEmailTemplate.is_active == is_active)
        query = query.order_by(
            RecruitmentEmailTemplate.stage_name, RecruitmentEmailTemplate.template_type
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_system_templates(self) -> list[RecruitmentEmailTemplate]:
        # TENANT-EXEMPT: system templates are tenant-null by design
        # (shared catalog).
        result = await self.db.execute(
            select(RecruitmentEmailTemplate).where(
                and_(
                    RecruitmentEmailTemplate.company_id.is_(None),
                    RecruitmentEmailTemplate.is_system,
                )
            )
        )
        return list(result.scalars().all())
