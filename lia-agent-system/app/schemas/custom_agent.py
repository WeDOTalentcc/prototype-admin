from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateCustomAgentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=256)
    role: str = Field(..., min_length=2, max_length=256)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    allowed_tools: list[str] = Field(default_factory=list)
    domain: str = Field(default="general", max_length=64)
    icon: Optional[str] = Field(default="🤖", max_length=10)
    config: dict[str, Any] = Field(default_factory=dict)
    max_steps: int = Field(default=8, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model_override: Optional[str] = None
    enable_memory: bool = True
    context_level: str = Field(default="full", pattern="^(full|standard|minimal)$")
    excluded_tools: list[str] = Field(default_factory=list)


class UpdateCustomAgentRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=256)
    role: Optional[str] = Field(None, min_length=2, max_length=256)
    description: Optional[str] = None
    system_prompt: Optional[str] = Field(None, min_length=10)
    allowed_tools: Optional[list[str]] = None
    domain: Optional[str] = Field(None, max_length=64)
    icon: Optional[str] = Field(None, max_length=10)
    config: Optional[dict[str, Any]] = None
    max_steps: Optional[int] = Field(None, ge=1, le=20)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    model_override: Optional[str] = None
    enable_memory: Optional[bool] = None
    context_level: Optional[str] = Field(None, pattern="^(full|standard|minimal)$")
    excluded_tools: Optional[list[str]] = None
    status: Optional[str] = Field(None, pattern="^(draft|active|paused|archived)$")


class CustomAgentResponse(BaseModel):
    id: str
    company_id: str
    created_by: str
    name: str
    role: str
    description: Optional[str] = None
    system_prompt: str
    allowed_tools: list[str] = []
    domain: str = "general"
    icon: Optional[str] = "🤖"
    status: str = "draft"
    version: int = 1
    config: dict[str, Any] = {}
    max_steps: int = 8
    temperature: float = 0.7
    model_override: Optional[str] = None
    enable_memory: bool = True
    context_level: str = "full"
    excluded_tools: list[str] = []
    total_executions: int = 0
    avg_confidence: float = 0.0
    last_executed_at: Optional[str] = None
    is_marketplace_published: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CustomAgentListResponse(BaseModel):
    agents: list[CustomAgentResponse]
    total: int


class TestCustomAgentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class TestCustomAgentResponse(BaseModel):
    agent_id: str
    message: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    execution_time_ms: int = 0


class PublishToMarketplaceRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=256)
    short_description: Optional[str] = Field(None, max_length=512)
    long_description: Optional[str] = None
    category: str = Field(default="general", max_length=64)
    tags: list[str] = Field(default_factory=list)
    icon_url: Optional[str] = None
    credits_per_execution: int = Field(default=1, ge=0)
    is_free: bool = False


class MarketplaceListingResponse(BaseModel):
    id: str
    agent_id: str
    publisher_company_id: str
    title: str
    short_description: Optional[str] = None
    long_description: Optional[str] = None
    category: str = "general"
    tags: list[str] = []
    icon_url: Optional[str] = None
    status: str = "pending_review"
    review_notes: Optional[str] = None
    credits_per_execution: int = 1
    is_free: bool = False
    install_count: int = 0
    avg_rating: float = 0.0
    total_ratings: int = 0
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    agent_name: Optional[str] = None
    agent_role: Optional[str] = None
    agent_domain: Optional[str] = None


class MarketplaceListResponse(BaseModel):
    listings: list[MarketplaceListingResponse]
    total: int


class MarketplaceReviewRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    review_notes: Optional[str] = None


class InstallAgentRequest(BaseModel):
    listing_id: str


class AgentInstallationResponse(BaseModel):
    id: str
    source_agent_id: str
    listing_id: Optional[str] = None
    installer_company_id: str
    installed_agent_id: Optional[str] = None
    installed_by: str
    status: str = "active"
    version_at_install: int = 1
    total_executions: int = 0
    total_credits_consumed: int = 0
    installed_at: Optional[str] = None
    agent_name: Optional[str] = None


class AgentInstallationListResponse(BaseModel):
    installations: list[AgentInstallationResponse]
    total: int


class ExecuteCustomAgentRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class ExecuteCustomAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    confidence: float = 0.0
    tool_calls: list[str] = []
    credits_consumed: int = 0
    execution_time_ms: int = 0
    metadata: dict[str, Any] = {}


class MarketplaceBillingResponse(BaseModel):
    agent_id: str
    agent_name: str
    total_executions: int = 0
    total_credits_consumed: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
