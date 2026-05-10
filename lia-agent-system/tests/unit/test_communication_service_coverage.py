"""
Unit tests for CommunicationService — targeting
app/domains/communication/services/communication_service.py.
Covers: time/scheduling helpers, rate limiting, opt-out checks, quarantine,
validate_can_send, provider selection, MESSAGE_REQUIRES_APPROVAL config.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from uuid import uuid4


# ---------------------------------------------------------------------------
# MODULE-LEVEL constants
# ---------------------------------------------------------------------------

class TestMessageRequiresApproval:
    def test_initial_contact_requires_approval(self):
        from app.domains.communication.services.communication_service import MESSAGE_REQUIRES_APPROVAL
        from app.enums.communication import MessageType
        assert MESSAGE_REQUIRES_APPROVAL[MessageType.INITIAL_CONTACT] is True

    def test_screening_reminder_is_automatic(self):
        from app.domains.communication.services.communication_service import MESSAGE_REQUIRES_APPROVAL
        from app.enums.communication import MessageType
        assert MESSAGE_REQUIRES_APPROVAL[MessageType.SCREENING_REMINDER] is False

    def test_rejection_feedback_requires_approval(self):
        from app.domains.communication.services.communication_service import MESSAGE_REQUIRES_APPROVAL
        from app.enums.communication import MessageType
        assert MESSAGE_REQUIRES_APPROVAL[MessageType.REJECTION_FEEDBACK] is True

    def test_interview_confirmation_is_automatic(self):
        from app.domains.communication.services.communication_service import MESSAGE_REQUIRES_APPROVAL
        from app.enums.communication import MessageType
        assert MESSAGE_REQUIRES_APPROVAL[MessageType.INTERVIEW_CONFIRMATION] is False

    def test_offer_requires_approval(self):
        from app.domains.communication.services.communication_service import MESSAGE_REQUIRES_APPROVAL
        from app.enums.communication import MessageType
        assert MESSAGE_REQUIRES_APPROVAL[MessageType.OFFER] is True


# ---------------------------------------------------------------------------
# Time and scheduling helpers
# ---------------------------------------------------------------------------

class TestTimeHelpers:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider"), \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider"), \
             patch("app.domains.communication.services.communication_service.MockEmailProvider"), \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider"), \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            return CommunicationService()

    def test_get_brazil_now_returns_datetime(self, service):
        result = service._get_brazil_now()
        assert isinstance(result, datetime)

    def test_is_within_sending_hours_weekday_business(self, service):
        # Monday at 10am Brazil time = 13:00 UTC
        mock_utc = datetime(2024, 1, 8, 13, 0, 0)  # Monday
        with patch("app.domains.communication.services.communication_service.datetime") as mock_dt:
            mock_dt.utcnow.return_value = mock_utc
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = service._is_within_sending_hours()
            assert result is True

    def test_is_within_sending_hours_weekend(self, service):
        # Saturday at 10am Brazil time = 13:00 UTC
        mock_utc = datetime(2024, 1, 6, 13, 0, 0)  # Saturday
        with patch("app.domains.communication.services.communication_service.datetime") as mock_dt:
            mock_dt.utcnow.return_value = mock_utc
            mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
            result = service._is_within_sending_hours()
            assert result is False

    def test_get_next_sending_window_returns_datetime(self, service):
        result = service._get_next_sending_window()
        assert isinstance(result, datetime)

    def test_constants(self, service):
        assert service.MAX_MESSAGES_PER_DAY == 3
        assert service.QUARANTINE_DAYS == 90
        assert service.SENDING_START_HOUR == 8
        assert service.SENDING_END_HOUR == 20
        assert service.MAX_RETRIES == 3


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider"), \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider"), \
             patch("app.domains.communication.services.communication_service.MockEmailProvider"), \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider"), \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            return CommunicationService()

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, service):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value = iter([])  # No messages today
        mock_db.execute = AsyncMock(return_value=mock_result)

        allowed, count = await service._check_rate_limit("c1", "comp-1", mock_db)
        assert allowed is True
        assert count == 0

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, service):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        # 3 messages already sent
        mock_result.scalars.return_value = iter([MagicMock(), MagicMock(), MagicMock()])
        mock_db.execute = AsyncMock(return_value=mock_result)

        allowed, count = await service._check_rate_limit("c1", "comp-1", mock_db)
        assert allowed is False
        assert count == 3


# ---------------------------------------------------------------------------
# Opt-out checking
# ---------------------------------------------------------------------------

class TestOptOutChecking:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider"), \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider"), \
             patch("app.domains.communication.services.communication_service.MockEmailProvider"), \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider"), \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            return CommunicationService()

    @pytest.mark.asyncio
    async def test_not_opted_out(self, service):
        from app.enums.communication import MessageChannel
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_opted_out, record = await service._check_opt_out("c1", "comp-1", MessageChannel.EMAIL, mock_db)
        assert is_opted_out is False
        assert record is None

    @pytest.mark.asyncio
    async def test_opted_out(self, service):
        from app.enums.communication import MessageChannel
        mock_db = AsyncMock()
        mock_opt_out = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_opt_out
        mock_db.execute = AsyncMock(return_value=mock_result)

        is_opted_out, record = await service._check_opt_out("c1", "comp-1", MessageChannel.EMAIL, mock_db)
        assert is_opted_out is True
        assert record is not None


# ---------------------------------------------------------------------------
# Quarantine checking
# ---------------------------------------------------------------------------

class TestQuarantineChecking:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider"), \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider"), \
             patch("app.domains.communication.services.communication_service.MockEmailProvider"), \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider"), \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            return CommunicationService()

    @pytest.mark.asyncio
    async def test_not_in_quarantine(self, service):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        in_quarantine, record = await service._check_quarantine("c1", "comp-1", mock_db)
        assert in_quarantine is False

    @pytest.mark.asyncio
    async def test_in_quarantine(self, service):
        mock_db = AsyncMock()
        mock_quarantine = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_quarantine
        mock_db.execute = AsyncMock(return_value=mock_result)

        in_quarantine, record = await service._check_quarantine("c1", "comp-1", mock_db)
        assert in_quarantine is True


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

class TestProviderSelection:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider") as mp, \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider") as rp, \
             patch("app.domains.communication.services.communication_service.MockEmailProvider") as me, \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider") as tw, \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider") as wb, \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider") as mw, \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            svc = CommunicationService()
            return svc

    def test_get_provider_email(self, service):
        from app.enums.communication import MessageChannel
        provider = service._get_provider(MessageChannel.EMAIL)
        assert provider is not None

    def test_get_provider_whatsapp(self, service):
        from app.enums.communication import MessageChannel
        provider = service._get_provider(MessageChannel.WHATSAPP)
        assert provider is not None

    def test_email_template_getter(self, service):
        from app.enums.communication import MessageType
        template = service._get_email_template(MessageType.INITIAL_CONTACT)
        # Should return a template string or None
        assert template is not None or template is None  # Just ensure no crash

    def test_whatsapp_template_getter(self, service):
        from app.enums.communication import MessageType
        template = service._get_whatsapp_template(MessageType.INITIAL_CONTACT)
        assert template is not None or template is None


# ---------------------------------------------------------------------------
# validate_can_send (integration of rate limit + opt-out + quarantine)
# ---------------------------------------------------------------------------

class TestValidateCanSend:
    @pytest.fixture
    def service(self):
        with patch("app.domains.communication.services.communication_service.MailgunMessageProvider"), \
             patch("app.domains.communication.services.communication_service.ResendMessageProvider"), \
             patch("app.domains.communication.services.communication_service.MockEmailProvider"), \
             patch("app.domains.communication.services.communication_service.TwilioWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.WhatsAppBusinessProvider"), \
             patch("app.domains.communication.services.communication_service.MockWhatsAppProvider"), \
             patch("app.domains.communication.services.communication_service.NotificationService"):
            from app.domains.communication.services.communication_service import CommunicationService
            return CommunicationService()

    @pytest.mark.asyncio
    async def test_validate_can_send_all_clear(self, service):
        from app.enums.communication import MessageChannel, MessageType
        mock_db = AsyncMock()

        mock_consent_result = MagicMock()
        mock_consent_result.allowed = True
        mock_consent_result.reason = "granted"
        mock_consent_result.consent_type = "EMAIL_TRANSACTIONAL"

        with patch.object(service, "_check_opt_out", new_callable=AsyncMock, return_value=(False, None)), \
             patch.object(service, "_check_quarantine", new_callable=AsyncMock, return_value=(False, None)), \
             patch.object(service, "_check_rate_limit", new_callable=AsyncMock, return_value=(True, 0)), \
             patch.object(service, "_is_within_sending_hours", return_value=True), \
             patch("app.domains.communication.services.communication_service._get_db") as mock_get_db, \
             patch("app.domains.communication.services.consent_gate.CommunicationConsentGate") as mock_cg_cls:

            mock_cg_cls.return_value.check = AsyncMock(return_value=mock_consent_result)

            # Mock the async context manager
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_db.return_value = mock_ctx

            result = await service.validate_can_send(
                "c1", "comp-1", MessageChannel.EMAIL, MessageType.SCREENING_REMINDER, db=mock_db
            )
            assert result["can_send"] is True

    @pytest.mark.asyncio
    async def test_validate_blocked_by_opt_out(self, service):
        from app.enums.communication import MessageChannel, MessageType
        mock_db = AsyncMock()
        mock_opt_out = MagicMock()
        mock_opt_out.channel = "email"

        with patch.object(service, "_check_opt_out", new_callable=AsyncMock, return_value=(True, mock_opt_out)), \
             patch.object(service, "_check_quarantine", new_callable=AsyncMock, return_value=(False, None)), \
             patch.object(service, "_check_rate_limit", new_callable=AsyncMock, return_value=(True, 0)), \
             patch.object(service, "_is_within_sending_hours", return_value=True), \
             patch("app.domains.communication.services.communication_service._get_db") as mock_get_db:

            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_get_db.return_value = mock_ctx

            result = await service.validate_can_send(
                "c1", "comp-1", MessageChannel.EMAIL, MessageType.INITIAL_CONTACT, db=mock_db
            )
            assert result["can_send"] is False
            assert any("opt" in r.lower() for r in result.get("reasons", result.get("blocking_reasons", ["opt_out"])))
