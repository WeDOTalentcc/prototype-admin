"""
Interview Repository - encapsulates all database access for the interview scheduling domain.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.candidate import Candidate
from app.models.interview import Interview, InterviewFeedback
from app.models.job_vacancy import JobVacancy


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Candidate helpers
    # ------------------------------------------------------------------

    async def get_candidate_by_id(
        self,
        candidate_id: uuid.UUID,
        company_id: str | None = None,
    ) -> Optional[Candidate]:
        """Get candidate by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Candidate.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Candidate).where(Candidate.id == candidate_id)
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Interview CRUD
    # ------------------------------------------------------------------

    async def get_interview_by_id(
        self,
        interview_id: str,
        company_id: str | None = None,
    ) -> Optional[Interview]:
        """Get interview by id. Multi-tenancy defense-in-depth via company_id
        filter quando passado (REGRA ZERO + harness B.1)."""
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Interview).where(Interview.id == interview_id)
        if company_id:
            query = query.where(Interview.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_interview(self, interview: Interview) -> Interview:
        self.db.add(interview)
        await self.db.flush()
        await self.db.refresh(interview)
        return interview

    async def commit(self) -> None:
        await self.db.commit()

    async def list_interviews(
        self,
        status: Optional[str] = None,
        candidate_email: Optional[str] = None,
        interviewer_email: Optional[str] = None,
        job_vacancy_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 50,
    ):
        """Return list of (Interview, job_code, job_manager) tuples."""
        jv = aliased(JobVacancy)
        # TENANT-EXEMPT: Interview.company_id == company_id é appended em
        # `filters` abaixo quando company_id passado. Sensor AST não rastreia
        # through list-builder pattern.
        query = select(Interview, jv.job_id, jv.manager).outerjoin(
            jv, Interview.job_vacancy_id == jv.id
        )

        filters = []
        if status:
            filters.append(Interview.status == status)
        if candidate_email:
            filters.append(Interview.candidate_email == candidate_email)
        if interviewer_email:
            filters.append(Interview.interviewer_email == interviewer_email)
        if job_vacancy_id:
            import uuid as _uuid
            filters.append(Interview.job_vacancy_id == _uuid.UUID(job_vacancy_id))
        if candidate_id:
            import uuid as _uuid
            filters.append(Interview.candidate_id == _uuid.UUID(candidate_id))
        if company_id:
            filters.append(Interview.company_id == company_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(Interview.start_time.desc()).limit(limit)

        result = await self.db.execute(query)
        return result.all()

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    async def add_feedback(self, feedback: InterviewFeedback) -> None:
        self.db.add(feedback)

    # ------------------------------------------------------------------
    # Recruitment stage helpers
    # ------------------------------------------------------------------

    async def get_recruitment_stage(
        self, stage_uuid: uuid.UUID, company_id: Optional[str] = None
    ):
        from app.domains.automation.models.recruitment_stages import RecruitmentStage

        # TENANT-EXEMPT: dynamic builder — RecruitmentStage.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(RecruitmentStage).where(RecruitmentStage.id == stage_uuid)
        if company_id:
            query = query.where(RecruitmentStage.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_interview_stages(self, company_id: str):
        from app.domains.automation.models.recruitment_stages import RecruitmentStage

        result = await self.db.execute(
            select(RecruitmentStage)
            .where(
                and_(
                    RecruitmentStage.company_id == company_id,
                    RecruitmentStage.is_active.is_(True),
                    RecruitmentStage.is_initial.is_(False),
                    RecruitmentStage.is_final.is_(False),
                    RecruitmentStage.is_rejection.is_(False),
                    RecruitmentStage.is_hired.is_(False),
                )
            )
            .order_by(RecruitmentStage.stage_order)
        )
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Sourcing pipeline helpers (Sprint Q2 ADR-001 cross-domain cleanup)
    # Used by app/domains/sourcing/services/sourcing_pipeline_service.py
    # ------------------------------------------------------------------

    async def count_distinct_candidates_for_job(
        self,
        job_vacancy_id: uuid.UUID,
        statuses: Optional[list[str]] = None,
    ) -> int:
        """Count distinct candidate_id rows for a job, optionally filtered by status."""
        from sqlalchemy import func as _func
        query = select(_func.count(_func.distinct(Interview.candidate_id))).where(
            Interview.job_vacancy_id == job_vacancy_id
        )
        if statuses:
            query = query.where(Interview.status.in_(statuses))
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_candidate_ids_for_job(self, job_vacancy_id: uuid.UUID) -> set:
        """Return distinct candidate_ids that already have any interview for this job."""
        result = await self.db.execute(
            select(Interview.candidate_id)
            .where(Interview.job_vacancy_id == job_vacancy_id)
            .distinct()
        )
        return {row[0] for row in result.fetchall() if row[0] is not None}

    async def get_for_candidate_and_job(
        self,
        candidate_id: uuid.UUID,
        job_vacancy_id: uuid.UUID,
        company_id: str | None = None,
    ) -> Optional[Interview]:
        """Return existing interview row for (candidate, job) pair if any.

        Multi-tenancy defense-in-depth via company_id filter (REGRA ZERO + B.1).
        """
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended conditionally below quando company_id passado.
        query = select(Interview).where(
            and_(
                Interview.candidate_id == candidate_id,
                Interview.job_vacancy_id == job_vacancy_id,
            )
        )
        if company_id:
            query = query.where(Interview.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Vacancy helpers
    # ------------------------------------------------------------------

    async def get_vacancy_company_id(self, vacancy_id: uuid.UUID) -> Optional[str]:
        result = await self.db.execute(
            select(JobVacancy.company_id).where(JobVacancy.id == vacancy_id)
        )
        row = result.scalar_one_or_none()
        return str(row) if row else None

    # ------------------------------------------------------------------
    # Shortlist / candidate_id queries
    # ------------------------------------------------------------------

    async def get_shortlisted_candidate_ids(
        self,
        scope: str,
        user_email: Optional[str] = None,
        company_id: Optional[str] = None,
        project_id: Optional[str] = None,
        since_datetime: Optional[datetime] = None,
    ):
        valid_statuses = ["scheduled", "confirmed", "completed", "rescheduled"]

        query = select(Interview.candidate_id).distinct()
        filters = [Interview.status.in_(valid_statuses)]

        if since_datetime:
            filters.append(Interview.created_at >= since_datetime)

        if scope == "shortlisted_by_you":
            if not user_email:
                return []
            filters.append(Interview.interviewer_email == user_email)

        elif scope == "shortlisted_org_this_project":
            if not project_id:
                return []
            filters.append(Interview.job_vacancy_id == project_id)

        elif scope == "shortlisted_org_all_projects":
            if company_id:
                vacancy_subquery = select(JobVacancy.id).where(
                    JobVacancy.company_id == company_id
                )
                filters.append(Interview.job_vacancy_id.in_(vacancy_subquery))
        else:
            return []

        query = query.where(and_(*filters))
        result = await self.db.execute(query)
        return [str(row[0]) for row in result.fetchall() if row[0] is not None]

    async def search_interviews(
        self,
        *,
        candidate_id: Optional[str] = None,
        vacancy_id: Optional[str] = None,
        interviewer_email: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        company_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Interview], int]:
        """Search interviews with optional filters; returns (rows, total).

        Used by SchedulingService.list_interviews — kept distinct from list_interviews
        above (which returns tuples with job_code/job_manager) because consumers differ.

        Multi-tenancy defense-in-depth via company_id filter (REGRA ZERO + B.1).
        """
        # TENANT-EXEMPT: dynamic builder — Interview.company_id == company_id
        # é appended em `filters` abaixo quando company_id passado.
        base_query = select(Interview)

        filters = []
        if candidate_id:
            filters.append(Interview.candidate_id == candidate_id)
        if vacancy_id:
            filters.append(Interview.job_vacancy_id == vacancy_id)
        if interviewer_email:
            filters.append(Interview.interviewer_email == interviewer_email)
        if status:
            filters.append(Interview.status == status)
        if from_date:
            filters.append(Interview.start_time >= from_date)
        if to_date:
            filters.append(Interview.start_time <= to_date)
        if company_id:
            filters.append(Interview.company_id == company_id)

        if filters:
            base_query = base_query.where(and_(*filters))

        total_result = await self.db.execute(base_query)
        total = len(total_result.scalars().all())

        page_query = (
            base_query.order_by(desc(Interview.start_time)).offset(skip).limit(limit)
        )
        page_result = await self.db.execute(page_query)
        rows = list(page_result.scalars().all())
        return rows, total
