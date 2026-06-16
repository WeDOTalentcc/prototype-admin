"""
Pydantic schemas for Compensation Analysis.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CompensationAlignmentStatus(StrEnum):
    """Alignment status for compensation components."""
    ALIGNED = "aligned"
    BELOW_MARKET = "below_market"
    ABOVE_MARKET = "above_market"
    BELOW_POLICY = "below_policy"
    ABOVE_POLICY = "above_policy"
    NO_DATA = "no_data"


class DataSource(StrEnum):
    """Sources of compensation data."""
    COMPANY_POLICY = "company_policy"
    MARKET_BENCHMARK = "market_benchmark"
    INTERNAL_HISTORY = "internal_history"
    INFERENCE = "inference"
    USER_INPUT = "user_input"


class SalaryAnalysis(BaseModel):
    """Analysis of salary component."""
    proposed_min: float | None = None
    proposed_max: float | None = None
    market_min: float | None = None
    market_max: float | None = None
    market_median: float | None = None
    market_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    market_percentile: int | None = None
    policy_min: float | None = None
    policy_max: float | None = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    suggested_min: float | None = None
    suggested_max: float | None = None
    suggestion_reason: str | None = None
    data_sources: list[DataSource] = Field(default_factory=list)
    confidence: float = 0.0


class BonusAnalysis(BaseModel):
    """Analysis of bonus component."""
    proposed_pct: float | None = None
    proposed_type: str | None = None
    proposed_criteria: str | None = None
    policy_exists: bool = False
    policy_min_pct: float | None = None
    policy_target_pct: float | None = None
    policy_max_pct: float | None = None
    policy_type: str | None = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    suggested_pct: float | None = None
    suggested_type: str | None = None
    suggestion_reason: str | None = None
    data_source: DataSource | None = None


class BenefitAnalysis(BaseModel):
    """Analysis of benefits component."""
    proposed_benefits: list[str] = Field(default_factory=list)
    company_standard_benefits: list[str] = Field(default_factory=list)
    monetizable_annual_value: float | None = None
    monetizable_breakdown: dict[str, float] = Field(default_factory=dict)
    missing_standard_benefits: list[str] = Field(default_factory=list)
    suggested_additions: list[str] = Field(default_factory=list)
    data_source: DataSource | None = None


class TotalCompAnalysis(BaseModel):
    """Analysis of total compensation."""
    proposed_annual_salary_min: float | None = None
    proposed_annual_salary_max: float | None = None
    proposed_bonus_annual: float | None = None
    proposed_benefits_annual: float | None = None
    proposed_total_comp_min: float | None = None
    proposed_total_comp_max: float | None = None
    market_total_comp_min: float | None = None
    market_total_comp_max: float | None = None
    market_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    policy_total_comp_min: float | None = None
    policy_total_comp_max: float | None = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    breakdown_chart: dict[str, Any] = Field(default_factory=dict)


class CompensationAnalysisResult(BaseModel):
    """Complete compensation analysis result."""
    salary: SalaryAnalysis = Field(default_factory=SalaryAnalysis)
    bonus: BonusAnalysis = Field(default_factory=BonusAnalysis)
    benefits: BenefitAnalysis = Field(default_factory=BenefitAnalysis)
    total_comp: TotalCompAnalysis = Field(default_factory=TotalCompAnalysis)
    overall_assessment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    summary: str | None = None
    alerts: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    suggested_values: dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    data_sources_used: list[DataSource] = Field(default_factory=list)
    analysis_confidence: float = 0.0
