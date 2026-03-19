"""
lia_messaging.whatsapp — Provider-agnostic WhatsApp message sending interface.

Supports two providers:
  - meta   → Meta Graph API (Cloud API)
  - twilio → Twilio Programmable Messaging

Environment variables:
    WHATSAPP_PROVIDER         → 'meta' | 'twilio' (default: 'meta')
    # Meta
    WHATSAPP_PHONE_NUMBER_ID  → Meta phone number ID
    WHATSAPP_API_TOKEN        → Meta access token (permanent or temporary)
    # Twilio
    TWILIO_ACCOUNT_SID        → Twilio account SID
    TWILIO_AUTH_TOKEN         → Twilio auth token
    TWILIO_WHATSAPP_NUMBER    → Twilio WhatsApp sender number (e.g. whatsapp:+14155238886)
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_META_API_BASE = "https://graph.facebook.com/v19.0"


def _detect_provider() -> str:
    return os.environ.get("WHATSAPP_PROVIDER", "meta").lower()


async def send_whatsapp_message(
    to: str,
    message: str,
    *,
    provider: Optional[str] = None,
    template_name: Optional[str] = None,
    template_params: Optional[list[str]] = None,
) -> Dict[str, Any]:
    """
    Send a WhatsApp message.

    Args:
        to: Recipient phone number in E.164 format (+5511999999999).
        message: Plain-text message body (ignored when template_name is set).
        provider: Override provider ('meta' or 'twilio').
        template_name: WhatsApp template name (Meta only).
        template_params: Parameter values for the template (Meta only).

    Returns:
        {"success": bool, "provider": str, "message_id": str | None, "error": str | None}
    """
    active_provider = provider or _detect_provider()

    try:
        if active_provider == "meta":
            return await _send_via_meta(to, message, template_name, template_params)
        if active_provider == "twilio":
            return await _send_via_twilio(to, message)

        return {
            "success": False, "provider": active_provider,
            "message_id": None, "error": f"Unknown provider: {active_provider}",
        }

    except Exception as exc:
        logger.error("WhatsApp send failed via %s: %s", active_provider, exc, exc_info=True)
        return {"success": False, "provider": active_provider, "message_id": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# Meta Cloud API
# ---------------------------------------------------------------------------

async def _send_via_meta(
    to: str,
    message: str,
    template_name: Optional[str],
    template_params: Optional[list[str]],
) -> Dict[str, Any]:
    import httpx

    phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    token = os.environ.get("WHATSAPP_API_TOKEN")

    if not phone_number_id or not token:
        return {
            "success": False, "provider": "meta", "message_id": None,
            "error": "WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_API_TOKEN not configured",
        }

    if template_name:
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "pt_BR"},
            },
        }
        if template_params:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": p} for p in template_params],
                }
            ]
    else:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": message},
        }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_META_API_BASE}/{phone_number_id}/messages",
            json=payload,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        )
        resp.raise_for_status()

    data = resp.json()
    message_id = data.get("messages", [{}])[0].get("id")
    return {"success": True, "provider": "meta", "message_id": message_id, "error": None}


# ---------------------------------------------------------------------------
# Twilio
# ---------------------------------------------------------------------------

async def _send_via_twilio(to: str, message: str) -> Dict[str, Any]:
    import httpx

    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_WHATSAPP_NUMBER")

    if not account_sid or not auth_token or not from_number:
        return {
            "success": False, "provider": "twilio", "message_id": None,
            "error": "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN or TWILIO_WHATSAPP_NUMBER not configured",
        }

    whatsapp_to = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
            data={"From": from_number, "To": whatsapp_to, "Body": message},
            auth=(account_sid, auth_token),
        )
        resp.raise_for_status()

    data = resp.json()
    return {"success": True, "provider": "twilio", "message_id": data.get("sid"), "error": None}
