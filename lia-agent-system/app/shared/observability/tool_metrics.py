"""
app/shared/observability/tool_metrics.py — FIX 13 (canonical migration).

Central helper for structured logging of tool calls. Moved here from
`app/core/observability.py` (FIX 12) to comply with Section 1 of
`docs/specs/CANONICAL_SOURCES_SPEC.md` — all observability code lives
under `app.shared.observability.*` with exactly one canonical path.

Provides:
    emit_tool_call(**kwargs)      → structured log + optional LangSmith span
    emit_hitl_pending(**kwargs)   → audit event for HITL confirmation requests

Reuses `app.shared.observability.langsmith.is_langsmith_enabled()` to gate
LangSmith forwarding, avoiding duplicate env-var checks.

## Environment variables (forwarding)

  LANGCHAIN_TRACING_V2=true         enables LangSmith span emission
  LANGSMITH_API_KEY=... or          required when tracing enabled
    LANGCHAIN_API_KEY=...
  LANGCHAIN_PROJECT=<name>          optional project name

See also ADR-019 and docs/LIA_AI_HANDOFF.md §11.
"""
from __future__ import annotations

import logging
from typing import Any

from app.shared.observability.langsmith import is_langsmith_enabled

logger = logging.getLogger("lia.tool_metrics")

_LANGSMITH_CLIENT: Any | None = None  # lazy-init singleton
_LANGSMITH_INIT_ATTEMPTED = False


def _maybe_get_langsmith_client() -> Any | None:
    """Return a LangSmith client if tracing is enabled and lib is available.

    Delegates env-var gating to `app.shared.observability.langsmith` to keep
    a single source of truth for "is tracing on?". Caches the client after
    first successful init.
    """
    global _LANGSMITH_CLIENT, _LANGSMITH_INIT_ATTEMPTED
    if _LANGSMITH_INIT_ATTEMPTED:
        return _LANGSMITH_CLIENT
    _LANGSMITH_INIT_ATTEMPTED = True

    if not is_langsmith_enabled():
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

    Always logs; optionally forwards to LangSmith when enabled. Never raises —
    observability failures must never break the request flow.
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

    Called when a tool with `governance_tags=[requires_hitl]` returns
    `pending_hitl_confirmation`. Enables HITL-funnel analytics.
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
    """Test helper: reset the cached LangSmith client."""
    global _LANGSMITH_CLIENT, _LANGSMITH_INIT_ATTEMPTED
    _LANGSMITH_CLIENT = None
    _LANGSMITH_INIT_ATTEMPTED = False
