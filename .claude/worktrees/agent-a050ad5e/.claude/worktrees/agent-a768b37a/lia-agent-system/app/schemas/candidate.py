"""
Pydantic schemas for candidate API.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr, field_validator
from uuid import UUID


class CandidateBase(BaseModel):
    """Base candidate schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, description="Email do candidato (opcional)")
    phone: Optional[str] = Field(None, max_length=50)
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    seniority_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    languages: Dict[str, str] = Field(default_factory=dict)
    certifications: List[str] = Field(default_factory=list)
    
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    is_remote: bool = False
    willing_to_relocate: bool = False
    
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    salary_currency: str = "BRL"
    work_model_preference: Optional[str] = None
    contract_type_preference: Optional[str] = None
    
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CandidateCreate(CandidateBase):
    """Schema for creating a new candidate."""
    source: str = Field(..., description="Source: 'ats', 'manual', 'pearch', 'linkedin'")
    ats_source_name: Optional[str] = None
    ats_candidate_id: Optional[str] = None
    pearch_profile_id: Optional[str] = None
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    work_history: Optional[List[Dict]] = Field(default_factory=list, description="List of work experiences with company metadata")
    additional_data: Dict = Field(default_factory=dict)
    auto_enrich: bool = Field(default=False, description="Auto-enrich from LinkedIn when linkedin_url is provided")


class CandidateUpdate(BaseModel):
    """Schema for updating a candidate (all fields optional)."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    seniority_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    technical_skills: Optional[List[str]] = None
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    timezone: Optional[str] = None
    past_locations: Optional[List[Dict]] = None
    status: Optional[str] = None
    stage: Optional[str] = None  # Pipeline stage: sourcing, screening, interview_hr, etc.
    sub_status: Optional[str] = None  # Detailed status within stage
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    work_history: Optional[List[Dict]] = None
    lia_score: Optional[float] = None
    lia_insights: Optional[Dict] = None


class CandidateStageUpdate(BaseModel):
    """Schema for updating candidate pipeline stage."""
    stage: str = Field(..., description="Pipeline stage: sourcing, screening, interview_hr, hired, rejected, etc.")
    sub_status: Optional[str] = Field(None, description="Detailed status within the stage")
    job_vacancy_id: Optional[str] = Field(None, description="Job vacancy ID for context")
    user_id: Optional[str] = Field(None, description="User ID who made the stage change (for calibration feedback)")


class CandidateResponse(BaseModel):
    """Complete candidate response with all fields."""
    id: UUID
    name: str
    email: Optional[str] = None
    secondary_email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    secondary_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Personal Information
    date_of_birth: Optional[str] = None
    
    @field_validator('date_of_birth', mode='before')
    @classmethod
    def convert_date_to_string(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, date):
            return v.isoformat()
        return str(v) if v else None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    cpf: Optional[str] = None
    
    # Professional
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    seniority_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    self_introduction: Optional[str] = None
    
    # Skills & Competencies
    technical_skills: Optional[List[str]] = Field(default_factory=list)
    soft_skills: Optional[List[str]] = Field(default_factory=list)
    languages: Optional[Dict[str, str]] = Field(default_factory=dict)
    certifications: Optional[List[str]] = Field(default_factory=list)
    interests: Optional[List[str]] = Field(default_factory=list)
    
    # Location
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    address_street: Optional[str] = None
    address_number: Optional[str] = None
    address_district: Optional[str] = None
    address_zip: Optional[str] = None
    address_complement: Optional[str] = None
    timezone: Optional[str] = None
    past_locations: Optional[List[Dict]] = Field(default_factory=list)
    
    # Work Preferences
    is_remote: Optional[bool] = False
    willing_to_relocate: Optional[bool] = False
    mobility: Optional[bool] = False
    work_model_preference: Optional[str] = None
    contract_type_preference: Optional[str] = None
    
    # Salary
    current_salary: Optional[float] = None
    desired_salary_min: Optional[float] = None
    desired_salary_max: Optional[float] = None
    salary_currency: Optional[str] = "BRL"
    salary_expectation_clt: Optional[float] = None
    salary_expectation_pj: Optional[float] = None
    salary_expectation_freelance: Optional[float] = None
    
    # Source & Integration
    source: str
    ats_source_name: Optional[str] = None
    ats_candidate_id: Optional[str] = None
    pearch_profile_id: Optional[str] = None
    
    # Documents
    resume_url: Optional[str] = None
    resume_text: Optional[str] = None
    cover_letter: Optional[str] = None
    
    # Pearch / Global Search Data
    is_open_to_work: Optional[bool] = None
    is_decision_maker: Optional[bool] = None
    is_top_universities: Optional[bool] = None
    is_hiring: Optional[bool] = None
    headline: Optional[str] = None
    expertise: Optional[List[str]] = Field(default_factory=list)
    linkedin_followers_count: Optional[int] = None
    linkedin_connections_count: Optional[int] = None
    pearch_insights: Optional[Dict] = Field(default_factory=dict)
    outreach_message: Optional[str] = None
    best_personal_email: Optional[str] = None
    best_business_email: Optional[str] = None
    personal_emails: Optional[List[str]] = Field(default_factory=list)
    business_emails: Optional[List[str]] = Field(default_factory=list)
    phone_types: Optional[Dict] = Field(default_factory=dict)
    estimated_age: Optional[int] = None
    middle_name: Optional[str] = None
    company_followers_count: Optional[int] = None
    company_keywords: Optional[List[str]] = Field(default_factory=list)
    
    # AI / LIA Insights
    lia_score: Optional[float] = None
    lia_insights: Optional[Dict] = Field(default_factory=dict)
    skills_match_percentage: Optional[float] = None
    
    # Status
    status: str = "new"
    is_active: bool = True
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    
    # Communication
    preferred_contact_method: str = "email"
    best_time_to_contact: Optional[str] = None
    communication_consent: bool = False
    
    # Registration
    completed_register: Optional[bool] = False
    accept_terms: Optional[bool] = False
    
    # Work History (denormalized snapshot)
    work_history: Optional[List[Dict]] = Field(default_factory=list)
    
    # Flattened company info from most recent experience
    company_industries: Optional[List[str]] = Field(default_factory=list, description="Industries from most recent experience")
    company_size: Optional[str] = Field(None, description="Company size from most recent experience")
    
    # Additional
    tags: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None
    additional_data: Optional[Dict] = Field(default_factory=dict)
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_contacted_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CandidateSearchFilters(BaseModel):
    """Filters for candidate search."""
    # Text search
    query: Optional[str] = Field(None, description="Natural language or keyword search")
    
    # Skills & Experience
    required_skills: List[str] = Field(default_factory=list, description="Must have all these skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice to have skills")
    seniority_levels: List[str] = Field(default_factory=list, description="junior, pleno, senior, etc")
    min_years_experience: Optional[int] = None
    max_years_experience: Optional[int] = None
    
    # Location
    locations: List[str] = Field(default_factory=list, description="Cities or countries")
    remote_only: bool = False
    
    # Salary
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    
    # Status & Source
    statuses: List[str] = Field(default_factory=list, description="new, screening, interview, etc")
    sources: List[str] = Field(default_factory=list, description="ats, manual, pearch")
    is_active: Optional[bool] = True
    
    # Tags
    tags: List[str] = Field(default_factory=list)
    
    # Pagination
    limit: int = Field(50, ge=1, le=100, description="Results per page")
    offset: int = Field(0, ge=0, description="Skip N results")


class CandidateSearchRequest(BaseModel):
    """Request for searching candidates."""
    filters: CandidateSearchFilters
    conversation_id: Optional[UUID] = None  # Link to chat conversation
    use_global_search: bool = Field(False, description="If True, also search Pearch AI")


class CandidateSearchResponse(BaseModel):
    """Response from candidate search."""
    candidates: List[CandidateResponse]
    total_count: int
    local_count: int  # Results from proprietary DB
    global_count: int = 0  # Results from Pearch AI (if used)
    search_id: Optional[UUID] = None  # ID of the search record
    credits_consumed: int = 0


class CandidateSearchAnalytics(BaseModel):
    """Analytics for candidate searches."""
    total_searches: int
    local_searches: int
    global_searches: int
    total_credits_consumed: int
    avg_results_per_search: float
    top_search_terms: List[Dict[str, int]]  # [{"term": "Python", "count": 123}]
