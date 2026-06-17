"""
WhatsApp Service for LIA Platform.

Provides a clean interface for sending WhatsApp messages via Twilio with:
- Development mode with logging (no real sending)
- Template-based messages
- Interactive messages with buttons
- Status tracking: sent, delivered, read, failed

Environment Variables:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_WHATSAPP_FROM: WhatsApp sender number (default: sandbox number)
- ENVIRONMENT: 'development' for logging only, 'production' for real sending
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client as TwilioClient
    TWILIO_SDK_AVAILABLE = True
except ImportError:
    TWILIO_SDK_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception

logger = logging.getLogger(__name__)


class WhatsAppStatus(StrEnum):
    """WhatsApp message delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    QUEUED_DEVELOPMENT = "queued_development"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class SendWhatsAppRequest(WeDoBaseModel):
    """Request model for sending WhatsApp messages."""
    to_phone: str = Field(..., description="Recipient phone number (with country code)")
    message: str = Field(..., description="Message text")
    media_url: str | None = Field(None, description="URL of media to attach")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")
    candidate_id: str | None = Field(None, description="Candidate ID for tracking")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_phone": "+5511999999999",
                "message": "Olá! Sua entrevista está agendada para amanhã às 10h.",
            }
        }


class SendWhatsAppTemplateRequest(WeDoBaseModel):
    """Request model for sending template-based WhatsApp messages."""
    to_phone: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Template name from WhatsAppTemplates")
    template_data: dict[str, Any] = Field(..., description="Template variables")
    media_url: str | None = Field(None, description="URL of media to attach")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")
    candidate_id: str | None = Field(None, description="Candidate ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_phone": "+5511999999999",
                "template_name": "screening_passed",
                "template_data": {
                    "candidate_name": "João Silva",
                    "strengths": ["Comunicação clara", "Experiência técnica"]
                }
            }
        }


class InteractiveButton(BaseModel):
    """Button for interactive WhatsApp messages."""
    id: str = Field(..., description="Button ID for callback")
    title: str = Field(..., description="Button text (max 20 chars)")


class SendInteractiveRequest(WeDoBaseModel):
    """Request model for interactive WhatsApp messages with buttons."""
    to_phone: str = Field(..., description="Recipient phone number")
    header: str | None = Field(None, description="Message header")
    body: str = Field(..., description="Message body")
    footer: str | None = Field(None, description="Message footer")
    buttons: list[InteractiveButton] = Field(..., description="List of buttons (max 3)")
    metadata: dict[str, Any] | None = Field(default=None, description="Custom metadata")
    candidate_id: str | None = Field(None, description="Candidate ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_phone": "+5511999999999",
                "header": "Confirmação de Entrevista",
                "body": "Sua entrevista está agendada para amanhã às 10h. Você confirma sua presença?",
                "footer": "Responda clicando em um botão",
                "buttons": [
                    {"id": "confirm", "title": "Confirmar"},
                    {"id": "reschedule", "title": "Reagendar"}
                ]
            }
        }


class WhatsAppSendResult(BaseModel):
    """Result of a WhatsApp send operation."""
    success: bool
    message_id: str | None = None
    status: WhatsAppStatus = WhatsAppStatus.PENDING
    provider: str = "twilio"
    error: str | None = None
    error_code: str | None = None
    sent_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WhatsAppService:
    """
    WhatsApp Service with Twilio integration.
    
    Features:
    - Development mode: logs messages without sending
    - Production mode: sends via Twilio WhatsApp API
    - Template support using WhatsAppTemplates
    - Interactive messages with buttons
    - Status tracking: sent, delivered, read, failed
    
    Note on Twilio WhatsApp:
    - For sandbox testing, use the Twilio sandbox number
    - For production, you need a Twilio-approved WhatsApp Business number
    - Template messages must be pre-approved by WhatsApp for outbound messaging
    """
    
    TWILIO_STATUS_MAP = {
        "queued": WhatsAppStatus.QUEUED,
        "sending": WhatsAppStatus.PENDING,
        "sent": WhatsAppStatus.SENT,
        "delivered": WhatsAppStatus.DELIVERED,
        "read": WhatsAppStatus.READ,
        "failed": WhatsAppStatus.FAILED,
        "undelivered": WhatsAppStatus.UNDELIVERED,
    }
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self._client = None
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() in ("development", "dev", "local", "test")
    
    @property
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return bool(self.account_sid and self.auth_token) and TWILIO_SDK_AVAILABLE
    
    @property
    def client(self):
        """Lazy initialization of Twilio client."""
        if self._client is None and self.is_configured:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        return self._client
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number for WhatsApp."""
        phone = phone.strip()
        
        if phone.startswith("whatsapp:"):
            return phone
        
        cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
        
        if not cleaned.startswith("+"):
            if cleaned.startswith("55"):
                cleaned = "+" + cleaned
            else:
                cleaned = "+55" + cleaned
        
        return f"whatsapp:{cleaned}"
    
    async def send_message(
        self,
        to_phone: str,
        message: str,
        media_url: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> WhatsAppSendResult:
        """
        Send a WhatsApp message.
        
        In development mode, logs the message without sending.
        In production mode, sends via Twilio WhatsApp API.
        
        Args:
            to_phone: Recipient phone number with country code
            message: Message text content
            media_url: Optional URL of media to attach (image, document, etc.)
            metadata: Optional custom metadata
        
        Returns:
            WhatsAppSendResult with success status and message_id
        """
        if self.is_development:
            return await self._send_development(
                to_phone=to_phone,
                message=message,
                media_url=media_url,
                metadata=metadata
            )
        
        return await self._send_production(
            to_phone=to_phone,
            message=message,
            media_url=media_url,
            metadata=metadata
        )
    
    async def send_template(
        self,
        to_phone: str,
        template_name: str,
        template_data: dict[str, Any],
        media_url: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> WhatsAppSendResult:
        """
        Send a WhatsApp message using a predefined template.
        
        Uses WhatsAppTemplates from communication_templates.py to generate
        the message content based on template name and data.
        
        Args:
            to_phone: Recipient phone number
            template_name: Name of the template method in WhatsAppTemplates
            template_data: Dictionary of variables for template rendering
            media_url: Optional media URL to attach
            metadata: Optional custom metadata
        
        Returns:
            WhatsAppSendResult with success status and message_id
        """
        from app.templates.communication_templates import WhatsAppTemplates
        
        template_method = getattr(WhatsAppTemplates, template_name, None)
        if not template_method:
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                error=f"Template not found: {template_name}",
                error_code="TEMPLATE_NOT_FOUND"
            )
        
        try:
            message = template_method(**template_data)
        except TypeError as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Template {template_name} parameter error: {e}")
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                error=f"Template parameter error: {str(e)}",
                error_code="TEMPLATE_PARAM_ERROR"
            )
        except Exception as e:
            # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
            logger.error(f"Error rendering template {template_name}: {e}")
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                error=f"Template rendering error: {str(e)}",
                error_code="TEMPLATE_ERROR"
            )
        
        enriched_metadata = {
            **(metadata or {}),
            "template_name": template_name,
            "template_data": template_data
        }
        
        return await self.send_message(
            to_phone=to_phone,
            message=message,
            media_url=media_url,
            metadata=enriched_metadata
        )
    
    async def send_interactive(
        self,
        to_phone: str,
        body: str,
        buttons: list[InteractiveButton],
        header: str | None = None,
        footer: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> WhatsAppSendResult:
        """
        Send an interactive WhatsApp message with buttons.
        
        Note: Interactive messages require WhatsApp Business API and
        may have limitations based on your Twilio/WhatsApp approval status.
        In development mode, this simulates the interactive message.
        
        Args:
            to_phone: Recipient phone number
            body: Main message body
            buttons: List of InteractiveButton (max 3)
            header: Optional message header
            footer: Optional message footer
            metadata: Optional custom metadata
        
        Returns:
            WhatsAppSendResult with success status and message_id
        """
        if len(buttons) > 3:
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                error="Maximum 3 buttons allowed for interactive messages",
                error_code="TOO_MANY_BUTTONS"
            )
        
        button_text = "\n".join([f"[{b.title}]" for b in buttons])
        full_message = ""
        if header:
            full_message += f"*{header}*\n\n"
        full_message += body
        full_message += f"\n\n{button_text}"
        if footer:
            full_message += f"\n\n_{footer}_"
        
        enriched_metadata = {
            **(metadata or {}),
            "interactive": True,
            "buttons": [{"id": b.id, "title": b.title} for b in buttons],
            "header": header,
            "footer": footer
        }
        
        return await self.send_message(
            to_phone=to_phone,
            message=full_message,
            metadata=enriched_metadata
        )
    
    async def _send_development(
        self,
        to_phone: str,
        message: str,
        media_url: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> WhatsAppSendResult:
        """Send WhatsApp message in development mode (logging only)."""
        message_id = f"dev_wa_{uuid.uuid4().hex[:12]}"
        formatted_phone = self._format_phone_number(to_phone)
        
        logger.info("=" * 70)
        logger.info("[DEV WHATSAPP] Mensagem enviada (modo desenvolvimento)")
        logger.info(f"[DEV WHATSAPP] Message ID: {message_id}")
        # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
        logger.info(f"[DEV WHATSAPP] De: {self.from_number}")
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"[DEV WHATSAPP] Para: {formatted_phone}")
        if media_url:
            logger.info(f"[DEV WHATSAPP] Mídia: {media_url}")
        logger.info(f"[DEV WHATSAPP] Mensagem ({len(message)} caracteres):")
        for line in message.split('\n'):
            logger.info(f"[DEV WHATSAPP] {line}")
        if metadata:
            logger.info(f"[DEV WHATSAPP] Metadata: {metadata}")
        logger.info("=" * 70)
        
        return WhatsAppSendResult(
            success=True,
            message_id=message_id,
            status=WhatsAppStatus.QUEUED_DEVELOPMENT,
            provider="development",
            sent_at=datetime.utcnow(),
            metadata={
                "mode": "development",
                "to_phone": formatted_phone,
                "message_preview": message[:100]
            }
        )
    
    async def _send_production(
        self,
        to_phone: str,
        message: str,
        media_url: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> WhatsAppSendResult:
        """Send WhatsApp message via Twilio API in production mode."""
        if not TWILIO_SDK_AVAILABLE:
            logger.warning("Twilio SDK not installed — falling back to development mode")
            return await self._send_development(
                to_phone=to_phone,
                message=message,
                media_url=media_url,
                metadata={**(metadata or {}), "fallback_reason": "sdk_not_available"},
            )
        
        if not self.is_configured:
            logger.warning("Twilio not configured - falling back to development mode")
            return await self._send_development(
                to_phone=to_phone,
                message=message,
                media_url=media_url,
                metadata=metadata
            )
        
        try:
            formatted_to = self._format_phone_number(to_phone)
            formatted_from = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
            
            message_params = {
                "from_": formatted_from,
                "to": formatted_to,
                "body": message
            }
            
            if media_url:
                if isinstance(media_url, str):
                    message_params["media_url"] = [media_url]
                else:
                    message_params["media_url"] = media_url
            
            loop = asyncio.get_event_loop()
            twilio_message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(**message_params)
            )
            
            logger.info(f"[TWILIO WHATSAPP] Sent to: {formatted_to}, SID: {twilio_message.sid}")
            
            status = self.TWILIO_STATUS_MAP.get(twilio_message.status, WhatsAppStatus.PENDING)
            
            return WhatsAppSendResult(
                success=True,
                message_id=twilio_message.sid,
                status=status,
                provider="twilio",
                sent_at=datetime.utcnow(),
                metadata={
                    "twilio_status": twilio_message.status,
                    "to_phone": formatted_to,
                    "from_phone": formatted_from
                }
            )
        
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] API error: {e.code} - {e.msg}", exc_info=True)
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                provider="twilio",
                error=e.msg,
                error_code=str(e.code)
            )
        except Exception as e:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"[TWILIO WHATSAPP] Error sending to {to_phone}: {e}", exc_info=True)
            return WhatsAppSendResult(
                success=False,
                status=WhatsAppStatus.FAILED,
                provider="twilio",
                error=str(e),
                error_code=type(e).__name__
            )
    
    async def check_status(self, message_id: str) -> tuple[WhatsAppStatus, dict[str, Any]]:
        """
        Check WhatsApp message delivery status.
        
        For Twilio messages, this fetches the actual status from Twilio API.
        For development messages, returns simulated status.
        
        Args:
            message_id: The Twilio message SID or development ID
        
        Returns:
            Tuple of (status, additional_data)
        """
        if message_id.startswith("dev_"):
            return WhatsAppStatus.DELIVERED, {
                "provider": "development",
                "note": "Development messages are always marked as delivered"
            }
        
        if not self.is_configured:
            return WhatsAppStatus.SENT, {
                "provider": "twilio",
                "note": "Twilio not configured - cannot check status"
            }
        
        if not message_id.startswith("SM"):
            return WhatsAppStatus.SENT, {
                "provider": "twilio",
                "error": f"Invalid Twilio message SID format: {message_id}"
            }
        
        try:
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages(message_id).fetch()
            )
            
            status = self.TWILIO_STATUS_MAP.get(message.status, WhatsAppStatus.SENT)
            
            return status, {
                "provider": "twilio",
                "message_sid": message.sid,
                "twilio_status": message.status,
                "to": message.to,
                "from": message.from_,
                "date_sent": str(message.date_sent) if message.date_sent else None,
                "date_updated": str(message.date_updated) if message.date_updated else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
        
        except TwilioRestException as e:
            logger.error(f"[TWILIO] Error checking status for {message_id}: {e.code} - {e.msg}")
            return WhatsAppStatus.SENT, {
                "provider": "twilio",
                "error": e.msg,
                "error_code": str(e.code)
            }
        except Exception as e:
            logger.error(f"[TWILIO] Error checking status for {message_id}: {e}")
            return WhatsAppStatus.SENT, {
                "provider": "twilio",
                "error": str(e)
            }


whatsapp_service = WhatsAppService()


def get_whatsapp_service() -> "WhatsAppService":
    return whatsapp_service
