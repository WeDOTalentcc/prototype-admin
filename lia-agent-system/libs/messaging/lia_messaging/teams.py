"""lia_messaging.teams - low-level Teams Incoming Webhook helper (canonical for domain abstractions).

When to use: domain-level abstractions (capabilities.yaml, domain.py, actions.py)
that need a thin send-to-Teams primitive. Used internally by TeamsService.
Auth: TEAMS_WEBHOOK_URL env var.
Tech: httpx wrapper, MessageCard format.

For full decision tree of which Teams send path to use, see:
lia-agent-system/CLAUDE.md "Teams send paths - when to use which" (W5.5).

Do NOT use this directly from API endpoints - use teams_simple/teams_bot/teams_service
instead, which provide higher-level semantics.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def send_teams_message(
    title: str,
    text: str,
    *,
    webhook_url: Optional[str] = None,
    color: Optional[str] = None,
    facts: Optional[list[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Send a message card to a Microsoft Teams channel via Incoming Webhook.

    Args:
        title: Card title.
        text: Card body text (supports Markdown).
        webhook_url: Teams webhook URL. Falls back to TEAMS_WEBHOOK_URL env var.
        color: Hex accent color (e.g. "0076D7"). Defaults to WeDO cyan (#60BED1).
        facts: Optional list of {"name": ..., "value": ...} key-value pairs.

    Returns:
        {"success": bool, "status_code": int | None, "error": str | None}
    """
    url = webhook_url or os.environ.get("TEAMS_WEBHOOK_URL")
    if not url:
        logger.warning("TEAMS_WEBHOOK_URL not configured — Teams message NOT sent (title=%r)", title)
        return {"success": False, "status_code": None, "error": "No Teams webhook URL configured"}

    card = _build_card(title, text, color=color or "60BED1", facts=facts)

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=card)
            resp.raise_for_status()

        return {"success": True, "status_code": resp.status_code, "error": None}

    except Exception as exc:
        logger.error("Teams message send failed: %s", exc, exc_info=True)
        return {"success": False, "status_code": None, "error": str(exc)}


def _build_card(
    title: str,
    text: str,
    color: str,
    facts: Optional[list[Dict[str, str]]],
) -> Dict[str, Any]:
    """Build a Teams MessageCard payload."""
    card: Dict[str, Any] = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": color,
        "summary": title,
        "sections": [
            {
                "activityTitle": f"**{title}**",
                "activityText": text,
            }
        ],
    }
    if facts:
        card["sections"][0]["facts"] = facts
    return card
