"""
Feedback Learning models for capturing recruiter corrections and job outcomes.

These models enable LIA to learn from:
- Recruiter corrections during the wizard flow
- Final job outcomes (filled, cancelled, expired)
- Success patterns from completed hires
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class JobOutcomeType(str, enum.Enum):
    """Possible outcomes for a job vacancy."""
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REPOSTED = "reposted"


class SuggestionFeedback(Base):
    """
    Captures feedback on suggestions made by LIA during the wizard flow.
    
    When LIA makes a suggestion (e.g., salary range, skills) and the user
    accepts or rejects it, this record stores the feedback for learning.
    
    Unlike WizardFeedback which is tied to a specific job_id,
    this model captures more general suggestion feedback that may occur
    before a job is finalized.
    
    Example:
        - LIA suggests salary {"min": 5000, "max": 6000}
        - User rejects and sets it to {"min": 6000, "max": 7500}
        - This feedback is stored for future suggestions
    """
    __tablename__ = "suggestion_feedback"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    
    field_name = Column(String(100), nullable=False, index=True)
    
    suggested_value = Column(JSON, nullable=True)
    actual_value = Column(JSON, nullable=True)
    
    accepted = Column(Integer, nullable=False, default=0)  # 1 = accepted, 0 = rejected
    
    context = Column(JSON, nullable=True)  # Additional context like role, seniority, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)


class WizardFeedback(Base):
    """
    Captures corrections made by recruiters during the job creation wizard.
    
    When LIA suggests a value (e.g., salary range) and the recruiter corrects it,
    this record stores the original and corrected values for learning.
    
    Example:
        - LIA suggests salary R$15,000 for "Dev Sênior"
        - Recruiter corrects to R$18,000
        - This feedback is stored for future suggestions
    """
    __tablename__ = "wizard_feedback"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    field_corrected = Column(String(100), nullable=False, index=True)
    
    original_value = Column(JSON, nullable=True)
    corrected_value = Column(JSON, nullable=True)
    
    stage = Column(String(100), nullable=True)
    
    role = Column(String(255), nullable=True, index=True)
    seniority = Column(String(50), nullable=True, index=True)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    
    correction_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)


class JobOutcome(Base):
    """
    Captures final outcomes of job vacancies.
    
    Tracks:
    - Whether the position was filled, cancelled, or expired
    - Time to fill metrics
    - Final salary offered
    - Candidate funnel metrics
    - Satisfaction scores
    
    This data is used to identify success patterns and improve future suggestions.
    """
    __tablename__ = "job_outcomes"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    
    outcome = Column(
        SQLEnum(JobOutcomeType, name="job_outcome_type"),
        nullable=False,
        index=True
    )
    
    time_to_fill_days = Column(Integer, nullable=True)
    
    salary_initial_min = Column(Float, nullable=True)
    salary_initial_max = Column(Float, nullable=True)
    salary_final = Column(Float, nullable=True)
    
    candidate_count_total = Column(Integer, nullable=True)
    candidate_count_screened = Column(Integer, nullable=True)
    candidate_count_interviewed = Column(Integer, nullable=True)
    candidate_count_offered = Column(Integer, nullable=True)
    
    satisfaction_score = Column(Float, nullable=True)
    
    role = Column(String(255), nullable=True, index=True)
    seniority = Column(String(50), nullable=True, index=True)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    work_model = Column(String(50), nullable=True)
    
    skills_used = Column(JSON, default=list)
    
    notes = Column(Text, nullable=True)
    
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)
