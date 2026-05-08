"""Company module repository — all ORM ops for module_service.

Per ADR-001: services do not run select(Model) inline.
All multi-tenant reads enforce company_id filter.
"""
from __future__ import annotations

import uuid as _uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.billing import CompanyModule


class CompanyModuleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str | _uuid.UUID) -> str:
        if not company_id:
            raise ValueError("company_id is required (multi-tenancy invariant)")
        return str(company_id)

    async def get_by_company_and_name(
        self, company_id: str, module_name: str
    ) -> Optional[CompanyModule]:
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyModule).where(
            and_(
                CompanyModule.company_id == company_id,
                CompanyModule.module_name == module_name,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_company(self, company_id: str) -> list[CompanyModule]:
        company_id = self._require_company_id(company_id)
        stmt = select(CompanyModule).where(CompanyModule.company_id == company_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, module_id: str) -> Optional[CompanyModule]:
        try:
            uid = _uuid.UUID(module_id)
        except (ValueError, AttributeError):
            return None
        stmt = select(CompanyModule).where(CompanyModule.id == uid)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add(self, mod: CompanyModule) -> CompanyModule:
        self.db.add(mod)
        await self.db.flush()
        return mod
