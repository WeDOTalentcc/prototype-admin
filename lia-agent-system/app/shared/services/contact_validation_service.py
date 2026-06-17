"""Validacao de contato (email/telefone) — Peca C do fluxo de disparo.

Decisao Paulo: o cliente paga pela busca/reveal, entao vale validar para nao
enganar o recrutador com candidatos que nunca vao receber email/WhatsApp.

- Email: sintaxe (email_validator) + dominio com registro MX (dnspython). Sem MX =
  dominio nao recebe email -> badge "nao verificado".
- Telefone: formato/validade E.164 (phonenumbers). whatsapp_capable via Twilio
  Lookup e OPCIONAL e guardado (None quando sem credenciais) — nunca crasha.

Tudo fail-safe: erro de rede/lib nunca propaga; retorna o melhor veredito possivel.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_MX_TIMEOUT_SECONDS = float(os.environ.get("CONTACT_VALIDATION_MX_TIMEOUT", "3.0"))
_DEFAULT_PHONE_REGION = os.environ.get("CONTACT_VALIDATION_PHONE_REGION", "BR")


class ContactValidationService:
    """Validacao deterministica de email/telefone. Stateless."""

    @staticmethod
    def validate_email(email: str | None) -> dict:
        result = {"valid": False, "syntax_ok": False, "mx_found": False, "reason": ""}
        if not email or not email.strip():
            result["reason"] = "empty"
            return result

        try:
            from email_validator import EmailNotValidError, validate_email as _ev
        except Exception as e:  # pragma: no cover — lib ausente
            logger.warning("[ContactValidation] email_validator indisponivel: %s", e)
            result["reason"] = "validator_unavailable"
            return result

        try:
            v = _ev(email.strip(), check_deliverability=False)
            domain = v.domain
            result["syntax_ok"] = True
        except EmailNotValidError as e:
            result["reason"] = f"syntax: {e}"
            return result

        # MX lookup (dominio recebe email?)
        try:
            import dns.resolver

            answers = dns.resolver.resolve(domain, "MX", lifetime=_MX_TIMEOUT_SECONDS)
            result["mx_found"] = len(answers) > 0
        except Exception as e:
            logger.debug("[ContactValidation] MX lookup falhou para %s: %s", domain, e)
            result["mx_found"] = False

        result["valid"] = result["syntax_ok"] and result["mx_found"]
        if not result["mx_found"]:
            result["reason"] = "no_mx"
        return result

    @staticmethod
    def validate_phone(phone: str | None, region: str | None = None) -> dict:
        region = region or _DEFAULT_PHONE_REGION
        result = {"valid": False, "e164": None, "reason": "", "whatsapp_capable": None}
        if not phone or not phone.strip():
            result["reason"] = "empty"
            return result

        try:
            import phonenumbers
        except Exception as e:  # pragma: no cover
            logger.warning("[ContactValidation] phonenumbers indisponivel: %s", e)
            result["reason"] = "validator_unavailable"
            return result

        try:
            parsed = phonenumbers.parse(phone.strip(), region)
        except phonenumbers.NumberParseException as e:
            result["reason"] = f"parse: {e}"
            return result

        if phonenumbers.is_valid_number(parsed):
            result["valid"] = True
            result["e164"] = phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
        else:
            result["reason"] = "invalid_number"
        return result

    @staticmethod
    async def check_whatsapp_capable(e164_phone: str | None) -> bool | None:
        """Twilio Lookup: numero tem WhatsApp ativo? OPCIONAL + guardado.

        Retorna None (desconhecido) se sem credenciais Twilio ou erro — nunca crasha.
        Custa (Twilio Lookup) quando habilitado.
        """
        if not e164_phone:
            return None
        sid = os.environ.get("TWILIO_ACCOUNT_SID")
        token = os.environ.get("TWILIO_AUTH_TOKEN")
        if not sid or not token:
            return None  # sem credenciais -> desconhecido (badge neutro)
        try:
            from twilio.rest import Client

            client = Client(sid, token)
            info = client.lookups.v2.phone_numbers(e164_phone).fetch(
                fields="line_type_intelligence"
            )
            lti = getattr(info, "line_type_intelligence", None) or {}
            line_type = (lti or {}).get("type") if isinstance(lti, dict) else None
            # mobile/voip podem ter WhatsApp; landline tipicamente nao
            if line_type in ("mobile", "voip"):
                return True
            if line_type == "landline":
                return False
            return None
        except Exception as e:
            logger.debug("[ContactValidation] Twilio Lookup falhou: %s", e)
            return None


contact_validation_service = ContactValidationService()


def get_contact_validation_service() -> ContactValidationService:
    return contact_validation_service
