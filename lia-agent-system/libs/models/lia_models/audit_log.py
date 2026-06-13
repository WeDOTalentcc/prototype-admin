"""
Audit Log model for AI Governance and Explainability.

This module provides comprehensive audit logging for all AI decisions made
by LIA agents, ensuring transparency, accountability, and LGPD compliance.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, JSON, Boolean, Text
from sqlalchemy.sql import func
from lia_config.database import Base
import enum
import uuid


class DecisionType(str, enum.Enum):  # R-053: canonical DecisionType — single active definition; observability.py has a dead duplicate
    """Types of AI decisions that can be audited."""
    SCORE_CANDIDATE = "score_candidate"
    APPROVE_CANDIDATE = "approve_candidate"
    REJECT_CANDIDATE = "reject_candidate"
    MOVE_STAGE = "move_stage"
    SEND_MESSAGE = "send_message"
    SCHEDULE_INTERVIEW = "schedule_interview"
    GENERATE_FEEDBACK = "generate_feedback"
    # PR4 (Task #1004) — categoria canônica para mutações em
    # company_settings (save_company_field/section, save_hiring_policy,
    # import_workforce_plan, import_benefits_from_data,
    # check_company_completeness). Necessária pra que AuditService não
    # caia no fallback SCORE_CANDIDATE e o decision_type persistido em
    # `audit_logs` reflita a operação real (queries forenses).
    COMPANY_SETTINGS_CHANGE = "company_settings_change"
    # Task #1018 — categoria canônica para eventos de autenticação
    # (login bem-sucedido/falho, logout, refresh). Antes, login sucesso
    # era logado como MOVE_STAGE e falha como REJECT_CANDIDATE, poluindo
    # dashboards de compliance SOX e o triage de incidentes de auth.
    AUTH_EVENT = "auth_event"


class AuditLog(Base):
    """
    Audit log for AI decisions with full explainability.
    
    This model tracks every decision made by LIA agents, including:
    - What decision was made
    - Why it was made (reasoning)
    - What criteria were used
    - What criteria were explicitly ignored (anti-bias)
    - Whether human review was required/performed
    
    Critical for AI governance, LGPD compliance, and candidate transparency.
    """
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String(255), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(255), nullable=False, index=True)
    
    agent_name = Column(String(255), nullable=False, index=True)
    decision_type = Column(String(100), nullable=False, index=True)
    action = Column(String(255), nullable=False)
    
    candidate_id = Column(String(255), nullable=True, index=True)
    job_vacancy_id = Column(String(255), nullable=True, index=True)
    
    decision = Column(String(100), nullable=False)
    score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    reasoning = Column(JSON, nullable=False, default=list)
    criteria_used = Column(JSON, nullable=False, default=list)
    criteria_ignored = Column(JSON, nullable=False, default=list)
    
    human_review_required = Column(Boolean, default=False)
    human_reviewed_by = Column(String(255), nullable=True)
    human_reviewed_at = Column(DateTime, nullable=True)
    human_override = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    retention_until = Column(DateTime, nullable=True)

    # Etapa 2 — Output Auditing (migration 052)
    session_id = Column(String(255), nullable=True, index=True)
    agent_used = Column(String(255), nullable=True)
    input_text = Column(Text, nullable=True)
    output_text = Column(Text, nullable=True)
    fairness_flags = Column(JSON, nullable=True, default=list)

    # Sprint A (2026-06-13): rastreabilidade cross-domain
    # Liga a decisao ao request HTTP que a originou.
    # Substitui o workaround session_id=trace_id (Task #366).
    correlation_id = Column(String(80), nullable=True, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.id} - {self.agent_name}: {self.decision_type} -> {self.decision}>"
    
    def to_dict(self):
        """Convert audit log to dictionary for API responses."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "agent_name": self.agent_name,
            "decision_type": self.decision_type,
            "action": self.action,
            "candidate_id": self.candidate_id,
            "job_vacancy_id": self.job_vacancy_id,
            "decision": self.decision,
            "score": self.score,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "criteria_used": self.criteria_used,
            "criteria_ignored": self.criteria_ignored,
            "human_review_required": self.human_review_required,
            "human_reviewed_by": self.human_reviewed_by,
            "human_reviewed_at": self.human_reviewed_at.isoformat() if self.human_reviewed_at else None,
            "human_override": self.human_override,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "retention_until": self.retention_until.isoformat() if self.retention_until else None,
        }
