"""Coverage tests for app/schemas/policy.py — Pydantic schemas and enums."""
import pytest
from app.schemas.policy import (
    RuleTypeEnum,
    TargetTypeEnum,
    TriggerTypeEnum,
    EscalationActionEnum,
    PolicyEvaluationResultEnum,
    BusinessRuleCreate,
    BusinessRuleUpdate,
    BusinessRuleResponse,
    RateLimitRuleCreate,
    RateLimitRuleUpdate,
    RateLimitRuleResponse,
    EscalationRuleCreate,
    EscalationRuleUpdate,
    EscalationRuleResponse,
    PolicyEvaluateRequest,
    PolicyEvaluateResponse,
    RateLimitCheckRequest,
    RateLimitCheckResponse,
    EscalationTriggerRequest,
    EscalationTriggerResponse,
    PolicyListResponse,
    PolicySeedResponse,
)


class TestRuleTypeEnum:
    def test_allow_value(self):
        assert RuleTypeEnum.ALLOW == "allow"

    def test_deny_value(self):
        assert RuleTypeEnum.DENY == "deny"

    def test_require_approval_value(self):
        assert RuleTypeEnum.REQUIRE_APPROVAL == "require_approval"


class TestTargetTypeEnum:
    def test_company(self):
        assert TargetTypeEnum.COMPANY == "company"

    def test_user(self):
        assert TargetTypeEnum.USER == "user"

    def test_agent(self):
        assert TargetTypeEnum.AGENT == "agent"

    def test_action(self):
        assert TargetTypeEnum.ACTION == "action"


class TestTriggerTypeEnum:
    def test_timeout(self):
        assert TriggerTypeEnum.TIMEOUT == "timeout"

    def test_failure(self):
        assert TriggerTypeEnum.FAILURE == "failure"

    def test_sla_breach(self):
        assert TriggerTypeEnum.SLA_BREACH == "sla_breach"

    def test_failure_count(self):
        assert TriggerTypeEnum.FAILURE_COUNT == "failure_count"

    def test_threshold(self):
        assert TriggerTypeEnum.THRESHOLD == "threshold"


class TestEscalationActionEnum:
    def test_notify_manager(self):
        assert EscalationActionEnum.NOTIFY_MANAGER == "notify_manager"

    def test_pause_workflow(self):
        assert EscalationActionEnum.PAUSE_WORKFLOW == "pause_workflow"

    def test_send_alert(self):
        assert EscalationActionEnum.SEND_ALERT == "send_alert"

    def test_notify_admin(self):
        assert EscalationActionEnum.NOTIFY_ADMIN == "notify_admin"

    def test_require_review(self):
        assert EscalationActionEnum.REQUIRE_REVIEW == "require_review"


class TestPolicyEvaluationResultEnum:
    def test_allow(self):
        assert PolicyEvaluationResultEnum.ALLOW == "allow"

    def test_deny(self):
        assert PolicyEvaluationResultEnum.DENY == "deny"

    def test_rate_limited(self):
        assert PolicyEvaluationResultEnum.RATE_LIMITED == "rate_limited"

    def test_require_approval(self):
        assert PolicyEvaluationResultEnum.REQUIRE_APPROVAL == "require_approval"


class TestBusinessRuleCreate:
    def test_minimal(self):
        m = BusinessRuleCreate(name="Test Rule")
        assert m.name == "Test Rule"
        assert m.is_active is True
        assert m.priority == 100

    def test_custom_rule_type(self):
        m = BusinessRuleCreate(name="Block Rule", rule_type=RuleTypeEnum.DENY)
        assert m.rule_type == "deny"

    def test_default_conditions_empty(self):
        m = BusinessRuleCreate(name="Rule")
        assert m.conditions == {}

    def test_with_company_id(self):
        m = BusinessRuleCreate(name="Company Rule", company_id="company-123")
        assert m.company_id == "company-123"

    def test_with_approval_config(self):
        m = BusinessRuleCreate(
            name="Approval Rule",
            rule_type=RuleTypeEnum.REQUIRE_APPROVAL,
            approval_config={"approvers": ["manager"]},
        )
        assert m.approval_config is not None

    def test_with_actions(self):
        m = BusinessRuleCreate(name="Rule", actions=["notify", "log"])
        assert m.actions == ["notify", "log"]


class TestBusinessRuleUpdate:
    def test_all_optional(self):
        m = BusinessRuleUpdate()
        assert m.name is None
        assert m.is_active is None

    def test_update_name(self):
        m = BusinessRuleUpdate(name="Updated Name")
        assert m.name == "Updated Name"

    def test_update_is_active(self):
        m = BusinessRuleUpdate(is_active=False)
        assert m.is_active is False

    def test_update_rule_type(self):
        m = BusinessRuleUpdate(rule_type=RuleTypeEnum.DENY)
        assert m.rule_type == "deny"


class TestBusinessRuleResponse:
    def test_basic(self):
        m = BusinessRuleResponse(
            id="rule-001",
            name="My Rule",
            rule_type="allow",
            conditions={},
            actions=[],
            priority=100,
            is_active=True,
        )
        assert m.id == "rule-001"
        assert m.rule_type == "allow"

    def test_optional_fields(self):
        m = BusinessRuleResponse(
            id="r1", name="R1", rule_type="deny",
            conditions={}, actions=[], priority=50, is_active=False,
        )
        assert m.description is None
        assert m.company_id is None


class TestRateLimitRuleCreate:
    def test_basic(self):
        m = RateLimitRuleCreate(
            name="Rate Limit",
            target_type=TargetTypeEnum.COMPANY,
            limit_value=100,
            window_seconds=3600,
        )
        assert m.limit_value == 100
        assert m.window_seconds == 3600

    def test_defaults(self):
        m = RateLimitRuleCreate(
            name="RL",
            target_type=TargetTypeEnum.USER,
            limit_value=50,
            window_seconds=60,
        )
        assert m.is_active is True

    def test_with_burst_limit(self):
        m = RateLimitRuleCreate(
            name="Burst RL",
            target_type=TargetTypeEnum.AGENT,
            limit_value=100,
            window_seconds=60,
            burst_limit=150,
        )
        assert m.burst_limit == 150


class TestRateLimitRuleUpdate:
    def test_all_optional(self):
        m = RateLimitRuleUpdate()
        assert m.limit_value is None

    def test_update_limit(self):
        m = RateLimitRuleUpdate(limit_value=200)
        assert m.limit_value == 200


class TestEscalationRuleCreate:
    def test_basic(self):
        m = EscalationRuleCreate(
            name="Escalation Rule",
            trigger_type=TriggerTypeEnum.FAILURE,
            escalation_action=EscalationActionEnum.NOTIFY_MANAGER,
        )
        assert m.name == "Escalation Rule"
        assert m.cooldown_seconds == 3600  # default

    def test_with_condition(self):
        m = EscalationRuleCreate(
            name="Threshold Rule",
            trigger_type=TriggerTypeEnum.THRESHOLD,
            escalation_action=EscalationActionEnum.SEND_ALERT,
            condition={"threshold": 0.9},
        )
        assert m.condition["threshold"] == pytest.approx(0.9)

    def test_with_cooldown(self):
        m = EscalationRuleCreate(
            name="Fast Escalation",
            trigger_type=TriggerTypeEnum.SLA_BREACH,
            escalation_action=EscalationActionEnum.NOTIFY_ADMIN,
            cooldown_seconds=300,
        )
        assert m.cooldown_seconds == 300


class TestEscalationRuleUpdate:
    def test_all_optional(self):
        m = EscalationRuleUpdate()
        assert m.name is None

    def test_update_action(self):
        m = EscalationRuleUpdate(escalation_action=EscalationActionEnum.PAUSE_WORKFLOW)
        assert m.escalation_action == "pause_workflow"


class TestPolicyEvaluateRequest:
    def test_basic(self):
        m = PolicyEvaluateRequest(action="send_message")
        assert m.action == "send_message"

    def test_with_context(self):
        m = PolicyEvaluateRequest(
            action="bulk_email",
            context={"recipient_count": 500},
            company_id="co-001",
        )
        assert m.context["recipient_count"] == 500

    def test_defaults(self):
        m = PolicyEvaluateRequest(action="read")
        assert m.check_rate_limit is True
        assert m.dry_run is False


class TestPolicyEvaluateResponse:
    def test_basic_allowed(self):
        m = PolicyEvaluateResponse(
            result=PolicyEvaluationResultEnum.ALLOW,
            allowed=True,
            evaluation_time_ms=1.5,
            rules_evaluated=3,
        )
        assert m.allowed is True
        assert m.rules_evaluated == 3

    def test_denied(self):
        m = PolicyEvaluateResponse(
            result=PolicyEvaluationResultEnum.DENY,
            allowed=False,
            evaluation_time_ms=0.8,
            rules_evaluated=1,
            reason="Rate limit exceeded",
        )
        assert m.allowed is False
        assert m.reason == "Rate limit exceeded"


class TestRateLimitCheckRequest:
    def test_basic(self):
        m = RateLimitCheckRequest(
            target_type=TargetTypeEnum.COMPANY,
            target_id="company-001",
            action="api_call",
        )
        assert m.action == "api_call"

    def test_increment_default_true(self):
        m = RateLimitCheckRequest(
            target_type=TargetTypeEnum.USER,
            target_id="user-001",
            action="chat",
        )
        assert m.increment is True


class TestRateLimitCheckResponse:
    def test_allowed(self):
        m = RateLimitCheckResponse(
            allowed=True,
            current_count=5,
            limit_value=100,
            window_seconds=3600,
            remaining=95,
        )
        assert m.allowed is True
        assert m.remaining == 95

    def test_not_allowed(self):
        m = RateLimitCheckResponse(
            allowed=False,
            current_count=100,
            limit_value=100,
            window_seconds=3600,
            remaining=0,
            reset_at="2026-05-10T12:00:00Z",
        )
        assert m.remaining == 0
        assert m.reset_at is not None


class TestEscalationTriggerRequest:
    def test_basic(self):
        m = EscalationTriggerRequest(
            trigger_type=TriggerTypeEnum.SLA_BREACH,
            context={"sla_hours": 48},
        )
        assert m.trigger_type == "sla_breach"

    def test_with_rule_id(self):
        m = EscalationTriggerRequest(rule_id="esc-rule-001")
        assert m.rule_id == "esc-rule-001"

    def test_empty(self):
        m = EscalationTriggerRequest()
        assert m.context == {}


class TestEscalationTriggerResponse:
    def test_success(self):
        m = EscalationTriggerResponse(
            success=True,
            action_taken="notify_manager",
        )
        assert m.success is True

    def test_failure(self):
        m = EscalationTriggerResponse(success=False)
        assert m.success is False
        assert m.escalation_log_id is None


class TestPolicyListResponse:
    def test_defaults(self):
        m = PolicyListResponse()
        assert m.business_rules == []
        assert m.total_business_rules == 0

    def test_with_totals(self):
        m = PolicyListResponse(total_business_rules=5, total_rate_limit_rules=3)
        assert m.total_business_rules == 5


class TestPolicySeedResponse:
    def test_basic(self):
        m = PolicySeedResponse(message="Seeded successfully")
        assert m.message == "Seeded successfully"
        assert m.business_rules_created == 0

    def test_with_counts(self):
        m = PolicySeedResponse(
            message="Done",
            business_rules_created=10,
            rate_limit_rules_created=5,
        )
        assert m.business_rules_created == 10
