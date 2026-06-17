"""
Abstract base class for email providers.
Provides a unified interface for different email sending services.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LGPD — Footer obrigatório em todos os emails enviados pela plataforma (K1)
#
# Identifica o sistema de IA, sub-processador Mailgun, e oferece opt-out.
# Deve ser injetado via EmailProvider.with_lgpd_footer() antes de envio.
# ---------------------------------------------------------------------------

BASE_EMAIL_FOOTER_HTML = (
    '<hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0"/>'
    '<p style="font-size:11px;color:#9ca3af;font-family:sans-serif;line-height:1.5">'
    "Este email foi gerado por <strong>LIA</strong>, assistente de recrutamento com inteligência artificial da WeDOTalent. "
    "O envio é realizado via <strong>Mailgun</strong> (sub-processador de dados — LGPD Lei 13.709/2018). "
    "Para exercer seus direitos de titular (acesso, correção, exclusão) ou cancelar o recebimento de comunicações, "
    "responda este email com o assunto <strong>PRIVACIDADE</strong> ou acesse "
    '<a href="https://wedotalent.com.br/privacidade" style="color:#6b7280">wedotalent.com.br/privacidade</a>.'
    "</p>"
)

BASE_EMAIL_FOOTER_TEXT = (
    "\n\n---\n"
    "Este email foi gerado por LIA, assistente de recrutamento com IA da WeDOTalent. "
    "Envio via Mailgun (sub-processador LGPD). "
    "Para exercer direitos de titular ou cancelar comunicações, responda com assunto PRIVACIDADE "
    "ou acesse wedotalent.com.br/privacidade."
)


@dataclass
class EmailMessage:
    """Data class representing an email message."""
    to: str
    subject: str
    html_content: str
    text_content: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    headers: dict[str, str] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailResult:
    """Result of an email send operation."""
    success: bool
    message_id: str | None = None
    provider: str = ""
    status: str = "unknown"
    error: str | None = None
    error_code: str | None = None
    sent_at: datetime | None = None
    raw_response: dict[str, Any] | None = None


class EmailProvider(ABC):
    """
    Abstract base class for email providers.
    
    Implementations should handle:
    - Single email sending
    - Bulk email sending
    - Health check/status reporting
    """
    
    provider_name: str = "base"
    
    @abstractmethod
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
        metadata: dict[str, Any] | None = None
    ) -> EmailResult:
        """
        Send a single email.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            html_content: HTML body content
            text_content: Plain text body (optional)
            from_email: Sender email address (uses default if not provided)
            from_name: Sender display name
            reply_to: Reply-to email address
            cc: List of CC recipients
            bcc: List of BCC recipients
            headers: Additional email headers
            metadata: Custom metadata for tracking
        
        Returns:
            EmailResult with success status and details
        """
        pass
    
    @abstractmethod
    async def send_bulk(
        self,
        messages: list[EmailMessage]
    ) -> list[EmailResult]:
        """
        Send multiple emails in bulk.
        
        Args:
            messages: List of EmailMessage objects to send
        
        Returns:
            List of EmailResult objects for each message
        """
        pass
    
    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Get provider status for health checks.
        
        Returns:
            Dictionary with status information:
            - provider: Provider name
            - configured: Whether API key is set
            - healthy: Whether provider is operational
            - details: Additional status details
        """
        pass
    
    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        status = self.get_status()
        return status.get("configured", False)

    def is_healthy(self) -> bool:
        """Check if the provider is healthy and ready to send emails."""
        status = self.get_status()
        return status.get("healthy", False)

    @staticmethod
    def with_lgpd_footer(message: "EmailMessage") -> "EmailMessage":
        """
        Retorna uma cópia do EmailMessage com footer LGPD/Mailgun obrigatório.

        LGPD — K1: Todo email enviado pela plataforma deve identificar o sistema
        de IA e o sub-processador Mailgun, e oferecer opt-out ao titular.

        Uso nos providers:
            message = EmailProvider.with_lgpd_footer(message)
            await self._send_impl(message)
        """
        from dataclasses import replace as dc_replace
        html = message.html_content + BASE_EMAIL_FOOTER_HTML
        text = (message.text_content or "") + BASE_EMAIL_FOOTER_TEXT
        return dc_replace(message, html_content=html, text_content=text)
