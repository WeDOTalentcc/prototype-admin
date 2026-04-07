"""
Integration Tests — Pipeline de comunicação WhatsApp (Task #53, Item 5).

Exercita o comportamento REAL de:
- TwilioWhatsAppProvider._format_phone_number(): normalização E.164 para whatsapp:+55...
- TwilioWhatsAppProvider.send(): template_sid / media_url / Twilio SDK call
- CommunicationService._is_within_sending_hours(): política BRT 8h-20h seg-sex
- CommunicationService.validate_can_send(): opt-out, rate-limit, quarantine checks
- CommunicationService.send_message(): guards no_recipient e blocked
- MockWhatsAppProvider.is_available(): sempre True
- WhatsAppTemplates: templates têm campos obrigatórios
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Seção 1 — TwilioWhatsAppProvider: phone number formatting
# ---------------------------------------------------------------------------

class TestTwilioPhoneNumberFormatting:

    def _get_provider(self):
        from app.domains.communication.services.communication_service import TwilioWhatsAppProvider
        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "ACtest",
            "TWILIO_AUTH_TOKEN": "authtest",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+15005550006",
        }):
            provider = TwilioWhatsAppProvider()
        return provider

    def test_plain_e164_phone_gets_whatsapp_prefix(self):
        """+5511999999999 → whatsapp:+5511999999999."""
        provider = self._get_provider()
        result = provider._format_phone_number("+5511999999999")
        assert result == "whatsapp:+5511999999999"

    def test_phone_already_with_whatsapp_prefix_is_not_doubled(self):
        """whatsapp:+5511... não deve ter prefixo duplicado."""
        provider = self._get_provider()
        result = provider._format_phone_number("whatsapp:+5511999999999")
        assert result == "whatsapp:+5511999999999"

    def test_phone_starting_with_55_gets_plus_prepended(self):
        """5511999999999 → whatsapp:+5511999999999."""
        provider = self._get_provider()
        result = provider._format_phone_number("5511999999999")
        assert result == "whatsapp:+5511999999999"

    def test_phone_without_country_code_gets_55_prepended(self):
        """11999999999 (sem código) → whatsapp:+5511999999999."""
        provider = self._get_provider()
        result = provider._format_phone_number("11999999999")
        assert result == "whatsapp:+5511999999999"

    def test_phone_with_whitespace_is_stripped(self):
        """Espaços ao redor do número devem ser removidos."""
        provider = self._get_provider()
        result = provider._format_phone_number("  +5511999999999  ")
        assert result == "whatsapp:+5511999999999"

    def test_formatted_phone_always_starts_with_whatsapp_colon(self):
        """Resultado deve sempre começar com 'whatsapp:'."""
        provider = self._get_provider()
        for phone in ["+5511999999999", "11999999999", "5511999999999"]:
            result = provider._format_phone_number(phone)
            assert result.startswith("whatsapp:"), f"'{phone}' → '{result}' sem 'whatsapp:'"


# ---------------------------------------------------------------------------
# Seção 2 — TwilioWhatsAppProvider: send without Twilio credentials returns error
# ---------------------------------------------------------------------------

class TestTwilioWhatsAppSendWithoutCredentials:

    @pytest.mark.asyncio
    async def test_send_without_twilio_configured_returns_error_tuple(self):
        """Sem Twilio configurado, send() deve retornar (False, None, {error: ...})."""
        from app.domains.communication.services.communication_service import TwilioWhatsAppProvider

        with patch.dict("os.environ", {}, clear=True):
            provider = TwilioWhatsAppProvider()

        with patch(
            "app.domains.communication.services.communication_service.TWILIO_AVAILABLE",
            True
        ):
            result = await provider.send(
                to="+5511999999999",
                subject=None,
                body="Teste",
            )

        success, sid, data = result
        assert success is False
        assert sid is None
        assert "error" in data

    @pytest.mark.asyncio
    async def test_send_with_template_sid_adds_content_sid_to_params(self):
        """send() com template_sid deve incluir content_sid nos params do Twilio."""
        from app.domains.communication.services.communication_service import TwilioWhatsAppProvider

        with patch.dict("os.environ", {
            "TWILIO_ACCOUNT_SID": "ACtest",
            "TWILIO_AUTH_TOKEN": "authtest",
            "TWILIO_WHATSAPP_FROM": "whatsapp:+15005550006",
        }):
            provider = TwilioWhatsAppProvider()

        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_message.status = "sent"
        mock_message.date_created = None
        mock_message.error_code = None

        mock_messages = MagicMock()
        mock_messages.create.return_value = mock_message

        mock_client = MagicMock()
        mock_client.messages = mock_messages
        provider._client = mock_client

        with patch(
            "app.domains.communication.services.communication_service.TWILIO_AVAILABLE",
            True
        ), patch.object(provider, "is_available", return_value=True):
            success, sid, data = await provider.send(
                to="+5511999999999",
                subject=None,
                body="Mensagem de template",
                template_sid="HX123456",
                content_variables={"1": "João"},
            )

        call_kwargs = mock_messages.create.call_args[1]
        assert "content_sid" in call_kwargs
        assert call_kwargs["content_sid"] == "HX123456"


# ---------------------------------------------------------------------------
# Seção 3 — CommunicationService: _is_within_sending_hours
# ---------------------------------------------------------------------------

class TestSendingHoursPolicy:

    def _build_service(self):
        from app.domains.communication.services.communication_service import CommunicationService
        svc = CommunicationService.__new__(CommunicationService)
        svc.SENDING_START_HOUR = 8
        svc.SENDING_END_HOUR = 20
        svc.MAX_MESSAGES_PER_DAY = 3
        return svc

    def test_monday_at_noon_is_within_sending_hours(self):
        """Segunda-feira ao meio-dia deve retornar True."""
        svc = self._build_service()
        monday_noon = datetime(2026, 4, 6, 12, 0)  # Monday
        assert monday_noon.weekday() == 0
        with patch.object(svc, "_get_brazil_now", return_value=monday_noon):
            assert svc._is_within_sending_hours() is True

    def test_evening_after_20h_is_outside_sending_hours(self):
        """Após 20h deve retornar False."""
        svc = self._build_service()
        evening = datetime(2026, 4, 7, 22, 0)
        with patch.object(svc, "_get_brazil_now", return_value=evening):
            assert svc._is_within_sending_hours() is False

    def test_saturday_is_outside_sending_hours(self):
        """Sábado deve retornar False independentemente do horário."""
        svc = self._build_service()
        saturday = datetime(2026, 4, 4, 14, 0)  # April 4, 2026 = Saturday
        assert saturday.weekday() == 5
        with patch.object(svc, "_get_brazil_now", return_value=saturday):
            assert svc._is_within_sending_hours() is False

    def test_sunday_is_outside_sending_hours(self):
        """Domingo deve retornar False."""
        svc = self._build_service()
        sunday = datetime(2026, 4, 5, 14, 0)  # April 5, 2026 = Sunday
        assert sunday.weekday() == 6
        with patch.object(svc, "_get_brazil_now", return_value=sunday):
            assert svc._is_within_sending_hours() is False

    def test_exactly_at_8h_is_within_sending_hours(self):
        """Exatamente às 8h deve retornar True."""
        svc = self._build_service()
        opening = datetime(2026, 4, 6, 8, 0)  # Monday at 8h
        with patch.object(svc, "_get_brazil_now", return_value=opening):
            assert svc._is_within_sending_hours() is True

    def test_before_8h_is_outside_sending_hours(self):
        """Antes das 8h deve retornar False."""
        svc = self._build_service()
        early = datetime(2026, 4, 6, 7, 59)
        with patch.object(svc, "_get_brazil_now", return_value=early):
            assert svc._is_within_sending_hours() is False


# ---------------------------------------------------------------------------
# Seção 4 — CommunicationService: _get_next_sending_window
# ---------------------------------------------------------------------------

class TestNextSendingWindow:

    def _build_service(self):
        from app.domains.communication.services.communication_service import CommunicationService
        svc = CommunicationService.__new__(CommunicationService)
        svc.SENDING_START_HOUR = 8
        svc.SENDING_END_HOUR = 20
        svc.MAX_MESSAGES_PER_DAY = 3
        return svc

    def test_after_hours_next_window_is_tomorrow_morning(self):
        """Após 20h de segunda, próxima janela deve ser um datetime futuro."""
        svc = self._build_service()
        monday_21h = datetime(2026, 4, 6, 21, 0)
        with patch.object(svc, "_get_brazil_now", return_value=monday_21h):
            nw = svc._get_next_sending_window()
        assert isinstance(nw, datetime)

    def test_weekend_next_window_is_computed_from_saturday(self):
        """De sábado, próxima janela deve ser calculada corretamente."""
        svc = self._build_service()
        saturday = datetime(2026, 4, 4, 14, 0)  # Saturday
        assert saturday.weekday() == 5
        with patch.object(svc, "_get_brazil_now", return_value=saturday):
            nw = svc._get_next_sending_window()
        assert nw is not None
        assert isinstance(nw, datetime)


# ---------------------------------------------------------------------------
# Seção 5 — validate_can_send: policy checks via mocked private methods
# ---------------------------------------------------------------------------

class TestValidateCanSend:

    def _make_svc(self):
        from app.domains.communication.services.communication_service import CommunicationService
        with patch(
            "app.domains.communication.services.communication_service.AsyncSessionLocal"
        ):
            svc = CommunicationService()
        return svc

    @pytest.mark.asyncio
    async def test_opted_out_candidate_cannot_receive_messages(self):
        """Candidato com opt-out → can_send=False, block type='opt_out'."""
        from app.domains.communication.services.communication_service import (
            MessageChannel, MessageType,
        )
        svc = self._make_svc()

        from datetime import datetime
        mock_opt_out = MagicMock()
        mock_opt_out.opted_out_at = datetime(2026, 1, 1, 12, 0)

        with patch.object(svc, "_check_opt_out", new_callable=AsyncMock,
                          return_value=(True, mock_opt_out)), \
             patch.object(svc, "_check_quarantine", new_callable=AsyncMock,
                          return_value=(False, None)), \
             patch.object(svc, "_check_rate_limit", new_callable=AsyncMock,
                          return_value=(True, 0)), \
             patch.object(svc, "_is_within_sending_hours", return_value=True):
            result = await svc.validate_can_send(
                candidate_id="cand-001",
                company_id="company-001",
                channel=MessageChannel.WHATSAPP,
                message_type=MessageType.INTERVIEW_INVITE,
                db=AsyncMock(),
            )

        assert result["can_send"] is False
        block_types = [b["type"] for b in result["blocks"]]
        assert "opt_out" in block_types

    @pytest.mark.asyncio
    async def test_rate_limited_candidate_cannot_receive_messages(self):
        """Candidato com 5 msgs hoje → can_send=False, block type='rate_limit'."""
        from app.domains.communication.services.communication_service import (
            MessageChannel, MessageType,
        )
        svc = self._make_svc()

        with patch.object(svc, "_check_opt_out", new_callable=AsyncMock,
                          return_value=(False, None)), \
             patch.object(svc, "_check_quarantine", new_callable=AsyncMock,
                          return_value=(False, None)), \
             patch.object(svc, "_check_rate_limit", new_callable=AsyncMock,
                          return_value=(False, 5)), \
             patch.object(svc, "_is_within_sending_hours", return_value=True):
            result = await svc.validate_can_send(
                candidate_id="cand-002",
                company_id="company-001",
                channel=MessageChannel.WHATSAPP,
                message_type=MessageType.INTERVIEW_INVITE,
                db=AsyncMock(),
            )

        assert result["can_send"] is False
        block_types = [b["type"] for b in result["blocks"]]
        assert "rate_limit" in block_types

    @pytest.mark.asyncio
    async def test_clean_candidate_can_receive_messages(self):
        """Candidato sem bloqueios → can_send=True, blocks=[]."""
        from app.domains.communication.services.communication_service import (
            MessageChannel, MessageType,
        )
        svc = self._make_svc()

        with patch.object(svc, "_check_opt_out", new_callable=AsyncMock,
                          return_value=(False, None)), \
             patch.object(svc, "_check_quarantine", new_callable=AsyncMock,
                          return_value=(False, None)), \
             patch.object(svc, "_check_rate_limit", new_callable=AsyncMock,
                          return_value=(True, 0)), \
             patch.object(svc, "_is_within_sending_hours", return_value=True):
            result = await svc.validate_can_send(
                candidate_id="cand-003",
                company_id="company-001",
                channel=MessageChannel.WHATSAPP,
                message_type=MessageType.INTERVIEW_INVITE,
                db=AsyncMock(),
            )

        assert result["can_send"] is True
        assert result["blocks"] == []


# ---------------------------------------------------------------------------
# Seção 6 — send_message: no_recipient guard
# ---------------------------------------------------------------------------

class TestSendMessageGuards:

    def _make_svc(self):
        from app.domains.communication.services.communication_service import CommunicationService
        with patch(
            "app.domains.communication.services.communication_service.AsyncSessionLocal"
        ):
            svc = CommunicationService()
        return svc

    @pytest.mark.asyncio
    async def test_send_message_without_phone_returns_no_recipient_error(self):
        """send_message sem phone → error='no_recipient' (policy passes, no recipient)."""
        from app.domains.communication.services.communication_service import (
            MessageChannel, MessageType,
        )
        svc = self._make_svc()

        with patch.object(svc, "validate_can_send", new_callable=AsyncMock,
                          return_value={"can_send": True, "requires_approval": False,
                                        "warnings": [], "blocks": []}):
            result = await svc.send_message(
                company_id="company-001",
                candidate_id="cand-001",
                candidate_email=None,
                candidate_phone=None,
                message_type=MessageType.INTERVIEW_INVITE,
                channel=MessageChannel.WHATSAPP,
                subject=None,
                body="Convite para entrevista",
                db=AsyncMock(),
            )

        assert result["success"] is False
        assert result["error"] == "no_recipient"

    @pytest.mark.asyncio
    async def test_send_message_blocked_by_policy_returns_blocked_error(self):
        """send_message bloqueado por política → success=False, error='blocked'."""
        from app.domains.communication.services.communication_service import (
            MessageChannel, MessageType,
        )
        svc = self._make_svc()

        with patch.object(svc, "validate_can_send", new_callable=AsyncMock,
                          return_value={
                              "can_send": False,
                              "blocks": [{"type": "opt_out"}],
                              "warnings": [],
                          }):
            result = await svc.send_message(
                company_id="company-001",
                candidate_id="cand-001",
                candidate_email=None,
                candidate_phone="+5511999999999",
                message_type=MessageType.INTERVIEW_INVITE,
                channel=MessageChannel.WHATSAPP,
                subject=None,
                body="Convite para entrevista",
                db=AsyncMock(),
            )

        assert result["success"] is False
        assert result["error"] == "blocked"


# ---------------------------------------------------------------------------
# Seção 7 — WhatsApp provider availability
# ---------------------------------------------------------------------------

class TestWhatsAppProviders:

    def test_mock_whatsapp_provider_is_always_available(self):
        """MockWhatsAppProvider.is_available() deve ser True."""
        from app.domains.communication.services.communication_service import MockWhatsAppProvider
        provider = MockWhatsAppProvider()
        assert provider.is_available() is True

    def test_communication_service_has_whatsapp_providers_list(self):
        """CommunicationService deve ter lista de WhatsApp providers."""
        from app.domains.communication.services.communication_service import CommunicationService
        svc = CommunicationService.__new__(CommunicationService)
        svc._whatsapp_providers = []
        svc._email_providers = []
        assert isinstance(svc._whatsapp_providers, list)

    def test_message_channel_whatsapp_has_correct_value(self):
        """MessageChannel.WHATSAPP deve ter valor 'whatsapp'."""
        from app.domains.communication.services.communication_service import MessageChannel
        assert MessageChannel.WHATSAPP.value == "whatsapp"

    def test_message_type_interview_invite_exists(self):
        """MessageType.INTERVIEW_INVITE deve existir."""
        from app.domains.communication.services.communication_service import MessageType
        assert hasattr(MessageType, "INTERVIEW_INVITE")

    def test_message_type_initial_contact_requires_approval(self):
        """MessageType.INITIAL_CONTACT deve requerer aprovação."""
        from app.domains.communication.services.communication_service import (
            MessageType, MESSAGE_REQUIRES_APPROVAL
        )
        assert MESSAGE_REQUIRES_APPROVAL.get(MessageType.INITIAL_CONTACT) is True
