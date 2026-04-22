"""Onda 3.2 G3 (2026-04-21) — HITL checkpoint builder.

HITL (Human-in-the-Loop) signal surfacer. Tool executor
(app/tools/executor.py) already blocks `requires_hitl` tools and returns a
dict with requires_hitl: True — but that signal never reached ChatResponse.

G3 adds build_hitl_checkpoint() to produce a structured checkpoint dict that
SystemPromptBuilder/main_orchestrator can attach to ChatResponse.hitl_checkpoint.
Frontend (G1) consumes this to render approval UI.

Existing /api/v1/approvals router handles the approval lifecycle — G3 is the
surfacing layer only.

Canonical-fix: producer = tool executor\'s governance_tags check; HITL is
the consumer/formatter.
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

_HITL_CHECKPOINT_ENABLED = os.environ.get(
    "LIA_HITL_CHECKPOINT_ENABLED", "true"
).lower() == "true"


def build_hitl_checkpoint(
    *,
    tool_name: str,
    tool_params: dict[str, Any] | None = None,
    governance_tags: list[str] | None = None,
    reason: str | None = None,
) -> dict[str, Any] | None:
    """Build canonical HITL checkpoint for ChatResponse surfacing.

    Args:
        tool_name: Tool that requires approval (e.g. "close_job", "send_feedback").
        tool_params: Parameters the tool would be called with. Summarized
            (truncated for safe display).
        governance_tags: Why HITL triggered (e.g. ["destructive", "external_comms"]).
        reason: Human-readable reason (e.g. "Encerramento de vaga é ação destrutiva").

    Returns:
        Checkpoint dict or None if disabled/no data.

    Shape:
        {
          "checkpoint_id": uuid-str,
          "tool_name": str,
          "tool_params_summary": dict (truncated),
          "governance_tags": list[str],
          "reason": str,
          "requested_at": iso-str,
          "approval_endpoint": "/api/v1/approvals"  # hint for frontend
        }
    """
    if not _HITL_CHECKPOINT_ENABLED or not tool_name:
        return None

    # Summarize params to avoid leaking long blobs in ChatResponse
    params_summary = {}
    for k, v in (tool_params or {}).items():
        if isinstance(v, str):
            params_summary[k] = v[:100]
        elif isinstance(v, (int, float, bool)) or v is None:
            params_summary[k] = v
        elif isinstance(v, (list, tuple)):
            params_summary[k] = f"list({len(v)} items)"
        elif isinstance(v, dict):
            params_summary[k] = f"dict(keys={list(v.keys())[:5]})"
        else:
            params_summary[k] = str(type(v).__name__)

    checkpoint = {
        "checkpoint_id": str(uuid.uuid4()),
        "tool_name": tool_name,
        "tool_params_summary": params_summary,
        "governance_tags": list(governance_tags or []),
        "reason": reason or _default_reason(tool_name, governance_tags),
        "requested_at": datetime.utcnow().isoformat(),
        "approval_endpoint": "/api/v1/approvals",
    }

    logger.info(
        "[LIA-HITL] checkpoint built tool=%s tags=%s id=%s",
        tool_name, governance_tags, checkpoint["checkpoint_id"],
    )
    return checkpoint


def _default_reason(tool_name: str, governance_tags: list[str] | None) -> str:
    """Provide a fallback human-readable reason based on governance tags."""
    tags = set(governance_tags or [])
    if "destructive" in tags or "write_destructive" in tags:
        return f"A ação '{tool_name}' é destrutiva (não-reversível). Confirme antes."
    if "external_comms" in tags:
        return f"A ação '{tool_name}' envia comunicação externa. Revise antes."
    if "pii" in tags:
        return f"A ação '{tool_name}' lida com dados pessoais (LGPD). Aprove antes."
    return f"A ação '{tool_name}' requer aprovação humana por política."
