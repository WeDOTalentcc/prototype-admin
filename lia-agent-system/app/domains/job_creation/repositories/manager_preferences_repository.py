"""ManagerPreferences repository — ORM ops for manager_preferences_service.

Per ADR-001: services do not run select(Model) inline.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.manager_preferences import ManagerPreferences


class ManagerPreferencesRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> str:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        return str(company_id)

    async def get_by_company_and_email(
        self,
        company_id: str,
        manager_email: str,
    ) -> Optional[ManagerPreferences]:
        company_id = self._require_company_id(company_id)
        stmt = select(ManagerPreferences).where(
            ManagerPreferences.company_id == company_id,
            ManagerPreferences.manager_email == manager_email,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
