"""
AgentVersionSnapshotRepository — acesso a dados de snapshots de versão de agentes.

ADR-001: toda query a AgentVersionSnapshot passa por aqui.
Multi-tenancy: company_id required em todos os métodos públicos (fail-closed via _require_company_id).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.agent_version_snapshot import AgentVersionSnapshot


class AgentVersionSnapshotRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _require_company_id(company_id: str | None) -> str:
        if not company_id:
            raise ValueError("company_id obrigatório — multi-tenancy fail-closed")
        return company_id

    async def list_for_agent(
        self,
        agent_id: str,
        company_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AgentVersionSnapshot], int]:
        """Lista snapshots de um agente (mais recentes primeiro) + total."""
        cid = self._require_company_id(company_id)
        base_filter = and_(
            AgentVersionSnapshot.agent_id == agent_id,
            AgentVersionSnapshot.company_id == cid,
        )
        total = await self.db.scalar(
            select(func.count(AgentVersionSnapshot.id)).where(base_filter)
        )
        result = await self.db.execute(
            select(AgentVersionSnapshot)
            .where(base_filter)
            .order_by(desc(AgentVersionSnapshot.version))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total or 0

    async def get_by_version(
        self,
        agent_id: str,
        version: int,
        company_id: str,
    ) -> Optional[AgentVersionSnapshot]:
        """Busca snapshot por versão específica."""
        cid = self._require_company_id(company_id)
        result = await self.db.execute(
            select(AgentVersionSnapshot).where(
                and_(
                    AgentVersionSnapshot.agent_id == agent_id,
                    AgentVersionSnapshot.version == version,
                    AgentVersionSnapshot.company_id == cid,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(self, snapshot: AgentVersionSnapshot) -> AgentVersionSnapshot:
        """Persiste novo snapshot."""
        self._require_company_id(snapshot.company_id)
        self.db.add(snapshot)
        await self.db.flush()
        return snapshot

    async def count_for_agent(self, agent_id: str, company_id: str) -> int:
        """Retorna total de snapshots de um agente."""
        cid = self._require_company_id(company_id)
        return await self.db.scalar(
            select(func.count(AgentVersionSnapshot.id)).where(
                and_(
                    AgentVersionSnapshot.agent_id == agent_id,
                    AgentVersionSnapshot.company_id == cid,
                )
            )
        ) or 0
