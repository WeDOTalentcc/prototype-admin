"""
Communication Automation Model - Database-backed automation rules.

This model stores automation configurations that trigger actions based on events
like candidate stage changes, interview scheduling, screening completion, etc.
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Index, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


# TriggerType imported from canonical source (Sprint Z.db 2026-05-27).
# DO NOT redefine here -- single source of truth is trigger_types_canonical.py.
from app.shared.automation.trigger_types_canonical import TriggerType  # noqa: F401


class ActionType(str, enum.Enum):
    """Types of automation actions."""
    SEND_EMAIL = "send_email"
    SEND_WHATSAPP = "send_whatsapp"
    CREATE_TASK = "create_task"
    NOTIFY_RECRUITER = "notify_recruiter"
    NOTIFY_MANAGER = "notify_manager"
    UPDATE_CANDIDATE_STATUS = "update_candidate_status"
    LOG_ACTIVITY = "log_activity"


class CommunicationAutomation(Base):
    """
    Communication Automation - Database-backed automation rules.
    
    Stores automation configurations that can be:
    - Created, updated, deleted by users
    - Enabled/disabled per company
    - Configured with custom trigger conditions and action parameters
    """
    __tablename__ = "communication_automations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    trigger_type = Column(String(50), nullable=False, index=True)
    trigger_config = Column(JSON, default=dict)
    
    action_type = Column(String(50), nullable=False)
    action_config = Column(JSON, default=dict)
    
    conditions = Column(JSON, default=list)
    
    is_active = Column(Boolean, default=True, index=True)
    
    priority = Column(String(20), default="normal")
    
    cooldown_minutes = Column(Integer, nullable=False, default=0)

    execution_count = Column(Integer, nullable=False, default=0)
    last_executed_at = Column(DateTime, nullable=True)
    
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_automation_company_active', 'company_id', 'is_active'),
        Index('idx_automation_trigger_type', 'company_id', 'trigger_type'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<CommunicationAutomation {self.id} - {self.name} - {self.trigger_type}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "trigger_config": self.trigger_config or {},
            "action_type": self.action_type,
            "action_config": self.action_config or {},
            "conditions": self.conditions or [],
            "is_active": self.is_active,
            "priority": self.priority,
            "cooldown_minutes": self.cooldown_minutes if self.cooldown_minutes is not None else 0,
            "execution_count": self.execution_count if self.execution_count is not None else 0,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AutomationExecutionLog(Base):
    """
    Log of automation executions for audit and debugging.
    """
    __tablename__ = "automation_execution_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    automation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(String(255), nullable=False, index=True)
    
    trigger_event = Column(String(100), nullable=False)
    trigger_data = Column(JSON, default=dict)
    
    candidate_id = Column(String(255), nullable=True, index=True)
    vacancy_id = Column(String(255), nullable=True, index=True)
    
    action_executed = Column(String(50), nullable=False)
    action_result = Column(JSON, default=dict)
    
    status = Column(String(20), nullable=False, default="success")
    error_message = Column(Text, nullable=True)
    
    execution_time_ms = Column(Integer, nullable=True)

    # Sprint A (2026-06-13): rastreabilidade cross-domain
    correlation_id = Column(String(80), nullable=True, index=True)
    
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_exec_log_automation', 'automation_id', 'executed_at'),
        Index('idx_exec_log_company', 'company_id', 'executed_at'),
    {"extend_existing": True}, )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "automation_id": str(self.automation_id),
            "company_id": self.company_id,
            "trigger_event": self.trigger_event,
            "trigger_data": self.trigger_data,
            "candidate_id": self.candidate_id,
            "vacancy_id": self.vacancy_id,
            "action_executed": self.action_executed,
            "action_result": self.action_result,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms if self.execution_time_ms is not None else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
        }


class SuggestionStatus(str, enum.Enum):
    """Status of AI suggestions."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AISuggestion(Base):
    """
    AI Suggestions for automation actions.
    
    Stores AI-generated suggestions for candidate stage transitions,
    communications, and other recruitment actions that require user approval.
    """
    __tablename__ = "ai_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    candidate_id = Column(String(255), nullable=True, index=True)
    vacancy_id = Column(String(255), nullable=True, index=True)
    
    suggestion_type = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    action_config = Column(JSON, default=dict)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    confidence_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)
    
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    reviewed_by = Column(String(255), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    
    extra_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_suggestion_company_status', 'company_id', 'status'),
        Index('idx_suggestion_candidate', 'candidate_id', 'status'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<AISuggestion {self.id} - {self.suggestion_type} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "candidate_id": self.candidate_id,
            "vacancy_id": self.vacancy_id,
            "suggestion_type": self.suggestion_type,
            "action_type": self.action_type,
            "action_config": self.action_config or {},
            "title": self.title,
            "description": self.description,
            "confidence_score": self.confidence_score if self.confidence_score is not None else None,
            "reasoning": self.reasoning,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "rejection_reason": self.rejection_reason,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "extra_data": self.extra_data or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StageAutomationRule(Base):
    """
    Company-specific stage automation rules.
    Defines how triggers behave for each company - which are enabled,
    auto-execute vs suggestion mode, conditions, etc.
    """
    __tablename__ = "stage_automation_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    trigger_type = Column(String(100), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    auto_execute = Column(Boolean, default=False)
    confidence_threshold = Column(Float, nullable=False, default=0.8)
    
    conditions = Column(JSON, default=dict)
    actions = Column(JSON, default=list)
    
    source_stage = Column(String(100), nullable=True)
    target_stage = Column(String(100), nullable=True)
    
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    
    priority = Column(String(20), default="normal")
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_stage_rule_company_active', 'company_id', 'is_active'),
        Index('idx_stage_rule_trigger', 'company_id', 'trigger_type'),
    {"extend_existing": True}, )
    
    def __repr__(self):
        return f"<StageAutomationRule {self.id} - {self.name} - {self.trigger_type}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "company_id": self.company_id,
            "trigger_type": self.trigger_type,
            "is_active": self.is_active,
            "auto_execute": self.auto_execute,
            "confidence_threshold": self.confidence_threshold if self.confidence_threshold is not None else 0.8,
            "conditions": self.conditions or {},
            "actions": self.actions or [],
            "source_stage": self.source_stage,
            "target_stage": self.target_stage,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


DEFAULT_STAGE_AUTOMATION_RULES = [
    {
        "trigger_type": "screening_completed",
        "name": "Após triagem concluída",
        "auto_execute": False,
        "actions": [{"type": "calculate_wsi"}, {"type": "notify_recruiter"}],
        "priority": "high",
    },
    {
        "trigger_type": "interview_completed",
        "name": "Após entrevista concluída",
        "auto_execute": False,
        "actions": [{"type": "generate_parecer"}, {"type": "suggest_next_stage"}],
        "priority": "high",
    },
    {
        "trigger_type": "candidate_inactive",
        "name": "Candidato inativo 7+ dias",
        "auto_execute": True,
        "conditions": {"inactive_days": 7},
        "actions": [{"type": "send_followup"}, {"type": "notify_recruiter"}],
        "priority": "normal",
    },
    {
        "trigger_type": "offer_accepted",
        "name": "Oferta aceita",
        "auto_execute": True,
        "actions": [{"type": "move_to_hired"}, {"type": "sync_ats"}, {"type": "notify_team"}],
        "priority": "high",
    },
    {
        "trigger_type": "candidate_applied",
        "name": "Nova candidatura recebida",
        "auto_execute": False,
        "actions": [{"type": "initial_screening"}, {"type": "send_confirmation_email"}],
        "priority": "normal",
    },
    {
        "trigger_type": "wsi_score_calculated",
        "name": "Score WSI calculado",
        "auto_execute": False,
        "conditions": {"min_wsi_score": 70},
        "actions": [{"type": "suggest_interview"}, {"type": "notify_recruiter"}],
        "priority": "normal",
    },
]
