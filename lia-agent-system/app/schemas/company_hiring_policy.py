"""
Pydantic schemas for CompanyHiringPolicy API.
"""
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class PipelineRulesSchema(BaseModel):
    min_interviews_before_offer: int = Field(default=2, ge=1, le=10)
    manager_approval_for_offer: bool = Field(default=True)
    max_days_in_stage: dict[str, int] = Field(default_factory=dict)


class SchedulingRulesSchema(BaseModel):
    allowed_days: list[str] = Field(default=["mon", "tue", "wed", "thu", "fri"])
    allowed_hours: dict[str, str] = Field(default={"start": "09:00", "end": "18:00"})
    default_duration_minutes: int = Field(default=60, ge=15, le=480)
    self_scheduling_enabled: bool = Field(default=False)


class CommunicationRulesSchema(BaseModel):
    auto_rejection_feedback: bool = Field(default=False)
    rejection_feedback_deadline_hours: int = Field(default=48, ge=1, le=720)
    preferred_channel: str = Field(default="whatsapp")
    lia_tone: str = Field(default="professional")


class ScreeningRulesSchema(BaseModel):
    salary_expectation_filter: bool = Field(default=False)
    salary_tolerance_percent: int = Field(default=15, ge=0, le=100)
    experience_policy: str = Field(default="per_job")
    default_screening_questions: list[str] = Field(default_factory=list)


class AutomationRulesSchema(BaseModel):
    auto_screening: bool = Field(default=False)
    auto_scheduling: bool = Field(default=False)
    auto_stage_advance: bool = Field(default=False)
    autonomy_level: str = Field(default="low")


class PipelineTemplateSchema(BaseModel):
    name: str
    stages: list[str] = Field(default_factory=list)
    rules: dict[str, Any] = Field(default_factory=dict)


class LearnedPatternSchema(BaseModel):
    pattern: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="observation")
    data: dict[str, Any] = Field(default_factory=dict)
    observation_count: int = Field(default=1, ge=0)
    last_observed: str | None = None


class CompanyHiringPolicyCreate(WeDoBaseModel):
    company_id: str
    pipeline_rules: PipelineRulesSchema | None = None
    scheduling_rules: SchedulingRulesSchema | None = None
    communication_rules: CommunicationRulesSchema | None = None
    screening_rules: ScreeningRulesSchema | None = None
    automation_rules: AutomationRulesSchema | None = None
    pipeline_templates: list[PipelineTemplateSchema] | None = None


class CompanyHiringPolicyUpdate(WeDoBaseModel):
    pipeline_rules: dict[str, Any] | None = None
    scheduling_rules: dict[str, Any] | None = None
    communication_rules: dict[str, Any] | None = None
    screening_rules: dict[str, Any] | None = None
    automation_rules: dict[str, Any] | None = None
    pipeline_templates: list[dict[str, Any]] | None = None
    updated_by: str | None = None


class CompanyHiringPolicyBlockUpdate(WeDoBaseModel):
    block: str = Field(..., description="Block name: pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules, pipeline_templates")
    data: dict[str, Any] = Field(..., description="Block data to merge")
    updated_by: str | None = None


class CompanyHiringPolicyResponse(BaseModel):
    id: str
    company_id: str
    pipeline_rules: dict[str, Any]
    scheduling_rules: dict[str, Any]
    communication_rules: dict[str, Any]
    screening_rules: dict[str, Any]
    automation_rules: dict[str, Any]
    pipeline_templates: list[dict[str, Any]]
    learned_patterns: list[dict[str, Any]]
    setup_progress: int
    setup_completed_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class PolicyProgressResponse(BaseModel):
    company_id: str
    setup_progress: int
    setup_completed_at: str | None = None
    blocks_completed: dict[str, bool]


class PolicyChatMessage(BaseModel):
    """# T-06 R2 fix canonical: PolicyChatMessage company_id field removed.

    Multi-tenancy via path /{company_id}/chat + require_company_id_strict_match.
    """
    message: str
    user_id: str | None = None
    session_id: str | None = None
    conversation_history: list[dict[str, Any]] | None = Field(default_factory=list)


class PolicyChatResponse(BaseModel):
    reply: str
    current_block: str | None = None
    current_question: int | None = None
    total_questions: int = 19
    setup_progress: int = 0
    updated_fields: dict[str, Any] = Field(default_factory=dict)
    block_completed: bool = False
    all_completed: bool = False
    session_id: str | None = None
