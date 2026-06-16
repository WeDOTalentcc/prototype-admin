"""
Pydantic schemas for LIA Profile Analysis API.
"""
from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class AnalysisTypeEnum(StrEnum):
    BULLET_POINTS = "bullet_points"
    SHORT_PARAGRAPH = "short_paragraph"
    DETAILED_BULLETS = "detailed_bullets"


class LiaProfileAnalysisCreate(WeDoBaseModel):
    """Schema for creating a new profile analysis."""
    candidate_id: str
    analysis_type: AnalysisTypeEnum
    content: str
    candidate_name: str | None = None
    created_by: str | None = None


class LiaProfileAnalysisResponse(BaseModel):
    """Response schema for a profile analysis."""
    id: str
    candidate_id: str
    analysis_type: str
    content: str
    candidate_name: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    created_by: str | None = None
    company_id: str
    
    class Config:
        from_attributes = True


class CandidateAnalysesSummary(BaseModel):
    """Summary of all analyses for a candidate."""
    candidate_id: str
    total_analyses: int = 0
    analyses: list[LiaProfileAnalysisResponse] = Field(default_factory=list)
    has_bullet_points: bool = False
    has_short_paragraph: bool = False
    has_detailed_bullets: bool = False
