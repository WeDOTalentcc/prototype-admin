"""
lia_messaging.email — Provider-agnostic email sending interface.

Detects active provider via environment variables (priority: Mailgun > Resend).
All functions are async-safe and return a consistent result dict.

Environment variables (read via os.environ — lia_config not required):
    MAILGUN_API_KEY +
    MAILGUN_DOMAIN       → use Mailgun provider (primary)
    RESEND_API_KEY       → use Resend provider (fallback)
    DEFAULT_FROM_EMAIL   → fallback sender address (default: noreply@wedotalent.com)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_FROM = "noreply@wedotalent.com"


def _detect_provider() -> str:
    """Return the first configured provider: mailgun | resend | none."""
    if os.environ.get("MAILGUN_API_KEY") and os.environ.get("MAILGUN_DOMAIN"):
        return "mailgun"
    if os.environ.get("RESEND_API_KEY"):
        return "resend"
    return "none"


async def send_email(
    to: str | List[str],
    subject: str,
    body: str,
    *,
    html_body: Optional[str] = None,
    from_email: Optional[str] = None,
    reply_to: Optional[str] = None,
    provider: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send an email via the configured provider.

    Args:
        to: Recipient address or list of addresses.
        subject: Email subject line.
        body: Plain-text body.
        html_body: Optional HTML body (fallback to body if omitted).
        from_email: Sender address (defaults to DEFAULT_FROM_EMAIL env var).
        reply_to: Reply-to address.
        provider: Override auto-detected provider ('mailgun', 'resend').

    Returns:
        {"success": bool, "provider": str, "message_id": str | None, "error": str | None}
    """
    recipients = [to] if isinstance(to, str) else to
    sender = from_email or os.environ.get("DEFAULT_FROM_EMAIL", _DEFAULT_FROM)
    active_provider = provider or _detect_provider()

    try:
        if active_provider == "mailgun":
            return await _send_via_mailgun(recipients, subject, body, html_body, sender, reply_to)
        if active_provider == "resend":
            return await _send_via_resend(recipients, subject, body, html_body, sender, reply_to)

        logger.warning("No email provider configured — email NOT sent (subject=%r)", subject)
        return {"success": False, "provider": "none", "message_id": None,
                "error": "No email provider configured"}

    except Exception as exc:
        logger.error("Email send failed via %s: %s", active_provider, exc, exc_info=True)
        return {"success": False, "provider": active_provider, "message_id": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------

async def _send_via_mailgun(
    recipients: List[str],
    subject: str,
    body: str,
    html_body: Optional[str],
    sender: str,
    reply_to: Optional[str],
) -> Dict[str, Any]:
    import httpx

    api_key = os.environ["MAILGUN_API_KEY"]
    domain = os.environ["MAILGUN_DOMAIN"]
    api_base = os.environ.get("MAILGUN_API_BASE", "https://api.mailgun.net/v3")

    data: Dict[str, Any] = {
        "from": sender,
        "to": ",".join(recipients),
        "subject": subject,
        "text": body,
    }
    if html_body:
        data["html"] = html_body
    if reply_to:
        data["h:Reply-To"] = reply_to

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{api_base}/{domain}/messages",
            auth=("api", api_key),
            data=data,
        )
        resp.raise_for_status()

    payload = resp.json()
    return {"success": True, "provider": "mailgun", "message_id": payload.get("id"), "error": None}


async def _send_via_resend(
    recipients: List[str],
    subject: str,
    body: str,
    html_body: Optional[str],
    sender: str,
    reply_to: Optional[str],
) -> Dict[str, Any]:
    import resend  # type: ignore[import-untyped]

    resend.api_key = os.environ["RESEND_API_KEY"]
    params: Dict[str, Any] = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "text": body,
    }
    if html_body:
        params["html"] = html_body
    if reply_to:
        params["reply_to"] = reply_to

    response = resend.Emails.send(params)
    message_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
    return {"success": True, "provider": "resend", "message_id": message_id, "error": None}
