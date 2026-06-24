"""
Calibration Model - Database models for the calibration loop system.

The calibration loop captures recruiter feedback (implicit and explicit)
to improve LIA's scoring accuracy over time.
"""
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum, JSON, Boolean, Integer, Float
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from lia_config.database import Base


class CalibrationFeedback(Base):
    """Feedback de calibração do recrutador para candidatos."""
    __tablename__ = "calibration_feedback"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vacancy_id = Column(String, nullable=True)
    search_session_id = Column(String, nullable=True)
    candidate_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False, default="default_user")
    feedback = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    candidate_snapshot = Column(JSON, nullable=True)
    company_id = Column(String, nullable=False)  # Bug 13: LGPD Art.18 tenant erasure anchor
    created_at = Column(DateTime, server_default=func.now())
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vacancy_id": self.vacancy_id,
            "search_session_id": self.search_session_id,
            "candidate_id": self.candidate_id,
            "user_id": self.user_id,
            "feedback": self.feedback,
            "reason": self.reason,
            "candidate_snapshot": self.candidate_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CalibrationSessionStatus(str, enum.Enum):
    """Status granular da sessão de calibração."""
    AWAITING_FEEDBACK = "awaiting_feedback"
    LEARNING = "learning"
    CONFIRMED = "confirmed"
    SOURCING_IN_PROGRESS = "sourcing_in_progress"
    COMPLETED = "completed"


class CalibrationSession(Base):
    """Sessão de calibração para uma vaga ou busca."""
    __tablename__ = "calibration_sessions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    vacancy_id = Column(String, nullable=True)
    user_id = Column(String, nullable=False, default="default_user")
    search_criteria = Column(JSON, nullable=True)
    status = Column(String, default="awaiting_feedback")
    total_shown = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    dislikes_count = Column(Integer, default=0)
    learned_criteria = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    min_feedbacks_required = Column(Integer, default=5)
    sourcing_blocked = Column(Boolean, default=True)
    confirmation_message = Column(Text, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "vacancy_id": self.vacancy_id,
            "user_id": self.user_id,
            "search_criteria": self.search_criteria,
            "status": self.status,
            "total_shown": self.total_shown,
            "likes_count": self.likes_count,
            "dislikes_count": self.dislikes_count,
            "learned_criteria": self.learned_criteria,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "min_feedbacks_required": self.min_feedbacks_required,
            "sourcing_blocked": self.sourcing_blocked,
            "confirmation_message": self.confirmation_message,
            "feedbacks_remaining": max(0, self.min_feedbacks_required - self.total_shown),
            "calibration_complete": self.status in ["confirmed", "sourcing_in_progress", "completed"],
        }


class FeedbackType(str, enum.Enum):
    """Types of calibration feedback."""
    EXPLICIT_AGREE = "explicit_agree"
    EXPLICIT_DISAGREE = "explicit_disagree"
    IMPLICIT_ADVANCE = "implicit_advance"
    IMPLICIT_REJECT = "implicit_reject"
    IMPLICIT_OVERRIDE = "implicit_override"
    POST_HIRE_SUCCESS = "post_hire_success"
    POST_HIRE_FAILURE = "post_hire_failure"


class CalibrationStatus(str, enum.Enum):
    """Status of calibration events."""
    PENDING = "pending"
    PROCESSED = "processed"
    APPLIED = "applied"
    IGNORED = "ignored"


class CalibrationEvent(Base):
    """
    Calibration event model for tracking recruiter feedback on LIA's evaluations.
    """
    __tablename__ = "calibration_events"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - calibration_events aggregated cross-tenant for global ML model improvement (ADR-LGPD-001 anonymization, N>=10 gate em CalibrationRepository)
    company_id = Column(String, nullable=True, index=True)  # multi-tenant isolation

    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    status = Column(SQLEnum(CalibrationStatus), default=CalibrationStatus.PENDING)

    candidate_id = Column(String, nullable=False)
    job_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    
    lia_score = Column(Float, nullable=True)
    lia_ranking = Column(Integer, nullable=True)
    lia_recommendation = Column(String(100), nullable=True)
    
    recruiter_action = Column(String(100), nullable=True)
    recruiter_stage_from = Column(String(100), nullable=True)
    recruiter_stage_to = Column(String(100), nullable=True)
    
    feedback_reason = Column(Text, nullable=True)
    
    score_delta = Column(Float, nullable=True)
    
    context = Column(JSON, default=dict)
    
    processed_at = Column(DateTime, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "feedback_type": self.feedback_type.value if self.feedback_type else None,
            "status": self.status.value if self.status else None,
            "candidate_id": self.candidate_id,
            "job_id": self.job_id,
            "user_id": self.user_id,
            "lia_score": self.lia_score,
            "lia_ranking": self.lia_ranking,
            "lia_recommendation": self.lia_recommendation,
            "recruiter_action": self.recruiter_action,
            "recruiter_stage_from": self.recruiter_stage_from,
            "recruiter_stage_to": self.recruiter_stage_to,
            "feedback_reason": self.feedback_reason,
            "score_delta": self.score_delta,
            "context": self.context,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<CalibrationEvent {self.id}: {self.feedback_type.value} ({self.status.value})>"


class CalibrationWeight(Base):
    """
    Calibration weight model for storing learned scoring weights.
    """
    __tablename__ = "calibration_weights"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - calibration_weights aggregated cross-tenant for global ML weights blending (ADR-LGPD-001 anonymization, sample_count>=10 enforced em CalibrationRepository read path)
    company_id = Column(String, nullable=True, index=True)  # multi-tenant isolation

    job_id = Column(String, nullable=True)
    job_category = Column(String(100), nullable=True)
    
    dimension = Column(String(100), nullable=False)
    
    base_weight = Column(Float, default=1.0)
    adjusted_weight = Column(Float, default=1.0)
    confidence = Column(Float, default=0.5)
    
    sample_size = Column(Integer, default=0)
    
    last_adjustment_reason = Column(Text, nullable=True)
    adjustment_history = Column(JSON, default=list)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert weight to dictionary."""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "job_id": self.job_id,
            "job_category": self.job_category,
            "dimension": self.dimension,
            "base_weight": self.base_weight,
            "adjusted_weight": self.adjusted_weight,
            "confidence": self.confidence,
            "sample_size": self.sample_size,
            "last_adjustment_reason": self.last_adjustment_reason,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CalibrationSuggestion(Base):
    """
    Model for storing calibration suggestions that need recruiter approval.
    """
    __tablename__ = "calibration_suggestions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    suggestion_type = Column(String(50), nullable=False)
    
    dimension = Column(String(100), nullable=True)
    current_weight = Column(Float, nullable=True)
    suggested_weight = Column(Float, nullable=True)
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    
    supporting_evidence = Column(JSON, default=list)
    
    impact_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    
    status = Column(String(50), default="pending")
    
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by = Column(String, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert suggestion to dictionary."""
        return {
            "id": self.id,
            "suggestion_type": self.suggestion_type,
            "dimension": self.dimension,
            "current_weight": self.current_weight,
            "suggested_weight": self.suggested_weight,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "supporting_evidence": self.supporting_evidence,
            "impact_score": self.impact_score,
            "confidence": self.confidence,
            "status": self.status,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
