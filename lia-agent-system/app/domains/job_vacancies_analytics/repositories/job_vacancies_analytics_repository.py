"""
JobVacanciesAnalyticsRepository — session-in-constructor pattern.
Covers all DB operations for job vacancies analytics routes.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate, VacancyCandidate
from app.models.job_vacancy import JobVacancy
from app.models.recruitment_stages import CandidateStageHistory

logger = logging.getLogger(__name__)


class JobVacanciesAnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ─── Shared: fetch a single job by id + company ──────────────────────────

    async def get_job_by_id_and_company(
        self, job_id: UUID, company_id: str
    ) -> JobVacancy | None:
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.id == job_id,
                    JobVacancy.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    # ─── Metrics ─────────────────────────────────────────────────────────────

    async def get_stage_counts_for_vacancy(
        self, vacancy_id: UUID
    ) -> dict[str, int]:
        """Return {stage: count} for a vacancy."""
        result = await self.db.execute(
            select(
                VacancyCandidate.stage,
                func.count(VacancyCandidate.id).label("count"),
            )
            .where(VacancyCandidate.vacancy_id == vacancy_id)
            .group_by(VacancyCandidate.stage)
        )
        return {row.stage: row.count for row in result.all()}

    async def get_total_candidates_for_vacancy(self, vacancy_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == vacancy_id
            )
        )
        return result.scalar() or 0

    async def get_source_counts_for_vacancy(
        self, vacancy_id: UUID
    ) -> dict[str, int]:
        """Return {source: count} for a vacancy."""
        result = await self.db.execute(
            select(
                VacancyCandidate.source,
                func.count(VacancyCandidate.id).label("count"),
            )
            .where(VacancyCandidate.vacancy_id == vacancy_id)
            .group_by(VacancyCandidate.source)
        )
        return {row.source: row.count for row in result.all()}

    async def get_applications_since(
        self, vacancy_id: UUID, since: datetime
    ) -> int:
        result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(
                and_(
                    VacancyCandidate.vacancy_id == vacancy_id,
                    VacancyCandidate.created_at >= since,
                )
            )
        )
        return result.scalar() or 0

    async def get_last_activity_for_vacancy(
        self, vacancy_id: UUID
    ) -> datetime | None:
        result = await self.db.execute(
            select(func.max(VacancyCandidate.updated_at)).where(
                VacancyCandidate.vacancy_id == vacancy_id
            )
        )
        return result.scalar()

    # ─── Deep Analytics ───────────────────────────────────────────────────────

    async def get_all_vacancy_candidates(
        self, vacancy_id: UUID
    ) -> list[VacancyCandidate]:
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy_id
            )
        )
        return list(result.scalars().all())

    async def get_stage_history_for_vacancy(
        self, vacancy_id: UUID
    ) -> list[CandidateStageHistory]:
        result = await self.db.execute(
            select(CandidateStageHistory)
            .where(CandidateStageHistory.vacancy_id == vacancy_id)
            .order_by(CandidateStageHistory.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_daily_applications(
        self, vacancy_id: UUID, since: datetime
    ) -> list:
        """Return rows with .date (str) and .count (int)."""
        result = await self.db.execute(
            select(
                func.date(VacancyCandidate.created_at).label("date"),
                func.count(VacancyCandidate.id).label("count"),
            )
            .where(
                and_(
                    VacancyCandidate.vacancy_id == vacancy_id,
                    VacancyCandidate.created_at >= since,
                )
            )
            .group_by(func.date(VacancyCandidate.created_at))
            .order_by(func.date(VacancyCandidate.created_at))
        )
        return result.all()

    async def get_applications_in_range(
        self,
        vacancy_id: UUID,
        start: datetime,
        end: datetime | None = None,
    ) -> int:
        conditions = [
            VacancyCandidate.vacancy_id == vacancy_id,
            VacancyCandidate.created_at >= start,
        ]
        if end is not None:
            conditions.append(VacancyCandidate.created_at < end)
        result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(and_(*conditions))
        )
        return result.scalar() or 0

    async def get_completed_jobs_for_company(
        self, company_id: str
    ) -> list[JobVacancy]:
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(
                    JobVacancy.company_id == company_id,
                    JobVacancy.status.in_(["Concluída", "Encerrada"]),
                )
            )
        )
        return list(result.scalars().all())

    # ─── Stats Overview ───────────────────────────────────────────────────────

    async def get_all_company_jobs(
        self, company_id: str
    ) -> list[JobVacancy]:
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.company_id == company_id)
        )
        return list(result.scalars().all())

    # ─── Job Report ──────────────────────────────────────────────────────────

    async def get_avg_time_to_hire(self, vacancy_id: UUID) -> float | None:
        """Average hours in previous stage for candidates reaching hired/contratado."""
        try:
            result = await self.db.execute(
                select(
                    func.avg(CandidateStageHistory.time_in_previous_stage_hours)
                ).where(
                    and_(
                        CandidateStageHistory.vacancy_id == vacancy_id,
                        CandidateStageHistory.to_stage_name.in_(
                            ["hired", "contratado"]
                        ),
                    )
                )
            )
            return result.scalar()
        except Exception:
            return None

    async def get_top_candidates_with_score(
        self, vacancy_id: UUID, limit: int = 5
    ) -> list[tuple[VacancyCandidate, Candidate]]:
        result = await self.db.execute(
            select(VacancyCandidate, Candidate)
            .join(Candidate, VacancyCandidate.candidate_id == Candidate.id)
            .where(
                and_(
                    VacancyCandidate.vacancy_id == vacancy_id,
                    VacancyCandidate.lia_score.isnot(None),
                )
            )
            .order_by(VacancyCandidate.lia_score.desc())
            .limit(limit)
        )
        return list(result.all())

    # ─── Work-Model Analytics ────────────────────────────────────────────────

    async def get_work_model_distribution(
        self, company_id: str, days: int
    ) -> list:
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(work_model, 'Não informado') as work_model,
                    COUNT(*) as total,
                    AVG(CASE WHEN salary_max > 0 THEN salary_max ELSE NULL END)::int as avg_salary
                FROM job_vacancies
                WHERE company_id = CAST(:co AS uuid)
                  AND created_at >= NOW() - (:days || ' days')::interval
                GROUP BY COALESCE(work_model, 'Não informado')
                ORDER BY total DESC
            """),
            {"co": company_id, "days": str(days)},
        )
        return result.fetchall()

    async def get_work_model_by_title(
        self, company_id: str, days: int
    ) -> list:
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(title, 'Sem título') as title,
                    COALESCE(work_model, 'Não informado') as work_model,
                    COUNT(*) as total
                FROM job_vacancies
                WHERE company_id = CAST(:co AS uuid)
                  AND created_at >= NOW() - (:days || ' days')::interval
                GROUP BY title, work_model
                ORDER BY total DESC
                LIMIT 10
            """),
            {"co": company_id, "days": str(days)},
        )
        return result.fetchall()

    async def get_work_model_by_location(
        self, company_id: str, days: int
    ) -> list:
        result = await self.db.execute(
            text("""
                SELECT
                    COALESCE(location, 'Não informado') as location,
                    COALESCE(work_model, 'Não informado') as work_model,
                    COUNT(*) as total
                FROM job_vacancies
                WHERE company_id = CAST(:co AS uuid)
                  AND created_at >= NOW() - (:days || ' days')::interval
                GROUP BY location, work_model
                ORDER BY total DESC
                LIMIT 20
            """),
            {"co": company_id, "days": str(days)},
        )
        return result.fetchall()
