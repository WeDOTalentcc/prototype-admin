"""Interview repository (ADR-001 canonical example for Sprint 5.8).

Extracts the `select(Interview)` query from
`interview_intelligence/services/feedback_generator_service.py:generate`
into a canonical repository per ADR-001.

Sprint 5.8 example for the `interview_intelligence` zero-repo domain
(parallels Sprint 5.4's `ConversationMemoryRepository` for
`recruiter_assistant`).
"""
from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.interview import Interview

logger = logging.getLogger(__name__)


class InterviewRepository:
    """Persistence access for Interview rows.

    Multi-tenancy invariant (CLAUDE.md REGRA 1): every public method
    enforces `_require_company_id` fail-closed.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _require_company_id(company_id: UUID | str) -> None:
        if not company_id:
            raise ValueError(
                "Multi-tenancy invariant violation: company_id required for "
                "InterviewRepository operations (ADR-001 + REGRA 1)"
            )

    async def get_for_company(
        self,
        *,
        interview_id: UUID | str,
        company_id: UUID | str,
    ) -> Interview | None:
        """Return the Interview row scoped to (company_id, interview_id).

        Returns None if not found (NOT raising) — caller decides handling.
        """
        self._require_company_id(company_id)

        stmt = select(Interview).where(
            and_(
                Interview.id == interview_id,
                Interview.company_id == company_id,
            )
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_vacancy_peers_with_transcript(
        self,
        *,
        job_vacancy_id: UUID | str,
        company_id: UUID | str,
        exclude_id: UUID | str,
        limit: int = 20,
    ) -> list[Interview]:
        """Peer interviews on the same vacancy, transcript present, completed/transcribed."""
        self._require_company_id(company_id)
        stmt = (
            select(Interview)
            .where(
                and_(
                    Interview.job_vacancy_id == job_vacancy_id,
                    Interview.company_id == company_id,
                    Interview.id != exclude_id,
                    Interview.transcript.isnot(None),
                    Interview.status.in_(["completed", "transcribed"]),
                )
            )
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def list_with_transcript_for_candidates(
        self,
        *,
        candidate_ids: list,
        company_id: UUID | str,
        exclude_id: UUID | str,
        limit: int = 10,
    ) -> list[Interview]:
        """Interviews for any candidate in candidate_ids, transcript present, completed/transcribed."""
        self._require_company_id(company_id)
        if not candidate_ids:
            return []
        stmt = (
            select(Interview)
            .where(
                and_(
                    Interview.candidate_id.in_(candidate_ids),
                    Interview.company_id == company_id,
                    Interview.id != exclude_id,
                    Interview.transcript.isnot(None),
                    Interview.status.in_(["completed", "transcribed"]),
                )
            )
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id_unscoped(self, interview_id: UUID | str) -> Interview | None:
        """Lookup by id without company filter (admin/transcription pipeline trusts
        interview_id origin and applies its own tenant scoping)."""
        stmt = select(Interview).where(Interview.id == interview_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()
