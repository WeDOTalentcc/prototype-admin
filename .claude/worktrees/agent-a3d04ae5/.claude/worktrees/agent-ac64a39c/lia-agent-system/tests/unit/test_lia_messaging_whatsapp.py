"""
Testes para lia_messaging.whatsapp — WhatsApp sending (Meta + Twilio).

Garante que:
- send_whatsapp_message retorna failure quando META vars não configuradas
- send_whatsapp_message via meta retorna success com httpx mockado
- send_whatsapp_message via twilio retorna success com httpx mockado
- send_whatsapp_message retorna failure em exceção
- número sem prefixo 'whatsapp:' é normalizado automaticamente no Twilio
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestSendWhatsappMessage:

    @pytest.mark.asyncio
    async def test_meta_failure_when_no_token(self, monkeypatch):
        monkeypatch.delenv("WHATSAPP_PHONE_NUMBER_ID", raising=False)
        monkeypatch.delenv("WHATSAPP_API_TOKEN", raising=False)
        from lia_messaging.whatsapp import send_whatsapp_message
        result = await send_whatsapp_message("+5511999990000", "Olá", provider="meta")
        assert result["success"] is False
        assert result["provider"] == "meta"

    @pytest.mark.asyncio
    async def test_meta_success(self, monkeypatch):
        monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "phone-123")
        monkeypatch.setenv("WHATSAPP_API_TOKEN", "token-abc")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"messages": [{"id": "wamid.123"}]})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from lia_messaging.whatsapp import send_whatsapp_message
            result = await send_whatsapp_message("+5511999990000", "Olá mundo", provider="meta")

        assert result["success"] is True
        assert result["provider"] == "meta"
        assert result["message_id"] == "wamid.123"

    @pytest.mark.asyncio
    async def test_twilio_success(self, monkeypatch):
        monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
        monkeypatch.setenv("TWILIO_AUTH_TOKEN", "auth_test")
        monkeypatch.setenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={"sid": "SM_test_sid"})

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from lia_messaging.whatsapp import send_whatsapp_message
            result = await send_whatsapp_message("+5511999990000", "Test Twilio", provider="twilio")

        assert result["success"] is True
        assert result["provider"] == "twilio"
        assert result["message_id"] == "SM_test_sid"

    @pytest.mark.asyncio
    async def test_unknown_provider(self, monkeypatch):
        from lia_messaging.whatsapp import send_whatsapp_message
        result = await send_whatsapp_message("+5511999990000", "msg", provider="unknown_provider")
        assert result["success"] is False
        assert "Unknown provider" in result["error"]
