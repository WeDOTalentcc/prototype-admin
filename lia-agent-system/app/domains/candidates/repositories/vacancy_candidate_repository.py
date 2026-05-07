"""
VacancyCandidateRepository — session-in-constructor pattern.
Covers all VacancyCandidate DB operations from app/api/v1/candidates.py.
"""
import logging
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import VacancyCandidate

logger = logging.getLogger(__name__)


class VacancyCandidateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_vacancy_and_candidate(
        self, vacancy_id: UUID, candidate_id: str | UUID
    ) -> VacancyCandidate | None:
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy_id,
                VacancyCandidate.candidate_id == (
                    uuid.UUID(str(candidate_id)) if isinstance(candidate_id, str) else candidate_id
                ),
            )
        )
        return result.scalar_one_or_none()

    async def get_most_recent_for_candidate(
        self, candidate_id: str | UUID
    ) -> VacancyCandidate | None:
        result = await self.db.execute(
            select(VacancyCandidate)
            .where(
                VacancyCandidate.candidate_id == (
                    uuid.UUID(str(candidate_id)) if isinstance(candidate_id, str) else candidate_id
                )
            )
            .order_by(VacancyCandidate.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_for_candidate_and_job(
        self,
        candidate_id: str,
        job_vacancy_id: str | None,
    ) -> VacancyCandidate | None:
        """
        Find VacancyCandidate by candidate + optional job.
        Falls back to most-recent if job_vacancy_id is None or invalid UUID.
        """
        if job_vacancy_id:
            try:
                vacancy_uuid = uuid.UUID(str(job_vacancy_id))
                vc = await self.get_by_vacancy_and_candidate(vacancy_uuid, candidate_id)
                if vc:
                    return vc
            except ValueError:
                logger.warning(
                    f"Invalid job_vacancy_id format: {job_vacancy_id} — falling back to most recent"
                )
        return await self.get_most_recent_for_candidate(candidate_id)

    async def update(self, vacancy_candidate: VacancyCandidate) -> VacancyCandidate:
        await self.db.commit()
        await self.db.refresh(vacancy_candidate)
        return vacancy_candidate

    # ── Cross-domain reads (used by automation_handlers — ADR-001) ──────────

    async def get_by_vacancy_candidate_and_company(
        self,
        vacancy_id: str | UUID,
        candidate_id: str | UUID,
        company_id: str | UUID,
    ) -> VacancyCandidate | None:
        """Multi-tenant lookup of a VacancyCandidate triple.

        Used by automation handlers' multi-tenancy validation.
        """
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.candidate_id == candidate_id,
                VacancyCandidate.vacancy_id == vacancy_id,
                VacancyCandidate.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_awaiting_screening_for_vacancy(
        self,
        vacancy_id: str | UUID,
        limit: int = 1,
    ) -> list[VacancyCandidate]:
        """Return queued candidates ordered by lia_score DESC, created_at ASC.

        Used by automation_handlers.process_screening_queue (slot promotion).
        """
        from sqlalchemy import and_

        result = await self.db.execute(
            select(VacancyCandidate)
            .where(
                and_(
                    VacancyCandidate.vacancy_id == vacancy_id,
                    VacancyCandidate.status == "awaiting_screening",
                )
            )
            .order_by(
                VacancyCandidate.lia_score.desc().nullslast(),
                VacancyCandidate.created_at.asc(),
            )
            .limit(limit)
        )
        return list(result.scalars().all())
