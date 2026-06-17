"""
Job Draft models for the enhanced job creation wizard.

Provides a staging area for job vacancies being created through
LIA's conversational interface, with full tracking of field origins,
confidence levels, and change history.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid

from lia_config.database import Base


class JobDraftStatus(str, Enum):
    """Status progression for job drafts through the wizard flow."""
    DRAFT = "draft"
    STRUCTURED = "structured"
    REVIEWED = "reviewed"
    CONFIRMED = "confirmed"
    PUBLISHED = "published"
    CANCELLED = "cancelled"


class ChangeType(str, Enum):
    """Type of change made to a draft field."""
    INFERRED = "inferred"
    CONFIRMED = "confirmed"
    EDITED = "edited"
    REVERTED = "reverted"


class JobDraft(Base):
    """
    Staging model for job vacancies during wizard flow.
    
    Tracks the full lifecycle from initial input through publication,
    including all inferences, confirmations, and edits.
    """
    __tablename__ = "job_drafts"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    recruiter_id = Column(String(255), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    status = Column(
        SQLEnum(JobDraftStatus, name="job_draft_status", create_type=True),
        nullable=False,
        default=JobDraftStatus.DRAFT,
        index=True
    )
    current_step = Column(String(100), nullable=True, default="input")
    
    raw_input = Column(Text, nullable=True)
    imported_jd = Column(Text, nullable=True)
    detected_language = Column(String(10), nullable=True, default="pt-BR")
    
    job_title = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    seniority = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), nullable=True)
    hybrid_days = Column(Integer, nullable=True)
    employment_type = Column(String(50), nullable=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True, default="BRL")
    country = Column(String(100), nullable=True, default="Brasil")
    pj_rate = Column(Float, nullable=True)
    
    is_affirmative = Column(Boolean, nullable=True, default=False)
    affirmative_criteria_primary = Column(String(100), nullable=True)
    affirmative_criteria_secondary = Column(String(100), nullable=True)
    manager = Column(String(255), nullable=True)
    manager_email = Column(String(255), nullable=True)
    
    skills = Column(ARRAY(String), default=list)
    benefits = Column(ARRAY(String), default=list)
    languages = Column(ARRAY(String), default=list)
    
    behavioral_competencies = Column(JSON, default=list)
    screening_questions = Column(JSON, default=list)
    pipeline_stages = Column(JSON, default=list)
    
    generated_jd = Column(Text, nullable=True)
    
    inferred_fields = Column(JSON, default=dict)
    confirmed_fields = Column(JSON, default=dict)
    company_defaults_used = Column(JSON, default=dict)
    confidence_map = Column(JSON, default=dict)
    
    insights = Column(JSON, default=list)
    warnings = Column(JSON, default=list)
    
    estimated_ttf = Column(Integer, nullable=True)
    job_complexity = Column(String(50), nullable=True)
    
    published_job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_vacancies.id", ondelete="SET NULL"),
        nullable=True
    )
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    structured_at = Column(DateTime, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    published_at = Column(DateTime, nullable=True)
    
    field_history = relationship(
        "DraftFieldHistory",
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="DraftFieldHistory.created_at.desc()"
    )
    
    def mark_structured(self) -> None:
        """Mark draft as structured after initial extraction."""
        self.status = JobDraftStatus.STRUCTURED
        self.structured_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_reviewed(self) -> None:
        """Mark draft as reviewed after user review."""
        self.status = JobDraftStatus.REVIEWED
        self.reviewed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_confirmed(self) -> None:
        """Mark draft as confirmed and ready for publication."""
        self.status = JobDraftStatus.CONFIRMED
        self.updated_at = datetime.utcnow()
    
    def mark_published(self, job_id: uuid.UUID) -> None:
        """Mark draft as published with reference to created job."""
        self.status = JobDraftStatus.PUBLISHED
        self.published_job_id = job_id
        self.published_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_cancelled(self) -> None:
        """Mark draft as cancelled."""
        self.status = JobDraftStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def set_field_confidence(self, field: str, confidence: float, source: str) -> None:
        """Record confidence level for a field."""
        current_map = dict(self.confidence_map) if self.confidence_map else {}
        current_map[field] = {
            "confidence": confidence,
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.confidence_map = current_map
    
    def mark_field_inferred(self, field: str, source: str) -> None:
        """Mark a field as inferred from a source."""
        current_inferred = dict(self.inferred_fields) if self.inferred_fields else {}
        current_inferred[field] = {
            "source": source,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.inferred_fields = current_inferred
    
    def mark_field_confirmed(self, field: str) -> None:
        """Mark a field as confirmed by user."""
        current_confirmed = dict(self.confirmed_fields) if self.confirmed_fields else {}
        current_confirmed[field] = {
            "confirmed_at": datetime.utcnow().isoformat()
        }
        self.confirmed_fields = current_confirmed
        
        if self.inferred_fields:
            current_inferred = dict(self.inferred_fields)
            if field in current_inferred:
                del current_inferred[field]
                self.inferred_fields = current_inferred
    
    def add_warning(self, warning_type: str, message: str, field: Optional[str] = None) -> None:
        """Add a warning to the draft."""
        current_warnings = list(self.warnings) if self.warnings else []
        current_warnings.append({
            "type": warning_type,
            "message": message,
            "field": field,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.warnings = current_warnings
    
    def add_insight(self, insight_type: str, message: str, data: Optional[dict] = None) -> None:
        """Add an insight to the draft."""
        current_insights = list(self.insights) if self.insights else []
        current_insights.append({
            "type": insight_type,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        self.insights = current_insights


class DraftFieldHistory(Base):
    """
    Tracks all changes made to draft fields during wizard flow.
    
    Provides full audit trail for debugging, learning, and undo functionality.
    """
    __tablename__ = "draft_field_history"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_drafts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    field_name = Column(String(100), nullable=False, index=True)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    
    change_type = Column(
        SQLEnum(ChangeType, name="draft_change_type", create_type=True),
        nullable=False,
        index=True
    )
    
    confidence_at_change = Column(Float, nullable=True)
    source = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    draft = relationship("JobDraft", back_populates="field_history")
    
    @classmethod
    def create_inferred(
        cls,
        draft_id: uuid.UUID,
        field_name: str,
        new_value,
        confidence: float,
        source: str
    ) -> "DraftFieldHistory":
        """Create a history entry for an inferred value."""
        return cls(
            draft_id=draft_id,
            field_name=field_name,
            old_value=None,
            new_value=new_value,
            change_type=ChangeType.INFERRED,
            confidence_at_change=confidence,
            source=source
        )
    
    @classmethod
    def create_confirmed(
        cls,
        draft_id: uuid.UUID,
        field_name: str,
        value,
        created_by: str
    ) -> "DraftFieldHistory":
        """Create a history entry for a confirmed value."""
        return cls(
            draft_id=draft_id,
            field_name=field_name,
            old_value=value,
            new_value=value,
            change_type=ChangeType.CONFIRMED,
            created_by=created_by
        )
    
    @classmethod
    def create_edited(
        cls,
        draft_id: uuid.UUID,
        field_name: str,
        old_value,
        new_value,
        created_by: str,
        reason: Optional[str] = None
    ) -> "DraftFieldHistory":
        """Create a history entry for an edited value."""
        return cls(
            draft_id=draft_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_type=ChangeType.EDITED,
            created_by=created_by,
            reason=reason
        )
    
    @classmethod
    def create_reverted(
        cls,
        draft_id: uuid.UUID,
        field_name: str,
        old_value,
        new_value,
        created_by: str
    ) -> "DraftFieldHistory":
        """Create a history entry for a reverted value."""
        return cls(
            draft_id=draft_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_type=ChangeType.REVERTED,
            created_by=created_by
        )
