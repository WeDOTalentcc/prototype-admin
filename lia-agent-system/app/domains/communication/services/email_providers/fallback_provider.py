"""
Fallback composite email provider.

Wraps a primary provider (Mailgun) and a fallback provider (Resend).
When the primary fails or its circuit breaker is open, automatically
retries via the fallback provider without requiring any caller changes.
"""
import logging
from datetime import datetime
from typing import Any

from app.shared.resilience.circuit_breaker import (
    MAILGUN_CIRCUIT,
    RESEND_CIRCUIT,
    CircuitState,
)

from .base import EmailMessage, EmailProvider, EmailResult

logger = logging.getLogger(__name__)


class FallbackEmailProvider(EmailProvider):
    """
    Composite email provider that implements automatic failover.

    Strategy:
    1. Check MAILGUN_CIRCUIT state — if OPEN, skip Mailgun entirely.
    2. Try primary provider (Mailgun).
    3. If primary fails or circuit opens, check RESEND_CIRCUIT state.
    4. Try fallback provider (Resend) when circuit is closed.
    5. Return the first successful result; propagate the last error if all fail.

    This provider does NOT decorate itself with a circuit breaker — each
    underlying provider already carries its own circuit-breaker decorator.
    """

    provider_name = "mailgun_with_resend_fallback"

    def __init__(
        self,
        primary: EmailProvider,
        fallback: EmailProvider,
    ):
        self._primary = primary
        self._fallback = fallback

    def get_status(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "primary": self._primary.get_status(),
            "fallback": self._fallback.get_status(),
            "configured": True,
            "healthy": (
                self._primary.get_status().get("configured", False)
                or self._fallback.get_status().get("configured", False)
            ),
        }

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
        """Send email with automatic Mailgun→Resend failover."""

        primary_circuit_open = MAILGUN_CIRCUIT.state == CircuitState.OPEN
        primary_result: EmailResult | None = None

        if not primary_circuit_open:
            try:
                primary_result = await self._primary.send_email(
                    to=to,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    from_email=from_email,
                    from_name=from_name,
                    reply_to=reply_to,
                    cc=cc,
                    bcc=bcc,
                    headers=headers,
                    metadata=metadata,
                )
                if primary_result.success:
                    return primary_result
                logger.warning(
                    "[FALLBACK PROVIDER] Mailgun failed for %s: %s — trying Resend",
                    to, primary_result.error
                )
            except Exception as exc:
                logger.warning(
                    "[FALLBACK PROVIDER] Mailgun exception for %s: %s — trying Resend",
                    to, exc
                )
                primary_result = EmailResult(
                    success=False,
                    provider=self._primary.provider_name,
                    status="failed",
                    error=str(exc),
                    error_code=type(exc).__name__,
                )
        else:
            logger.warning(
                "[FALLBACK PROVIDER] MAILGUN_CIRCUIT is OPEN — routing %s to Resend", to
            )

        fallback_circuit_open = RESEND_CIRCUIT.state == CircuitState.OPEN
        if fallback_circuit_open:
            logger.error(
                "[FALLBACK PROVIDER] RESEND_CIRCUIT is also OPEN — both providers unavailable for %s",
                to
            )
            return primary_result or EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error="Both Mailgun and Resend circuits are OPEN",
                error_code="ALL_CIRCUITS_OPEN",
                sent_at=datetime.utcnow(),
            )

        try:
            fallback_result = await self._fallback.send_email(
                to=to,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                cc=cc,
                bcc=bcc,
                headers=headers,
                metadata=metadata,
            )
            if fallback_result.success:
                logger.info(
                    "[FALLBACK PROVIDER] Resend delivered to %s, ID: %s",
                    to, fallback_result.message_id
                )
            else:
                logger.error(
                    "[FALLBACK PROVIDER] Resend also failed for %s: %s",
                    to, fallback_result.error
                )
            return fallback_result
        except Exception as exc:
            logger.error(
                "[FALLBACK PROVIDER] Resend exception for %s: %s",
                to, exc, exc_info=True
            )
            return EmailResult(
                success=False,
                provider=self._fallback.provider_name,
                status="failed",
                error=str(exc),
                error_code=type(exc).__name__,
            )

    async def send_bulk(
        self,
        messages: list[EmailMessage],
    ) -> list[EmailResult]:
        """Send bulk emails with per-message failover."""
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
