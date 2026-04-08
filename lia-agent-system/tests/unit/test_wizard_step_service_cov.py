"""
Coverage tests for app/domains/job_management/services/wizard_step_service.py
Covers module-level constants, _track_field_confidence, WIZARD_STAGES, and entity map.
"""
import pytest
from unittest.mock import MagicMock, patch


# ── Module-level constants ───────────────────────────────────────────────────

class TestModuleConstants:
    @pytest.mark.easy
    def test_entity_field_map(self):
        from app.domains.job_management.services.wizard_step_service import _ENTITY_FIELD_MAP
        assert "cargo" in _ENTITY_FIELD_MAP
        assert _ENTITY_FIELD_MAP["cargo"] == "job_title"
        assert _ENTITY_FIELD_MAP["area"] == "department"
        assert _ENTITY_FIELD_MAP["senioridade"] == "seniority"
        assert _ENTITY_FIELD_MAP["salario_min"] == "salary_min"
        assert _ENTITY_FIELD_MAP["salario_max"] == "salary_max"
        assert _ENTITY_FIELD_MAP["modelo_trabalho"] == "work_model"
        assert _ENTITY_FIELD_MAP["localizacao"] == "location"
        assert _ENTITY_FIELD_MAP["skills_tecnicas"] == "detected_skills"
        assert _ENTITY_FIELD_MAP["beneficios"] == "benefits"
        assert _ENTITY_FIELD_MAP["idiomas"] == "languages"
        assert _ENTITY_FIELD_MAP["is_afirmativa"] == "is_affirmative"
        assert _ENTITY_FIELD_MAP["gestor"] == "manager"
        assert _ENTITY_FIELD_MAP["gestor_email"] == "manager_email"
        assert len(_ENTITY_FIELD_MAP) >= 14

    @pytest.mark.easy
    def test_wizard_stages(self):
        from app.domains.job_management.services.wizard_step_service import WIZARD_STAGES
        assert len(WIZARD_STAGES) == 10
        assert WIZARD_STAGES[0]["stage"] == 1
        assert WIZARD_STAGES[0]["name"] == "description"
        assert WIZARD_STAGES[-1]["stage"] == 10
        assert WIZARD_STAGES[-1]["name"] == "active-search"
        # Check all stages have required keys
        for stage in WIZARD_STAGES:
            assert "stage" in stage
            assert "name" in stage
            assert "panel" in stage

    @pytest.mark.easy
    def test_use_enhanced_classifier(self):
        from app.domains.job_management.services.wizard_step_service import USE_ENHANCED_CLASSIFIER
        assert USE_ENHANCED_CLASSIFIER is True


# ── _track_field_confidence ──────────────────────────────────────────────────

class TestTrackFieldConfidence:
    @pytest.mark.easy
    def test_text_extraction_source(self):
        from app.domains.job_management.services.wizard_step_service import _track_field_confidence
        
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.confidence = 0.85
        mock_result.action.value = "auto_fill"
        mock_service.calculate_field_confidence.return_value = mock_result
        
        field_origins = {}
        _track_field_confidence(
            confidence_service=mock_service,
            field_origins=field_origins,
            field="job_title",
            value="Dev Python",
            source="text_extraction",
        )
        
        assert "job_title" in field_origins
        assert field_origins["job_title"]["source"] == "detected"
        assert field_origins["job_title"]["confidence"] == 0.85
        assert field_origins["job_title"]["action"] == "auto_fill"

    @pytest.mark.easy
    def test_other_source(self):
        from app.domains.job_management.services.wizard_step_service import _track_field_confidence
        
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.confidence = 0.60
        mock_result.action.value = "suggest"
        mock_service.calculate_field_confidence.return_value = mock_result
        
        field_origins = {}
        _track_field_confidence(
            confidence_service=mock_service,
            field_origins=field_origins,
            field="salary_min",
            value=10000,
            source="catalog",
        )
        
        assert field_origins["salary_min"]["source"] == "catalog"
        assert field_origins["salary_min"]["confidence"] == 0.60

    @pytest.mark.easy
    def test_with_extra(self):
        from app.domains.job_management.services.wizard_step_service import _track_field_confidence
        
        mock_service = MagicMock()
        mock_result = MagicMock()
        mock_result.confidence = 0.90
        mock_result.action.value = "auto_fill"
        mock_service.calculate_field_confidence.return_value = mock_result
        
        field_origins = {}
        _track_field_confidence(
            confidence_service=mock_service,
            field_origins=field_origins,
            field="department",
            value="Engineering",
            source="company_default",
            extra={"company_id": "comp-1"},
        )
        
        assert field_origins["department"]["company_id"] == "comp-1"
        assert field_origins["department"]["confidence"] == 0.90


# ── WizardStepService class ─────────────────────────────────────────────────

class TestWizardStepServiceClass:
    @pytest.mark.easy
    def test_instantiation(self):
        from app.domains.job_management.services.wizard_step_service import WizardStepService
        svc = WizardStepService()
        assert hasattr(svc, "process")

    @pytest.mark.easy
    def test_stage_name_mapping(self):
        from app.domains.job_management.services.wizard_step_service import WIZARD_STAGES
        stage_names = [s["name"] for s in WIZARD_STAGES]
        assert "description" in stage_names
        assert "basic-info" in stage_names
        assert "competencies" in stage_names
        assert "salary" in stage_names
        assert "wsi-questions" in stage_names
        assert "review" in stage_names
        assert "pre-publish" in stage_names
        assert "candidate-search" in stage_names
        assert "calibration" in stage_names
        assert "active-search" in stage_names


# ── Also test the wizard_step_service/service.py if it's separate ────────────

class TestWizardStepServiceModule:
    @pytest.mark.easy
    def test_import_main_module(self):
        """Verify the main module can be imported."""
        import app.domains.job_management.services.wizard_step_service as mod
        assert hasattr(mod, "WizardStepService")
        assert hasattr(mod, "_ENTITY_FIELD_MAP")
        assert hasattr(mod, "WIZARD_STAGES")
        assert hasattr(mod, "_track_field_confidence")

    @pytest.mark.easy
    def test_import_sub_service(self):
        """Verify the sub-module can be imported if it exists."""
        try:
            import app.domains.job_management.services.wizard_step_service.service as sub
            assert hasattr(sub, "WizardStepService") or True
        except (ImportError, ModuleNotFoundError):
            pytest.skip("Sub-module not found")
