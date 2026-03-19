"""
Pydantic schemas for Compensation Analysis.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CompensationAlignmentStatus(str, Enum):
    """Alignment status for compensation components."""
    ALIGNED = "aligned"
    BELOW_MARKET = "below_market"
    ABOVE_MARKET = "above_market"
    BELOW_POLICY = "below_policy"
    ABOVE_POLICY = "above_policy"
    NO_DATA = "no_data"


class DataSource(str, Enum):
    """Sources of compensation data."""
    COMPANY_POLICY = "company_policy"
    MARKET_BENCHMARK = "market_benchmark"
    INTERNAL_HISTORY = "internal_history"
    INFERENCE = "inference"
    USER_INPUT = "user_input"


class SalaryAnalysis(BaseModel):
    """Analysis of salary component."""
    proposed_min: Optional[float] = None
    proposed_max: Optional[float] = None
    market_min: Optional[float] = None
    market_max: Optional[float] = None
    market_median: Optional[float] = None
    market_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    market_percentile: Optional[int] = None
    policy_min: Optional[float] = None
    policy_max: Optional[float] = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    suggested_min: Optional[float] = None
    suggested_max: Optional[float] = None
    suggestion_reason: Optional[str] = None
    data_sources: List[DataSource] = Field(default_factory=list)
    confidence: float = 0.0


class BonusAnalysis(BaseModel):
    """Analysis of bonus component."""
    proposed_pct: Optional[float] = None
    proposed_type: Optional[str] = None
    proposed_criteria: Optional[str] = None
    policy_exists: bool = False
    policy_min_pct: Optional[float] = None
    policy_target_pct: Optional[float] = None
    policy_max_pct: Optional[float] = None
    policy_type: Optional[str] = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    suggested_pct: Optional[float] = None
    suggested_type: Optional[str] = None
    suggestion_reason: Optional[str] = None
    data_source: Optional[DataSource] = None


class BenefitAnalysis(BaseModel):
    """Analysis of benefits component."""
    proposed_benefits: List[str] = Field(default_factory=list)
    company_standard_benefits: List[str] = Field(default_factory=list)
    monetizable_annual_value: Optional[float] = None
    monetizable_breakdown: Dict[str, float] = Field(default_factory=dict)
    missing_standard_benefits: List[str] = Field(default_factory=list)
    suggested_additions: List[str] = Field(default_factory=list)
    data_source: Optional[DataSource] = None


class TotalCompAnalysis(BaseModel):
    """Analysis of total compensation."""
    proposed_annual_salary_min: Optional[float] = None
    proposed_annual_salary_max: Optional[float] = None
    proposed_bonus_annual: Optional[float] = None
    proposed_benefits_annual: Optional[float] = None
    proposed_total_comp_min: Optional[float] = None
    proposed_total_comp_max: Optional[float] = None
    market_total_comp_min: Optional[float] = None
    market_total_comp_max: Optional[float] = None
    market_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    policy_total_comp_min: Optional[float] = None
    policy_total_comp_max: Optional[float] = None
    policy_alignment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    breakdown_chart: Dict[str, Any] = Field(default_factory=dict)


class CompensationAnalysisResult(BaseModel):
    """Complete compensation analysis result."""
    salary: SalaryAnalysis = Field(default_factory=SalaryAnalysis)
    bonus: BonusAnalysis = Field(default_factory=BonusAnalysis)
    benefits: BenefitAnalysis = Field(default_factory=BenefitAnalysis)
    total_comp: TotalCompAnalysis = Field(default_factory=TotalCompAnalysis)
    overall_assessment: CompensationAlignmentStatus = CompensationAlignmentStatus.NO_DATA
    summary: Optional[str] = None
    alerts: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    suggested_values: Dict[str, Any] = Field(default_factory=dict)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    data_sources_used: List[DataSource] = Field(default_factory=list)
    analysis_confidence: float = 0.0
