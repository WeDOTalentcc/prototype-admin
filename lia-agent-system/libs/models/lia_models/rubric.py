"""
Rubric models for structured candidate evaluation.

Based on Schmidt & Hunter (1998) meta-analysis and BARS methodology.
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from lia_config.database import Base


class RequirementPriority(str, Enum):
    """Priority levels for job requirements with multipliers."""
    ESSENTIAL = "essential"      # 3x multiplier - eliminatory requirements
    IMPORTANT = "important"      # 2x multiplier - significant impact on performance
    NICE_TO_HAVE = "nice_to_have"  # 1x multiplier - differentiators

    @property
    def multiplier(self) -> int:
        """Get the weight multiplier for this priority."""
        multipliers = {
            RequirementPriority.ESSENTIAL: 3,
            RequirementPriority.IMPORTANT: 2,
            RequirementPriority.NICE_TO_HAVE: 1,
        }
        return multipliers[self]


class EvaluationLevel(str, Enum):
    """Evaluation levels based on BARS (Behaviorally Anchored Rating Scales)."""
    EXCEEDS = "exceeds"   # 100 pts - Exceptional evidence, exceeds requirements
    MEETS = "meets"       # 75 pts  - Clearly demonstrates the competency
    PARTIAL = "partial"   # 40 pts  - Related but not direct evidence
    MISSING = "missing"   # 0 pts   - No evidence found

    @property
    def points(self) -> int:
        """Get the points for this evaluation level."""
        points_map = {
            EvaluationLevel.EXCEEDS: 100,
            EvaluationLevel.MEETS: 75,
            EvaluationLevel.PARTIAL: 40,
            EvaluationLevel.MISSING: 0,
        }
        return points_map[self]


class JobRequirement(Base):
    """
    Job requirement with priority for rubric evaluation.
    """
    __tablename__ = "job_requirements"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    requirement = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), nullable=False, default=RequirementPriority.IMPORTANT.value)
    category = Column(String(100), nullable=True)  # technical, experience, education, soft_skill
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<JobRequirement {self.id} - {self.requirement[:50]}>"


class RubricEvaluation(Base):
    """
    Stores rubric evaluation results for a candidate-job pair.
    """
    __tablename__ = "rubric_evaluations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False, index=True)
    
    score = Column(Float, nullable=False)  # 0-100
    evaluations = Column(JSONB, nullable=False, default=list)  # List of RequirementEvaluation
    strengths = Column(JSONB, nullable=False, default=list)
    concerns = Column(JSONB, nullable=False, default=list)
    reasoning = Column(Text, nullable=True)
    
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    evaluated_by = Column(String(100), nullable=True)  # 'system' or user_id
    model_version = Column(String(50), nullable=True)  # LLM model used
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RubricEvaluation {self.id} - Score: {self.score}>"
