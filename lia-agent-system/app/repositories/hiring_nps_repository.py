"""
HiringNpsRepository — ADR-001 canonical.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.hiring_nps import HiringNps, NPS_DEFAULT_TTL_HOURS


class HiringNpsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _require_company_id(company_id: Optional[str]) -> str:
        if not company_id:
            raise ValueError("company_id is required")
        return company_id

    # ── Write ──────────────────────────────────────────────────────────────

    async def create(
        self,
        *,
        company_id: str,
        job_vacancy_id: str,
        respondent_type: str,
        candidate_id: Optional[str] = None,
        respondent_email: Optional[str] = None,
        sent_by: Optional[str] = None,
        ttl_hours: int = NPS_DEFAULT_TTL_HOURS,
    ) -> HiringNps:
        cid = self._require_company_id(company_id)
        import secrets
        nps = HiringNps(
            id=str(uuid.uuid4()),
            company_id=cid,
            job_vacancy_id=job_vacancy_id,
            candidate_id=candidate_id,
            respondent_type=respondent_type,
            respondent_email=respondent_email,
            token=secrets.token_urlsafe(32),
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=ttl_hours),
            sent_by=sent_by,
        )
        self._db.add(nps)
        await self._db.flush()
        return nps

    async def respond(
        self,
        nps: HiringNps,
        score: int,
        comment: Optional[str] = None,
    ) -> HiringNps:
        nps.score = score
        nps.comment = comment
        nps.status = "responded"
        nps.responded_at = datetime.now(timezone.utc)
        await self._db.flush()
        return nps

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_by_token(self, token: str) -> Optional[HiringNps]:
        result = await self._db.execute(
            select(HiringNps).where(HiringNps.token == token)
        )
        return result.scalar_one_or_none()

    async def list_for_job(
        self,
        company_id: str,
        job_vacancy_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ):
        cid = self._require_company_id(company_id)
        filters = [HiringNps.company_id == cid, HiringNps.job_vacancy_id == job_vacancy_id]
        if status:
            filters.append(HiringNps.status == status)
        result = await self._db.execute(
            select(HiringNps)
            .where(and_(*filters))
            .order_by(HiringNps.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def avg_score_for_job(self, company_id: str, job_vacancy_id: str) -> Optional[float]:
        """Average NPS score for responded surveys on this job."""
        cid = self._require_company_id(company_id)
        result = await self._db.execute(
            select(func.avg(HiringNps.score)).where(
                and_(
                    HiringNps.company_id == cid,
                    HiringNps.job_vacancy_id == job_vacancy_id,
                    HiringNps.status == "responded",
                    HiringNps.score.isnot(None),
                )
            )
        )
        val = result.scalar_one_or_none()
        return round(float(val), 1) if val is not None else None

    async def count_by_status(self, company_id: str, job_vacancy_id: Optional[str] = None) -> dict:
        cid = self._require_company_id(company_id)
        filters = [HiringNps.company_id == cid]
        if job_vacancy_id:
            filters.append(HiringNps.job_vacancy_id == job_vacancy_id)
        result = await self._db.execute(
            select(HiringNps.status, func.count(HiringNps.id))
            .where(and_(*filters))
            .group_by(HiringNps.status)
        )
        return {row[0]: row[1] for row in result.all()}
