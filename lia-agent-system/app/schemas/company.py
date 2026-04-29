"""
Pydantic schemas for Company Setup endpoints.
"""
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator


class DepartmentBase(BaseModel):
    name: str
    code: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    manager_name: str | None = None
    manager_email: str | None = None
    manager_title: str | None = None
    manager_phone: str | None = None
    headcount: int | None = 0
    cost_center: str | None = None
    location: str | None = None
    hiring_priority: str | None = "normal"
    order: int | None = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    parent_id: UUID | None = None
    manager_name: str | None = None
    manager_email: str | None = None
    manager_title: str | None = None
    manager_phone: str | None = None
    headcount: int | None = None
    cost_center: str | None = None
    location: str | None = None
    hiring_priority: str | None = None
    is_active: bool | None = None
    order: int | None = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DepartmentMemberBase(BaseModel):
    name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    avatar_url: str | None = None
    level: str | None = "outros"
    order: int | None = 0


class DepartmentMemberCreate(DepartmentMemberBase):
    department_id: UUID | None = None  # Optional because it comes from URL path


class DepartmentMemberUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    avatar_url: str | None = None
    level: str | None = None
    is_active: bool | None = None
    order: int | None = None


class DepartmentMemberResponse(DepartmentMemberBase):
    id: UUID
    department_id: UUID
    company_id: UUID
    linkedin_url: str | None = None
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BenefitBase(BaseModel):
    name: str
    description: str | None = None
    category: str
    icon: str | None = None
    value: float | None = None
    value_type: str | None = "monetary"
    value_details: str | None = None
    percentage_value: float | None = None
    applicable_to: list[str] | None = []
    seniority_levels: list[str] | None = []
    contract_types: list[str] | None = []
    departments: list[str] | None = []
    waiting_period_days: int | None = 0
    is_mandatory: bool | None = False
    is_highlighted: bool | None = False
    is_discount: bool | None = False
    provider: str | None = None
    order: int | None = 0


class BenefitCreate(BenefitBase):
    pass


class BenefitUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    value: float | None = None
    value_type: str | None = None
    value_details: str | None = None
    percentage_value: float | None = None
    applicable_to: list[str] | None = None
    seniority_levels: list[str] | None = None
    contract_types: list[str] | None = None
    departments: list[str] | None = None
    waiting_period_days: int | None = None
    is_mandatory: bool | None = None
    is_highlighted: bool | None = None
    is_discount: bool | None = None
    is_active: bool | None = None
    provider: str | None = None
    order: int | None = None


class BenefitResponse(BenefitBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CultureValueBase(BaseModel):
    name: str
    description: str | None = None
    category: str | None = "value"
    icon: str | None = None
    color: str | None = None
    behavioral_indicators: list[str] | None = []
    interview_questions: list[str] | None = []
    weight: float | None = 1.0
    order: int | None = 0


class CultureValueCreate(CultureValueBase):
    pass


class CultureValueUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    color: str | None = None
    behavioral_indicators: list[str] | None = None
    interview_questions: list[str] | None = None
    weight: float | None = None
    is_active: bool | None = None
    order: int | None = None


class CultureValueResponse(CultureValueBase):
    id: UUID
    company_id: UUID
    is_active: bool
    ai_generated: bool
    source: str | None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanyProfileBase(BaseModel):
    name: str
    trading_name: str | None = None
    website: str | None = None
    logo_url: str | None = None
    cnpj: str | None = None
    industry: str | None = None
    sector: str | None = None
    company_size: str | None = None
    founded_year: int | None = None
    description: str | None = None
    short_description: str | None = None
    headquarters_city: str | None = None
    headquarters_state: str | None = None
    headquarters_country: str | None = "Brasil"
    address: str | None = None
    main_phone: str | None = None
    hr_phone: str | None = None
    main_email: str | None = None
    hr_email: str | None = None
    linkedin_url: str | None = None
    glassdoor_url: str | None = None
    employee_count: int | None = None
    revenue_range: str | None = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: str | None = None
    trading_name: str | None = None
    website: str | None = None
    logo_url: str | None = None
    cnpj: str | None = None
    industry: str | None = None
    sector: str | None = None
    company_size: str | None = None
    founded_year: int | None = None
    description: str | None = None
    short_description: str | None = None
    headquarters_city: str | None = None
    headquarters_state: str | None = None
    headquarters_country: str | None = None
    address: str | None = None
    main_phone: str | None = None
    hr_phone: str | None = None
    main_email: str | None = None
    hr_email: str | None = None
    linkedin_url: str | None = None
    glassdoor_url: str | None = None
    employee_count: int | None = None
    revenue_range: str | None = None
    is_active: bool | None = None
    additional_data: dict[str, Any] | None = None


class CompanyProfileResponse(CompanyProfileBase):
    id: UUID
    is_active: bool
    is_default: bool
    culture_analyzed: bool | None = False
    culture_analysis_date: datetime | None = None
    culture_insights: dict[str, Any] | None = None
    ats_history_analyzed: bool | None = False
    ats_analysis_date: datetime | None = None
    ats_insights: dict[str, Any] | None = None
    additional_data: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    
    @field_validator('culture_analyzed', 'ats_history_analyzed', mode='before')
    @classmethod
    def convert_none_to_false(cls, v):
        return v if v is not None else False
    
    class Config:
        from_attributes = True


class CompanyProfileWithRelations(CompanyProfileResponse):
    departments: list[DepartmentResponse] = []
    benefits: list[BenefitResponse] = []
    culture_values: list[CultureValueResponse] = []


class IdealProfileBase(BaseModel):
    name: str
    description: str | None = None
    department_id: UUID | None = None
    role_type: str | None = None
    seniority_level: str | None = None
    technical_requirements: dict[str, Any] | None = {}
    behavioral_requirements: dict[str, Any] | None = {}
    experience_requirements: dict[str, Any] | None = {}
    education_requirements: dict[str, Any] | None = {}
    big_five_ideal: dict[str, Any] | None = {}
    evaluation_weights: dict[str, Any] | None = {}
    mandatory_skills: list[str] | None = []
    preferred_skills: list[str] | None = []
    languages: dict[str, str] | None = {}
    salary_range_min: float | None = None
    salary_range_max: float | None = None
    culture_fit_criteria: dict[str, Any] | None = {}


class IdealProfileCreate(IdealProfileBase):
    pass


class IdealProfileUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    department_id: UUID | None = None
    role_type: str | None = None
    seniority_level: str | None = None
    technical_requirements: dict[str, Any] | None = None
    behavioral_requirements: dict[str, Any] | None = None
    experience_requirements: dict[str, Any] | None = None
    education_requirements: dict[str, Any] | None = None
    big_five_ideal: dict[str, Any] | None = None
    evaluation_weights: dict[str, Any] | None = None
    mandatory_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    languages: dict[str, str] | None = None
    salary_range_min: float | None = None
    salary_range_max: float | None = None
    culture_fit_criteria: dict[str, Any] | None = None
    is_active: bool | None = None
    validated: bool | None = None
    validated_by: str | None = None


class IdealProfileResponse(IdealProfileBase):
    id: UUID
    company_id: UUID
    ai_generated: bool
    ai_analysis_date: datetime | None
    ai_confidence: float | None
    validated: bool
    validated_by: str | None
    validated_at: datetime | None
    is_active: bool
    is_template: bool
    usage_count: int
    success_rate: float | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True



class CultureAnalysisRequest(BaseModel):
    website_url: str | None = None
    linkedin_url: str | None = None
    glassdoor_url: str | None = None
    additional_context: str | None = None


class CultureAnalysisResponse(BaseModel):
    success: bool
    analysis: dict[str, Any]
    suggested_values: list[CultureValueBase]
    confidence: float
    sources_analyzed: list[str]


class IdealProfileGenerateRequest(BaseModel):
    role_type: str
    seniority_level: str
    department_id: UUID | None = None
    job_description: str | None = None
    additional_requirements: str | None = None


class IdealProfileGenerateResponse(BaseModel):
    success: bool
    profile: IdealProfileResponse
    confidence: float
    reasoning: str


class GlobalSearchSettingsBase(BaseModel):
    default_limit: int = 50
    search_type: str = 'fast'
    show_emails: bool = False
    show_phone_numbers: bool = False
    high_freshness: bool = False
    auto_expand_global: bool = False
    confirm_before_search: bool = True
    global_search_enabled: bool = True


class GlobalSearchSettingsUpdate(BaseModel):
    default_limit: int | None = None
    search_type: str | None = None
    show_emails: bool | None = None
    show_phone_numbers: bool | None = None
    high_freshness: bool | None = None
    auto_expand_global: bool | None = None
    confirm_before_search: bool | None = None
    global_search_enabled: bool | None = None


class GlobalSearchSettingsResponse(GlobalSearchSettingsBase):
    id: UUID
    company_id: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApproverBase(BaseModel):
    user_name: str
    email: str
    role: str | None = None
    level: int = 1
    user_id: UUID | None = None


class ApproverCreate(ApproverBase):
    pass


class ApproverUpdate(BaseModel):
    user_name: str | None = None
    email: str | None = None
    role: str | None = None
    level: int | None = None
    user_id: UUID | None = None
    is_active: bool | None = None


class ApproverResponse(ApproverBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Tenant / Onboarding / Enrichment schemas
# (extracted from app/api/v1/company.py to keep route module handler-only)
# ---------------------------------------------------------------------------

class TenantResolutionResponse(BaseModel):
    client_account_id: str | None = None
    company_profile_id: str | None = None
    company_name: str | None = None
    plan_id: str | None = None
    status: str | None = None


class CompanyEnrichRequest(BaseModel):
    linkedin_url: str | None = None
    glassdoor_company_name: str | None = None


class CompanyEnrichResponse(BaseModel):
    success: bool
    linkedin_data: dict[str, Any] = {}
    glassdoor_data: dict[str, Any] = {}
    enriched_culture: dict[str, Any] = {}
    errors: list[str] = []


class AutoEnrichResponse(BaseModel):
    success: bool
    fields_updated: list[str] = []
    apify_data: dict[str, Any] = {}
    inferred_data: dict[str, Any] = {}
    errors: list[str] = []


class OnboardingCultureProfile(BaseModel):
    mission: str | None = None
    vision: str | None = None
    values: list[str] | None = None
    evp_bullets: list[str] | None = None
    openness_score: int | None = None
    conscientiousness_score: int | None = None
    extraversion_score: int | None = None
    agreeableness_score: int | None = None
    stability_score: int | None = None


class OnboardingData(BaseModel):
    company_id: str | None = None
    company_name: str
    trade_name: str | None = None
    cnpj: str | None = None
    address: str | None = None
    work_model: str | None = None
    logo_url: str | None = None
    sector: str | None = None
    employee_count: str | None = None
    website: str | None = None
    linkedin_url: str | None = None
    hiring_volume: int | None = None
    job_types: list[str] | None = None
    current_ats: str | None = None
    main_challenges: list[str] | None = None
    main_priority: str | None = None
    platform_expectations: str | None = None
    communication_channels: list[str] | None = None
    allow_lia_contact: bool = True
    additional_notes: str | None = None
    responsible_name: str | None = None
    responsible_email: str | None = None
    responsible_phone: str | None = None
    responsible_position: str | None = None
    preferred_contact_time: str | None = None
    culture_profile: OnboardingCultureProfile | None = None


class EVPAnalysisResponse(BaseModel):
    success: bool
    evp_analysis: dict[str, Any] | None = None
    error: str | None = None


class ManagerResponse(BaseModel):
    id: str
    name: str
    email: str | None = None
    role: str | None = None
    department_id: str | None = None
    department_name: str | None = None


class ManagerSearchResponse(BaseModel):
    managers: list[ManagerResponse]
    total_count: int


class BenefitsSummaryResponse(BaseModel):
    total_count: int
    active_count: int
    highlighted_count: int
    categories: dict
    formatted_text: str
    benefits: list[dict]


class DepartmentImportRow(BaseModel):
    name: str
    description: str | None = None
    manager: str | None = None
    cost_center: str | None = None
    row_number: int
    is_valid: bool = True
    errors: list[str] = []


class DepartmentImportResponse(BaseModel):
    success: bool
    imported_count: int
    error_count: int
    errors: list[dict[str, Any]]
    items: list[dict[str, Any]]
    ai_suggestions: dict[str, Any] | None = None


class CompanyUserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool
    active_jobs_count: int
    performance_score: int


class CompanyUsersListResponse(BaseModel):
    users: list[CompanyUserResponse]
    total: int


class CatalogStatusResponse(BaseModel):
    company_id: str
    maturity_score: int
    maturity_level: str
    maturity_factors: list[str]
    smart_start_enabled: bool
    required_fields_for_wizard: list[str]
    available_data_summary: list[str]
    counts: dict[str, int]
    recommendations: list[str]


class SmartWizardGreetingResponse(BaseModel):
    greeting_message: str
    catalog_status: CatalogStatusResponse
    prefill_data: dict[str, Any]
