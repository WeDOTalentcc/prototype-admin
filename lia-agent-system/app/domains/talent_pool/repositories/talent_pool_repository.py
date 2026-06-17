"""
TalentPoolRepository — ADR-001 canonical.

Gerencia TalentPool entities para o domínio talent_pool.
Usa lia_config.database.AsyncSessionLocal (padrão deste domínio).

Multi-tenancy: _require_company_id fail-closed em todos os métodos públicos.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.talent_pool import TalentPool


class TalentPoolRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def list_pools(self, company_id: str, status: Optional[str] = None) -> list[TalentPool]:
        """Lista todos os pools do tenant com filtro opcional de status. Fail-closed."""
        self._require_company_id(company_id)
        stmt = (
            select(TalentPool)
            .where(TalentPool.company_id == company_id)
            .order_by(TalentPool.created_at.desc())
        )
        if status:
            stmt = stmt.where(TalentPool.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, pool_id: str, company_id: str) -> Optional[TalentPool]:
        """Busca pool por id validando company_id (multi-tenant guard). Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            select(TalentPool).where(
                TalentPool.id == pool_id,
                TalentPool.company_id == company_id,
            )
        )
        return result.scalars().first()

    async def exists(self, pool_id: str, company_id: str) -> bool:
        """Verifica existência de pool validando company_id. Fail-closed."""
        self._require_company_id(company_id)
        pool = await self.get_by_id(pool_id, company_id)
        return pool is not None
