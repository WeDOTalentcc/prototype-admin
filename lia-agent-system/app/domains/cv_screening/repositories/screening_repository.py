import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.screening import ScreeningTask


class ScreeningRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------ #
    # Existing ScreeningTask methods                                        #
    # ------------------------------------------------------------------ #

    async def create_task(self, task: ScreeningTask) -> ScreeningTask:
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(self, task_uuid: UUID) -> ScreeningTask | None:
        result = await self.db.execute(
            select(ScreeningTask).where(ScreeningTask.id == task_uuid)
        )
        return result.scalar_one_or_none()

    async def list_tasks_by_job(self, job_id: str) -> list[ScreeningTask]:
        result = await self.db.execute(
            select(ScreeningTask)
            .where(ScreeningTask.job_id == job_id)
            .order_by(ScreeningTask.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_task_status(self, task: ScreeningTask, status: str) -> ScreeningTask:
        task.status = status
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def rollback(self) -> None:
        await self.db.rollback()

    # ------------------------------------------------------------------ #
    # Candidate methods                                                     #
    # ------------------------------------------------------------------ #

    async def get_candidate_by_id(self, candidate_id: UUID):
        from lia_models.candidate import Candidate
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_candidates_by_ids(self, candidate_ids: list[UUID]) -> list:
        from lia_models.candidate import Candidate
        result = await self.db.execute(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        )
        return list(result.scalars().all())

    async def get_random_candidates(self, limit: int) -> list:
        from lia_models.candidate import Candidate
        result = await self.db.execute(
            select(Candidate).order_by(func.random()).limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------ #
    # JobVacancy methods                                                    #
    # ------------------------------------------------------------------ #

    async def get_job_vacancy_by_id(self, job_id: UUID):
        from lia_models.job_vacancy import JobVacancy
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------ #
    # JobRequirement methods                                                #
    # ------------------------------------------------------------------ #

    async def get_requirements_by_vacancy(self, job_vacancy_id: UUID) -> list:
        from lia_models.rubric import JobRequirement
        result = await self.db.execute(
            select(JobRequirement).where(JobRequirement.job_vacancy_id == job_vacancy_id)
        )
        return list(result.scalars().all())

    async def get_requirement_by_id(self, requirement_id: UUID, job_vacancy_id: UUID):
        from lia_models.rubric import JobRequirement
        result = await self.db.execute(
            select(JobRequirement).where(
                JobRequirement.id == requirement_id,
                JobRequirement.job_vacancy_id == job_vacancy_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_requirement(self, requirement) -> object:
        from lia_models.rubric import JobRequirement  # noqa: F401
        self.db.add(requirement)
        await self.db.flush()
        await self.db.refresh(requirement)
        return requirement

    async def delete_requirement(self, requirement) -> None:
        await self.db.delete(requirement)

    # ------------------------------------------------------------------ #
    # RubricEvaluation methods                                              #
    # ------------------------------------------------------------------ #

    async def create_evaluation(self, evaluation) -> object:
        self.db.add(evaluation)
        await self.db.flush()
        await self.db.refresh(evaluation)
        return evaluation

    async def add_evaluation(self, evaluation) -> None:
        """Add evaluation without flush (for batch operations)."""
        self.db.add(evaluation)

    async def flush(self) -> None:
        await self.db.flush()

    async def get_evaluations_by_vacancy(
        self, job_vacancy_id: UUID, min_score: float | None = None
    ) -> list:
        from lia_models.rubric import RubricEvaluation
        from sqlalchemy import select as sa_select

        query = sa_select(RubricEvaluation).where(
            RubricEvaluation.job_vacancy_id == job_vacancy_id
        )
        if min_score is not None:
            query = query.where(RubricEvaluation.score >= min_score)
        query = query.order_by(RubricEvaluation.score.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_evaluation(self, candidate_id: UUID, job_vacancy_id: UUID):
        from lia_models.rubric import RubricEvaluation
        result = await self.db.execute(
            select(RubricEvaluation)
            .where(
                RubricEvaluation.candidate_id == candidate_id,
                RubricEvaluation.job_vacancy_id == job_vacancy_id,
            )
            .order_by(RubricEvaluation.evaluated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------ #
    # CalibrationSession methods                                            #
    # ------------------------------------------------------------------ #

    async def get_calibration_session_by_id(self, session_id: str):
        from lia_models.calibration import CalibrationSession
        result = await self.db.execute(
            select(CalibrationSession).where(CalibrationSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_blocked_session_for_vacancy(self, vacancy_id: str):
        from lia_models.calibration import CalibrationSession
        result = await self.db.execute(
            select(CalibrationSession)
            .where(
                CalibrationSession.vacancy_id == vacancy_id,
                CalibrationSession.sourcing_blocked,
            )
            .order_by(CalibrationSession.created_at.desc())
        )
        return result.scalars().first()

    async def get_latest_session_for_vacancy(self, vacancy_id: str):
        from lia_models.calibration import CalibrationSession
        result = await self.db.execute(
            select(CalibrationSession)
            .where(CalibrationSession.vacancy_id == vacancy_id)
            .order_by(CalibrationSession.created_at.desc())
        )
        return result.scalars().first()

    async def create_calibration_session(self, session) -> object:
        self.db.add(session)
        await self.db.flush()
        return session

    # ------------------------------------------------------------------ #
    # CalibrationFeedback methods                                           #
    # ------------------------------------------------------------------ #

    async def create_calibration_feedback(self, feedback) -> object:
        self.db.add(feedback)
        return feedback

    async def get_feedbacks_by_session(self, session_id: str) -> list:
        from lia_models.calibration import CalibrationFeedback
        result = await self.db.execute(
            select(CalibrationFeedback).where(
                CalibrationFeedback.session_id == session_id
            )
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------ #
    # VacancyCandidate methods                                              #
    # ------------------------------------------------------------------ #

    async def count_vacancy_candidates(self, vacancy_id: UUID) -> int:
        from lia_models.candidate import VacancyCandidate
        result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(
                VacancyCandidate.vacancy_id == vacancy_id
            )
        )
        return result.scalar() or 0

    async def get_vacancy_candidate(self, vacancy_id: UUID, candidate_id: UUID):
        from lia_models.candidate import VacancyCandidate
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == vacancy_id,
                VacancyCandidate.candidate_id == candidate_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_vacancy_candidate(self, vc) -> None:
        self.db.add(vc)

    # ------------------------------------------------------------------
    # CV Parser — candidate creation (cv_parser.py Phase 2)
    # ------------------------------------------------------------------

    async def add_candidate_with_experiences_and_education(
        self,
        candidate,
        experiences: list,
        educations: list,
    ):
        """
        Persist a new Candidate plus its CandidateExperience and CandidateEducation
        records in a single unit of work.  Caller is responsible for commit/rollback.
        """
        self.db.add(candidate)
        for exp in experiences:
            self.db.add(exp)
        for edu in educations:
            self.db.add(edu)
        await self.db.flush()
        await self.db.refresh(candidate)
        return candidate
