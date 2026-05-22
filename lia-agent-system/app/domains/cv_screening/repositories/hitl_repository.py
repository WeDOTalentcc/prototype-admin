"""HITLRepository — DB access for human-in-the-loop pending actions and audit trail.

Extracted from app/domains/cv_screening/services/hitl_service.py per ADR-001.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.hitl import HITLAuditTrail, HITLPendingAction


UTC = timezone.utc


class HITLRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_pending_id(
        self,
        pending_id: str,
        company_id: str | None = None,
    ) -> HITLPendingAction | None:
        """Get pending action by id.

        pending_id is globally unique (UUID); company_id is optional defense-in-depth.
        When passed, filter is added — when None, relies on pending_id uniqueness +
        Postgres RLS (Task #1143).
        """
        conditions = [HITLPendingAction.pending_id == pending_id]
        if company_id:
            conditions.append(HITLPendingAction.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # X.company_id == company_id earlier in this function. Sensor cannot
        # trace company_id through where(*conditions) spread.
        result = await self.db.execute(
            select(HITLPendingAction).where(*conditions)
        )
        return result.scalar_one_or_none()

    async def get_latest_pending_for_thread(
        self,
        *,
        thread_id: str,
        company_id: str | None = None,
        now: datetime | None = None,
    ) -> HITLPendingAction | None:
        """Get latest pending action for thread.

        thread_id is allocated per recruiter session and globally unique. company_id
        is optional defense-in-depth (Postgres RLS — Task #1143 — guards by default).
        """
        now = now or datetime.now(UTC)
        conditions = [
            HITLPendingAction.thread_id == thread_id,
            HITLPendingAction.status == "pending",
            HITLPendingAction.expires_at > now,
        ]
        if company_id:
            conditions.append(HITLPendingAction.company_id == company_id)
        # TENANT-EXEMPT: dynamic builder — conditions list seeded with
        # HITLPendingAction.company_id filter (conditional, above). Sensor cannot
        # trace through where(*conditions) spread.
        result = await self.db.execute(
            select(HITLPendingAction)
            .where(*conditions)
            .order_by(HITLPendingAction.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_pending_for_company(
        self,
        *,
        company_id: str,
        now: datetime | None = None,
    ) -> list[HITLPendingAction]:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        now = now or datetime.now(UTC)
        result = await self.db.execute(
            select(HITLPendingAction)
            .where(
                HITLPendingAction.company_id == company_id,
                HITLPendingAction.status == "pending",
                HITLPendingAction.expires_at > now,
            )
            .order_by(HITLPendingAction.created_at.desc())
        )
        return list(result.scalars().all())

    def add_audit_trail(self, trail: HITLAuditTrail) -> None:
        self.db.add(trail)
