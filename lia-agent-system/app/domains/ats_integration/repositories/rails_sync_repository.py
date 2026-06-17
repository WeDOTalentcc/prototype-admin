"""
RailsSyncRepository — read-only aggregator for the Rails → FastAPI sync surface.

Encapsulates every DB read consumed by `app/api/v1/rails_sync.py` so the
controller layer stays free of SQLAlchemy (ADR-001). All operations are
read-only; writes from Rails go through dedicated mutation endpoints.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate import Candidate
from lia_models.email_template import EmailTemplate
from lia_models.job_vacancy import JobVacancy


class RailsSyncRepository:
    """Read-only facade for cross-domain reads triggered by Rails."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Candidate ────────────────────────────────────────────────────────

    async def get_candidate(self, candidate_id: str) -> Candidate | None:
        # TENANT-EXEMPT: rails-sync service-to-service endpoint; Rails passes own
        # tenant context via service token + RLS at session level (Task #1143)
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def get_candidate_for_company(
        self, candidate_id: str, company_id: str
    ) -> Candidate | None:
        """Tenant-scoped fetch (canonical multi-tenant pattern).

        Used by controllers gated via Depends(require_company_id). Defense-in-depth:
        explicit company_id WHERE alongside Postgres RLS (Task #1143).
        """
        result = await self.db.execute(
            select(Candidate).where(
                Candidate.id == candidate_id,
                Candidate.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_candidates_by_ids(self, candidate_ids: list[str]) -> list[Candidate]:
        if not candidate_ids:
            return []
        # TENANT-EXEMPT: rails-sync service-to-service endpoint; Rails passes own
        # tenant context via service token + RLS at session level (Task #1143)
        result = await self.db.execute(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        )
        return list(result.scalars().all())

    async def list_candidates_by_ids_for_company(
        self, candidate_ids: list[str], company_id: str
    ) -> list[Candidate]:
        """Tenant-scoped bulk fetch (canonical multi-tenant pattern).

        Defense-in-depth: explicit company_id WHERE + Postgres RLS.
        """
        if not candidate_ids:
            return []
        result = await self.db.execute(
            select(Candidate).where(
                Candidate.id.in_(candidate_ids),
                Candidate.company_id == company_id,
            )
        )
        return list(result.scalars().all())

    async def count_candidates(self) -> int:
        result = await self.db.execute(select(func.count(Candidate.id)))
        return int(result.scalar() or 0)

    # ── Job vacancy ──────────────────────────────────────────────────────

    async def get_job(self, job_id: str) -> JobVacancy | None:
        # TENANT-EXEMPT: rails-sync service-to-service endpoint; Rails passes own
        # tenant context via service token + RLS at session level (Task #1143)
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_job_for_company(
        self, job_id: str, company_id: str
    ) -> JobVacancy | None:
        """Tenant-scoped fetch (canonical multi-tenant pattern).

        Defense-in-depth: explicit company_id WHERE + Postgres RLS.
        """
        result = await self.db.execute(
            select(JobVacancy).where(
                JobVacancy.id == job_id,
                JobVacancy.company_id == company_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_jobs(self) -> int:
        result = await self.db.execute(select(func.count(JobVacancy.id)))
        return int(result.scalar() or 0)

    # ── Email template ───────────────────────────────────────────────────

    async def count_email_templates(self) -> int:
        result = await self.db.execute(select(func.count(EmailTemplate.id)))
        return int(result.scalar() or 0)
