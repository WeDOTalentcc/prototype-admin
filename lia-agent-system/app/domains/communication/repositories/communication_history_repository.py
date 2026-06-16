"""CommunicationHistoryRepository — DB access for CommunicationHistory records.

Extracted from app/domains/communication/services/communication_history_service.py per ADR-001.
All multi-row queries scoped by company_id (multi-tenancy invariant).
"""
from __future__ import annotations

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CommunicationHistory


class CommunicationHistoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        communication_id: str,
        company_id: str | None = None,
    ) -> CommunicationHistory | None:
        """Get CommunicationHistory by id.

        Multi-tenancy defense-in-depth: pass company_id to filter at query level
        (Postgres RLS — Task #1143 — guards by default).
        """
        conditions = [CommunicationHistory.id == communication_id]
        if company_id:
            conditions.append(CommunicationHistory.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(CommunicationHistory).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self,
        *,
        company_id: str,
        candidate_id: str | None = None,
        vacancy_id: str | None = None,
        communication_type: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[CommunicationHistory], int]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        where_conditions = [CommunicationHistory.company_id == company_id]
        if candidate_id:
            where_conditions.append(CommunicationHistory.candidate_id == candidate_id)
        if vacancy_id:
            where_conditions.append(CommunicationHistory.vacancy_id == vacancy_id)
        if communication_type:
            where_conditions.append(CommunicationHistory.communication_type == communication_type)
        if channel:
            where_conditions.append(CommunicationHistory.channel == channel)
        if status:
            where_conditions.append(CommunicationHistory.status == status)

        # TENANT-EXEMPT: dynamic builder — where_conditions seeded with
        # CommunicationHistory.company_id == company_id (line 38). Sensor cannot
        # trace company_id through and_(*where_conditions) spread.
        count_query = (
            select(func.count())
            .select_from(CommunicationHistory)
            .where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # TENANT-EXEMPT: data_query — same dynamic builder as count_query above.
        data_query = (
            select(CommunicationHistory)
            .where(and_(*where_conditions))
            .order_by(desc(CommunicationHistory.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(data_query)
        return list(result.scalars().all()), total

    async def list_for_candidate(
        self,
        *,
        candidate_id: str,
        company_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CommunicationHistory], int]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        where_conditions = [
            CommunicationHistory.candidate_id == candidate_id,
            CommunicationHistory.company_id == company_id,
        ]
        # TENANT-EXEMPT: dynamic builder — where_conditions seeded with
        # CommunicationHistory.company_id filter above.
        count_query = (
            select(func.count())
            .select_from(CommunicationHistory)
            .where(and_(*where_conditions))
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # TENANT-EXEMPT: data_query — same dynamic builder as count_query above.
        data_query = (
            select(CommunicationHistory)
            .where(and_(*where_conditions))
            .order_by(desc(CommunicationHistory.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(data_query)
        return list(result.scalars().all()), total

    async def add(self, communication: CommunicationHistory) -> CommunicationHistory:
        self.db.add(communication)
        await self.db.commit()
        await self.db.refresh(communication)
        return communication

    async def commit_changes(self, communication: CommunicationHistory) -> CommunicationHistory:
        await self.db.commit()
        await self.db.refresh(communication)
        return communication

    async def transfer_pending_ownership(
        self,
        *,
        job_id: str,
        from_user_ids: list[str],
        to_user_id: str,
        company_id: str,
        pending_statuses: list,
    ) -> int:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        stmt = (
            update(CommunicationHistory)
            .where(
                and_(
                    CommunicationHistory.vacancy_id == job_id,
                    CommunicationHistory.sent_by.in_(from_user_ids),
                    CommunicationHistory.company_id == company_id,
                    CommunicationHistory.status.in_(pending_statuses),
                )
            )
            .values(sent_by=to_user_id)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount or 0
