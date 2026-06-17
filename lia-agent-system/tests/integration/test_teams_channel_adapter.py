"""
Integration Tests — MS Teams Channel Adapter (Task #64).

Exercita:
- MSTeamsChannelAdapter.is_available(): retorna True quando webhook ou bot configurado
- MSTeamsChannelAdapter.send(): envia via TeamsBot._deliver_card e fallback TeamsService
- Payload correto para cards Adaptive (triagem_concluida, match_alto_detectado,
  sla_violado, meta_em_risco)
- TeamsBot.notify_triagem_completed, notify_high_match, notify_sla_violated,
  notify_goal_at_risk: constroem payloads válidos
- Fallback automático quando canal indisponível
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Seção 1 — MSTeamsChannelAdapter.is_available()
# ---------------------------------------------------------------------------

class TestMSTeamsChannelAdapterAvailability:

    @pytest.mark.asyncio
    async def test_is_available_true_when_webhook_url_set(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        with patch.dict("os.environ", {"TEAMS_WEBHOOK_URL": "https://example.webhook.office.com/xxx"}):
            adapter = MSTeamsChannelAdapter()
            assert await adapter.is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_false_when_only_app_credentials_set(self):
        """
        Bot credentials alone are not sufficient for delivery.
        TEAMS_WEBHOOK_URL is required for the fallback delivery path.
        """
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        with patch.dict("os.environ", {
            "MICROSOFT_APP_ID": "app-id-123",
            "MICROSOFT_APP_PASSWORD": "secret",
        }, clear=True):
            adapter = MSTeamsChannelAdapter()
            assert await adapter.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_false_when_no_config(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        with patch.dict("os.environ", {}, clear=True):
            adapter = MSTeamsChannelAdapter()
            result = await adapter.is_available()
            assert result is False


# ---------------------------------------------------------------------------
# Seção 2 — MSTeamsChannelAdapter.send() via TeamsBot
# ---------------------------------------------------------------------------

class TestMSTeamsChannelAdapterSend:

    def _make_message(self, subject="Test Subject", body="Test body"):
        from app.shared.channels.channel_adapter import ChannelMessage
        return ChannelMessage(
            recipient_id="user_001",
            recipient_name="Maria Santos",
            recipient_contact="maria@empresa.com",
            subject=subject,
            body_text=body,
            company_id="comp_001",
        )

    def _patch_teams_bot(self, mock_bot):
        """
        Patch teams_bot in the module where the adapter imports it from.
        The adapter does a local import inside send(), so we must patch the
        module-level singleton in teams_bot.py.
        """
        import app.domains.communication.services.teams_bot as _tb_mod
        return patch.object(_tb_mod, "teams_bot", mock_bot)

    def _patch_teams_service(self, mock_service):
        import app.domains.communication.services.teams_service as _ts_mod
        return patch.object(_ts_mod, "teams_service", mock_service)

    @pytest.mark.asyncio
    async def test_send_success_via_teams_bot(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        from app.shared.channels.channel_adapter import DeliveryStatus

        adapter = MSTeamsChannelAdapter()
        mock_bot = MagicMock()
        mock_bot._deliver_card = AsyncMock(return_value=True)

        with self._patch_teams_bot(mock_bot):
            result = await adapter.send(self._make_message())

        assert result.success is True
        assert result.status == DeliveryStatus.SENT
        assert result.error is None
        mock_bot._deliver_card.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_falls_back_to_teams_service_when_bot_fails(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        from app.shared.channels.channel_adapter import DeliveryStatus

        adapter = MSTeamsChannelAdapter()
        mock_bot = MagicMock()
        mock_bot._deliver_card = AsyncMock(return_value=False)
        mock_service = MagicMock()
        mock_service.send_message = AsyncMock(return_value={"success": True, "mode": "development"})

        with self._patch_teams_bot(mock_bot), self._patch_teams_service(mock_service):
            result = await adapter.send(self._make_message())

        assert result.success is True
        assert result.status == DeliveryStatus.SENT
        mock_service.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_failure_when_both_providers_fail(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        from app.shared.channels.channel_adapter import DeliveryStatus

        adapter = MSTeamsChannelAdapter()
        mock_bot = MagicMock()
        mock_bot._deliver_card = AsyncMock(return_value=False)
        mock_service = MagicMock()
        mock_service.send_message = AsyncMock(return_value={"success": False, "error": "Webhook timeout"})

        with self._patch_teams_bot(mock_bot), self._patch_teams_service(mock_service):
            result = await adapter.send(self._make_message())

        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_send_with_adaptive_card_in_metadata(self):
        from app.shared.channels.adapters.teams_adapter import MSTeamsChannelAdapter
        from app.shared.channels.channel_adapter import ChannelMessage, DeliveryStatus

        adapter = MSTeamsChannelAdapter()
        custom_card = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [{"type": "TextBlock", "text": "Custom card"}],
        }
        message = ChannelMessage(
            recipient_id="user_001",
            recipient_name="Test",
            recipient_contact="test@test.com",
            body_text="Test",
            metadata={"adaptive_card": custom_card},
            company_id="comp_001",
        )

        mock_bot = MagicMock()
        mock_bot._deliver_card = AsyncMock(return_value=True)

        with self._patch_teams_bot(mock_bot):
            result = await adapter.send(message)

        assert result.success is True
        delivered_card = mock_bot._deliver_card.call_args[0][0]
        assert delivered_card == custom_card


# ---------------------------------------------------------------------------
# Seção 3 — TeamsBot Adaptive Cards para os 4 triggers principais
# ---------------------------------------------------------------------------

class TestTeamsBotAdaptiveCards:

    @pytest.mark.asyncio
    async def test_notify_triagem_completed_sends_card(self):
        from app.domains.communication.services.teams_bot import TeamsBot

        bot = TeamsBot()
        with patch.object(bot, "_deliver_card", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True
            result = await bot.notify_triagem_completed(
                candidate_name="João Silva",
                job_title="Dev Python",
                score=87.5,
                classification="Aprovado",
                details_url="https://app.wedotalent.com/candidates/123",
            )

        assert result is True
        card = mock_deliver.call_args[0][0]
        assert card["type"] == "AdaptiveCard"
        body_texts = [b.get("text", "") for b in card["body"]]
        assert any("Triagem Concluída" in t for t in body_texts)
        facts = next(b for b in card["body"] if b["type"] == "FactSet")["facts"]
        fact_values = {f["title"]: f["value"] for f in facts}
        assert fact_values["Candidato:"] == "João Silva"
        assert fact_values["Vaga:"] == "Dev Python"
        assert "87.5" in fact_values.get("Score WSI:", "")

    @pytest.mark.asyncio
    async def test_notify_high_match_sends_card_with_actions(self):
        from app.domains.communication.services.teams_bot import TeamsBot

        bot = TeamsBot()
        with patch.object(bot, "_deliver_card", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True
            result = await bot.notify_high_match(
                candidate_name="Ana Costa",
                job_title="Product Manager",
                match_score=92.0,
                key_matches=["5 anos de experiência", "Inglês fluente"],
                candidate_profile_url="https://app.wedotalent.com/candidates/456",
            )

        assert result is True
        card = mock_deliver.call_args[0][0]
        assert card["type"] == "AdaptiveCard"
        body_texts = [b.get("text", "") for b in card["body"]]
        assert any("Match Alto" in t for t in body_texts)
        assert "actions" in card
        action_titles = [a["title"] for a in card["actions"]]
        assert any("Avançar" in t for t in action_titles)
        assert any("Agendar" in t for t in action_titles)
        assert any("Ver Perfil" in t for t in action_titles)

    @pytest.mark.asyncio
    async def test_notify_sla_violated_sends_warning_card(self):
        from app.domains.communication.services.teams_bot import TeamsBot

        bot = TeamsBot()
        with patch.object(bot, "_deliver_card", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True
            result = await bot.notify_sla_violated(
                job_title="Engenheiro de Software",
                sla_type="Resposta ao candidato",
                expected_time="48h",
                actual_time="72h",
                candidates_affected=3,
            )

        assert result is True
        card = mock_deliver.call_args[0][0]
        body_texts = [b.get("text", "") for b in card["body"]]
        assert any("SLA Violado" in t or "⚠️" in t for t in body_texts)
        facts = next(b for b in card["body"] if b["type"] == "FactSet")["facts"]
        fact_values = {f["title"]: f["value"] for f in facts}
        assert fact_values["Candidatos afetados:"] == "3"

    @pytest.mark.asyncio
    async def test_notify_goal_at_risk_sends_card_with_suggestions(self):
        from app.domains.communication.services.teams_bot import TeamsBot

        bot = TeamsBot()
        with patch.object(bot, "_deliver_card", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True
            result = await bot.notify_goal_at_risk(
                recruiter_name="Carlos Lima",
                goal_name="Triagens Concluídas - Q2",
                current_progress=45.0,
                target=80.0,
                deadline="30/06/2026",
                suggestions=["Aumentar divulgação", "Revisar critérios de triagem"],
            )

        assert result is True
        card = mock_deliver.call_args[0][0]
        body_texts = [b.get("text", "") for b in card["body"]]
        assert any("Meta em Risco" in t for t in body_texts)
        assert any("Carlos Lima" in t for t in body_texts)
        text_items_with_bullets = [b for b in card["body"] if b.get("text", "").startswith("•")]
        assert len(text_items_with_bullets) >= 1

    @pytest.mark.asyncio
    async def test_notify_candidate_timeout_sends_warning_card(self):
        from app.domains.communication.services.teams_bot import TeamsBot

        bot = TeamsBot()
        with patch.object(bot, "_deliver_card", new_callable=AsyncMock) as mock_deliver:
            mock_deliver.return_value = True
            result = await bot.notify_candidate_timeout(
                candidate_name="Pedro Alves",
                job_title="Analista de Dados",
                timeout_type="triagem",
                hours_elapsed=48.0,
            )

        assert result is True
        card = mock_deliver.call_args[0][0]
        body_texts = [b.get("text", "") for b in card["body"]]
        assert any("Timeout" in t or "Alerta" in t for t in body_texts)


# ---------------------------------------------------------------------------
# Seção 4 — Validate card structure (AdaptiveCard schema compliance)
# ---------------------------------------------------------------------------

class TestAdaptiveCardStructure:

    def _get_bot(self):
        from app.domains.communication.services.teams_bot import TeamsBot
        return TeamsBot()

    def test_triagem_completed_card_has_required_fields(self):
        bot = self._get_bot()
        card = bot._card_triagem_completed({
            "candidate_name": "Test",
            "job_title": "Dev",
            "completed_at": "01/01/2026 10:00 UTC",
            "score": "85.0",
            "classification": "Aprovado",
            "details_url": "https://example.com",
        })
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert "body" in card
        assert any(b["type"] == "FactSet" for b in card["body"])
        assert "actions" in card

    def test_high_match_card_has_required_fields(self):
        bot = self._get_bot()
        card = bot._card_high_match({
            "candidate_name": "Test",
            "job_title": "Dev",
            "match_score": "92%",
            "detected_at": "01/01/2026 10:00 UTC",
            "key_matches": ["Skill A", "Skill B"],
            "candidate_profile_url": "https://example.com",
        })
        assert card["type"] == "AdaptiveCard"
        assert "actions" in card
        action_types = [a["type"] for a in card["actions"]]
        assert "Action.Submit" in action_types
        assert "Action.OpenUrl" in action_types

    def test_sla_violated_card_has_required_fields(self):
        bot = self._get_bot()
        card = bot._card_sla_violated({
            "job_title": "Dev",
            "sla_type": "Resposta",
            "expected_time": "48h",
            "actual_time": "72h",
            "candidates_affected": "3",
            "detected_at": "01/01/2026 10:00 UTC",
        })
        assert card["type"] == "AdaptiveCard"
        assert any(b["type"] == "FactSet" for b in card["body"])

    def test_goal_at_risk_card_has_required_fields(self):
        bot = self._get_bot()
        card = bot._card_goal_at_risk({
            "recruiter_name": "Test",
            "goal_name": "Meta Q2",
            "current_progress": "45%",
            "target": "80%",
            "deadline": "30/06/2026",
            "suggestions": ["Ação 1", "Ação 2"],
        })
        assert card["type"] == "AdaptiveCard"
        fact_sets = [b for b in card["body"] if b["type"] == "FactSet"]
        assert len(fact_sets) >= 1
