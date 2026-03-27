"""
Pydantic schemas for Company Culture Profile endpoints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class CompanyCultureProfileBase(BaseModel):
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: List[str] = []
    evp_bullets: List[str] = []
    core_competencies: List[str] = []
    culture_description: Optional[str] = None
    website_url: str
    linkedin_url: Optional[str] = None
    analyzed_pages: List[str] = []
    openness_score: int = Field(default=50, ge=0, le=100)
    conscientiousness_score: int = Field(default=50, ge=0, le=100)
    extraversion_score: int = Field(default=50, ge=0, le=100)
    agreeableness_score: int = Field(default=50, ge=0, le=100)
    stability_score: int = Field(default=50, ge=0, le=100)
    
    industry: Optional[str] = None
    employee_count: Optional[str] = None  # e.g., "501-1000"
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    locations: List[str] = []
    founded_year: Optional[int] = None
    
    work_model: Optional[str] = None
    growth_opportunities: Optional[str] = None
    team_dynamics: Optional[str] = None
    leadership_style: Optional[str] = None
    
    dei_initiatives: Optional[str] = None
    sustainability: Optional[str] = None
    social_impact: Optional[str] = None
    
    tech_stack: List[str] = []
    engineering_culture: Optional[str] = None
    default_languages: List[str] = []


class CompanyCultureProfileCreate(CompanyCultureProfileBase):
    company_id: UUID
    source: str = "manual"
    confidence_score: float = Field(default=1.0, ge=0, le=1)


class CompanyCultureProfileUpdate(BaseModel):
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: Optional[List[str]] = None
    evp_bullets: Optional[List[str]] = None
    core_competencies: Optional[List[str]] = None
    culture_description: Optional[str] = None
    linkedin_url: Optional[str] = None
    openness_score: Optional[int] = Field(default=None, ge=0, le=100)
    conscientiousness_score: Optional[int] = Field(default=None, ge=0, le=100)
    extraversion_score: Optional[int] = Field(default=None, ge=0, le=100)
    agreeableness_score: Optional[int] = Field(default=None, ge=0, le=100)
    stability_score: Optional[int] = Field(default=None, ge=0, le=100)
    
    industry: Optional[str] = None
    employee_count: Optional[str] = None  # e.g., "501-1000"
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    locations: Optional[List[str]] = None
    founded_year: Optional[int] = None
    
    work_model: Optional[str] = None
    growth_opportunities: Optional[str] = None
    team_dynamics: Optional[str] = None
    leadership_style: Optional[str] = None
    
    dei_initiatives: Optional[str] = None
    sustainability: Optional[str] = None
    social_impact: Optional[str] = None
    
    tech_stack: Optional[List[str]] = None
    engineering_culture: Optional[str] = None
    default_languages: Optional[List[str]] = None


class CompanyCultureProfileResponse(CompanyCultureProfileBase):
    id: UUID
    company_id: UUID
    source: str
    confidence_score: float
    last_analysis_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CultureAnalysisRequest(BaseModel):
    website_url: str
    company_id: UUID
    force_refresh: bool = False


class CultureAnalysisDirectRequest(BaseModel):
    """Request for direct culture analysis without requiring company_id in database."""
    website_url: str
    linkedin_url: Optional[str] = None
    company_id: Optional[str] = None


class CultureAnalysisJobResponse(BaseModel):
    job_id: UUID
    status: str
    progress: int
    current_step: Optional[str] = None
    message: str


class CultureAnalysisJobStatus(BaseModel):
    job_id: UUID
    status: str
    progress: int
    current_step: Optional[str] = None
    pages_discovered: int = 0
    pages_scraped: int = 0
    error_message: Optional[str] = None
    result_profile_id: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class BigFiveOrgProfile(BaseModel):
    openness: int = Field(default=50, description="Inovação, abertura a mudanças, criatividade", ge=0, le=100)
    conscientiousness: int = Field(default=50, description="Processos, qualidade, organização", ge=0, le=100)
    extraversion: int = Field(default=50, description="Colaboração, energia, comunicação", ge=0, le=100)
    agreeableness: int = Field(default=50, description="Foco em pessoas, empatia, trabalho em equipe", ge=0, le=100)
    stability: int = Field(default=50, description="Resiliência, calma, estabilidade", ge=0, le=100)


class CultureAnalysisResult(BaseModel):
    mission: Optional[str] = None
    vision: Optional[str] = None
    values: List[str] = []
    evp_bullets: List[str] = []
    core_competencies: List[str] = []
    culture_description: Optional[str] = None
    big_five: BigFiveOrgProfile
    linkedin_url: Optional[str] = None
    analyzed_pages: List[str] = []
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    
    industry: Optional[str] = None
    employee_count: Optional[str] = None  # e.g., "501-1000"
    company_size: Optional[str] = None
    headquarters: Optional[str] = None
    locations: List[str] = []
    founded_year: Optional[int] = None
    
    work_model: Optional[str] = None
    growth_opportunities: Optional[str] = None
    team_dynamics: Optional[str] = None
    leadership_style: Optional[str] = None
    
    dei_initiatives: Optional[str] = None
    sustainability: Optional[str] = None
    social_impact: Optional[str] = None
    
    tech_stack: List[str] = []
    engineering_culture: Optional[str] = None


class ScrapedPageContent(BaseModel):
    url: str
    title: Optional[str] = None
    content: str
    page_type: str
