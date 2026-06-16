"""
GAP-07-005: Opt-out sync entre canais (email/WhatsApp) — TDD RED→GREEN
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.enums.communication import MessageChannel


# ==========================================================================
# GAP A: _check_opt_out deve respeitar candidate.channel_opt_out JSONB
# ==========================================================================

@pytest.mark.asyncio
async def test_check_opt_out_respects_email_jsonb_flag():
    """CandidateOptOut table vazia + channel_opt_out=['marketing_email'] → bloqueia email."""
    from app.domains.communication.services.communication_service import CommunicationService

    svc = CommunicationService.__new__(CommunicationService)
    db = AsyncMock()

    mock_candidate = MagicMock()
    mock_candidate.channel_opt_out = ["marketing_email"]

    with (
        patch("app.domains.communication.services.communication_service.CommunicationRepository") as MockCommRepo,
        patch("app.domains.communication.services.communication_service.CandidateRepository") as MockCandRepo,
    ):
        MockCommRepo.return_value.get_active_optout = AsyncMock(return_value=None)
        MockCandRepo.return_value.get_by_id        = AsyncMock(return_value=mock_candidate)

        is_opted_out, opt_out_obj = await svc._check_opt_out(
            candidate_id="cand-1",
            company_id="comp-1",
            channel=MessageChannel.EMAIL,
            db=db,
        )

    assert is_opted_out is True
    assert opt_out_obj is None  # legado — sem linha na tabela


@pytest.mark.asyncio
async def test_check_opt_out_respects_whatsapp_jsonb_flag():
    """channel_opt_out=['whatsapp'] → bloqueia WhatsApp."""
    from app.domains.communication.services.communication_service import CommunicationService

    svc = CommunicationService.__new__(CommunicationService)
    db = AsyncMock()

    mock_candidate = MagicMock()
    mock_candidate.channel_opt_out = ["whatsapp"]

    with (
        patch("app.domains.communication.services.communication_service.CommunicationRepository") as MockCommRepo,
        patch("app.domains.communication.services.communication_service.CandidateRepository") as MockCandRepo,
    ):
        MockCommRepo.return_value.get_active_optout = AsyncMock(return_value=None)
        MockCandRepo.return_value.get_by_id        = AsyncMock(return_value=mock_candidate)

        is_opted_out, _ = await svc._check_opt_out(
            candidate_id="cand-1",
            company_id="comp-1",
            channel=MessageChannel.WHATSAPP,
            db=db,
        )

    assert is_opted_out is True


@pytest.mark.asyncio
async def test_check_opt_out_table_takes_priority():
    """CandidateOptOut table tem prioridade — retorna obj real, não consulta JSONB."""
    from app.domains.communication.services.communication_service import CommunicationService

    svc = CommunicationService.__new__(CommunicationService)
    db = AsyncMock()
    real_opt_out = MagicMock()

    with (
        patch("app.domains.communication.services.communication_service.CommunicationRepository") as MockCommRepo,
        patch("app.domains.communication.services.communication_service.CandidateRepository") as MockCandRepo,
    ):
        MockCommRepo.return_value.get_active_optout = AsyncMock(return_value=real_opt_out)

        is_opted_out, obj = await svc._check_opt_out(
            candidate_id="cand-1",
            company_id="comp-1",
            channel=MessageChannel.EMAIL,
            db=db,
        )

    assert is_opted_out is True
    assert obj is real_opt_out
    MockCandRepo.assert_not_called()  # não consulta JSONB quando tabela tem resultado


@pytest.mark.asyncio
async def test_check_opt_out_empty_jsonb_returns_false():
    """Sem opt-out em nenhum lugar → False."""
    from app.domains.communication.services.communication_service import CommunicationService

    svc = CommunicationService.__new__(CommunicationService)
    db = AsyncMock()

    mock_candidate = MagicMock()
    mock_candidate.channel_opt_out = []

    with (
        patch("app.domains.communication.services.communication_service.CommunicationRepository") as MockCommRepo,
        patch("app.domains.communication.services.communication_service.CandidateRepository") as MockCandRepo,
    ):
        MockCommRepo.return_value.get_active_optout = AsyncMock(return_value=None)
        MockCandRepo.return_value.get_by_id        = AsyncMock(return_value=mock_candidate)

        is_opted_out, _ = await svc._check_opt_out(
            candidate_id="cand-1",
            company_id="comp-1",
            channel=MessageChannel.EMAIL,
            db=db,
        )

    assert is_opted_out is False


# ==========================================================================
# GAP B: WhatsApp STOP command
# ==========================================================================

def _make_mock_data_request():
    mock_request = MagicMock()
    mock_request.company_id   = UUID("00000000-0000-0000-0000-000000000002")
    mock_request.candidate_id = UUID("00000000-0000-0000-0000-000000000001")
    mock_request.whatsapp_conversation_state = {"state": "collecting", "phone": "+5511999999999"}
    mock_request.fields_requested = []
    return mock_request


@pytest.mark.asyncio
async def test_whatsapp_stop_records_opt_out():
    """Mensagem 'STOP' aciona record_opt_out(channel=WHATSAPP)."""
    from app.domains.communication.services.data_request_whatsapp_service import DataRequestWhatsAppService

    svc = DataRequestWhatsAppService.__new__(DataRequestWhatsAppService)
    svc.whatsapp_service = AsyncMock()

    db = AsyncMock()
    mock_request  = _make_mock_data_request()
    mock_candidate = MagicMock(); mock_candidate.name = "João"

    from lia_models.data_request import DataRequest
    from lia_models.candidate import Candidate

    async def _fake_get(model, id):
        if model is DataRequest:
            return mock_request
        return mock_candidate

    db.get = _fake_get

    with patch("app.domains.communication.services.data_request_whatsapp_service.CommunicationService") as MockSvc:
        mock_comm_svc = AsyncMock()
        MockSvc.return_value = mock_comm_svc

        result = await svc.process_incoming_message(
            db, UUID("aaaaaaaa-0000-0000-0000-000000000000"), "STOP"
        )

    assert result.get("status") == "opted_out"
    mock_comm_svc.record_opt_out.assert_awaited_once()
    kwargs = mock_comm_svc.record_opt_out.call_args.kwargs
    assert kwargs["channel"] == MessageChannel.WHATSAPP
    assert str(kwargs["candidate_id"]) == "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
@pytest.mark.parametrize("msg", ["stop", "Stop", " STOP ", "PARAR", "parar", "CANCELAR", "SAIR"])
async def test_whatsapp_stop_variants(msg):
    """Todas as variantes de STOP/PARAR/CANCELAR/SAIR acionam opt-out."""
    from app.domains.communication.services.data_request_whatsapp_service import DataRequestWhatsAppService

    svc = DataRequestWhatsAppService.__new__(DataRequestWhatsAppService)
    svc.whatsapp_service = AsyncMock()

    db = AsyncMock()
    mock_request  = _make_mock_data_request()
    mock_candidate = MagicMock(); mock_candidate.name = "João"

    from lia_models.data_request import DataRequest
    from lia_models.candidate import Candidate

    async def _fake_get(model, id):
        if model is DataRequest:
            return mock_request
        return mock_candidate

    db.get = _fake_get

    with patch("app.domains.communication.services.data_request_whatsapp_service.CommunicationService") as MockSvc:
        mock_comm_svc = AsyncMock()
        MockSvc.return_value = mock_comm_svc
        result = await svc.process_incoming_message(db, UUID("aaaaaaaa-0000-0000-0000-000000000000"), msg)

    assert result.get("status") == "opted_out"
    mock_comm_svc.record_opt_out.assert_awaited_once()


@pytest.mark.asyncio
async def test_whatsapp_status_does_not_trigger_opt_out():
    """STATUS não aciona opt-out."""
    from app.domains.communication.services.data_request_whatsapp_service import DataRequestWhatsAppService

    svc = DataRequestWhatsAppService.__new__(DataRequestWhatsAppService)
    svc.whatsapp_service = AsyncMock()

    db = AsyncMock()
    mock_request  = _make_mock_data_request()
    mock_candidate = MagicMock(); mock_candidate.name = "João"

    from lia_models.data_request import DataRequest
    from lia_models.candidate import Candidate

    async def _fake_get(model, id):
        if model is DataRequest:
            return mock_request
        return mock_candidate

    db.get = _fake_get

    with patch.object(svc, "_send_status_message", new_callable=AsyncMock, return_value={"success": True}), \
         patch("app.domains.communication.services.data_request_whatsapp_service.CommunicationService") as MockSvc:
        mock_comm_svc = AsyncMock()
        MockSvc.return_value = mock_comm_svc
        await svc.process_incoming_message(db, UUID("aaaaaaaa-0000-0000-0000-000000000000"), "STATUS")

    mock_comm_svc.record_opt_out.assert_not_awaited()
