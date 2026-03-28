"""
Twilio WhatsApp Service

WhatsApp Business API integration using Twilio as the messaging provider.

Environment Variables Required:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_WHATSAPP_NUMBER: Twilio WhatsApp sender number (format: whatsapp:+1234567890)
"""

import os
import logging
import hmac
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlencode

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator

from app.services.whatsapp_provider import (
    WhatsAppProvider,
    ProviderType,
    SendResult,
    IncomingMessage
)

logger = logging.getLogger(__name__)


class TwilioWhatsAppService(WhatsAppProvider):
    """
    Twilio WhatsApp Business API Service.
    
    Features:
    - Text messages
    - Interactive messages (via template workaround)
    - Document/media handling
    - Webhook verification and parsing
    
    Setup Requirements:
    1. Twilio Account with WhatsApp enabled
    2. WhatsApp Sender approved in Twilio Console
    3. Webhook URL configured in Twilio
    """
    
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        self._client: Optional[Client] = None
        self._validator: Optional[RequestValidator] = None
        
        if not self.is_configured:
            logger.warning("Twilio WhatsApp credentials not configured. Service will log messages only.")
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.TWILIO
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local", "test")
    
    @property
    def is_configured(self) -> bool:
        """Check if Twilio service is properly configured."""
        return bool(self.account_sid and self.auth_token and self.whatsapp_number)
    
    @property
    def client(self) -> Optional[Client]:
        """Get or create Twilio client."""
        if self._client is None and self.is_configured:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client
    
    @property
    def validator(self) -> Optional[RequestValidator]:
        """Get or create Twilio request validator."""
        if self._validator is None and self.auth_token:
            self._validator = RequestValidator(self.auth_token)
        return self._validator
    
    def _format_whatsapp_number(self, phone: str) -> str:
        """Format phone number for Twilio WhatsApp API (whatsapp:+...)."""
        cleaned = self.format_phone_number(phone)
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        return f"whatsapp:{cleaned}"
    
    async def send_text_message(self, to: str, text: str) -> SendResult:
        """Send a text message via Twilio WhatsApp API."""
        formatted_to = self._format_whatsapp_number(to)
        
        if self.is_development or not self.is_configured:
            return await self._send_development(formatted_to, text, "text")
        
        try:
            message = self.client.messages.create(
                body=text,
                from_=self.whatsapp_number,
                to=formatted_to
            )
            
            logger.info(f"[TWILIO WHATSAPP] Sent to {formatted_to}: {message.sid}")
            
            return SendResult(
                success=True,
                message_id=message.sid,
                sent_at=datetime.utcnow(),
                provider="twilio",
                metadata={"status": message.status, "to": formatted_to}
            )
            
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] API error: {e.code} - {e.msg}")
            return SendResult(
                success=False,
                error=e.msg,
                error_code=str(e.code),
                provider="twilio",
                metadata={"details": str(e)}
            )
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Send error: {e}")
            return SendResult(success=False, error=str(e), provider="twilio")
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> SendResult:
        """
        Send an interactive message with buttons.
        
        Note: Twilio WhatsApp doesn't support native interactive buttons
        in the same way as Meta. We simulate with numbered options.
        """
        formatted_to = self._format_whatsapp_number(to)
        
        button_lines = []
        for i, btn in enumerate(buttons[:10], 1):
            button_lines.append(f"{i}. {btn['title']}")
        
        full_text = body_text
        if header_text:
            full_text = f"*{header_text}*\n\n{full_text}"
        full_text += "\n\n" + "\n".join(button_lines)
        if footer_text:
            full_text += f"\n\n_{footer_text}_"
        
        if self.is_development or not self.is_configured:
            return await self._send_development(formatted_to, full_text, "interactive")
        
        try:
            message = self.client.messages.create(
                body=full_text,
                from_=self.whatsapp_number,
                to=formatted_to
            )
            
            logger.info(f"[TWILIO WHATSAPP] Interactive sent to {formatted_to}: {message.sid}")
            
            return SendResult(
                success=True,
                message_id=message.sid,
                sent_at=datetime.utcnow(),
                provider="twilio",
                metadata={"response": {"sid": message.sid, "status": message.status}}
            )
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] Interactive send error: {e.code} - {e.msg}")
            return SendResult(
                success=False,
                error=e.msg,
                error_code=str(e.code),
                provider="twilio"
            )
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Interactive send error: {e}")
            return SendResult(success=False, error=str(e), provider="twilio")
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        caption: Optional[str] = None,
        filename: Optional[str] = None
    ) -> SendResult:
        """Send a document via Twilio WhatsApp API."""
        formatted_to = self._format_whatsapp_number(to)
        
        if self.is_development or not self.is_configured:
            msg = f"[Document: {filename or document_url}]"
            if caption:
                msg += f"\n{caption}"
            return await self._send_development(formatted_to, msg, "document")
        
        try:
            message = self.client.messages.create(
                body=caption or "",
                from_=self.whatsapp_number,
                to=formatted_to,
                media_url=[document_url]
            )
            
            logger.info(f"[TWILIO WHATSAPP] Document sent to {formatted_to}: {message.sid}")
            
            return SendResult(
                success=True,
                message_id=message.sid,
                sent_at=datetime.utcnow(),
                provider="twilio",
                metadata={"status": message.status, "media_url": document_url}
            )
            
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] Document send error: {e.code} - {e.msg}")
            return SendResult(
                success=False,
                error=e.msg,
                error_code=str(e.code),
                provider="twilio"
            )
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Document send error: {e}")
            return SendResult(success=False, error=str(e), provider="twilio")
    
    def verify_webhook_signature(self, payload: bytes, signature: str, url: str = "") -> bool:
        """
        Verify Twilio webhook signature.
        
        Args:
            payload: Raw request body bytes (form data)
            signature: X-Twilio-Signature header value
            url: Full webhook URL
            
        Returns:
            True if signature is valid
        """
        if not self.auth_token:
            logger.warning("[TWILIO WEBHOOK] Auth token not configured, skipping verification")
            return True
        
        if not signature:
            return False
        
        if self.validator and url:
            try:
                params = dict(item.split("=") for item in payload.decode().split("&") if "=" in item)
                from urllib.parse import unquote_plus
                params = {k: unquote_plus(v) for k, v in params.items()}
                return self.validator.validate(url, params, signature)
            except Exception as e:
                logger.error(f"[TWILIO WEBHOOK] Signature validation error: {e}")
                return False
        
        return True
    
    def parse_webhook_message(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Parse incoming Twilio webhook payload.
        
        Twilio sends form data with fields like:
        - MessageSid: Unique message ID
        - From: Sender number (whatsapp:+...)
        - To: Recipient number
        - Body: Message text
        - NumMedia: Number of media attachments
        - MediaUrl0, MediaContentType0, etc.
        """
        try:
            message_sid = payload.get("MessageSid")
            if not message_sid:
                if payload.get("SmsStatus") or payload.get("MessageStatus"):
                    return IncomingMessage(
                        type="status_update",
                        message_id=payload.get("SmsSid") or payload.get("MessageSid"),
                        status=payload.get("SmsStatus") or payload.get("MessageStatus"),
                        recipient_id=payload.get("To", "").replace("whatsapp:", ""),
                        metadata=payload
                    )
                return None
            
            from_number = payload.get("From", "").replace("whatsapp:", "").replace("+", "")
            body = payload.get("Body", "")
            num_media = int(payload.get("NumMedia", 0))
            
            parsed = IncomingMessage(
                type="message",
                message_id=message_sid,
                from_number=from_number,
                timestamp=payload.get("Timestamp"),
                contact_name=payload.get("ProfileName"),
                text=body,
                metadata={
                    "account_sid": payload.get("AccountSid"),
                    "to": payload.get("To"),
                    "wa_id": payload.get("WaId"),
                    "provider": "twilio"
                }
            )
            
            if num_media > 0:
                media_url = payload.get("MediaUrl0")
                media_type = payload.get("MediaContentType0", "")
                
                if "image" in media_type:
                    parsed.message_type = "image"
                    parsed.image = {
                        "id": message_sid,
                        "url": media_url,
                        "mime_type": media_type,
                        "caption": body
                    }
                elif "pdf" in media_type or "document" in media_type or "msword" in media_type:
                    parsed.message_type = "document"
                    parsed.document = {
                        "id": message_sid,
                        "url": media_url,
                        "mime_type": media_type,
                        "filename": payload.get("MediaFilename0"),
                        "caption": body
                    }
                else:
                    parsed.message_type = "media"
                    parsed.metadata["media"] = {
                        "url": media_url,
                        "mime_type": media_type
                    }
            else:
                parsed.message_type = "text"
            
            return parsed
            
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Error parsing webhook: {e}")
            return None
    
    async def download_media(self, media_url: str) -> Dict[str, Any]:
        """
        Download media from Twilio.
        
        Args:
            media_url: The media URL from the webhook
            
        Returns:
            Dict with media content and metadata
        """
        if not self.is_configured:
            return {"success": False, "error": "Service not configured"}
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    media_url,
                    auth=(self.account_sid, self.auth_token)
                )
                response.raise_for_status()
                
                content_type = response.headers.get("content-type", "application/octet-stream")
                
                logger.info(f"[TWILIO WHATSAPP] Downloaded media from {media_url}")
                
                return {
                    "success": True,
                    "content": response.content,
                    "mime_type": content_type,
                    "file_size": len(response.content)
                }
                
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Media download error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_development(
        self,
        to: str,
        text: str,
        msg_type: str = "text"
    ) -> SendResult:
        """Log message in development mode."""
        import uuid
        message_id = f"dev_twilio_{uuid.uuid4().hex[:12]}"
        
        logger.info("=" * 70)
        logger.info(f"[DEV TWILIO WHATSAPP] Mensagem ({msg_type}) - modo desenvolvimento")
        logger.info(f"[DEV TWILIO WHATSAPP] Message ID: {message_id}")
        logger.info(f"[DEV TWILIO WHATSAPP] Para: {to}")
        logger.info(f"[DEV TWILIO WHATSAPP] Conteúdo ({len(text)} chars):")
        for line in text.split('\n')[:20]:
            logger.info(f"[DEV TWILIO WHATSAPP]   {line}")
        if len(text.split('\n')) > 20:
            logger.info(f"[DEV TWILIO WHATSAPP]   ... ({len(text.split(chr(10))) - 20} mais linhas)")
        logger.info("=" * 70)
        
        return SendResult(
            success=True,
            message_id=message_id,
            sent_at=datetime.utcnow(),
            provider="twilio",
            metadata={"mode": "development", "to": to}
        )


twilio_whatsapp_service = TwilioWhatsAppService()
