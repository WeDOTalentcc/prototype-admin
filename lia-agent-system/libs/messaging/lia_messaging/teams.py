"""
lia_messaging.teams — Microsoft Teams notification interface.

Sends Adaptive Card messages via an Incoming Webhook URL.

Environment variables:
    TEAMS_WEBHOOK_URL   → default webhook (can be overridden per-call)

Per-tenant URL resolution:
    When ``company_id`` is supplied the function resolves the saved webhook URL
    from the database via ``resolve_tenant_teams_webhook_url`` before falling
    back to the environment variable.  If a live ``db`` session is provided it
    is reused; otherwise a short-lived session is opened internally.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def _resolve_url_for_tenant(company_id: str, db: Any | None) -> str | None:
    """Return the Teams webhook URL saved for *company_id*, or ``None``.

    Uses the canonical ``resolve_tenant_teams_webhook_url`` helper.  Opens its
    own DB session when *db* is ``None`` (same pattern as
    ``_get_recruiter_for_job`` in ``StakeholderNotificationService``).
    """
    try:
        from app.domains.communication.services.teams_service import (
            resolve_tenant_teams_webhook_url,
        )

        if db is not None:
            url, _ = await resolve_tenant_teams_webhook_url(company_id, db)
            return url or None

        from lia_config.database import AsyncSessionLocal

        async with AsyncSessionLocal() as _session:
            url, _ = await resolve_tenant_teams_webhook_url(company_id, _session)
            return url or None
    except Exception as exc:
        logger.debug(
            "send_teams_message: per-tenant URL resolution failed for company=%s: %s",
            company_id,
            exc,
        )
        return None


async def send_teams_message(
    title: str,
    text: str,
    *,
    webhook_url: Optional[str] = None,
    company_id: Optional[str] = None,
    db: Optional[Any] = None,
    color: Optional[str] = None,
    facts: Optional[list[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Send a message card to a Microsoft Teams channel via Incoming Webhook.

    Args:
        title: Card title.
        text: Card body text (supports Markdown).
        webhook_url: Explicit Teams webhook URL — skips all resolution when set.
        company_id: Tenant company ID.  When supplied (and ``webhook_url`` is
            not), the per-tenant webhook URL saved in the database is resolved
            first; the ``TEAMS_WEBHOOK_URL`` env var is only used as a final
            fallback.
        db: Optional async DB session.  When ``company_id`` is provided and
            ``db`` is ``None``, a short-lived session is opened internally for
            the URL lookup.
        color: Hex accent color (e.g. "0076D7"). Defaults to WeDO cyan (#60BED1).
        facts: Optional list of {"name": ..., "value": ...} key-value pairs.

    Returns:
        {"success": bool, "status_code": int | None, "error": str | None}
    """
    url = webhook_url

    if not url and company_id:
        url = await _resolve_url_for_tenant(company_id, db)

    url = url or os.environ.get("TEAMS_WEBHOOK_URL")

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
