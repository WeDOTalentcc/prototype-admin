"""
Coverage tests for app/domains/automation/services/automation_handlers.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


# ── validate_multi_tenancy ───────────────────────────────────────────────────

class TestValidateMultiTenancy:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_valid(self, mock_db):
        from app.domains.automation.services.automation_handlers import validate_multi_tenancy
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = MagicMock()  # vacancy found
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = MagicMock()  # candidate found
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        valid, msg = await validate_multi_tenancy(mock_db, "cand-1", "vac-1", "comp-1")
        assert valid is True
        assert msg == ""

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_vacancy_not_found(self, mock_db):
        from app.domains.automation.services.automation_handlers import validate_multi_tenancy
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        valid, msg = await validate_multi_tenancy(mock_db, "cand-1", "vac-1", "comp-1")
        assert valid is False
        assert "Vacancy" in msg

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_candidate_not_found(self, mock_db):
        from app.domains.automation.services.automation_handlers import validate_multi_tenancy
        mock_result1 = MagicMock()
        mock_result1.scalar_one_or_none.return_value = MagicMock()
        mock_result2 = MagicMock()
        mock_result2.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [mock_result1, mock_result2]

        valid, msg = await validate_multi_tenancy(mock_db, "cand-1", "vac-1", "comp-1")
        assert valid is False
        assert "Candidate" in msg


# ── handler functions (mock all deps) ────────────────────────────────────────

class TestHandlerFunctions:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_screening_completed_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_screening_completed
        with patch("app.domains.automation.services.automation_handlers.select") as mock_sel:
            mock_db.execute.side_effect = Exception("DB error")
            result = await handle_screening_completed("c1", "v1", "comp-1", mock_db, passed=True)
        assert "cascade_errors" in result
        assert len(result["cascade_errors"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_interview_scheduled_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_interview_scheduled
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_interview_scheduled("c1", "v1", "comp-1", mock_db, interview_datetime="2025-01-15T10:00")
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_interview_completed_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_interview_completed
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_interview_completed("c1", "v1", "comp-1", mock_db)
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_candidate_inactive_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_candidate_inactive
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_candidate_inactive("c1", "v1", "comp-1", mock_db)
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_candidate_no_show_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_candidate_no_show
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_candidate_no_show("c1", "v1", "comp-1", mock_db)
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_offer_sent_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_offer_sent
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_offer_sent("c1", "v1", "comp-1", mock_db)
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_candidate_hired_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_candidate_hired
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_candidate_hired("c1", "v1", "comp-1", mock_db)
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_candidate_rejected_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_candidate_rejected
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_candidate_rejected("c1", "v1", "comp-1", mock_db, reason="No fit")
        assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_handle_ats_sync_error(self, mock_db):
        from app.domains.automation.services.automation_handlers import handle_ats_sync
        with patch("app.domains.analytics.services.activity_service.ActivityService") as MockAS:
            MockAS.return_value.create_activity = AsyncMock(side_effect=Exception("fail"))
            result = await handle_ats_sync("c1", "v1", "comp-1", mock_db)
        assert "error" in result


# ── register_all_handlers ────────────────────────────────────────────────────

class TestRegisterHandlers:
    @pytest.mark.easy
    def test_register_all(self):
        with patch("app.domains.automation.services.automation_handlers.stage_automation_engine", create=True) as mock_engine, \
             patch("app.domains.automation.services.stage_automation_engine.stage_automation_engine", mock_engine):
            from app.domains.automation.services.automation_handlers import register_all_handlers
            register_all_handlers()
            assert mock_engine.register_handler.call_count >= 10
