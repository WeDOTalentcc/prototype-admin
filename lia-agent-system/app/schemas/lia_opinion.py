"""
Pydantic schemas for LIA Opinion (Parecer) API.
"""
from datetime import datetime
from enum import Enum, StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class OpinionTypeEnum(StrEnum):
    GENERAL = "general"
    WSI = "wsi"


class OpinionSourceEnum(StrEnum):
    CV_ANALYSIS = "cv_analysis"
    TEXT_SCREENING = "text_screening"
    VOICE_SCREENING = "voice_screening"
    FULL_INTERVIEW = "full_interview"
    MANUAL = "manual"
    CALIBRATION = "calibration"


class RecommendationEnum(StrEnum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    NOT_APPROVED = "not_approved"


class LiaOpinionScoreBreakdown(BaseModel):
    """Detailed score breakdown."""
    skills_match: float | None = None
    experience_match: float | None = None
    seniority_match: float | None = None
    location_match: float | None = None
    title_match: float | None = None
    cultural_fit: float | None = None
    personality_fit: float | None = None


class TechnicalAnalysis(BaseModel):
    """Technical competency analysis."""
    strengths: list[dict[str, Any]] = Field(default_factory=list)
    gaps: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class BehavioralAnalysis(BaseModel):
    """Behavioral/Big Five analysis."""
    collaboration_score: float | None = None
    innovation_score: float | None = None
    organization_score: float | None = None
    resilience_score: float | None = None
    observations: list[str] = Field(default_factory=list)


class CulturalFitAnalysis(BaseModel):
    """Cultural fit analysis."""
    score: float | None = None
    aligned_values: list[str] = Field(default_factory=list)
    attention_points: list[str] = Field(default_factory=list)


class LiaOpinionCreate(WeDoBaseModel):
    """Schema for creating a new LIA opinion."""
    candidate_id: UUID
    opinion_type: OpinionTypeEnum = OpinionTypeEnum.GENERAL
    source: OpinionSourceEnum = OpinionSourceEnum.CV_ANALYSIS
    job_vacancy_id: UUID | None = None
    wsi_screening_id: UUID | None = None
    
    score: float | None = Field(None, ge=0, le=100)
    wsi_score: float | None = Field(None, ge=0, le=5)
    recommendation: RecommendationEnum | None = None
    
    summary: str | None = None
    archetype: str | None = None
    archetype_match_score: float | None = None
    
    score_breakdown: dict[str, Any] | None = Field(default_factory=dict)
    technical_analysis: dict[str, Any] | None = Field(default_factory=dict)
    behavioral_analysis: dict[str, Any] | None = Field(default_factory=dict)
    cultural_fit: dict[str, Any] | None = Field(default_factory=dict)
    
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    
    next_steps: str | None = None
    recruiter_notes: str | None = None


class LiaOpinionUpdate(WeDoBaseModel):
    """Schema for updating a LIA opinion."""
    score: float | None = Field(None, ge=0, le=100)
    wsi_score: float | None = Field(None, ge=0, le=5)
    recommendation: RecommendationEnum | None = None
    summary: str | None = None
    
    recruiter_notes: str | None = None
    recruiter_override: RecommendationEnum | None = None
    recruiter_override_reason: str | None = None


class LiaOpinionCompact(BaseModel):
    """Compact representation for preview display."""
    id: UUID
    opinion_type: str
    source: str
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score: float | None = None
    wsi_score: float | None = None
    recommendation: str | None = None
    summary: str | None = None
    archetype: str | None = None
    job_vacancy_id: UUID | None = None
    job_vacancy_title: str | None = None
    created_at: datetime | None = None
    is_current: bool = True
    
    class Config:
        from_attributes = True


class LiaOpinionFull(BaseModel):
    """Full representation with all details."""
    id: UUID
    candidate_id: UUID
    opinion_type: str
    source: str
    job_vacancy_id: UUID | None = None
    job_vacancy_title: str | None = None
    wsi_screening_id: UUID | None = None
    
    score: float | None = None
    wsi_score: float | None = None
    recommendation: str | None = None
    
    summary: str | None = None
    archetype: str | None = None
    archetype_match_score: float | None = None
    
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    technical_analysis: dict[str, Any] = Field(default_factory=dict)
    behavioral_analysis: dict[str, Any] = Field(default_factory=dict)
    cultural_fit: dict[str, Any] = Field(default_factory=dict)
    
    strengths: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    
    next_steps: str | None = None
    
    recruiter_notes: str | None = None
    recruiter_override: str | None = None
    recruiter_override_reason: str | None = None
    recruiter_override_by: str | None = None
    recruiter_override_at: datetime | None = None
    
    is_current: bool = True
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    
    class Config:
        from_attributes = True


class CandidateOpinionsSummary(BaseModel):
    """Summary of all opinions for a candidate."""
    candidate_id: UUID
    total_opinions: int = 0
    current_general_opinion: LiaOpinionCompact | None = None
    vacancy_opinions: list[LiaOpinionCompact] = Field(default_factory=list)
    has_pending_review: bool = False


class LiaOpinionListResponse(BaseModel):
    """Response for listing opinions."""
    items: list[LiaOpinionFull]
    total: int
    page: int = 1
    page_size: int = 20
