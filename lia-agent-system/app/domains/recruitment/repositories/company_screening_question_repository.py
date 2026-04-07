"""
CompanyScreeningQuestion Repository — data access layer for company default screening questions.
Extracted from app/api/v1/screening_questions.py as part of Phase 2 refactor.
"""
import logging
import uuid as uuid_lib
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening_question import CompanyScreeningQuestion

logger = logging.getLogger(__name__)


class CompanyScreeningQuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[CompanyScreeningQuestion]:
        stmt = select(CompanyScreeningQuestion).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        if is_active is not None:
            stmt = stmt.where(CompanyScreeningQuestion.is_active == is_active)
        if category:
            stmt = stmt.where(CompanyScreeningQuestion.category == category)
        stmt = stmt.order_by(
            CompanyScreeningQuestion.order, CompanyScreeningQuestion.created_at
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_max_order(self, company_id: str) -> int:
        stmt = select(func.max(CompanyScreeningQuestion.order)).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_by_id(
        self, question_id: UUID, company_id: str
    ) -> CompanyScreeningQuestion | None:
        stmt = select(CompanyScreeningQuestion).where(
            CompanyScreeningQuestion.id == question_id,
            CompanyScreeningQuestion.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, company_id: str, data: dict) -> CompanyScreeningQuestion:
        q = CompanyScreeningQuestion(
            id=uuid_lib.uuid4(),
            company_id=company_id,
            **data,
        )
        self.db.add(q)
        await self.db.flush()
        await self.db.refresh(q)
        return q

    async def update(
        self, question: CompanyScreeningQuestion, data: dict
    ) -> CompanyScreeningQuestion:
        for key, value in data.items():
            setattr(question, key, value)
        question.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete(self, question: CompanyScreeningQuestion) -> None:
        await self.db.delete(question)

    async def count_for_company(self, company_id: str) -> int:
        stmt = select(func.count(CompanyScreeningQuestion.id)).where(
            CompanyScreeningQuestion.company_id == company_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def reorder(self, company_id: str, question_ids: list[str]) -> None:
        for idx, q_id in enumerate(question_ids, start=1):
            stmt = update(CompanyScreeningQuestion).where(
                CompanyScreeningQuestion.id == UUID(q_id),
                CompanyScreeningQuestion.company_id == company_id,
            ).values(order=idx, updated_at=datetime.utcnow())
            await self.db.execute(stmt)

    async def bulk_create(
        self, company_id: str, questions_data: list[dict]
    ) -> list[CompanyScreeningQuestion]:
        created = []
        for qdata in questions_data:
            q = CompanyScreeningQuestion(
                id=uuid_lib.uuid4(),
                company_id=company_id,
                **qdata,
            )
            self.db.add(q)
            created.append(q)
        await self.db.flush()
        return created
