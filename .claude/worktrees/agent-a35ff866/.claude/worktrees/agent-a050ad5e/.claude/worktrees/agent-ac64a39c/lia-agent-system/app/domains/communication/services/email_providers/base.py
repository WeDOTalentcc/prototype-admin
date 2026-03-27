"""
Abstract base class for email providers.
Provides a unified interface for different email sending services.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Data class representing an email message."""
    to: str
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailResult:
    """Result of an email send operation."""
    success: bool
    message_id: Optional[str] = None
    provider: str = ""
    status: str = "unknown"
    error: Optional[str] = None
    error_code: Optional[str] = None
    sent_at: Optional[datetime] = None
    raw_response: Optional[Dict[str, Any]] = None


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
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
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
        messages: List[EmailMessage]
    ) -> List[EmailResult]:
        """
        Send multiple emails in bulk.
        
        Args:
            messages: List of EmailMessage objects to send
        
        Returns:
            List of EmailResult objects for each message
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
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
