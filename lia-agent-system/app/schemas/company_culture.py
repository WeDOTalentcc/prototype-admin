"""
Pydantic schemas for Company Culture Profile endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from app.shared.types import WeDoBaseModel


def _normalize_list_of_strings(v):
    """Task #1161 (Bug C raiz): aceita lista mista (str | dict) vinda de seeds/UI
    legados — ex.: default_languages com [{code,label,level,required}] — e
    devolve sempre list[str]. Defesa em profundidade: protege a serialização
    Pydantic contra ResponseValidationError 500 quando o JSON salvo no banco
    drifta do contrato. Mantém ordem; ignora None/strings vazias depois do strip."""
    if v is None:
        return []
    if not isinstance(v, list):
        return v  # deixa Pydantic levantar o erro original (não é uma lista)
    out: list[str] = []
    for item in v:
        if item is None:
            continue
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
            continue
        if isinstance(item, dict):
            # Preferência: code → name → label → value → str(item)
            for key in ("code", "name", "label", "value"):
                candidate = item.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    out.append(candidate.strip())
                    break
            continue
        # Outros tipos primitivos: coerce para str
        out.append(str(item))
    return out


class CompanyCultureProfileBase(BaseModel):
    mission: str | None = None
    vision: str | None = None
    values: list[str] = []
    evp_bullets: list[str] = []
    core_competencies: list[str] = []
    culture_description: str | None = None
    website_url: str
    linkedin_url: str | None = None
    analyzed_pages: list[str] = []
    openness_score: int = Field(default=50, ge=0, le=100)
    conscientiousness_score: int = Field(default=50, ge=0, le=100)
    extraversion_score: int = Field(default=50, ge=0, le=100)
    agreeableness_score: int = Field(default=50, ge=0, le=100)
    stability_score: int = Field(default=50, ge=0, le=100)
    
    industry: str | None = None
    employee_count: str | None = None  # e.g., "501-1000"
    company_size: str | None = None
    headquarters: str | None = None
    locations: list[str] = []
    founded_year: int | None = None
    
    work_model: str | None = None
    growth_opportunities: str | None = None
    team_dynamics: str | None = None
    leadership_style: str | None = None
    
    dei_initiatives: str | None = None
    sustainability: str | None = None
    social_impact: str | None = None
    
    tech_stack: list[str] = []
    engineering_culture: str | None = None
    default_languages: list[str] = []

    # Task #1161 (Bug C raiz): defesa em profundidade contra ResponseValidationError 500
    # quando o JSON salvo no banco drifta do contrato list[str] (ex.: default_languages
    # gravado como [{code,label,level,required}] pelo UI antigo).
    @field_validator(
        "values",
        "evp_bullets",
        "core_competencies",
        "analyzed_pages",
        "locations",
        "tech_stack",
        "default_languages",
        mode="before",
    )
    @classmethod
    def _coerce_list_of_strings(cls, v):
        return _normalize_list_of_strings(v)


class CompanyCultureProfileCreate(CompanyCultureProfileBase):
    company_id: UUID
    source: str = "manual"
    confidence_score: float = Field(default=1.0, ge=0, le=1)


class CompanyCultureProfileUpdate(WeDoBaseModel):
    mission: str | None = None
    vision: str | None = None
    values: list[str] | None = None
    evp_bullets: list[str] | None = None
    core_competencies: list[str] | None = None
    culture_description: str | None = None
    linkedin_url: str | None = None
    openness_score: int | None = Field(default=None, ge=0, le=100)
    conscientiousness_score: int | None = Field(default=None, ge=0, le=100)
    extraversion_score: int | None = Field(default=None, ge=0, le=100)
    agreeableness_score: int | None = Field(default=None, ge=0, le=100)
    stability_score: int | None = Field(default=None, ge=0, le=100)
    
    industry: str | None = None
    employee_count: str | None = None  # e.g., "501-1000"
    company_size: str | None = None
    headquarters: str | None = None
    locations: list[str] | None = None
    founded_year: int | None = None
    
    work_model: str | None = None
    growth_opportunities: str | None = None
    team_dynamics: str | None = None
    leadership_style: str | None = None
    
    dei_initiatives: str | None = None
    sustainability: str | None = None
    social_impact: str | None = None
    
    tech_stack: list[str] | None = None
    engineering_culture: str | None = None
    default_languages: list[str] | None = None


class CompanyCultureProfileResponse(CompanyCultureProfileBase):
    id: UUID
    company_id: UUID
    source: str
    confidence_score: float
    is_approved: bool = False
    approved_at: datetime | None = None
    last_analysis_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CultureAnalysisRequest(WeDoBaseModel):
    website_url: str
    company_id: UUID
    force_refresh: bool = False


class CultureAnalysisDirectRequest(WeDoBaseModel):
    """Request for direct culture analysis without requiring company_id in database."""
    website_url: str
    linkedin_url: str | None = None
    company_id: str | None = None


class CultureAnalysisJobResponse(BaseModel):
    job_id: UUID
    status: str
    progress: int
    current_step: str | None = None
    message: str


class CultureAnalysisJobStatus(BaseModel):
    job_id: UUID
    status: str
    progress: int
    current_step: str | None = None
    pages_discovered: int = 0
    pages_scraped: int = 0
    error_message: str | None = None
    result_profile_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
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
    mission: str | None = None
    vision: str | None = None
    values: list[str] = []
    evp_bullets: list[str] = []
    core_competencies: list[str] = []
    culture_description: str | None = None
    big_five: BigFiveOrgProfile
    linkedin_url: str | None = None
    analyzed_pages: list[str] = []
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    
    industry: str | None = None
    employee_count: str | None = None  # e.g., "501-1000"
    company_size: str | None = None
    headquarters: str | None = None
    locations: list[str] = []
    founded_year: int | None = None
    
    work_model: str | None = None
    growth_opportunities: str | None = None
    team_dynamics: str | None = None
    leadership_style: str | None = None
    
    dei_initiatives: str | None = None
    sustainability: str | None = None
    social_impact: str | None = None
    
    tech_stack: list[str] = []
    engineering_culture: str | None = None


class ScrapedPageContent(BaseModel):
    url: str
    title: str | None = None
    content: str
    page_type: str
