"""
JobTemplate Repository — data access for Fast Track job templates.

Extracted per ADR-001 from app/domains/job_management/services/job_template_service.py.
"""
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_template import JobTemplate


class JobTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, template_id: UUID) -> JobTemplate | None:
        result = await self.db.execute(
            select(JobTemplate).where(JobTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        *,
        company_id: UUID | None = None,
        category: str | None = None,
        subcategory: str | None = None,
        seniority: str | None = None,
        include_system: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> list[JobTemplate]:
        query = select(JobTemplate).where(JobTemplate.is_active)

        if company_id and include_system:
            query = query.where(
                or_(JobTemplate.company_id == company_id, JobTemplate.is_system)
            )
        elif company_id:
            query = query.where(JobTemplate.company_id == company_id)
        elif include_system:
            query = query.where(JobTemplate.is_system)

        if category:
            query = query.where(JobTemplate.category == category)
        if subcategory:
            query = query.where(JobTemplate.subcategory == subcategory)
        if seniority:
            query = query.where(JobTemplate.seniority == seniority)

        query = query.order_by(JobTemplate.popularity_score.desc())
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        query: str,
        *,
        company_id: UUID | None = None,
        limit: int = 20,
    ) -> list[JobTemplate]:
        query_lower = f"%{query.lower()}%"
        sql_query = (
            select(JobTemplate)
            .where(JobTemplate.is_active)
            .where(
                or_(
                    func.lower(JobTemplate.title).like(query_lower),
                    func.lower(JobTemplate.title_normalized).like(query_lower),
                    func.lower(
                        func.array_to_string(JobTemplate.title_alternatives, " ")
                    ).like(query_lower),
                )
            )
        )
        if company_id:
            sql_query = sql_query.where(
                or_(JobTemplate.company_id == company_id, JobTemplate.is_system)
            )
        else:
            sql_query = sql_query.where(JobTemplate.is_system)

        sql_query = sql_query.order_by(JobTemplate.popularity_score.desc()).limit(limit)
        result = await self.db.execute(sql_query)
        return list(result.scalars().all())

    async def get_popular(
        self,
        *,
        company_id: UUID | None = None,
        category: str | None = None,
        limit: int = 10,
    ) -> list[JobTemplate]:
        query = (
            select(JobTemplate)
            .where(JobTemplate.is_active)
            .order_by(JobTemplate.usage_count.desc())
            .limit(limit)
        )
        if category:
            query = query.where(JobTemplate.category == category)
        if company_id:
            query = query.where(
                or_(JobTemplate.company_id == company_id, JobTemplate.is_system)
            )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def find_system_by_title_seniority(
        self, title: str, seniority: str
    ) -> JobTemplate | None:
        result = await self.db.execute(
            select(JobTemplate).where(
                JobTemplate.is_system,
                JobTemplate.title == title,
                JobTemplate.seniority == seniority,
            )
        )
        return result.scalar_one_or_none()

    async def category_stats(self) -> dict[str, int]:
        result = await self.db.execute(
            select(JobTemplate.category, func.count(JobTemplate.id).label("count"))
            .where(JobTemplate.is_active)
            .where(JobTemplate.is_system)
            .group_by(JobTemplate.category)
        )
        return {row.category: row.count for row in result}

    def add(self, template: JobTemplate) -> None:
        self.db.add(template)
