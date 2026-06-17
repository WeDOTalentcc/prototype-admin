from datetime import datetime
from typing import Any
from uuid import UUID

import uuid as uuid_lib

from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_vacancy import JobVacancy
from app.models.candidate import Candidate, VacancyCandidate
from app.models.company import CompanyProfile


class JobVacancyPublicRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── generate-public-link / share-link helpers ─────────────────────────────

    async def get_vacancy_by_id_and_company(self, vacancy_id: UUID, company_id):
        result = await self.db.execute(
            select(JobVacancy).where(
                and_(JobVacancy.id == vacancy_id, JobVacancy.company_id == company_id)
            )
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        existing = await self.db.execute(
            select(JobVacancy.id).where(JobVacancy.public_slug == slug)
        )
        return existing.scalar_one_or_none() is not None

    async def save_public_slug(self, job: JobVacancy, new_slug: str) -> JobVacancy:
        job.public_slug = new_slug
        job.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(job)
        return job

    # ── public vacancy view ────────────────────────────────────────────────────

    async def get_vacancy_by_slug(self, slug: str):
        """Get vacancy by public slug (unauthenticated public-page lookup)."""
        # TENANT-EXEMPT: public share-link lookup — anonymous candidates
        # access via public_slug which is globally unique. Slug itself
        # carries no tenant secret; vacancy returns its own company_id for
        # downstream rendering.
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.public_slug == slug)
        )
        return result.scalar_one_or_none()

    async def increment_view_count(self, job: JobVacancy) -> None:
        job.view_count = (job.view_count or 0) + 1

    # ── apply flow ────────────────────────────────────────────────────────────

    async def get_candidate_by_email(self, email: str, company_id: Any | None = None):
        """Look up a candidate by email. ``company_id`` optional for
        backwards-compat (recommended for defense-in-depth REGRA ZERO).

        Note: public apply flow may resolve cross-tenant when candidate
        already exists in another company — caller decides what to do.
        """
        # TENANT-EXEMPT: public apply flow — candidate-by-email lookup is
        # global by design (a candidate may apply to multiple tenants);
        # company_id appended conditionally when caller wants strict scope.
        from app.shared.encryption.encrypted_field_mixin import _sha256_hash
        from sqlalchemy import or_
        query = select(Candidate).where(
            or_(
                Candidate.email_hash == _sha256_hash(email),
                Candidate._email_raw == email,
            )
        )
        if company_id:
            query = query.where(Candidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_candidate(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        await self.db.flush()
        return candidate

    async def flush_candidate(self, candidate: Candidate) -> None:
        await self.db.flush()

    async def get_vacancy_candidate(self, vacancy_id, candidate_id, company_id: Any | None = None):
        """Lookup VacancyCandidate by composite key. ``company_id`` optional
        for defense-in-depth (REGRA ZERO)."""
        # TENANT-EXEMPT: dynamic builder — VacancyCandidate.company_id
        # appended conditionally below when caller passes it.
        query = select(VacancyCandidate).where(
            VacancyCandidate.vacancy_id == vacancy_id,
            VacancyCandidate.candidate_id == candidate_id,
        )
        if company_id:
            query = query.where(VacancyCandidate.company_id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_company_profile(self, company_id):
        cr = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.id == company_id)
        )
        return cr.scalar_one_or_none()

    async def count_organic_candidates(self, vacancy_id, excluded_statuses: tuple) -> int:
        active_filter = and_(
            VacancyCandidate.vacancy_id == vacancy_id,
            not_(VacancyCandidate.status.in_(excluded_statuses)),
            VacancyCandidate.origin.in_(("web", "whatsapp"))
        )
        count_result = await self.db.execute(
            select(func.count(VacancyCandidate.id)).where(active_filter)
        )
        return count_result.scalar() or 0

    async def add_vacancy_candidate(self, vacancy_candidate: VacancyCandidate) -> VacancyCandidate:
        self.db.add(vacancy_candidate)
        return vacancy_candidate

    async def rollback(self) -> None:
        await self.db.rollback()

    def get_session(self) -> AsyncSession:
        return self.db
