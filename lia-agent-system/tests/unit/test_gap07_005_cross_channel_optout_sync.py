"""
GAP-07-005: Cross-channel opt-out sync — TDD tests.

When a candidate opts out via ANY channel, ALL channels must be opted out.
Re-consent (opt-in) does NOT auto-sync — must be explicit per channel (LGPD).
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.enums.communication import MessageChannel


COMPANY_ID = str(uuid4())
CANDIDATE_ID = str(uuid4())


def _make_optout_service():
    from app.domains.communication.services.communication_optout_service import (
        CommunicationOptOutService,
    )
    db = AsyncMock()
    return CommunicationOptOutService(db), db


# ======================================================================
# 1. Email opt-out syncs to WhatsApp
# ======================================================================

@pytest.mark.asyncio
async def test_email_optout_syncs_to_whatsapp():
    """When candidate opts out via email, WhatsApp channel is also opted out."""
    svc, db = _make_optout_service()

    with patch.object(svc, "_record_single_channel_optout", new_callable=AsyncMock) as mock_record:
        await svc.revoke_all_channels(
            company_id=COMPANY_ID,
            candidate_id=CANDIDATE_ID,
            source_channel=MessageChannel.EMAIL,
            reason="email unsubscribe link",
        )

    # Should record opt-out for BOTH email AND whatsapp
    channels_recorded = {call.kwargs["channel"] for call in mock_record.call_args_list}
    assert MessageChannel.EMAIL in channels_recorded
    assert MessageChannel.WHATSAPP in channels_recorded


# ======================================================================
# 2. WhatsApp opt-out syncs to email
# ======================================================================

@pytest.mark.asyncio
async def test_whatsapp_optout_syncs_to_email():
    """When candidate opts out via WhatsApp STOP, email channel is also opted out."""
    svc, db = _make_optout_service()

    with patch.object(svc, "_record_single_channel_optout", new_callable=AsyncMock) as mock_record:
        await svc.revoke_all_channels(
            company_id=COMPANY_ID,
            candidate_id=CANDIDATE_ID,
            source_channel=MessageChannel.WHATSAPP,
            reason="whatsapp STOP command",
        )

    channels_recorded = {call.kwargs["channel"] for call in mock_record.call_args_list}
    assert MessageChannel.EMAIL in channels_recorded
    assert MessageChannel.WHATSAPP in channels_recorded


# ======================================================================
# 3. Opt-out is company-scoped (multi-tenancy)
# ======================================================================

@pytest.mark.asyncio
async def test_optout_is_company_scoped():
    """Each opt-out record carries the correct company_id — multi-tenancy invariant."""
    svc, db = _make_optout_service()
    specific_company = str(uuid4())

    with patch.object(svc, "_record_single_channel_optout", new_callable=AsyncMock) as mock_record:
        await svc.revoke_all_channels(
            company_id=specific_company,
            candidate_id=CANDIDATE_ID,
            source_channel=MessageChannel.EMAIL,
            reason="test",
        )

    for call in mock_record.call_args_list:
        assert call.kwargs["company_id"] == specific_company


# ======================================================================
# 4. Opt-in does NOT auto-sync (re-consent must be explicit per channel)
# ======================================================================

@pytest.mark.asyncio
async def test_optin_does_not_auto_sync():
    """Re-consent on one channel must NOT auto-reactivate other channels.
    
    LGPD requires explicit consent per channel — silence is not consent.
    """
    svc, db = _make_optout_service()

    with patch.object(svc, "_reactivate_single_channel", new_callable=AsyncMock) as mock_reactivate:
        await svc.reactivate_channel(
            company_id=COMPANY_ID,
            candidate_id=CANDIDATE_ID,
            channel=MessageChannel.EMAIL,
            reason="candidate re-consented via portal",
        )

    # Must call reactivate for ONLY the specified channel
    assert mock_reactivate.call_count == 1
    assert mock_reactivate.call_args.kwargs["channel"] == MessageChannel.EMAIL


# ======================================================================
# 5. revoke_all_channels records correct source_channel metadata
# ======================================================================

@pytest.mark.asyncio
async def test_revoke_records_source_channel():
    """Each opt-out record should indicate which channel triggered the sync."""
    svc, db = _make_optout_service()

    with patch.object(svc, "_record_single_channel_optout", new_callable=AsyncMock) as mock_record:
        await svc.revoke_all_channels(
            company_id=COMPANY_ID,
            candidate_id=CANDIDATE_ID,
            source_channel=MessageChannel.WHATSAPP,
            reason="whatsapp STOP",
        )

    for call in mock_record.call_args_list:
        assert call.kwargs["opted_out_via"] == "cross_channel_sync:whatsapp"


# ======================================================================
# 6. Idempotency — already opted-out channel is skipped
# ======================================================================

@pytest.mark.asyncio
async def test_revoke_skips_already_opted_out():
    """If a channel is already opted out, don't create a duplicate record."""
    from app.domains.communication.services.communication_optout_service import (
        CommunicationOptOutService,
    )

    db = AsyncMock()
    svc = CommunicationOptOutService(db)

    existing_optout = MagicMock()
    existing_optout.is_active = True

    with (
        patch(
            "app.domains.communication.services.communication_optout_service.CommunicationRepository"
        ) as MockRepo,
        patch(
            "app.domains.communication.services.communication_optout_service.CandidateOptOut"
        ),
    ):
        # Email already opted out, WhatsApp not
        async def _get_optout(*, candidate_id, company_id, channel_value):
            if channel_value == "email":
                return existing_optout
            return None

        MockRepo.return_value.get_active_optout_for_channel = AsyncMock(side_effect=_get_optout)

        await svc.revoke_all_channels(
            company_id=COMPANY_ID,
            candidate_id=CANDIDATE_ID,
            source_channel=MessageChannel.EMAIL,
            reason="unsubscribe",
        )

    # db.add should only be called for WhatsApp (not email — already exists)
    added_objects = [call.args[0] for call in db.add.call_args_list]
    assert len(added_objects) == 1  # only whatsapp


# ======================================================================
# 7. Integration: WhatsApp STOP handler uses cross-channel sync
# ======================================================================

@pytest.mark.asyncio
async def test_whatsapp_stop_triggers_cross_channel_sync():
    """The WhatsApp _handle_stop_command should use CommunicationOptOutService.revoke_all_channels."""
    from app.domains.communication.services.data_request_whatsapp_service import (
        DataRequestWhatsAppService,
    )

    svc = DataRequestWhatsAppService.__new__(DataRequestWhatsAppService)
    svc.whatsapp_service = AsyncMock()

    db = AsyncMock()
    mock_request = MagicMock()
    mock_request.company_id = uuid4()
    mock_request.candidate_id = uuid4()

    with patch(
        "app.domains.communication.services.data_request_whatsapp_service.CommunicationOptOutService"
    ) as MockOptOutSvc:
        mock_instance = AsyncMock()
        MockOptOutSvc.return_value = mock_instance

        result = await svc._handle_stop_command(db, mock_request)

    assert result["status"] == "opted_out"
    mock_instance.revoke_all_channels.assert_awaited_once()
    kwargs = mock_instance.revoke_all_channels.call_args.kwargs
    assert kwargs["source_channel"] == MessageChannel.WHATSAPP
