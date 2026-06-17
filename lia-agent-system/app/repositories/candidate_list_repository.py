"""
CandidateListRepository — session-in-constructor pattern.
Covers all DB operations needed by app/api/v1/candidate_lists.py.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, delete as sa_delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate import Candidate, VacancyCandidate
from app.models.candidate_list import CandidateList, CandidateListMember

logger = logging.getLogger(__name__)


class CandidateListRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── List queries ────────────────────────────────────────────────────────

    async def list_for_company(
        self,
        company_id: Any,
        skip: int = 0,
        limit: int = 50,
        search: str | None = None,
    ) -> tuple[int, list[CandidateList]]:
        """Return (total, items) for a company's active candidate lists."""
        query = select(CandidateList).where(
            and_(
                CandidateList.company_id == company_id,
                CandidateList.is_active,
            )
        )

        if search:
            query = query.where(CandidateList.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset(skip).limit(limit).order_by(CandidateList.updated_at.desc())
        result = await self.db.execute(query)
        return total, list(result.scalars().all())

    async def get_list(
        self,
        list_id: uuid.UUID,
        company_id: Any,
    ) -> CandidateList | None:
        """Fetch a single active list belonging to company_id."""
        result = await self.db.execute(
            select(CandidateList).where(
                and_(
                    CandidateList.id == list_id,
                    CandidateList.company_id == company_id,
                    CandidateList.is_active,
                )
            )
        )
        return result.scalar_one_or_none()

    async def count_members(self, list_id: uuid.UUID) -> int:
        """Return the number of members in a list."""
        result = await self.db.execute(
            select(func.count()).where(CandidateListMember.list_id == list_id)
        )
        return result.scalar() or 0

    # ── CRUD ────────────────────────────────────────────────────────────────

    async def create_list(
        self,
        company_id: Any,
        name: str,
        description: str | None,
        color: str | None,
        created_by: str,
    ) -> CandidateList:
        """Insert a new CandidateList and return the refreshed instance."""
        now = datetime.utcnow()
        new_list = CandidateList(
            id=uuid.uuid4(),
            company_id=company_id,
            name=name,
            description=description,
            color=color,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            is_active=True,
        )
        self.db.add(new_list)
        await self.db.commit()
        await self.db.refresh(new_list)
        return new_list

    async def update_list(
        self,
        lst: CandidateList,
        name: str | None = None,
        description: str | None = None,
        color: str | None = None,
    ) -> CandidateList:
        """Apply partial updates to a list and commit."""
        if name is not None:
            lst.name = name
        if description is not None:
            lst.description = description
        if color is not None:
            lst.color = color
        lst.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lst)
        return lst

    async def soft_delete_list(self, lst: CandidateList) -> None:
        """Soft-delete a list."""
        lst.is_active = False
        lst.updated_at = datetime.utcnow()
        await self.db.commit()

    # ── Member management ───────────────────────────────────────────────────

    async def list_members(
        self,
        list_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[tuple[CandidateListMember, Candidate]]:
        """Return paginated (member, candidate) tuples ordered by added_at desc."""
        query = (
            select(CandidateListMember, Candidate)
            .join(Candidate, CandidateListMember.candidate_id == Candidate.id)
            .where(CandidateListMember.list_id == list_id)
            .offset(skip)
            .limit(limit)
            .order_by(CandidateListMember.added_at.desc())
        )
        result = await self.db.execute(query)
        return result.all()

    async def find_existing_candidate_ids(
        self, candidate_uuids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Return which UUIDs actually exist as Candidates."""
        result = await self.db.execute(
            select(Candidate.id).where(Candidate.id.in_(candidate_uuids))
        )
        return {row[0] for row in result.fetchall()}

    async def find_existing_member_ids(
        self, list_id: uuid.UUID, candidate_uuids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Return which candidate UUIDs are already members of the list."""
        result = await self.db.execute(
            select(CandidateListMember.candidate_id).where(
                and_(
                    CandidateListMember.list_id == list_id,
                    CandidateListMember.candidate_id.in_(candidate_uuids),
                )
            )
        )
        return {row[0] for row in result.fetchall()}

    async def bulk_add_members(
        self,
        list_id: uuid.UUID,
        candidate_uuids: list[uuid.UUID],
        added_by: str,
        notes: str | None = None,
        source: str = "manual",
    ) -> int:
        """Bulk-insert members (on_conflict_do_nothing). Returns added count."""
        if not candidate_uuids:
            return 0
        now = datetime.utcnow()
        await self.db.execute(
            insert(CandidateListMember).values(
                [
                    {
                        "id": uuid.uuid4(),
                        "list_id": list_id,
                        "candidate_id": uid,
                        "added_by": added_by,
                        "added_at": now,
                        "notes": notes,
                        "source": source,
                    }
                    for uid in candidate_uuids
                ]
            ).on_conflict_do_nothing()
        )
        return len(candidate_uuids)

    async def bulk_remove_members(
        self, list_id: uuid.UUID, candidate_uuids: list[uuid.UUID]
    ) -> int:
        """Bulk-delete members. Returns rowcount."""
        if not candidate_uuids:
            return 0
        delete_result = await self.db.execute(
            sa_delete(CandidateListMember).where(
                and_(
                    CandidateListMember.list_id == list_id,
                    CandidateListMember.candidate_id.in_(candidate_uuids),
                )
            )
        )
        return delete_result.rowcount

    async def touch_list(self, lst: CandidateList) -> None:
        """Update updated_at and commit (no refresh)."""
        lst.updated_at = datetime.utcnow()
        await self.db.commit()

    # ── Members query (no join) ─────────────────────────────────────────────

    async def get_members_for_candidates(
        self,
        list_id: uuid.UUID,
        candidate_ids: list[uuid.UUID] | None = None,
    ) -> list[CandidateListMember]:
        """Return list members, optionally filtered by candidate_ids."""
        if candidate_ids is not None:
            query = select(CandidateListMember).where(
                and_(
                    CandidateListMember.list_id == list_id,
                    CandidateListMember.candidate_id.in_(candidate_ids),
                )
            )
        else:
            query = select(CandidateListMember).where(
                CandidateListMember.list_id == list_id
            )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── VacancyCandidate helpers ────────────────────────────────────────────

    async def find_vacancy_candidate(
        self, job_vacancy_id: uuid.UUID, candidate_id: uuid.UUID
    ) -> VacancyCandidate | None:
        """Return existing VacancyCandidate link or None."""
        result = await self.db.execute(
            select(VacancyCandidate).where(
                and_(
                    VacancyCandidate.vacancy_id == job_vacancy_id,
                    VacancyCandidate.candidate_id == candidate_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_vacancy_candidate(
        self,
        company_id: Any,
        job_vacancy_id: uuid.UUID,
        candidate_id: uuid.UUID,
    ) -> VacancyCandidate:
        """Insert a new VacancyCandidate (no commit — caller commits)."""
        now = datetime.utcnow()
        # Task #1306: record the structural stage link so SLA detection can join
        # by id instead of fragile name matching.
        from app.shared.services.stage_id_resolver import (
            resolve_recruitment_stage_id,
        )

        recruitment_stage_id = await resolve_recruitment_stage_id(
            self.db, str(company_id), "sourcing"
        )
        vc = VacancyCandidate(
            id=uuid.uuid4(),
            company_id=company_id,
            vacancy_id=job_vacancy_id,
            candidate_id=candidate_id,
            stage="sourcing",
            recruitment_stage_id=recruitment_stage_id,
            status="sourced",
            source="list",
            created_at=now,
            updated_at=now,
        )
        self.db.add(vc)
        return vc

    async def commit(self) -> None:
        """Explicit commit for multi-step operations."""
        await self.db.commit()

    async def rollback(self) -> None:
        """Explicit rollback."""
        await self.db.rollback()
