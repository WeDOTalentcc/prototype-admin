"""Wizard session REST endpoints (Task #1128).

Two canonical operations on the LangGraph checkpointer for the job-creation
wizard, addressed by the same ``(company_id, session_id)`` pair the WS/SSE
path uses:

  GET    /api/v1/lia/job-wizard/session/{session_id}
  DELETE /api/v1/lia/job-wizard/session/{session_id}

Why this exists
---------------
Before Task #1128 the frontend treated ``localStorage["lia-wizard-state-*"]``
as the source of truth for "is the wizard active?". A "Nova conversa" click
only wiped the chat message list; the wizard kept resuming on the next
``ws_stage_payload`` because the local cache was never cleared and the
backend checkpointer was never touched. The bug also surfaced when two
recruiters shared a browser (LGPD bleed).

The canonical fix is server-side: there is one wizard state per
``(company_id, session_id)`` and it lives in the LangGraph checkpointer
exclusively. The frontend asks the backend on mount/conversation-switch
(GET) and tells the backend to reset on "Nova conversa" / "Cancelar wizard"
(DELETE). No more local cache. ``app.shared.sessions.thread_id`` already
derives the thread_id and answers "is this session active?" — these
endpoints reuse it verbatim.

Authentication / multi-tenancy
------------------------------
Both endpoints use ``get_current_user_or_demo`` (same pattern as the
neighbouring ``conversational.py::clear_job_draft``). The ``company_id``
that scopes the checkpointer key is read from ``current_user.company_id``
server-side and never trusted from the client — a recruiter cannot derive
or reset another tenant's wizard thread by guessing a session_id.

Reset semantics
---------------
LangGraph's stable checkpointer API does not expose "delete a thread", so
the reset writes ``current_stage="completed", conversation_messages=[]``
into the checkpoint via ``update_state``. After that, the canonical
``is_wizard_session_active`` returns False (stage == "completed" short-circuit)
and the next WS turn starts a fresh wizard from the ``intake`` node.
Idempotent: DELETE on a missing thread returns ``was_active=False`` and
``success=True`` so the frontend can call it unconditionally on every
"Nova conversa".
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user_or_demo
from app.auth.models import User
from app.shared.sessions import derive_thread_id, is_wizard_session_active
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter()


class SessionStateResponse(BaseModel):
    """Snapshot of the wizard checkpoint, shaped for the frontend chat.

    ``active`` is the canonical "should the wizard UI mount?" flag — it
    mirrors ``is_wizard_session_active`` exactly so the frontend doesn't
    have to reimplement the (stage != "completed") rule.
    """

    session_id: str
    thread_id: str
    active: bool
    current_stage: str | None = None
    completeness: float = 0.0
    requires_approval: bool = False
    stage_data: dict[str, Any] = Field(default_factory=dict)
    degraded_stages: dict[str, Any] = Field(default_factory=dict)
    conversation_message_count: int = 0


class ResetSessionResponse(BaseModel):
    success: bool
    session_id: str
    thread_id: str
    was_active: bool


_DEGRADED_FLAG_KEYS = (
    ("jd_enrichment", "jd_enrichment_used_fallback", "jd_enrichment_fallback_reason"),
    ("bigfive", "bigfive_used_fallback", "bigfive_fallback_reason"),
    ("salary", "salary_used_fallback", "salary_fallback_reason"),
    ("wsi_questions", "wsi_questions_used_fallback", "wsi_questions_fallback_reason"),
)


def _extract_degraded(values: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for stage, flag_key, reason_key in _DEGRADED_FLAG_KEYS:
        if values.get(flag_key) is True:
            reason = values.get(reason_key)
            out[stage] = reason if isinstance(reason, str) and reason else True
    return out


async def _read_state_snapshot(thread_id: str) -> dict[str, Any] | None:
    """Return raw ``snapshot.values`` dict or ``None`` when nothing checkpointed."""
    try:
        from app.domains.job_creation.graph import get_job_creation_graph

        wiz_g = get_job_creation_graph()
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = await asyncio.to_thread(wiz_g._graph.get_state, config)
    except Exception as exc:  # pragma: no cover — fail-open mirrors is_wizard_session_active
        logger.warning(
            "[wizard_session] checkpointer read failed thread=%s reason=%s",
            thread_id,
            type(exc).__name__,
        )
        return None
    if snapshot is None or not snapshot.values:
        return None
    return dict(snapshot.values)


@router.get(
    "/job-wizard/session/{session_id}",
    response_model=SessionStateResponse,
)
async def get_wizard_session_state(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)) -> SessionStateResponse:
    """Return the canonical wizard checkpoint snapshot for this session.

    Frontend mounts this on conversation load/switch instead of reading
    ``localStorage["lia-wizard-state-*"]`` (which was abolished in Task
    #1128). Tenant-scoped via ``current_user.company_id`` — a recruiter
    cannot probe another tenant's thread by guessing a ``session_id``.
    """
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=422, detail="session_id must be non-empty")
    company_id = current_user.company_id
    thread_id = derive_thread_id(company_id, session_id)

    values = await _read_state_snapshot(thread_id)
    active = await is_wizard_session_active(company_id, session_id)

    if values is None:
        return SessionStateResponse(
            session_id=session_id,
            thread_id=thread_id,
            active=False,
        )

    stage_raw = values.get("current_stage") or None
    stage = str(stage_raw) if stage_raw else None
    try:
        from app.domains.job_creation.state import calculate_completeness

        completeness = float(calculate_completeness(stage)) if stage else 0.0
    except Exception:
        # REGRA-4-EXEMPT: progress calc fallback (not LLM I/O). Stage import
        # failure means we lack the helper to compute completeness — 0.0 is
        # a sentinel that UI renders as "0% progress" (correct surface).
        completeness = 0.0
    requires_approval = bool(values.get("requires_approval") or values.get("awaiting_approval"))
    conversation = values.get("conversation_messages") or []

    return SessionStateResponse(
        session_id=session_id,
        thread_id=thread_id,
        active=active,
        current_stage=stage,
        completeness=completeness,
        requires_approval=requires_approval,
        stage_data=values,
        degraded_stages=_extract_degraded(values),
        conversation_message_count=len(conversation) if isinstance(conversation, list) else 0,
    )


@router.delete(
    "/job-wizard/session/{session_id}",
    response_model=ResetSessionResponse,
)
async def reset_wizard_session(
    session_id: str,
    current_user: User = Depends(get_current_user_or_demo),
company_id: str = Depends(require_company_id)) -> ResetSessionResponse:
    """Reset the wizard checkpoint for this ``(company_id, session_id)``.

    Marks the checkpoint as ``current_stage="completed"`` and clears the
    conversation log so the canonical ``is_wizard_session_active`` returns
    False and the next WS turn starts a fresh ``intake``. Idempotent —
    calling on a missing thread returns ``was_active=False`` without
    raising, which is what "Nova conversa" needs (the recruiter shouldn't
    see an error just because no wizard was open).
    """
    if not session_id or not session_id.strip():
        raise HTTPException(status_code=422, detail="session_id must be non-empty")
    company_id = current_user.company_id
    thread_id = derive_thread_id(company_id, session_id)

    was_active = await is_wizard_session_active(company_id, session_id)

    if not was_active:
        logger.info(
            "[wizard_session.reset] no-op (already inactive) thread=%s session=%s",
            thread_id,
            session_id,
        )
        return ResetSessionResponse(
            success=True,
            session_id=session_id,
            thread_id=thread_id,
            was_active=False,
        )

    try:
        from app.domains.job_creation.graph import get_job_creation_graph

        wiz_g = get_job_creation_graph()
        config = {"configurable": {"thread_id": thread_id}}
        # Two-write reset: first nuke conversation + stage so subsequent
        # ``is_wizard_session_active`` short-circuits on stage=="completed".
        # Run via ``asyncio.to_thread`` because PostgresSaver.put is sync.
        await asyncio.to_thread(
            wiz_g._graph.update_state,
            config,
            {
                "current_stage": "completed",
                "conversation_messages": [],
                "requires_approval": False,
                "awaiting_approval": False,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "[wizard_session.reset] checkpointer write failed thread=%s reason=%s",
            thread_id,
            type(exc).__name__,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset wizard session: {type(exc).__name__}",
        ) from exc

    logger.info(
        "[wizard_session.reset] cleared thread=%s session=%s company=%s",
        thread_id,
        session_id,
        company_id,
    )
    return ResetSessionResponse(
        success=True,
        session_id=session_id,
        thread_id=thread_id,
        was_active=True,
    )
