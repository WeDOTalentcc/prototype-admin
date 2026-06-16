"""
Outcome Tracker Service - Records job closure outcomes for learning.

Captures structured data when a job is closed (filled, cancelled, expired)
and feeds it into the feedback learning pipeline for continuous improvement.
"""
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.job_management.repositories.job_vacancy_crud_repository import JobVacancyCRUDRepository

from lia_models.candidate import VacancyCandidate
from lia_models.feedback_learning import JobOutcome, JobOutcomeType
from lia_models.job_vacancy import JobVacancy
from app.domains.analytics.services.feedback_learning_service import FeedbackLearningService

logger = logging.getLogger(__name__)

REASON_TO_OUTCOME = {
    "filled": JobOutcomeType.FILLED,
    "cancelled": JobOutcomeType.CANCELLED,
    "budget": JobOutcomeType.CANCELLED,
    "on_hold": JobOutcomeType.CANCELLED,
    "expired": JobOutcomeType.EXPIRED,
    "reposted": JobOutcomeType.REPOSTED,
    "other": JobOutcomeType.CANCELLED,
}


class OutcomeTracker:
    """Tracks job closure outcomes and feeds learning pipeline."""

    def __init__(self):
        self._feedback_service = FeedbackLearningService()

    async def record_job_close(
        self,
        job_id: str,
        company_id: str,
        reason: str,
        hired_candidate_id: str | None,
        db: AsyncSession,
    ) -> JobOutcome | None:
        """
        Record structured outcome data when a job is closed.

        Args:
            job_id: UUID string of the closed job
            company_id: Company that owns the job
            reason: Close reason (filled, cancelled, budget, etc.)
            hired_candidate_id: Candidate hired (if filled)
            db: Active async database session

        Returns:
            Created JobOutcome record or None on failure
        """
        try:
            job = await self._fetch_job(db, job_id)
            if not job:
                logger.warning(f"OutcomeTracker: job {job_id} not found, skipping")
                return None

            outcome_type = REASON_TO_OUTCOME.get(reason, JobOutcomeType.CANCELLED)
            time_to_fill = self._calc_time_to_fill(job)
            pipeline_stats = await self._fetch_pipeline_stats(db, job_id)
            skills = self._extract_skills(job)
            salary_min, salary_max = self._extract_salary(job)

            job_outcome = await self._feedback_service.record_outcome(
                db=db,
                company_id=company_id,
                job_id=UUID(job_id),
                outcome=outcome_type,
                time_to_fill_days=time_to_fill,
                salary_initial_min=salary_min,
                salary_initial_max=salary_max,
                candidate_count_total=pipeline_stats["total"],
                candidate_count_screened=pipeline_stats["screened"],
                candidate_count_interviewed=pipeline_stats["interviewed"],
                candidate_count_offered=pipeline_stats["offered"],
                role=getattr(job, "title", None),
                seniority=getattr(job, "seniority_level", None),
                department=getattr(job, "department", None),
                location=getattr(job, "location", None),
                work_model=getattr(job, "work_model", None),
                skills_used=skills,
                notes=f"Close reason: {reason}. Hired candidate: {hired_candidate_id or 'N/A'}",
            )

            logger.info(
                f"OutcomeTracker: recorded outcome '{outcome_type.value}' for job {job_id} "
                f"(ttf={time_to_fill}d, candidates={pipeline_stats['total']})"
            )

            return job_outcome

        except Exception as e:
            logger.error(f"OutcomeTracker: failed to record outcome for job {job_id}: {e}", exc_info=True)
            return None

    async def _fetch_job(self, db: AsyncSession, job_id: str) -> JobVacancy | None:
        return await JobVacancyCRUDRepository(db).get_by_id_only_uuid(UUID(job_id))

    def _calc_time_to_fill(self, job: JobVacancy) -> int | None:
        open_date = getattr(job, "open_date", None) or getattr(job, "created_at", None)
        if not open_date:
            return None
        delta = datetime.utcnow() - open_date
        return max(delta.days, 0)

    async def _fetch_pipeline_stats(self, db: AsyncSession, job_id: str) -> dict:
        stats = {"total": 0, "screened": 0, "interviewed": 0, "offered": 0}
        try:
            job_uuid = UUID(job_id)

            total_result = await db.execute(
                select(func.count()).select_from(VacancyCandidate).where(
                    VacancyCandidate.vacancy_id == job_uuid
                )
            )
            stats["total"] = total_result.scalar() or 0

            screened_result = await db.execute(
                select(func.count()).select_from(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == job_uuid,
                        VacancyCandidate.stage.in_(["screening", "screened", "triagem", "triado"]),
                    )
                )
            )
            stats["screened"] = screened_result.scalar() or 0

            interviewed_result = await db.execute(
                select(func.count()).select_from(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == job_uuid,
                        VacancyCandidate.stage.in_(["interview", "interviewed", "entrevista", "entrevistado"]),
                    )
                )
            )
            stats["interviewed"] = interviewed_result.scalar() or 0

            offered_result = await db.execute(
                select(func.count()).select_from(VacancyCandidate).where(
                    and_(
                        VacancyCandidate.vacancy_id == job_uuid,
                        VacancyCandidate.stage.in_(["offer", "offered", "proposta", "oferta", "hired", "contratado"]),
                    )
                )
            )
            stats["offered"] = offered_result.scalar() or 0

        except Exception as e:
            logger.warning(f"OutcomeTracker: failed to fetch pipeline stats for {job_id}: {e}")

        return stats

    def _extract_skills(self, job: JobVacancy) -> list:
        additional = getattr(job, "additional_data", None) or {}
        skills = additional.get("skills", []) if isinstance(additional, dict) else []
        tech_reqs = getattr(job, "technical_requirements", None) or []
        for req in tech_reqs:
            if isinstance(req, dict) and req.get("technology"):
                skills.append(req["technology"])
        return skills

    def _extract_salary(self, job: JobVacancy) -> tuple:
        salary_range = getattr(job, "salary_range", None)
        if isinstance(salary_range, dict):
            return salary_range.get("min"), salary_range.get("max")
        return None, None


outcome_tracker = OutcomeTracker()
