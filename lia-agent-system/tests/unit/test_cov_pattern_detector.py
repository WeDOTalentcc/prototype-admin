"""Coverage tests for pattern_detector_service.py — pure _calculate_confidence method."""
import pytest
from app.domains.analytics.services.pattern_detector_service import (
    DetectedPattern,
    PatternDetectorService,
)


class TestDetectedPattern:
    def test_basic_instantiation(self):
        p = DetectedPattern(
            pattern_type="salary_correction",
            field="salary_min",
            key="salary_correction_2026",
            data={"avg_correction": 1500.0},
            sample_size=15,
            confidence=0.7,
        )
        assert p.pattern_type == "salary_correction"
        assert p.sample_size == 15
        assert p.confidence == pytest.approx(0.7)

    def test_optional_applies_to_none(self):
        p = DetectedPattern(
            pattern_type="skill_match",
            field="skills",
            key="python_match",
            data={},
            sample_size=5,
            confidence=0.5,
        )
        assert p.applies_to is None

    def test_with_applies_to(self):
        p = DetectedPattern(
            pattern_type="stage_pattern",
            field="stage",
            key="stage_1",
            data={"stage": "screening"},
            sample_size=25,
            confidence=0.8,
            applies_to="screening_agent",
        )
        assert p.applies_to == "screening_agent"


class TestCalculateConfidence:
    def setup_method(self):
        self.service = PatternDetectorService()

    def test_small_sample_returns_low(self):
        result = self.service._calculate_confidence(sample_size=3)
        assert result == pytest.approx(0.3)

    def test_sample_5_to_9_returns_0_5(self):
        result = self.service._calculate_confidence(sample_size=7)
        assert result == pytest.approx(0.5)

    def test_sample_10_to_19_returns_0_7(self):
        result = self.service._calculate_confidence(sample_size=15)
        assert result == pytest.approx(0.7)

    def test_sample_20_to_49_returns_0_8(self):
        result = self.service._calculate_confidence(sample_size=30)
        assert result == pytest.approx(0.8)

    def test_sample_50_plus_returns_0_9(self):
        result = self.service._calculate_confidence(sample_size=100)
        assert result == pytest.approx(0.9)

    def test_low_cv_increases_confidence(self):
        # std_dev / mean = 0.05 < 0.1 → boost
        result = self.service._calculate_confidence(
            sample_size=30,
            std_deviation=50.0,
            mean_value=1000.0,
        )
        # base=0.8, cv=0.05 < 0.1 → base += 0.05 = 0.85
        assert result == pytest.approx(0.85)

    def test_high_cv_decreases_confidence(self):
        # std_dev / mean = 0.6 > 0.5 → penalty
        result = self.service._calculate_confidence(
            sample_size=30,
            std_deviation=600.0,
            mean_value=1000.0,
        )
        # base=0.8, cv=0.6 > 0.5 → base -= 0.10 = 0.7
        assert result == pytest.approx(0.7)

    def test_zero_mean_no_cv_adjustment(self):
        result = self.service._calculate_confidence(
            sample_size=30,
            std_deviation=0.0,
            mean_value=0.0,
        )
        assert result == pytest.approx(0.8)  # no CV adjustment when mean=0

    def test_none_std_no_adjustment(self):
        result = self.service._calculate_confidence(sample_size=30, std_deviation=None)
        assert result == pytest.approx(0.8)

    def test_sample_exactly_5(self):
        result = self.service._calculate_confidence(sample_size=5)
        assert result == pytest.approx(0.5)

    def test_sample_exactly_10(self):
        result = self.service._calculate_confidence(sample_size=10)
        assert result == pytest.approx(0.7)

    def test_sample_exactly_20(self):
        result = self.service._calculate_confidence(sample_size=20)
        assert result == pytest.approx(0.8)

    def test_sample_exactly_50(self):
        result = self.service._calculate_confidence(sample_size=50)
        assert result == pytest.approx(0.9)

    def test_returns_float(self):
        result = self.service._calculate_confidence(sample_size=10)
        assert isinstance(result, float)

    def test_result_between_0_and_1(self):
        for n in [1, 5, 10, 20, 50, 100]:
            r = self.service._calculate_confidence(sample_size=n)
            assert 0.0 <= r <= 1.0
