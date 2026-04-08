"""
Coverage tests for wizard_step_service package and standalone file.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSharedConstants:
    @pytest.mark.easy
    def test_wizard_stages(self):
        from app.domains.job_management.services.wizard_step_service._shared import WIZARD_STAGES
        assert len(WIZARD_STAGES) == 10
        assert WIZARD_STAGES[0]["stage"] == 1
        assert WIZARD_STAGES[0]["name"] == "description"
        assert WIZARD_STAGES[-1]["stage"] == 10
        for stage in WIZARD_STAGES:
            assert "stage" in stage
            assert "name" in stage
            assert "panel" in stage

    @pytest.mark.easy
    def test_use_enhanced_classifier(self):
        from app.domains.job_management.services.wizard_step_service._shared import USE_ENHANCED_CLASSIFIER
        assert USE_ENHANCED_CLASSIFIER is True

    @pytest.mark.easy
    def test_re_exported_helpers(self):
        from app.domains.job_management.services.wizard_step_service._shared import (
            QuestionType, detect_question_type, record_field_history,
        )
        assert QuestionType is not None
        assert callable(detect_question_type)

    @pytest.mark.easy
    def test_import_service_class(self):
        from app.domains.job_management.services.wizard_step_service import WizardStepService
        svc = WizardStepService()
        assert hasattr(svc, "process")


class TestSharedHelpers:
    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_historical_job_patterns_no_data(self):
        from app.domains.job_management.services.wizard_step_service._shared import get_historical_job_patterns
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result
        result = await get_historical_job_patterns(mock_db, "comp-1")
        assert isinstance(result, dict)
        assert len(result) == 0

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_historical_job_patterns_with_data(self):
        from app.domains.job_management.services.wizard_step_service._shared import get_historical_job_patterns
        mock_db = AsyncMock()
        row = MagicMock()
        row.count = 5
        row.work_model = "remote"
        row.employment_type = "CLT"
        row.location = "SP"
        mock_result = MagicMock()
        mock_result.first.return_value = row
        mock_total = MagicMock()
        mock_total.scalar.return_value = 10
        mock_db.execute.side_effect = [mock_result, mock_total, mock_result, mock_total, mock_result, mock_total]
        result = await get_historical_job_patterns(mock_db, "comp-1")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    @pytest.mark.easy
    async def test_get_historical_salary_patterns_no_data(self):
        from app.domains.job_management.services.wizard_step_service._shared import get_historical_salary_patterns
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute.return_value = mock_result
        result = await get_historical_salary_patterns(mock_db, "comp-1", "Dev", "Senior")
        assert isinstance(result, dict)


# ── Stage modules (import to cover module-level code) ────────────────────────

class TestStageModuleImports:
    @pytest.mark.easy
    def test_import_stage_description(self):
        import app.domains.job_management.services.wizard_step_service.stage_description as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_basic_info(self):
        import app.domains.job_management.services.wizard_step_service.stage_basic_info as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_competencies(self):
        import app.domains.job_management.services.wizard_step_service.stage_competencies as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_salary(self):
        import app.domains.job_management.services.wizard_step_service.stage_salary as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_wsi(self):
        import app.domains.job_management.services.wizard_step_service.stage_wsi as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_review(self):
        import app.domains.job_management.services.wizard_step_service.stage_review as mod
        assert mod is not None

    @pytest.mark.easy
    def test_import_stage_publication(self):
        import app.domains.job_management.services.wizard_step_service.stage_publication as mod
        assert mod is not None
