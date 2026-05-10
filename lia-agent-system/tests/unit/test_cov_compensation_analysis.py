"""Coverage tests for app/schemas/compensation_analysis.py — Pydantic models."""
import pytest
from app.schemas.compensation_analysis import (
    SalaryAnalysis,
    BonusAnalysis,
    BenefitAnalysis,
    TotalCompAnalysis,
    CompensationAnalysisResult,
)


class TestSalaryAnalysis:
    def test_empty(self):
        m = SalaryAnalysis()
        assert m is not None

    def test_with_values(self):
        m = SalaryAnalysis(
            proposed_min=10000.0,
            proposed_max=15000.0,
            market_min=9000.0,
            market_median=13000.0,
            market_max=18000.0,
            market_percentile=55.0,
        )
        assert m.proposed_min == pytest.approx(10000.0)
        assert m.market_percentile == pytest.approx(55.0)

    def test_with_policy(self):
        m = SalaryAnalysis(
            proposed_min=12000.0,
            proposed_max=16000.0,
            policy_min=10000.0,
            policy_max=20000.0,
            policy_alignment="aligned",
        )
        assert m.policy_alignment == "aligned"

    def test_with_suggestion(self):
        m = SalaryAnalysis(
            suggested_min=13000.0,
            suggested_max=17000.0,
            suggestion_reason="Below market median",
        )
        assert m.suggestion_reason == "Below market median"


class TestBonusAnalysis:
    def test_empty(self):
        m = BonusAnalysis()
        assert m is not None

    def test_with_values(self):
        m = BonusAnalysis(
            proposed_pct=10.0,
            proposed_type="performance",
            policy_exists=True,
            policy_target_pct=12.0,
            policy_alignment="below_policy",
        )
        assert m.proposed_pct == pytest.approx(10.0)
        assert m.policy_exists is True

    def test_with_suggestion(self):
        m = BonusAnalysis(
            suggested_pct=12.0,
            suggested_type="profit_sharing",
            suggestion_reason="Align with policy target",
        )
        assert m.suggestion_reason == "Align with policy target"


class TestBenefitAnalysis:
    def test_empty(self):
        m = BenefitAnalysis()
        assert m is not None

    def test_with_values(self):
        m = BenefitAnalysis(
            proposed_benefits=["health", "dental", "meal"],
            company_standard_benefits=["health", "dental"],
            monetizable_annual_value=18000.0,
        )
        assert len(m.proposed_benefits) == 3
        assert m.monetizable_annual_value == pytest.approx(18000.0)

    def test_with_missing(self):
        m = BenefitAnalysis(
            proposed_benefits=["health"],
            missing_standard_benefits=["dental", "meal"],
        )
        assert len(m.missing_standard_benefits) == 2


class TestTotalCompAnalysis:
    def test_empty(self):
        m = TotalCompAnalysis()
        assert m is not None

    def test_with_values(self):
        m = TotalCompAnalysis(
            proposed_annual_salary_min=144000.0,
            proposed_annual_salary_max=180000.0,
            proposed_bonus_annual=18000.0,
            proposed_benefits_annual=12000.0,
            proposed_total_comp_min=174000.0,
            proposed_total_comp_max=210000.0,
        )
        assert m.proposed_total_comp_min == pytest.approx(174000.0)
        assert m.proposed_bonus_annual == pytest.approx(18000.0)

    def test_market_comparison(self):
        m = TotalCompAnalysis(
            proposed_total_comp_min=180000.0,
            proposed_total_comp_max=220000.0,
            market_total_comp_min=160000.0,
            market_total_comp_max=240000.0,
            market_alignment="aligned",
        )
        assert m.market_alignment == "aligned"


class TestCompensationAnalysisResult:
    def test_empty(self):
        m = CompensationAnalysisResult()
        assert m is not None

    def test_with_components(self):
        sal = SalaryAnalysis(proposed_min=12000.0, proposed_max=16000.0)
        bon = BonusAnalysis(proposed_pct=10.0)
        ben = BenefitAnalysis(proposed_benefits=["health"])
        tot = TotalCompAnalysis(proposed_total_comp_min=174000.0)
        m = CompensationAnalysisResult(
            salary=sal,
            bonus=bon,
            benefits=ben,
            total_comp=tot,
        )
        assert m.salary.proposed_min == pytest.approx(12000.0)
        assert m.bonus.proposed_pct == pytest.approx(10.0)

    def test_with_assessment(self):
        m = CompensationAnalysisResult(
            overall_assessment="aligned",
            summary="Base salary within range; benefits complete.",
            alerts=["Bonus below policy target"],
            recommendations=["Increase bonus to 12%"],
        )
        assert m.overall_assessment is not None
        assert len(m.alerts) == 1
        assert len(m.recommendations) == 1

    def test_confidence(self):
        m = CompensationAnalysisResult(
            analysis_confidence=0.85,
            data_sources_used=["company_policy", "market_benchmark"],
        )
        assert m.analysis_confidence == pytest.approx(0.85)
        assert len(m.data_sources_used) == 2
