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
