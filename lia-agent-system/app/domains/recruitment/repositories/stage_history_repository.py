"""
StageHistoryRepository — persistence layer for candidate stage history.
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# CandidateStageHistory may not be in the shim; import gracefully
try:
    from app.models.recruitment_stages import CandidateStageHistory
    _HAS_HISTORY_MODEL = True
except ImportError:
    _HAS_HISTORY_MODEL = False
    CandidateStageHistory = None  # type: ignore[assignment,misc]


class StageHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_candidate(
        self,
        candidate_id: UUID | str,
        vacancy_id: UUID | str | None = None,
    ) -> list:
        if not _HAS_HISTORY_MODEL or CandidateStageHistory is None:
            return []
        query = select(CandidateStageHistory).where(
            CandidateStageHistory.candidate_id == candidate_id
        )
        if vacancy_id is not None:
            query = query.where(CandidateStageHistory.vacancy_id == vacancy_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict):
        if not _HAS_HISTORY_MODEL or CandidateStageHistory is None:
            return None
        record = CandidateStageHistory(**data)
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record
