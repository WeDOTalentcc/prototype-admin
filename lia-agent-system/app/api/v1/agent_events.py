"""Agent lifecycle events — SSE endpoint (FIX-P0-03).

GET /api/v1/agent-events/{session_id}
  → text/event-stream of agent lifecycle events for the given chat session.

Clients reconnect automatically using the `Last-Event-ID` header; the emitter
replays buffered events to cover brief disconnects (no dropped events).

Authentication: Bearer token via Authorization header (same as REST endpoints).
The session_id must belong to the authenticated company (multi-tenancy gate).
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.shared.events.agent_lifecycle_emitter import AgentEventBus, AgentEvent
from app.shared.security import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-events", tags=["agent-events"])

_KEEPALIVE_INTERVAL_S: float = 15.0
_EVENT_BUS_SENTINEL = ": keepalive\n\n"


def _format_sse(event: AgentEvent) -> str:
    """Format an AgentEvent as a valid SSE frame."""
    data = json.dumps(event.to_dict(), ensure_ascii=False)
    return f"id: {event.event_id}\ndata: {data}\n\n"


async def _sse_stream(
    session_id: str,
    last_event_id: str | None,
    request: Request,
) -> AsyncGenerator[str, None]:
    """Yield SSE frames for the session, with keepalive and disconnect detection."""
    bus = AgentEventBus.get_instance()
    gen = bus.subscribe(session_id, last_event_id=last_event_id)

    logger.info(
        "[agent-events] SSE client connected session=%s last_event_id=%s",
        session_id,
        last_event_id,
    )

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("[agent-events] client disconnected session=%s", session_id)
                break

            # Wait for next event with keepalive timeout
            try:
                event = await asyncio.wait_for(
                    gen.__anext__(), timeout=_KEEPALIVE_INTERVAL_S
                )
                yield _format_sse(event)
            except (asyncio.TimeoutError, TimeoutError):
                yield _EVENT_BUS_SENTINEL  # keepalive comment
            except StopAsyncIteration:
                logger.info("[agent-events] generator exhausted session=%s", session_id)
                break

    except asyncio.CancelledError:
        logger.info("[agent-events] stream cancelled session=%s", session_id)
    finally:
        # Ensure generator is properly closed
        try:
            await gen.aclose()
        except Exception:  # noqa: BLE001
            pass


@router.get("/{session_id}", summary="Subscribe to agent lifecycle events (SSE)")
async def agent_events_stream(
    session_id: str,
    request: Request,
    company_id: str = Depends(require_company_id),
) -> StreamingResponse:
    """Stream agent lifecycle events for a chat session.

    Event types:
    - agent_thinking: agent started processing the message
    - agent_action: agent is about to execute an action
    - agent_action_result: action completed (status: success|error)
    - agent_context_update: page/UI state changed

    Reconnection: send Last-Event-ID header to resume without missing events.
    The server buffers the last 50 events per session.
    """
    last_event_id = request.headers.get("Last-Event-ID") or request.headers.get(
        "last-event-id"
    )

    return StreamingResponse(
        _sse_stream(session_id, last_event_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
