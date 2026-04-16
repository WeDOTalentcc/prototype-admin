"""TechnicalTestRepository - session-in-constructor pattern."""
import logging
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company import TechnicalQuestion, TechnicalTestTemplate

logger = logging.getLogger(__name__)


class TechnicalTestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_questions(
        self, company_id: UUID | None = None
    ) -> list[TechnicalQuestion]:
        query = select(TechnicalQuestion).where(TechnicalQuestion.is_active)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_question(self, q_id: UUID) -> TechnicalQuestion | None:
        result = await self.db.execute(
            select(TechnicalQuestion).where(TechnicalQuestion.id == q_id)
        )
        return result.scalar_one_or_none()

    async def create_question(self, data: dict) -> TechnicalQuestion:
        q = TechnicalQuestion(**data)
        self.db.add(q)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def update_question(
        self, q_id: UUID, data: dict
    ) -> TechnicalQuestion | None:
        q = await self.get_question(q_id)
        if not q:
            return None
        for key, value in data.items():
            if hasattr(q, key):
                setattr(q, key, value)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def delete_question(self, q_id: UUID) -> bool:
        q = await self.get_question(q_id)
        if not q:
            return False
        q.is_active = False
        await self.db.commit()
        return True

    async def list_templates(
        self, company_id: UUID
    ) -> list[TechnicalTestTemplate]:
        result = await self.db.execute(
            select(TechnicalTestTemplate)
            .where(
                or_(
                    TechnicalTestTemplate.company_id == company_id,
                    TechnicalTestTemplate.is_public,
                )
            )
            .order_by(TechnicalTestTemplate.name)
        )
        return list(result.scalars().all())

    async def get_template(self, tmpl_id: UUID) -> TechnicalTestTemplate | None:
        result = await self.db.execute(
            select(TechnicalTestTemplate).where(TechnicalTestTemplate.id == tmpl_id)
        )
        return result.scalar_one_or_none()

    async def create_template(self, data: dict) -> TechnicalTestTemplate:
        tmpl = TechnicalTestTemplate(**data)
        self.db.add(tmpl)
        await self.db.commit()
        await self.db.refresh(tmpl)
        return tmpl

    async def update_template(
        self, tmpl_id: UUID, data: dict
    ) -> TechnicalTestTemplate | None:
        tmpl = await self.get_template(tmpl_id)
        if not tmpl:
            return None
        for key, value in data.items():
            if hasattr(tmpl, key):
                setattr(tmpl, key, value)
        await self.db.commit()
        await self.db.refresh(tmpl)
        return tmpl

    async def delete_template(self, tmpl_id: UUID) -> bool:
        tmpl = await self.get_template(tmpl_id)
        if not tmpl:
            return False
        tmpl.is_active = False
        await self.db.commit()
        return True
