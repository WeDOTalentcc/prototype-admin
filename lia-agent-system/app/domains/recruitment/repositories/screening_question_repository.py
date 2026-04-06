"""
ScreeningQuestionRepository — persistence layer for screening questions.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recruitment_stages import ScreeningQuestion

logger = logging.getLogger(__name__)


class ScreeningQuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        include_inactive: bool = False,
    ) -> list[ScreeningQuestion]:
        query = select(ScreeningQuestion).where(
            ScreeningQuestion.company_id == company_id
        )
        if not include_inactive:
            query = query.where(ScreeningQuestion.is_active)
        query = query.order_by(ScreeningQuestion.order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_all_for_company(self, company_id: str) -> list[ScreeningQuestion]:
        """Return all (including inactive) for bulk sync purposes."""
        result = await self.db.execute(
            select(ScreeningQuestion).where(
                ScreeningQuestion.company_id == company_id
            )
        )
        return list(result.scalars().all())

    async def get_last_order(self, company_id: str) -> int:
        result = await self.db.execute(
            select(ScreeningQuestion)
            .where(ScreeningQuestion.company_id == company_id)
            .order_by(ScreeningQuestion.order.desc())
        )
        last = result.scalars().first()
        return (last.order + 1) if last else 1  # type: ignore[return-value]

    async def get_by_id(self, q_id: UUID) -> ScreeningQuestion | None:
        return await self.db.get(ScreeningQuestion, q_id)

    async def create(self, data: dict) -> ScreeningQuestion:
        q = ScreeningQuestion(**data)
        self.db.add(q)
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def create_no_commit(self, data: dict) -> ScreeningQuestion:
        q = ScreeningQuestion(**data)
        self.db.add(q)
        return q

    async def update(self, q_id: UUID, data: dict) -> ScreeningQuestion | None:
        q = await self.get_by_id(q_id)
        if not q:
            return None
        for key, value in data.items():
            if key != "id":
                setattr(q, key, value)
        q.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        await self.db.refresh(q)
        return q

    async def soft_delete(self, q_id: UUID) -> bool:
        q = await self.get_by_id(q_id)
        if not q:
            return False
        q.is_active = False  # type: ignore[assignment]
        q.updated_at = datetime.utcnow()  # type: ignore[assignment]
        await self.db.commit()
        return True

    async def soft_delete_no_commit(self, q: ScreeningQuestion) -> None:
        q.is_active = False  # type: ignore[assignment]
        q.updated_at = datetime.utcnow()  # type: ignore[assignment]

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh(self, q: ScreeningQuestion) -> None:
        await self.db.refresh(q)
