"""
OpinionsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/opinions.py.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_vacancy import JobVacancy
from lia_models.lia_opinion import LiaOpinion

logger = logging.getLogger(__name__)


class OpinionsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Job vacancy helper ─────────────────────────────────────────────────

    async def get_job_title(self, job_vacancy_id: UUID) -> str | None:
        result = await self.db.execute(
            select(JobVacancy.title).where(JobVacancy.id == job_vacancy_id)
        )
        return result.scalar_one_or_none()

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_current_by_candidate(
        self, candidate_id: UUID, company_id: UUID
    ) -> list[LiaOpinion]:
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            ).order_by(desc(LiaOpinion.created_at))
        )
        return list(result.scalars().all())

    async def get_history_by_candidate(
        self, candidate_id: UUID, company_id: UUID
    ) -> list[LiaOpinion]:
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == company_id,
                )
            ).order_by(desc(LiaOpinion.created_at))
        )
        return list(result.scalars().all())

    async def list_with_filters(
        self,
        candidate_id: UUID,
        company_id: UUID,
        opinion_type: str | None = None,
        job_vacancy_id: UUID | None = None,
        include_history: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LiaOpinion], int]:
        conditions = [
            LiaOpinion.candidate_id == candidate_id,
            LiaOpinion.company_id == company_id,
        ]

        if not include_history:
            conditions.append(LiaOpinion.is_current)

        if opinion_type:
            conditions.append(LiaOpinion.opinion_type == opinion_type)

        if job_vacancy_id:
            conditions.append(LiaOpinion.job_vacancy_id == job_vacancy_id)

        # Count total
        count_result = await self.db.execute(
            select(LiaOpinion).where(and_(*conditions))
        )
        total = len(count_result.scalars().all())

        # Paginated fetch
        result = await self.db.execute(
            select(LiaOpinion).where(and_(*conditions))
            .order_by(desc(LiaOpinion.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(
        self, opinion_id: UUID, company_id: UUID
    ) -> LiaOpinion | None:
        result = await self.db.execute(
            select(LiaOpinion).where(
                and_(
                    LiaOpinion.id == opinion_id,
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ── Version helpers ────────────────────────────────────────────────────

    async def get_max_version_for_vacancy(
        self,
        candidate_id: UUID,
        job_vacancy_id: UUID,
        opinion_type: str,
        company_id: UUID,
    ) -> int | None:
        result = await self.db.execute(
            select(func.max(LiaOpinion.version)).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == job_vacancy_id,
                    LiaOpinion.opinion_type == opinion_type,
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_max_version_general(
        self,
        candidate_id: UUID,
        company_id: UUID,
    ) -> int | None:
        result = await self.db.execute(
            select(func.max(LiaOpinion.version)).where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.opinion_type == "general",
                    LiaOpinion.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ── Write ──────────────────────────────────────────────────────────────

    async def mark_vacancy_opinions_non_current(
        self,
        candidate_id: UUID,
        job_vacancy_id: UUID,
        opinion_type: str,
        company_id: UUID,
    ) -> None:
        await self.db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == job_vacancy_id,
                    LiaOpinion.opinion_type == opinion_type,
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            )
            .values(is_current=False)
        )

    async def mark_general_opinions_non_current(
        self,
        candidate_id: UUID,
        company_id: UUID,
    ) -> None:
        await self.db.execute(
            update(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.opinion_type == "general",
                    LiaOpinion.company_id == company_id,
                    LiaOpinion.is_current,
                )
            )
            .values(is_current=False)
        )

    async def create(self, opinion: LiaOpinion) -> LiaOpinion:
        self.db.add(opinion)
        await self.db.commit()
        await self.db.refresh(opinion)
        return opinion

    async def update(self, opinion: LiaOpinion) -> LiaOpinion:
        await self.db.commit()
        await self.db.refresh(opinion)
        return opinion

    async def soft_delete(self, opinion: LiaOpinion) -> None:
        opinion.is_current = False
        await self.db.commit()
