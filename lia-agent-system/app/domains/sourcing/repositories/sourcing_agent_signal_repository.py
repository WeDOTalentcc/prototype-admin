"""SourcingAgentSignal repository — canonical ADR-001 abstraction.

Wave C1.4 (2026-05-27). Encapsulates reads against `sourcing_agent_signals`
that previously lived inline in `app/services/sourcing_agent_orchestrator.py`.

Multi-tenancy: signals are scoped by `custom_agent_id` (FK → custom_agents).
Caller is expected to have already validated tenant ownership of the parent
agent via `CustomAgentRepository.get_by_id(company_id=...)` before invoking
read methods here — these methods take `custom_agent_id` (already verified).
The write paths inside the orchestrator stay tied to the agent row which is
loaded under tenant scope.
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.sourcing_agent import SourcingAgentSignal


def _require_custom_agent_id(custom_agent_id: Any) -> None:
    """Fail-closed guard — caller must pass a non-empty agent id."""
    if custom_agent_id is None:
        raise ValueError(
            "SourcingAgentSignalRepository: custom_agent_id is required."
        )
    if isinstance(custom_agent_id, str) and not custom_agent_id.strip():
        raise ValueError(
            "SourcingAgentSignalRepository: custom_agent_id is required."
        )


class SourcingAgentSignalRepository:
    """ADR-001 canonical reads/writes for sourcing_agent_signals."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, signal: SourcingAgentSignal) -> SourcingAgentSignal:
        """Persist a constructed signal. Caller commits."""
        _require_custom_agent_id(signal.custom_agent_id)
        self._db.add(signal)
        await self._db.flush()
        return signal

    async def count_for_agent(
        self, *, custom_agent_id: uuid.UUID | str
    ) -> int:
        """Total signals attached to a sourcing agent."""
        _require_custom_agent_id(custom_agent_id)
        stmt = select(func.count()).where(
            SourcingAgentSignal.custom_agent_id == custom_agent_id
        )
        result = await self._db.execute(stmt)
        return int(result.scalar() or 0)

    async def list_recent(
        self,
        *,
        custom_agent_id: uuid.UUID | str,
        limit: int = 20,
    ) -> list[SourcingAgentSignal]:
        """Most-recent signals for a sourcing agent (timeline view)."""
        _require_custom_agent_id(custom_agent_id)
        stmt = (
            select(SourcingAgentSignal)
            .where(SourcingAgentSignal.custom_agent_id == custom_agent_id)
            .order_by(SourcingAgentSignal.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return list(result.scalars().all())
