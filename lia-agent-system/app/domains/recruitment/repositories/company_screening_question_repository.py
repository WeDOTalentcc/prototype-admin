"""
ScreeningQuestion Repository (API layer) — data access for company screening questions.
Extracted from app/api/v1/screening_questions.py as part of Phase 2 refactor.
Note: a recruitment-domain repo already exists at
      app/domains/recruitment/repositories/screening_question_repository.py
      This repo handles the /api/v1/screening_questions endpoint pattern.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CompanyScreeningQuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_model(self):
        from app.models.screening_question import ScreeningQuestion
        return ScreeningQuestion

    async def list_for_company(
        self,
        company_id: str,
        *,
        question_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list, int]:
        M = await self._get_model()
        q = select(M).where(M.company_id == company_id)
        if question_type:
            q = q.where(M.question_type == question_type)
        if is_active is not None:
            q = q.where(M.is_active == is_active)
        q = q.order_by(M.order, M.created_at).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(M.id)).where(M.company_id == company_id)
        if question_type:
            cq = cq.where(M.question_type == question_type)
        if is_active is not None:
            cq = cq.where(M.is_active == is_active)
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, question_id: UUID) -> object | None:
        M = await self._get_model()
        result = await self.db.execute(select(M).where(M.id == question_id))
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> object:
        M = await self._get_model()
        q = M(company_id=company_id, **data)
        self.db.add(q)
        await self.db.flush()
        await self.db.refresh(q)
        return q

    async def update(self, question, data: dict) -> object:
        for key, value in data.items():
            setattr(question, key, value)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete(self, question) -> None:
        await self.db.delete(question)
        await self.db.flush()

    async def bulk_create(self, company_id: str, questions_data: list[dict]) -> list:
        M = await self._get_model()
        created = []
        for qdata in questions_data:
            q = M(company_id=company_id, **qdata)
            self.db.add(q)
            created.append(q)
        await self.db.flush()
        for q in created:
            await self.db.refresh(q)
        return created
