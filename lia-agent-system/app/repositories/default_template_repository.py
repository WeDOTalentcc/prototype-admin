"""
DefaultTemplate Repository — data access layer for system-wide default communication templates.
Extracted from app/api/v1/default_templates.py as part of Phase 2 refactor.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.default_templates import DEFAULT_TEMPLATES_SEED, DefaultTemplate

logger = logging.getLogger(__name__)


class DefaultTemplateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_templates(
        self,
        *,
        conditions: list,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DefaultTemplate], int]:
        query = select(DefaultTemplate)
        if conditions:
            query = query.where(and_(*conditions))
        query = query.order_by(DefaultTemplate.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        templates = list(result.scalars().all())

        count_q = select(func.count(DefaultTemplate.id))
        if conditions:
            count_q = count_q.where(and_(*conditions))
        total = (await self.db.execute(count_q)).scalar() or 0
        return templates, total

    async def get_by_id(self, template_id: UUID) -> DefaultTemplate | None:
        result = await self.db.execute(
            select(DefaultTemplate).where(DefaultTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> DefaultTemplate | None:
        result = await self.db.execute(
            select(DefaultTemplate).where(DefaultTemplate.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> DefaultTemplate:
        template = DefaultTemplate(**data)
        self.db.add(template)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def update(self, template: DefaultTemplate, data: dict) -> DefaultTemplate:
        for key, value in data.items():
            setattr(template, key, value)
        template.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def delete(self, template: DefaultTemplate) -> None:
        await self.db.delete(template)

    async def duplicate(self, original: DefaultTemplate, new_name: str, created_by: str) -> DefaultTemplate:
        copy = DefaultTemplate(
            name=new_name,
            category=original.category,
            subject=original.subject,
            body=original.body,
            variables=original.variables.copy() if original.variables else [],
            status="draft",
            created_by=created_by,
        )
        self.db.add(copy)
        await self.db.flush()
        await self.db.refresh(copy)
        return copy

    async def seed_defaults(self, created_by: str = "system") -> list[DefaultTemplate]:
        created = []
        for tdata in DEFAULT_TEMPLATES_SEED:
            if await self.get_by_name(tdata["name"]):
                continue
            t = DefaultTemplate(
                name=tdata["name"],
                category=tdata["category"],
                subject=tdata.get("subject"),
                body=tdata["body"],
                variables=tdata.get("variables", []),
                status=tdata.get("status", "active"),
                created_by=created_by,
            )
            self.db.add(t)
            created.append(t)
        if created:
            await self.db.flush()
            for t in created:
                await self.db.refresh(t)
        return created
