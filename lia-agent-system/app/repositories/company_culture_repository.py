"""
CompanyCultureRepository — encapsulates all DB access for
CompanyCultureProfile and CultureAnalysisJob models.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyProfile
from app.models.company_culture import CompanyCultureProfile, CultureAnalysisJob

logger = logging.getLogger(__name__)


class CompanyCultureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CompanyProfile helpers
    # ------------------------------------------------------------------

    async def get_company_by_id(self, company_id: UUID) -> Optional[CompanyProfile]:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.id == company_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # CompanyCultureProfile
    # ------------------------------------------------------------------

    async def get_profile_by_company(self, company_id: UUID) -> Optional[CompanyCultureProfile]:
        result = await self.db.execute(
            select(CompanyCultureProfile).where(
                CompanyCultureProfile.company_id == company_id
            )
        )
        return result.scalar_one_or_none()

    async def create_profile(
        self, company_id: UUID, profile_data: dict
    ) -> CompanyCultureProfile:
        profile = CompanyCultureProfile(company_id=company_id, **profile_data)
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update_profile(
        self, profile: CompanyCultureProfile, profile_data: dict
    ) -> CompanyCultureProfile:
        for key, value in profile_data.items():
            setattr(profile, key, value)
        profile.last_analysis_at = datetime.utcnow()
        profile.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def create_or_update_profile(
        self, company_id: UUID, profile_data: dict
    ) -> CompanyCultureProfile:
        profile = await self.get_profile_by_company(company_id)
        if profile:
            return await self.update_profile(profile, profile_data)
        return await self.create_profile(company_id, profile_data)

    async def update_profile_fields(
        self, company_id: UUID, update_data: dict
    ) -> Optional[CompanyCultureProfile]:
        """Apply recruiter-driven field updates, marking source as 'manual'.

        DEPRECATED for new write paths: returns None when profile does not
        exist yet, which surfaces as HTTP 404 to the caller. Use
        :py:meth:`upsert_profile_fields` instead so manual edits work even
        before any culture analysis job has populated an initial row.

        Retained because external callers may still rely on the strict
        update-only semantics (e.g. background reconciliation jobs that
        MUST fail when the row is missing).
        """
        profile = await self.get_profile_by_company(company_id)
        if not profile:
            return None
        for field, value in update_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        profile.source = "manual"
        profile.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def upsert_profile_fields(
        self, company_id: UUID, update_data: dict
    ) -> CompanyCultureProfile:
        """Apply recruiter-driven field updates with CREATE-IF-MISSING semantics.

        Used by the REST PUT handler so manual inline edits on Minha Empresa
        cards work even when the culture analysis job has not yet produced
        an initial row. Always marks ``source = 'manual'`` to keep agent
        consumers (bigfive_service, wsi_question_generator) aware that the
        data is human-curated and should override learned defaults.

        Filters update_data to model attributes before set/insert so callers
        can pass partial payloads safely. Never raises on missing row — the
        row is created on the fly with the given fields.

        Bug fix 2026-05-21 (Paulo): UI saveField loop was 404'ing for every
        company that had not gone through /analyze yet. Closes the gap
        between LIA chat tool save (already upserts via tool registry) and
        REST manual save (was UPDATE-only).
        """
        # Filter unknown attrs once — same defensive pattern as
        # update_profile_fields above. dict comprehension preserves order.
        filtered = {
            field: value
            for field, value in update_data.items()
            if hasattr(CompanyCultureProfile, field)
        }
        profile = await self.get_profile_by_company(company_id)
        if profile is None:
            # CREATE: cold start — no analyze run yet, recruiter is filling
            # in fields manually via Minha Empresa. Source must be 'manual'
            # so downstream agents know not to overwrite from auto runs.
            # website_url is NOT NULL without server_default (bug fix 2026-05-25):
            # provide empty-string fallback so manual-only saves don't trip the
            # constraint. The real URL is set by /analyze when the recruiter
            # runs a full culture scan.
            filtered.setdefault("website_url", "")
            profile = CompanyCultureProfile(
                company_id=company_id,
                source="manual",
                **filtered,
            )
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
            return profile
        # UPDATE: row exists. Apply filtered diff and flip source to manual.
        for field, value in filtered.items():
            setattr(profile, field, value)
        profile.source = "manual"
        profile.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete_profile(self, company_id: UUID) -> bool:
        profile = await self.get_profile_by_company(company_id)
        if not profile:
            return False
        await self.db.delete(profile)
        return True

    async def list_profiles(
        self, skip: int = 0, limit: int = 50
    ) -> list[CompanyCultureProfile]:
        result = await self.db.execute(
            select(CompanyCultureProfile)
            .order_by(CompanyCultureProfile.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # CultureAnalysisJob
    # ------------------------------------------------------------------

    async def get_job_by_id(self, job_id: UUID) -> Optional[CultureAnalysisJob]:
        result = await self.db.execute(
            select(CultureAnalysisJob).where(CultureAnalysisJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def create_job(
        self,
        company_id: UUID,
        website_url: str,
    ) -> CultureAnalysisJob:
        job = CultureAnalysisJob(
            company_id=company_id,
            website_url=website_url,
            status="pending",
            progress=0,
            current_step="Aguardando início",
        )
        self.db.add(job)
        await self.db.flush()
        await self.db.refresh(job)
        return job

    async def mark_job_running(self, job: CultureAnalysisJob) -> None:
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.current_step = "Iniciando análise..."
        job.progress = 5

    async def update_job_progress(
        self,
        job: CultureAnalysisJob,
        progress: int,
        current_step: str,
        pages_discovered: Optional[int] = None,
        pages_scraped: Optional[int] = None,
    ) -> None:
        job.progress = progress
        job.current_step = current_step
        if pages_discovered is not None:
            job.pages_discovered = pages_discovered
        if pages_scraped is not None:
            job.pages_scraped = pages_scraped

    async def mark_job_failed(
        self, job: CultureAnalysisJob, error_message: str
    ) -> None:
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.utcnow()

    async def mark_job_completed(
        self, job: CultureAnalysisJob, result_profile_id: UUID
    ) -> None:
        job.status = "completed"
        job.progress = 100
        job.current_step = "Análise concluída"
        job.result_profile_id = result_profile_id
        job.completed_at = datetime.utcnow()
