"""FairnessReportRepository — DB access layer for FairnessGuard audit logs.

Extracted from app/api/v1/fairness_reports.py as part of Phase 2 refactor.
Tables covered:
  - fairness_audit_logs
"""
import logging
import uuid
from datetime import datetime

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class FairnessReportRepository:
    """Repository for FairnessGuard reporting and audit-log data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary_by_category(
        self,
        since: datetime,
        company_id: str | None = None,
    ) -> list:
        """Return (category, blocks, warnings, last_occurrence) grouped by category."""
        from app.models.fairness_audit import FairnessAuditLog

        stmt = select(
            FairnessAuditLog.category,
            func.count().filter(FairnessAuditLog.is_blocked.is_(True)).label("blocks"),
            func.count().filter(FairnessAuditLog.is_blocked.is_(False)).label("warnings"),
            func.max(FairnessAuditLog.created_at).label("last_occurrence"),
        ).where(FairnessAuditLog.created_at >= since)

        if company_id:
            stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))

        stmt = stmt.group_by(FairnessAuditLog.category)
        result = await self.db.execute(stmt)
        return result.all()

    async def get_daily_trend(
        self,
        since: datetime,
        company_id: str | None = None,
    ) -> list:
        """Return (day, blocks, warnings) per day for a time-series trend."""
        from app.models.fairness_audit import FairnessAuditLog

        stmt = select(
            cast(FairnessAuditLog.created_at, Date).label("day"),
            func.count().filter(FairnessAuditLog.is_blocked.is_(True)).label("blocks"),
            func.count().filter(FairnessAuditLog.is_blocked.is_(False)).label("warnings"),
        ).where(FairnessAuditLog.created_at >= since)

        if company_id:
            stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))

        stmt = stmt.group_by(cast(FairnessAuditLog.created_at, Date)).order_by("day")
        result = await self.db.execute(stmt)
        return result.all()

    async def get_audit_logs_paginated(
        self,
        since: datetime,
        company_id: str | None = None,
        category: str | None = None,
        blocked_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list]:
        """Return (total_count, rows) for paginated audit log queries."""
        from app.models.fairness_audit import FairnessAuditLog

        # TENANT-EXEMPT: fairness report cross-tenant aggregate; LGPD-safe per ADR-LGPD-001 §3 (anonymized aggregate)
        stmt = select(FairnessAuditLog).where(FairnessAuditLog.created_at >= since)

        if company_id:
            try:
                stmt = stmt.where(FairnessAuditLog.company_id == uuid.UUID(company_id))
            except ValueError:
                pass

        if category:
            stmt = stmt.where(FairnessAuditLog.category == category)

        if blocked_only:
            stmt = stmt.where(FairnessAuditLog.is_blocked.is_(True))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(FairnessAuditLog.created_at.desc()).limit(limit).offset(offset)
        rows = (await self.db.execute(stmt)).scalars().all()
        return total, list(rows)

    async def get_export_data(
        self,
        since: datetime,
        company_id: str | None = None,
    ) -> list:
        """Return summary rows for CSV/JSON export (same shape as get_summary_by_category)."""
        return await self.get_summary_by_category(since, company_id)
