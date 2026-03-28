"""
Pydantic schemas for CompanyHiringPolicy API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class PipelineRulesSchema(BaseModel):
    min_interviews_before_offer: int = Field(default=2, ge=1, le=10)
    manager_approval_for_offer: bool = Field(default=True)
    max_days_in_stage: Dict[str, int] = Field(default_factory=dict)


class SchedulingRulesSchema(BaseModel):
    allowed_days: List[str] = Field(default=["mon", "tue", "wed", "thu", "fri"])
    allowed_hours: Dict[str, str] = Field(default={"start": "09:00", "end": "18:00"})
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
    default_screening_questions: List[str] = Field(default_factory=list)


class AutomationRulesSchema(BaseModel):
    auto_screening: bool = Field(default=False)
    auto_scheduling: bool = Field(default=False)
    auto_stage_advance: bool = Field(default=False)
    autonomy_level: str = Field(default="low")


class PipelineTemplateSchema(BaseModel):
    name: str
    stages: List[str] = Field(default_factory=list)
    rules: Dict[str, Any] = Field(default_factory=dict)


class LearnedPatternSchema(BaseModel):
    pattern: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="observation")
    data: Dict[str, Any] = Field(default_factory=dict)
    observation_count: int = Field(default=1, ge=0)
    last_observed: Optional[str] = None


class CompanyHiringPolicyCreate(BaseModel):
    company_id: str
    pipeline_rules: Optional[PipelineRulesSchema] = None
    scheduling_rules: Optional[SchedulingRulesSchema] = None
    communication_rules: Optional[CommunicationRulesSchema] = None
    screening_rules: Optional[ScreeningRulesSchema] = None
    automation_rules: Optional[AutomationRulesSchema] = None
    pipeline_templates: Optional[List[PipelineTemplateSchema]] = None


class CompanyHiringPolicyUpdate(BaseModel):
    pipeline_rules: Optional[Dict[str, Any]] = None
    scheduling_rules: Optional[Dict[str, Any]] = None
    communication_rules: Optional[Dict[str, Any]] = None
    screening_rules: Optional[Dict[str, Any]] = None
    automation_rules: Optional[Dict[str, Any]] = None
    pipeline_templates: Optional[List[Dict[str, Any]]] = None
    updated_by: Optional[str] = None


class CompanyHiringPolicyBlockUpdate(BaseModel):
    block: str = Field(..., description="Block name: pipeline_rules, scheduling_rules, communication_rules, screening_rules, automation_rules, pipeline_templates")
    data: Dict[str, Any] = Field(..., description="Block data to merge")
    updated_by: Optional[str] = None


class CompanyHiringPolicyResponse(BaseModel):
    id: str
    company_id: str
    pipeline_rules: Dict[str, Any]
    scheduling_rules: Dict[str, Any]
    communication_rules: Dict[str, Any]
    screening_rules: Dict[str, Any]
    automation_rules: Dict[str, Any]
    pipeline_templates: List[Dict[str, Any]]
    learned_patterns: List[Dict[str, Any]]
    setup_progress: int
    setup_completed_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class PolicyProgressResponse(BaseModel):
    company_id: str
    setup_progress: int
    setup_completed_at: Optional[str] = None
    blocks_completed: Dict[str, bool]


class PolicyChatMessage(BaseModel):
    message: str
    company_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class PolicyChatResponse(BaseModel):
    reply: str
    current_block: Optional[str] = None
    current_question: Optional[int] = None
    total_questions: int = 19
    setup_progress: int = 0
    updated_fields: Dict[str, Any] = Field(default_factory=dict)
    block_completed: bool = False
    all_completed: bool = False
    session_id: Optional[str] = None
