"""
Mailgun email provider implementation for the domain communication layer.
Uses the Mailgun HTTP API for transactional email delivery.
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import EmailProvider, EmailMessage, EmailResult
from app.shared.resilience.circuit_breaker import MAILGUN_CIRCUIT, circuit_breaker_decorator

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore[assignment]


class MailgunProvider(EmailProvider):
    """
    Mailgun-based email provider for the communication domain.

    Environment Variables:
    - MAILGUN_API_KEY: Mailgun API key (required)
    - MAILGUN_DOMAIN: Mailgun sending domain (required)
    - MAILGUN_FROM_EMAIL: Default sender email (default: noreply@wedotalent.com)
    - MAILGUN_FROM_NAME: Default sender name (default: WeDo Talent)
    - MAILGUN_API_BASE: Mailgun API base URL (default: https://api.mailgun.net/v3)
    """

    provider_name = "mailgun"

    def __init__(
        self,
        api_key: Optional[str] = None,
        domain: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("MAILGUN_API_KEY")
        self.domain = domain or os.getenv("MAILGUN_DOMAIN")
        self.from_email = from_email or os.getenv(
            "MAILGUN_FROM_EMAIL",
            "noreply@wedotalent.com"
        )
        self.from_name = from_name or os.getenv(
            "MAILGUN_FROM_NAME",
            "WeDo Talent"
        )
        self.api_base = api_base or os.getenv(
            "MAILGUN_API_BASE",
            "https://api.mailgun.net/v3"
        )
        self._configured = False

        if self.api_key and self.domain and HTTPX_AVAILABLE:
            self._configured = True
            logger.info(
                "Mailgun provider configured. Domain: %s, From: %s",
                self.domain, self.from_email
            )
        else:
            if not HTTPX_AVAILABLE:
                logger.warning("httpx not available — Mailgun emails will be simulated")
            elif not self.api_key:
                logger.warning("MAILGUN_API_KEY not set — emails will be simulated")
            elif not self.domain:
                logger.warning("MAILGUN_DOMAIN not set — emails will be simulated")

    @circuit_breaker_decorator(MAILGUN_CIRCUIT)
    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EmailResult:
        """Send a single email via Mailgun."""

        if not self._configured:
            logger.info("[SIMULATED] Mailgun email to: %s, subject: %s", to, subject)
            return EmailResult(
                success=True,
                message_id=f"simulated-{datetime.utcnow().timestamp()}",
                provider=self.provider_name,
                status="simulated",
                sent_at=datetime.utcnow()
            )

        try:
            sender_name = from_name or self.from_name
            sender_email = from_email or self.from_email
            sender = f"{sender_name} <{sender_email}>" if sender_name else sender_email

            data: Dict[str, Any] = {
                "from": sender,
                "to": to,
                "subject": subject,
                "html": html_content,
            }

            if text_content:
                data["text"] = text_content

            if reply_to:
                data["h:Reply-To"] = reply_to

            if cc:
                data["cc"] = ",".join(cc) if isinstance(cc, list) else cc

            if bcc:
                data["bcc"] = ",".join(bcc) if isinstance(bcc, list) else bcc

            if headers:
                for key, value in headers.items():
                    data[f"h:{key}"] = value

            if metadata:
                for key, value in metadata.items():
                    data[f"v:{key}"] = str(value)

            import httpx as _httpx

            async with _httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/{self.domain}/messages",
                    auth=("api", self.api_key),
                    data=data,
                )

            if response.status_code == 200:
                payload = response.json()
                message_id = payload.get("id", f"mg_{id(response)}")
                logger.info("[MAILGUN] Email sent to %s, ID: %s", to, message_id)
                return EmailResult(
                    success=True,
                    message_id=message_id,
                    provider=self.provider_name,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    raw_response=payload
                )
            else:
                logger.error(
                    "[MAILGUN] Failed to send to %s: %s %s",
                    to, response.status_code, response.text
                )
                return EmailResult(
                    success=False,
                    provider=self.provider_name,
                    status="failed",
                    error=f"Mailgun returned {response.status_code}: {response.text}",
                    error_code=str(response.status_code),
                )

        except Exception as exc:
            logger.error("[MAILGUN] Error sending email to %s: %s", to, exc, exc_info=True)
            return EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(exc),
                error_code=type(exc).__name__
            )

    @circuit_breaker_decorator(MAILGUN_CIRCUIT)
    async def send_bulk(
        self,
        messages: List[EmailMessage]
    ) -> List[EmailResult]:
        """Send multiple emails via Mailgun."""
        results = []
        for msg in messages:
            result = await self.send_email(
                to=msg.to,
                subject=msg.subject,
                html_content=msg.html_content,
                text_content=msg.text_content,
                from_email=msg.from_email,
                from_name=msg.from_name,
                reply_to=msg.reply_to,
                cc=msg.cc,
                bcc=msg.bcc,
                headers=msg.headers,
                metadata=msg.metadata,
            )
            results.append(result)
        return results

    def get_status(self) -> Dict[str, Any]:
        """Return provider health/configuration status."""
        return {
            "provider": self.provider_name,
            "configured": self._configured,
            "healthy": self._configured,
            "domain": self.domain or "not_set",
            "from_email": self.from_email,
        }

    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get delivery status for a specific message.
        Note: Mailgun does not expose per-message status via REST — use Event Webhooks.
        """
        return {
            "provider": self.provider_name,
            "message_id": message_id,
            "status": "unknown",
            "note": "Mailgun email status tracking requires webhook configuration.",
            "recommendation": "Set MAILGUN_WEBHOOK_SIGNING_KEY and configure Mailgun webhooks."
        }
