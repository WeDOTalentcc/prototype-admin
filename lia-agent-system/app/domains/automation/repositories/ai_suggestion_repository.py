"""
AISuggestion Repository — data access layer for automation AI suggestions.
Extracted from app/api/v1/automation/suggestions.py as part of Phase 2 refactor.

Multi-tenancy fail-closed: every method that fetches/lists AISuggestion rows
requires company_id and applies `AISuggestion.company_id == company_id` filter.
Callers must source company_id from JWT/session context (never request body).
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

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        """Fail-closed multi-tenancy guard."""
        if not company_id:
            raise ValueError(
                "company_id is required for fail-closed multi-tenancy "
                "(never trust company_id from request body)"
            )
        return str(company_id)

    async def list_for_company(
        self,
        company_id: str,
        *,
        status: str | None = None,
        suggestion_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AISuggestion], int]:
        cid = self._require_company_id(company_id)
        q = select(AISuggestion).where(AISuggestion.company_id == cid)
        if status:
            q = q.where(AISuggestion.status == status)
        if suggestion_type:
            q = q.where(AISuggestion.suggestion_type == suggestion_type)
        q = q.order_by(AISuggestion.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(q)
        items = list(result.scalars().all())

        cq = select(func.count(AISuggestion.id)).where(AISuggestion.company_id == cid)
        total = (await self.db.execute(cq)).scalar() or 0
        return items, total

    async def get_by_id(
        self, suggestion_id: UUID, *, company_id: str
    ) -> AISuggestion | None:
        """Get suggestion by id scoped to company (fail-closed multi-tenancy)."""
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(AISuggestion).where(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == cid,
            )
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
        company_id: str,
        status: str | None = None,
    ) -> list[AISuggestion]:
        """List suggestions for a specific vacancy (scoped to company)."""
        cid = self._require_company_id(company_id)
        query = select(AISuggestion).where(
            AISuggestion.vacancy_id == vacancy_id,
            AISuggestion.company_id == cid,
        )
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
        company_id: str,
        status: str | None = None,
    ) -> list[AISuggestion]:
        """List suggestions for a specific candidate (scoped to company)."""
        cid = self._require_company_id(company_id)
        query = select(AISuggestion).where(
            AISuggestion.candidate_id == candidate_id,
            AISuggestion.company_id == cid,
        )
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
        cid = self._require_company_id(company_id)
        query = select(AISuggestion).where(
            AISuggestion.company_id == cid,
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
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(AISuggestion).where(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == cid,
                AISuggestion.status == "pending",
            )
        )
        return result.scalar_one_or_none()
