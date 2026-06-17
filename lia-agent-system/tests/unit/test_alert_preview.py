"""Testes do endpoint de preview de alertas por vaga."""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_preview_new_candidate_returns_count():
    """Preview para new_candidate retorna contagem de candidatos recentes."""
    from app.api.v1.vacancy_alerts import preview_alert

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 7
    mock_db.execute.return_value = mock_result

    result = await preview_alert(
        alert_type="new_candidate",
        vacancy_id="vac-1",
        db=mock_db,
        company_id="co-1",
    )

    assert result["alert_type"] == "new_candidate"
    assert result["preview_count"] == 7
    assert "description" in result


@pytest.mark.asyncio
async def test_preview_screening_complete_returns_count():
    """Preview para screening_complete retorna contagem."""
    from app.api.v1.vacancy_alerts import preview_alert

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 3
    mock_db.execute.return_value = mock_result

    result = await preview_alert(
        alert_type="screening_complete",
        vacancy_id="vac-1",
        db=mock_db,
        company_id="co-1",
    )

    assert result["alert_type"] == "screening_complete"
    assert result["preview_count"] == 3


@pytest.mark.asyncio
async def test_preview_stage_change_returns_count():
    """Preview para stage_change retorna contagem."""
    from app.api.v1.vacancy_alerts import preview_alert

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 12
    mock_db.execute.return_value = mock_result

    result = await preview_alert(
        alert_type="stage_change",
        vacancy_id="vac-1",
        db=mock_db,
        company_id="co-1",
    )

    assert result["alert_type"] == "stage_change"
    assert result["preview_count"] == 12


@pytest.mark.asyncio
async def test_preview_unknown_type_returns_zero():
    """Preview para tipo desconhecido retorna count 0 sem erro."""
    from app.api.v1.vacancy_alerts import preview_alert

    mock_db = AsyncMock()

    result = await preview_alert(
        alert_type="unknown_type",
        vacancy_id=None,
        db=mock_db,
        company_id="co-1",
    )

    assert result["preview_count"] == 0
    assert result["alert_type"] == "unknown_type"


@pytest.mark.asyncio
async def test_preview_none_vacancy_id_queries_all():
    """Preview sem vacancy_id retorna contagem global da company."""
    from app.api.v1.vacancy_alerts import preview_alert

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar.return_value = 20
    mock_db.execute.return_value = mock_result

    result = await preview_alert(
        alert_type="new_candidate",
        vacancy_id=None,
        db=mock_db,
        company_id="co-1",
    )

    assert result["preview_count"] == 20
