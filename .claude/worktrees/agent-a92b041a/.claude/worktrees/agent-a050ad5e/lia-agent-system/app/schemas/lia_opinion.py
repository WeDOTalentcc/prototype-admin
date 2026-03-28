"""
Pydantic schemas for LIA Opinion (Parecer) API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class OpinionTypeEnum(str, Enum):
    GENERAL = "general"
    WSI = "wsi"


class OpinionSourceEnum(str, Enum):
    CV_ANALYSIS = "cv_analysis"
    TEXT_SCREENING = "text_screening"
    VOICE_SCREENING = "voice_screening"
    FULL_INTERVIEW = "full_interview"
    MANUAL = "manual"
    CALIBRATION = "calibration"


class RecommendationEnum(str, Enum):
    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    NOT_APPROVED = "not_approved"


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown."""
    skills_match: Optional[float] = None
    experience_match: Optional[float] = None
    seniority_match: Optional[float] = None
    location_match: Optional[float] = None
    title_match: Optional[float] = None
    cultural_fit: Optional[float] = None
    personality_fit: Optional[float] = None


class TechnicalAnalysis(BaseModel):
    """Technical competency analysis."""
    strengths: List[Dict[str, Any]] = Field(default_factory=list)
    gaps: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)


class BehavioralAnalysis(BaseModel):
    """Behavioral/Big Five analysis."""
    collaboration_score: Optional[float] = None
    innovation_score: Optional[float] = None
    organization_score: Optional[float] = None
    resilience_score: Optional[float] = None
    observations: List[str] = Field(default_factory=list)


class CulturalFitAnalysis(BaseModel):
    """Cultural fit analysis."""
    score: Optional[float] = None
    aligned_values: List[str] = Field(default_factory=list)
    attention_points: List[str] = Field(default_factory=list)


class LiaOpinionCreate(BaseModel):
    """Schema for creating a new LIA opinion."""
    candidate_id: UUID
    opinion_type: OpinionTypeEnum = OpinionTypeEnum.GENERAL
    source: OpinionSourceEnum = OpinionSourceEnum.CV_ANALYSIS
    job_vacancy_id: Optional[UUID] = None
    wsi_screening_id: Optional[UUID] = None
    
    score: Optional[float] = Field(None, ge=0, le=100)
    wsi_score: Optional[float] = Field(None, ge=0, le=5)
    recommendation: Optional[RecommendationEnum] = None
    
    summary: Optional[str] = None
    archetype: Optional[str] = None
    archetype_match_score: Optional[float] = None
    
    score_breakdown: Optional[Dict[str, Any]] = Field(default_factory=dict)
    technical_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    behavioral_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    cultural_fit: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    
    next_steps: Optional[str] = None
    recruiter_notes: Optional[str] = None


class LiaOpinionUpdate(BaseModel):
    """Schema for updating a LIA opinion."""
    score: Optional[float] = Field(None, ge=0, le=100)
    wsi_score: Optional[float] = Field(None, ge=0, le=5)
    recommendation: Optional[RecommendationEnum] = None
    summary: Optional[str] = None
    
    recruiter_notes: Optional[str] = None
    recruiter_override: Optional[RecommendationEnum] = None
    recruiter_override_reason: Optional[str] = None


class LiaOpinionCompact(BaseModel):
    """Compact representation for preview display."""
    id: UUID
    opinion_type: str
    source: str
    score: Optional[float] = None
    wsi_score: Optional[float] = None
    recommendation: Optional[str] = None
    summary: Optional[str] = None
    archetype: Optional[str] = None
    job_vacancy_id: Optional[UUID] = None
    job_vacancy_title: Optional[str] = None
    created_at: Optional[datetime] = None
    is_current: bool = True
    
    class Config:
        from_attributes = True


class LiaOpinionFull(BaseModel):
    """Full representation with all details."""
    id: UUID
    candidate_id: UUID
    opinion_type: str
    source: str
    job_vacancy_id: Optional[UUID] = None
    job_vacancy_title: Optional[str] = None
    wsi_screening_id: Optional[UUID] = None
    
    score: Optional[float] = None
    wsi_score: Optional[float] = None
    recommendation: Optional[str] = None
    
    summary: Optional[str] = None
    archetype: Optional[str] = None
    archetype_match_score: Optional[float] = None
    
    score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    technical_analysis: Dict[str, Any] = Field(default_factory=dict)
    behavioral_analysis: Dict[str, Any] = Field(default_factory=dict)
    cultural_fit: Dict[str, Any] = Field(default_factory=dict)
    
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    
    next_steps: Optional[str] = None
    
    recruiter_notes: Optional[str] = None
    recruiter_override: Optional[str] = None
    recruiter_override_reason: Optional[str] = None
    recruiter_override_by: Optional[str] = None
    recruiter_override_at: Optional[datetime] = None
    
    is_current: bool = True
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class CandidateOpinionsSummary(BaseModel):
    """Summary of all opinions for a candidate."""
    candidate_id: UUID
    total_opinions: int = 0
    current_general_opinion: Optional[LiaOpinionCompact] = None
    vacancy_opinions: List[LiaOpinionCompact] = Field(default_factory=list)
    has_pending_review: bool = False


class LiaOpinionListResponse(BaseModel):
    """Response for listing opinions."""
    items: List[LiaOpinionFull]
    total: int
    page: int = 1
    page_size: int = 20
