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
        result = await self.db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        )
        return result.scalar_one_or_none()

    async def list_candidates_by_ids(self, candidate_ids: list[str]) -> list[Candidate]:
        if not candidate_ids:
            return []
        result = await self.db.execute(
            select(Candidate).where(Candidate.id.in_(candidate_ids))
        )
        return list(result.scalars().all())

    async def count_candidates(self) -> int:
        result = await self.db.execute(select(func.count(Candidate.id)))
        return int(result.scalar() or 0)

    # ── Job vacancy ──────────────────────────────────────────────────────

    async def get_job(self, job_id: str) -> JobVacancy | None:
        result = await self.db.execute(
            select(JobVacancy).where(JobVacancy.id == job_id)
        )
        return result.scalar_one_or_none()

    async def count_jobs(self) -> int:
        result = await self.db.execute(select(func.count(JobVacancy.id)))
        return int(result.scalar() or 0)

    # ── Email template ───────────────────────────────────────────────────

    async def count_email_templates(self) -> int:
        result = await self.db.execute(select(func.count(EmailTemplate.id)))
        return int(result.scalar() or 0)
