"""
TDD — P2-FASE4: data_fields auto_collect trigger no pipeline.

Verifica que check_data_request_triggers cria DataRequest automaticamente
quando um campo com auto_collect=True existe no RecruitmentStage e nenhum
DataRequestTemplate está configurado para o stage.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


COMPANY_ID = str(uuid.uuid4())
CANDIDATE_ID = str(uuid.uuid4())
VACANCY_ID = str(uuid.uuid4())
STAGE_NAME = "Entrevista RH"


def _make_stage(data_fields=None):
    s = MagicMock()
    s.name = STAGE_NAME
    s.data_fields = data_fields or []
    return s


def _make_data_request():
    dr = MagicMock()
    dr.id = uuid.uuid4()
    dr.token = "tok_abc"
    return dr


@pytest.mark.asyncio
async def test_fase4_creates_request_for_auto_collect_field():
    """Quando stage tem campo auto_collect=True e sem template, cria DataRequest."""
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    svc = PipelineStageService.__new__(PipelineStageService)

    data_fields = [
        {"id": "cpf", "displayName": "CPF", "category": "document", "required": True, "auto_collect": True},
    ]
    stage = _make_stage(data_fields)
    dr = _make_data_request()

    mock_drs = MagicMock()
    mock_drs.get_trigger_fields_for_stage = AsyncMock(return_value=None)
    mock_drs.check_existing_pending_request = AsyncMock(return_value=False)
    mock_drs.create_data_request = AsyncMock(return_value=dr)
    mock_drs.send_notification = AsyncMock(return_value=None)

    mock_stages = AsyncMock(return_value=[stage])

    with (
        patch.object(type(svc), "data_request_service", new_callable=lambda: property(lambda self: mock_drs)),
        patch.object(PipelineStageService, "_get_company_stages", mock_stages),
        patch("app.domains.recruiter_assistant.services.pipeline_stage_service.AsyncSessionLocal") as mock_sl,
    ):
        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=None)
        mock_sl.return_value = mock_db

        result = await svc.check_data_request_triggers(
            candidate_id=CANDIDATE_ID,
            new_stage=STAGE_NAME,
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
        )

    assert result is not None
    assert result["triggered"] is True
    assert result["source"] == "data_fields_auto_collect"
    assert result["fields_count"] == 1
    assert result["is_blocking"] is True  # campo required=True → is_blocking


@pytest.mark.asyncio
async def test_fase4_ignores_fields_without_auto_collect():
    """Campos com auto_collect=False não disparam DataRequest."""
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    svc = PipelineStageService.__new__(PipelineStageService)

    data_fields = [
        {"id": "address", "displayName": "Endereço", "category": "basic", "required": False, "auto_collect": False},
    ]
    stage = _make_stage(data_fields)

    mock_drs = MagicMock()
    mock_drs.get_trigger_fields_for_stage = AsyncMock(return_value=None)
    mock_drs.create_data_request = AsyncMock()

    with (
        patch.object(type(svc), "data_request_service", new_callable=lambda: property(lambda self: mock_drs)),
        patch.object(PipelineStageService, "_get_company_stages", AsyncMock(return_value=[stage])),
        patch("app.domains.recruiter_assistant.services.pipeline_stage_service.AsyncSessionLocal") as mock_sl,
    ):
        mock_sl.return_value = AsyncMock()

        result = await svc.check_data_request_triggers(
            candidate_id=CANDIDATE_ID,
            new_stage=STAGE_NAME,
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
        )

    assert result is None
    mock_drs.create_data_request.assert_not_called()


@pytest.mark.asyncio
async def test_fase4_skips_when_pending_request_exists():
    """Se já existe DataRequest pendente, não cria duplicata."""
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    svc = PipelineStageService.__new__(PipelineStageService)

    data_fields = [
        {"id": "cpf", "displayName": "CPF", "category": "document", "required": True, "auto_collect": True},
    ]
    stage = _make_stage(data_fields)

    mock_drs = MagicMock()
    mock_drs.get_trigger_fields_for_stage = AsyncMock(return_value=None)
    mock_drs.check_existing_pending_request = AsyncMock(return_value=True)  # já existe
    mock_drs.create_data_request = AsyncMock()

    with (
        patch.object(type(svc), "data_request_service", new_callable=lambda: property(lambda self: mock_drs)),
        patch.object(PipelineStageService, "_get_company_stages", AsyncMock(return_value=[stage])),
        patch("app.domains.recruiter_assistant.services.pipeline_stage_service.AsyncSessionLocal") as mock_sl,
    ):
        mock_sl.return_value = AsyncMock()

        result = await svc.check_data_request_triggers(
            candidate_id=CANDIDATE_ID,
            new_stage=STAGE_NAME,
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
        )

    assert result is not None
    assert result["triggered"] is False
    assert result["reason"] == "pending_request_exists"
    mock_drs.create_data_request.assert_not_called()


@pytest.mark.asyncio
async def test_fase4_defers_to_template_when_available():
    """Quando template existe (sistema A), P2-FASE4 não entra — sem chamar _get_company_stages."""
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    svc = PipelineStageService.__new__(PipelineStageService)

    template_config = {
        "source": "data_request_template",
        "fields": ["rg", "cpf"],
        "is_blocking": False,
        "trigger_type": "stage_entry",
        "template_id": str(uuid.uuid4()),
    }

    mock_drs = MagicMock()
    mock_drs.get_trigger_fields_for_stage = AsyncMock(return_value=template_config)
    mock_drs.check_existing_pending_request = AsyncMock(return_value=False)
    dr = _make_data_request()
    mock_drs.create_data_request = AsyncMock(return_value=dr)
    mock_drs.send_notification = AsyncMock(return_value=None)

    mock_get_stages = AsyncMock(return_value=[])

    with (
        patch.object(type(svc), "data_request_service", new_callable=lambda: property(lambda self: mock_drs)),
        patch.object(PipelineStageService, "_get_company_stages", mock_get_stages),
        patch("app.domains.recruiter_assistant.services.pipeline_stage_service.AsyncSessionLocal") as mock_sl,
    ):
        mock_sl.return_value = AsyncMock()

        result = await svc.check_data_request_triggers(
            candidate_id=CANDIDATE_ID,
            new_stage=STAGE_NAME,
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
        )

    assert result is not None
    assert result["triggered"] is True
    # P2-FASE4 não é invocado quando template existe
    mock_get_stages.assert_not_called()


@pytest.mark.asyncio
async def test_fase4_returns_none_when_stage_not_found():
    """Stage não encontrado na empresa → None (sem crash)."""
    from app.domains.recruiter_assistant.services.pipeline_stage_service import PipelineStageService

    svc = PipelineStageService.__new__(PipelineStageService)

    mock_drs = MagicMock()
    mock_drs.get_trigger_fields_for_stage = AsyncMock(return_value=None)

    with (
        patch.object(type(svc), "data_request_service", new_callable=lambda: property(lambda self: mock_drs)),
        patch.object(PipelineStageService, "_get_company_stages", AsyncMock(return_value=[])),
        patch("app.domains.recruiter_assistant.services.pipeline_stage_service.AsyncSessionLocal") as mock_sl,
    ):
        mock_sl.return_value = AsyncMock()

        result = await svc.check_data_request_triggers(
            candidate_id=CANDIDATE_ID,
            new_stage="stage_inexistente",
            vacancy_id=VACANCY_ID,
            company_id=COMPANY_ID,
        )

    assert result is None
