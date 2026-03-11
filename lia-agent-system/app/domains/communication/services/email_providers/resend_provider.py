"""
Resend email provider implementation.
Uses the Resend API for transactional email delivery.
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .base import EmailProvider, EmailMessage, EmailResult

logger = logging.getLogger(__name__)

try:
    import resend
    RESEND_SDK_AVAILABLE = True
except ImportError:
    RESEND_SDK_AVAILABLE = False
    resend = None


class ResendProvider(EmailProvider):
    """
    Resend-based email provider.
    
    Environment Variables:
    - RESEND_API_KEY: Resend API key
    - RESEND_FROM_EMAIL: Default sender email (default: LIA Recrutamento <onboarding@resend.dev>)
    """
    
    provider_name = "resend"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.from_email = from_email or os.getenv(
            "RESEND_FROM_EMAIL", 
            "onboarding@resend.dev"
        )
        self.from_name = from_name or os.getenv(
            "RESEND_FROM_NAME",
            "LIA Recrutamento"
        )
        self._configured = False
        
        if self.api_key and RESEND_SDK_AVAILABLE:
            resend.api_key = self.api_key
            self._configured = True
            logger.info(f"Resend provider configured. From: {self.from_email}")
        else:
            if not RESEND_SDK_AVAILABLE:
                logger.warning("Resend SDK not available - emails will be simulated")
            else:
                logger.warning("RESEND_API_KEY not found - emails will be simulated")
    
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
        """Send a single email via Resend."""
        
        if not self._configured:
            logger.info(f"[SIMULATED] Resend email to: {to}, subject: {subject}")
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
            
            params: Dict[str, Any] = {
                "from": sender,
                "to": [to],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            if reply_to:
                params["reply_to"] = reply_to
            
            if cc:
                params["cc"] = cc
            
            if bcc:
                params["bcc"] = bcc
            
            if headers:
                params["headers"] = headers
            
            response = await asyncio.to_thread(
                resend.Emails.send, params
            )
            
            if response and response.get("id"):
                logger.info(f"Email sent via Resend to {to}, ID: {response['id']}")
                return EmailResult(
                    success=True,
                    message_id=response["id"],
                    provider=self.provider_name,
                    status="sent",
                    sent_at=datetime.utcnow(),
                    raw_response=response
                )
            else:
                logger.error(f"Resend returned unexpected response: {response}")
                return EmailResult(
                    success=False,
                    provider=self.provider_name,
                    status="failed",
                    error="Unexpected response from Resend",
                    raw_response=response
                )
                
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {str(e)}")
            return EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(e),
                error_code="RESEND_ERROR"
            )
    
    async def send_bulk(
        self,
        messages: List[EmailMessage]
    ) -> List[EmailResult]:
        """Send multiple emails via Resend."""
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
        """Get Resend provider status."""
        return {
            "provider": self.provider_name,
            "configured": self._configured,
            "healthy": self._configured and RESEND_SDK_AVAILABLE,
            "sdk_available": RESEND_SDK_AVAILABLE,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "details": {
                "api_key_set": bool(self.api_key),
                "mode": "live" if self._configured else "simulated"
            }
        }
