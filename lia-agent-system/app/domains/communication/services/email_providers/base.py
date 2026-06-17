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
