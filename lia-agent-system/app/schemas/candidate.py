"""
Pydantic schemas for candidate API.
"""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from app.shared.types import WeDoBaseModel


class CandidateBase(BaseModel):
    """Base candidate schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    email: str | None = Field(None, description="Email do candidato (opcional)")

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v):
        """UC-P1-30: Validate email format, normalize to lowercase, reject empty strings."""
        if v is None:
            return None
        import re
        cleaned = str(v).strip().lower()
        if cleaned == "":
            raise ValueError("Formato de email invalido: string vazia nao e aceita")
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$"
        if not re.match(pattern, cleaned):
            raise ValueError(f"Formato de email invalido: {v!r}")
        return cleaned
    phone: str | None = Field(None, max_length=50)
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    
    current_title: str | None = None
    current_company: str | None = None
    seniority_level: str | None = None
    years_of_experience: int | None = None
    
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    languages: dict[str, str] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    is_remote: bool = False
    willing_to_relocate: bool = False
    
    desired_salary_min: float | None = None
    desired_salary_max: float | None = None
    salary_currency: str = "BRL"
    work_model_preference: str | None = None
    contract_type_preference: str | None = None
    
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class CandidateCreate(CandidateBase):
    """Schema for creating a new candidate."""
    source: str = Field(..., description="Source: 'ats', 'manual', 'pearch', 'linkedin'")
    ats_source_name: str | None = None
    ats_candidate_id: str | None = None
    pearch_profile_id: str | None = None
    resume_url: str | None = None
    resume_text: str | None = None
    work_history: list[dict] | None = Field(default_factory=list, description="List of work experiences with company metadata")
    additional_data: dict = Field(default_factory=dict)
    auto_enrich: bool = Field(default=False, description="Auto-enrich from LinkedIn when linkedin_url is provided")


class CandidateUpdate(WeDoBaseModel):
    """Schema for updating a candidate (all fields optional)."""
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    current_title: str | None = None
    current_company: str | None = None
    seniority_level: str | None = None
    years_of_experience: int | None = None
    technical_skills: list[str] | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    timezone: str | None = None
    past_locations: list[dict] | None = None
    status: str | None = None
    stage: str | None = None  # Pipeline stage: sourcing, screening, interview_hr, etc.
    sub_status: str | None = None  # Detailed status within stage
    is_active: bool | None = None
    tags: list[str] | None = None
    notes: str | None = None
    work_history: list[dict] | None = None
    lia_score: float | None = None
    lia_insights: dict | None = None


class CandidateStageUpdate(WeDoBaseModel):
    """Schema for updating candidate pipeline stage."""
    stage: str = Field(..., description="Pipeline stage: sourcing, screening, interview_hr, hired, rejected, etc.")
    sub_status: str | None = Field(None, description="Detailed status within the stage")
    job_vacancy_id: str | None = Field(None, description="Job vacancy ID for context")
    user_id: str | None = Field(None, description="User ID who made the stage change (for calibration feedback)")


class CandidateResponse(BaseModel):
    """Complete candidate response with all fields."""
    id: UUID
    name: str
    email: str | None = None
    secondary_email: str | None = None
    phone: str | None = None
    mobile_phone: str | None = None
    secondary_phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    avatar_url: str | None = None
    
    # Personal Information
    date_of_birth: str | None = None
    
    @field_validator('date_of_birth', mode='before')
    @classmethod
    def convert_date_to_string(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, date):
            return v.isoformat()
        return str(v) if v else None
    gender: str | None = None
    nationality: str | None = None
    marital_status: str | None = None
    cpf: str | None = None
    
    # Professional
    current_title: str | None = None
    current_company: str | None = None
    seniority_level: str | None = None
    years_of_experience: int | None = None
    self_introduction: str | None = None
    
    # Skills & Competencies
    technical_skills: list[str] | None = Field(default_factory=list)
    soft_skills: list[str] | None = Field(default_factory=list)
    languages: list[dict] | dict[str, str] | None = Field(default_factory=list)  # F8.B2: DB stores list[{language,level}]
    certifications: list[str] | None = Field(default_factory=list)
    interests: list[str] | None = Field(default_factory=list)
    
    # Location
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    address_street: str | None = None
    address_number: str | None = None
    address_district: str | None = None
    address_zip: str | None = None
    address_complement: str | None = None
    timezone: str | None = None
    past_locations: list[dict] | None = Field(default_factory=list)
    
    # Work Preferences
    is_remote: bool | None = False
    willing_to_relocate: bool | None = False
    mobility: bool | None = False
    work_model_preference: str | None = None
    contract_type_preference: str | None = None
    
    # Salary
    current_salary: float | None = None
    desired_salary_min: float | None = None
    desired_salary_max: float | None = None
    salary_currency: str | None = "BRL"
    salary_expectation_clt: float | None = None
    salary_expectation_pj: float | None = None
    salary_expectation_freelance: float | None = None
    
    # Source & Integration
    source: str
    ats_source_name: str | None = None
    ats_candidate_id: str | None = None
    pearch_profile_id: str | None = None
    
    # Documents
    resume_url: str | None = None
    resume_text: str | None = None
    cover_letter: str | None = None
    
    # Pearch / Global Search Data
    is_open_to_work: bool | None = None
    is_decision_maker: bool | None = None
    is_top_universities: bool | None = None
    is_hiring: bool | None = None
    headline: str | None = None
    expertise: list[str] | None = Field(default_factory=list)
    linkedin_followers_count: int | None = None
    linkedin_connections_count: int | None = None
    pearch_insights: dict | None = Field(default_factory=dict)
    outreach_message: str | None = None
    best_personal_email: str | None = None
    best_business_email: str | None = None
    personal_emails: list[str] | None = Field(default_factory=list)
    business_emails: list[str] | None = Field(default_factory=list)
    phone_types: dict | None = Field(default_factory=dict)
    estimated_age: int | None = None
    middle_name: str | None = None
    company_followers_count: int | None = None
    company_keywords: list[str] | None = Field(default_factory=list)
    
    # AI / LIA Insights
    lia_score: float | None = None
    lia_insights: dict | None = Field(default_factory=dict)
    skills_match_percentage: float | None = None
    
    # Status
    status: str = "new"
    is_active: bool = True
    is_blacklisted: bool | None = False  # F8.B2: tolerate None from DB
    blacklist_reason: str | None = None
    
    # Communication
    preferred_contact_method: str | None = "email"  # F8.B2
    best_time_to_contact: str | None = None
    communication_consent: bool | None = False  # F8.B2
    
    # Registration
    completed_register: bool | None = False
    accept_terms: bool | None = False
    
    # Work History (denormalized snapshot)
    work_history: list[dict] | None = Field(default_factory=list)
    
    # Flattened company info from most recent experience
    company_industries: list[str] | None = Field(default_factory=list, description="Industries from most recent experience")
    company_size: str | None = Field(None, description="Company size from most recent experience")
    
    # Additional
    tags: list[str] | None = Field(default_factory=list)
    notes: str | None = None
    additional_data: dict | None = Field(default_factory=dict)
    
    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_contacted_at: datetime | None = None
    last_activity_at: datetime | None = None
    
    class Config:
        from_attributes = True


class CandidateSearchFilters(BaseModel):
    """Filters for candidate search."""
    # Text search
    query: str | None = Field(None, description="Natural language or keyword search")
    
    # Skills & Experience
    required_skills: list[str] = Field(default_factory=list, description="Must have all these skills")
    preferred_skills: list[str] = Field(default_factory=list, description="Nice to have skills")
    seniority_levels: list[str] = Field(default_factory=list, description="junior, pleno, senior, etc")
    min_years_experience: int | None = None
    max_years_experience: int | None = None
    
    # Location
    locations: list[str] = Field(default_factory=list, description="Cities or countries")
    remote_only: bool = False
    
    # Salary
    min_salary: float | None = None
    max_salary: float | None = None
    
    # Status & Source
    statuses: list[str] = Field(default_factory=list, description="new, screening, interview, etc")
    sources: list[str] = Field(default_factory=list, description="ats, manual, pearch")
    is_active: bool | None = True
    
    # Tags
    tags: list[str] = Field(default_factory=list)
    
    # Pagination
    limit: int = Field(50, ge=1, le=100, description="Results per page")
    offset: int = Field(0, ge=0, description="Skip N results")


class CandidateSearchRequest(WeDoBaseModel):
    """Request for searching candidates."""
    filters: CandidateSearchFilters
    conversation_id: UUID | None = None  # Link to chat conversation
    use_global_search: bool = Field(False, description="If True, also search Pearch AI")


class CandidateSearchResponse(BaseModel):
    """Response from candidate search."""
    candidates: list[CandidateResponse]
    total_count: int
    local_count: int  # Results from proprietary DB
    global_count: int = 0  # Results from Pearch AI (if used)
    search_id: UUID | None = None  # ID of the search record
    credits_consumed: int = 0


class CandidateSearchAnalytics(BaseModel):
    """Analytics for candidate searches."""
    total_searches: int
    local_searches: int
    global_searches: int
    total_credits_consumed: int
    avg_results_per_search: float
    top_search_terms: list[dict[str, int]]  # [{"term": "Python", "count": 123}]
