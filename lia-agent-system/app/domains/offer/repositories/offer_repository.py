"""
OfferRepository — multi-tenant CRUD for OfferProposal.
"""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.offer_proposal import OfferProposal

logger = logging.getLogger(__name__)


class OfferRepository:

    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, offer_id: UUID, company_id: str) -> OfferProposal | None:
        result = await self._db.execute(
            select(OfferProposal).where(
                and_(
                    OfferProposal.id == offer_id,
                    OfferProposal.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_draft(
        self, company_id: str, candidate_id: str, job_id: UUID
    ) -> OfferProposal | None:
        """Return existing draft for (company, candidate, job), if any.

        Note (Sprint F.4 #42 canonical-remap): caller param remains ``job_id``
        for backwards compat (FE wire contract). Internally maps to the
        canonical column ``OfferProposal.job_vacancy_id``.
        """
        result = await self._db.execute(
            select(OfferProposal).where(
                and_(
                    OfferProposal.company_id == company_id,
                    OfferProposal.candidate_id == candidate_id,
                    OfferProposal.job_vacancy_id == job_id,
                    OfferProposal.status == "draft",
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, proposal: OfferProposal) -> OfferProposal:
        self._db.add(proposal)
        await self._db.flush()
        await self._db.refresh(proposal)
        return proposal

    async def update(self, proposal: OfferProposal) -> OfferProposal:
        proposal.updated_at = datetime.utcnow()
        await self._db.flush()
        await self._db.refresh(proposal)
        return proposal

    async def get_by_candidate_token(self, token) -> OfferProposal | None:
        result = await self._db.execute(
            select(OfferProposal).where(OfferProposal.candidate_token == token)
        )
        return result.scalar_one_or_none()


    async def list_deadline_passed(self, limit: int = 500) -> list[OfferProposal]:
        """ADR-001: find offers where response_deadline < now and status pending.

        Cross-tenant: intentionally no company_id filter — scheduler processes
        all tenants. Each returned offer carries its own company_id.
        """
        from datetime import datetime as _dt
        now = _dt.utcnow()
        result = await self._db.execute(
            select(OfferProposal).where(
                and_(
                    OfferProposal.status.in_(["sent", "viewed"]),
                    OfferProposal.response_deadline.isnot(None),
                    OfferProposal.response_deadline < now,
                )
            ).limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_candidate(
        self, company_id: str, candidate_id: str
    ) -> list[OfferProposal]:
        result = await self._db.execute(
            select(OfferProposal).where(
                and_(
                    OfferProposal.company_id == company_id,
                    OfferProposal.candidate_id == candidate_id,
                )
            ).order_by(OfferProposal.created_at.desc())
        )
        return list(result.scalars().all())
