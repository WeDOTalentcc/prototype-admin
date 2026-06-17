"""DataIncident repository — ORM ops for incident_response_service.

Per ADR-001: services do not run select(Model) inline.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.incident import DataIncident, IncidentStatus


class DataIncidentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> str:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        return str(company_id)

    async def list_open_for_company(self, company_id: str) -> list[DataIncident]:
        company_id = self._require_company_id(company_id)
        stmt = (
            select(DataIncident)
            .where(
                DataIncident.company_id == company_id,
                DataIncident.status.in_([
                    IncidentStatus.OPEN,
                    IncidentStatus.INVESTIGATING,
                ]),
            )
            .order_by(DataIncident.incident_detected_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self,
        incident_id: str,
        company_id: str | None = None,
    ) -> Optional[DataIncident]:
        """Lookup DataIncident por id.

        Sprint B.1 tail (2026-05-22): company_id RECOMENDADO (defense-in-depth).
        """
        # TENANT-EXEMPT: defense-in-depth — caller eh tenant-gated; company_id opcional desde Sprint B.1 tail
        if company_id is not None:
            company_id = self._require_company_id(company_id)
            stmt = select(DataIncident).where(
                DataIncident.id == incident_id,
                DataIncident.company_id == company_id,
            )
        else:
            # TENANT-EXEMPT: backwards-compat — caller validates incident.company_id post-fetch
            stmt = select(DataIncident).where(DataIncident.id == incident_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
