"""
Mailgun email provider implementation.
Uses the Mailgun HTTP API for transactional email delivery.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Any


from app.shared.resilience.circuit_breaker import MAILGUN_CIRCUIT, circuit_breaker_decorator

from .base import EmailMessage, EmailProvider, EmailResult

logger = logging.getLogger(__name__)

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None  # type: ignore[assignment]


class MailgunProvider(EmailProvider):
    """
    Mailgun-based email provider.

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
        api_key: str | None = None,
        domain: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        api_base: str | None = None,
    ):
        self.api_key = api_key or os.getenv("MAILGUN") or os.getenv("MAILGUN_API_KEY")
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
        text_content: str | None = None,
        from_email: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        headers: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> EmailResult:
        """Send a single email via Mailgun."""
        if not self._configured:
            logger.info("[SIMULATED] Mailgun email to: %s, subject: %s", to, subject)
            return EmailResult(
                success=True,
                message_id=f"simulated-mg-{datetime.utcnow().timestamp()}",
                provider=self.provider_name,
                status="simulated",
                sent_at=datetime.utcnow(),
            )

        try:
            sender_name = from_name or self.from_name
            sender_addr = from_email or self.from_email
            sender = f"{sender_name} <{sender_addr}>" if sender_name else sender_addr

            data: dict[str, Any] = {
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
                data["cc"] = ",".join(cc)
            if bcc:
                data["bcc"] = ",".join(bcc)

            if headers:
                for key, value in headers.items():
                    data[f"h:{key}"] = value

            if metadata:
                for key, value in metadata.items():
                    if key != "categories":
                        data[f"v:{key}"] = str(value)

            url = f"{self.api_base}/{self.domain}/messages"
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    url,
                    auth=("api", self.api_key),
                    data=data,
                )

            if resp.status_code == 200:
                payload = resp.json()
                message_id = payload.get("id", "")
                logger.info("Email sent via Mailgun to %s, ID: %s", to, message_id)
                return EmailResult(
                    success=True,
                    message_id=message_id,
                    provider=self.provider_name,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    raw_response=payload,
                )
            else:
                error_body = resp.text
                logger.error(
                    "Mailgun returned error: %s - %s", resp.status_code, error_body
                )
                return EmailResult(
                    success=False,
                    provider=self.provider_name,
                    status="failed",
                    error=error_body,
                    error_code=str(resp.status_code),
                    raw_response={"status_code": resp.status_code, "body": error_body},
                )

        except Exception as e:
            logger.error("Failed to send email via Mailgun: %s", str(e))
            return EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(e),
                error_code="MAILGUN_ERROR",
            )

    async def send_bulk(
        self,
        messages: list[EmailMessage],
    ) -> list[EmailResult]:
        """
        Send multiple emails via Mailgun.

        Sends individually with a short delay to avoid rate limits.
        """
        results = []
        for message in messages:
            result = await self.send_email(
                to=message.to,
                subject=message.subject,
                html_content=message.html_content,
                text_content=message.text_content,
                from_email=message.from_email,
                from_name=message.from_name,
                reply_to=message.reply_to,
                cc=message.cc,
                bcc=message.bcc,
                headers=message.headers,
                metadata=message.metadata,
            )
            results.append(result)
            await asyncio.sleep(0.05)
        return results

    def get_status(self) -> dict[str, Any]:
        """Get Mailgun provider status."""
        return {
            "provider": self.provider_name,
            "configured": self._configured,
            "healthy": self._configured and HTTPX_AVAILABLE,
            "sdk_available": HTTPX_AVAILABLE,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "domain": self.domain,
            "details": {
                "api_key_set": bool(self.api_key),
                "domain_set": bool(self.domain),
                "mode": "live" if self._configured else "simulated",
            },
        }
