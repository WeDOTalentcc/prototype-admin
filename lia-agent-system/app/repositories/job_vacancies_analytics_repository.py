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
        """List candidates de uma vacancy.

        TENANT-EXEMPT: vacancy_id eh sempre derivado de get_job_by_id_and_company
        (L25-35 acima) que faz tenant gate; caller eh tenant-gated upstream.
        """
        # TENANT-EXEMPT: vacancy_id ja tenant-gated upstream via get_job_by_id_and_company
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy_id
            )
        )
        return list(result.scalars().all())

    async def get_stage_history_for_vacancy(
        self, vacancy_id: UUID
    ) -> list[CandidateStageHistory]:
        """List stage history de uma vacancy.

        TENANT-EXEMPT: vacancy_id eh tenant-gated upstream via get_job_by_id_and_company.
        """
        # TENANT-EXEMPT: vacancy_id ja tenant-gated upstream
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

    async def get_candidate_counts_by_vacancy_for_company(
        self, company_id: str
    ) -> dict[str, int]:
        """Live count of VacancyCandidate rows per vacancy for the given company.

        Single aggregate query that joins VacancyCandidate to JobVacancy and
        filters by JobVacancy.company_id, so multi-tenant isolation is enforced
        by the JOIN itself (Task #439 contract). The lifecycle-overview endpoint
        consumes this to report real candidate counts instead of the stale
        ``JobVacancy.funnel_data['total']`` cache.
        """
        result = await self.db.execute(
            select(
                VacancyCandidate.vacancy_id,
                func.count(VacancyCandidate.id).label("count"),
            )
            .join(JobVacancy, JobVacancy.id == VacancyCandidate.vacancy_id)
            .where(JobVacancy.company_id == company_id)
            .group_by(VacancyCandidate.vacancy_id)
        )
        return {str(row.vacancy_id): int(row.count) for row in result.all()}

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
        """Top N candidates by lia_score.

        TENANT-EXEMPT: vacancy_id eh tenant-gated upstream via get_job_by_id_and_company.
        """
        # TENANT-EXEMPT: vacancy_id ja tenant-gated upstream
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
                    AVG(CASE WHEN (salary_range->>'max')::int > 0 THEN (salary_range->>'max')::int ELSE NULL END)::int as avg_salary
                FROM job_vacancies
                WHERE company_id = :co
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
                WHERE company_id = :co
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
                WHERE company_id = :co
                  AND created_at >= NOW() - (:days || ' days')::interval
                GROUP BY location, work_model
                ORDER BY total DESC
                LIMIT 20
            """),
            {"co": company_id, "days": str(days)},
        )
        return result.fetchall()

    async def get_pipeline_overview(self, company_id: str) -> list:
        """
        Return cross-vacancy stage counts for active vacancies.
        Each row has: stage (str), count (int), candidate_names (list[str])
        grouped by stage across all active vacancies in the company.
        """
        result = await self.db.execute(
            text("""
                SELECT
                    vc.stage,
                    COUNT(vc.id) AS count,
                    ARRAY_AGG(c.name ORDER BY vc.created_at DESC) AS candidate_names,
                    ARRAY_AGG(vc.id::text ORDER BY vc.created_at DESC) AS vc_ids,
                    ARRAY_AGG(vc.vacancy_id::text ORDER BY vc.created_at DESC) AS vacancy_ids
                FROM vacancy_candidates vc
                JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                JOIN candidates c ON c.id = vc.candidate_id
                WHERE jv.company_id = :co
                  AND LOWER(jv.status) IN ('ativa', 'active', 'open', 'published', 'publicada', 'em andamento')
                  AND vc.stage IS NOT NULL
                  AND vc.stage NOT IN ('rejected', 'declined', 'withdrawn', 'cancelado', 'reprovado')
                GROUP BY vc.stage
                ORDER BY count DESC
            """),
            {"co": company_id},
        )
        return result.fetchall()

    async def get_pipeline_overview_enriched(self, company_id: str, candidates_per_stage: int = 100) -> list:
        """
        Return enriched per-candidate data for active vacancies, including
        scores from test_results, lia_opinions, vacancy title, sub_status, and stage_entered_at.
        Uses ROW_NUMBER to cap enriched rows per stage at candidates_per_stage,
        while still computing accurate total counts.
        Returns one row per vacancy_candidate (capped), plus a _total_count column.
        """
        result = await self.db.execute(
            text("""
                WITH base AS (
                    SELECT
                        vc.id AS vc_uuid,
                        vc.vacancy_id,
                        vc.candidate_id,
                        vc.stage,
                        vc.status AS sub_status,
                        vc.lia_score,
                        vc.match_percentage,
                        vc.stage_entered_at,
                        vc.created_at,
                        c.name AS candidate_name,
                        jv.title AS vacancy_title,
                        ROW_NUMBER() OVER (PARTITION BY vc.stage ORDER BY vc.created_at DESC) AS rn,
                        COUNT(*) OVER (PARTITION BY vc.stage) AS stage_total
                    FROM vacancy_candidates vc
                    JOIN job_vacancies jv ON jv.id = vc.vacancy_id
                    JOIN candidates c ON c.id = vc.candidate_id
                    WHERE jv.company_id = :co
                      AND LOWER(jv.status) IN ('ativa', 'active', 'open', 'published', 'publicada', 'em andamento')
                      AND vc.stage IS NOT NULL
                      AND vc.stage NOT IN ('rejected', 'declined', 'withdrawn', 'cancelado', 'reprovado')
                )
                SELECT
                    b.vc_uuid::text AS vc_id,
                    b.vacancy_id::text AS vacancy_id,
                    b.candidate_id::text AS candidate_id,
                    b.candidate_name,
                    b.stage,
                    b.sub_status,
                    b.lia_score,
                    b.match_percentage,
                    b.stage_entered_at,
                    b.vacancy_title,
                    b.rn,
                    b.stage_total,
                    lo.wsi_score AS wsi_score,
                    lo.score AS lia_opinion_score,
                    lo.score_breakdown AS score_breakdown,
                    tr_tech.score AS technical_test_score,
                    tr_eng.score AS english_test_score,
                    lo_b5.ocean_traits AS big_five_data
                FROM base b
                LEFT JOIN LATERAL (
                    SELECT lo2.wsi_score, lo2.score, lo2.score_breakdown
                    FROM lia_opinions lo2
                    WHERE lo2.candidate_id = b.candidate_id
                      AND (lo2.job_vacancy_id = b.vacancy_id OR lo2.job_vacancy_id IS NULL)
                    ORDER BY (lo2.job_vacancy_id = b.vacancy_id) DESC, lo2.created_at DESC
                    LIMIT 1
                ) lo ON true
                LEFT JOIN LATERAL (
                    SELECT tr2.score
                    FROM test_results tr2
                    JOIN technical_tests tt2 ON tt2.id = tr2.test_id
                    WHERE tr2.candidate_id = b.candidate_id
                      AND tt2.category = 'coding'
                    ORDER BY tr2.created_at DESC
                    LIMIT 1
                ) tr_tech ON true
                LEFT JOIN LATERAL (
                    SELECT tr3.score
                    FROM test_results tr3
                    JOIN technical_tests tt3 ON tt3.id = tr3.test_id
                    WHERE tr3.candidate_id = b.candidate_id
                      AND tt3.category = 'domain_specific'
                    ORDER BY tr3.created_at DESC
                    LIMIT 1
                ) tr_eng ON true
                LEFT JOIN LATERAL (
                    SELECT lo3.behavioral_analysis->'ocean_traits' AS ocean_traits
                    FROM lia_opinions lo3
                    WHERE lo3.candidate_id = b.candidate_id
                      AND (lo3.job_vacancy_id = b.vacancy_id OR lo3.job_vacancy_id IS NULL)
                      AND lo3.is_current = true
                    ORDER BY (lo3.job_vacancy_id = b.vacancy_id) DESC, lo3.created_at DESC
                    LIMIT 1
                ) lo_b5 ON true
                WHERE b.rn <= :limit
                ORDER BY b.stage, b.created_at DESC
            """),
            {"co": company_id, "limit": candidates_per_stage},
        )
        return result.fetchall()
