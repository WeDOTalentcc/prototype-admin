"""
RecruitmentEmailTemplate Repository — data access layer for recruitment email templates.
Extracted from app/api/v1/recruitment_email_templates.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.recruitment_email_template import RecruitmentEmailTemplate

logger = logging.getLogger(__name__)


class RecruitmentEmailTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        stage: str | None = None,
        template_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RecruitmentEmailTemplate], int]:
        q = select(RecruitmentEmailTemplate).where(
            RecruitmentEmailTemplate.company_id == company_id
        )
        if stage:
            q = q.where(RecruitmentEmailTemplate.stage == stage)
        if template_type:
            q = q.where(RecruitmentEmailTemplate.template_type == template_type)
        if is_active is not None:
            q = q.where(RecruitmentEmailTemplate.is_active == is_active)
        q = q.order_by(RecruitmentEmailTemplate.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(RecruitmentEmailTemplate.id)).where(
            RecruitmentEmailTemplate.company_id == company_id
        )
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, template_id: UUID) -> RecruitmentEmailTemplate | None:
        result = await self.db.execute(
            select(RecruitmentEmailTemplate).where(RecruitmentEmailTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> RecruitmentEmailTemplate:
        t = RecruitmentEmailTemplate(company_id=company_id, **data)
        self.db.add(t)
        await self.db.flush()
        await self.db.refresh(t)
        return t

    async def update(self, template: RecruitmentEmailTemplate, data: dict) -> RecruitmentEmailTemplate:
        for key, value in data.items():
            setattr(template, key, value)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template: RecruitmentEmailTemplate) -> None:
        await self.db.delete(template)
        await self.db.flush()
