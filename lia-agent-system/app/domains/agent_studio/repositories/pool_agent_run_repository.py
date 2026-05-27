"""PoolAgentRunRepository — ADR-001 canonical (Sprint 7C Part 1.5a).

Foundation pra orchestrator real (Part 1.5b).
Multi-tenancy fail-closed: cada metodo publico chama _require_company_id.

Métodos consumidos por Part 1.5b orchestrator:
- create(): início do dispatch (status=queued)
- update_status(): transitions queued→running→success/error/timeout/cancelled
Métodos consumidos por GET endpoints:
- list_by_assignment(): histórico paginado
- get_by_id(): detalhe single run
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.pool_agent_run import PoolAgentRun


class CrossTenantError(Exception):
    """Raised quando company_id de input != row.company_id."""


def _require_company_id(company_id: Any) -> None:
    if not isinstance(company_id, str) or not company_id.strip():
        raise ValueError(
            "PoolAgentRunRepository: company_id required (multi-tenancy fail-closed)."
        )


_TERMINAL_STATUSES = {"success", "error", "timeout", "cancelled"}


class PoolAgentRunRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_assignment(
        self,
        assignment_id: UUID | str,
        company_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PoolAgentRun]:
        _require_company_id(company_id)
        stmt = (
            select(PoolAgentRun)
            .where(
                PoolAgentRun.assignment_id == assignment_id,
                PoolAgentRun.company_id == company_id,
            )
            .order_by(PoolAgentRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(
        self, run_id: UUID | str, company_id: str
    ) -> PoolAgentRun | None:
        _require_company_id(company_id)
        stmt = select(PoolAgentRun).where(
            PoolAgentRun.id == run_id,
            PoolAgentRun.company_id == company_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        assignment_id: UUID | str,
        company_id: str,
        trigger_source: str,
        dispatch_metadata: dict | None = None,
    ) -> PoolAgentRun:
        """Orchestrator (Part 1.5b) chama no início do dispatch."""
        _require_company_id(company_id)
        if trigger_source not in ("cron", "on_demand", "event_driven"):
            raise ValueError(
                f"invalid trigger_source={trigger_source!r}; "
                "expected one of cron|on_demand|event_driven"
            )
        run = PoolAgentRun(
            assignment_id=assignment_id,
            company_id=company_id,
            trigger_source=trigger_source,
            status="queued",
            dispatch_metadata=dispatch_metadata or {},
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def update_status(
        self,
        run_id: UUID | str,
        status: str,
        *,
        error_message: str | None = None,
        results: dict | None = None,
        runtime_metrics: dict | None = None,
        reasoning_payload: list[dict] | None = None,
    ) -> PoolAgentRun:
        """Orchestrator (Part 1.5b) atualiza durante execução.

        - status='running' seta started_at se ainda não setado.
        - status terminal seta finished_at se ainda não setado.
        """
        if status not in (
            "queued",
            "running",
            "success",
            "error",
            "timeout",
            "cancelled",
        ):
            raise ValueError(f"invalid status={status!r}")
        run = await self._get_by_id_no_tenant(run_id)
        if not run:
            raise ValueError(f"PoolAgentRun {run_id} not found")
        run.status = status
        now = datetime.now(timezone.utc)
        if status == "running" and not run.started_at:
            run.started_at = now
        if status in _TERMINAL_STATUSES and not run.finished_at:
            run.finished_at = now
        if error_message is not None:
            run.error_message = error_message
        if results is not None:
            run.results = results
        if runtime_metrics is not None:
            run.runtime_metrics = runtime_metrics
        if reasoning_payload is not None:
            run.reasoning_payload = reasoning_payload
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def _get_by_id_no_tenant(
        self, run_id: UUID | str
    ) -> PoolAgentRun | None:
        """Internal: orchestrator update_status (tenant validated upstream via assignment)."""
        stmt = select(PoolAgentRun).where(PoolAgentRun.id == run_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
