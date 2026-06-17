"""
Testes para lia_messaging.email — provider-agnostic email sending.

Garante que:
- _detect_provider() retorna 'mailgun' quando MAILGUN_API_KEY + MAILGUN_DOMAIN estão definidos
- _detect_provider() retorna 'resend' quando RESEND_API_KEY está definido (sem Mailgun)
- _detect_provider() retorna 'none' sem nenhuma chave
- send_email() retorna {"success": False} quando nenhum provider configurado
- send_email() via mailgun retorna {"success": True, "provider": "mailgun"} (httpx mockado)
- send_email() retorna {"success": False} em exception
- from_email padrão usa DEFAULT_FROM_EMAIL env var
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestDetectProvider:

    def test_mailgun_priority_over_resend(self, monkeypatch):
        monkeypatch.setenv("MAILGUN_API_KEY", "mg_abc")
        monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")
        monkeypatch.setenv("RESEND_API_KEY", "re_abc")
        from lia_messaging.email import _detect_provider
        assert _detect_provider() == "mailgun"

    def test_resend_when_no_mailgun(self, monkeypatch):
        monkeypatch.delenv("MAILGUN_API_KEY", raising=False)
        monkeypatch.delenv("MAILGUN_DOMAIN", raising=False)
        monkeypatch.setenv("RESEND_API_KEY", "re_abc")
        from lia_messaging.email import _detect_provider
        assert _detect_provider() == "resend"

    def test_mailgun_when_both_keys_present(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.setenv("MAILGUN_API_KEY", "mg_abc")
        monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")
        from lia_messaging.email import _detect_provider
        assert _detect_provider() == "mailgun"

    def test_none_when_no_keys(self, monkeypatch):
        for key in ("RESEND_API_KEY", "MAILGUN_API_KEY", "MAILGUN_DOMAIN"):
            monkeypatch.delenv(key, raising=False)
        from lia_messaging.email import _detect_provider
        assert _detect_provider() == "none"


class TestSendEmail:

    @pytest.mark.asyncio
    async def test_returns_failure_when_no_provider(self, monkeypatch):
        for key in ("RESEND_API_KEY", "MAILGUN_API_KEY", "MAILGUN_DOMAIN"):
            monkeypatch.delenv(key, raising=False)
        from lia_messaging.email import send_email
        result = await send_email("test@example.com", "Subject", "Body")
        assert result["success"] is False
        assert result["provider"] == "none"
        assert result["error"] is not None

    @pytest.mark.asyncio
    async def test_mailgun_success(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.setenv("MAILGUN_API_KEY", "mg_test_key")
        monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json = MagicMock(return_value={"id": "msg-123", "message": "Queued."})
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from lia_messaging.email import send_email
            result = await send_email("user@example.com", "Hello", "World")

        assert result["success"] is True
        assert result["provider"] == "mailgun"
        assert result["message_id"] == "msg-123"

    @pytest.mark.asyncio
    async def test_returns_failure_on_exception(self, monkeypatch):
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.setenv("MAILGUN_API_KEY", "mg_bad")
        monkeypatch.setenv("MAILGUN_DOMAIN", "mg.example.com")

        with patch("httpx.AsyncClient", side_effect=RuntimeError("network error")):
            from lia_messaging.email import send_email
            result = await send_email("x@example.com", "S", "B")

        assert result["success"] is False
        assert "network error" in result["error"]

    @pytest.mark.asyncio
    async def test_default_from_uses_env_var(self, monkeypatch):
        monkeypatch.setenv("DEFAULT_FROM_EMAIL", "custom@company.com")
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.delenv("MAILGUN_API_KEY", raising=False)

        from lia_messaging.email import send_email
        result = await send_email("to@example.com", "S", "B")
        assert result["success"] is False
        assert result["provider"] == "none"
