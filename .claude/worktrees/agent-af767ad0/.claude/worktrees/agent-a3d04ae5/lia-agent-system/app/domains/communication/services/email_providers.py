"""
Email providers abstraction layer.
Supports Resend as primary provider.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailResult:
    """Result of sending an email."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider:
    """Base class for email providers."""
    
    def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> EmailResult:
        raise NotImplementedError


class ResendProvider(EmailProvider):
    """Resend email provider."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            import resend
            resend.api_key = api_key
            self._resend = resend
            self._available = True
        except ImportError:
            logger.warning("Resend package not installed")
            self._resend = None
            self._available = False
    
    @property
    def is_available(self) -> bool:
        return self._available and bool(self.api_key)
    
    def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> EmailResult:
        if not self.is_available:
            return EmailResult(success=False, error="Resend not available")
        
        try:
            sender = from_email or os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
            if from_name:
                sender = f"{from_name} <{sender}>"
            
            params: Dict[str, Any] = {
                "from": sender,
                "to": [to],
                "subject": subject,
                "html": html,
            }
            if text:
                params["text"] = text
            if reply_to:
                params["reply_to"] = reply_to
            
            response = self._resend.Emails.send(params)
            message_id = response.get("id") if isinstance(response, dict) else None
            logger.info(f"Email sent via Resend: to={to}, id={message_id}")
            return EmailResult(success=True, message_id=message_id)
        except Exception as e:
            logger.error(f"Resend error: {e}")
            return EmailResult(success=False, error=str(e))


class MockProvider(EmailProvider):
    """Mock provider for development/testing."""
    
    def send(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> EmailResult:
        logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}")
        return EmailResult(success=True, message_id="mock-id")


_provider_instance: Optional[EmailProvider] = None


def get_email_provider() -> EmailProvider:
    """Get the configured email provider."""
    global _provider_instance
    
    if _provider_instance is None:
        api_key = os.environ.get("RESEND_API_KEY")
        if api_key:
            _provider_instance = ResendProvider(api_key)
            if _provider_instance.is_available:
                logger.info("Using Resend email provider")
            else:
                logger.warning("Resend not available, using mock provider")
                _provider_instance = MockProvider()
        else:
            logger.warning("No RESEND_API_KEY, using mock provider")
            _provider_instance = MockProvider()
    
    return _provider_instance


def get_provider_for_client(client_id: Optional[str] = None) -> EmailProvider:
    """Get provider for a specific client (returns default for now)."""
    return get_email_provider()


def get_all_providers_status() -> Dict[str, Any]:
    """Get status of all configured providers."""
    api_key = os.environ.get("RESEND_API_KEY")
    return {
        "resend": {
            "configured": bool(api_key),
            "active": bool(api_key)
        }
    }
