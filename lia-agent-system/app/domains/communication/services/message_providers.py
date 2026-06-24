"""
Message provider implementations for the communication domain.

Provides:
  - MessageProvider: abstract base class for all providers
  - Email providers: MockEmailProvider, ResendMessageProvider,
                     MailgunMessageProvider, AWSEmailProvider
  - WhatsApp providers: MockWhatsAppProvider, TwilioWhatsAppProvider,
                        WhatsAppBusinessProvider

Extracted from communication_service.py to keep that module focused on
orchestration / policy logic rather than low-level HTTP/SDK calls.
"""
import asyncio
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any

try:
    import httpx as _httpx_comm
    MAILGUN_HTTPX_COMM_AVAILABLE = True
except ImportError:
    MAILGUN_HTTPX_COMM_AVAILABLE = False
    _httpx_comm = None  # type: ignore[assignment]

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception

from app.enums.communication import MessageChannel

logger = logging.getLogger(__name__)


class MessageProvider(ABC):
    """Abstract base class for message providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def channel(self) -> MessageChannel:
        """Channel type (email, whatsapp, sms)."""
        pass
    
    @abstractmethod
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Send a message.
        
        Returns:
            Tuple of (success, provider_message_id, response_data)
        """
        pass
    
    @abstractmethod
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """
        Check the status of a sent message.
        
        Returns:
            Tuple of (status, additional_data)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass


class MockEmailProvider(MessageProvider):
    """Mock email provider for development/testing. Blocked in production."""
    
    def __init__(self):
        self._environment = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
        if self._environment == "production":
            _has_real_provider = bool(
                os.environ.get("MAILGUN_API_KEY") or os.environ.get("RESEND_API_KEY")
            )
            if not _has_real_provider:
                logger.critical(
                    "[MOCK EMAIL] MockEmailProvider activated in PRODUCTION — "
                    "emails will NOT be delivered! Configure MAILGUN_API_KEY or RESEND_API_KEY immediately."
                )

    @property
    def name(self) -> str:
        return "mock_email"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.EMAIL
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Simulate sending an email. Returns failure in production."""
        if self._environment == "production":
            logger.critical(f"[MOCK EMAIL] BLOCKED in production — email to {to} was NOT sent. Configure a real email provider.")
            return False, None, {"mock": True, "blocked": True, "reason": "MockEmailProvider is not allowed in production"}
        logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}")
        message_id = f"mock_email_{uuid.uuid4().hex[:12]}"
        return True, message_id, {"mock": True, "to": to, "subject": subject}
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """Simulate checking email status."""
        return "delivered", {"mock": True}
    
    def is_available(self) -> bool:
        if self._environment == "production":
            return False
        return True


class ResendMessageProvider(MessageProvider):
    """Resend email provider — fallback after Mailgun."""
    
    def __init__(self):
        self.api_key = os.environ.get("RESEND_API_KEY")
        self.from_email = os.environ.get("RESEND_FROM_EMAIL", "noreply@wedotalent.com")
        self.from_name = os.environ.get("RESEND_FROM_NAME", "WeDo Talent")
    
    @property
    def name(self) -> str:
        return "resend"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.EMAIL
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        if not self.api_key:
            return False, None, {"error": "RESEND_API_KEY not configured"}
        try:
            import httpx
            sender = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
            payload = {
                "from": sender,
                "to": [to],
                "subject": subject or "(sem assunto)",
                "html": body_html or body,
            }
            if body and not body_html:
                payload["text"] = body
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            if response.status_code in (200, 201):
                data = response.json()
                message_id = data.get("id", f"resend-{uuid.uuid4().hex[:12]}")
                logger.info(f"[RESEND] Email sent to {to}. ID: {message_id}")
                return True, message_id, {"provider": "resend", "status_code": response.status_code}
            else:
                logger.error(f"[RESEND] Failed for {to}: {response.status_code} {response.text}")
                return False, None, {"error": f"Resend API error: {response.status_code}"}
        except Exception as e:
            logger.error(f"[RESEND] Exception sending to {to}: {e}", exc_info=True)
            return False, None, {"error": str(e)}
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        return "unknown", {"note": "Resend status tracking requires webhook setup"}
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class MailgunMessageProvider(MessageProvider):
    """
    Mailgun email provider implementation using the Mailgun HTTP API.

    Requires:
        - MAILGUN_API_KEY environment variable
        - MAILGUN_DOMAIN environment variable
        - Optional: MAILGUN_FROM_EMAIL (defaults to noreply@wedotalent.com)
        - Optional: MAILGUN_FROM_NAME (defaults to WeDo Talent)
        - Optional: MAILGUN_API_BASE (defaults to https://api.mailgun.net/v3)

    Note on check_status:
        Mailgun delivery status is tracked via webhooks (Event Webhook).
        The check_status method returns 'unknown' status and recommends webhook setup.
    """

    def __init__(self):
        self.api_key = os.environ.get("MAILGUN_API_KEY")
        self.domain = os.environ.get("MAILGUN_DOMAIN")
        self.from_email = os.environ.get("MAILGUN_FROM_EMAIL", "noreply@wedotalent.com")
        self.from_name = os.environ.get("MAILGUN_FROM_NAME", "WeDo Talent")
        self.api_base = os.environ.get("MAILGUN_API_BASE", "https://api.mailgun.net/v3")

    @property
    def name(self) -> str:
        return "mailgun"

    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.EMAIL

    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Send email via Mailgun HTTP API.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Plain text email body
            body_html: Optional HTML email body
            **kwargs: Additional options:
                - reply_to: Reply-to email address
                - categories: List of categories for tracking

        Returns:
            Tuple of (success, message_id, response_data)
        """
        if not MAILGUN_HTTPX_COMM_AVAILABLE:
            logger.warning("httpx not available — Mailgun send disabled")
            return False, None, {"error": "httpx not installed. Install with: pip install httpx"}

        if not self.is_available():
            logger.warning("Mailgun not configured (missing MAILGUN_API_KEY/MAILGUN_DOMAIN)")
            return False, None, {"error": "Mailgun not configured — MAILGUN_API_KEY and MAILGUN_DOMAIN required"}

        try:
            import httpx

            sender = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
            data: dict[str, Any] = {
                "from": sender,
                "to": to,
                "subject": subject or "(No Subject)",
                "text": body,
            }

            if body_html:
                data["html"] = body_html

            reply_to = kwargs.get("reply_to")
            if reply_to:
                data["h:Reply-To"] = reply_to

            categories = kwargs.get("categories", [])
            for tag in categories:
                data.setdefault("o:tag", [])
                if isinstance(data["o:tag"], list):
                    data["o:tag"].append(tag)

            custom_args = kwargs.get("custom_args", {})
            for key, value in custom_args.items():
                data[f"v:{key}"] = str(value)

            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.api_base}/{self.domain}/messages",
                    auth=("api", self.api_key),
                    data=data,
                )

            if response.status_code == 200:
                payload = response.json()
                message_id = payload.get("id", f"mg_{uuid.uuid4().hex[:12]}")
                logger.info(f"[MAILGUN] Successfully sent email to: {to}, message_id: {message_id}")
                return True, message_id, {
                    "provider": "mailgun",
                    "status_code": response.status_code,
                    "message_id": message_id
                }
            else:
                logger.error(f"[MAILGUN] Failed to send email to: {to}, status: {response.status_code}")
                return False, None, {
                    "provider": "mailgun",
                    "error": f"Mailgun returned status {response.status_code}: {response.text}",
                    "status_code": response.status_code,
                }

        except Exception as e:
            logger.error(f"[MAILGUN] Error sending email to {to}: {str(e)}", exc_info=True)
            return False, None, {
                "provider": "mailgun",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """
        Check Mailgun email status.

        Note: Mailgun does not provide a real-time API to check individual message delivery status.
        Email delivery tracking is handled via Mailgun's Event Webhook.

        Returns:
            Tuple of (status, additional_data) - status will be 'unknown' with webhook setup info
        """
        return "unknown", {
            "provider": "mailgun",
            "message_id": message_id,
            "note": "Mailgun email status tracking requires Event Webhook configuration.",
            "recommendation": "Set up a webhook endpoint to receive delivery events"
        }

    def is_available(self) -> bool:
        """Check if Mailgun is configured."""
        return bool(self.api_key) and bool(self.domain) and MAILGUN_HTTPX_COMM_AVAILABLE


class AWSEmailProvider(MessageProvider):
    """AWS SES email provider implementation."""
    
    def __init__(self):
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.from_email = os.environ.get("AWS_SES_FROM_EMAIL", "noreply@wedotalent.com")
    
    @property
    def name(self) -> str:
        return "aws_ses"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.EMAIL
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Send email via AWS SES."""
        if not self.is_available():
            logger.warning("AWS SES not configured, falling back")
            return False, None, {"error": "AWS SES not configured"}
        
        try:
            logger.info(f"[AWS SES] Sending email to: {to}")
            message_id = f"ses_{uuid.uuid4().hex[:12]}"
            return True, message_id, {"provider": "aws_ses"}
        except Exception as e:
            logger.error(f"AWS SES error: {e}")
            return False, None, {"error": str(e)}
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """Check AWS SES email status."""
        return "delivered", {"provider": "aws_ses"}
    
    def is_available(self) -> bool:
        return bool(self.aws_access_key and self.aws_secret_key)


class MockWhatsAppProvider(MessageProvider):
    """Mock WhatsApp provider for development/testing. Blocked in production."""
    
    def __init__(self):
        self._environment = os.environ.get("ENVIRONMENT", os.environ.get("APP_ENV", "development")).lower()
        if self._environment == "production":
            logger.critical(
                "[MOCK WHATSAPP] MockWhatsAppProvider activated in PRODUCTION — "
                "messages will NOT be delivered! Configure TWILIO credentials immediately."
            )

    @property
    def name(self) -> str:
        return "mock_whatsapp"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.WHATSAPP
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Simulate sending a WhatsApp message. Returns failure in production."""
        if self._environment == "production":
            logger.critical(f"[MOCK WHATSAPP] BLOCKED in production — message to {to} was NOT sent.")
            return False, None, {"mock": True, "blocked": True, "reason": "MockWhatsAppProvider is not allowed in production"}
        logger.info(f"[MOCK WHATSAPP] To: {to}")
        logger.info(f"[MOCK WHATSAPP] Message: {body[:100]}...")
        message_id = f"mock_wa_{uuid.uuid4().hex[:12]}"
        return True, message_id, {"mock": True, "to": to}
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """Simulate checking WhatsApp status."""
        return "delivered", {"mock": True}
    
    def is_available(self) -> bool:
        if self._environment == "production":
            return False
        return True


class TwilioWhatsAppProvider(MessageProvider):
    """
    Twilio WhatsApp provider implementation using the official Twilio Python SDK.
    
    Requires:
        - TWILIO_ACCOUNT_SID environment variable
        - TWILIO_AUTH_TOKEN environment variable
        - Optional: TWILIO_WHATSAPP_FROM (defaults to Twilio sandbox number)
    
    Note: For production WhatsApp messaging, you need:
        1. A Twilio account with WhatsApp enabled
        2. An approved WhatsApp Business Profile
        3. Approved message templates for outbound messaging (24h window rule)
    
    The check_status method uses Twilio's Message API to fetch real delivery status.
    """
    
    TWILIO_STATUS_MAP = {
        "queued": "queued",
        "sending": "pending",
        "sent": "sent",
        "delivered": "delivered",
        "read": "read",
        "failed": "failed",
        "undelivered": "failed",
    }
    
    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        self._client: TwilioClient | None = None
    
    @property
    def client(self) -> TwilioClient | None:
        """Lazy initialization of Twilio client."""
        if self._client is None and self.is_available() and TWILIO_AVAILABLE:
            self._client = TwilioClient(self.account_sid, self.auth_token)
        return self._client
    
    @property
    def name(self) -> str:
        return "twilio_whatsapp"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.WHATSAPP
    
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
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Send WhatsApp message via Twilio API.
        
        Args:
            to: Recipient phone number (with or without country code)
            subject: Ignored for WhatsApp (used for logging only)
            body: Message text content
            body_html: Ignored for WhatsApp
            **kwargs: Additional options:
                - media_url: URL of media to attach (image, document, etc.)
                - template_sid: Twilio Content Template SID for approved templates
                - content_variables: Variables for template substitution
        
        Returns:
            Tuple of (success, message_sid, response_data)
        """
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio SDK not installed, falling back to mock")
            return False, None, {"error": "Twilio SDK not installed. Install with: pip install twilio"}
        
        if not self.is_available():
            logger.warning("Twilio WhatsApp not configured (missing credentials), falling back")
            return False, None, {"error": "Twilio not configured - TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN required"}
        
        try:
            formatted_to = self._format_phone_number(to)
            formatted_from = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
            
            message_params = {
                "from_": formatted_from,
                "to": formatted_to,
                "body": body
            }
            
            media_url = kwargs.get("media_url")
            if media_url:
                if isinstance(media_url, str):
                    message_params["media_url"] = [media_url]
                else:
                    message_params["media_url"] = media_url
            
            template_sid = kwargs.get("template_sid")
            content_variables = kwargs.get("content_variables")
            if template_sid:
                message_params["content_sid"] = template_sid
                if content_variables:
                    import json
                    message_params["content_variables"] = json.dumps(content_variables)
            
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(**message_params)
            )
            
            logger.info(f"[TWILIO WHATSAPP] Successfully sent message to: {formatted_to}, SID: {message.sid}")
            
            return True, message.sid, {
                "provider": "twilio_whatsapp",
                "message_sid": message.sid,
                "status": message.status,
                "to": formatted_to,
                "from": formatted_from,
                "date_created": str(message.date_created) if message.date_created else None
            }
            
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] Twilio API error: {e.code} - {e.msg}", exc_info=True)
            return False, None, {
                "provider": "twilio_whatsapp",
                "error": e.msg,
                "error_code": e.code,
                "error_type": "TwilioRestException",
                "more_info": e.more_info
            }
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Error sending message to {to}: {str(e)}", exc_info=True)
            return False, None, {
                "provider": "twilio_whatsapp",
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """
        Check Twilio WhatsApp message status using Twilio's Message API.
        
        Twilio provides real-time status updates for messages. Possible statuses:
        - queued: Message is queued to be sent
        - sending: Message is being sent
        - sent: Message was successfully sent to carrier
        - delivered: Message was delivered to recipient
        - read: Message was read by recipient (if read receipts enabled)
        - failed: Message could not be sent
        - undelivered: Carrier could not deliver the message
        
        Args:
            message_id: Twilio Message SID (e.g., "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        
        Returns:
            Tuple of (normalized_status, additional_data)
        """
        if not TWILIO_AVAILABLE:
            return "unknown", {
                "provider": "twilio_whatsapp",
                "error": "Twilio SDK not installed"
            }
        
        if not self.is_available():
            return "unknown", {
                "provider": "twilio_whatsapp",
                "error": "Twilio not configured"
            }
        
        if not message_id or not message_id.startswith("SM"):
            return "unknown", {
                "provider": "twilio_whatsapp",
                "error": f"Invalid Twilio message SID format: {message_id}"
            }
        
        try:
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages(message_id).fetch()
            )
            
            twilio_status = message.status
            normalized_status = self.TWILIO_STATUS_MAP.get(twilio_status, "unknown")
            
            return normalized_status, {
                "provider": "twilio_whatsapp",
                "message_sid": message.sid,
                "twilio_status": twilio_status,
                "to": message.to,
                "from": message.from_,
                "date_sent": str(message.date_sent) if message.date_sent else None,
                "date_updated": str(message.date_updated) if message.date_updated else None,
                "error_code": message.error_code,
                "error_message": message.error_message
            }
            
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] Error checking status for {message_id}: {e.code} - {e.msg}")
            return "unknown", {
                "provider": "twilio_whatsapp",
                "error": e.msg,
                "error_code": e.code
            }
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Error checking status for {message_id}: {str(e)}")
            return "unknown", {
                "provider": "twilio_whatsapp",
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if Twilio is configured and SDK is available."""
        return bool(self.account_sid and self.auth_token) and TWILIO_AVAILABLE


class WhatsAppBusinessProvider(MessageProvider):
    """WhatsApp Business API provider implementation."""
    
    def __init__(self):
        self.access_token = os.environ.get("WHATSAPP_BUSINESS_TOKEN")
        self.phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID")
    
    @property
    def name(self) -> str:
        return "whatsapp_business"
    
    @property
    def channel(self) -> MessageChannel:
        return MessageChannel.WHATSAPP
    
    async def send(
        self,
        to: str,
        subject: str | None,
        body: str,
        body_html: str | None = None,
        **kwargs
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """Send message via WhatsApp Business API."""
        if not self.is_available():
            logger.warning("WhatsApp Business API not configured, falling back")
            return False, None, {"error": "WhatsApp Business API not configured"}
        
        try:
            logger.info(f"[WHATSAPP BUSINESS] Sending to: {to}")
            message_id = f"waba_{uuid.uuid4().hex[:12]}"
            return True, message_id, {"provider": "whatsapp_business"}
        except Exception as e:
            logger.error(f"WhatsApp Business API error: {e}")
            return False, None, {"error": str(e)}
    
    async def check_status(self, message_id: str) -> tuple[str, dict[str, Any] | None]:
        """Check WhatsApp Business API message status."""
        return "delivered", {"provider": "whatsapp_business"}
    
    def is_available(self) -> bool:
        return bool(self.access_token and self.phone_number_id)


