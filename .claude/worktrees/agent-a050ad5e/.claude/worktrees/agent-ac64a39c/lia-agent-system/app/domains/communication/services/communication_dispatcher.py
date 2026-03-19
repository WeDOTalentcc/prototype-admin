"""
Communication Dispatcher Service - Low-level API wrappers for SendGrid and Twilio.

This service provides direct access to email and messaging APIs with:
- Graceful fallback when API keys are not configured (mock success for development)
- Comprehensive logging of all attempts
- Consistent return format with success/error status and message_id
"""
import os
import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime

from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, ReplyTo
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    SendGridAPIClient = None

try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception

logger = logging.getLogger(__name__)


class CommunicationDispatcher:
    """
    Low-level dispatcher for sending emails via SendGrid and SMS/WhatsApp via Twilio.
    
    Each method checks for API key availability and returns mock success in development
    when keys are not configured.
    """
    
    def __init__(self):
        self._sendgrid_client: Optional[SendGridAPIClient] = None
        self._twilio_client: Optional[TwilioClient] = None
        self._initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of API clients."""
        if self._initialized:
            return
        
        sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_api_key and SENDGRID_AVAILABLE:
            try:
                self._sendgrid_client = SendGridAPIClient(api_key=sendgrid_api_key)
                logger.info("SendGrid client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid client: {e}")
        
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if twilio_account_sid and twilio_auth_token and TWILIO_AVAILABLE:
            try:
                self._twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio client: {e}")
        
        self._initialized = True
    
    @property
    def is_sendgrid_enabled(self) -> bool:
        """Check if SendGrid is configured and available."""
        self._ensure_initialized()
        return self._sendgrid_client is not None
    
    @property
    def is_twilio_enabled(self) -> bool:
        """Check if Twilio is configured and available."""
        self._ensure_initialized()
        return self._twilio_client is not None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML content of the email
            body_text: Plain text fallback (optional)
            from_name: Sender display name (optional)
            reply_to: Reply-to email address (optional)
        
        Returns:
            Dict with keys:
                - success: bool
                - message_id: str (if successful or mock)
                - error: str (if failed)
                - mock: bool (true if mock response for development)
        """
        self._ensure_initialized()
        
        from_email_address = os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com")
        default_from_name = os.getenv("SENDGRID_FROM_NAME", "LIA Recruitment")
        sender_name = from_name or default_from_name
        
        logger.info(f"Attempting to send email to {to_email} with subject: {subject[:50]}...")
        
        if not self.is_sendgrid_enabled:
            mock_id = f"mock-email-{uuid.uuid4().hex[:12]}"
            logger.warning(f"SendGrid not configured. Returning mock success for email to {to_email}")
            return {
                "success": True,
                "message_id": mock_id,
                "mock": True,
                "channel": "email",
                "recipient": to_email,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            from_email = Email(from_email_address, sender_name)
            to = To(to_email)
            
            message = Mail(
                from_email=from_email,
                to_emails=to,
                subject=subject,
                html_content=body_html
            )
            
            if body_text:
                message.add_content(Content("text/plain", body_text))
            
            if reply_to:
                message.reply_to = ReplyTo(reply_to)
            
            response = self._sendgrid_client.send(message)
            message_id = response.headers.get("X-Message-Id", f"sg-{uuid.uuid4().hex[:12]}")
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {message_id}, Status: {response.status_code}")
            
            return {
                "success": True,
                "message_id": message_id,
                "mock": False,
                "channel": "email",
                "recipient": to_email,
                "status_code": response.status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "mock": False,
                "channel": "email",
                "recipient": to_email,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        template_sid: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message via Twilio.
        
        Args:
            to_phone: Recipient phone number (with country code, e.g., +5511999999999)
            message: Message content
            template_sid: Optional WhatsApp template SID for pre-approved templates
        
        Returns:
            Dict with keys:
                - success: bool
                - message_id: str (Twilio SID if successful)
                - error: str (if failed)
                - mock: bool (true if mock response for development)
        """
        self._ensure_initialized()
        
        from_whatsapp = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
        
        if not to_phone.startswith("whatsapp:"):
            to_whatsapp = f"whatsapp:{to_phone}"
        else:
            to_whatsapp = to_phone
        
        logger.info(f"Attempting to send WhatsApp message to {to_phone}...")
        
        if not self.is_twilio_enabled:
            mock_id = f"mock-whatsapp-{uuid.uuid4().hex[:12]}"
            logger.warning(f"Twilio not configured. Returning mock success for WhatsApp to {to_phone}")
            return {
                "success": True,
                "message_id": mock_id,
                "mock": True,
                "channel": "whatsapp",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            msg_params = {
                "body": message,
                "from_": from_whatsapp,
                "to": to_whatsapp
            }
            
            if template_sid:
                msg_params["content_sid"] = template_sid
            
            twilio_message = self._twilio_client.messages.create(**msg_params)
            
            logger.info(f"WhatsApp message sent successfully to {to_phone}. SID: {twilio_message.sid}")
            
            return {
                "success": True,
                "message_id": twilio_message.sid,
                "mock": False,
                "channel": "whatsapp",
                "recipient": to_phone,
                "status": twilio_message.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TwilioRestException as e:
            error_msg = f"Twilio error {e.code}: {e.msg}"
            logger.error(f"Failed to send WhatsApp to {to_phone}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_code": e.code,
                "mock": False,
                "channel": "whatsapp",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send WhatsApp to {to_phone}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "mock": False,
                "channel": "whatsapp",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_sms(
        self,
        to_phone: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send an SMS via Twilio.
        
        Args:
            to_phone: Recipient phone number (with country code, e.g., +5511999999999)
            message: SMS message content (max 1600 characters, will be split automatically)
        
        Returns:
            Dict with keys:
                - success: bool
                - message_id: str (Twilio SID if successful)
                - error: str (if failed)
                - mock: bool (true if mock response for development)
        """
        self._ensure_initialized()
        
        from_sms = os.getenv("TWILIO_SMS_FROM", os.getenv("TWILIO_PHONE_NUMBER"))
        
        logger.info(f"Attempting to send SMS to {to_phone}...")
        
        if not self.is_twilio_enabled:
            mock_id = f"mock-sms-{uuid.uuid4().hex[:12]}"
            logger.warning(f"Twilio not configured. Returning mock success for SMS to {to_phone}")
            return {
                "success": True,
                "message_id": mock_id,
                "mock": True,
                "channel": "sms",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        if not from_sms:
            logger.error("TWILIO_SMS_FROM or TWILIO_PHONE_NUMBER not configured")
            return {
                "success": False,
                "error": "SMS sender phone number not configured (TWILIO_SMS_FROM or TWILIO_PHONE_NUMBER)",
                "mock": False,
                "channel": "sms",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            twilio_message = self._twilio_client.messages.create(
                body=message,
                from_=from_sms,
                to=to_phone
            )
            
            logger.info(f"SMS sent successfully to {to_phone}. SID: {twilio_message.sid}")
            
            return {
                "success": True,
                "message_id": twilio_message.sid,
                "mock": False,
                "channel": "sms",
                "recipient": to_phone,
                "status": twilio_message.status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except TwilioRestException as e:
            error_msg = f"Twilio error {e.code}: {e.msg}"
            logger.error(f"Failed to send SMS to {to_phone}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "error_code": e.code,
                "mock": False,
                "channel": "sms",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send SMS to {to_phone}: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "mock": False,
                "channel": "sms",
                "recipient": to_phone,
                "timestamp": datetime.utcnow().isoformat()
            }

    async def dispatch_message(
        self,
        company_id: str,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        subject: Optional[str] = None,
        message: str = "",
        channel: Optional[str] = None,
        candidate_name: Optional[str] = None,
        db=None,
        multi_channel: bool = True,
    ) -> Dict[str, Any]:
        """
        Smart dispatcher with multi-channel support.
        
        When multi_channel=True (default), sends to ALL available channels
        (email + WhatsApp) simultaneously. When False or when an explicit
        channel is specified, sends to that single channel only.
        
        Applies lia_tone to message content when available.
        """
        lia_tone = "professional"
        
        if company_id and db:
            try:
                policy = await get_policy_for_company(company_id, db)
                lia_tone = resolve_policy_value(
                    policy, "communication_rules", "lia_tone",
                    default="professional",
                )
            except Exception as e:
                logger.warning(f"Failed to load communication policy for {company_id}: {e}")
        
        formatted_message = self._apply_tone(message, lia_tone, candidate_name)

        if channel and not multi_channel:
            return await self._send_single_channel(
                channel=channel,
                recipient_email=recipient_email,
                recipient_phone=recipient_phone,
                subject=subject,
                formatted_message=formatted_message,
            )

        results = {}
        any_success = False

        if recipient_email:
            email_result = self.send_email(
                to_email=recipient_email,
                subject=subject or "Atualização do processo seletivo",
                body_html=f"<p>{formatted_message}</p>",
                body_text=formatted_message,
            )
            results["email"] = email_result
            if email_result.get("success"):
                any_success = True

        if recipient_phone:
            whatsapp_result = self.send_whatsapp(
                to_phone=recipient_phone,
                message=formatted_message,
            )
            results["whatsapp"] = whatsapp_result
            if whatsapp_result.get("success"):
                any_success = True

        if not results:
            return {"success": False, "error": "No recipient contact info provided", "channels": []}

        return {
            "success": any_success,
            "channels_sent": list(results.keys()),
            "results": results,
        }

    async def _send_single_channel(
        self,
        channel: str,
        recipient_email: Optional[str],
        recipient_phone: Optional[str],
        subject: Optional[str],
        formatted_message: str,
    ) -> Dict[str, Any]:
        if channel == "email" and recipient_email:
            return self.send_email(
                to_email=recipient_email,
                subject=subject or "Atualização do processo seletivo",
                body_html=f"<p>{formatted_message}</p>",
                body_text=formatted_message,
            )
        elif channel == "whatsapp" and recipient_phone:
            return self.send_whatsapp(
                to_phone=recipient_phone,
                message=formatted_message,
            )
        elif channel == "sms" and recipient_phone:
            return self.send_sms(
                to_phone=recipient_phone,
                message=formatted_message,
            )
        elif recipient_phone:
            return self.send_whatsapp(to_phone=recipient_phone, message=formatted_message)
        elif recipient_email:
            return self.send_email(
                to_email=recipient_email,
                subject=subject or "Atualização do processo seletivo",
                body_html=f"<p>{formatted_message}</p>",
                body_text=formatted_message,
            )
        return {"success": False, "error": "No recipient contact info provided", "channel": channel}
    
    def _apply_tone(
        self,
        message: str,
        tone: str,
        candidate_name: Optional[str] = None,
    ) -> str:
        """
        Apply lia_tone modifier to message content.
        
        Tones:
        - professional: Formal, Sr./Sra. treatment
        - friendly: Informal, first name
        - formal: Institutional, legal language
        """
        if not candidate_name:
            return message
        
        first_name = candidate_name.split()[0] if candidate_name else ""
        
        if tone == "friendly":
            greeting = f"Oi, {first_name}! "
        elif tone == "formal":
            greeting = f"Prezado(a) Sr(a). {candidate_name}, "
        else:
            greeting = f"Olá, {candidate_name}. "
        
        if not message.startswith(("Oi,", "Olá,", "Prezado", "Caro")):
            message = greeting + message
        
        return message
    
    async def get_communication_policy(
        self,
        company_id: str,
        db=None,
    ) -> Dict[str, Any]:
        """
        Get effective communication configuration for a company.
        """
        try:
            if db:
                policy = await get_policy_for_company(company_id, db)
                comm = policy.get("communication_rules", {})
                return {
                    "preferred_channel": comm.get("preferred_channel", "whatsapp"),
                    "lia_tone": comm.get("lia_tone", "professional"),
                    "auto_rejection_feedback": comm.get("auto_rejection_feedback", False),
                    "rejection_feedback_deadline_hours": comm.get("rejection_feedback_deadline_hours", 48),
                }
        except Exception as e:
            logger.warning(f"Failed to load communication policy: {e}")
        
        return {
            "preferred_channel": "whatsapp",
            "lia_tone": "professional",
            "auto_rejection_feedback": False,
            "rejection_feedback_deadline_hours": 48,
        }


communication_dispatcher = CommunicationDispatcher()
