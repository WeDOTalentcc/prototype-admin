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
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.cv_screening.repositories.agent_checkpoint_repository import (
    AgentCheckpointRepository,
)

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
    LangGraph PostgresSaver handles checkpoints for the standard path.
    """
    sanitized = _sanitize_state(state)
    repo = AgentCheckpointRepository(db)
    await repo.upsert(
        session_id=session_id,
        agent_type=agent_type,
        state=sanitized,
        company_id=company_id,
    )
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
    repo = AgentCheckpointRepository(db)
    row = await repo.get(session_id=session_id, agent_type=agent_type)
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
    repo = AgentCheckpointRepository(db)
    await repo.delete(session_id=session_id, agent_type=agent_type)
    logger.info("Checkpoint deleted", extra={"session_id": session_id})
