"""
Communication Dispatcher Service - Low-level API wrappers for Mailgun and Twilio.

This service provides direct access to email and messaging APIs with:
- Graceful fallback when API keys are not configured (mock success for development)
- Comprehensive logging of all attempts
- Consistent return format with success/error status and message_id
"""
import logging
import os
import uuid
from datetime import datetime
from typing import Any

from app.shared.policy_middleware import get_policy_for_company, resolve_policy_value
from app.domains.persona.services.ai_persona_validator import (  # P1-6 sensor: tone normalization
    TONE_PT_TO_EN_LEGACY,
)

try:
    import httpx as _httpx
    MAILGUN_HTTPX_AVAILABLE = True
except ImportError:
    MAILGUN_HTTPX_AVAILABLE = False
    _httpx = None  # type: ignore[assignment]

try:
    from twilio.base.exceptions import TwilioRestException
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception

logger = logging.getLogger(__name__)


class CommunicationDispatcher:
    """
    Low-level dispatcher for sending emails via Mailgun and SMS/WhatsApp via Twilio.

    Each method checks for API key availability and returns mock success in development
    when keys are not configured.
    """

    def __init__(self):
        self._twilio_client: TwilioClient | None = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of API clients."""
        if self._initialized:
            return

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
    def is_mailgun_enabled(self) -> bool:
        """Check if Mailgun is configured and available."""
        return bool(
            os.getenv("MAILGUN_API_KEY")
            and os.getenv("MAILGUN_DOMAIN")
            and MAILGUN_HTTPX_AVAILABLE
        )

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
        body_text: str | None = None,
        from_name: str | None = None,
        reply_to: str | None = None
    ) -> dict[str, Any]:
        """
        Send an email via Mailgun with automatic Resend fallback.

        Attempts Mailgun first. If the MAILGUN_CIRCUIT is open, Mailgun is not
        configured, or Mailgun returns a failure, automatically retries via Resend
        (when RESEND_API_KEY is set and RESEND_CIRCUIT is closed).

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
                - provider: str (mailgun|resend|mock)
        """
        from app.shared.resilience.circuit_breaker import (
            MAILGUN_CIRCUIT,
            RESEND_CIRCUIT,
            CircuitState,
        )

        from_email_address = os.getenv("MAILGUN_FROM_EMAIL", "noreply@wedotalent.com")
        default_from_name = os.getenv("MAILGUN_FROM_NAME", "LIA Recruitment")
        sender_name = from_name or default_from_name
        sender = f"{sender_name} <{from_email_address}>" if sender_name else from_email_address

        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Attempting to send email to {to_email} with subject: {subject[:50]}...")

        mailgun_circuit_open = MAILGUN_CIRCUIT.state == CircuitState.OPEN
        mailgun_skip = not self.is_mailgun_enabled or mailgun_circuit_open

        if mailgun_circuit_open:
            logger.warning("[DISPATCHER] MAILGUN_CIRCUIT is OPEN — routing to Resend fallback")

        mailgun_error: str | None = None

        if not mailgun_skip:
            api_key = os.getenv("MAILGUN_API_KEY", "")
            domain = os.getenv("MAILGUN_DOMAIN", "")
            api_base = os.getenv("MAILGUN_API_BASE", "https://api.mailgun.net/v3")

            data: dict[str, Any] = {
                "from": sender,
                "to": to_email,
                "subject": subject,
                "html": body_html,
            }
            if body_text:
                data["text"] = body_text
            if reply_to:
                data["h:Reply-To"] = reply_to

            # GAP-07-002: CAN-SPAM / Gmail deliverability compliance headers
            _base_url = os.getenv("APP_BASE_URL", "https://app.wedotalent.cc").rstrip("/")
            data["h:List-Unsubscribe"] = (
                f"<{_base_url}/api/v1/communication/unsubscribe>, "
                f"<mailto:unsubscribe@wedotalent.cc?subject=Unsubscribe>"
            )
            data["h:List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
            data["h:DMARC-Policy"] = "v=DMARC1; p=quarantine; rua=mailto:dmarc@wedotalent.cc"
            data["h:X-Mailer"] = "WeDOTalent/LIA"

            try:
                import httpx
                with httpx.Client(timeout=30) as client:
                    response = client.post(
                        f"{api_base}/{domain}/messages",
                        auth=("api", api_key),
                        data=data,
                    )

                if response.status_code == 200:
                    payload = response.json()
                    message_id = payload.get("id", f"mg-{uuid.uuid4().hex[:12]}")
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.info(f"[MAILGUN] Email sent to {to_email}. ID: {message_id}")
                    return {
                        "success": True,
                        "message_id": message_id,
                        "mock": False,
                        "provider": "mailgun",
                        "channel": "email",
                        "recipient": to_email,
                        "status_code": response.status_code,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    mailgun_error = f"status {response.status_code}: {response.text}"
                    logger.error(
                        f"[MAILGUN] Failed for {to_email}: {mailgun_error} — trying Resend fallback"
                    )

            except Exception as e:
                mailgun_error = str(e)
                logger.error(
                    f"[MAILGUN] Exception for {to_email}: {mailgun_error} — trying Resend fallback",
                    exc_info=True
                )

        resend_circuit_open = RESEND_CIRCUIT.state == CircuitState.OPEN
        resend_api_key = os.getenv("RESEND_API_KEY")

        if resend_api_key and not resend_circuit_open:
            resend_result = self._send_via_resend(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                from_name=sender_name,
                from_email=from_email_address,
                reply_to=reply_to,
                resend_api_key=resend_api_key,
            )
            if resend_result.get("success"):
                return resend_result
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"[RESEND FALLBACK] Also failed for {to_email}: {resend_result.get('error')}")

        elif resend_circuit_open:
            logger.warning("[DISPATCHER] RESEND_CIRCUIT is OPEN — both providers unavailable")
        elif not resend_api_key:
            if not mailgun_skip:
                logger.warning("[DISPATCHER] RESEND_API_KEY not set — no fallback available")

        if not self.is_mailgun_enabled and not resend_api_key:
            environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
            if environment == "production":
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.critical(f"[DISPATCHER] No email provider configured in PRODUCTION — email to {to_email} was NOT sent!")
                return {
                    "success": False,
                    "error": "No email provider configured in production",
                    "mock": False,
                    "provider": "none",
                    "channel": "email",
                    "recipient": to_email,
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_id = f"mock-email-{uuid.uuid4().hex[:12]}"
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.warning(f"No email provider configured. Returning mock for {to_email}")
            return {
                "success": True,
                "message_id": mock_id,
                "mock": True,
                "provider": "mock",
                "channel": "email",
                "recipient": to_email,
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "success": False,
            "error": mailgun_error or "All email providers failed or unavailable",
            "mock": False,
            "provider": "none",
            "channel": "email",
            "recipient": to_email,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _send_via_resend(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        resend_api_key: str,
        body_text: str | None = None,
        from_name: str | None = None,
        from_email: str | None = None,
        reply_to: str | None = None,
    ) -> dict[str, Any]:
        """Send email via Resend as fallback provider."""
        try:
            import resend as resend_sdk
        except ImportError:
            return {
                "success": False,
                "error": "Resend SDK not installed",
                "provider": "resend",
                "mock": False
            }

        try:
            resend_sdk.api_key = resend_api_key
            resend_from_email = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
            resend_from_name = from_name or os.getenv("RESEND_FROM_NAME", "LIA Recruitment")
            resend_sender = (
                f"{resend_from_name} <{resend_from_email}>" if resend_from_name else resend_from_email
            )

            params: dict[str, Any] = {
                "from": resend_sender,
                "to": [to_email],
                "subject": subject,
                "html": body_html,
            }
            if body_text:
                params["text"] = body_text
            if reply_to:
                params["reply_to"] = reply_to

            response = resend_sdk.Emails.send(params)

            if response and response.get("id"):
                msg_id = response["id"]
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.info(f"[RESEND FALLBACK] Email sent to {to_email}. ID: {msg_id}")
                return {
                    "success": True,
                    "message_id": msg_id,
                    "mock": False,
                    "provider": "resend",
                    "channel": "email",
                    "recipient": to_email,
                    "fallback": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            return {
                "success": False,
                "error": f"Unexpected Resend response: {response}",
                "provider": "resend",
                "mock": False
            }
        except Exception as exc:
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
            logger.error(f"[RESEND FALLBACK] Exception for {to_email}: {exc}", exc_info=True)
            return {
                "success": False,
                "error": str(exc),
                "provider": "resend",
                "mock": False
            }
    
    def send_whatsapp(
        self,
        to_phone: str,
        message: str,
        template_sid: str | None = None
    ) -> dict[str, Any]:
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
        
        _twilio_phone = os.getenv("TWILIO_PHONE_NUMBER", "")
        from_whatsapp = (
            os.getenv("TWILIO_WHATSAPP_FROM")
            or (f"whatsapp:{_twilio_phone}" if _twilio_phone else "whatsapp:+14155238886")
        )
        
        if not to_phone.startswith("whatsapp:"):
            to_whatsapp = f"whatsapp:{to_phone}"
        else:
            to_whatsapp = to_phone
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Attempting to send WhatsApp message to {to_phone}...")
        
        if not self.is_twilio_enabled:
            environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
            if environment == "production":
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.critical(f"[DISPATCHER] Twilio not configured in PRODUCTION — WhatsApp to {to_phone} was NOT sent!")
                return {
                    "success": False,
                    "error": "Twilio not configured in production",
                    "mock": False,
                    "channel": "whatsapp",
                    "recipient": to_phone,
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_id = f"mock-whatsapp-{uuid.uuid4().hex[:12]}"
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
    ) -> dict[str, Any]:
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
        
        # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
        logger.info(f"Attempting to send SMS to {to_phone}...")
        
        if not self.is_twilio_enabled:
            environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
            if environment == "production":
                # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                logger.critical(f"[DISPATCHER] Twilio not configured in PRODUCTION — SMS to {to_phone} was NOT sent!")
                return {
                    "success": False,
                    "error": "Twilio not configured in production",
                    "mock": False,
                    "channel": "sms",
                    "recipient": to_phone,
                    "timestamp": datetime.utcnow().isoformat()
                }
            mock_id = f"mock-sms-{uuid.uuid4().hex[:12]}"
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
            # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
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
        recipient_email: str | None = None,
        recipient_phone: str | None = None,
        subject: str | None = None,
        message: str = "",
        channel: str | None = None,
        candidate_name: str | None = None,
        db=None,
        multi_channel: bool = True,
    ) -> dict[str, Any]:
        """
        Smart dispatcher with multi-channel support.
        
        When multi_channel=True (default), sends to ALL available channels
        (email + WhatsApp) simultaneously. When False or when an explicit
        channel is specified, sends to that single channel only.
        
        Applies lia_tone to message content when available.

        P1-5 scope clarification (audit 2026-05-21):
        ``lia_tone`` controls ONLY outbound message wording (email + WhatsApp
        bodies dispatched to candidates). It does NOT modify the LIA chat
        system prompt — that is owned by ``lia_persona.yaml`` (base) and
        ``tenant_overrides/shared/lia_persona.yaml`` (per-tenant override),
        both consumed by :class:`SystemPromptBuilder`. The two surfaces are
        independent on purpose: ``lia_tone`` is a quick formality knob the
        recruiter flips in Configurações; the persona override is a deeper
        re-write of how the LIA introduces herself in chat. See CLAUDE.md
        section "lia_tone canonical precedence" for the canonical reasoning.
        """
        lia_tone = "professional"

        if company_id and db:
            try:
                policy = await get_policy_for_company(company_id, db)
                lia_tone = resolve_policy_value(
                    policy, "communication_rules", "lia_tone",
                    default="professional",
                )
                # P1-6 sensor (audit 2026-05-26): detecta divergencia entre
                # lia_tone (outbound, configurado em Politicas) e ai_persona.tone
                # (chat persona E2, configurado em Recrutamento & LIA > Instrucoes LIA).
                # Ambos vivem em communication_rules JSONB mas em chaves diferentes
                # com superficies UI distintas — divergencia = silent inconsistency
                # que o recrutador nao ve. Log warn (nao bloqueia dispatch).
                # CLAUDE.md "lia_tone canonical precedence" documenta a separacao.
                ai_persona_data = resolve_policy_value(
                    policy, "communication_rules", "ai_persona",
                    default=None,
                )
                if isinstance(ai_persona_data, dict):
                    persona_tone = ai_persona_data.get("tone")
                    if persona_tone:
                        # Normalize PT-BR ai_persona.tone to EN before comparing with
                        # legacy lia_tone (EN). Without normalization "profissional" ≠
                        # "professional" fires a false positive even when tones are synced.
                        # TONE_PT_TO_EN_LEGACY graceful passthrough: if already EN (legacy
                        # config path), .get(v, v) returns unchanged — no double-translate.
                        persona_tone_en = TONE_PT_TO_EN_LEGACY.get(persona_tone, persona_tone)
                        if persona_tone_en != lia_tone:
                            logger.warning(
                                "lia_tone_divergence: outbound lia_tone=%r vs "
                                "chat ai_persona.tone=%r (→EN: %r) for company_id=%s. "
                                "Outbound messages use lia_tone; chat persona uses "
                                "ai_persona.tone. UI surfaces edited independently — "
                                "P1-6 sensor (read-time).",
                                lia_tone, persona_tone, persona_tone_en, company_id,
                                extra={"company_id": company_id,
                                       "lia_tone": lia_tone,
                                       "ai_persona_tone": persona_tone,
                                       "ai_persona_tone_en": persona_tone_en},
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
        recipient_email: str | None,
        recipient_phone: str | None,
        subject: str | None,
        formatted_message: str,
    ) -> dict[str, Any]:
        if channel == "email" and recipient_email:
            email_result = self.send_email(
                to_email=recipient_email,
                subject=subject or "Atualiza\u00e7\u00e3o do processo seletivo",
                body_html=f"<p>{formatted_message}</p>",
                body_text=formatted_message,
            )
            if email_result.get("success"):
                return email_result

            if recipient_phone:
                logger.warning(
                    "[DISPATCHER] Email failed for %s (error=%s) \u2014 attempting WhatsApp fallback to %s",
                    recipient_email,
                    email_result.get("error", "unknown"),
                    recipient_phone,
                )
                wa_result = self.send_whatsapp(
                    to_phone=recipient_phone,
                    message=formatted_message,
                )
                if wa_result.get("success"):
                    wa_result["fallback_from"] = "email"
                    wa_result["original_email_error"] = email_result.get("error")
                    return wa_result

                logger.error(
                    "[DISPATCHER] Both email and WhatsApp failed for %s / %s",
                    recipient_email,
                    recipient_phone,
                )
                return {
                    "success": False,
                    "error": "Both email and WhatsApp failed",
                    "email_error": email_result.get("error"),
                    "whatsapp_error": wa_result.get("error"),
                    "both_channels_failed": True,
                    "channel": "email",
                    "recipient": recipient_email,
                    "timestamp": datetime.utcnow().isoformat(),
                }

            return email_result

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
                subject=subject or "Atualiza\u00e7\u00e3o do processo seletivo",
                body_html=f"<p>{formatted_message}</p>",
                body_text=formatted_message,
            )
        return {"success": False, "error": "No recipient contact info provided", "channel": channel}
    
    def _apply_tone(
        self,
        message: str,
        tone: str,
        candidate_name: str | None = None,
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
    
    async def make_voice_call(
        self,
        candidate_id: str,
        candidate_name: str,
        phone_number: str,
        job_title: str,
        company_id: str,
        job_id: str | None = None,
        language: str = "pt-BR",
        db=None,
    ) -> dict[str, Any]:
        """
        Initiate a voice screening call via Twilio Programmable Voice.

        Checks LGPD consent before calling. If Twilio circuit is open or
        voice is not configured, returns fallback_channel='whatsapp' so
        callers can route to chat/WhatsApp screening.

        Args:
            candidate_id: Candidate UUID
            candidate_name: Candidate display name
            phone_number: E.164 phone number (e.g. +5511999999999)
            job_title: Job title for screening context
            company_id: Company/tenant UUID
            job_id: Optional job vacancy UUID
            language: Conversation language (default: pt-BR)
            db: SQLAlchemy async session for consent check

        Returns:
            Dict with success, session_id, call_sid, status, fallback_channel
        """
        try:
            from app.domains.voice.services.voice_screening_orchestrator import (
                ConsentNotGrantedError,
                voice_screening_orchestrator,
            )

            session = await voice_screening_orchestrator.initiate_call(
                candidate_id=candidate_id,
                candidate_name=candidate_name,
                phone_number=phone_number,
                job_title=job_title,
                company_id=company_id,
                job_id=job_id,
                language=language,
                db=db,
            )

            fallback = None
            if session.status in ("fallback", "failed", "circuit_open"):
                fallback = "whatsapp"
                logger.warning(
                    "[DISPATCHER] Voice call unavailable (status=%s) — fallback to WhatsApp for %s",
                    session.status,
                    phone_number,
                )

            return {
                "success": session.status == "initiated",
                "session_id": session.session_id,
                "call_sid": session.call_sid,
                "status": session.status,
                "channel": "voice",
                "fallback_channel": fallback,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except ConsentNotGrantedError:
            raise
        except Exception as e:
            logger.error("[DISPATCHER] make_voice_call error: %s", e)
            return {
                "success": False,
                "error": str(e),
                "channel": "voice",
                "fallback_channel": "whatsapp",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_communication_policy(
        self,
        company_id: str,
        db=None,
    ) -> dict[str, Any]:
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
