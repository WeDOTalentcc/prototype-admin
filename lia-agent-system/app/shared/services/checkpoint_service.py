"""
Checkpoint Service — save and restore agent state by session_id.

Provides fault tolerance for LangGraph-style agents: if the process
restarts between user turns, the agent can restore its accumulated
state from the database instead of starting from scratch.

Note: LangGraph agents use PostgresSaver natively for checkpointing.
The functions in this module are retained for legacy graph invocations
(e.g., custom start_node paths in JobWizardGraph). For the standard
LangGraph path, PostgresSaver manages checkpoints automatically.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_checkpoint import AgentCheckpoint

logger = logging.getLogger(__name__)

_FIELDS_NOT_TO_PERSIST = {
    "user_message",
    "error",
    "tool_calls",
    "tool_results",
    "streaming_chunks",
}


def _sanitize_state(state: dict) -> dict:
    """Remove ephemeral/non-serialisable fields before persisting."""
    return {
        k: v for k, v in state.items()
        if k not in _FIELDS_NOT_TO_PERSIST and _is_json_serializable(v)
    }


def _is_json_serializable(value: Any) -> bool:
    """Quick check — rejects objects that cannot be stored as JSON."""
    return not callable(value)


async def save_checkpoint(
    db: AsyncSession,
    session_id: str,
    agent_type: str,
    state: dict,
    company_id: str | None = None,
) -> None:
    """Upsert the agent state for the given session.

    Used only by legacy graph paths (e.g., custom start_node in JobWizardGraph).
    LangGraph's PostgresSaver handles checkpoints for the standard path.
    """
    sanitized = _sanitize_state(state)

    stmt = (
        pg_insert(AgentCheckpoint)
        .values(
            session_id=session_id,
            agent_type=agent_type,
            company_id=company_id,
            state_json=sanitized,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        .on_conflict_do_update(
            constraint="uq_agent_checkpoints_session_type",
            set_={
                "state_json": sanitized,
                "company_id": company_id,
                "updated_at": datetime.utcnow(),
            },
        )
    )

    await db.execute(stmt)
    await db.commit()
    logger.debug("Checkpoint saved", extra={"session_id": session_id, "agent_type": agent_type})


async def restore_checkpoint(
    db: AsyncSession,
    session_id: str,
    agent_type: str,
) -> dict | None:
    """Return the persisted state dict, or None if no checkpoint exists.

    Used only by legacy graph paths. For the standard LangGraph path,
    PostgresSaver restores state automatically via thread_id at ainvoke() time.
    """
    result = await db.execute(
        select(AgentCheckpoint).where(
            AgentCheckpoint.session_id == session_id,
            AgentCheckpoint.agent_type == agent_type,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    logger.debug("Checkpoint restored", extra={"session_id": session_id, "agent_type": agent_type})
    return dict(row.state_json or {})


async def delete_checkpoint(
    db: AsyncSession,
    session_id: str,
    agent_type: str,
) -> None:
    """Remove checkpoint after the wizard session is completed or abandoned.

    Used only by legacy graph paths. For the standard LangGraph path,
    PostgresSaver manages cleanup via thread_id.
    """
    result = await db.execute(
        select(AgentCheckpoint).where(
            AgentCheckpoint.session_id == session_id,
            AgentCheckpoint.agent_type == agent_type,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
        logger.info("Checkpoint deleted", extra={"session_id": session_id})
