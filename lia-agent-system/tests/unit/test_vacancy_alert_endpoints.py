"""Testes dos endpoints de alertas por vaga."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_get_preferences_returns_empty_list():
    """GET preferences retorna lista vazia quando nenhuma config existe."""
    from app.api.v1.vacancy_alerts import get_vacancy_alert_preferences

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_result

    with patch("app.api.v1.vacancy_alerts.select"):
        result = await get_vacancy_alert_preferences(
            vacancy_id="vac-1",
            user_id="user-1",
            db=mock_db,
            company_id="co-1",
        )

    assert result["preferences"] == []
    assert result["vacancy_id"] == "vac-1"
    assert result["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_get_preferences_returns_existing_configs():
    """GET preferences retorna configs existentes."""
    from app.api.v1.vacancy_alerts import get_vacancy_alert_preferences

    mock_db = AsyncMock()
    fake_config = MagicMock(alert_type="new_candidate", frequency="weekly")
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_config]
    mock_db.execute.return_value = mock_result

    with patch("app.api.v1.vacancy_alerts.select"):
        result = await get_vacancy_alert_preferences(
            vacancy_id="vac-1",
            user_id="user-1",
            db=mock_db,
            company_id="co-1",
        )

    assert len(result["preferences"]) == 1
    assert result["preferences"][0]["alert_type"] == "new_candidate"
    assert result["preferences"][0]["frequency"] == "weekly"


@pytest.mark.asyncio
async def test_update_preferences_inserts_new():
    """PUT preferences chama db.add quando entrada nao existe."""
    from app.api.v1.vacancy_alerts import update_vacancy_alert_preferences, VacancyAlertPreferencesRequest

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    payload = VacancyAlertPreferencesRequest(
        preferences=[{"alert_type": "new_candidate", "frequency": "weekly"}]
    )

    with patch("app.api.v1.vacancy_alerts.select"):
        result = await update_vacancy_alert_preferences(
            vacancy_id="vac-1",
            payload=payload,
            user_id="user-1",
            db=mock_db,
            company_id="co-1",
        )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    assert result["updated"] == 1
    assert result["status"] == "ok"


@pytest.mark.asyncio
async def test_update_preferences_updates_existing():
    """PUT preferences atualiza frequencia quando config ja existe."""
    from app.api.v1.vacancy_alerts import update_vacancy_alert_preferences, VacancyAlertPreferencesRequest

    mock_db = AsyncMock()
    existing_config = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_config
    mock_db.execute.return_value = mock_result

    payload = VacancyAlertPreferencesRequest(
        preferences=[{"alert_type": "new_candidate", "frequency": "off"}]
    )

    with patch("app.api.v1.vacancy_alerts.select"):
        result = await update_vacancy_alert_preferences(
            vacancy_id="vac-1",
            payload=payload,
            user_id="user-1",
            db=mock_db,
            company_id="co-1",
        )

    assert existing_config.frequency == "off"
    mock_db.add.assert_not_called()
    mock_db.commit.assert_called_once()
    assert result["updated"] == 1
