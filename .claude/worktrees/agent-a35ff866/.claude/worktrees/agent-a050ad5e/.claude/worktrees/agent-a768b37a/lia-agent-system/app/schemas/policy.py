"""
Pydantic schemas for Policy Engine API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class RuleTypeEnum(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class TargetTypeEnum(str, Enum):
    COMPANY = "company"
    USER = "user"
    AGENT = "agent"
    ACTION = "action"


class TriggerTypeEnum(str, Enum):
    TIMEOUT = "timeout"
    FAILURE = "failure"
    FAILURE_COUNT = "failure_count"
    THRESHOLD = "threshold"
    SLA_BREACH = "sla_breach"


class EscalationActionEnum(str, Enum):
    NOTIFY_MANAGER = "notify_manager"
    NOTIFY_ADMIN = "notify_admin"
    PAUSE_WORKFLOW = "pause_workflow"
    REQUIRE_REVIEW = "require_review"
    SEND_ALERT = "send_alert"
    CREATE_TASK = "create_task"


class PolicyEvaluationResultEnum(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    RATE_LIMITED = "rate_limited"


class BusinessRuleCreate(BaseModel):
    """Schema for creating a business rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: RuleTypeEnum = RuleTypeEnum.ALLOW
    conditions: Dict[str, Any] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=1, le=1000)
    approval_config: Optional[Dict[str, Any]] = None
    is_active: bool = True
    rule_metadata: Optional[Dict[str, Any]] = None
    company_id: Optional[str] = None


class BusinessRuleUpdate(BaseModel):
    """Schema for updating a business rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    rule_type: Optional[RuleTypeEnum] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    approval_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    rule_metadata: Optional[Dict[str, Any]] = None


class BusinessRuleResponse(BaseModel):
    """Schema for business rule response."""
    id: str
    company_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    rule_type: str
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int
    approval_config: Optional[Dict[str, Any]] = None
    is_active: bool
    rule_metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class RateLimitRuleCreate(BaseModel):
    """Schema for creating a rate limit rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: TargetTypeEnum
    target_id: Optional[str] = None
    action_pattern: Optional[str] = None
    limit_value: int = Field(..., ge=1)
    window_seconds: int = Field(..., ge=1)
    burst_limit: Optional[int] = None
    is_active: bool = True
    company_id: Optional[str] = None


class RateLimitRuleUpdate(BaseModel):
    """Schema for updating a rate limit rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    target_type: Optional[TargetTypeEnum] = None
    target_id: Optional[str] = None
    action_pattern: Optional[str] = None
    limit_value: Optional[int] = Field(None, ge=1)
    window_seconds: Optional[int] = Field(None, ge=1)
    burst_limit: Optional[int] = None
    is_active: Optional[bool] = None


class RateLimitRuleResponse(BaseModel):
    """Schema for rate limit rule response."""
    id: str
    company_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    target_type: str
    target_id: Optional[str] = None
    action_pattern: Optional[str] = None
    limit_value: int
    window_seconds: int
    current_count: int
    window_start: Optional[str] = None
    burst_limit: Optional[int] = None
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class EscalationRuleCreate(BaseModel):
    """Schema for creating an escalation rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: TriggerTypeEnum
    condition: Dict[str, Any] = Field(default_factory=dict)
    escalate_to: List[str] = Field(default_factory=list)
    escalation_action: EscalationActionEnum = EscalationActionEnum.NOTIFY_MANAGER
    notification_template: Optional[str] = None
    cooldown_seconds: int = Field(default=3600, ge=0)
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = True
    company_id: Optional[str] = None


class EscalationRuleUpdate(BaseModel):
    """Schema for updating an escalation rule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    trigger_type: Optional[TriggerTypeEnum] = None
    condition: Optional[Dict[str, Any]] = None
    escalate_to: Optional[List[str]] = None
    escalation_action: Optional[EscalationActionEnum] = None
    notification_template: Optional[str] = None
    cooldown_seconds: Optional[int] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None


class EscalationRuleResponse(BaseModel):
    """Schema for escalation rule response."""
    id: str
    company_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    trigger_type: str
    condition: Dict[str, Any]
    escalate_to: List[str]
    escalation_action: str
    notification_template: Optional[str] = None
    cooldown_seconds: int
    last_triggered: Optional[str] = None
    is_active: bool
    priority: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class PolicyEvaluateRequest(BaseModel):
    """Schema for policy evaluation request."""
    action: str = Field(..., min_length=1)
    context: Dict[str, Any] = Field(default_factory=dict)
    agent_name: Optional[str] = None
    company_id: Optional[str] = None
    user_id: Optional[str] = None
    check_rate_limit: bool = True
    dry_run: bool = False


class PolicyEvaluateResponse(BaseModel):
    """Schema for policy evaluation response."""
    result: PolicyEvaluationResultEnum
    allowed: bool
    reason: Optional[str] = None
    matching_rule: Optional[BusinessRuleResponse] = None
    rate_limit_status: Optional[Dict[str, Any]] = None
    requires_approval: bool = False
    approval_config: Optional[Dict[str, Any]] = None
    evaluation_time_ms: float
    rules_evaluated: int


class RateLimitCheckRequest(BaseModel):
    """Schema for rate limit check request."""
    target_type: TargetTypeEnum
    target_id: str
    action: str
    company_id: Optional[str] = None
    increment: bool = True


class RateLimitCheckResponse(BaseModel):
    """Schema for rate limit check response."""
    allowed: bool
    current_count: int
    limit_value: int
    window_seconds: int
    remaining: int
    reset_at: Optional[str] = None
    rule_name: Optional[str] = None


class EscalationTriggerRequest(BaseModel):
    """Schema for escalation trigger request."""
    rule_id: Optional[str] = None
    trigger_type: Optional[TriggerTypeEnum] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    company_id: Optional[str] = None


class EscalationTriggerResponse(BaseModel):
    """Schema for escalation trigger response."""
    success: bool
    escalation_log_id: Optional[str] = None
    action_taken: Optional[str] = None
    notifications_sent: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class PolicyListResponse(BaseModel):
    """Schema for listing policies."""
    business_rules: List[BusinessRuleResponse] = Field(default_factory=list)
    rate_limit_rules: List[RateLimitRuleResponse] = Field(default_factory=list)
    escalation_rules: List[EscalationRuleResponse] = Field(default_factory=list)
    total_business_rules: int = 0
    total_rate_limit_rules: int = 0
    total_escalation_rules: int = 0


class PolicySeedResponse(BaseModel):
    """Schema for seeding default policies."""
    business_rules_created: int = 0
    business_rules_skipped: int = 0
    rate_limit_rules_created: int = 0
    rate_limit_rules_skipped: int = 0
    escalation_rules_created: int = 0
    escalation_rules_skipped: int = 0
    message: str


class PolicyEvaluationLogResponse(BaseModel):
    """Schema for policy evaluation log."""
    id: str
    company_id: Optional[str] = None
    agent_name: Optional[str] = None
    action: str
    context: Optional[Dict[str, Any]] = None
    result: str
    rules_evaluated: List[Dict[str, Any]] = Field(default_factory=list)
    matching_rule_id: Optional[str] = None
    matching_rule_name: Optional[str] = None
    rate_limit_checked: bool
    rate_limit_result: Optional[bool] = None
    escalation_triggered: bool
    escalation_rule_id: Optional[str] = None
    evaluation_time_ms: Optional[float] = None
    user_id: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class EscalationLogResponse(BaseModel):
    """Schema for escalation log."""
    id: str
    company_id: Optional[str] = None
    escalation_rule_id: Optional[str] = None
    trigger_reason: str
    trigger_context: Optional[Dict[str, Any]] = None
    action_taken: str
    action_result: Optional[Dict[str, Any]] = None
    escalated_to: List[str] = Field(default_factory=list)
    notification_sent: bool
    resolved: bool
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
