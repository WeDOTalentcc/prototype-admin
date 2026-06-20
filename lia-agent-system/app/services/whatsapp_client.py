"""
WhatsApp client for Twilio Business API.

Handles: template messages, free-form messages, WhatsApp Flows, buttons, CTAs.

Apply to: lia-agent-system/app/services/whatsapp_client.py
"""

import os
import logging
from typing import Optional

from app.shared.http_client import get_http_client

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("LIA_WHATSAPP_NUMBER", "")  # +5511...

class WhatsAppClient:
    """
    Twilio WhatsApp Business API client.

    All methods are async and non-blocking.
    Failures are logged but don't raise (non-blocking pattern from VoiceInterviewStateMachine).
    """

    def __init__(self):
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"

    async def send_template(
        self,
        phone: str,
        template_name: str,
        variables: list[str],
        language: str = "pt_BR",
    ) -> dict:
        """Send a Meta-approved template message."""
        try:
            to_number = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            # Build content variables for template
            content_vars = {str(i + 1): v for i, v in enumerate(variables)}

            async with get_http_client("twilio") as client:
                resp = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "ContentSid": template_name,  # Template SID from Twilio
                        "ContentVariables": str(content_vars),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"[WhatsApp] Template sent: {data.get('sid')}")
                return {"message_sid": data.get("sid"), "conversation_sid": data.get("sid")}

        except Exception as e:
            logger.error(f"[WhatsApp] Template send failed: {e}")
            return {"error": str(e)}

    async def send_message(
        self,
        phone: str,
        text: str,
    ) -> dict:
        """Send a free-form message (within 24h window)."""
        try:
            to_number = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            async with get_http_client("twilio") as client:
                resp = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "Body": text,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return {"message_sid": data.get("sid")}

        except Exception as e:
            logger.error(f"[WhatsApp] Message send failed: {e}")
            return {"error": str(e)}

    async def send_buttons(
        self,
        phone: str,
        body_text: str,
        buttons: list[dict],  # [{"id": "btn1", "title": "Option 1"}, ...]
    ) -> dict:
        """Send interactive message with quick reply buttons (max 3)."""
        try:
            to_number = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            # Twilio interactive button format
            import json
            interactive = {
                "type": "button",
                "body": {"text": body_text},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                        for b in buttons[:3]  # Max 3 buttons
                    ]
                },
            }

            async with get_http_client("twilio") as client:
                resp = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "Body": body_text,  # Fallback
                        "PersistentAction": json.dumps(interactive),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return {"message_sid": data.get("sid")}

        except Exception as e:
            logger.error(f"[WhatsApp] Buttons send failed: {e}")
            return {"error": str(e)}

    async def send_cta(
        self,
        phone: str,
        text: str,
        url: str,
        button_text: str = "Abrir",
    ) -> dict:
        """Send message with CTA button (opens URL)."""
        # CTA messages use template or interactive format
        full_text = f"{text}\n\n{button_text}: {url}"
        return await self.send_message(phone, full_text)

    async def trigger_flow(
        self,
        phone: str,
        flow_id: str,
        flow_token: str = "",
    ) -> dict:
        """Trigger a WhatsApp Flow (multi-screen form)."""
        try:
            to_number = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            import json
            interactive = {
                "type": "flow",
                "header": {"type": "text", "text": "LIA - Onboarding"},
                "body": {"text": "Responda 4 perguntas rapidas para eu te conhecer melhor:"},
                "footer": {"text": "Leva menos de 1 minuto"},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_id": flow_id,
                        "flow_token": flow_token or phone,
                        "mode": "published",
                    },
                },
            }

            async with get_http_client("twilio") as client:
                resp = await client.post(
                    url,
                    auth=(self.account_sid, self.auth_token),
                    data={
                        "From": self.from_number,
                        "To": to_number,
                        "PersistentAction": json.dumps(interactive),
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return {"message_sid": data.get("sid")}

        except Exception as e:
            logger.error(f"[WhatsApp] Flow trigger failed: {e}")
            return {"error": str(e)}
