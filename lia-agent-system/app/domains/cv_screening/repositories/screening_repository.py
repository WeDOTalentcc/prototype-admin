import uuid
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.screening import ScreeningTask


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

    async def get_task_by_id(
        self,
        task_uuid: UUID,
        company_id: str | None = None,
    ) -> ScreeningTask | None:
        """Get ScreeningTask by id.

        Multi-tenancy defense-in-depth: pass company_id to enforce tenant filter
        at query level (Postgres RLS — Task #1143 — guards by default).
        """
        conditions = [ScreeningTask.id == task_uuid]
        if company_id:
            conditions.append(ScreeningTask.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(ScreeningTask).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def list_tasks_by_job(
        self,
        job_id: str,
        company_id: str | None = None,
    ) -> list[ScreeningTask]:
        """List ScreeningTasks by job.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level.
        """
        conditions = [ScreeningTask.job_id == job_id]
        if company_id:
            conditions.append(ScreeningTask.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # ScreeningTask.company_id filter (conditional, above). Sensor cannot
        # trace through where(*conditions) spread.
        result = await self.db.execute(
            select(ScreeningTask)
            .where(*conditions)
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

    async def get_candidate_by_id(
        self,
        candidate_id: UUID,
        company_id: str | None = None,
    ):
        """Get Candidate by id.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.candidate import Candidate
        conditions = [Candidate.id == candidate_id]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def get_candidates_by_ids(
        self,
        candidate_ids: list[UUID],
        company_id: str | None = None,
    ) -> list:
        """Get Candidates by ids.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level.
        """
        from app.models.candidate import Candidate
        conditions = [Candidate.id.in_(candidate_ids)]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return list(result.scalars().all())

    async def get_random_candidates(
        self,
        limit: int,
        company_id: str | None = None,
    ) -> list:
        """Get random Candidates.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level.
        Without company_id this returns ALL candidates platform-wide (legacy fixture
        helper — only safe in test contexts).
        """
        from app.models.candidate import Candidate
        # TENANT-EXEMPT: legacy fixture helper — cross-tenant by design when
        # company_id is None. When company_id is provided, filter is applied.
        if company_id:
            result = await self.db.execute(
                select(Candidate)
                .where(Candidate.company_id == company_id)
                .order_by(func.random())
                .limit(limit)
            )
        else:
            # TENANT-EXEMPT: this branch is the legacy fixture path documented
            # in the docstring — returns cross-tenant random Candidates. Only
            # safe in test contexts (caller is responsible).
            result = await self.db.execute(
                select(Candidate).order_by(func.random()).limit(limit)
            )
        return list(result.scalars().all())

    # ------------------------------------------------------------------ #
    # JobVacancy methods                                                    #
    # ------------------------------------------------------------------ #

    async def get_job_vacancy_by_id(
        self,
        job_id: UUID,
        company_id: str | None = None,
    ):
        """Get JobVacancy by id.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.job_vacancy import JobVacancy
        conditions = [JobVacancy.id == job_id]
        if company_id:
            conditions.append(JobVacancy.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(JobVacancy).where(*conditions)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------ #
    # JobRequirement methods                                                #
    # ------------------------------------------------------------------ #

    async def get_requirements_by_vacancy(self, job_vacancy_id: UUID) -> list:
        from app.models.rubric import JobRequirement
        result = await self.db.execute(
            select(JobRequirement).where(JobRequirement.job_vacancy_id == job_vacancy_id)
        )
        return list(result.scalars().all())

    async def get_requirement_by_id(self, requirement_id: UUID, job_vacancy_id: UUID):
        from app.models.rubric import JobRequirement
        result = await self.db.execute(
            select(JobRequirement).where(
                JobRequirement.id == requirement_id,
                JobRequirement.job_vacancy_id == job_vacancy_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_requirement(self, requirement) -> object:
        from app.models.rubric import JobRequirement  # noqa: F401
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
        from app.models.rubric import RubricEvaluation
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
        from app.models.rubric import RubricEvaluation
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
        from app.models.calibration import CalibrationSession
        result = await self.db.execute(
            select(CalibrationSession).where(CalibrationSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_blocked_session_for_vacancy(self, vacancy_id: str):
        from app.models.calibration import CalibrationSession
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
        from app.models.calibration import CalibrationSession
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
        from app.models.calibration import CalibrationFeedback
        result = await self.db.execute(
            select(CalibrationFeedback).where(
                CalibrationFeedback.session_id == session_id
            )
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------ #
    # VacancyCandidate methods                                              #
    # ------------------------------------------------------------------ #

    async def count_vacancy_candidates(
        self,
        vacancy_id: UUID,
        company_id: str | None = None,
    ) -> int:
        """Count VacancyCandidate rows for a vacancy.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.candidate import VacancyCandidate
        conditions = [VacancyCandidate.vacancy_id == vacancy_id]
        if company_id:
            conditions.append(VacancyCandidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(*conditions)
        )
        return result.scalar() or 0

    async def get_vacancy_candidate(
        self,
        vacancy_id: UUID,
        candidate_id: UUID,
        company_id: str | None = None,
    ):
        """Get VacancyCandidate by (vacancy_id, candidate_id).

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.candidate import VacancyCandidate
        conditions = [
            VacancyCandidate.vacancy_id == vacancy_id,
            VacancyCandidate.candidate_id == candidate_id,
        ]
        if company_id:
            conditions.append(VacancyCandidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(VacancyCandidate).where(*conditions)
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


    # ------------------------------------------------------------------ #
    # Candidate dedup + scoring helper methods                              #
    # ------------------------------------------------------------------ #

    async def find_active_candidate_by_email(
        self,
        email: str,
        company_id: str | None = None,
    ):
        """Lookup active Candidate by email (hash or raw fallback).

        Multi-tenancy defense-in-depth: pass company_id to scope dedup search to
        the current tenant (canonical use). Without company_id, this is a
        platform-wide dedup search (legacy admin path).
        """
        from app.models.candidate import Candidate
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        conditions = [
            or_(
                Candidate.email_hash == _sha256_hash(email),
                Candidate._email_raw == email,
            ),
            Candidate.is_active,
        ]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def list_active_candidates_by_name_lowered(
        self,
        name_normalized: str,
        company_id: str | None = None,
    ):
        """List active Candidates by lowered name.

        Multi-tenancy defense-in-depth: pass company_id to scope to current tenant.
        """
        from app.models.candidate import Candidate
        conditions = [
            func.lower(Candidate.name) == name_normalized,
            Candidate.is_active,
        ]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return list(result.scalars().all())

    async def find_active_candidate_by_linkedin_username(
        self,
        linkedin_username: str,
        company_id: str | None = None,
    ):
        """Lookup active Candidate by LinkedIn URL substring.

        Multi-tenancy defense-in-depth: pass company_id to scope to current tenant.
        """
        from app.models.candidate import Candidate
        conditions = [
            Candidate.linkedin_url.ilike(f"%{linkedin_username}%"),
            Candidate.is_active,
        ]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def get_candidate_by_uuid_string(
        self,
        candidate_id: str,
        company_id: str | None = None,
    ):
        """Get Candidate by string UUID (auto-converts).

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.candidate import Candidate
        try:
            cid = uuid.UUID(candidate_id)
        except Exception:
            return None
        conditions = [Candidate.id == cid]
        if company_id:
            conditions.append(Candidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(Candidate).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def get_job_vacancy_by_uuid_string(
        self,
        job_id: str,
        company_id: str | None = None,
    ):
        """Get JobVacancy by string UUID (auto-converts).

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.job_vacancy import JobVacancy
        try:
            jid = uuid.UUID(job_id)
        except Exception:
            return None
        conditions = [JobVacancy.id == jid]
        if company_id:
            conditions.append(JobVacancy.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(JobVacancy).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def list_requirements_by_vacancy_uuid_string(self, job_id: str):
        from app.models.job_requirement import JobRequirement
        try:
            jid = uuid.UUID(job_id)
        except Exception:
            return []
        result = await self.db.execute(
            select(JobRequirement).where(JobRequirement.job_vacancy_id == jid)
        )
        return list(result.scalars().all())

    async def get_vacancy_candidate_by_pair(
        self,
        *,
        vacancy_id,
        candidate_id,
        company_id: str | None = None,
    ):
        """Get VacancyCandidate by (vacancy_id, candidate_id) — accepts UUID or str.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        from app.models.candidate import VacancyCandidate
        conditions = [
            VacancyCandidate.vacancy_id == vacancy_id,
            VacancyCandidate.candidate_id == candidate_id,
        ]
        if company_id:
            conditions.append(VacancyCandidate.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(VacancyCandidate).where(*conditions)
        )
        return result.scalar_one_or_none()
