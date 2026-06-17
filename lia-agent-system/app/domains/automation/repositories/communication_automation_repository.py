"""CommunicationAutomationRepository — data access for CommunicationAutomation.

Per ADR-001: services delegate SQL access here.
Multi-tenant: every public method requires company_id.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.automation import CommunicationAutomation

logger = logging.getLogger(__name__)


class CommunicationAutomationRepository:
    """Repository for CommunicationAutomation rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id) -> None:
        if not company_id:
            raise ValueError(
                "Multi-tenancy invariant violation: company_id required "
                "for CommunicationAutomationRepository operations (ADR-001)."
            )

    async def list_active_for_trigger(
        self,
        company_id: str,
        trigger_type: str,
    ) -> list[CommunicationAutomation]:
        """Active automations matching (company, trigger_type)."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(CommunicationAutomation).where(
                and_(
                    CommunicationAutomation.company_id == company_id,
                    CommunicationAutomation.trigger_type == trigger_type,
                    CommunicationAutomation.is_active,
                )
            )
        )
        return list(result.scalars().all())

    async def find_first_active_for_trigger(
        self,
        company_id: str,
        trigger_type: str,
    ) -> CommunicationAutomation | None:
        """Single active automation for (company, trigger_type)."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(CommunicationAutomation).where(
                CommunicationAutomation.company_id == company_id,
                CommunicationAutomation.trigger_type == trigger_type,
                CommunicationAutomation.is_active,
            )
        )
        return result.scalar_one_or_none()

    async def list_paginated(
        self,
        company_id: str,
        *,
        is_active: bool | None = None,
        trigger_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Paginated list with total count."""
        self._require_company_id(company_id)

        query = select(CommunicationAutomation).where(
            CommunicationAutomation.company_id == company_id
        )
        if is_active is not None:
            query = query.where(CommunicationAutomation.is_active == is_active)
        if trigger_type:
            query = query.where(CommunicationAutomation.trigger_type == trigger_type)

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = (
            query.order_by(desc(CommunicationAutomation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        automations = list(result.scalars().all())

        return {
            "automations": automations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_by_id_for_company(
        self, automation_id: str, company_id: str
    ) -> CommunicationAutomation | None:
        """Single automation by id, scoped to company."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(CommunicationAutomation).where(
                and_(
                    CommunicationAutomation.id == automation_id,
                    CommunicationAutomation.company_id == company_id,
                )
            )
        )
        return result.scalar_one_or_none()


    # ── Sprint Q2 ADR-001 cleanup: AutomationExecutionLog access ──────

    async def list_execution_logs(
        self,
        company_id: str,
        *,
        automation_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        """Paginated execution logs for a company, optionally scoped to one automation."""
        from lia_models.automation import AutomationExecutionLog

        self._require_company_id(company_id)

        query = select(AutomationExecutionLog).where(
            AutomationExecutionLog.company_id == company_id
        )
        if automation_id:
            query = query.where(
                AutomationExecutionLog.automation_id == automation_id
            )

        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        query = (
            query.order_by(desc(AutomationExecutionLog.executed_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return {"logs": logs, "total": total, "limit": limit, "offset": offset}
