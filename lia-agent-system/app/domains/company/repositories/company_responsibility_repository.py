"""CompanyResponsibilityRepository - data access for CompanyResponsibility.

Per ADR-001: extracted from responsibilities_catalog_service.py.
"""
from __future__ import annotations

import logging

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.company_learning import CompanyResponsibility

logger = logging.getLogger(__name__)


class CompanyResponsibilityRepository:
    """Repository for CompanyResponsibility entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _require_company_id(company_id) -> None:
        if not company_id:
            raise ValueError(
                "Multi-tenancy invariant violation: company_id required "
                "for CompanyResponsibilityRepository operations (ADR-001)."
            )

    async def list_promoted_for_company(
        self, company_id
    ) -> list[CompanyResponsibility]:
        """Return promoted responsibilities (times_confirmed >= 3) for company."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(CompanyResponsibility).where(
                and_(
                    CompanyResponsibility.company_id == company_id,
                    CompanyResponsibility.is_promoted,
                )
            )
        )
        return list(result.scalars().all())
