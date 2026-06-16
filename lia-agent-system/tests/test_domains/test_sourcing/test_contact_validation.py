"""Sensores do ContactValidationService (Peca C).

Email = sintaxe + MX; telefone = E.164. MX e mockado para determinismo (sem rede).
"""
import pytest
from unittest.mock import MagicMock, patch

from app.shared.services.contact_validation_service import ContactValidationService as V


def _mock_mx(found: bool):
    if found:
        return patch("dns.resolver.resolve", return_value=[MagicMock()])
    return patch("dns.resolver.resolve", side_effect=Exception("NXDOMAIN"))


def test_email_valid_with_mx():
    with _mock_mx(True):
        r = V.validate_email("ana@empresa.com")
    assert r["valid"] is True
    assert r["syntax_ok"] is True
    assert r["mx_found"] is True


def test_email_syntax_invalid():
    r = V.validate_email("notanemail")
    assert r["valid"] is False
    assert r["syntax_ok"] is False
    assert "syntax" in r["reason"]


def test_email_syntax_ok_but_no_mx():
    with _mock_mx(False):
        r = V.validate_email("ana@dominio-sem-mx.com")
    assert r["syntax_ok"] is True
    assert r["mx_found"] is False
    assert r["valid"] is False
    assert r["reason"] == "no_mx"


def test_email_empty():
    r = V.validate_email("")
    assert r["valid"] is False and r["reason"] == "empty"


def test_phone_valid_e164():
    r = V.validate_phone("+55 11 97052-7381")
    assert r["valid"] is True
    assert r["e164"] == "+5511970527381"


def test_phone_invalid():
    r = V.validate_phone("123")
    assert r["valid"] is False
    assert r["e164"] is None


def test_phone_empty():
    r = V.validate_phone(None)
    assert r["valid"] is False and r["reason"] == "empty"


@pytest.mark.asyncio
async def test_whatsapp_capable_none_without_twilio(monkeypatch):
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    out = await V.check_whatsapp_capable("+5511970527381")
    assert out is None  # sem credenciais -> desconhecido, nunca crasha
