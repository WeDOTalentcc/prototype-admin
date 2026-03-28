"""
Checkpoint Service — save and restore agent state by session_id.

Provides fault tolerance for LangGraph-style agents: if the process
restarts between user turns, the agent can restore its accumulated
state from the database instead of starting from scratch.

Usage in an agent graph:

    # Restore at the start of invoke()
    prior = await restore_checkpoint(db, session_id, "job_wizard")
    if prior:
        state = {**prior, **incoming_message_fields}

    # Save at the end of invoke()
    await save_checkpoint(db, session_id, "job_wizard", state)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.agent_checkpoint import AgentCheckpoint

logger = logging.getLogger(__name__)

# Quando USE_LANGGRAPH_NATIVE=True, o PostgresSaver do LangGraph gerencia
# os checkpoints nativamente. As funções abaixo tornam-se no-ops para evitar
# duplicidade de persistência — o dual-path de invoke() já garante que
# _invoke_legacy() não é chamado quando o flag está ativo.
def _langgraph_native_active() -> bool:
    try:
        from app.core.config import settings
        return bool(settings.USE_LANGGRAPH_NATIVE)
    except Exception:
        return False


_FIELDS_NOT_TO_PERSIST = {
    # Ephemeral fields that should not survive across turns
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
    company_id: Optional[str] = None,
) -> None:
    """Upsert the agent state for the given session.

    No-op quando USE_LANGGRAPH_NATIVE=True — PostgresSaver gerencia checkpoints.
    """
    if _langgraph_native_active():
        logger.debug(
            "save_checkpoint skipped (USE_LANGGRAPH_NATIVE=True)",
            extra={"session_id": session_id, "agent_type": agent_type},
        )
        return

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
) -> Optional[dict]:
    """Return the persisted state dict, or None if no checkpoint exists.

    Retorna None quando USE_LANGGRAPH_NATIVE=True — PostgresSaver restaura
    automaticamente via thread_id no momento do ainvoke().
    """
    if _langgraph_native_active():
        logger.debug(
            "restore_checkpoint skipped (USE_LANGGRAPH_NATIVE=True)",
            extra={"session_id": session_id, "agent_type": agent_type},
        )
        return None

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

    No-op quando USE_LANGGRAPH_NATIVE=True — PostgresSaver limpa via thread_id.
    """
    if _langgraph_native_active():
        logger.debug(
            "delete_checkpoint skipped (USE_LANGGRAPH_NATIVE=True)",
            extra={"session_id": session_id, "agent_type": agent_type},
        )
        return

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
