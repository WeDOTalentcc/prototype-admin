"""
Evaluation Criteria models for André's methodology - Phase 3.
Stores positive/negative evidence examples per criterion type for LLM prompt enhancement.
Auto-seeded from existing catalogs, auto-updated by feedback. No manual admin needed.
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from lia_config.database import Base


class CriterionCategory(str, Enum):
    TECHNICAL_SKILL = "technical_skill"
    BEHAVIORAL_COMPETENCY = "behavioral_competency"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    RESPONSIBILITY = "responsibility"


class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(300), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)

    positive_evidences = Column(JSONB, nullable=False, default=list)
    negative_evidences = Column(JSONB, nullable=False, default=list)

    evaluation_guidelines = Column(Text, nullable=True)

    effectiveness_score = Column(Float, nullable=False, default=0.5)
    usage_count = Column(Integer, nullable=False, default=0)
    feedback_count = Column(Integer, nullable=False, default=0)

    source = Column(String(50), nullable=False, default="seed")
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<EvaluationCriteria {self.name} ({self.category})>"
