"""PoolAgentAssignmentRepository — ADR-001 canonical (Sub-sprint 7A).

Multi-tenancy fail-closed: cada metodo publico chama _require_company_id.
Cross-tenant invariant check em create() — pool.company_id == agent.company_id == company_id.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.custom_agent import AgentType, CustomAgent
from lia_models.pool_agent_assignment import PoolAgentAssignment
from lia_models.talent_pool import TalentPool


class CrossTenantError(Exception):
    """Raised quando pool.company_id != agent.company_id != jwt company_id."""


def _require_company_id(company_id: Any) -> None:
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError(
            "PoolAgentAssignmentRepository: company_id required (multi-tenancy fail-closed)."
        )


class PoolAgentAssignmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_by_pool(
        self, *, pool_id: str, company_id: str
    ) -> list[PoolAgentAssignment]:
        _require_company_id(company_id)
        stmt = (
            select(PoolAgentAssignment)
            .where(
                PoolAgentAssignment.talent_pool_id == pool_id,
                PoolAgentAssignment.company_id == company_id,
            )
            .order_by(PoolAgentAssignment.created_at.desc())
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, *, assignment_id: str, company_id: str
    ) -> PoolAgentAssignment | None:
        _require_company_id(company_id)
        stmt = select(PoolAgentAssignment).where(
            PoolAgentAssignment.id == assignment_id,
            PoolAgentAssignment.company_id == company_id,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        company_id: str,
        pool_id: str,
        custom_agent_id: str,
        schedule_type: str = "on_demand",
        schedule_config: dict[str, Any] | None = None,
        config_overrides: dict[str, Any] | None = None,
        created_by: str,
    ) -> PoolAgentAssignment:
        _require_company_id(company_id)

        # Cross-tenant invariant — fetch pool + agent, assert company_id match
        pool_stmt = select(TalentPool).where(TalentPool.id == pool_id)
        agent_stmt = select(CustomAgent).where(CustomAgent.id == custom_agent_id)
        pool = (await self._db.execute(pool_stmt)).scalar_one_or_none()
        agent = (await self._db.execute(agent_stmt)).scalar_one_or_none()

        if pool is None:
            raise ValueError(f"TalentPool {pool_id} not found")
        if agent is None:
            raise ValueError(f"CustomAgent {custom_agent_id} not found")
        if pool.company_id != company_id:
            raise CrossTenantError(
                f"Pool company={pool.company_id} != jwt company={company_id}"
            )
        # first_party agents have company_id=None by design (globally available).
        # Assigning them to any tenant pool is always valid — skip cross-tenant check.
        if agent.agent_type != AgentType.first_party and agent.company_id != company_id:
            raise CrossTenantError(
                f"Agent company={agent.company_id} != jwt company={company_id}"
            )

        # Write legado mantido read-write durante a janela de transição C1.5
        # (Fase 2.5). Endpoints talent_pool_agents.py ainda criam assignments aqui.
        # Backlog: migrar callers pra AgentDeployment(target_type=talent_pool) e
        # tornar a tabela read-only/drop.
        # CANONICAL-EXEMPT: legacy talent_pool assignment write (transição C1.5).
        row = PoolAgentAssignment(
            company_id=company_id,
            talent_pool_id=pool_id,
            custom_agent_id=custom_agent_id,
            schedule_type=schedule_type,
            schedule_config=schedule_config or {},
            config_overrides=config_overrides or {},
            status="active",
            runtime_metrics={},
            created_by=created_by,
        )
        self._db.add(row)
        await self._db.flush()
        return row

    async def update(
        self,
        *,
        assignment_id: str,
        company_id: str,
        **fields: Any,
    ) -> PoolAgentAssignment | None:
        _require_company_id(company_id)
        row = await self.get_by_id(assignment_id=assignment_id, company_id=company_id)
        if row is None:
            return None
        allowed = {"status", "schedule_type", "schedule_config", "config_overrides"}
        for k, v in fields.items():
            if k in allowed and v is not None:
                setattr(row, k, v)
        await self._db.flush()
        return row

    async def delete(self, *, assignment_id: str, company_id: str) -> bool:
        _require_company_id(company_id)
        row = await self.get_by_id(assignment_id=assignment_id, company_id=company_id)
        if row is None:
            return False
        await self._db.delete(row)
        await self._db.flush()
        return True

    async def mark_run(
        self,
        *,
        assignment_id: str,
        company_id: str,
        run_status: str,
    ) -> None:
        """Update last_run_at + last_run_status (chamado pelo dispatch worker)."""
        _require_company_id(company_id)
        from datetime import datetime, timezone
        row = await self.get_by_id(assignment_id=assignment_id, company_id=company_id)
        if row is None:
            return
        row.last_run_at = datetime.now(timezone.utc)
        row.last_run_status = run_status
        await self._db.flush()
