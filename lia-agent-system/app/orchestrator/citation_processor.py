"""Onda 2.4 Init V (2026-04-21) — Citation processor.

Turns `tool_calls` records (already produced by orchestrator during response
generation) into citation entries that can be rendered by frontend as
tooltip/footnote/sidebar for reasoning transparency.

Citation shape:
    {
      "tool_name": str,
      "tool_params": dict,
      "timestamp": str (ISO),
      "result_summary": str (truncated),
      "confidence": float (0.0-1.0),
    }

Canonical-fix: producer = orchestrator tool_calls stream; this module is a
pure transformer (no independent data access). Frontend (G1) consumes the
citations list without backend changes when rendering.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Feature flag — default ON
_CITATIONS_ENABLED = os.environ.get(
    "LIA_CITATIONS_ENABLED", "true"
).lower() == "true"


def build_citations_from_tool_calls(
    tool_calls: list[dict[str, Any]] | None,
    response_text: str = "",
) -> list[dict[str, Any]]:
    """Transform tool_calls into citation entries.

    Args:
        tool_calls: List of tool call records from orchestrator. Each
            expected to have at minimum: tool_name (or name), tool_params
            (or parameters / arguments), result (or output).
        response_text: LIA response text (reserved for future text_span
            extraction — currently unused).

    Returns:
        List of citation dicts. Empty list if disabled/no tool_calls.

    Robust to varied tool_call shapes (different producers have slightly
    different fields); normalizes to canonical citation shape.
    """
    if not _CITATIONS_ENABLED or not tool_calls:
        return []

    now_iso = datetime.utcnow().isoformat()
    citations: list[dict[str, Any]] = []

    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue

        tool_name = tc.get("tool_name") or tc.get("name") or tc.get("tool") or "unknown"
        params = tc.get("tool_params") or tc.get("parameters") or tc.get("arguments") or {}
        if not isinstance(params, dict):
            params = {"_raw": str(params)[:200]}

        result = tc.get("result") or tc.get("output") or tc.get("response")
        result_summary = _summarize_result(result)

        timestamp = tc.get("timestamp") or tc.get("created_at") or now_iso
        if not isinstance(timestamp, str):
            try:
                timestamp = timestamp.isoformat()
            except Exception:
                timestamp = now_iso

        confidence = tc.get("confidence")
        if not isinstance(confidence, (int, float)):
            confidence = 1.0 if result else 0.5

        citations.append({
            "tool_name": tool_name,
            "tool_params": params,
            "timestamp": timestamp,
            "result_summary": result_summary,
            "confidence": float(confidence),
        })

    return citations


def _summarize_result(result: Any, max_chars: int = 160) -> str:
    """Truncate a tool result to a short string for citation display."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result[:max_chars]
    if isinstance(result, dict):
        # Prefer `message` or `summary` keys if present
        for key in ("message", "summary", "text"):
            if key in result and isinstance(result[key], str):
                return result[key][:max_chars]
        # Else show keys
        keys = list(result.keys())[:5]
        return f"dict with keys: {keys}"
    if isinstance(result, list):
        return f"list of {len(result)} items"
    return str(result)[:max_chars]
