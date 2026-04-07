"""ShortListRepository — DB operations for short list management.

Short lists are CandidateList records with description prefixed by 'shortlist:'.
Extracted from app/api/v1/short_lists.py as part of Phase 2 refactor.
"""
import logging
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_list import CandidateList, CandidateListMember

logger = logging.getLogger(__name__)

_SHORTLIST_PREFIX = "shortlist:"


class ShortListRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Queries ──────────────────────────────────────────────────────────────

    async def list_for_company(
        self,
        company_id: str,
        job_id: str | None = None,
    ) -> list[CandidateList]:
        """List all active short lists for a company, optionally filtered by job_id."""
        result = await self.db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.company_id == company_id,
                    CandidateList.is_active,
                    CandidateList.description.like(f"{_SHORTLIST_PREFIX}%"),
                )
            ).order_by(CandidateList.created_at.desc())
        )
        records = result.scalars().all()

        if job_id:
            records = [
                r for r in records
                if self._decode_job_id(r.description) == job_id
            ]
        return list(records)

    async def get_by_id(
        self,
        list_id: UUID,
        company_id: str,
    ) -> CandidateList | None:
        """Fetch a specific short list by ID and company."""
        result = await self.db.execute(
            select(CandidateList).where(
                CandidateList.id == list_id,
                CandidateList.company_id == company_id,
            )
        )
        record = result.scalar_one_or_none()
        if record and not record.description.startswith(_SHORTLIST_PREFIX):
            return None
        return record

    async def get_member(
        self,
        list_id: UUID,
        candidate_id: str,
    ) -> CandidateListMember | None:
        """Fetch a specific member of a short list."""
        result = await self.db.execute(
            select(CandidateListMember).where(
                CandidateListMember.list_id == list_id,
                CandidateListMember.candidate_id == candidate_id,
            )
        )
        return result.scalar_one_or_none()

    # ── Writes ───────────────────────────────────────────────────────────────

    async def create(
        self,
        company_id: str,
        name: str,
        description_encoded: str,
        created_by: str,
    ) -> CandidateList:
        """Create a new short list (CandidateList with shortlist: prefix)."""
        record = CandidateList(
            company_id=company_id,
            name=name,
            description=description_encoded,
            created_by=created_by,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def add_member(
        self,
        list_id: UUID,
        candidate_id: str,
        notes: str | None = None,
    ) -> CandidateListMember:
        """Add a candidate to a short list."""
        member = CandidateListMember(
            list_id=list_id,
            candidate_id=candidate_id,
            notes=notes,
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_member(self, member: CandidateListMember) -> None:
        """Remove a candidate member from a short list."""
        await self.db.delete(member)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _decode_job_id(description: str | None) -> str:
        """Extract job_id from encoded description field."""
        if not description or not description.startswith(_SHORTLIST_PREFIX):
            return ""
        rest = description[len(_SHORTLIST_PREFIX):]
        return rest.split("|", 1)[0] if "|" in rest else rest
