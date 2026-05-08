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

    async def get_by_pending_id(self, pending_id: str) -> HITLPendingAction | None:
        result = await self.db.execute(
            select(HITLPendingAction).where(HITLPendingAction.pending_id == pending_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_pending_for_thread(
        self,
        *,
        thread_id: str,
        now: datetime | None = None,
    ) -> HITLPendingAction | None:
        now = now or datetime.now(UTC)
        result = await self.db.execute(
            select(HITLPendingAction)
            .where(
                HITLPendingAction.thread_id == thread_id,
                HITLPendingAction.status == "pending",
                HITLPendingAction.expires_at > now,
            )
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
