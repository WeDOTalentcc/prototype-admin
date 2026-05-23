"""
CommunicationMatrixRepository — ADR-001 canonical repository.
Consulta políticas de canal de comunicação por tenant.
Usado por: nurture_sequence_tool_registry, referral_tool_registry.
"""
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class CommunicationMatrixRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str) -> None:
        if not company_id:
            raise ValueError("company_id is required — multi-tenancy fail-closed")

    async def get_channel_policy(
        self, company_id: str, channel: str
    ) -> Optional[dict]:
        """
        Retorna política de canal para empresa (requires_approval, is_blocked, etc).

        Prioriza registro específico do company_id; fallback para registro global
        (company_id IS NULL). Fail-closed: _require_company_id valida antes.
        """
        self._require_company_id(company_id)
        result = await self.db.execute(
            text("""
                SELECT channel, requires_approval, is_blocked, daily_limit, metadata
                FROM communication_matrix
                WHERE channel = :channel
                  AND (company_id = :company_id OR company_id IS NULL)
                ORDER BY CASE WHEN company_id = :company_id THEN 0 ELSE 1 END
                LIMIT 1
            """),
            {"company_id": company_id, "channel": channel},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else None
