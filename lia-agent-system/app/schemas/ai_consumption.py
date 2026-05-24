"""
Pydantic schemas for AI Consumption API.
"""

from datetime import date
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class AgentTypeEnum(StrEnum):
    """Types of AI agents for consumption tracking."""
    SCREENING = "screening"
    SCORING = "scoring"
    INTERVIEW = "interview"
    CV_PARSING = "cv_parsing"
    SEARCH = "search"
    MATCHING = "matching"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class ModelEnum(StrEnum):
    """AI models used."""
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    GEMINI_PRO = "gemini-pro"
    GEMINI_FLASH = "gemini-flash"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"


class AiConsumptionRecord(WeDoBaseModel):
    """Schema for recording AI consumption.

    P2-W3-AI-4: herda WeDoBaseModel (extra='forbid') — impede fields fantasma
    no endpoint POST /api/v1/ai-consumption/record (Pydantic Convention R1).
    """
    agent_type: str = Field(..., description="Type of AI agent")
    operation: str = Field(..., description="Operation performed")
    model: str = Field(..., description="AI model used")
    input_tokens: int = Field(default=0, ge=0, description="Input tokens used")
    output_tokens: int = Field(default=0, ge=0, description="Output tokens generated")
    total_tokens: int | None = Field(default=None, description="Total tokens (calculated if not provided)")
    cost_cents: int | None = Field(default=0, ge=0, description="Cost in cents")
    user_id: str | None = Field(default=None, description="User who triggered the operation")
    candidate_id: str | None = Field(default=None, description="Related candidate ID")
    vacancy_id: str | None = Field(default=None, description="Related vacancy ID")
    metadata: dict[str, Any] | None = Field(default_factory=dict, description="Additional metadata")


class AiConsumptionResponse(BaseModel):
    """Response schema for AI consumption record."""
    id: str
    company_id: str
    user_id: str | None = None
    agent_type: str
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_cents: int
    candidate_id: str | None = None
    vacancy_id: str | None = None
    metadata: dict[str, Any] = {}
    created_at: str | None = None


class AiConsumptionListResponse(BaseModel):
    """Response schema for list of AI consumption records."""
    records: list[AiConsumptionResponse]
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
    projected_monthly_tokens: int = 0
    projected_monthly_cost_cents: int = 0
    avg_daily_tokens_7d: int = 0
    avg_daily_cost_7d: int = 0
    daily_limit: int = 0
    daily_usage_today: int = 0
    daily_usage_percentage: float = 0


class UsageByAgentResponse(BaseModel):
    """Usage breakdown by agent type."""
    agent_type: str
    total_tokens: int
    total_operations: int
    total_cost_cents: int
    percentage_of_total: float


class UsageByAgentListResponse(BaseModel):
    """List of usage by agent type."""
    data: list[UsageByAgentResponse]
    total_tokens: int
    total_operations: int


class AgentDailyTrendResponse(BaseModel):
    """Daily trend for a specific agent."""
    date: str
    agent_type: str
    total_tokens: int
    total_cost_cents: int
    total_operations: int


class AgentDailyTrendListResponse(BaseModel):
    """List of agent daily trend data."""
    data: list[AgentDailyTrendResponse]
    total_days: int


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
    data: list[UsageByDayResponse]
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
    updated_at: str | None = None


class UpdateLimitsRequest(WeDoBaseModel):
    """Request to update client AI limits."""
    monthly_limit: int | None = Field(default=None, ge=0, description="Monthly token limit")
    overage_allowed: bool | None = Field(default=None, description="Allow overage usage")
    overage_rate_cents: int | None = Field(default=None, ge=0, description="Cost per 1000 tokens overage in cents")
    period_start: date | None = Field(default=None, description="Billing period start")
    period_end: date | None = Field(default=None, description="Billing period end")
    reset_usage: bool | None = Field(default=False, description="Reset current usage to 0")


class UsageHistoryResponse(BaseModel):
    """Historical usage data."""
    records: list[AiConsumptionResponse]
    total: int
    limit: int
    offset: int
    period_start: str | None = None
    period_end: str | None = None


class ConsumptionStatsResponse(BaseModel):
    """Comprehensive consumption statistics."""
    company_id: str
    period_start: str
    period_end: str
    total_tokens: int
    total_cost_cents: int
    total_operations: int
    by_agent_type: dict[str, int]
    by_model: dict[str, int]
    avg_tokens_per_operation: float
    peak_usage_day: str | None = None
    peak_usage_tokens: int = 0
