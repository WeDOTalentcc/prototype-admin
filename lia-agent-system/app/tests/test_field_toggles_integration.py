"""
Tests for the LIA Field Toggles system.

Tests validate:
1. Toggle model with comment field
2. LiaFieldConfigService with fallback strategies
3. Agent context endpoint
4. Data source tracking
"""
from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.lia_field_toggles import (
    DEFAULT_FIELD_TOGGLES,
    FALLBACK_STRATEGIES,
    FIELD_FALLBACK_CONFIG,
    LiaFieldToggle,
)
from app.shared.services.lia_field_config_service import (
    MARKET_BENCHMARKS,
    DataSource,
    FieldConfig,
    FieldContext,
    LiaFieldConfigService,
)


class TestLiaFieldToggleModel:
    """Tests for the LiaFieldToggle model."""
    
    def test_model_has_comment_field(self):
        """Verify the model includes the comment field."""
        toggle = LiaFieldToggle(
            id=uuid4(),
            company_id=uuid4(),
            field_key="salary_ranges",
            is_active=False,
            comment="Use only internal salary bands, not market data"
        )
        
        assert toggle.comment == "Use only internal salary bands, not market data"
        assert toggle.field_key == "salary_ranges"
        assert toggle.is_active is False
    
    def test_default_toggles_defined(self):
        """Verify default toggles are properly defined."""
        assert len(DEFAULT_FIELD_TOGGLES) >= 30
        
        required_fields = [
            "seniority_levels", "work_model", "salary_ranges",
            "benefits", "tech_stack", "behavioral_competencies"
        ]
        toggle_keys = [t["field_key"] for t in DEFAULT_FIELD_TOGGLES]
        
        for field in required_fields:
            assert field in toggle_keys, f"Missing required field: {field}"
    
    def test_fallback_strategies_defined(self):
        """Verify fallback strategies are defined for all fields."""
        assert "job_history" in FALLBACK_STRATEGIES
        assert "market_benchmark" in FALLBACK_STRATEGIES
        assert "role_inference" in FALLBACK_STRATEGIES
        assert "skip" in FALLBACK_STRATEGIES
    
    def test_field_fallback_config_exists(self):
        """Verify field fallback configuration exists."""
        assert "salary_ranges" in FIELD_FALLBACK_CONFIG
        assert "job_history" in FIELD_FALLBACK_CONFIG["salary_ranges"]
        assert "market_benchmark" in FIELD_FALLBACK_CONFIG["salary_ranges"]


class TestLiaFieldConfigService:
    """Tests for the LiaFieldConfigService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.close = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock db."""
        return LiaFieldConfigService(mock_db)
    
    def test_data_source_enum(self):
        """Verify DataSource enum values."""
        assert DataSource.COMPANY_CONFIG.value == "company_config"
        assert DataSource.JOB_HISTORY.value == "job_history"
        assert DataSource.MARKET_BENCHMARK.value == "market_benchmark"
        assert DataSource.ROLE_INFERENCE.value == "role_inference"
        assert DataSource.NOT_AVAILABLE.value == "not_available"
    
    def test_field_config_dataclass(self):
        """Test FieldConfig dataclass."""
        config = FieldConfig(
            field_key="salary_ranges",
            is_active=False,
            comment="Test comment",
            fallback_strategies=["job_history", "market_benchmark"],
            company_value=None,
            fallback_value={"min": 5000, "max": 10000},
            data_source=DataSource.MARKET_BENCHMARK,
            confidence=0.6
        )
        
        assert config.field_key == "salary_ranges"
        assert config.is_active is False
        assert config.comment == "Test comment"
        assert config.confidence == 0.6
    
    def test_field_context_dataclass(self):
        """Test FieldContext dataclass."""
        context = FieldContext(
            field_key="work_model",
            value="hybrid",
            source=DataSource.JOB_HISTORY,
            source_explanation="Baseado no histórico de vagas da empresa",
            confidence=0.85,
            is_toggle_active=False,
            recruiter_comment="Preferimos trabalho híbrido"
        )
        
        assert context.field_key == "work_model"
        assert context.value == "hybrid"
        assert context.source == DataSource.JOB_HISTORY
        assert context.is_toggle_active is False
    
    def test_market_benchmarks_defined(self):
        """Verify market benchmarks are properly defined."""
        assert "salary_ranges" in MARKET_BENCHMARKS
        assert "Júnior" in MARKET_BENCHMARKS["salary_ranges"]
        assert "Sênior" in MARKET_BENCHMARKS["salary_ranges"]
        
        junior_salary = MARKET_BENCHMARKS["salary_ranges"]["Júnior"]
        assert "min" in junior_salary
        assert "max" in junior_salary
        assert "currency" in junior_salary
    
    def test_format_value_list(self, service):
        """Test value formatting for lists."""
        result = service._format_value(["Python", "JavaScript", "Go"])
        assert result == "Python, JavaScript, Go"
    
    def test_format_value_dict_salary(self, service):
        """Test value formatting for salary dict."""
        result = service._format_value({"min": 5000, "max": 10000, "currency": "BRL"})
        assert "BRL" in result
        assert "5" in result
        assert "10" in result
    
    def test_format_value_empty(self, service):
        """Test value formatting for empty values."""
        assert service._format_value(None) == ""
        assert service._format_value([]) == ""
    
    def test_get_source_explanation(self, service):
        """Test source explanation generation."""
        assert "empresa" in service._get_source_explanation(DataSource.COMPANY_CONFIG, "test").lower()
        assert "histórico" in service._get_source_explanation(DataSource.JOB_HISTORY, "test").lower()
        assert "benchmark" in service._get_source_explanation(DataSource.MARKET_BENCHMARK, "test").lower()
    
    def test_from_market_benchmark_salary(self, service):
        """Test market benchmark for salary ranges."""
        job_context = {"seniority": "Sênior"}
        result = service._from_market_benchmark("salary_ranges", job_context, None)
        
        assert result is not None
        assert "min" in result
        assert "max" in result
    
    def test_from_job_history_empty(self, service):
        """Test job history fallback with no history."""
        value, confidence = service._from_job_history("work_model", [])
        assert value is None
        assert confidence == 0.0
    
    def test_from_job_history_with_data(self, service):
        """Test job history fallback with data."""
        job_history = [
            {"work_model": "hybrid"},
            {"work_model": "hybrid"},
            {"work_model": "remote"},
        ]
        value, confidence = service._from_job_history("work_model", job_history)
        
        assert value == "hybrid"
        assert confidence > 0.5
    
    def test_resolve_fallback_skip_strategy(self, service):
        """Test fallback resolution with skip strategy."""
        value, source, confidence = service._resolve_fallback(
            "trade_name",
            ["skip"],
            [],
            None,
            None
        )
        
        assert value is None
        assert source == DataSource.NOT_AVAILABLE
        assert confidence == 0.0
    
    def test_resolve_fallback_market_benchmark(self, service):
        """Test fallback resolution with market benchmark."""
        value, source, confidence = service._resolve_fallback(
            "salary_ranges",
            ["job_history", "market_benchmark"],
            [],
            {"seniority": "Pleno"},
            None
        )
        
        assert value is not None
        assert source == DataSource.MARKET_BENCHMARK
        assert confidence > 0
    
    def test_calculate_data_quality_empty(self, service):
        """Test data quality calculation with empty contexts."""
        score = service._calculate_data_quality({})
        assert score == 0.0
    
    def test_calculate_data_quality_full(self, service):
        """Test data quality calculation with full data."""
        field_contexts = {
            "salary_ranges": FieldContext(
                field_key="salary_ranges",
                value={"min": 5000, "max": 10000},
                source=DataSource.COMPANY_CONFIG,
                source_explanation="test",
                confidence=1.0,
                is_toggle_active=True
            ),
            "work_model": FieldContext(
                field_key="work_model",
                value="hybrid",
                source=DataSource.JOB_HISTORY,
                source_explanation="test",
                confidence=0.8,
                is_toggle_active=False
            )
        }
        
        score = service._calculate_data_quality(field_contexts)
        assert score > 0


class TestFieldToggleAPIIntegration:
    """Integration tests for the field toggle API endpoints."""
    
    def test_field_toggle_response_includes_comment(self):
        """Verify API response includes comment field."""
        from app.api.v1.lia_field_toggles import FieldToggleResponse
        
        response = FieldToggleResponse(
            field_key="salary_ranges",
            is_active=False,
            comment="Only use our internal salary bands",
            fallback_strategies=["job_history", "market_benchmark"],
            updated_at=datetime.utcnow(),
            updated_by="recruiter@example.com"
        )
        
        assert response.comment == "Only use our internal salary bands"
        assert response.fallback_strategies == ["job_history", "market_benchmark"]
    
    def test_field_toggles_response_includes_comments(self):
        """Verify field toggles response includes comments dict."""
        from app.api.v1.lia_field_toggles import FieldTogglesResponse
        
        response = FieldTogglesResponse(
            company_id="test-company",
            toggles={"salary_ranges": False, "work_model": True},
            comments={"salary_ranges": "Internal only", "work_model": None},
            details=[]
        )
        
        assert "salary_ranges" in response.comments
        assert response.comments["salary_ranges"] == "Internal only"
    
    def test_agent_context_response_structure(self):
        """Verify agent context response structure."""
        from app.api.v1.lia_field_toggles import AgentContextResponse, FieldContextResponse
        
        response = AgentContextResponse(
            company_id="test-company",
            context_prompt="Test prompt",
            data_quality_score=0.85,
            active_field_count=25,
            inactive_field_count=7,
            field_contexts={
                "salary_ranges": FieldContextResponse(
                    field_key="salary_ranges",
                    value={"min": 5000, "max": 10000},
                    source="job_history",
                    source_explanation="Based on job history",
                    confidence=0.8,
                    is_toggle_active=False,
                    recruiter_comment="Use internal bands"
                )
            }
        )
        
        assert response.data_quality_score == 0.85
        assert response.active_field_count == 25
        assert response.field_contexts["salary_ranges"].source == "job_history"


# W1-002 (2026-05-22): TestAgentFieldConfigIntegration class removed.
# Os 3 tests testavam métodos phantom (get_field_config_context,
# is_field_active, get_field_value_with_source) que NUNCA existiram
# em BaseAgent (verificado via grep). Tests broken-by-design desde D0.
# Ref: sprint_logs/sprint_1.2/W1-002_AUDIT.md


class TestToggleBehaviorScenarios:
    """Test scenarios for toggle behavior."""
    
    def test_active_toggle_uses_company_data(self):
        """When toggle is active, AI should use company config data."""
        config = FieldConfig(
            field_key="salary_ranges",
            is_active=True,
            company_value={"min": 8000, "max": 15000},
            fallback_value=None,
            data_source=DataSource.COMPANY_CONFIG,
            confidence=1.0
        )
        
        assert config.is_active is True
        assert config.company_value is not None
        assert config.data_source == DataSource.COMPANY_CONFIG
        assert config.confidence == 1.0
    
    def test_inactive_toggle_uses_fallback(self):
        """When toggle is inactive, AI should use fallback data."""
        config = FieldConfig(
            field_key="salary_ranges",
            is_active=False,
            company_value={"min": 8000, "max": 15000},
            fallback_value={"min": 5000, "max": 9000},
            data_source=DataSource.JOB_HISTORY,
            confidence=0.8,
            fallback_strategies=["job_history", "market_benchmark"]
        )
        
        assert config.is_active is False
        assert config.fallback_value is not None
        assert config.data_source == DataSource.JOB_HISTORY
        assert config.confidence < 1.0
    
    def test_inactive_toggle_with_skip_strategy(self):
        """When toggle is inactive with skip strategy, data is not available."""
        config = FieldConfig(
            field_key="trade_name",
            is_active=False,
            company_value="Example Corp",
            fallback_value=None,
            data_source=DataSource.NOT_AVAILABLE,
            confidence=0.0,
            fallback_strategies=["skip"]
        )
        
        assert config.is_active is False
        assert config.fallback_value is None
        assert config.data_source == DataSource.NOT_AVAILABLE
    
    def test_recruiter_comment_provides_context(self):
        """Recruiter comments should be included in context."""
        context = FieldContext(
            field_key="salary_ranges",
            value={"min": 5000, "max": 10000},
            source=DataSource.MARKET_BENCHMARK,
            source_explanation="Market benchmark",
            confidence=0.6,
            is_toggle_active=False,
            recruiter_comment="Adjust for our location (interior) - typically 20% below SP capital"
        )
        
        assert context.recruiter_comment is not None
        assert "20%" in context.recruiter_comment


# TestJobIntakeAgentFieldToggles removida — JobIntakeAgent migrado para WizardReActAgent (Sprint 5).


class TestEmptyFieldDetection:
    """Tests for empty active field detection and reminder system."""
    
    def test_reminder_actions_defined(self):
        """Test that reminder action constants are defined."""
        from app.models.recruiter_profile import REMINDER_ACTIONS
        
        assert "fill_now" in REMINDER_ACTIONS
        assert "remind_later" in REMINDER_ACTIONS
        assert "dont_remind" in REMINDER_ACTIONS
        assert "dismissed" in REMINDER_ACTIONS
    
    def test_field_impact_descriptions_defined(self):
        """Test that field impact descriptions are defined."""
        from app.models.recruiter_profile import DEFAULT_IMPACT_DESCRIPTION, FIELD_IMPACT_DESCRIPTIONS
        
        assert "benefits" in FIELD_IMPACT_DESCRIPTIONS
        assert "tech_stack" in FIELD_IMPACT_DESCRIPTIONS
        assert "salary_ranges" in FIELD_IMPACT_DESCRIPTIONS
        assert len(DEFAULT_IMPACT_DESCRIPTION) > 0
    
    def test_recruiter_field_preference_model_has_reminder_fields(self):
        """Test that RecruiterFieldPreference has the reminder fields."""
        import inspect

        from app.models.recruiter_profile import RecruiterFieldPreference
        
        source = inspect.getsource(RecruiterFieldPreference)
        
        assert "remind_me_empty_field" in source
        assert "last_reminded_at" in source
        assert "snooze_until" in source
        assert "times_reminded" in source
        assert "times_filled_with_lia" in source
        assert "last_reminder_action" in source
    
    def test_is_empty_value_helper(self):
        """Test the _is_empty_value helper method."""
        from app.shared.services.lia_field_config_service import LiaFieldConfigService
        
        service = LiaFieldConfigService(None)
        
        assert service._is_empty_value(None) is True
        assert service._is_empty_value("") is True
        assert service._is_empty_value("  ") is True
        assert service._is_empty_value([]) is True
        assert service._is_empty_value({}) is True
        
        assert service._is_empty_value("value") is False
        assert service._is_empty_value(["item"]) is False
        assert service._is_empty_value({"key": "value"}) is False
        assert service._is_empty_value(0) is False
    
    def test_empty_field_notification_structure(self):
        """Test structure of empty field notifications."""
        notification = {
            "field_key": "benefits",
            "field_label": "Benefícios",
            "impact_description": "Impacto na qualidade da vaga",
            "has_fallback": True,
            "fallback_strategies": ["job_history", "market_benchmark"],
            "times_reminded": 2,
            "actions": [
                {"action": "fill_now", "label": "Preencher Agora", "description": "LIA ajuda"},
                {"action": "remind_later", "label": "Lembrar Depois", "description": "7 dias"},
                {"action": "dont_remind", "label": "Não Lembrar", "description": "Permanente"}
            ]
        }
        
        assert notification["field_key"] == "benefits"
        assert len(notification["actions"]) == 3
        assert notification["actions"][0]["action"] == "fill_now"
    
    def test_preference_update_result_structure(self):
        """Test structure of preference update results."""
        result = {
            "field_key": "benefits",
            "action": "remind_later",
            "remind_me": True,
            "snooze_until": "2026-02-04T20:00:00",
            "times_reminded": 3,
            "times_filled_with_lia": 1
        }
        
        assert result["action"] == "remind_later"
        assert result["remind_me"] is True
        assert result["snooze_until"] is not None


class TestEmptyFieldAPIEndpoints:
    """Tests for empty field API endpoint schemas."""
    
    def test_empty_fields_response_schema(self):
        """Test EmptyFieldsResponse schema structure."""
        from app.api.v1.lia_field_toggles import EmptyFieldsResponse
        
        schema = EmptyFieldsResponse.model_json_schema()
        
        assert "company_id" in schema["properties"]
        assert "user_id" in schema["properties"]
        assert "notifications" in schema["properties"]
        assert "total_empty_fields" in schema["properties"]
    
    def test_reminder_preference_update_schema(self):
        """Test ReminderPreferenceUpdate schema."""
        from app.api.v1.lia_field_toggles import ReminderPreferenceUpdate
        
        schema = ReminderPreferenceUpdate.model_json_schema()
        
        assert "action" in schema["properties"]
    
    def test_reminder_preference_response_schema(self):
        """Test ReminderPreferenceResponse schema."""
        from app.api.v1.lia_field_toggles import ReminderPreferenceResponse
        
        schema = ReminderPreferenceResponse.model_json_schema()
        
        assert "field_key" in schema["properties"]
        assert "action" in schema["properties"]
        assert "remind_me" in schema["properties"]
        assert "snooze_until" in schema["properties"]
        assert "times_reminded" in schema["properties"]
        assert "times_filled_with_lia" in schema["properties"]
    
    def test_field_value_suggestion_schema(self):
        """Test FieldValueSuggestion schema."""
        from app.api.v1.lia_field_toggles import FieldValueSuggestion
        
        schema = FieldValueSuggestion.model_json_schema()
        
        assert "field_key" in schema["properties"]
        assert "suggested_value" in schema["properties"]
        assert "source" in schema["properties"]
        assert "confidence" in schema["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
