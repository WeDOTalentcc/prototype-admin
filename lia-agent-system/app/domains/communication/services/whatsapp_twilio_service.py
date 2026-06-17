"""
Twilio WhatsApp Service

WhatsApp Business API integration using Twilio as the messaging provider.

Environment Variables Required:
- TWILIO_ACCOUNT_SID: Twilio Account SID
- TWILIO_AUTH_TOKEN: Twilio Auth Token
- TWILIO_WHATSAPP_NUMBER: Twilio WhatsApp sender number (format: whatsapp:+1234567890)

Interactive Buttons (Twilio Content API):
- TWILIO_TEMPLATE_TRIAGEM_SID: Content SID for screening invitation template
- TWILIO_TEMPLATE_ENTREVISTA_SID: Content SID for interview confirmation template
- TWILIO_TEMPLATE_FEEDBACK_SID: Content SID for feedback/result template
  When not set, falls back to numbered text options (legacy behaviour).
"""

import logging
import os
from datetime import datetime
from typing import Any

from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from app.domains.communication.services.whatsapp_provider import (
    IncomingMessage,
    ProviderType,
    SendResult,
    WhatsAppProvider,
)

logger = logging.getLogger(__name__)

TWILIO_INTERACTIVE_TEMPLATES: dict[str, str] = {
    "triagem": "TWILIO_TEMPLATE_TRIAGEM_SID",
    "entrevista": "TWILIO_TEMPLATE_ENTREVISTA_SID",
    "feedback": "TWILIO_TEMPLATE_FEEDBACK_SID",
}


class TwilioWhatsAppService(WhatsAppProvider):
    """
    Twilio WhatsApp Business API Service.

    Features:
    - Text messages
    - Native interactive buttons via Twilio Content API templates (when approved)
    - Automatic fallback to numbered text options when template not available
    - Document/media handling
    - Webhook verification and parsing

    Setup Requirements:
    1. Twilio Account with WhatsApp enabled
    2. WhatsApp Sender approved in Twilio Console
    3. Webhook URL configured in Twilio
    4. (Optional) Twilio Content API templates registered for interactive buttons
    """

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER") or os.getenv("TWILIO_VOICE_NUMBER")
        self.environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "production"))
        
        self._client: Client | None = None
        self._validator: RequestValidator | None = None
        
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
    def client(self) -> Client | None:
        """Get or create Twilio client."""
        if self._client is None and self.is_configured:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client
    
    @property
    def validator(self) -> RequestValidator | None:
        """Get or create Twilio request validator."""
        if self._validator is None and self.auth_token:
            self._validator = RequestValidator(self.auth_token)
        return self._validator
    
    def _format_whatsapp_number(self, phone: str) -> str:
        """Format phone number for Twilio WhatsApp API (whatsapp:+...)."""
        # ORCHESTRATOR-GHOST-EXEMPT: format_phone_number defined in WhatsAppProvider base
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
    
    def get_template_sid(self, template_name: str) -> str | None:
        """
        Return the Twilio Content API SID for a named interactive template.

        Template names: "triagem", "entrevista", "feedback".
        Returns None when the env-var is not set (triggers text fallback).
        """
        env_key = TWILIO_INTERACTIVE_TEMPLATES.get(template_name)
        if not env_key:
            return None
        return os.getenv(env_key) or None

    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header_text: str | None = None,
        footer_text: str | None = None,
        template_name: str | None = None,
        template_variables: dict[str, str] | None = None,
    ) -> SendResult:
        """
        Send an interactive message with buttons.

        When *template_name* is provided and the corresponding Twilio Content
        API template SID is configured (e.g. TWILIO_TEMPLATE_TRIAGEM_SID),
        the message is sent as a native WhatsApp interactive template with
        real quick-reply buttons.

        When the template SID is not available the method falls back to the
        numbered-text simulation for backwards compatibility.

        Args:
            to: Recipient phone number.
            body_text: Message body (used in fallback text mode).
            buttons: List of dicts with 'title' key (and optional 'id').
            header_text: Optional bold header text (fallback text mode).
            footer_text: Optional italic footer text (fallback text mode).
            template_name: Named template key ("triagem", "entrevista", "feedback").
            template_variables: Variables to inject into the Content template.
        """
        formatted_to = self._format_whatsapp_number(to)

        template_sid = self.get_template_sid(template_name) if template_name else None

        if template_sid and not (self.is_development or not self.is_configured):
            native_result = await self._send_native_interactive(
                formatted_to=formatted_to,
                template_sid=template_sid,
                template_variables=template_variables or {},
            )
            if native_result.success:
                return native_result
            logger.warning(
                f"[TWILIO WHATSAPP] Native template send failed "
                f"(template_sid={template_sid}, error={native_result.error}) "
                "— falling back to numbered-text mode"
            )

        return await self._send_interactive_text_fallback(
            formatted_to=formatted_to,
            body_text=body_text,
            buttons=buttons,
            header_text=header_text,
            footer_text=footer_text,
        )

    async def _send_native_interactive(
        self,
        formatted_to: str,
        template_sid: str,
        template_variables: dict[str, str],
    ) -> SendResult:
        """
        Send a native WhatsApp interactive message via Twilio Content API template.

        The Content SID must reference an approved WhatsApp template with
        quick-reply buttons registered in the Twilio Console.
        """
        try:
            content_variables_str = None
            if template_variables:
                import json
                content_variables_str = json.dumps(template_variables)

            create_kwargs: dict[str, Any] = {
                "from_": self.whatsapp_number,
                "to": formatted_to,
                "content_sid": template_sid,
            }
            if content_variables_str:
                create_kwargs["content_variables"] = content_variables_str

            message = self.client.messages.create(**create_kwargs)

            logger.info(
                f"[TWILIO WHATSAPP] Native interactive template sent to {formatted_to}: "
                f"{message.sid} (template_sid={template_sid})"
            )
            return SendResult(
                success=True,
                message_id=message.sid,
                sent_at=datetime.utcnow(),
                provider="twilio",
                metadata={
                    "status": message.status,
                    "to": formatted_to,
                    "template_sid": template_sid,
                    "mode": "native_interactive",
                },
            )
        except TwilioRestException as e:
            logger.warning(
                f"[TWILIO WHATSAPP] Native interactive failed (code={e.code}): {e.msg} "
                "— this may happen when the template is pending approval."
            )
            return SendResult(
                success=False,
                error=e.msg,
                error_code=str(e.code),
                provider="twilio",
                metadata={"template_sid": template_sid},
            )
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Native interactive error: {e}")
            return SendResult(success=False, error=str(e), provider="twilio")

    async def _send_interactive_text_fallback(
        self,
        formatted_to: str,
        body_text: str,
        buttons: list[dict[str, str]],
        header_text: str | None = None,
        footer_text: str | None = None,
    ) -> SendResult:
        """
        Send interactive buttons as numbered text options (fallback).

        This is the behaviour when no approved Twilio Content template is
        available. Numbers allow candidates to reply with the digit to select.
        """
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
            return await self._send_development(formatted_to, full_text, "interactive_text_fallback")

        try:
            message = self.client.messages.create(
                body=full_text,
                from_=self.whatsapp_number,
                to=formatted_to,
            )

            logger.info(f"[TWILIO WHATSAPP] Text-fallback interactive sent to {formatted_to}: {message.sid}")

            return SendResult(
                success=True,
                message_id=message.sid,
                sent_at=datetime.utcnow(),
                provider="twilio",
                metadata={
                    "response": {"sid": message.sid, "status": message.status},
                    "mode": "text_fallback",
                },
            )
        except TwilioRestException as e:
            logger.error(f"[TWILIO WHATSAPP] Interactive text fallback error: {e.code} - {e.msg}")
            return SendResult(
                success=False,
                error=e.msg,
                error_code=str(e.code),
                provider="twilio",
            )
        except Exception as e:
            logger.error(f"[TWILIO WHATSAPP] Interactive text fallback error: {e}")
            return SendResult(success=False, error=str(e), provider="twilio")

    async def send_screening_invitation(
        self,
        to: str,
        candidate_name: str,
        job_title: str,
        company_name: str,
        recruiter_name: str = "Equipe de Recrutamento",
    ) -> SendResult:
        """
        Send a WhatsApp screening invitation with native interactive buttons.

        Uses the "triagem" template when TWILIO_TEMPLATE_TRIAGEM_SID is set.
        Falls back to numbered text when template is not available.
        """
        buttons = [
            {"id": "sim", "title": "Sim, quero participar"},
            {"id": "nao", "title": "Não tenho interesse"},
            {"id": "mais_info", "title": "Quero mais informações"},
        ]
        body_text = (
            f"Olá {candidate_name}! 👋\n\n"
            f"Sou {recruiter_name} da {company_name}.\n\n"
            f"Temos uma oportunidade para *{job_title}* e seu perfil chamou nossa atenção! 🎯\n\n"
            f"Gostaria de participar de uma triagem rápida via WhatsApp?"
        )
        footer_text = "Responda com o número da opção desejada"

        template_variables = {
            "1": candidate_name,
            "2": recruiter_name,
            "3": company_name,
            "4": job_title,
        }

        return await self.send_interactive_buttons(
            to=to,
            body_text=body_text,
            buttons=buttons,
            footer_text=footer_text,
            template_name="triagem",
            template_variables=template_variables,
        )

    async def send_interview_confirmation_request(
        self,
        to: str,
        candidate_name: str,
        job_title: str,
        interview_date: str,
        interview_time: str,
        interview_location: str,
    ) -> SendResult:
        """
        Send an interview confirmation request with native interactive buttons.

        Uses the "entrevista" template when TWILIO_TEMPLATE_ENTREVISTA_SID is set.
        Falls back to numbered text when template is not available.
        """
        buttons = [
            {"id": "confirmar", "title": "Confirmar presença"},
            {"id": "reagendar", "title": "Reagendar"},
            {"id": "cancelar", "title": "Cancelar"},
        ]
        body_text = (
            f"Olá {candidate_name}! 📅\n\n"
            f"Confirmação da sua entrevista para *{job_title}*:\n\n"
            f"📅 Data: {interview_date}\n"
            f"🕐 Horário: {interview_time}\n"
            f"📍 Local: {interview_location}\n\n"
            f"Por favor, confirme sua presença:"
        )
        footer_text = "Responda com o número da opção desejada"

        template_variables = {
            "1": candidate_name,
            "2": job_title,
            "3": interview_date,
            "4": interview_time,
            "5": interview_location,
        }

        return await self.send_interactive_buttons(
            to=to,
            body_text=body_text,
            buttons=buttons,
            footer_text=footer_text,
            template_name="entrevista",
            template_variables=template_variables,
        )

    async def send_feedback_result(
        self,
        to: str,
        candidate_name: str,
        job_title: str,
        result: str,
        feedback_message: str = "",
    ) -> SendResult:
        """
        Send screening/interview feedback with native interactive buttons.

        Uses the "feedback" template when TWILIO_TEMPLATE_FEEDBACK_SID is set.
        Falls back to numbered text when template is not available.
        """
        buttons = [
            {"id": "ver_resultado", "title": "Ver resultado completo"},
            {"id": "falar_recrutador", "title": "Falar com recrutador"},
        ]
        result_emoji = "✅" if result.lower() in ("aprovado", "approved", "pass") else "📋"
        body_text = (
            f"Olá {candidate_name}! {result_emoji}\n\n"
            f"Temos uma atualização sobre sua candidatura para *{job_title}*.\n\n"
            f"Resultado: *{result}*\n"
        )
        if feedback_message:
            body_text += f"\n{feedback_message}\n"

        template_variables = {
            "1": candidate_name,
            "2": job_title,
            "3": result,
            "4": feedback_message[:200] if feedback_message else "",
        }

        return await self.send_interactive_buttons(
            to=to,
            body_text=body_text,
            buttons=buttons,
            template_name="feedback",
            template_variables=template_variables,
        )
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        caption: str | None = None,
        filename: str | None = None
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
    
    def parse_webhook_message(self, payload: dict[str, Any]) -> IncomingMessage | None:
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
    
    async def download_media(self, media_url: str) -> dict[str, Any]:
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
