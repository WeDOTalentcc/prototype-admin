"""
JobOfferRepository — ADR-001 canonical. No inline SQL in services.
All company-scoped methods call _require_company_id().
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.job_offer import JobOffer


class JobOfferRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── Guard ──────────────────────────────────────────────────────────────

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
        candidate_id: str,
        created_by: Optional[str] = None,
        salary: Optional[float] = None,
        currency: str = "BRL",
        start_date=None,
        notes: Optional[str] = None,
        requires_manager_approval: bool = False,
    ) -> JobOffer:
        cid = self._require_company_id(company_id)
        offer = JobOffer(
            id=str(uuid.uuid4()),
            company_id=cid,
            job_vacancy_id=job_vacancy_id,
            candidate_id=candidate_id,
            created_by=created_by,
            salary=salary,
            currency=currency,
            start_date=start_date,
            notes=notes,
            status="draft",
            requires_manager_approval=requires_manager_approval,
        )
        self._db.add(offer)
        await self._db.flush()
        return offer

    async def send(self, offer: JobOffer) -> JobOffer:
        offer.status = "sent"
        offer.sent_at = datetime.now(timezone.utc)
        await self._db.flush()
        return offer

    async def record_response(
        self,
        offer: JobOffer,
        response: str,  # "accepted" | "rejected"
        response_notes: Optional[str] = None,
    ) -> JobOffer:
        offer.candidate_response = response
        offer.response_notes = response_notes
        offer.status = response  # "accepted" or "rejected"
        offer.responded_at = datetime.now(timezone.utc)
        await self._db.flush()
        return offer

    async def withdraw(self, offer: JobOffer) -> JobOffer:
        offer.status = "withdrawn"
        await self._db.flush()
        return offer

    # ── Read ───────────────────────────────────────────────────────────────

    async def get_by_id(self, company_id: str, offer_id: str) -> Optional[JobOffer]:
        cid = self._require_company_id(company_id)
        result = await self._db.execute(
            select(JobOffer).where(
                and_(JobOffer.id == offer_id, JobOffer.company_id == cid)
            )
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
        filters = [JobOffer.company_id == cid, JobOffer.job_vacancy_id == job_vacancy_id]
        if status:
            filters.append(JobOffer.status == status)
        result = await self._db.execute(
            select(JobOffer)
            .where(and_(*filters))
            .order_by(JobOffer.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_for_company(
        self,
        company_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ):
        cid = self._require_company_id(company_id)
        filters = [JobOffer.company_id == cid]
        if status:
            filters.append(JobOffer.status == status)
        result = await self._db.execute(
            select(JobOffer)
            .where(and_(*filters))
            .order_by(JobOffer.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def count_by_status(self, company_id: str, job_vacancy_id: Optional[str] = None) -> dict:
        """Returns {status: count} for the given scope."""
        from sqlalchemy import func as sa_func
        cid = self._require_company_id(company_id)
        filters = [JobOffer.company_id == cid]
        if job_vacancy_id:
            filters.append(JobOffer.job_vacancy_id == job_vacancy_id)
        result = await self._db.execute(
            select(JobOffer.status, sa_func.count(JobOffer.id))
            .where(and_(*filters))
            .group_by(JobOffer.status)
        )
        return {row[0]: row[1] for row in result.all()}
