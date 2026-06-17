"""
Policy Engine Models for Multi-Agent System.

This module provides models for:
- BusinessRule: Business rules for agent actions (allow/deny/require_approval)
- RateLimitRule: Rate limiting rules per company/user/agent/action
- EscalationRule: Escalation rules for timeouts, failures, thresholds
- PolicyEvaluationLog: Audit log for policy evaluations
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from lia_config.database import Base
import enum
import uuid


class RuleType(str, enum.Enum):
    """Types of business rules."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class TargetType(str, enum.Enum):
    """Target types for rate limiting."""
    COMPANY = "company"
    USER = "user"
    AGENT = "agent"
    ACTION = "action"


class TriggerType(str, enum.Enum):
    """Trigger types for escalation rules."""
    TIMEOUT = "timeout"
    FAILURE = "failure"
    FAILURE_COUNT = "failure_count"
    THRESHOLD = "threshold"
    SLA_BREACH = "sla_breach"


class EscalationAction(str, enum.Enum):
    """Actions to take on escalation."""
    NOTIFY_MANAGER = "notify_manager"
    NOTIFY_ADMIN = "notify_admin"
    PAUSE_WORKFLOW = "pause_workflow"
    REQUIRE_REVIEW = "require_review"
    SEND_ALERT = "send_alert"
    CREATE_TASK = "create_task"


class PolicyEvaluationResult(str, enum.Enum):
    """Result of policy evaluation."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    RATE_LIMITED = "rate_limited"


class BusinessRule(Base):
    """
    Business rules for controlling agent actions.
    
    Rules define conditions under which actions are allowed, denied,
    or require approval. Evaluated by priority order (lower = higher priority).
    """
    __tablename__ = "business_rules"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: BusinessRule com company_id NULL = regra global do sistema (default cross-tenant)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    rule_type = Column(String(50), nullable=False, default="allow")
    
    conditions = Column(JSON, nullable=False, default={})
    
    actions = Column(ARRAY(String), nullable=False, default=[])
    
    priority = Column(Integer, nullable=False, default=100)
    
    approval_config = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    rule_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    def __repr__(self):
        return f"<BusinessRule {self.name} ({self.rule_type})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "name": self.name,
            "description": self.description,
            "rule_type": self.rule_type,
            "conditions": self.conditions,
            "actions": self.actions,
            "priority": self.priority,
            "approval_config": self.approval_config,
            "is_active": self.is_active,
            "rule_metadata": self.rule_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
        }


class RateLimitRule(Base):
    """
    Rate limiting rules for API calls, messages, and other actions.
    
    Uses sliding window algorithm for accurate rate limiting.
    """
    __tablename__ = "rate_limit_rules"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: RateLimitRule com company_id NULL = rate limit global do sistema
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    target_type = Column(String(50), nullable=False)
    target_id = Column(String(255), nullable=True, index=True)
    
    action_pattern = Column(String(255), nullable=True)
    
    limit_value = Column(Integer, nullable=False)
    window_seconds = Column(Integer, nullable=False)
    
    current_count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=True)
    
    burst_limit = Column(Integer, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RateLimitRule {self.name} ({self.target_type}:{self.limit_value}/{self.window_seconds}s)>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "name": self.name,
            "description": self.description,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "action_pattern": self.action_pattern,
            "limit_value": self.limit_value,
            "window_seconds": self.window_seconds,
            "current_count": self.current_count,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "burst_limit": self.burst_limit,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RateLimitCounter(Base):
    """
    Individual rate limit counters for sliding window tracking.
    Each counter tracks a specific target's usage within a time window.
    """
    __tablename__ = "rate_limit_counters"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("rate_limit_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    
    target_key = Column(String(500), nullable=False, index=True)
    
    count = Column(Integer, default=0)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RateLimitCounter {self.target_key}: {self.count}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "rule_id": str(self.rule_id),
            "target_key": self.target_key,
            "count": self.count,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EscalationRule(Base):
    """
    Escalation rules for handling timeouts, failures, and threshold breaches.
    
    Defines triggers and actions for escalating issues to managers or admins.
    """
    __tablename__ = "escalation_rules"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: EscalationRule com company_id NULL = escalation policy global do sistema
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_type = Column(String(50), nullable=False)
    
    condition = Column(JSON, nullable=False, default={})
    
    escalate_to = Column(ARRAY(String), nullable=False, default=[])
    
    escalation_action = Column(String(50), nullable=False, default="notify_manager")
    
    notification_template = Column(Text, nullable=True)
    
    cooldown_seconds = Column(Integer, default=3600)
    last_triggered = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True, index=True)
    
    priority = Column(Integer, default=100)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<EscalationRule {self.name} ({self.trigger_type})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "condition": self.condition,
            "escalate_to": self.escalate_to,
            "escalation_action": self.escalation_action,
            "notification_template": self.notification_template,
            "cooldown_seconds": self.cooldown_seconds,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PolicyEvaluationLog(Base):
    """
    Audit log for policy evaluations.
    
    Tracks every policy evaluation for transparency and debugging.
    """
    __tablename__ = "policy_evaluation_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: PolicyEvaluationLog cross-tenant analytics (auditor WeDOTalent)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    agent_name = Column(String(100), nullable=True)
    action = Column(String(255), nullable=False)
    
    context = Column(JSON, nullable=True)
    
    result = Column(String(50), nullable=False)
    
    rules_evaluated = Column(JSON, default=[])
    matching_rule_id = Column(UUID(as_uuid=True), nullable=True)
    matching_rule_name = Column(String(255), nullable=True)
    
    rate_limit_checked = Column(Boolean, default=False)
    rate_limit_result = Column(Boolean, nullable=True)
    
    escalation_triggered = Column(Boolean, default=False)
    escalation_rule_id = Column(UUID(as_uuid=True), nullable=True)
    
    evaluation_time_ms = Column(Float, nullable=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<PolicyEvaluationLog {self.action}: {self.result}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "agent_name": self.agent_name,
            "action": self.action,
            "context": self.context,
            "result": self.result,
            "rules_evaluated": self.rules_evaluated,
            "matching_rule_id": str(self.matching_rule_id) if self.matching_rule_id else None,
            "matching_rule_name": self.matching_rule_name,
            "rate_limit_checked": self.rate_limit_checked,
            "rate_limit_result": self.rate_limit_result,
            "escalation_triggered": self.escalation_triggered,
            "escalation_rule_id": str(self.escalation_rule_id) if self.escalation_rule_id else None,
            "evaluation_time_ms": self.evaluation_time_ms,
            "user_id": str(self.user_id) if self.user_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class EscalationLog(Base):
    """
    Log of triggered escalations.
    """
    __tablename__ = "escalation_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # TENANT-EXEMPT: EscalationLog cross-tenant compliance (auditor WeDOTalent)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    escalation_rule_id = Column(UUID(as_uuid=True), ForeignKey("escalation_rules.id", ondelete="SET NULL"), nullable=True)
    
    trigger_reason = Column(Text, nullable=False)
    trigger_context = Column(JSON, nullable=True)
    
    action_taken = Column(String(50), nullable=False)
    action_result = Column(JSON, nullable=True)
    
    escalated_to = Column(ARRAY(String), default=[])
    notification_sent = Column(Boolean, default=False)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<EscalationLog {self.action_taken} (resolved={self.resolved})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "escalation_rule_id": str(self.escalation_rule_id) if self.escalation_rule_id else None,
            "trigger_reason": self.trigger_reason,
            "trigger_context": self.trigger_context,
            "action_taken": self.action_taken,
            "action_result": self.action_result,
            "escalated_to": self.escalated_to,
            "notification_sent": self.notification_sent,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": str(self.resolved_by) if self.resolved_by else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


DEFAULT_BUSINESS_RULES = [
    {
        "name": "max_candidates_per_vacancy",
        "description": "Limite máximo de candidatos que podem ser adicionados a uma vaga",
        "rule_type": "deny",
        "conditions": {
            "action": "add_candidate_to_vacancy",
            "check": "candidate_count",
            "operator": "greater_than",
            "value": 500
        },
        "actions": ["add_candidate_to_vacancy", "bulk_add_candidates"],
        "priority": 10
    },
    {
        "name": "require_approval_bulk_rejection",
        "description": "Aprovação obrigatória para rejeição em massa de candidatos",
        "rule_type": "require_approval",
        "conditions": {
            "action": "bulk_reject_candidates",
            "check": "candidate_count",
            "operator": "greater_than",
            "value": 10
        },
        "actions": ["bulk_reject_candidates", "reject_all_pending"],
        "priority": 5,
        "approval_config": {
            "approvers": ["manager", "hr_admin"],
            "timeout_hours": 24
        }
    },
    {
        "name": "communication_hours",
        "description": "Horário permitido para envio de comunicações (8h às 20h)",
        "rule_type": "deny",
        "conditions": {
            "action": "send_communication",
            "check": "current_hour",
            "operator": "not_between",
            "value": [8, 20]
        },
        "actions": ["send_email", "send_whatsapp", "send_sms"],
        "priority": 20
    },
    {
        "name": "max_interviews_per_day",
        "description": "Número máximo de entrevistas agendadas por dia",
        "rule_type": "deny",
        "conditions": {
            "action": "schedule_interview",
            "check": "interviews_today",
            "operator": "greater_than",
            "value": 15
        },
        "actions": ["schedule_interview", "auto_schedule_interview"],
        "priority": 15
    },
    {
        "name": "require_approval_salary_disclosure",
        "description": "Aprovação necessária para divulgar faixa salarial fora do padrão",
        "rule_type": "require_approval",
        "conditions": {
            "action": "publish_vacancy",
            "check": "salary_variance_percent",
            "operator": "greater_than",
            "value": 30
        },
        "actions": ["publish_vacancy", "update_vacancy_salary"],
        "priority": 25
    },
    {
        "name": "deny_duplicate_screening",
        "description": "Impedir triagem duplicada de candidato na mesma vaga",
        "rule_type": "deny",
        "conditions": {
            "action": "start_screening",
            "check": "already_screened",
            "operator": "equals",
            "value": True
        },
        "actions": ["start_screening", "auto_screen"],
        "priority": 5
    }
]


DEFAULT_RATE_LIMIT_RULES = [
    {
        "name": "api_calls_per_minute",
        "description": "Limite de chamadas API por minuto por empresa",
        "target_type": "company",
        "limit_value": 100,
        "window_seconds": 60,
        "action_pattern": "api:*"
    },
    {
        "name": "messages_per_hour",
        "description": "Limite de mensagens enviadas por hora por usuário",
        "target_type": "user",
        "limit_value": 50,
        "window_seconds": 3600,
        "action_pattern": "send_message:*"
    },
    {
        "name": "evaluations_per_day",
        "description": "Limite de avaliações de candidatos por dia por empresa",
        "target_type": "company",
        "limit_value": 500,
        "window_seconds": 86400,
        "action_pattern": "evaluate_candidate:*"
    },
    {
        "name": "ai_calls_per_minute",
        "description": "Limite de chamadas AI por minuto por empresa",
        "target_type": "company",
        "limit_value": 30,
        "window_seconds": 60,
        "action_pattern": "ai:*"
    },
    {
        "name": "bulk_actions_per_hour",
        "description": "Limite de ações em massa por hora por usuário",
        "target_type": "user",
        "limit_value": 10,
        "window_seconds": 3600,
        "action_pattern": "bulk:*"
    }
]


DEFAULT_ESCALATION_RULES = [
    {
        "name": "interview_no_show_escalation",
        "description": "Escalar quando candidato não comparece à entrevista",
        "trigger_type": "timeout",
        "condition": {
            "event": "interview_start",
            "timeout_minutes": 15,
            "check": "candidate_joined",
            "expected": True
        },
        "escalate_to": ["recruiter", "hiring_manager"],
        "escalation_action": "notify_manager",
        "notification_template": "O candidato {candidate_name} não compareceu à entrevista agendada para {interview_time}.",
        "cooldown_seconds": 1800
    },
    {
        "name": "high_rejection_rate_alert",
        "description": "Alerta quando taxa de rejeição ultrapassa limite",
        "trigger_type": "threshold",
        "condition": {
            "metric": "rejection_rate",
            "operator": "greater_than",
            "value": 80,
            "window_hours": 24
        },
        "escalate_to": ["hr_admin"],
        "escalation_action": "send_alert",
        "notification_template": "A taxa de rejeição na vaga {vacancy_title} atingiu {rejection_rate}% nas últimas 24h.",
        "cooldown_seconds": 86400
    },
    {
        "name": "agent_failure_escalation",
        "description": "Escalar após múltiplas falhas de agente",
        "trigger_type": "failure_count",
        "condition": {
            "agent": "*",
            "failure_count": 5,
            "window_minutes": 30
        },
        "escalate_to": ["tech_admin"],
        "escalation_action": "pause_workflow",
        "notification_template": "O agente {agent_name} falhou {failure_count} vezes nos últimos 30 minutos. Workflow pausado.",
        "cooldown_seconds": 3600
    },
    {
        "name": "pending_approval_timeout",
        "description": "Escalar aprovações pendentes por muito tempo",
        "trigger_type": "timeout",
        "condition": {
            "event": "approval_requested",
            "timeout_hours": 48,
            "check": "approval_status",
            "expected": "pending"
        },
        "escalate_to": ["hr_director"],
        "escalation_action": "notify_admin",
        "notification_template": "Aprovação pendente há mais de 48h: {approval_type} para {target_name}.",
        "cooldown_seconds": 43200
    },
    {
        "name": "sla_breach_warning",
        "description": "Alerta quando SLA está próximo de ser violado",
        "trigger_type": "sla_breach",
        "condition": {
            "sla_type": "time_to_hire",
            "threshold_percent": 80
        },
        "escalate_to": ["recruiter", "hiring_manager"],
        "escalation_action": "send_alert",
        "notification_template": "A vaga {vacancy_title} está a {remaining_days} dias de violar o SLA de contratação.",
        "cooldown_seconds": 86400
    }
]


# ============================================================================
# W1-003 (2026-05-22) · Canonical policy budget/quota constants
# ============================================================================
#
# Source-of-truth para defaults setoriais e quotas — internalizadas de
# `app/orchestrator/policy_engine.py` (V1 deletado em W1-003) para permitir
# `PolicyEngineService.apply_industry_defaults` + `save_policy_block` ler
# direto sem instanciar V1.
#
# WT-2022 Phase 2 checklist completo (docstring V2 apply_industry_defaults).
# Pre-audit: sprint_logs/sprint_1.2/W1-003_AUDIT.md.
#
# Distinto de `ALPHA1_SECTOR_RULES` em `policy_engine_service.py:47-92`
# (esse é fairness/HITL/autonomy; este aqui é budget/quota).
# ============================================================================


# Whitelist de usage_type permitido em queries SQL (anti-injection).
# Origem histórica: V1 PolicyEngine.ALLOWED_USAGE_TYPES (W1-003 cleanup).
CANONICAL_ALLOWED_USAGE_TYPES: frozenset[str] = frozenset({
    "chat_requests",
    "action_executions",
    "llm_calls",
})


# Quotas default por usage_type (override per tenant via CompanyHiringPolicy).
# Origem: V1 PolicyEngine.DEFAULT_USAGE_LIMITS.
CANONICAL_DEFAULT_USAGE_LIMITS: dict[str, int] = {
    "chat_requests": 1000,
    "action_executions": 500,
    "llm_calls": 5000,
}


# Defaults canonical de política (fallback quando setor não reconhecido).
# Origem: V1 PolicyEngine.DEFAULT_POLICIES.
CANONICAL_DEFAULT_POLICIES: dict[str, int | bool] = {
    "max_pearch_searches_per_day": 10,
    "max_voice_screenings_per_day": 20,
    "max_tokens_per_request": 50000,
    "max_concurrent_requests": 5,
    "allow_global_search": True,
    "require_approval_for_bulk_email": True,
}


# Defaults por setor — Alpha 1 WeDOTalent (tech, varejo, logistica,
# financeiro, saude, rpo). Setor desconhecido → CANONICAL_DEFAULT_POLICIES.
# Origem: V1 PolicyEngine.SECTOR_DEFAULTS.
# Invariantes-chave (preservadas em W1-003):
#   - tech.allow_global_search = True
#   - financeiro.allow_global_search = False (regulatório BCB 498)
#   - saude.allow_global_search = False
#   - rpo: maiores limites (RPO = high-volume sourcing)
CANONICAL_SECTOR_DEFAULTS: dict[str, dict[str, int | bool]] = {
    "tech": {
        "max_pearch_searches_per_day": 50,
        "max_voice_screenings_per_day": 100,
        "max_tokens_per_request": 100000,
        "max_concurrent_requests": 10,
        "allow_global_search": True,
        "require_approval_for_bulk_email": False,  # tech: menor burocracia
    },
    "varejo": {
        "max_pearch_searches_per_day": 200,
        "max_voice_screenings_per_day": 500,
        "max_tokens_per_request": 50000,
        "max_concurrent_requests": 20,
        "allow_global_search": True,
        "require_approval_for_bulk_email": True,
    },
    "logistica": {
        "max_pearch_searches_per_day": 300,
        "max_voice_screenings_per_day": 1000,
        "max_tokens_per_request": 50000,
        "max_concurrent_requests": 30,
        "allow_global_search": True,
        "require_approval_for_bulk_email": True,
    },
    "financeiro": {
        "max_pearch_searches_per_day": 20,
        "max_voice_screenings_per_day": 50,
        "max_tokens_per_request": 50000,
        "max_concurrent_requests": 5,
        "allow_global_search": False,  # regulatório BCB 498
        "require_approval_for_bulk_email": True,
    },
    "saude": {
        "max_pearch_searches_per_day": 30,
        "max_voice_screenings_per_day": 80,
        "max_tokens_per_request": 50000,
        "max_concurrent_requests": 8,
        "allow_global_search": False,
        "require_approval_for_bulk_email": True,
    },
    "rpo": {
        "max_pearch_searches_per_day": 500,
        "max_voice_screenings_per_day": 2000,
        "max_tokens_per_request": 100000,
        "max_concurrent_requests": 50,
        "allow_global_search": True,
        "require_approval_for_bulk_email": False,
    },
}
