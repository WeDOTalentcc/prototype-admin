"""
Unit tests for AutomationService — targeting app/domains/automation/services/automation_service.py.
Covers: evaluate_conditions, execute_action, trigger_automation, CRUD operations, get_ai_suggestions.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from uuid import uuid4


# ---------------------------------------------------------------------------
# evaluate_conditions — pure logic, no I/O
# ---------------------------------------------------------------------------

class TestEvaluateConditions:
    """Test condition evaluation logic (the core rule engine)."""

    @pytest.fixture
    def service(self):
        with patch("app.domains.automation.services.automation_service.NotificationService"):
            from app.domains.automation.services.automation_service import AutomationService
            return AutomationService()

    @pytest.mark.asyncio
    async def test_empty_conditions_returns_true(self, service):
        result = await service.evaluate_conditions([], {"stage": "interview"})
        assert result is True

    @pytest.mark.asyncio
    async def test_equals_condition_match(self, service):
        conditions = [{"field": "stage", "operator": "equals", "value": "interview"}]
        assert await service.evaluate_conditions(conditions, {"stage": "interview"}) is True

    @pytest.mark.asyncio
    async def test_equals_condition_mismatch(self, service):
        conditions = [{"field": "stage", "operator": "equals", "value": "interview"}]
        assert await service.evaluate_conditions(conditions, {"stage": "screening"}) is False

    @pytest.mark.asyncio
    async def test_not_equals_condition(self, service):
        conditions = [{"field": "stage", "operator": "not_equals", "value": "rejected"}]
        assert await service.evaluate_conditions(conditions, {"stage": "interview"}) is True
        assert await service.evaluate_conditions(conditions, {"stage": "rejected"}) is False

    @pytest.mark.asyncio
    async def test_contains_condition(self, service):
        conditions = [{"field": "name", "operator": "contains", "value": "Silva"}]
        assert await service.evaluate_conditions(conditions, {"name": "João Silva"}) is True
        assert await service.evaluate_conditions(conditions, {"name": "João Santos"}) is False

    @pytest.mark.asyncio
    async def test_not_contains_condition(self, service):
        conditions = [{"field": "name", "operator": "not_contains", "value": "teste"}]
        assert await service.evaluate_conditions(conditions, {"name": "João Silva"}) is True

    @pytest.mark.asyncio
    async def test_in_condition(self, service):
        conditions = [{"field": "stage", "operator": "in", "value": ["interview", "offer"]}]
        assert await service.evaluate_conditions(conditions, {"stage": "interview"}) is True
        assert await service.evaluate_conditions(conditions, {"stage": "rejected"}) is False

    @pytest.mark.asyncio
    async def test_not_in_condition(self, service):
        conditions = [{"field": "stage", "operator": "not_in", "value": ["rejected", "withdrawn"]}]
        assert await service.evaluate_conditions(conditions, {"stage": "interview"}) is True
        assert await service.evaluate_conditions(conditions, {"stage": "rejected"}) is False

    @pytest.mark.asyncio
    async def test_greater_than_condition(self, service):
        conditions = [{"field": "score", "operator": "greater_than", "value": 70}]
        assert await service.evaluate_conditions(conditions, {"score": 85}) is True
        assert await service.evaluate_conditions(conditions, {"score": 50}) is False

    @pytest.mark.asyncio
    async def test_less_than_condition(self, service):
        conditions = [{"field": "score", "operator": "less_than", "value": 40}]
        assert await service.evaluate_conditions(conditions, {"score": 30}) is True
        assert await service.evaluate_conditions(conditions, {"score": 50}) is False

    @pytest.mark.asyncio
    async def test_exists_condition(self, service):
        conditions = [{"field": "email", "operator": "exists", "value": None}]
        assert await service.evaluate_conditions(conditions, {"email": "a@b.com"}) is True
        assert await service.evaluate_conditions(conditions, {"email": None}) is False

    @pytest.mark.asyncio
    async def test_not_exists_condition(self, service):
        conditions = [{"field": "phone", "operator": "not_exists", "value": None}]
        assert await service.evaluate_conditions(conditions, {"phone": None}) is True
        assert await service.evaluate_conditions(conditions, {"phone": "123"}) is False

    @pytest.mark.asyncio
    async def test_multiple_conditions_all_must_pass(self, service):
        conditions = [
            {"field": "stage", "operator": "equals", "value": "interview"},
            {"field": "score", "operator": "greater_than", "value": 70},
        ]
        assert await service.evaluate_conditions(conditions, {"stage": "interview", "score": 85}) is True
        assert await service.evaluate_conditions(conditions, {"stage": "interview", "score": 50}) is False

    @pytest.mark.asyncio
    async def test_condition_without_field_is_skipped(self, service):
        conditions = [{"operator": "equals", "value": "x"}]
        assert await service.evaluate_conditions(conditions, {"x": "y"}) is True

    @pytest.mark.asyncio
    async def test_greater_than_with_invalid_value(self, service):
        conditions = [{"field": "score", "operator": "greater_than", "value": 70}]
        assert await service.evaluate_conditions(conditions, {"score": "not_a_number"}) is False


# ---------------------------------------------------------------------------
# execute_action — test dispatch to action handlers
# ---------------------------------------------------------------------------

class TestExecuteAction:
    @pytest.fixture
    def service(self):
        with patch("app.domains.automation.services.automation_service.NotificationService"):
            from app.domains.automation.services.automation_service import AutomationService
            svc = AutomationService()
            return svc

    @pytest.mark.asyncio
    async def test_execute_action_unknown_type(self, service):
        db = AsyncMock()
        result = await service.execute_action(
            "unknown_action", {}, {"candidate_id": None}, "comp-1", db
        )
        assert result["status"] == "unknown_action"

    @pytest.mark.asyncio
    async def test_execute_action_send_email(self, service):
        db = AsyncMock()
        mock_email_svc = AsyncMock()
        mock_email_svc.send_email = AsyncMock(return_value={"success": True, "message_id": "m1"})

        with patch.object(type(service), "email_service", new_callable=PropertyMock, return_value=mock_email_svc):
            result = await service.execute_action(
                "send_email",
                {"template_id": "t1", "subject": "Hello"},
                {"candidate_email": "a@b.com", "candidate_name": "Test"},
                "comp-1",
                db,
            )
            assert result.get("action") == "send_email"

    @pytest.mark.asyncio
    async def test_execute_action_log_activity(self, service):
        db = AsyncMock()
        result = await service.execute_action(
            "log_activity",
            {"message": "Test log"},
            {"candidate_id": "c1"},
            "comp-1",
            db,
        )
        assert result.get("action") == "log_activity"

    @pytest.mark.asyncio
    async def test_execute_action_skips_missing_candidate(self, service):
        db = AsyncMock()
        with patch.object(service, "_validate_candidate_exists", new_callable=AsyncMock, return_value=False):
            result = await service.execute_action(
                "send_email", {}, {"candidate_id": "missing-id"}, "comp-1", db
            )
            assert result["status"] == "skipped"
            assert result["reason"] == "candidate_not_found"

    @pytest.mark.asyncio
    async def test_execute_action_skips_missing_vacancy(self, service):
        db = AsyncMock()
        with patch.object(service, "_validate_candidate_exists", new_callable=AsyncMock, return_value=True):
            with patch.object(service, "_validate_vacancy_exists", new_callable=AsyncMock, return_value=False):
                result = await service.execute_action(
                    "send_email", {}, {"candidate_id": "c1", "vacancy_id": "bad-v"}, "comp-1", db
                )
                assert result["status"] == "skipped"
                assert result["reason"] == "vacancy_not_found"


# ---------------------------------------------------------------------------
# trigger_automation — integration of conditions + actions
# ---------------------------------------------------------------------------

class TestTriggerAutomation:
    @pytest.fixture
    def service(self):
        with patch("app.domains.automation.services.automation_service.NotificationService"):
            from app.domains.automation.services.automation_service import AutomationService
            return AutomationService()

    @pytest.mark.asyncio
    async def test_trigger_with_no_matching_automations(self, service):
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.close = AsyncMock()

        with patch("app.domains.automation.services.automation_service.AsyncSessionLocal", return_value=mock_db):
            result = await service.trigger_automation(
                "candidate_stage_changed",
                {"candidate_id": "c1", "stage": "interview"},
                "comp-1",
            )
            assert result["automations_executed"] == 0

    @pytest.mark.asyncio
    async def test_trigger_with_conditions_not_met(self, service):
        mock_automation = MagicMock()
        mock_automation.id = uuid4()
        mock_automation.name = "Auto 1"
        mock_automation.conditions = [{"field": "stage", "operator": "equals", "value": "offer"}]
        mock_automation.action_type = "send_email"
        mock_automation.action_config = {}

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_automation]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.close = AsyncMock()

        with patch.object(service, "_check_cooldown", new_callable=AsyncMock, return_value=True):
            with patch("app.domains.automation.services.automation_service.AsyncSessionLocal", return_value=mock_db):
                result = await service.trigger_automation(
                    "candidate_stage_changed",
                    {"candidate_id": "c1", "stage": "interview"},
                    "comp-1",
                )
                assert result["automations_skipped"] == 1
                assert result["details"]["skipped"][0]["reason"] == "conditions_not_met"

    @pytest.mark.asyncio
    async def test_trigger_with_cooldown_active(self, service):
        mock_automation = MagicMock()
        mock_automation.id = uuid4()
        mock_automation.name = "Auto 1"
        mock_automation.conditions = []
        mock_automation.action_type = "send_email"

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_automation]
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()
        mock_db.close = AsyncMock()

        with patch.object(service, "_check_cooldown", new_callable=AsyncMock, return_value=False):
            with patch("app.domains.automation.services.automation_service.AsyncSessionLocal", return_value=mock_db):
                result = await service.trigger_automation(
                    "candidate_stage_changed",
                    {"candidate_id": "c1"},
                    "comp-1",
                )
                assert result["automations_skipped"] == 1
                assert result["details"]["skipped"][0]["reason"] == "cooldown_active"


# ---------------------------------------------------------------------------
# get_ai_suggestions — test the AI suggestion generator
# ---------------------------------------------------------------------------

class TestGetAiSuggestions:
    @pytest.fixture
    def service(self):
        with patch("app.domains.automation.services.automation_service.NotificationService"):
            from app.domains.automation.services.automation_service import AutomationService
            return AutomationService()

    def test_returns_suggestions_list(self, service):
        result = service.get_ai_suggestions(
            transition_data={"from_stage": "screening", "to_stage": "interview"},
        )
        assert isinstance(result, list)
        # Each suggestion should be a dict with known keys
        if result:
            suggestion = result[0]
            assert "name" in suggestion or "description" in suggestion or "trigger_type" in suggestion


# ---------------------------------------------------------------------------
# Validate candidate/vacancy helpers
# ---------------------------------------------------------------------------

class TestValidationHelpers:
    @pytest.fixture
    def service(self):
        with patch("app.domains.automation.services.automation_service.NotificationService"):
            from app.domains.automation.services.automation_service import AutomationService
            return AutomationService()

    @pytest.mark.asyncio
    async def test_validate_candidate_with_none_returns_true(self, service):
        db = AsyncMock()
        assert await service._validate_candidate_exists(None, db) is True

    @pytest.mark.asyncio
    async def test_validate_vacancy_with_none_returns_true(self, service):
        db = AsyncMock()
        assert await service._validate_vacancy_exists(None, db) is True

    @pytest.mark.asyncio
    async def test_validate_candidate_db_error_returns_false(self, service):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("DB down"))
        assert await service._validate_candidate_exists("c1", db) is False

    @pytest.mark.asyncio
    async def test_validate_vacancy_db_error_returns_false(self, service):
        db = AsyncMock()
        db.execute = AsyncMock(side_effect=Exception("DB down"))
        assert await service._validate_vacancy_exists("v1", db) is False
