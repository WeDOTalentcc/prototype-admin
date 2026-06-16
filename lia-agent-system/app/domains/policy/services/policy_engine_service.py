"""
Policy Engine Service for Multi-Agent System.

This service provides:
- Policy evaluation for agent actions
- Rate limiting with sliding window algorithm
- Escalation workflow management
- Integration with audit and notification services
"""
import fnmatch
import logging
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.policy.repositories.policy_engine_repository import (
    PolicyEngineRepository,
)
from app.shared.observability.canary_metrics import (
    inc_policy_engine_invocation,
)
from lia_models.policy import (
    DEFAULT_BUSINESS_RULES,
    DEFAULT_ESCALATION_RULES,
    DEFAULT_RATE_LIMIT_RULES,
    BusinessRule,
    EscalationAction,
    EscalationLog,
    EscalationRule,
    PolicyEvaluationLog,
    PolicyEvaluationResult,
    RateLimitCounter,
    RateLimitRule,
    RuleType,
    TargetType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Regras setoriais Alpha 1 — Sprint III.8
# ---------------------------------------------------------------------------

# ALPHA1_SECTOR_RULES — campos de threshold removidos em 2026-06-13.
# hitl_threshold, auto_approve_threshold e max_pipeline_days vivem agora em:
#   fairness_policy_rules (Regra 9, platform_domain/screening, rule_type=decision_threshold)
# Os campos remanescentes sao exclusivos desta estrutura:
#   - autonomy_level: usado por policy_engine_service para logica de orquestracao
#   - fairness_layer3_enabled: usado por FairnessGuard.check_with_sector()
ALPHA1_SECTOR_RULES: dict = {
    "tech":       {"autonomy_level": "high",    "fairness_layer3_enabled": True},
    "varejo":     {"autonomy_level": "medium",  "fairness_layer3_enabled": True},
    "logistica":  {"autonomy_level": "medium",  "fairness_layer3_enabled": True},
    "financeiro": {"autonomy_level": "low",     "fairness_layer3_enabled": True},
    "saude":      {"autonomy_level": "low",     "fairness_layer3_enabled": True},
    "rpo":        {"autonomy_level": "high",    "fairness_layer3_enabled": True},
}


class EvaluationResult:
    """Result of policy evaluation."""
    
    def __init__(
        self,
        result: PolicyEvaluationResult,
        allowed: bool,
        reason: str | None = None,
        matching_rule: BusinessRule | None = None,
        rate_limit_status: dict[str, Any] | None = None,
        requires_approval: bool = False,
        approval_config: dict[str, Any] | None = None,
        evaluation_time_ms: float = 0.0,
        rules_evaluated: int = 0
    ):
        self.result = result
        self.allowed = allowed
        self.reason = reason
        self.matching_rule = matching_rule
        self.rate_limit_status = rate_limit_status
        self.requires_approval = requires_approval
        self.approval_config = approval_config
        self.evaluation_time_ms = evaluation_time_ms
        self.rules_evaluated = rules_evaluated
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "result": self.result.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "matching_rule": self.matching_rule.to_dict() if self.matching_rule else None,
            "rate_limit_status": self.rate_limit_status,
            "requires_approval": self.requires_approval,
            "approval_config": self.approval_config,
            "evaluation_time_ms": self.evaluation_time_ms,
            "rules_evaluated": self.rules_evaluated
        }


class RateLimitResult:
    """Result of rate limit check."""
    
    def __init__(
        self,
        allowed: bool,
        current_count: int,
        limit_value: int,
        window_seconds: int,
        remaining: int,
        reset_at: datetime | None = None,
        rule_name: str | None = None
    ):
        self.allowed = allowed
        self.current_count = current_count
        self.limit_value = limit_value
        self.window_seconds = window_seconds
        self.remaining = remaining
        self.reset_at = reset_at
        self.rule_name = rule_name
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "current_count": self.current_count,
            "limit_value": self.limit_value,
            "window_seconds": self.window_seconds,
            "remaining": self.remaining,
            "reset_at": self.reset_at.isoformat() if self.reset_at else None,
            "rule_name": self.rule_name
        }


class EscalationResult:
    """Result of escalation trigger."""
    
    def __init__(
        self,
        success: bool,
        escalation_log_id: str | None = None,
        action_taken: str | None = None,
        notifications_sent: list[str] = None,
        message: str | None = None
    ):
        self.success = success
        self.escalation_log_id = escalation_log_id
        self.action_taken = action_taken
        self.notifications_sent = notifications_sent or []
        self.message = message
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "escalation_log_id": self.escalation_log_id,
            "action_taken": self.action_taken,
            "notifications_sent": self.notifications_sent,
            "message": self.message
        }


class PolicyEngineService:
    """
    Policy Engine for evaluating business rules, rate limits, and escalations.
    """
    
    def __init__(self):
        self._rules_cache: dict[str, list[BusinessRule]] = {}
        self._cache_ttl = 300
        self._cache_timestamp: datetime | None = None
    
    async def evaluate(
        self,
        action: str,
        context: dict[str, Any],
        agent_name: str | None = None,
        company_id: str | None = None,
        user_id: str | None = None,
        check_rate_limit: bool = True,
        dry_run: bool = False
    ) -> EvaluationResult:
        """
        Evaluate whether an action is allowed based on business rules.
        
        Args:
            action: The action being performed (e.g., "add_candidate_to_vacancy")
            context: Context data for condition evaluation
            agent_name: Name of the agent performing the action
            company_id: Company ID for scoped rules
            user_id: User ID for rate limiting
            check_rate_limit: Whether to also check rate limits
            dry_run: If True, don't log the evaluation
            
        Returns:
            EvaluationResult with the decision and details
        """
        start_time = time.time()
        rules_evaluated = 0

        # Hardening C.2 -- canary signal for "V2 not called in 24h" alarm
        inc_policy_engine_invocation("evaluate")

        # Safely parse company_id to UUID — invalid strings fall back to no-tenant filter
        _company_uuid: UUID | None = None
        if company_id:
            try:
                _company_uuid = UUID(company_id)
            except (ValueError, AttributeError):
                logger.warning(
                    "[PolicyEngine] Invalid company_id format — treating as global rules: %s",
                    company_id,
                )

        async with AsyncSessionLocal() as session:
            try:
                _engine_repo = PolicyEngineRepository(session)
                rules = await _engine_repo.list_active_business_rules_for_company(
                    _company_uuid
                )
                
                matching_rule: BusinessRule | None = None
                evaluation_result = PolicyEvaluationResult.ALLOW
                reason = None
                requires_approval = False
                approval_config = None
                
                for rule in rules:
                    rules_evaluated += 1
                    
                    if not self._action_matches(action, rule.actions):
                        continue
                    
                    if self._conditions_match(rule.conditions, action, context):
                        matching_rule = rule
                        
                        if rule.rule_type == RuleType.DENY.value:
                            evaluation_result = PolicyEvaluationResult.DENY
                            reason = f"Denied by rule: {rule.name}"
                        elif rule.rule_type == RuleType.REQUIRE_APPROVAL.value:
                            evaluation_result = PolicyEvaluationResult.REQUIRE_APPROVAL
                            reason = f"Approval required by rule: {rule.name}"
                            requires_approval = True
                            approval_config = rule.approval_config
                        else:
                            evaluation_result = PolicyEvaluationResult.ALLOW
                            reason = f"Allowed by rule: {rule.name}"
                        
                        break
                
                rate_limit_status = None
                if check_rate_limit and company_id:
                    rate_result = await self.check_rate_limit(
                        target_type=TargetType.COMPANY.value,
                        target_id=company_id,
                        action=action,
                        company_id=company_id,
                        increment=not dry_run,
                        session=session
                    )
                    rate_limit_status = rate_result.to_dict()
                    
                    if not rate_result.allowed:
                        evaluation_result = PolicyEvaluationResult.RATE_LIMITED
                        reason = f"Rate limit exceeded: {rate_result.rule_name}"
                
                evaluation_time_ms = (time.time() - start_time) * 1000
                
                allowed = evaluation_result == PolicyEvaluationResult.ALLOW
                
                if not dry_run:
                    eval_log = PolicyEvaluationLog(
                        company_id=UUID(company_id) if company_id else None,
                        agent_name=agent_name,
                        action=action,
                        context=context,
                        result=evaluation_result.value,
                        rules_evaluated=[{"id": str(r.id), "name": r.name} for r in rules[:10]],
                        matching_rule_id=matching_rule.id if matching_rule else None,
                        matching_rule_name=matching_rule.name if matching_rule else None,
                        rate_limit_checked=check_rate_limit,
                        rate_limit_result=rate_limit_status.get("allowed") if rate_limit_status else None,
                        evaluation_time_ms=evaluation_time_ms,
                        user_id=UUID(user_id) if user_id else None
                    )
                    session.add(eval_log)
                    await session.commit()
                
                return EvaluationResult(
                    result=evaluation_result,
                    allowed=allowed,
                    reason=reason,
                    matching_rule=matching_rule,
                    rate_limit_status=rate_limit_status,
                    requires_approval=requires_approval,
                    approval_config=approval_config,
                    evaluation_time_ms=evaluation_time_ms,
                    rules_evaluated=rules_evaluated
                )
                
            except Exception as e:
                # rollback handled automatically by `async with AsyncSessionLocal()`
                logger.error(f"Error evaluating policy: {e}", exc_info=True)
                return EvaluationResult(
                    result=PolicyEvaluationResult.ALLOW,
                    allowed=True,
                    reason=f"Policy evaluation error (defaulting to allow): {str(e)}",
                    evaluation_time_ms=(time.time() - start_time) * 1000,
                    rules_evaluated=rules_evaluated
                )
    
    def _action_matches(self, action: str, rule_actions: list[str]) -> bool:
        """Check if action matches any of the rule's action patterns."""
        if not rule_actions:
            return True
        
        for pattern in rule_actions:
            if pattern == "*":
                return True
            if fnmatch.fnmatch(action, pattern):
                return True
            if action == pattern:
                return True
        
        return False
    
    def _conditions_match(
        self,
        conditions: dict[str, Any],
        action: str,
        context: dict[str, Any]
    ) -> bool:
        """Evaluate if the conditions match the current context."""
        if not conditions:
            return True
        
        check_field = conditions.get("check")
        operator = conditions.get("operator")
        expected_value = conditions.get("value")
        
        if not check_field or not operator:
            return True
        
        if check_field == "current_hour":
            actual_value = datetime.now().hour
        elif check_field == "is_weekend":
            actual_value = datetime.now().weekday() >= 5
        else:
            actual_value = context.get(check_field)
        
        if actual_value is None:
            return False
        
        return self._evaluate_operator(operator, actual_value, expected_value)
    
    def _evaluate_operator(self, operator: str, actual: Any, expected: Any) -> bool:
        """Evaluate an operator condition."""
        try:
            if operator == "equals":
                return actual == expected
            elif operator == "not_equals":
                return actual != expected
            elif operator == "greater_than":
                return float(actual) > float(expected)
            elif operator == "less_than":
                return float(actual) < float(expected)
            elif operator == "greater_or_equal":
                return float(actual) >= float(expected)
            elif operator == "less_or_equal":
                return float(actual) <= float(expected)
            elif operator == "between":
                if isinstance(expected, list) and len(expected) == 2:
                    return expected[0] <= float(actual) <= expected[1]
            elif operator == "not_between":
                if isinstance(expected, list) and len(expected) == 2:
                    return not (expected[0] <= float(actual) <= expected[1])
            elif operator == "contains":
                return expected in actual
            elif operator == "not_contains":
                return expected not in actual
            elif operator == "in":
                return actual in expected
            elif operator == "not_in":
                return actual not in expected
            elif operator == "matches":
                import re
                return bool(re.match(expected, str(actual)))
            return False
        except (ValueError, TypeError):
            return False
    
    async def check_rate_limit(
        self,
        target_type: str,
        target_id: str,
        action: str,
        company_id: str | None = None,
        increment: bool = True,
        session: AsyncSession | None = None
    ) -> RateLimitResult:
        """
        Check and optionally increment rate limit counter.
        
        Uses sliding window algorithm for accurate rate limiting.
        
        Args:
            target_type: Type of target (company, user, agent, action)
            target_id: ID of the target
            action: The action being performed
            company_id: Company ID for scoped rules
            increment: Whether to increment the counter
            session: Optional existing database session
            
        Returns:
            RateLimitResult with the decision and current counts
        """
        # Hardening C.2 -- canary signal (emit ANTES de qualquer early-return
        # downstream pra garantir contagem precisa de invocacoes).
        inc_policy_engine_invocation("check_rate_limit")

        async def _check(db_session: AsyncSession) -> RateLimitResult:
            _engine_repo = PolicyEngineRepository(db_session)
            _company_uuid = UUID(company_id) if company_id else None
            rules = await _engine_repo.list_active_rate_limit_rules(
                target_type=target_type,
                company_uuid=_company_uuid,
            )
            
            matching_rule: RateLimitRule | None = None
            for rule in rules:
                if rule.action_pattern:
                    if fnmatch.fnmatch(action, rule.action_pattern):
                        matching_rule = rule
                        break
                elif rule.target_id:
                    if rule.target_id == target_id:
                        matching_rule = rule
                        break
                else:
                    matching_rule = rule
                    break
            
            if not matching_rule:
                return RateLimitResult(
                    allowed=True,
                    current_count=0,
                    limit_value=0,
                    window_seconds=0,
                    remaining=0
                )
            
            target_key = f"{target_type}:{target_id}:{action}"
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=matching_rule.window_seconds)
            
            counters = await _engine_repo.list_rate_limit_counters_in_window(
                rule_id=matching_rule.id,
                target_key=target_key,
                window_start=window_start,
            )
            
            current_count = sum(c.count for c in counters)
            
            allowed = current_count < matching_rule.limit_value
            remaining = max(0, matching_rule.limit_value - current_count)
            
            if increment and allowed:
                await db_session.execute(
                    delete(RateLimitCounter).where(
                        and_(
                            RateLimitCounter.rule_id == matching_rule.id,
                            RateLimitCounter.target_key == target_key,
                            RateLimitCounter.window_start < window_start
                        )
                    )
                )
                
                window_bucket_start = now.replace(second=0, microsecond=0)
                existing_counter = next(
                    (c for c in counters if c.window_start == window_bucket_start),
                    None
                )
                
                if existing_counter:
                    existing_counter.count += 1
                    existing_counter.updated_at = now
                else:
                    new_counter = RateLimitCounter(
                        rule_id=matching_rule.id,
                        target_key=target_key,
                        count=1,
                        window_start=window_bucket_start,
                        window_end=window_bucket_start + timedelta(seconds=60)
                    )
                    db_session.add(new_counter)
                
                current_count += 1
                remaining = max(0, matching_rule.limit_value - current_count)
                
                await db_session.commit()
            
            reset_at = now + timedelta(seconds=matching_rule.window_seconds)
            
            return RateLimitResult(
                allowed=allowed,
                current_count=current_count,
                limit_value=matching_rule.limit_value,
                window_seconds=matching_rule.window_seconds,
                remaining=remaining,
                reset_at=reset_at,
                rule_name=matching_rule.name
            )
        
        if session:
            return await _check(session)
        else:
            async with AsyncSessionLocal() as new_session:
                return await _check(new_session)
    
    async def increment_counter(
        self,
        target_type: str,
        target_id: str,
        action: str,
        company_id: str | None = None
    ) -> RateLimitResult:
        """
        Increment rate limit counter and return current status.
        
        Convenience method that always increments.
        """
        return await self.check_rate_limit(
            target_type=target_type,
            target_id=target_id,
            action=action,
            company_id=company_id,
            increment=True
        )
    
    async def check_limit(
        self,
        target_type: str,
        target_id: str,
        action: str,
        company_id: str | None = None
    ) -> bool:
        """
        Check if action is within rate limit without incrementing.
        
        Returns True if allowed, False if rate limited.
        """
        result = await self.check_rate_limit(
            target_type=target_type,
            target_id=target_id,
            action=action,
            company_id=company_id,
            increment=False
        )
        return result.allowed
    
    async def trigger_escalation(
        self,
        rule_id: str | None = None,
        trigger_type: str | None = None,
        context: dict[str, Any] = None,
        company_id: str | None = None
    ) -> EscalationResult:
        """
        Trigger an escalation based on a rule or trigger type.
        
        Args:
            rule_id: Specific escalation rule ID to trigger
            trigger_type: Type of trigger (timeout, failure, threshold)
            context: Context data for the escalation
            company_id: Company ID for scoped rules
            
        Returns:
            EscalationResult with the outcome
        """
        # Hardening C.2 -- canary signal antes de any branching.
        inc_policy_engine_invocation("trigger_escalation")

        context = context or {}

        async with AsyncSessionLocal() as session:
            try:
                _engine_repo = PolicyEngineRepository(session)
                if rule_id:
                    _rule = await _engine_repo.get_active_escalation_rule_by_id(
                        UUID(rule_id)
                    )
                    rules = [_rule] if _rule else []
                elif trigger_type:
                    _company_uuid = UUID(company_id) if company_id else None
                    rules = await _engine_repo.list_escalation_rules_by_trigger(
                        trigger_type=trigger_type,
                        company_uuid=_company_uuid,
                    )
                else:
                    return EscalationResult(
                        success=False,
                        message="Either rule_id or trigger_type must be provided"
                    )
                
                if not rules:
                    return EscalationResult(
                        success=False,
                        message="No matching escalation rules found"
                    )
                
                rule = rules[0]
                
                now = datetime.utcnow()
                if rule.last_triggered:
                    cooldown_end = rule.last_triggered + timedelta(seconds=rule.cooldown_seconds)
                    if now < cooldown_end:
                        return EscalationResult(
                            success=False,
                            message=f"Escalation in cooldown until {cooldown_end.isoformat()}"
                        )
                
                notifications_sent = []
                action_result = {}
                
                if rule.escalation_action == EscalationAction.NOTIFY_MANAGER.value:
                    notifications_sent = await self._send_notifications(
                        rule.escalate_to,
                        rule.notification_template,
                        context
                    )
                    action_result["notifications"] = len(notifications_sent)
                    
                elif rule.escalation_action == EscalationAction.PAUSE_WORKFLOW.value:
                    action_result["workflow_paused"] = True
                    notifications_sent = await self._send_notifications(
                        rule.escalate_to,
                        rule.notification_template,
                        context
                    )
                    
                elif rule.escalation_action == EscalationAction.CREATE_TASK.value:
                    action_result["task_created"] = True
                    
                elif rule.escalation_action == EscalationAction.SEND_ALERT.value:
                    notifications_sent = await self._send_notifications(
                        rule.escalate_to,
                        rule.notification_template,
                        context
                    )
                    action_result["alert_sent"] = True
                
                trigger_reason = self._format_template(
                    rule.notification_template or f"Escalation triggered: {rule.name}",
                    context
                )
                
                escalation_log = EscalationLog(
                    company_id=UUID(company_id) if company_id else None,
                    escalation_rule_id=rule.id,
                    trigger_reason=trigger_reason,
                    trigger_context=context,
                    action_taken=rule.escalation_action,
                    action_result=action_result,
                    escalated_to=rule.escalate_to,
                    notification_sent=len(notifications_sent) > 0
                )
                session.add(escalation_log)
                
                rule.last_triggered = now
                
                await session.commit()
                await session.refresh(escalation_log)
                
                # pii-logs ok: nome de entidade/config (não PII per LGPD Art.5 V — pessoa natural)
                logger.info(f"Escalation triggered: {rule.name} -> {rule.escalation_action}")
                
                return EscalationResult(
                    success=True,
                    escalation_log_id=str(escalation_log.id),
                    action_taken=rule.escalation_action,
                    notifications_sent=notifications_sent,
                    message=f"Escalation '{rule.name}' triggered successfully"
                )
                
            except Exception as e:
                # rollback handled automatically by `async with AsyncSessionLocal()`
                logger.error(f"Error triggering escalation: {e}", exc_info=True)
                return EscalationResult(
                    success=False,
                    message=f"Error triggering escalation: {str(e)}"
                )
    
    async def _send_notifications(
        self,
        recipients: list[str],
        template: str | None,
        context: dict[str, Any]
    ) -> list[str]:
        """Send notifications to recipients. Returns list of sent notification IDs."""
        notifications_sent = []
        
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService()
            
            message = self._format_template(template or "Escalation triggered", context)
            
            for recipient in recipients:
                try:
                    await notification_service.send_notification(
                        user_id=recipient,
                        title="Escalação - Ação Necessária",
                        message=message,
                        notification_type="urgent",
                        priority="high",
                        source_agent="policy_engine"
                    )
                    notifications_sent.append(f"notification:{recipient}")
                except Exception as e:
                    # pii-logs ok: email/phone mascarado em runtime via PIIMaskingFilter (LGPD Art.46 + ADR-006 defesa em profundidade)
                    logger.warning(f"Failed to send notification to {recipient}: {e}")
                    
        except Exception as e:
            logger.warning(f"Could not send notifications: {e}")
        
        return notifications_sent
    
    def _format_template(self, template: str, context: dict[str, Any]) -> str:
        """Format a notification template with context variables."""
        try:
            for key, value in context.items():
                template = template.replace(f"{{{key}}}", str(value))
            return template
        except Exception:
            return template
    
    async def pre_execute_check(
        self,
        agent_name: str,
        action: str,
        context: dict[str, Any],
        company_id: str | None = None,
        user_id: str | None = None
    ) -> tuple[bool, str | None, dict[str, Any] | None]:
        """
        Pre-execution check for agent actions.
        
        Args:
            agent_name: Name of the agent
            action: Action to be executed
            context: Execution context
            company_id: Company ID
            user_id: User ID
            
        Returns:
            Tuple of (allowed, reason, approval_config)
        """
        result = await self.evaluate(
            action=action,
            context=context,
            agent_name=agent_name,
            company_id=company_id,
            user_id=user_id
        )
        
        approval_config = result.approval_config if result.requires_approval else None
        
        return (result.allowed, result.reason, approval_config)
    
    async def load_default_rules(self) -> dict[str, int]:
        """
        Load default rules from configuration into the database.
        
        Returns dict with counts of created/skipped rules.
        """
        async with AsyncSessionLocal() as session:
            stats = {
                "business_rules_created": 0,
                "business_rules_skipped": 0,
                "rate_limit_rules_created": 0,
                "rate_limit_rules_skipped": 0,
                "escalation_rules_created": 0,
                "escalation_rules_skipped": 0
            }
            
            try:
                _engine_repo = PolicyEngineRepository(session)
                for rule_data in DEFAULT_BUSINESS_RULES:
                    if await _engine_repo.get_business_rule_by_name(rule_data["name"]):
                        stats["business_rules_skipped"] += 1
                        continue
                    
                    rule = BusinessRule(
                        name=rule_data["name"],
                        description=rule_data.get("description"),
                        rule_type=rule_data["rule_type"],
                        conditions=rule_data["conditions"],
                        actions=rule_data["actions"],
                        priority=rule_data.get("priority", 100),
                        approval_config=rule_data.get("approval_config"),
                        is_active=True
                    )
                    session.add(rule)
                    stats["business_rules_created"] += 1
                
                for rule_data in DEFAULT_RATE_LIMIT_RULES:
                    if await _engine_repo.get_rate_limit_rule_by_name(rule_data["name"]):
                        stats["rate_limit_rules_skipped"] += 1
                        continue
                    
                    rule = RateLimitRule(
                        name=rule_data["name"],
                        description=rule_data.get("description"),
                        target_type=rule_data["target_type"],
                        action_pattern=rule_data.get("action_pattern"),
                        limit_value=rule_data["limit_value"],
                        window_seconds=rule_data["window_seconds"],
                        is_active=True
                    )
                    session.add(rule)
                    stats["rate_limit_rules_created"] += 1
                
                for rule_data in DEFAULT_ESCALATION_RULES:
                    if await _engine_repo.get_escalation_rule_by_name(rule_data["name"]):
                        stats["escalation_rules_skipped"] += 1
                        continue
                    
                    rule = EscalationRule(
                        name=rule_data["name"],
                        description=rule_data.get("description"),
                        trigger_type=rule_data["trigger_type"],
                        condition=rule_data["condition"],
                        escalate_to=rule_data["escalate_to"],
                        escalation_action=rule_data["escalation_action"],
                        notification_template=rule_data.get("notification_template"),
                        cooldown_seconds=rule_data.get("cooldown_seconds", 3600),
                        is_active=True
                    )
                    session.add(rule)
                    stats["escalation_rules_created"] += 1
                
                await session.commit()
                
                logger.info(f"Default rules loaded: {stats}")
                return stats
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error loading default rules: {e}", exc_info=True)
                raise


    async def apply_industry_defaults(self, sector: str) -> dict:
        """
        Aplica defaults setoriais para política da empresa.
        Delega para PolicyEngine.apply_industry_defaults().

        WT-2022 Phase 2 audit (2026-05-21):
        --------------------------------------------------------------
        Esta delegação ao V1 PolicyEngine é instanciação real (não import
        de constante). O dataset SECTOR_DEFAULTS + DEFAULT_POLICIES vive
        em `app/orchestrator/policy_engine.py` como classvars do V1.

        Para deletar V1 (Q3 2026), antes:
          1. Mover SECTOR_DEFAULTS + DEFAULT_POLICIES para
             `lia_models/policy.py` como constantes módulo-level
             (CANONICAL_SECTOR_DEFAULTS, CANONICAL_DEFAULT_POLICIES).
          2. Substituir esta delegação por lookup direto:
                from lia_models.policy import (
                    CANONICAL_SECTOR_DEFAULTS,
                    CANONICAL_DEFAULT_POLICIES,
                )
                key = (sector or "").lower().strip()
                return dict(CANONICAL_SECTOR_DEFAULTS.get(
                    key, CANONICAL_DEFAULT_POLICIES))
          3. Mesma substituição em `save_policy_block` abaixo.
          4. Remover ambos imports V1 (linhas marcadas TODO(WT-2022-P2)).
          5. Atualizar EXEMPT_RELATIVE em scripts/check_no_v1_policy_engine.py
             removendo policy_engine_service.py (vira limpo, sem fallback).
        Ver ADR-WT-2022 Phase 2 checklist para sequência completa.
        --------------------------------------------------------------
        """
        # W1-003 (2026-05-22): V1 deletado. Canonical lookup em lia_models.policy.
        from lia_models.policy import (
            CANONICAL_DEFAULT_POLICIES,
            CANONICAL_SECTOR_DEFAULTS,
        )

        sector_key = (sector or "").lower().strip()
        defaults = CANONICAL_SECTOR_DEFAULTS.get(
            sector_key, CANONICAL_DEFAULT_POLICIES
        )
        logger.info(
            f"PolicyEngineService.apply_industry_defaults: "
            f"sector={sector_key!r} → keys={list(defaults.keys())}"
        )
        return dict(defaults)

    async def save_policy_block(
        self,
        company_id: str,
        sector: str,
        db: AsyncSession | None = None,
    ) -> dict:
        """
        Persiste os defaults setoriais em CompanyHiringPolicy.

        Mapeia SECTOR_DEFAULTS[sector] para os blocos de CompanyHiringPolicy:
        - automation_rules: autonomy_level, auto_screening, auto_stage_advance
        - screening_rules: limites de triagem e busca

        Idempotente: upsert seguro mesmo rodando múltiplas vezes.

        Args:
            company_id: UUID da empresa (multi-tenant obrigatório)
            sector: Setor (tech | varejo | logistica | financeiro | saude | rpo)
            db: Sessão SQLAlchemy (cria nova se None)

        Returns:
            Dict com os campos atualizados em CompanyHiringPolicy.
        """
        import uuid as _uuid

        from sqlalchemy import select

        from lia_models.company_hiring_policy import CompanyHiringPolicy
        # W1-003 (2026-05-22): V1 deletado. Canonical lookup em lia_models.policy.
        from lia_models.policy import (
            CANONICAL_DEFAULT_POLICIES,
            CANONICAL_SECTOR_DEFAULTS,
        )

        sector_key = (sector or "").lower().strip()
        defaults = dict(
            CANONICAL_SECTOR_DEFAULTS.get(sector_key, CANONICAL_DEFAULT_POLICIES)
        )

        # Mapeamento sector_defaults → CompanyHiringPolicy blocks
        automation_patch = {
            "auto_screening": True,
            "auto_stage_advance": defaults.get("max_concurrent_requests", 5) >= 10,
            "autonomy_level": (
                "high" if defaults.get("max_concurrent_requests", 5) >= 20
                else "medium" if defaults.get("max_concurrent_requests", 5) >= 5
                else "low"
            ),
        }
        screening_patch = {
            "max_pearch_searches_per_day": defaults.get("max_pearch_searches_per_day", 10),
            "max_voice_screenings_per_day": defaults.get("max_voice_screenings_per_day", 20),
            "max_tokens_per_request": defaults.get("max_tokens_per_request", 50000),
            "allow_global_search": defaults.get("allow_global_search", True),
            "require_approval_for_bulk_email": defaults.get("require_approval_for_bulk_email", True),
        }

        async def _upsert(session: AsyncSession) -> dict:
            from app.domains.hiring_policy.repositories.hiring_policy_repository import (
                HiringPolicyRepository,
            )
            _hp_repo = HiringPolicyRepository(session)
            policy = await _hp_repo.get_by_company(company_id)

            if policy:
                existing_automation = dict(policy.automation_rules or {})
                existing_automation.update(automation_patch)
                policy.automation_rules = existing_automation

                existing_screening = dict(policy.screening_rules or {})
                existing_screening.update(screening_patch)
                policy.screening_rules = existing_screening
            else:
                policy = CompanyHiringPolicy(
                    id=_uuid.uuid4(),
                    company_id=company_id,
                    automation_rules=automation_patch,
                    screening_rules=screening_patch,
                    created_by="policy_engine_alpha1",
                )
                session.add(policy)

            await session.flush()
            await session.commit()
            logger.info(
                f"PolicyEngineService.save_policy_block: company={company_id} sector={sector!r} saved"
            )
            return {
                "company_id": company_id,
                "sector": sector,
                "automation_rules": policy.automation_rules,
                "screening_rules": policy.screening_rules,
            }

        if db is not None:
            return await _upsert(db)

        async with AsyncSessionLocal() as session:
            return await _upsert(session)


def require_policy_check(action: str, context_extractor=None):
    """
    Decorator for enforcing policy checks on agent actions.
    
    Usage:
        @require_policy_check("add_candidate_to_vacancy")
        async def add_candidate(self, candidate_id: str, vacancy_id: str):
            ...
            
        @require_policy_check(
            "bulk_reject_candidates",
            context_extractor=lambda args: {"candidate_count": len(args[1])}
        )
        async def bulk_reject(self, candidate_ids: List[str]):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            context = {}
            if context_extractor:
                try:
                    context = context_extractor(args, kwargs)
                except Exception as e:
                    logger.warning(f"Error extracting context: {e}")
            
            # TENANT-FALLBACK-OK: self.company_id set in PolicyEngineService ctor from RLS-validated context
            company_id = getattr(self, 'company_id', None)
            if not company_id:
                company_id = kwargs.get('company_id')
            
            agent_name = getattr(self, 'name', None) or getattr(self, 'agent_type', None)
            if agent_name and hasattr(agent_name, 'value'):
                agent_name = agent_name.value
            
            policy_engine = PolicyEngineService()
            allowed, reason, approval_config = await policy_engine.pre_execute_check(
                agent_name=str(agent_name) if agent_name else "unknown",
                action=action,
                context=context,
                company_id=str(company_id) if company_id else None
            )
            
            if not allowed:
                if approval_config:
                    raise PolicyApprovalRequired(
                        action=action,
                        reason=reason,
                        approval_config=approval_config
                    )
                else:
                    raise PolicyDenied(action=action, reason=reason)
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


class PolicyDenied(Exception):
    """Exception raised when a policy denies an action."""
    
    def __init__(self, action: str, reason: str):
        self.action = action
        self.reason = reason
        super().__init__(f"Action '{action}' denied: {reason}")


class PolicyApprovalRequired(Exception):
    """Exception raised when a policy requires approval for an action."""
    
    def __init__(self, action: str, reason: str, approval_config: dict[str, Any]):
        self.action = action
        self.reason = reason
        self.approval_config = approval_config
        super().__init__(f"Action '{action}' requires approval: {reason}")


policy_engine = PolicyEngineService()


def get_policy_engine_service() -> "PolicyEngineService":
    return policy_engine
