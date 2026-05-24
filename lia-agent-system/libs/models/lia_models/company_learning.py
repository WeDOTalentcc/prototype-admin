"""
Company Learning models for dynamic catalogs and unified learning.

These models enable company-specific learning:
- Dynamic skill catalogs that grow with confirmed suggestions
- Dynamic responsibility catalogs
- Unified feedback tracking across wizard and agents
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Boolean, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from lia_config.database import Base


class LearningSource(str, enum.Enum):
    """Source of learned data."""
    WIZARD_CONFIRMED = "wizard_confirmed"
    RECRUITER_ADDED = "recruiter_added"
    AGENT_SUGGESTED = "agent_suggested"
    OUTCOME_SUCCESS = "outcome_success"
    IMPORTED = "imported"


class CompanySkill(Base):
    """
    Dynamic skill catalog per company.
    
    Skills are added when:
    - Recruiter confirms a suggested skill in wizard
    - Recruiter manually adds a skill not in global catalog
    - A skill appears in successful hires
    
    After N confirmations (threshold), skill becomes "promoted" 
    and is suggested by default for that company.
    """
    __tablename__ = "company_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    skill_name = Column(String(255), nullable=False, index=True)
    skill_type = Column(String(50), nullable=False, default="technical")
    category = Column(String(100), nullable=True)
    
    times_confirmed = Column(Integer, default=1)
    times_rejected = Column(Integer, default=0)
    times_used_in_jobs = Column(Integer, default=0)
    times_in_successful_hires = Column(Integer, default=0)
    
    source = Column(String(50), default=LearningSource.WIZARD_CONFIRMED.value)
    
    is_promoted = Column(Boolean, default=False)
    promotion_threshold = Column(Integer, default=3)
    
    roles_associated = Column(JSON, default=list)
    seniority_levels = Column(JSON, default=list)
    
    confidence_score = Column(Float, default=0.5)
    
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'skill_name', name='uq_company_skill'),
        Index('ix_company_skills_company_type', 'company_id', 'skill_type'),
        Index('ix_company_skills_promoted', 'company_id', 'is_promoted'),
    {"extend_existing": True}, )


class CompanyResponsibility(Base):
    """
    Dynamic responsibility catalog per company.
    
    Similar to CompanySkill but for job responsibilities.
    """
    __tablename__ = "company_responsibilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    
    times_confirmed = Column(Integer, default=1)
    times_rejected = Column(Integer, default=0)
    times_used_in_jobs = Column(Integer, default=0)
    times_in_successful_hires = Column(Integer, default=0)
    
    source = Column(String(50), default=LearningSource.WIZARD_CONFIRMED.value)
    
    is_promoted = Column(Boolean, default=False)
    promotion_threshold = Column(Integer, default=3)
    
    roles_associated = Column(JSON, default=list)
    seniority_levels = Column(JSON, default=list)
    
    confidence_score = Column(Float, default=0.5)
    
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    description_hash = Column(String(64), nullable=False, index=True)
    
    __table_args__ = (
        UniqueConstraint('company_id', 'description_hash', name='uq_company_responsibility'),
        Index('ix_company_resp_company_category', 'company_id', 'category'),
        Index('ix_company_resp_promoted', 'company_id', 'is_promoted'),
    {"extend_existing": True}, )


class AgentFeedback(Base):
    """
    Captures feedback on agent actions/suggestions.
    
    When an agent (Sourcing, WSI Evaluator, etc.) makes a suggestion
    and the recruiter accepts or rejects it, this record stores the feedback.
    
    This complements WizardFeedback and SuggestionFeedback to create
    a unified learning loop across all system components.
    """
    __tablename__ = "agent_feedback"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True)
    
    agent_name = Column(String(100), nullable=False, index=True)
    action_type = Column(String(100), nullable=False)
    
    suggested_value = Column(JSON, nullable=True)
    actual_value = Column(JSON, nullable=True)
    
    accepted = Column(Boolean, nullable=False, default=False)
    
    context = Column(JSON, nullable=True)
    feedback_reason = Column(Text, nullable=True)
    
    processing_time_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_by = Column(String(255), nullable=True)


class CompanyPattern(Base):
    """
    Stores detected patterns specific to a company.
    
    Examples:
    - "77% of jobs are hybrid"
    - "Average salary for Senior Dev is R$18k"
    - "Tech roles filled 2x faster than Sales"
    """
    __tablename__ = "company_patterns"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(String(255), nullable=False, index=True)
    
    pattern_type = Column(String(100), nullable=False, index=True)
    pattern_key = Column(String(255), nullable=False)
    
    pattern_value = Column(JSON, nullable=False)
    
    sample_size = Column(Integer, default=0)
    confidence = Column(String(20), default="low")
    
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureFlag(Base):
    """
    Feature flags for granular control of platform functionality.
    
    Allows enabling/disabling features per company or globally.
    Supports gradual rollouts and A/B testing.
    """
    __tablename__ = "feature_flags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    flag_key = Column(String(100), nullable=False, index=True)
    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - feature_flags global rollout (NULL=enabled for ALL companies, UUID=enabled per-company) - anonymized cross-tenant pattern per ADR-LGPD-001
    company_id = Column(String(255), nullable=True, index=True)
    
    is_enabled = Column(Boolean, default=False)
    
    rollout_percentage = Column(Integer, default=100)
    
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")
    
    flag_metadata = Column(JSON, default=dict)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('flag_key', 'company_id', name='uq_feature_flag_company'),
        Index('ix_feature_flags_key_enabled', 'flag_key', 'is_enabled'),
        Index(
            'ix_feature_flags_global_unique',
            'flag_key',
            unique=True,
            postgresql_where=text('company_id IS NULL')
        ),
    {"extend_existing": True}, )


class StageFeedback(Base):
    """
    Captures feedback from all wizard stages (2-7).
    
    Tracks what was suggested vs what was accepted/rejected
    to improve future suggestions per stage.
    """
    __tablename__ = "stage_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    stage_number = Column(Integer, nullable=False, index=True)
    stage_name = Column(String(100), nullable=True)
    
    field_name = Column(String(100), nullable=False, index=True)
    
    suggested_value = Column(JSON, nullable=True)
    accepted_value = Column(JSON, nullable=True)
    
    was_accepted = Column(Boolean, default=True)
    was_modified = Column(Boolean, default=False)
    
    role = Column(String(255), nullable=True, index=True)
    seniority = Column(String(50), nullable=True)
    
    confidence_before = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('ix_stage_feedback_company_stage', 'company_id', 'stage_number'),
        Index('ix_stage_feedback_field', 'company_id', 'field_name'),
    {"extend_existing": True}, )


class LearningAnalytics(Base):
    """
    Aggregated analytics for learning system dashboard.
    
    Pre-computed metrics for fast dashboard loading.
    """
    __tablename__ = "learning_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    company_id = Column(String(255), nullable=False, index=True)
    
    metric_type = Column(String(100), nullable=False, index=True)
    metric_key = Column(String(255), nullable=False)
    
    metric_value = Column(JSON, nullable=False)
    
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    sample_size = Column(Integer, default=0)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_learning_analytics_company_type', 'company_id', 'metric_type'),
    {"extend_existing": True}, )
