"""
Pydantic schemas for Policy Engine API.
"""
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class RuleTypeEnum(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class TargetTypeEnum(StrEnum):
    COMPANY = "company"
    USER = "user"
    AGENT = "agent"
    ACTION = "action"


class TriggerTypeEnum(StrEnum):
    TIMEOUT = "timeout"
    FAILURE = "failure"
    FAILURE_COUNT = "failure_count"
    THRESHOLD = "threshold"
    SLA_BREACH = "sla_breach"


class EscalationActionEnum(StrEnum):
    NOTIFY_MANAGER = "notify_manager"
    NOTIFY_ADMIN = "notify_admin"
    PAUSE_WORKFLOW = "pause_workflow"
    REQUIRE_REVIEW = "require_review"
    SEND_ALERT = "send_alert"
    CREATE_TASK = "create_task"


class PolicyEvaluationResultEnum(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    RATE_LIMITED = "rate_limited"


class BusinessRuleCreate(WeDoBaseModel):
    """Schema for creating a business rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    rule_type: RuleTypeEnum = RuleTypeEnum.ALLOW
    conditions: dict[str, Any] = Field(default_factory=dict)
    actions: list[str] = Field(default_factory=list)
    priority: int = Field(default=100, ge=1, le=1000)
    approval_config: dict[str, Any] | None = None
    is_active: bool = True
    rule_metadata: dict[str, Any] | None = None


class BusinessRuleUpdate(WeDoBaseModel):
    """Schema for updating a business rule."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    rule_type: RuleTypeEnum | None = None
    conditions: dict[str, Any] | None = None
    actions: list[str] | None = None
    priority: int | None = Field(None, ge=1, le=1000)
    approval_config: dict[str, Any] | None = None
    is_active: bool | None = None
    rule_metadata: dict[str, Any] | None = None


class BusinessRuleResponse(BaseModel):
    """Schema for business rule response."""
    id: str
    company_id: str | None = None
    name: str
    description: str | None = None
    rule_type: str
    conditions: dict[str, Any]
    actions: list[str]
    priority: int
    approval_config: dict[str, Any] | None = None
    is_active: bool
    rule_metadata: dict[str, Any] | None = None
    created_at: str | None = None
    updated_at: str | None = None
    created_by: str | None = None

    class Config:
        from_attributes = True


class RateLimitRuleCreate(WeDoBaseModel):
    """Schema for creating a rate limit rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    target_type: TargetTypeEnum
    target_id: str | None = None
    action_pattern: str | None = None
    limit_value: int = Field(..., ge=1)
    window_seconds: int = Field(..., ge=1)
    burst_limit: int | None = None
    is_active: bool = True


class RateLimitRuleUpdate(WeDoBaseModel):
    """Schema for updating a rate limit rule."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target_type: TargetTypeEnum | None = None
    target_id: str | None = None
    action_pattern: str | None = None
    limit_value: int | None = Field(None, ge=1)
    window_seconds: int | None = Field(None, ge=1)
    burst_limit: int | None = None
    is_active: bool | None = None


class RateLimitRuleResponse(BaseModel):
    """Schema for rate limit rule response."""
    id: str
    company_id: str | None = None
    name: str
    description: str | None = None
    target_type: str
    target_id: str | None = None
    action_pattern: str | None = None
    limit_value: int
    window_seconds: int
    current_count: int
    window_start: str | None = None
    burst_limit: int | None = None
    is_active: bool
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class EscalationRuleCreate(WeDoBaseModel):
    """Schema for creating an escalation rule."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    trigger_type: TriggerTypeEnum
    condition: dict[str, Any] = Field(default_factory=dict)
    escalate_to: list[str] = Field(default_factory=list)
    escalation_action: EscalationActionEnum = EscalationActionEnum.NOTIFY_MANAGER
    notification_template: str | None = None
    cooldown_seconds: int = Field(default=3600, ge=0)
    priority: int = Field(default=100, ge=1, le=1000)
    is_active: bool = True


class EscalationRuleUpdate(WeDoBaseModel):
    """Schema for updating an escalation rule."""
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    trigger_type: TriggerTypeEnum | None = None
    condition: dict[str, Any] | None = None
    escalate_to: list[str] | None = None
    escalation_action: EscalationActionEnum | None = None
    notification_template: str | None = None
    cooldown_seconds: int | None = Field(None, ge=0)
    priority: int | None = Field(None, ge=1, le=1000)
    is_active: bool | None = None


class EscalationRuleResponse(BaseModel):
    """Schema for escalation rule response."""
    id: str
    company_id: str | None = None
    name: str
    description: str | None = None
    trigger_type: str
    condition: dict[str, Any]
    escalate_to: list[str]
    escalation_action: str
    notification_template: str | None = None
    cooldown_seconds: int
    last_triggered: str | None = None
    is_active: bool
    priority: int
    created_at: str | None = None
    updated_at: str | None = None

    class Config:
        from_attributes = True


class PolicyEvaluateRequest(WeDoBaseModel):
    """Schema for policy evaluation request."""
    action: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)
    agent_name: str | None = None
    user_id: str | None = None
    check_rate_limit: bool = True
    dry_run: bool = False


class PolicyEvaluateResponse(BaseModel):
    """Schema for policy evaluation response."""
    result: PolicyEvaluationResultEnum
    allowed: bool
    reason: str | None = None
    matching_rule: BusinessRuleResponse | None = None
    rate_limit_status: dict[str, Any] | None = None
    requires_approval: bool = False
    approval_config: dict[str, Any] | None = None
    evaluation_time_ms: float
    rules_evaluated: int


class RateLimitCheckRequest(WeDoBaseModel):
    """Schema for rate limit check request."""
    target_type: TargetTypeEnum
    target_id: str
    action: str
    increment: bool = True


class RateLimitCheckResponse(BaseModel):
    """Schema for rate limit check response."""
    allowed: bool
    current_count: int
    limit_value: int
    window_seconds: int
    remaining: int
    reset_at: str | None = None
    rule_name: str | None = None


class EscalationTriggerRequest(WeDoBaseModel):
    """Schema for escalation trigger request."""
    rule_id: str | None = None
    trigger_type: TriggerTypeEnum | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class EscalationTriggerResponse(BaseModel):
    """Schema for escalation trigger response."""
    success: bool
    escalation_log_id: str | None = None
    action_taken: str | None = None
    notifications_sent: list[str] = Field(default_factory=list)
    message: str | None = None


class PolicyListResponse(BaseModel):
    """Schema for listing policies."""
    business_rules: list[BusinessRuleResponse] = Field(default_factory=list)
    rate_limit_rules: list[RateLimitRuleResponse] = Field(default_factory=list)
    escalation_rules: list[EscalationRuleResponse] = Field(default_factory=list)
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
    company_id: str | None = None
    agent_name: str | None = None
    action: str
    context: dict[str, Any] | None = None
    result: str
    rules_evaluated: list[dict[str, Any]] = Field(default_factory=list)
    matching_rule_id: str | None = None
    matching_rule_name: str | None = None
    rate_limit_checked: bool
    rate_limit_result: bool | None = None
    escalation_triggered: bool
    escalation_rule_id: str | None = None
    evaluation_time_ms: float | None = None
    user_id: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True


class EscalationLogResponse(BaseModel):
    """Schema for escalation log."""
    id: str
    company_id: str | None = None
    escalation_rule_id: str | None = None
    trigger_reason: str
    trigger_context: dict[str, Any] | None = None
    action_taken: str
    action_result: dict[str, Any] | None = None
    escalated_to: list[str] = Field(default_factory=list)
    notification_sent: bool
    resolved: bool
    resolved_at: str | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True
