"""
Pydantic schemas for Company Culture Profile endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


# Field-name -> default value used to coerce legacy NULL values from the DB.
#
# Belt-and-suspenders since Task #1100 / alembic 130_culture_profile_defaults_not_null:
# the database now enforces NOT NULL + ``server_default`` (``ARRAY[]::text[]``
# for the array columns, ``50`` for the Big Five scores) on every field
# below, so freshly-written rows can no longer carry NULL. We keep the
# coercion as a defensive guard for any pre-migration row that might still
# be cached in a long-lived ORM session, and to keep the response contract
# (``[]`` and ``50``) deterministic if the migration is rolled back via
# ``downgrade()`` (which leaves the DEFAULT in place but drops NOT NULL).
#
# Original symptom: ``GET /culture-profile`` raised ``ResponseValidationError``
# when reading a legacy row with NULL in any non-Optional field.
_CULTURE_BASE_NONE_DEFAULTS: dict[str, object] = {
    "values": list,
    "evp_bullets": list,
    "core_competencies": list,
    "analyzed_pages": list,
    "locations": list,
    "tech_stack": list,
    "default_languages": list,
    "openness_score": 50,
    "conscientiousness_score": 50,
    "extraversion_score": 50,
    "agreeableness_score": 50,
    "stability_score": 50,
}


def _coerce_culture_none_defaults(data: object) -> object:
    """Replace NULL DB values with the schema default for non-Optional fields.

    Handles both dict input (direct construction / ``model_validate``) and
    ORM object input (``from_attributes=True``, the production path used by
    the FastAPI ``response_model`` machinery). For ORM objects we promote
    them to a dict carrying every attribute Pydantic will need to read,
    substituting ``None`` with the canonical defaults along the way.
    """
    if isinstance(data, dict):
        for field, default in _CULTURE_BASE_NONE_DEFAULTS.items():
            if data.get(field) is None:
                data[field] = default() if callable(default) else default
        return data

    # Non-dict, non-base-model: treat as ORM-like object and project to dict
    # so the coerced defaults survive ``from_attributes`` validation.
    if isinstance(data, BaseModel):
        return data
    if not hasattr(data, "__dict__") and not hasattr(data, "__class__"):
        return data
    promoted: dict[str, object] = {}
    # Copy every attribute Pydantic could possibly read off the ORM row.
    # We rely on getattr (not __dict__) so SQLAlchemy lazy-load attributes
    # behave correctly. Unknown attributes are simply ignored by Pydantic.
    candidate_fields = set(_CULTURE_BASE_NONE_DEFAULTS.keys()) | {
        # everything CompanyCultureProfileBase / Response declares
        "mission", "vision", "culture_description", "website_url",
        "linkedin_url", "industry", "employee_count", "company_size",
        "headquarters", "founded_year", "work_model", "growth_opportunities",
        "team_dynamics", "leadership_style", "dei_initiatives",
        "sustainability", "social_impact", "engineering_culture",
        "id", "company_id", "source", "confidence_score",
        "last_analysis_at", "created_at", "updated_at",
    }
    for field in candidate_fields:
        if hasattr(data, field):
            promoted[field] = getattr(data, field)
    for field, default in _CULTURE_BASE_NONE_DEFAULTS.items():
        if promoted.get(field) is None:
            promoted[field] = default() if callable(default) else default
    return promoted


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

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_nulls(cls, data: object) -> object:
        return _coerce_culture_none_defaults(data)


class CompanyCultureProfileCreate(CompanyCultureProfileBase):
    company_id: UUID
    source: str = "manual"
    confidence_score: float = Field(default=1.0, ge=0, le=1)


class CompanyCultureProfileUpdate(BaseModel):
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
