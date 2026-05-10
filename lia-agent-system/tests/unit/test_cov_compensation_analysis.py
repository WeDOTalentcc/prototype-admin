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
            base_salary=12000.0,
            currency="BRL",
            market_percentile=50.0,
            competitive_rating="competitive",
        )
        assert m.base_salary == pytest.approx(12000.0)
        assert m.currency == "BRL"
        assert m.market_percentile == pytest.approx(50.0)

    def test_range(self):
        m = SalaryAnalysis(
            base_salary=15000.0,
            market_min=10000.0,
            market_median=14000.0,
            market_max=20000.0,
        )
        assert m.market_min == pytest.approx(10000.0)
        assert m.market_max == pytest.approx(20000.0)


class TestBonusAnalysis:
    def test_empty(self):
        m = BonusAnalysis()
        assert m is not None

    def test_with_values(self):
        m = BonusAnalysis(
            total_bonus=5000.0,
            variable_percentage=10.0,
            has_performance_bonus=True,
        )
        assert m.total_bonus == pytest.approx(5000.0)
        assert m.has_performance_bonus is True


class TestBenefitAnalysis:
    def test_empty(self):
        m = BenefitAnalysis()
        assert m is not None

    def test_with_values(self):
        m = BenefitAnalysis(
            total_benefit_value=3000.0,
            has_health_insurance=True,
            has_dental=True,
            has_meal_voucher=True,
        )
        assert m.total_benefit_value == pytest.approx(3000.0)
        assert m.has_health_insurance is True


class TestTotalCompAnalysis:
    def test_empty(self):
        m = TotalCompAnalysis()
        assert m is not None

    def test_with_values(self):
        m = TotalCompAnalysis(
            total_annual_compensation=200000.0,
            currency="BRL",
            competitiveness_score=8.5,
            recommendation="increase_base",
        )
        assert m.total_annual_compensation == pytest.approx(200000.0)
        assert m.competitiveness_score == pytest.approx(8.5)


class TestCompensationAnalysisResult:
    def test_empty(self):
        m = CompensationAnalysisResult()
        assert m is not None

    def test_with_components(self):
        sal = SalaryAnalysis(base_salary=12000.0, currency="BRL")
        bon = BonusAnalysis(total_bonus=2000.0)
        ben = BenefitAnalysis(total_benefit_value=1500.0)
        tot = TotalCompAnalysis(total_annual_compensation=186000.0, currency="BRL")
        m = CompensationAnalysisResult(
            salary=sal,
            bonus=bon,
            benefits=ben,
            total_comp=tot,
            job_title="Senior Backend Engineer",
            seniority_level="senior",
        )
        assert m.job_title == "Senior Backend Engineer"
        assert m.salary.base_salary == pytest.approx(12000.0)
        assert m.total_comp.total_annual_compensation == pytest.approx(186000.0)

    def test_analysis_only(self):
        m = CompensationAnalysisResult(
            overall_assessment="Package is competitive for the Brazilian market.",
            recommendations=["Consider adding profit sharing", "Increase meal voucher"],
        )
        assert "competitive" in m.overall_assessment
        assert len(m.recommendations) == 2
