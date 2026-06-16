"""AgentCheckpointRepository — DB access for legacy agent state checkpoints.

Extracted from app/domains/cv_screening/services/checkpoint_service.py per ADR-001.
LangGraph PostgresSaver is used for the standard path; this repo serves only
legacy graph paths (e.g., custom start_node in JobWizardGraph).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from lia_models.agent_checkpoint import AgentCheckpoint


class AgentCheckpointRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        *,
        session_id: str,
        agent_type: str,
        state: dict[str, Any],
        company_id: str | None,
    ) -> None:
        now = datetime.utcnow()
        stmt = (
            pg_insert(AgentCheckpoint)
            .values(
                session_id=session_id,
                agent_type=agent_type,
                company_id=company_id,
                state_json=state,
                created_at=now,
                updated_at=now,
            )
            .on_conflict_do_update(
                constraint="uq_agent_checkpoints_session_type",
                set_={
                    "state_json": state,
                    "company_id": company_id,
                    "updated_at": now,
                },
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get(
        self,
        *,
        session_id: str,
        agent_type: str,
    ) -> AgentCheckpoint | None:
        """Get checkpoint by (session_id, agent_type).

        session_id is globally unique (uq_agent_checkpoints_session_type
        constraint enforces (session_id, agent_type) uniqueness across the platform).
        session_id is allocated per-recruiter-session and cannot collide across tenants;
        additional company_id filter would be redundant. company_id is persisted on
        the row for audit/observability purposes.
        """
        # TENANT-EXEMPT: session_id global UNIQUE constraint guarantees tenant
        # isolation by construction (see docstring).
        result = await self.db.execute(
            select(AgentCheckpoint).where(
                AgentCheckpoint.session_id == session_id,
                AgentCheckpoint.agent_type == agent_type,
            )
        )
        return result.scalar_one_or_none()

    async def delete(
        self,
        *,
        session_id: str,
        agent_type: str,
    ) -> None:
        row = await self.get(session_id=session_id, agent_type=agent_type)
        if row:
            await self.db.delete(row)
            await self.db.commit()
