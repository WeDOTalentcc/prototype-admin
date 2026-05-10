"""
OpinionsRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/opinions.py.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy
from app.models.lia_opinion import LiaOpinion

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


    # ── Phase 2.5 / P1-LiaRepo + P1-Clobber methods ──────────────────────

    # Source priority for field-clobber guard (P1-Clobber fix).
    # text_screening < full_interview — never downgrade authority fields.
    _SOURCE_PRIORITY: dict[str, int] = {
        "cv_analysis": 0,
        "text_screening": 1,
        "full_interview": 2,
    }

    async def get_latest_for_candidate_company(
        self,
        candidate_id,
        company_id: str,
    ) -> "LiaOpinion | None":
        """P1-LiaRepo: most recent LiaOpinion for (candidate, company).

        Used by _record_bigfive_hire to read ocean_traits without inline
        SQL in the service (ADR-001 compliance).
        """
        result = await self.db.execute(
            select(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.company_id == str(company_id),
                )
            )
            .order_by(desc(LiaOpinion.created_at))
            .limit(1)
        )
        return result.scalars().first()

    async def get_latest_for_candidate_vacancy(
        self,
        candidate_id,
        vacancy_id,
        company_id: str,
    ) -> "LiaOpinion | None":
        """P1-LiaRepo: most recent is_current LiaOpinion for (candidate,
        vacancy, company).

        Used by upsert_ocean_opinion and _persist_lia_opinion_with_ocean.
        """
        result = await self.db.execute(
            select(LiaOpinion)
            .where(
                and_(
                    LiaOpinion.candidate_id == candidate_id,
                    LiaOpinion.job_vacancy_id == vacancy_id,
                    LiaOpinion.company_id == str(company_id),
                    LiaOpinion.is_current.is_(True),
                )
            )
            .order_by(desc(LiaOpinion.created_at))
            .limit(1)
        )
        return result.scalars().first()

    async def upsert_ocean_opinion(
        self,
        candidate_id,
        vacancy_id,
        company_id: str,
        ocean_traits: dict,
        overall_wsi: float,
        recommendation: str,
        summary: "str | None",
    ) -> "LiaOpinion":
        """P1-LiaRepo + P1-Clobber: upsert LiaOpinion(opinion_type='wsi')
        with OCEAN snapshot in behavioral_analysis['ocean_traits'].

        Field-clobber guard: source/wsi_score/recommendation are only
        overwritten when the existing source has SAME or LOWER priority
        than 'text_screening'. behavioral_analysis['ocean_traits'] is
        ALWAYS updated (new measurement data, not an authority field).

        Priority: cv_analysis(0) < text_screening(1) < full_interview(2).
        A full_interview opinion is never downgraded to text_screening.
        """
        from datetime import datetime as _dt

        existing = await self.get_latest_for_candidate_vacancy(
            candidate_id=candidate_id,
            vacancy_id=vacancy_id,
            company_id=company_id,
        )

        behavioral_blob: dict = {}
        if existing is not None:
            behavioral_blob = dict(existing.behavioral_analysis or {})
        # ocean_traits always updated (new measurement data)
        behavioral_blob["ocean_traits"] = ocean_traits

        if existing is not None:
            # P1-Clobber guard: only overwrite authority fields if new
            # source is NOT lower priority than existing.
            new_priority = self._SOURCE_PRIORITY.get("text_screening", 1)
            existing_priority = self._SOURCE_PRIORITY.get(
                existing.source or "cv_analysis", 0
            )
            existing.behavioral_analysis = behavioral_blob
            if new_priority >= existing_priority:
                existing.wsi_score = float(overall_wsi)
                existing.recommendation = recommendation
                existing.source = "text_screening"
            existing.updated_at = _dt.utcnow()
            return existing
        else:
            # P1-IsCurrentCoord: ensure only one is_current=True row per
            # (candidate, vacancy, opinion_type='wsi'). Without this, each
            # writer (screening, interview, etc.) can stack duplicate True rows.
            from uuid import UUID as _UUID

            def _to_uuid(v):
                if isinstance(v, _UUID):
                    return v
                try:
                    return _UUID(str(v))
                except (ValueError, AttributeError):
                    return v

            await self.mark_vacancy_opinions_non_current(
                candidate_id=_to_uuid(candidate_id),
                job_vacancy_id=_to_uuid(vacancy_id),
                opinion_type="wsi",
                company_id=_to_uuid(company_id),
            )
            from app.models.lia_opinion import LiaOpinion as _LiaOpinion
            opinion = _LiaOpinion(
                candidate_id=candidate_id,
                job_vacancy_id=vacancy_id,
                company_id=str(company_id),
                opinion_type="wsi",
                source="text_screening",
                wsi_score=float(overall_wsi),
                recommendation=recommendation,
                behavioral_analysis=behavioral_blob,
                summary=summary,
                is_current=True,
                version=1,
                created_by="screening_completed",
            )
            self.db.add(opinion)
            return opinion

    async def soft_delete(self, opinion: LiaOpinion) -> None:
        opinion.is_current = False
        await self.db.commit()
