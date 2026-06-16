"""
P0-3 — WhatsApp silent fallback fix tests.
Verifica que o ENVIRONMENT default é fail-safe (production, não development).
"""
import os
import pytest
from unittest.mock import patch


def test_whatsapp_service_environment_default_is_failsafe():
    """Sem APP_ENV nem ENVIRONMENT setados, o default deve ser 'production' (fail-safe)."""
    with patch.dict(os.environ, {}, clear=False):
        # Remover APP_ENV e ENVIRONMENT do environ para testar o default
        env = {k: v for k, v in os.environ.items() if k not in ("APP_ENV", "ENVIRONMENT")}
        with patch.dict(os.environ, env, clear=True):
            # Reimportar o serviço para pegar o novo valor
            import importlib
            import app.domains.communication.services.whatsapp_twilio_service as mod
            importlib.reload(mod)
            svc = mod.TwilioWhatsAppService()
            assert svc.environment == "production", (
                f"Default ENVIRONMENT deveria ser 'production' (fail-safe) mas é '{svc.environment}'"
            )
            assert not svc.is_development, (
                "is_development deveria ser False quando ENVIRONMENT=production"
            )


def test_whatsapp_service_respects_app_env():
    """APP_ENV=development → is_development=True (comportamento de dev preservado)."""
    with patch.dict(os.environ, {"APP_ENV": "development"}, clear=False):
        import importlib
        import app.domains.communication.services.whatsapp_twilio_service as mod
        importlib.reload(mod)
        svc = mod.TwilioWhatsAppService()
        assert svc.environment == "development"
        assert svc.is_development


def test_whatsapp_service_configured_without_number():
    """is_configured=False quando TWILIO_WHATSAPP_NUMBER está ausente."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("TWILIO_WHATSAPP_NUMBER",)}
    env["TWILIO_ACCOUNT_SID"] = "AC123"
    env["TWILIO_AUTH_TOKEN"] = "token123"
    with patch.dict(os.environ, env, clear=True):
        import importlib
        import app.domains.communication.services.whatsapp_twilio_service as mod
        importlib.reload(mod)
        svc = mod.TwilioWhatsAppService()
        assert not svc.is_configured, (
            "is_configured deveria ser False sem TWILIO_WHATSAPP_NUMBER"
        )


def test_whatsapp_service_configured_with_all_creds():
    """is_configured=True quando SID + token + número estão presentes."""
    with patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "AC76fd82fbff27b6d334ea540ec6a1840b",
        "TWILIO_AUTH_TOKEN": "1b3319733bf330ec307ada46f617e52a",
        "TWILIO_WHATSAPP_NUMBER": "+551140403098",
    }):
        import importlib
        import app.domains.communication.services.whatsapp_twilio_service as mod
        importlib.reload(mod)
        svc = mod.TwilioWhatsAppService()
        assert svc.is_configured, "is_configured deveria ser True com todas as credenciais"
