"""
SourcingCandidateRepository — ADR-001 canonical.
Queries de candidatos para fluxos de sourcing.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SourcingCandidateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def count_active(self, company_id: str) -> int:
        """Conta candidatos ativos no tenant. Fail-closed."""
        self._require_company_id(company_id)
        result = await self.db.execute(
            text(
                "SELECT COUNT(*) FROM candidates "
                "WHERE company_id = :company_id AND status != 'archived'"
            ),
            {"company_id": company_id},
        )
        row = result.fetchone()
        return int(row[0]) if row else 0
