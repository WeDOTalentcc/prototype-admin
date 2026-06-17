"""
LIA Opinion (Parecer) models for candidate assessments.

Two types of opinions:
1. General Opinion - Independent assessment without a vacancy
2. WSI Opinion - Vacancy-linked assessment based on screening/interview
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, Float, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from lia_config.database import Base


class OpinionType(enum.Enum):
    """Type of LIA opinion."""
    GENERAL = "general"  # Independent assessment
    WSI = "wsi"  # Vacancy-linked WSI assessment


class OpinionSource(enum.Enum):
    """Source of the opinion data."""
    CV_ANALYSIS = "cv_analysis"  # From CV/resume analysis
    TEXT_SCREENING = "text_screening"  # From WSI text screening
    VOICE_SCREENING = "voice_screening"  # From voice interview
    FULL_INTERVIEW = "full_interview"  # From complete WSI interview
    MANUAL = "manual"  # Manually entered by recruiter
    CALIBRATION = "calibration"  # From calibration process


class RecommendationType(enum.Enum):
    """Recommendation status."""
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    NOT_APPROVED = "not_approved"


class LiaOpinion(Base):
    """
    LIA's structured opinion/assessment for a candidate.
    
    Can be:
    - General: Independent assessment based on CV/profile analysis
    - WSI: Vacancy-linked assessment based on screening/interview process
    """
    __tablename__ = "lia_opinions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    opinion_type = Column(String(50), nullable=False, default="general", index=True)
    source = Column(String(50), nullable=False, default="cv_analysis")
    
    job_vacancy_id = Column(UUID(as_uuid=True), ForeignKey("job_vacancies.id", ondelete="SET NULL"), nullable=True, index=True)
    wsi_screening_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    score = Column(Float, nullable=True)
    wsi_score = Column(Float, nullable=True)
    
    recommendation = Column(String(50), nullable=True)
    
    summary = Column(Text, nullable=True)
    
    archetype = Column(String(100), nullable=True)
    archetype_match_score = Column(Float, nullable=True)
    
    score_breakdown = Column(JSON, default={})
    
    technical_analysis = Column(JSON, default={})
    
    behavioral_analysis = Column(JSON, default={})
    
    cultural_fit = Column(JSON, default={})
    
    strengths = Column(JSON, default=[])
    concerns = Column(JSON, default=[])
    gaps = Column(JSON, default=[])
    
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    
    next_steps = Column(Text, nullable=True)
    
    recruiter_notes = Column(Text, nullable=True)
    recruiter_override = Column(String(50), nullable=True)
    recruiter_override_reason = Column(Text, nullable=True)
    recruiter_override_by = Column(String(255), nullable=True)
    recruiter_override_at = Column(DateTime, nullable=True)
    
    is_current = Column(Boolean, default=True, index=True)
    version = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255), nullable=True)
    
    company_id = Column(String(100), nullable=False, index=True)
    
    def __repr__(self):
        return f"<LiaOpinion {self.id} - {self.opinion_type} - Score: {self.score}>"
    
    @property
    def is_vacancy_linked(self) -> bool:
        """Check if this opinion is linked to a vacancy."""
        return self.job_vacancy_id is not None
    
    def to_compact_dict(self) -> dict:
        """Return compact representation for preview."""
        return {
            "id": str(self.id),
            "opinion_type": self.opinion_type,
            "score": self.score,
            "wsi_score": self.wsi_score,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "archetype": self.archetype,
            "job_vacancy_id": str(self.job_vacancy_id) if self.job_vacancy_id else None,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_current": self.is_current,
        }
    
    def to_full_dict(self) -> dict:
        """Return full representation with all details."""
        return {
            "id": str(self.id),
            "candidate_id": str(self.candidate_id),
            "opinion_type": self.opinion_type,
            "source": self.source,
            "job_vacancy_id": str(self.job_vacancy_id) if self.job_vacancy_id else None,
            "wsi_screening_id": str(self.wsi_screening_id) if self.wsi_screening_id else None,
            "score": self.score,
            "wsi_score": self.wsi_score,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "archetype": self.archetype,
            "archetype_match_score": self.archetype_match_score,
            "score_breakdown": self.score_breakdown,
            "technical_analysis": self.technical_analysis,
            "behavioral_analysis": self.behavioral_analysis,
            "cultural_fit": self.cultural_fit,
            "strengths": self.strengths,
            "concerns": self.concerns,
            "gaps": self.gaps,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "next_steps": self.next_steps,
            "recruiter_notes": self.recruiter_notes,
            "recruiter_override": self.recruiter_override,
            "recruiter_override_reason": self.recruiter_override_reason,
            "recruiter_override_by": self.recruiter_override_by,
            "recruiter_override_at": self.recruiter_override_at.isoformat() if self.recruiter_override_at else None,
            "is_current": self.is_current,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "company_id": self.company_id,
        }
