"""
Pydantic schemas for LIA Profile Analysis API.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AnalysisTypeEnum(str, Enum):
    BULLET_POINTS = "bullet_points"
    SHORT_PARAGRAPH = "short_paragraph"
    DETAILED_BULLETS = "detailed_bullets"


class LiaProfileAnalysisCreate(BaseModel):
    """Schema for creating a new profile analysis."""
    candidate_id: str
    analysis_type: AnalysisTypeEnum
    content: str
    candidate_name: Optional[str] = None
    created_by: Optional[str] = None


class LiaProfileAnalysisResponse(BaseModel):
    """Response schema for a profile analysis."""
    id: str
    candidate_id: str
    analysis_type: str
    content: str
    candidate_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    company_id: str
    
    class Config:
        from_attributes = True


class CandidateAnalysesSummary(BaseModel):
    """Summary of all analyses for a candidate."""
    candidate_id: str
    total_analyses: int = 0
    analyses: List[LiaProfileAnalysisResponse] = Field(default_factory=list)
    has_bullet_points: bool = False
    has_short_paragraph: bool = False
    has_detailed_bullets: bool = False
