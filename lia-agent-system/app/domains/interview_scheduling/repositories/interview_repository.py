"""
Interview Repository - encapsulates all database access for the interview scheduling domain.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
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

    async def get_candidate_by_id(self, candidate_id: uuid.UUID) -> Optional[Candidate]:
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Interview CRUD
    # ------------------------------------------------------------------

    async def get_interview_by_id(self, interview_id: str) -> Optional[Interview]:
        result = await self.db.execute(
            select(Interview).where(Interview.id == interview_id)
        )
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
        limit: int = 50,
    ):
        """Return list of (Interview, job_code, job_manager) tuples."""
        jv = aliased(JobVacancy)
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
