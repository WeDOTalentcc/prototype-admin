"""
SendGrid email provider implementation.
Uses the official SendGrid SDK for transactional email delivery.
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import EmailProvider, EmailMessage, EmailResult
from app.shared.resilience.circuit_breaker import SENDGRID_CIRCUIT, circuit_breaker_decorator

logger = logging.getLogger(__name__)

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail, 
        Email, 
        To, 
        Content, 
        Cc, 
        Bcc,
        ReplyTo,
        Header,
        Category,
        Personalization
    )
    SENDGRID_SDK_AVAILABLE = True
except ImportError:
    SENDGRID_SDK_AVAILABLE = False
    SendGridAPIClient = None
    Mail = None


class SendGridProvider(EmailProvider):
    """
    SendGrid-based email provider.
    
    Environment Variables:
    - SENDGRID_API_KEY: SendGrid API key
    - SENDGRID_FROM_EMAIL: Default sender email (default: noreply@wedotalent.com)
    - SENDGRID_FROM_NAME: Default sender name (default: WeDo Talent)
    """
    
    provider_name = "sendgrid"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("SENDGRID_API_KEY")
        self.from_email = from_email or os.getenv(
            "SENDGRID_FROM_EMAIL", 
            "noreply@wedotalent.com"
        )
        self.from_name = from_name or os.getenv(
            "SENDGRID_FROM_NAME",
            "WeDo Talent"
        )
        self._client: Optional[Any] = None
        self._configured = False
        
        if self.api_key and SENDGRID_SDK_AVAILABLE:
            self._client = SendGridAPIClient(self.api_key)
            self._configured = True
            logger.info(f"SendGrid provider configured. From: {self.from_email}")
        else:
            if not SENDGRID_SDK_AVAILABLE:
                logger.warning("SendGrid SDK not available - emails will be simulated")
            else:
                logger.warning("SENDGRID_API_KEY not found - emails will be simulated")
    
    @circuit_breaker_decorator(SENDGRID_CIRCUIT)
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
        """Send a single email via SendGrid."""
        
        if not self._configured:
            logger.info(f"[SIMULATED] SendGrid email to: {to}, subject: {subject}")
            return EmailResult(
                success=True,
                message_id=f"simulated-sg-{datetime.utcnow().timestamp()}",
                provider=self.provider_name,
                status="simulated",
                sent_at=datetime.utcnow()
            )
        
        try:
            sender_email = from_email or self.from_email
            sender_name = from_name or self.from_name
            
            from_email_obj = Email(sender_email, sender_name)
            to_email_obj = To(to)
            
            message = Mail(
                from_email=from_email_obj,
                to_emails=to_email_obj,
                subject=subject
            )
            
            message.add_content(Content("text/html", html_content))
            
            if text_content:
                message.add_content(Content("text/plain", text_content))
            
            if reply_to:
                message.reply_to = ReplyTo(reply_to)
            
            if cc:
                for cc_email in cc:
                    message.add_cc(Cc(cc_email))
            
            if bcc:
                for bcc_email in bcc:
                    message.add_bcc(Bcc(bcc_email))
            
            if headers:
                for key, value in headers.items():
                    message.add_header(Header(key, value))
            
            if metadata and metadata.get("categories"):
                for cat in metadata["categories"]:
                    message.add_category(Category(cat))
            
            response = await asyncio.to_thread(
                self._client.send, message
            )
            
            if response.status_code in (200, 201, 202):
                message_id = response.headers.get("X-Message-Id", "")
                logger.info(f"Email sent via SendGrid to {to}, ID: {message_id}")
                return EmailResult(
                    success=True,
                    message_id=message_id,
                    provider=self.provider_name,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    raw_response={
                        "status_code": response.status_code,
                        "headers": dict(response.headers)
                    }
                )
            else:
                error_body = response.body.decode() if response.body else "Unknown error"
                logger.error(f"SendGrid returned error: {response.status_code} - {error_body}")
                return EmailResult(
                    success=False,
                    provider=self.provider_name,
                    status="failed",
                    error=error_body,
                    error_code=str(response.status_code),
                    raw_response={
                        "status_code": response.status_code,
                        "body": error_body
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {str(e)}")
            return EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(e),
                error_code="SENDGRID_ERROR"
            )
    
    async def send_bulk(
        self,
        messages: List[EmailMessage]
    ) -> List[EmailResult]:
        """
        Send multiple emails via SendGrid.
        
        SendGrid supports batch sending, but for simplicity we send 
        individually with a small delay to avoid rate limits.
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
                metadata=message.metadata
            )
            results.append(result)
            await asyncio.sleep(0.05)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get SendGrid provider status."""
        return {
            "provider": self.provider_name,
            "configured": self._configured,
            "healthy": self._configured and SENDGRID_SDK_AVAILABLE,
            "sdk_available": SENDGRID_SDK_AVAILABLE,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "details": {
                "api_key_set": bool(self.api_key),
                "mode": "live" if self._configured else "simulated"
            }
        }
