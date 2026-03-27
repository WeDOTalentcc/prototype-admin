"""
Pydantic schemas for AI Consumption API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class AgentTypeEnum(str, Enum):
    """Types of AI agents for consumption tracking."""
    SCREENING = "screening"
    SCORING = "scoring"
    INTERVIEW = "interview"
    CV_PARSING = "cv_parsing"
    SEARCH = "search"
    MATCHING = "matching"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class ModelEnum(str, Enum):
    """AI models used."""
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"


class AiConsumptionRecord(BaseModel):
    """Schema for recording AI consumption."""
    agent_type: str = Field(..., description="Type of AI agent")
    operation: str = Field(..., description="Operation performed")
    model: str = Field(..., description="AI model used")
    input_tokens: int = Field(default=0, ge=0, description="Input tokens used")
    output_tokens: int = Field(default=0, ge=0, description="Output tokens generated")
    total_tokens: Optional[int] = Field(default=None, description="Total tokens (calculated if not provided)")
    cost_cents: Optional[int] = Field(default=0, ge=0, description="Cost in cents")
    user_id: Optional[str] = Field(default=None, description="User who triggered the operation")
    candidate_id: Optional[str] = Field(default=None, description="Related candidate ID")
    vacancy_id: Optional[str] = Field(default=None, description="Related vacancy ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AiConsumptionResponse(BaseModel):
    """Response schema for AI consumption record."""
    id: str
    company_id: str
    user_id: Optional[str] = None
    agent_type: str
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_cents: int
    candidate_id: Optional[str] = None
    vacancy_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: Optional[str] = None


class AiConsumptionListResponse(BaseModel):
    """Response schema for list of AI consumption records."""
    records: List[AiConsumptionResponse]
    total: int
    limit: int
    offset: int


class UsageSummaryResponse(BaseModel):
    """Summary of AI usage for current period."""
    company_id: str
    period_start: str
    period_end: str
    total_tokens: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_cents: int
    total_operations: int
    monthly_limit: int
    usage_percentage: float
    remaining_tokens: int
    overage_allowed: bool


class UsageByAgentResponse(BaseModel):
    """Usage breakdown by agent type."""
    agent_type: str
    total_tokens: int
    total_operations: int
    total_cost_cents: int
    percentage_of_total: float


class UsageByAgentListResponse(BaseModel):
    """List of usage by agent type."""
    data: List[UsageByAgentResponse]
    total_tokens: int
    total_operations: int


class UsageByModelResponse(BaseModel):
    """Usage breakdown by model."""
    model: str
    total_tokens: int
    total_operations: int
    total_cost_cents: int
    percentage_of_total: float


class UsageByDayResponse(BaseModel):
    """Usage for a specific day."""
    date: str
    total_tokens: int
    total_operations: int
    total_cost_cents: int


class UsageByDayListResponse(BaseModel):
    """List of daily usage."""
    data: List[UsageByDayResponse]
    total_tokens: int
    total_days: int


class BalanceResponse(BaseModel):
    """AI credits balance response."""
    id: str
    company_id: str
    monthly_limit: int
    current_usage: int
    period_start: str
    period_end: str
    overage_allowed: bool
    overage_rate_cents: int
    usage_percentage: float
    remaining_tokens: int
    updated_at: Optional[str] = None


class UpdateLimitsRequest(BaseModel):
    """Request to update client AI limits."""
    monthly_limit: Optional[int] = Field(default=None, ge=0, description="Monthly token limit")
    overage_allowed: Optional[bool] = Field(default=None, description="Allow overage usage")
    overage_rate_cents: Optional[int] = Field(default=None, ge=0, description="Cost per 1000 tokens overage in cents")
    period_start: Optional[date] = Field(default=None, description="Billing period start")
    period_end: Optional[date] = Field(default=None, description="Billing period end")
    reset_usage: Optional[bool] = Field(default=False, description="Reset current usage to 0")


class UsageHistoryResponse(BaseModel):
    """Historical usage data."""
    records: List[AiConsumptionResponse]
    total: int
    limit: int
    offset: int
    period_start: Optional[str] = None
    period_end: Optional[str] = None


class ConsumptionStatsResponse(BaseModel):
    """Comprehensive consumption statistics."""
    company_id: str
    period_start: str
    period_end: str
    total_tokens: int
    total_cost_cents: int
    total_operations: int
    by_agent_type: Dict[str, int]
    by_model: Dict[str, int]
    avg_tokens_per_operation: float
    peak_usage_day: Optional[str] = None
    peak_usage_tokens: int = 0
