"""
PipelineTemplate Repository — data access layer for pipeline templates.
Extracted from app/api/v1/pipeline_templates.py as part of Phase 2 refactor.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pipeline_template import DEFAULT_PIPELINE_TEMPLATES, PipelineTemplate

logger = logging.getLogger(__name__)


class PipelineTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        is_active: bool | None = True,
        search: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[PipelineTemplate], int]:
        """Return (items, total) with optional filters."""
        query = select(PipelineTemplate).where(PipelineTemplate.company_id == company_id)
        if is_active is not None:
            query = query.where(PipelineTemplate.is_active == is_active)
        if search:
            p = f"%{search}%"
            query = query.where(
                or_(
                    PipelineTemplate.name.ilike(p),
                    PipelineTemplate.description.ilike(p),
                )
            )
        count_q = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0
        query = (
            query
            .order_by(
                PipelineTemplate.is_default.desc(),
                PipelineTemplate.usage_count.desc(),
                PipelineTemplate.name,
            )
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_by_id(self, template_id: uuid.UUID, company_id: str) -> PipelineTemplate | None:
        result = await self.db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.id == template_id,
                PipelineTemplate.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def clear_default(self, company_id: str, exclude_id: uuid.UUID | None = None) -> None:
        """Un-set is_default on all templates for the company (optionally excluding one)."""
        q = select(PipelineTemplate).where(
            PipelineTemplate.company_id == company_id,
            PipelineTemplate.is_default.is_(True),
        )
        if exclude_id:
            q = q.where(PipelineTemplate.id != exclude_id)
        result = await self.db.execute(q)
        for t in result.scalars():
            t.is_default = False

    async def create(self, company_id: str, data: dict, created_by: str) -> PipelineTemplate:
        template = PipelineTemplate(
            id=uuid.uuid4(),
            company_id=company_id,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            usage_count=0,
            is_active=True,
            **data,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def update(self, template: PipelineTemplate, data: dict) -> PipelineTemplate:
        for key, value in data.items():
            setattr(template, key, value)
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        return template

    async def soft_delete(self, template: PipelineTemplate) -> None:
        template.is_active = False
        template.updated_at = datetime.utcnow()
        await self.db.flush()

    async def clone(
        self, original: PipelineTemplate, new_name: str, created_by: str
    ) -> PipelineTemplate:
        cloned = PipelineTemplate(
            id=uuid.uuid4(),
            company_id=original.company_id,
            name=new_name,
            description=original.description,
            stages=original.stages.copy() if original.stages else [],
            is_default=False,
            is_active=True,
            usage_count=0,
            created_by=created_by,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(cloned)
        await self.db.flush()
        return cloned

    async def count_active(self, company_id: str) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.is_active.is_(True),
            )
        )
        return result.scalar() or 0

    async def get_by_name(self, company_id: str, name: str) -> PipelineTemplate | None:
        result = await self.db.execute(
            select(PipelineTemplate).where(
                PipelineTemplate.company_id == company_id,
                PipelineTemplate.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def seed_defaults(self, company_id: str, created_by: str) -> int:
        seeded = 0
        for tdata in DEFAULT_PIPELINE_TEMPLATES:
            if await self.get_by_name(company_id, tdata["name"]):
                continue
            t = PipelineTemplate(
                id=uuid.uuid4(),
                company_id=company_id,
                name=tdata["name"],
                description=tdata["description"],
                stages=tdata["stages"],
                is_default=tdata["is_default"],
                is_active=True,
                usage_count=0,
                created_by=created_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(t)
            seeded += 1
        await self.db.flush()
        return seeded

    async def increment_usage(self, template: PipelineTemplate) -> PipelineTemplate:
        template.usage_count = (template.usage_count or 0) + 1
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        return template
