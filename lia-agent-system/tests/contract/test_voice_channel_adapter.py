"""
Sprint 3.4 W4-1 V2 — VoiceChannelAdapter contract tests.

Pin canonical behaviour of the voice channel adapter so future refactors do
not regress:

* ChannelType.VOICE enum is exported
* validate_contact accepts E.164 phone + voip: prefixed VoIP session id
* is_available delegates to Twilio AND/OR Gemini Live availability probes
* send() requires company_id (multi-tenancy fail-closed)
* send() routes PSTN → initiate_call, VoIP → initiate_voip_session
* send() returns DeliveryStatus.QUEUED on success (async session)
* Adapter consumes VoiceCoreOrchestrator (Sprint 3.2 canonical), not
  VoiceScreeningOrchestrator (legacy WSI-bound subclass)
* Plugin pass-through works (WSI mode + generic mode)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from app.shared.channels.adapters.voice_adapter import VoiceChannelAdapter
from app.shared.channels.channel_adapter import (
    ChannelMessage,
    ChannelType,
    DeliveryResult,
    DeliveryStatus,
)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _make_session(
    session_id: str = "sess-canonical-uuid",
    status: str = "initiated",
    call_sid: str | None = "CA-canonical",
    voice_provider: str = "twilio",
) -> MagicMock:
    s = MagicMock()
    s.session_id = session_id
    s.status = status
    s.call_sid = call_sid
    s.voice_provider = voice_provider
    return s


def _make_message(
    contact: str = "+5511999999999",
    company_id: str = "company-uuid-1",
    metadata: dict | None = None,
    recipient_id: str = "cand-uuid-1",
    recipient_name: str = "Maria",
    subject: str = "Triagem WSI",
    vacancy_id: str | None = None,
) -> ChannelMessage:
    return ChannelMessage(
        recipient_id=recipient_id,
        recipient_name=recipient_name,
        recipient_contact=contact,
        subject=subject,
        body_text="",
        company_id=company_id,
        vacancy_id=vacancy_id,
        metadata=metadata,
    )


# ----------------------------------------------------------------------------
# Enum + adapter shape
# ----------------------------------------------------------------------------

class TestChannelTypeVoiceEnum:
    def test_voice_in_channel_type_enum(self):
        assert ChannelType.VOICE.value == "voice"

    def test_adapter_channel_type_is_voice(self):
        assert VoiceChannelAdapter().channel_type == ChannelType.VOICE


# ----------------------------------------------------------------------------
# validate_contact
# ----------------------------------------------------------------------------

class TestValidateContact:
    @pytest.mark.parametrize("contact", [
        "+5511999999999",
        "+14155552671",
        "5511999999999",
        "+55 (11) 99999-9999",
    ])
    def test_validate_phone_e164_format(self, contact):
        assert VoiceChannelAdapter().validate_contact(contact) is True

    def test_validate_voip_session_format(self):
        assert VoiceChannelAdapter().validate_contact("voip:sess-uuid-abc") is True

    def test_validate_voip_prefix_alone_rejected(self):
        # "voip:" with nothing after is not a valid session id
        assert VoiceChannelAdapter().validate_contact("voip:") is False

    def test_validate_rejects_empty(self):
        assert VoiceChannelAdapter().validate_contact("") is False

    def test_validate_rejects_garbage(self):
        assert VoiceChannelAdapter().validate_contact("not-a-phone") is False
        assert VoiceChannelAdapter().validate_contact("abc") is False


# ----------------------------------------------------------------------------
# is_available — delegates to Twilio AND/OR Gemini Live
# ----------------------------------------------------------------------------

class TestIsAvailable:
    """is_configured is a @property on TwilioVoiceService → patch with PropertyMock."""

    @pytest.mark.asyncio
    async def test_is_available_true_when_twilio_configured(self):
        from app.domains.communication.services.twilio_voice_service import (
            TwilioVoiceService,
        )
        with patch.object(
            TwilioVoiceService, "is_configured",
            new_callable=PropertyMock, return_value=True,
        ), patch(
            "app.domains.voice.services.gemini_live_audio_service.get_gemini_live_service"
        ) as mock_gemini:
            mock_gemini.return_value.is_available.return_value = False
            assert await VoiceChannelAdapter().is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_true_when_gemini_only(self):
        from app.domains.communication.services.twilio_voice_service import (
            TwilioVoiceService,
        )
        with patch.object(
            TwilioVoiceService, "is_configured",
            new_callable=PropertyMock, return_value=False,
        ), patch(
            "app.domains.voice.services.gemini_live_audio_service.get_gemini_live_service"
        ) as mock_gemini:
            mock_gemini.return_value.is_available.return_value = True
            assert await VoiceChannelAdapter().is_available() is True

    @pytest.mark.asyncio
    async def test_is_available_false_when_both_unavailable(self):
        from app.domains.communication.services.twilio_voice_service import (
            TwilioVoiceService,
        )
        with patch.object(
            TwilioVoiceService, "is_configured",
            new_callable=PropertyMock, return_value=False,
        ), patch(
            "app.domains.voice.services.gemini_live_audio_service.get_gemini_live_service"
        ) as mock_gemini:
            mock_gemini.return_value.is_available.return_value = False
            assert await VoiceChannelAdapter().is_available() is False


# ----------------------------------------------------------------------------
# send() — multi-tenancy, routing, status mapping
# ----------------------------------------------------------------------------

class TestSendMultiTenancy:
    @pytest.mark.asyncio
    async def test_send_requires_company_id(self):
        msg = _make_message(company_id="")
        result = await VoiceChannelAdapter().send(msg)
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "company_id" in result.error

    @pytest.mark.asyncio
    async def test_send_rejects_invalid_contact(self):
        msg = _make_message(contact="not-a-phone")
        result = await VoiceChannelAdapter().send(msg)
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "Invalid contact" in result.error


class TestSendPSTNRouting:
    @pytest.mark.asyncio
    async def test_send_pstn_calls_initiate_call(self):
        fake_session = _make_session(session_id="sess-pstn-1")
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            inst = MockOrchestrator.return_value
            inst.initiate_call = AsyncMock(return_value=fake_session)
            inst.initiate_voip_session = AsyncMock()

            adapter = VoiceChannelAdapter()
            msg = _make_message(contact="+5511999999999")
            result = await adapter.send(msg)

            inst.initiate_call.assert_awaited_once()
            inst.initiate_voip_session.assert_not_called()
            assert result.success is True
            assert result.status == DeliveryStatus.QUEUED
            assert result.provider_id == "sess-pstn-1"
            assert result.metadata["is_voip"] is False

    @pytest.mark.asyncio
    async def test_send_pstn_propagates_candidate_and_job(self):
        fake_session = _make_session()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            inst = MockOrchestrator.return_value
            inst.initiate_call = AsyncMock(return_value=fake_session)

            adapter = VoiceChannelAdapter()
            msg = _make_message(
                metadata={"candidate_id": "cand-x", "candidate_name": "X",
                          "job_id": "job-y", "job_title": "Senior Eng"},
            )
            await adapter.send(msg)

            kwargs = inst.initiate_call.await_args.kwargs
            assert kwargs["candidate_id"] == "cand-x"
            assert kwargs["candidate_name"] == "X"
            assert kwargs["job_id"] == "job-y"
            assert kwargs["job_title"] == "Senior Eng"
            assert kwargs["company_id"] == "company-uuid-1"


class TestSendVoIPRouting:
    @pytest.mark.asyncio
    async def test_send_voip_calls_initiate_voip_session(self):
        fake_session = _make_session(
            session_id="sess-voip-1",
            call_sid=None,
            voice_provider="gemini_live",
        )
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            inst = MockOrchestrator.return_value
            inst.initiate_voip_session = AsyncMock(return_value=fake_session)
            inst.initiate_call = AsyncMock()

            adapter = VoiceChannelAdapter()
            msg = _make_message(contact="voip:browser-sess-123")
            result = await adapter.send(msg)

            inst.initiate_voip_session.assert_awaited_once()
            inst.initiate_call.assert_not_called()
            assert result.success is True
            assert result.metadata["is_voip"] is True
            assert result.metadata["voice_provider"] == "gemini_live"


class TestSendStatusMapping:
    @pytest.mark.asyncio
    async def test_send_returns_queued_status_on_success(self):
        fake_session = _make_session(status="initiated")
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value.initiate_call = AsyncMock(return_value=fake_session)
            result = await VoiceChannelAdapter().send(_make_message())
        assert result.status == DeliveryStatus.QUEUED
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_returns_failed_on_provider_fallback(self):
        fake_session = _make_session(status="fallback")
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value.initiate_call = AsyncMock(return_value=fake_session)
            result = await VoiceChannelAdapter().send(_make_message())
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "fallback" in (result.error or "")

    @pytest.mark.asyncio
    async def test_send_failed_on_orchestrator_exception(self):
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value.initiate_call = AsyncMock(
                side_effect=RuntimeError("twilio outage")
            )
            result = await VoiceChannelAdapter().send(_make_message())
        assert result.success is False
        assert result.status == DeliveryStatus.FAILED
        assert "twilio outage" in result.error


# ----------------------------------------------------------------------------
# Architectural sentinel: adapter consumes VoiceCoreOrchestrator, not
# VoiceScreeningOrchestrator. Sprint 3.4 contract — never regress.
# ----------------------------------------------------------------------------

class TestAdapterArchitecturalContract:
    @pytest.mark.asyncio
    async def test_adapter_uses_voice_core_orchestrator_directly(self):
        """Sprint 3.4: adapter imports VoiceCoreOrchestrator, never the
        legacy WSI subclass VoiceScreeningOrchestrator. The generic core
        is canonical; WSI behaviour comes via plugins."""
        import inspect
        from app.shared.channels.adapters import voice_adapter as mod
        src = inspect.getsource(mod)
        assert "VoiceCoreOrchestrator" in src, "must import canonical core"
        assert "VoiceScreeningOrchestrator(" not in src, (
            "adapter must NOT instantiate VoiceScreeningOrchestrator — that "
            "is the legacy WSI-bound subclass. Use VoiceCoreOrchestrator + "
            "plugins instead."
        )

    @pytest.mark.asyncio
    async def test_adapter_with_wsi_plugin_for_screening(self):
        """Plugins list is forwarded to VoiceCoreOrchestrator constructor."""
        fake_plugin = MagicMock()
        fake_session = _make_session()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value.initiate_call = AsyncMock(return_value=fake_session)
            adapter = VoiceChannelAdapter(plugins=[fake_plugin])
            await adapter.send(_make_message())
            MockOrchestrator.assert_called_once_with(plugins=[fake_plugin])

    @pytest.mark.asyncio
    async def test_adapter_without_plugin_generic_mode(self):
        """Default constructor → empty plugin list → generic voice."""
        fake_session = _make_session()
        with patch(
            "app.domains.voice.services.voice_screening_orchestrator.VoiceCoreOrchestrator"
        ) as MockOrchestrator:
            MockOrchestrator.return_value.initiate_call = AsyncMock(return_value=fake_session)
            adapter = VoiceChannelAdapter()
            await adapter.send(_make_message())
            MockOrchestrator.assert_called_once_with(plugins=[])


# ----------------------------------------------------------------------------
# check_status — Sprint 3.4 follow-up: real implementation reading
# VoiceSessionRedisRepository. Full mapping/edge-case coverage lives in
# tests/contract/test_voice_adapter_check_status.py. This module keeps the
# smoke test for "unknown id -> FAILED" so accidental regressions to the
# placeholder (return QUEUED always) are caught here too.
# ----------------------------------------------------------------------------

class TestCheckStatus:
    @pytest.mark.asyncio
    async def test_check_status_unknown_session_returns_failed(self):
        """Unknown session_id (no reverse-index entry) maps to FAILED, not the
        old placeholder QUEUED. Regression guard against revert to baseline
        placeholder. Full mapping coverage in test_voice_adapter_check_status.py.
        """
        result = await VoiceChannelAdapter().check_status("definitely-not-a-real-session")
        assert result == DeliveryStatus.FAILED
