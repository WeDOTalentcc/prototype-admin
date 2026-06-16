"""
GAP-11-018: Email Failure -> WhatsApp Fallback

TDD tests for the WhatsApp fallback when email sending fails.
Tests two layers:
1. _send_single_channel in CommunicationDispatcher
2. _dispatch_single_channel in TransitionDispatchService
"""
import pytest
import re
from unittest.mock import AsyncMock, MagicMock, patch


class TestSendSingleChannelWhatsAppFallback:
    """Tests for _send_single_channel WhatsApp fallback when email fails."""

    def _make_dispatcher(self):
        from app.domains.communication.services.communication_dispatcher import (
            CommunicationDispatcher,
        )
        return CommunicationDispatcher()

    @pytest.mark.asyncio
    async def test_email_success_no_fallback(self):
        """When email succeeds, WhatsApp is NOT attempted."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_email = MagicMock(return_value={
            "success": True, "message_id": "mg-123", "mock": False, "provider": "mailgun",
        })
        dispatcher.send_whatsapp = MagicMock()

        result = await dispatcher._send_single_channel(
            channel="email",
            recipient_email="test@example.com",
            recipient_phone="+5511999999999",
            subject="Test",
            formatted_message="Hello",
        )

        assert result["success"] is True
        assert result.get("provider") == "mailgun"
        dispatcher.send_whatsapp.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_fails_whatsapp_fallback_attempted(self):
        """When email fails and phone is available, WhatsApp fallback is attempted."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "All providers failed", "provider": "none",
        })
        dispatcher.send_whatsapp = MagicMock(return_value={
            "success": True, "message_id": "SM123", "mock": False, "channel": "whatsapp",
        })

        result = await dispatcher._send_single_channel(
            channel="email",
            recipient_email="test@example.com",
            recipient_phone="+5511999999999",
            subject="Test",
            formatted_message="Hello",
        )

        assert result["success"] is True
        assert result.get("channel") == "whatsapp"
        assert result.get("fallback_from") == "email"
        dispatcher.send_whatsapp.assert_called_once_with(
            to_phone="+5511999999999",
            message="Hello",
        )

    @pytest.mark.asyncio
    async def test_email_fails_no_phone_no_fallback(self):
        """When email fails but no phone available, no fallback -- returns email failure."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "All providers failed", "provider": "none",
        })
        dispatcher.send_whatsapp = MagicMock()

        result = await dispatcher._send_single_channel(
            channel="email",
            recipient_email="test@example.com",
            recipient_phone=None,
            subject="Test",
            formatted_message="Hello",
        )

        assert result["success"] is False
        dispatcher.send_whatsapp.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_fails_whatsapp_also_fails(self):
        """When both email and WhatsApp fail, return failure with both_failed flag."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "Mailgun down", "provider": "none",
        })
        dispatcher.send_whatsapp = MagicMock(return_value={
            "success": False, "error": "Twilio error 21608", "channel": "whatsapp",
        })

        result = await dispatcher._send_single_channel(
            channel="email",
            recipient_email="test@example.com",
            recipient_phone="+5511999999999",
            subject="Test",
            formatted_message="Hello",
        )

        assert result["success"] is False
        assert result.get("email_error") == "Mailgun down"
        assert result.get("whatsapp_error") == "Twilio error 21608"
        assert result.get("both_channels_failed") is True

    @pytest.mark.asyncio
    async def test_whatsapp_channel_no_email_fallback(self):
        """When WhatsApp is the explicit channel, no reverse fallback to email."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_whatsapp = MagicMock(return_value={
            "success": False, "error": "Twilio not configured", "channel": "whatsapp",
        })
        dispatcher.send_email = MagicMock()

        result = await dispatcher._send_single_channel(
            channel="whatsapp",
            recipient_email="test@example.com",
            recipient_phone="+5511999999999",
            subject="Test",
            formatted_message="Hello",
        )

        assert result["success"] is False
        dispatcher.send_email.assert_not_called()

    @pytest.mark.asyncio
    async def test_sms_channel_no_fallback(self):
        """SMS channel does not fallback to anything."""
        dispatcher = self._make_dispatcher()
        dispatcher.send_sms = MagicMock(return_value={
            "success": False, "error": "SMS failed",
        })
        dispatcher.send_whatsapp = MagicMock()

        result = await dispatcher._send_single_channel(
            channel="sms",
            recipient_email=None,
            recipient_phone="+5511999999999",
            subject=None,
            formatted_message="Hello",
        )

        assert result["success"] is False
        dispatcher.send_whatsapp.assert_not_called()


class TestTransitionDispatchWhatsAppFallback:
    """Tests for transition_dispatch_service _dispatch_single_channel email->WhatsApp fallback."""

    def _make_service(self):
        from app.domains.communication.services.transition_dispatch_service import (
            TransitionDispatchService,
        )
        service = TransitionDispatchService.__new__(TransitionDispatchService)
        service.dispatcher = MagicMock()
        service.db = AsyncMock()
        service._log_dispatch = AsyncMock()
        service._reveal_contact_for_dispatch = AsyncMock(return_value=None)
        service._find_template = AsyncMock()
        service._render_template = MagicMock(side_effect=lambda text, vars: text)
        return service

    def _make_template(self, name="test_template"):
        tpl = MagicMock()
        tpl.id = "tpl-1"
        tpl.name = name
        tpl.subject = "Subject"
        tpl.body_html = "<p>Body</p>"
        tpl.body_text = "Body"
        return tpl

    @pytest.mark.asyncio
    async def test_email_fails_whatsapp_fallback_with_phone(self):
        """When email dispatch fails and candidate has phone, WhatsApp fallback is attempted."""
        service = self._make_service()
        template = self._make_template()
        service._find_template.return_value = template

        service.dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "Mailgun circuit open",
        })
        service.dispatcher.send_whatsapp = MagicMock(return_value={
            "success": True, "message_id": "SM456", "mock": False, "channel": "whatsapp",
        })

        candidate_data = {
            "candidate_id": "cand-123",
            "email": "candidate@test.com",
            "mobile_phone": "+5511999999999",
        }

        result = await service._dispatch_single_channel(
            channel="email",
            situation="approved",
            candidate_data=candidate_data,
            variables={},
            company_id="comp-1",
            triggered_by="system",
            personalized_content=None,
        )

        assert result["success"] is True
        assert result.get("channel") == "whatsapp"
        assert result.get("fallback_from") == "email"
        service.dispatcher.send_whatsapp.assert_called_once()
        assert service._log_dispatch.call_count == 2

    @pytest.mark.asyncio
    async def test_email_fails_no_phone_returns_failure(self):
        """When email fails and no phone available, returns failure without fallback."""
        service = self._make_service()
        template = self._make_template()
        service._find_template.return_value = template

        service.dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "All providers failed",
        })

        candidate_data = {
            "candidate_id": "cand-456",
            "email": "candidate@test.com",
        }

        result = await service._dispatch_single_channel(
            channel="email",
            situation="rejected",
            candidate_data=candidate_data,
            variables={},
            company_id="comp-1",
            triggered_by="system",
            personalized_content=None,
        )

        assert result["success"] is False
        assert result["channel"] == "email"
        service.dispatcher.send_whatsapp.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_success_no_whatsapp_fallback(self):
        """When email succeeds, WhatsApp is NOT attempted even if phone exists."""
        service = self._make_service()
        template = self._make_template()
        service._find_template.return_value = template

        service.dispatcher.send_email = MagicMock(return_value={
            "success": True, "message_id": "mg-789", "mock": False,
        })

        candidate_data = {
            "candidate_id": "cand-789",
            "email": "candidate@test.com",
            "mobile_phone": "+5511999999999",
        }

        result = await service._dispatch_single_channel(
            channel="email",
            situation="approved",
            candidate_data=candidate_data,
            variables={},
            company_id="comp-1",
            triggered_by="system",
            personalized_content=None,
        )

        assert result["success"] is True
        assert result["channel"] == "email"
        service.dispatcher.send_whatsapp.assert_not_called()

    @pytest.mark.asyncio
    async def test_email_fails_reveal_phone_for_fallback(self):
        """When email fails and no phone in candidate_data, _reveal_contact is tried."""
        service = self._make_service()
        template = self._make_template()
        service._find_template.return_value = template
        service._reveal_contact_for_dispatch = AsyncMock(return_value="+5511888888888")

        service.dispatcher.send_email = MagicMock(return_value={
            "success": False, "error": "Resend also failed",
        })
        service.dispatcher.send_whatsapp = MagicMock(return_value={
            "success": True, "message_id": "SM999", "mock": False, "channel": "whatsapp",
        })

        candidate_data = {
            "candidate_id": "cand-reveal",
            "email": "candidate@test.com",
        }

        result = await service._dispatch_single_channel(
            channel="email",
            situation="interview_scheduled",
            candidate_data=candidate_data,
            variables={},
            company_id="comp-1",
            triggered_by="system",
            personalized_content=None,
        )

        assert result["success"] is True
        assert result["channel"] == "whatsapp"
        assert result["fallback_from"] == "email"
        service._reveal_contact_for_dispatch.assert_called_with(
            candidate_data, "phone", "comp-1",
        )
