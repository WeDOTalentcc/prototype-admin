"""
Test suite for Feature Flags system.

Tests cover:
- Default flag definitions
- Rollout percentage functionality
- Flag expiration evaluation
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.shared.services.feature_flag_service import FeatureFlagService


class TestFeatureFlagService:
    """Tests for FeatureFlagService."""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for testing."""
        return FeatureFlagService()
    
    def test_default_flags_exist(self, service):
        """Verify all default flags are defined."""
        expected_flags = [
            "learning_hub_enabled",
            "outcome_learning_enabled",
            "stage_feedback_enabled",
            "skills_deduplication_enabled",
            "analytics_dashboard_enabled",
            "ai_suggestions_enhanced",
            "empty_field_notifications",
            "field_toggles_enabled"
        ]
        
        for flag in expected_flags:
            assert flag in service.DEFAULT_FLAGS, f"Missing flag: {flag}"
            assert "description" in service.DEFAULT_FLAGS[flag]
            assert "category" in service.DEFAULT_FLAGS[flag]
            assert "default" in service.DEFAULT_FLAGS[flag]
    
    def test_default_flags_have_correct_categories(self, service):
        """Verify flags are categorized correctly."""
        categories = set()
        for value in service.DEFAULT_FLAGS.values():
            categories.add(value.get("category"))
        
        assert "learning" in categories
        assert "wizard" in categories
        assert "ai" in categories
        assert "analytics" in categories
    
    def test_default_flag_count(self, service):
        """Verify we have exactly 11 default flags (8 original + 3 automation)."""
        assert len(service.DEFAULT_FLAGS) == 11

    def test_automation_flags_default_false(self, service):
        """Automation flags (ENABLE_AUTO_*) should default to False."""
        automation_flags = [k for k in service.DEFAULT_FLAGS if k.startswith("ENABLE_AUTO_")]
        assert len(automation_flags) == 3
        for key in automation_flags:
            assert service.DEFAULT_FLAGS[key]["default"] is False, f"Flag {key} should default to False"

    def test_all_defaults_are_true(self, service):
        """Non-automation default flags should default to True."""
        for key, value in service.DEFAULT_FLAGS.items():
            if not key.startswith("ENABLE_AUTO_"):
                assert value["default"] == True, f"Flag {key} should default to True"
    
    def test_evaluate_flag_enabled_100_percent(self, service):
        """Flag enabled with 100% rollout should return True."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 100
        mock_flag.expires_at = None
        
        result = service._evaluate_flag(mock_flag)
        assert result == True
    
    def test_evaluate_flag_disabled(self, service):
        """Disabled flag should return False."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = False
        mock_flag.rollout_percentage = 100
        mock_flag.expires_at = None
        
        result = service._evaluate_flag(mock_flag)
        assert result == False
    
    def test_evaluate_flag_expired(self, service):
        """Expired flag should return False."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 100
        mock_flag.expires_at = datetime.utcnow() - timedelta(days=1)
        
        result = service._evaluate_flag(mock_flag)
        assert result == False
    
    def test_evaluate_flag_not_expired(self, service):
        """Non-expired flag should work normally."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 100
        mock_flag.expires_at = datetime.utcnow() + timedelta(days=1)
        
        result = service._evaluate_flag(mock_flag)
        assert result == True
    
    def test_rollout_percentage_zero_always_disabled(self, service):
        """0% rollout should always return False."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 0
        mock_flag.expires_at = None
        
        for _ in range(10):
            result = service._evaluate_flag(mock_flag)
            assert result == False
    
    def test_rollout_percentage_50_under_threshold(self, service):
        """50% rollout with random=25 should return True."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 50
        mock_flag.expires_at = None
        
        with patch('app.services.feature_flag_service.random.randint', return_value=25):
            result = service._evaluate_flag(mock_flag)
        
        assert result == True
    
    def test_rollout_percentage_50_above_threshold(self, service):
        """50% rollout with random=75 should return False."""
        mock_flag = MagicMock()
        mock_flag.is_enabled = True
        mock_flag.rollout_percentage = 50
        mock_flag.expires_at = None
        
        with patch('app.services.feature_flag_service.random.randint', return_value=75):
            result = service._evaluate_flag(mock_flag)
        
        assert result == False
    
    def test_learning_flags_category(self, service):
        """Learning-related flags should be in learning category."""
        learning_flags = ["learning_hub_enabled", "outcome_learning_enabled", "stage_feedback_enabled"]
        
        for flag in learning_flags:
            assert service.DEFAULT_FLAGS[flag]["category"] == "learning"
    
    def test_wizard_flags_category(self, service):
        """Wizard-related flags should be in wizard category."""
        wizard_flags = ["skills_deduplication_enabled", "empty_field_notifications", "field_toggles_enabled"]
        
        for flag in wizard_flags:
            assert service.DEFAULT_FLAGS[flag]["category"] == "wizard"
    
    def test_ai_flag_category(self, service):
        """AI flag should be in ai category."""
        assert service.DEFAULT_FLAGS["ai_suggestions_enhanced"]["category"] == "ai"
    
    def test_analytics_flag_category(self, service):
        """Analytics flag should be in analytics category."""
        assert service.DEFAULT_FLAGS["analytics_dashboard_enabled"]["category"] == "analytics"


class TestFeatureFlagDescriptions:
    """Test flag descriptions are meaningful."""
    
    @pytest.fixture
    def service(self):
        return FeatureFlagService()
    
    def test_descriptions_not_empty(self, service):
        """All flags should have non-empty descriptions."""
        for key, value in service.DEFAULT_FLAGS.items():
            assert len(value["description"]) > 10, f"Flag {key} has too short description"
    
    def test_descriptions_are_unique(self, service):
        """Each flag should have a unique description."""
        descriptions = [v["description"] for v in service.DEFAULT_FLAGS.values()]
        assert len(descriptions) == len(set(descriptions)), "Duplicate descriptions found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
