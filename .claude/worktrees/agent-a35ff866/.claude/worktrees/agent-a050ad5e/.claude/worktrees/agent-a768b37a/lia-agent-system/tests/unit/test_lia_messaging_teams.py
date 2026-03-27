"""
Testes para lia_messaging.teams — Teams webhook sending.

Garante que:
- send_teams_message retorna failure quando TEAMS_WEBHOOK_URL não configurado
- send_teams_message retorna success com httpx mockado (status 200)
- _build_card inclui title, text e facts corretamente
- send_teams_message retorna failure em exceção HTTP
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


class TestSendTeamsMessage:

    @pytest.mark.asyncio
    async def test_returns_failure_when_no_webhook(self, monkeypatch):
        monkeypatch.delenv("TEAMS_WEBHOOK_URL", raising=False)
        from lia_messaging.teams import send_teams_message
        result = await send_teams_message("Alert", "Something happened")
        assert result["success"] is False
        assert result["status_code"] is None
        assert "webhook" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_success_with_mocked_httpx(self, monkeypatch):
        monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://teams.webhook.example/hook")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        with patch("httpx.AsyncClient", return_value=mock_client):
            from lia_messaging.teams import send_teams_message
            result = await send_teams_message("Test Title", "Test Body")

        assert result["success"] is True
        assert result["status_code"] == 200

    @pytest.mark.asyncio
    async def test_returns_failure_on_exception(self, monkeypatch):
        monkeypatch.setenv("TEAMS_WEBHOOK_URL", "https://teams.webhook.example/hook")
        with patch("httpx.AsyncClient", side_effect=ConnectionError("refused")):
            from lia_messaging.teams import send_teams_message
            result = await send_teams_message("Title", "Body")
        assert result["success"] is False

    def test_build_card_has_title_and_facts(self):
        from lia_messaging.teams import _build_card
        facts = [{"name": "Cargo", "value": "Dev"}]
        card = _build_card("My Title", "My Text", color="FF0000", facts=facts)
        assert card["sections"][0]["activityTitle"] == "**My Title**"
        assert card["sections"][0]["activityText"] == "My Text"
        assert card["sections"][0]["facts"] == facts
        assert card["themeColor"] == "FF0000"
