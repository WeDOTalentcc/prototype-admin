"""
app/core/observability.py — FIX 12 / G9.

Central helper for structured logging of tool calls. Provides a single
entry point used by agentic_loop.py (and future consumers). Emits:

  1. structured `logger.info("tool_call", extra={...})` — always
  2. optional LangSmith span — when LANGCHAIN_TRACING_V2=true + langsmith installed

This centralization was added to close Gap 9 (tool-metrics ingestion gap).
Previously, `logger.info("tool_call", ...)` was inlined in agentic_loop.py
without any ingestion layer — logs existed but were not actionable.

## Usage

    from app.core.observability import emit_tool_call

    emit_tool_call(
        tool_name="create_job_vacancy",
        company_id="abc-123",
        success=True,
        first_shot=True,
        call_index=1,
        governance_tags=["multi_tenant"],
        has_related_tools=True,
        latency_ms=420.5,
    )

## Environment variables

  LANGCHAIN_TRACING_V2=true     enables LangSmith span emission
  LANGCHAIN_API_KEY=...         required when tracing enabled
  LANGCHAIN_PROJECT=<name>      optional project name
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("lia.tool_metrics")

_LANGSMITH_CLIENT: Any | None = None  # lazy-init singleton
_LANGSMITH_INIT_ATTEMPTED = False


def _maybe_get_langsmith_client() -> Any | None:
    """Return a LangSmith client if tracing is enabled and lib is available.

    The lookup is cached: first call attempts init, subsequent calls return
    the cached client (or None). Safe to call hot-path.
    """
    global _LANGSMITH_CLIENT, _LANGSMITH_INIT_ATTEMPTED
    if _LANGSMITH_INIT_ATTEMPTED:
        return _LANGSMITH_CLIENT
    _LANGSMITH_INIT_ATTEMPTED = True

    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() in ("true", "1", "yes")
    if not tracing_enabled:
        return None
    if not os.getenv("LANGCHAIN_API_KEY"):
        return None

    try:
        from langsmith import Client  # type: ignore[import-not-found]
    except ImportError:
        return None

    try:
        _LANGSMITH_CLIENT = Client()
        return _LANGSMITH_CLIENT
    except Exception:  # pragma: no cover - defensive
        return None


def emit_tool_call(
    *,
    tool_name: str,
    company_id: str | None,
    success: bool,
    first_shot: bool,
    call_index: int,
    governance_tags: list[str] | None = None,
    has_related_tools: bool = False,
    latency_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Emit a structured tool-call event.

    Always logs; optionally forwards to LangSmith when enabled. Never raises
    — observability failures must never break the request flow.
    """
    event: dict[str, Any] = {
        "tool_name": tool_name,
        "company_id": company_id,
        "success": success,
        "first_shot": first_shot,
        "call_index": call_index,
        "governance_tags": list(governance_tags or []),
        "has_related_tools": has_related_tools,
        "latency_ms": latency_ms,
    }
    if error:
        event["error"] = error

    try:
        logger.info("tool_call", extra=event)
    except Exception:
        pass  # defensive — logging must never fail

    # Optional LangSmith forwarding
    client = _maybe_get_langsmith_client()
    if client is not None:
        try:
            # Minimal: create a run record tagged with our event. Uses
            # LangSmith's lightweight tracer — does not block.
            client.create_run(  # type: ignore[attr-defined]
                name=f"tool_call:{tool_name}",
                run_type="tool",
                inputs={"call_index": call_index, "first_shot": first_shot},
                outputs={"success": success, "error": error},
                extra={"metadata": event},
            )
        except Exception:
            pass  # defensive — never break the request


def emit_hitl_pending(
    *,
    tool_name: str,
    company_id: str | None,
    governance_tags: list[str] | None = None,
    conversation_id: str | None = None,
) -> None:
    """Emit a HITL-pending event for audit trail.

    Called when a tool with governance_tags=[requires_hitl] returns
    pending_hitl_confirmation. Lets us measure HITL confirmation funnel.
    """
    event = {
        "tool_name": tool_name,
        "company_id": company_id,
        "governance_tags": list(governance_tags or []),
        "conversation_id": conversation_id,
    }
    try:
        logger.info("hitl_pending", extra=event)
    except Exception:
        pass


def reset_langsmith_cache() -> None:
    """Test helper: reset the cached LangSmith client (for unit tests)."""
    global _LANGSMITH_CLIENT, _LANGSMITH_INIT_ATTEMPTED
    _LANGSMITH_CLIENT = None
    _LANGSMITH_INIT_ATTEMPTED = False
