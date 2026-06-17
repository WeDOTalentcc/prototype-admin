"""CandidateAttachmentRepository — DB access for CandidateAttachment records.

Extracted from app/domains/cv_screening/services/attachment_service.py per ADR-001.
All queries scoped by company_id (multi-tenancy invariant).
"""
from __future__ import annotations

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.candidate_attachment import CandidateAttachment


class CandidateAttachmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        attachment_id: str,
        company_id: str | None = None,
    ) -> CandidateAttachment | None:
        """Get attachment by id, optionally scoped to tenant.

        Multi-tenancy defense-in-depth: pass company_id to enforce tenant filter
        at query level (defense-in-depth on top of Postgres RLS — Task #1143).
        When company_id is None, relies on RLS at the DB layer.

        TODO(harness): new callers should always pass company_id; legacy callers
        in attachment_service still pass None. Migrate them in a follow-up sprint
        and then change this signature to require company_id.
        """
        conditions = [CandidateAttachment.id == attachment_id]
        if company_id:
            conditions.append(CandidateAttachment.company_id == company_id)
        result = await self.db.execute(
            select(CandidateAttachment).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        company_id: str,
        candidate_id: str | None = None,
        file_type: str | None = None,
        upload_source: str | None = None,
        is_active: bool | None = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CandidateAttachment], int]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        where_conditions = [CandidateAttachment.company_id == company_id]
        if candidate_id:
            where_conditions.append(CandidateAttachment.candidate_id == candidate_id)
        if file_type:
            where_conditions.append(CandidateAttachment.file_type == file_type)
        if upload_source:
            where_conditions.append(CandidateAttachment.upload_source == upload_source)
        if is_active is not None:
            where_conditions.append(CandidateAttachment.is_active == is_active)

        # TENANT-EXEMPT: dynamic builder — where_conditions list is seeded with
        # CandidateAttachment.company_id == company_id (line 37). Sensor cannot trace
        # company_id through and_(*where_conditions) spread. Defense-in-depth via
        # require_company_id raise above + Postgres RLS (Task #1143).
        count_query = (
            select(func.count())
            .select_from(CandidateAttachment)
            .where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # TENANT-EXEMPT: data_query — same dynamic builder as count_query above.
        # where_conditions seeded with CandidateAttachment.company_id filter.
        data_query = (
            select(CandidateAttachment)
            .where(and_(*where_conditions))
            .order_by(desc(CandidateAttachment.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(data_query)
        attachments = list(result.scalars().all())
        return attachments, total

    async def list_for_candidate(
        self,
        *,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CandidateAttachment], int]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        where_conditions = [
            CandidateAttachment.candidate_id == candidate_id,
            CandidateAttachment.company_id == company_id,
            CandidateAttachment.is_active,
        ]
        # TENANT-EXEMPT: dynamic builder — where_conditions list is seeded with
        # CandidateAttachment.company_id == company_id (above). Sensor cannot trace
        # company_id through and_(*where_conditions) spread.
        count_query = (
            select(func.count())
            .select_from(CandidateAttachment)
            .where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # TENANT-EXEMPT: data_query — same dynamic builder as count_query above.
        # where_conditions seeded with CandidateAttachment.company_id filter.
        data_query = (
            select(CandidateAttachment)
            .where(and_(*where_conditions))
            .order_by(desc(CandidateAttachment.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(data_query)
        attachments = list(result.scalars().all())
        return attachments, total

    async def add(self, attachment: CandidateAttachment) -> CandidateAttachment:
        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)
        return attachment

    async def commit_changes(self, attachment: CandidateAttachment) -> CandidateAttachment:
        await self.db.commit()
        await self.db.refresh(attachment)
        return attachment

    async def find_by_hash(
        self,
        file_hash: str,
        company_id: str,
    ) -> CandidateAttachment | None:
        """Return first active attachment with matching SHA-256 hash in this tenant.

        Used for file-level dedup on CV uploads (GAP-05-006).
        company_id is required — multi-tenancy invariant.
        """
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        result = await self.db.execute(
            select(CandidateAttachment).where(
                CandidateAttachment.file_hash == file_hash,
                CandidateAttachment.company_id == company_id,
                CandidateAttachment.is_active.is_(True),
            )
        )
        return result.scalars().first()
