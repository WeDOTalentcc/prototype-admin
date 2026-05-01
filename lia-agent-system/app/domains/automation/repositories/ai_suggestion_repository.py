"""
AISuggestion Repository — data access layer for automation AI suggestions.
Extracted from app/api/v1/automation/suggestions.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import AISuggestion

logger = logging.getLogger(__name__)


class AISuggestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_company(
        self,
        company_id: str,
        *,
        status: str | None = None,
        suggestion_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AISuggestion], int]:
        q = select(AISuggestion).where(AISuggestion.company_id == company_id)
        if status:
            q = q.where(AISuggestion.status == status)
        if suggestion_type:
            q = q.where(AISuggestion.suggestion_type == suggestion_type)
        q = q.order_by(AISuggestion.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(AISuggestion.id)).where(AISuggestion.company_id == company_id)
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(self, suggestion_id: UUID) -> AISuggestion | None:
        result = await self.db.execute(
            select(AISuggestion).where(AISuggestion.id == suggestion_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: dict) -> AISuggestion:
        s = AISuggestion(**data)
        self.db.add(s)
        await self.db.flush()
        await self.db.refresh(s)
        return s

    async def update(self, suggestion: AISuggestion, data: dict) -> AISuggestion:
        for key, value in data.items():
            setattr(suggestion, key, value)
        await self.db.flush()
        await self.db.refresh(suggestion)
        return suggestion

    async def delete(self, suggestion: AISuggestion) -> None:
        await self.db.delete(suggestion)
        await self.db.flush()

    async def list_by_vacancy(
        self,
        vacancy_id: str,
        *,
        status: str | None = None,
    ) -> list[AISuggestion]:
        """List suggestions for a specific vacancy."""
        query = select(AISuggestion).where(AISuggestion.vacancy_id == vacancy_id)
        if status:
            query = query.where(AISuggestion.status == status)
        else:
            query = query.where(AISuggestion.status == "pending")
        query = query.order_by(AISuggestion.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_candidate(
        self,
        candidate_id: str,
        *,
        status: str | None = None,
    ) -> list[AISuggestion]:
        """List suggestions for a specific candidate."""
        query = select(AISuggestion).where(AISuggestion.candidate_id == candidate_id)
        if status:
            query = query.where(AISuggestion.status == status)
        else:
            query = query.where(AISuggestion.status == "pending")
        query = query.order_by(AISuggestion.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_pending_for_company(
        self,
        company_id: str,
        *,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        suggestion_type: str | None = None,
        limit: int = 50,
    ) -> list[AISuggestion]:
        """List pending suggestions with optional filters."""
        query = select(AISuggestion).where(
            AISuggestion.company_id == company_id,
            AISuggestion.status == "pending",
        )
        if candidate_id:
            query = query.where(AISuggestion.candidate_id == candidate_id)
        if vacancy_id:
            query = query.where(AISuggestion.vacancy_id == vacancy_id)
        if suggestion_type:
            query = query.where(AISuggestion.suggestion_type == suggestion_type)
        query = query.order_by(AISuggestion.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_pending_by_id_and_company(
        self,
        suggestion_id: str,
        company_id: str,
    ) -> AISuggestion | None:
        """Fetch a pending suggestion scoped to a company."""
        result = await self.db.execute(
            select(AISuggestion).where(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == company_id,
                AISuggestion.status == "pending",
            )
        )
        return result.scalar_one_or_none()
