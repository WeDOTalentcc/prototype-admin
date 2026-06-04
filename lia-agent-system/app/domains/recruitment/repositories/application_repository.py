"""
ApplicationRepository -- persistence layer for candidate applications.
Encapsulates all DB access for the applications API controller.
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate, VacancyCandidate
from app.models.candidate_feedback import CandidateFeedback
from app.models.job_vacancy import JobVacancy
from app.models.rubric import JobRequirement

logger = logging.getLogger(__name__)


class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # JobVacancy
    # ------------------------------------------------------------------

    async def get_vacancy_by_id(self, vacancy_id: str):
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == vacancy_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Candidate
    # ------------------------------------------------------------------

    async def get_candidate_by_email(self, email: str):
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        result = await self.db.execute(
            select(Candidate).where(
                or_(
                    Candidate.email_hash == _sha256_hash(email),
                    Candidate._email_raw == email,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_candidate_by_id(self, candidate_id: str):
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == uuid.UUID(candidate_id))
        )
        return result.scalar_one_or_none()

    async def create_candidate(self, candidate_data: dict) -> Candidate:
        candidate = Candidate(
            id=uuid.uuid4(),
            name=candidate_data["name"],
            email=candidate_data["email"],
            phone=candidate_data.get("phone"),
            linkedin_url=candidate_data.get("linkedin_url"),
            current_title=candidate_data.get("current_title"),
            current_company=candidate_data.get("current_company"),
            years_of_experience=candidate_data.get("years_of_experience"),
            technical_skills=candidate_data.get("technical_skills", []),
            location_city=candidate_data.get("location"),
            desired_salary_min=candidate_data.get("salary_expectation"),
            source="application",
            status="new",
        )
        self.db.add(candidate)
        return candidate

    async def update_candidate_from_data(self, candidate: Candidate, candidate_data: dict) -> Candidate:
        for key, value in candidate_data.items():
            if value is not None and hasattr(candidate, key):
                setattr(candidate, key, value)
        candidate.updated_at = datetime.utcnow()
        return candidate

    async def flush(self):
        await self.db.flush()

    async def rollback(self):
        await self.db.rollback()

    # ------------------------------------------------------------------
    # VacancyCandidate
    # ------------------------------------------------------------------

    async def get_vacancy_candidate(self, vacancy_id: str, candidate_id) -> "VacancyCandidate | None":
        result = await self.db.execute(
            select(VacancyCandidate).where(
                VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
                VacancyCandidate.candidate_id == candidate_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_organic_candidates(self, vacancy_id: str, excluded_statuses: tuple) -> int:
        EXCLUDED = excluded_statuses
        active_filter = and_(
            VacancyCandidate.vacancy_id == uuid.UUID(vacancy_id),
            not_(VacancyCandidate.status.in_(EXCLUDED)),
            VacancyCandidate.origin.in_(("web", "whatsapp")) if hasattr(VacancyCandidate, "origin") else True,
        )
        cnt = await self.db.execute(select(func.count(VacancyCandidate.id)).where(active_filter))
        return cnt.scalar() or 0

    async def create_vacancy_candidate(
        self,
        vacancy_id: str,
        candidate_id,
        company_id,
        source: str,
        lia_score: float,
        match_percentage: float,
        status: str,
        stage: str,
        additional_data: "dict | None" = None,
    ) -> VacancyCandidate:
        # Task #1306: resolve the structural stage link at creation so the SLA
        # detector can join by id instead of fragile name matching.
        from app.shared.services.stage_id_resolver import resolve_recruitment_stage_id
        stage_id = await resolve_recruitment_stage_id(self.db, str(company_id), stage)
        vacancy_candidate = VacancyCandidate(
            id=uuid.uuid4(),
            vacancy_id=uuid.UUID(vacancy_id),
            candidate_id=candidate_id,
            company_id=company_id,
            source=source,
            lia_score=lia_score,
            match_percentage=match_percentage,
            status=status,
            stage=stage,
            recruitment_stage_id=stage_id,
            additional_data=additional_data or {},
        )
        self.db.add(vacancy_candidate)
        return vacancy_candidate

    # ------------------------------------------------------------------
    # CompanyProfile (saturation check)
    # ------------------------------------------------------------------

    async def get_company_threshold(self, company_id, default_threshold: int = 20) -> int:
        try:
            from app.models.company import CompanyProfile
            if not company_id:
                return default_threshold
            cp_result = await self.db.execute(
                select(CompanyProfile).where(CompanyProfile.id == company_id)
            )
            cp = cp_result.scalar_one_or_none()
            if cp and cp.additional_data:
                sat_cfg = cp.additional_data.get("saturation_settings", {})
                return sat_cfg.get("threshold_web", default_threshold)
        except Exception as e:
            logger.warning(f"Could not fetch company threshold: {e}")
        return default_threshold

    # ------------------------------------------------------------------
    # CandidateFeedback
    # ------------------------------------------------------------------

    async def get_feedback_by_token(self, candidate_id: str, vacancy_id: str, token: str):
        result = await self.db.execute(
            select(CandidateFeedback).where(
                CandidateFeedback.candidate_id == candidate_id,
                CandidateFeedback.vacancy_id == vacancy_id,
                CandidateFeedback.resubmit_token == token,
            )
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # JobRequirement
    # ------------------------------------------------------------------

    async def get_job_requirements(self, vacancy_id: str) -> list:
        reqs_result = await self.db.execute(
            select(JobRequirement).where(JobRequirement.job_vacancy_id == uuid.UUID(vacancy_id))
        )
        return list(reqs_result.scalars().all())
