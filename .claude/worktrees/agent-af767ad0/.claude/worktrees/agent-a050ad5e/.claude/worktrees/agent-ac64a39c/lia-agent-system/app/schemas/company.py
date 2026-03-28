"""
Pydantic schemas for Company Setup endpoints.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID


class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    manager_title: Optional[str] = None
    manager_phone: Optional[str] = None
    headcount: Optional[int] = 0
    cost_center: Optional[str] = None
    location: Optional[str] = None
    hiring_priority: Optional[str] = "normal"
    order: Optional[int] = 0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    manager_name: Optional[str] = None
    manager_email: Optional[str] = None
    manager_title: Optional[str] = None
    manager_phone: Optional[str] = None
    headcount: Optional[int] = None
    cost_center: Optional[str] = None
    location: Optional[str] = None
    hiring_priority: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


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
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    level: Optional[str] = "outros"
    order: Optional[int] = 0


class DepartmentMemberCreate(DepartmentMemberBase):
    department_id: Optional[UUID] = None  # Optional because it comes from URL path


class DepartmentMemberUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    level: Optional[str] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class DepartmentMemberResponse(DepartmentMemberBase):
    id: UUID
    department_id: UUID
    company_id: UUID
    linkedin_url: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BenefitBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    icon: Optional[str] = None
    value: Optional[float] = None
    value_type: Optional[str] = "monetary"
    value_details: Optional[str] = None
    percentage_value: Optional[float] = None
    applicable_to: Optional[List[str]] = []
    seniority_levels: Optional[List[str]] = []
    contract_types: Optional[List[str]] = []
    departments: Optional[List[str]] = []
    waiting_period_days: Optional[int] = 0
    is_mandatory: Optional[bool] = False
    is_highlighted: Optional[bool] = False
    is_discount: Optional[bool] = False
    provider: Optional[str] = None
    order: Optional[int] = 0


class BenefitCreate(BenefitBase):
    pass


class BenefitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    value: Optional[float] = None
    value_type: Optional[str] = None
    value_details: Optional[str] = None
    percentage_value: Optional[float] = None
    applicable_to: Optional[List[str]] = None
    seniority_levels: Optional[List[str]] = None
    contract_types: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    waiting_period_days: Optional[int] = None
    is_mandatory: Optional[bool] = None
    is_highlighted: Optional[bool] = None
    is_discount: Optional[bool] = None
    is_active: Optional[bool] = None
    provider: Optional[str] = None
    order: Optional[int] = None


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
    description: Optional[str] = None
    category: Optional[str] = "value"
    icon: Optional[str] = None
    color: Optional[str] = None
    behavioral_indicators: Optional[List[str]] = []
    interview_questions: Optional[List[str]] = []
    weight: Optional[float] = 1.0
    order: Optional[int] = 0


class CultureValueCreate(CultureValueBase):
    pass


class CultureValueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    behavioral_indicators: Optional[List[str]] = None
    interview_questions: Optional[List[str]] = None
    weight: Optional[float] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class CultureValueResponse(CultureValueBase):
    id: UUID
    company_id: UUID
    is_active: bool
    ai_generated: bool
    source: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CompanyProfileBase(BaseModel):
    name: str
    trading_name: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    cnpj: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    headquarters_country: Optional[str] = "Brasil"
    address: Optional[str] = None
    main_phone: Optional[str] = None
    hr_phone: Optional[str] = None
    main_email: Optional[str] = None
    hr_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    glassdoor_url: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    name: Optional[str] = None
    trading_name: Optional[str] = None
    website: Optional[str] = None
    logo_url: Optional[str] = None
    cnpj: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    company_size: Optional[str] = None
    founded_year: Optional[int] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    headquarters_country: Optional[str] = None
    address: Optional[str] = None
    main_phone: Optional[str] = None
    hr_phone: Optional[str] = None
    main_email: Optional[str] = None
    hr_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    glassdoor_url: Optional[str] = None
    employee_count: Optional[int] = None
    revenue_range: Optional[str] = None
    is_active: Optional[bool] = None
    additional_data: Optional[Dict[str, Any]] = None


class CompanyProfileResponse(CompanyProfileBase):
    id: UUID
    is_active: bool
    is_default: bool
    culture_analyzed: Optional[bool] = False
    culture_analysis_date: Optional[datetime] = None
    culture_insights: Optional[Dict[str, Any]] = None
    ats_history_analyzed: Optional[bool] = False
    ats_analysis_date: Optional[datetime] = None
    ats_insights: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    @field_validator('culture_analyzed', 'ats_history_analyzed', mode='before')
    @classmethod
    def convert_none_to_false(cls, v):
        return v if v is not None else False
    
    class Config:
        from_attributes = True


class CompanyProfileWithRelations(CompanyProfileResponse):
    departments: List[DepartmentResponse] = []
    benefits: List[BenefitResponse] = []
    culture_values: List[CultureValueResponse] = []


class IdealProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    role_type: Optional[str] = None
    seniority_level: Optional[str] = None
    technical_requirements: Optional[Dict[str, Any]] = {}
    behavioral_requirements: Optional[Dict[str, Any]] = {}
    experience_requirements: Optional[Dict[str, Any]] = {}
    education_requirements: Optional[Dict[str, Any]] = {}
    big_five_ideal: Optional[Dict[str, Any]] = {}
    evaluation_weights: Optional[Dict[str, Any]] = {}
    mandatory_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    languages: Optional[Dict[str, str]] = {}
    salary_range_min: Optional[float] = None
    salary_range_max: Optional[float] = None
    culture_fit_criteria: Optional[Dict[str, Any]] = {}


class IdealProfileCreate(IdealProfileBase):
    pass


class IdealProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    role_type: Optional[str] = None
    seniority_level: Optional[str] = None
    technical_requirements: Optional[Dict[str, Any]] = None
    behavioral_requirements: Optional[Dict[str, Any]] = None
    experience_requirements: Optional[Dict[str, Any]] = None
    education_requirements: Optional[Dict[str, Any]] = None
    big_five_ideal: Optional[Dict[str, Any]] = None
    evaluation_weights: Optional[Dict[str, Any]] = None
    mandatory_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    languages: Optional[Dict[str, str]] = None
    salary_range_min: Optional[float] = None
    salary_range_max: Optional[float] = None
    culture_fit_criteria: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    validated: Optional[bool] = None
    validated_by: Optional[str] = None


class IdealProfileResponse(IdealProfileBase):
    id: UUID
    company_id: UUID
    ai_generated: bool
    ai_analysis_date: Optional[datetime]
    ai_confidence: Optional[float]
    validated: bool
    validated_by: Optional[str]
    validated_at: Optional[datetime]
    is_active: bool
    is_template: bool
    usage_count: int
    success_rate: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class BigFiveQuestionBase(BaseModel):
    text: str
    text_en: Optional[str] = None
    trait: str
    facet: Optional[str] = None
    polarity: Optional[str] = "positive"
    scale_min: Optional[int] = 1
    scale_max: Optional[int] = 5
    scale_labels: Optional[Dict[str, str]] = {}
    category: Optional[str] = "general"
    role_specific: Optional[List[str]] = []
    weight: Optional[float] = 1.0
    is_core: Optional[bool] = False
    order: Optional[int] = 0


class BigFiveQuestionCreate(BigFiveQuestionBase):
    pass


class BigFiveQuestionUpdate(BaseModel):
    text: Optional[str] = None
    text_en: Optional[str] = None
    trait: Optional[str] = None
    facet: Optional[str] = None
    polarity: Optional[str] = None
    scale_min: Optional[int] = None
    scale_max: Optional[int] = None
    scale_labels: Optional[Dict[str, str]] = None
    category: Optional[str] = None
    role_specific: Optional[List[str]] = None
    weight: Optional[float] = None
    is_core: Optional[bool] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None


class BigFiveQuestionResponse(BigFiveQuestionBase):
    id: UUID
    is_active: bool
    ai_generated: bool
    validation_stats: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BigFiveRoleProfileBase(BaseModel):
    name: str
    description: Optional[str] = None
    role_category: Optional[str] = None
    seniority_level: Optional[str] = None
    openness_min: Optional[float] = 1.0
    openness_max: Optional[float] = 5.0
    openness_ideal: Optional[float] = 3.0
    openness_weight: Optional[float] = 1.0
    conscientiousness_min: Optional[float] = 1.0
    conscientiousness_max: Optional[float] = 5.0
    conscientiousness_ideal: Optional[float] = 3.0
    conscientiousness_weight: Optional[float] = 1.0
    extroversion_min: Optional[float] = 1.0
    extroversion_max: Optional[float] = 5.0
    extroversion_ideal: Optional[float] = 3.0
    extroversion_weight: Optional[float] = 1.0
    agreeableness_min: Optional[float] = 1.0
    agreeableness_max: Optional[float] = 5.0
    agreeableness_ideal: Optional[float] = 3.0
    agreeableness_weight: Optional[float] = 1.0
    neuroticism_min: Optional[float] = 1.0
    neuroticism_max: Optional[float] = 5.0
    neuroticism_ideal: Optional[float] = 3.0
    neuroticism_weight: Optional[float] = 1.0
    facet_requirements: Optional[Dict[str, Any]] = {}


class BigFiveRoleProfileCreate(BigFiveRoleProfileBase):
    company_id: Optional[UUID] = None


class BigFiveRoleProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    role_category: Optional[str] = None
    seniority_level: Optional[str] = None
    openness_min: Optional[float] = None
    openness_max: Optional[float] = None
    openness_ideal: Optional[float] = None
    openness_weight: Optional[float] = None
    conscientiousness_min: Optional[float] = None
    conscientiousness_max: Optional[float] = None
    conscientiousness_ideal: Optional[float] = None
    conscientiousness_weight: Optional[float] = None
    extroversion_min: Optional[float] = None
    extroversion_max: Optional[float] = None
    extroversion_ideal: Optional[float] = None
    extroversion_weight: Optional[float] = None
    agreeableness_min: Optional[float] = None
    agreeableness_max: Optional[float] = None
    agreeableness_ideal: Optional[float] = None
    agreeableness_weight: Optional[float] = None
    neuroticism_min: Optional[float] = None
    neuroticism_max: Optional[float] = None
    neuroticism_ideal: Optional[float] = None
    neuroticism_weight: Optional[float] = None
    facet_requirements: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class BigFiveRoleProfileResponse(BigFiveRoleProfileBase):
    id: UUID
    company_id: Optional[UUID]
    is_active: bool
    is_template: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class TechnicalQuestionBase(BaseModel):
    title: str
    description: Optional[str] = None
    question_type: str
    difficulty: Optional[str] = "medium"
    estimated_time: Optional[int] = 5
    area: str
    tags: Optional[List[str]] = []
    options: Optional[List[Dict[str, Any]]] = []
    correct_answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    code_solution: Optional[str] = None
    code_language: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = []
    rubric: Optional[Dict[str, Any]] = {}
    ai_correction_enabled: Optional[bool] = True


class TechnicalQuestionCreate(TechnicalQuestionBase):
    pass


class TechnicalQuestionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    question_type: Optional[str] = None
    difficulty: Optional[str] = None
    estimated_time: Optional[int] = None
    area: Optional[str] = None
    tags: Optional[List[str]] = None
    options: Optional[List[Dict[str, Any]]] = None
    correct_answer: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    code_template: Optional[str] = None
    code_solution: Optional[str] = None
    code_language: Optional[str] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    rubric: Optional[Dict[str, Any]] = None
    ai_correction_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class TechnicalQuestionResponse(TechnicalQuestionBase):
    id: UUID
    ai_generated: bool
    is_active: bool
    is_public: bool
    usage_count: int
    avg_score: Optional[float]
    avg_time: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class TechnicalTestTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    area: Optional[str] = None
    role_type: Optional[str] = None
    seniority_level: Optional[str] = None
    question_ids: Optional[List[UUID]] = []
    question_config: Optional[Dict[str, Any]] = {}
    total_time: Optional[int] = 60
    passing_score: Optional[float] = 70.0
    instructions: Optional[str] = None
    instructions_en: Optional[str] = None
    randomize_questions: Optional[bool] = True
    randomize_options: Optional[bool] = True
    show_score: Optional[bool] = True
    proctoring_enabled: Optional[bool] = False
    webcam_required: Optional[bool] = False
    ai_correction_enabled: Optional[bool] = True
    ai_correction_prompt: Optional[str] = None


class TechnicalTestTemplateCreate(TechnicalTestTemplateBase):
    company_id: Optional[UUID] = None


class TechnicalTestTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    area: Optional[str] = None
    role_type: Optional[str] = None
    seniority_level: Optional[str] = None
    question_ids: Optional[List[UUID]] = None
    question_config: Optional[Dict[str, Any]] = None
    total_time: Optional[int] = None
    passing_score: Optional[float] = None
    instructions: Optional[str] = None
    instructions_en: Optional[str] = None
    randomize_questions: Optional[bool] = None
    randomize_options: Optional[bool] = None
    show_score: Optional[bool] = None
    proctoring_enabled: Optional[bool] = None
    webcam_required: Optional[bool] = None
    ai_correction_enabled: Optional[bool] = None
    ai_correction_prompt: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class TechnicalTestTemplateResponse(TechnicalTestTemplateBase):
    id: UUID
    company_id: Optional[UUID]
    is_active: bool
    is_public: bool
    usage_count: int
    avg_score: Optional[float]
    completion_rate: Optional[float]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


class CultureAnalysisRequest(BaseModel):
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    glassdoor_url: Optional[str] = None
    additional_context: Optional[str] = None


class CultureAnalysisResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    suggested_values: List[CultureValueBase]
    confidence: float
    sources_analyzed: List[str]


class IdealProfileGenerateRequest(BaseModel):
    role_type: str
    seniority_level: str
    department_id: Optional[UUID] = None
    job_description: Optional[str] = None
    additional_requirements: Optional[str] = None


class IdealProfileGenerateResponse(BaseModel):
    success: bool
    profile: IdealProfileResponse
    confidence: float
    reasoning: str


class BigFiveGenerateRequest(BaseModel):
    trait: str
    count: Optional[int] = 5
    role_specific: Optional[List[str]] = None


class BigFiveGenerateResponse(BaseModel):
    success: bool
    questions: List[BigFiveQuestionBase]
    trait: str


class TechnicalQuestionsGenerateRequest(BaseModel):
    area: str
    difficulty: str
    question_type: str
    count: Optional[int] = 5
    context: Optional[str] = None


class TechnicalQuestionsGenerateResponse(BaseModel):
    success: bool
    questions: List[TechnicalQuestionBase]
    area: str
    difficulty: str


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
    default_limit: Optional[int] = None
    search_type: Optional[str] = None
    show_emails: Optional[bool] = None
    show_phone_numbers: Optional[bool] = None
    high_freshness: Optional[bool] = None
    auto_expand_global: Optional[bool] = None
    confirm_before_search: Optional[bool] = None
    global_search_enabled: Optional[bool] = None


class GlobalSearchSettingsResponse(GlobalSearchSettingsBase):
    id: UUID
    company_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ApproverBase(BaseModel):
    user_name: str
    email: str
    role: Optional[str] = None
    level: int = 1
    user_id: Optional[UUID] = None


class ApproverCreate(ApproverBase):
    pass


class ApproverUpdate(BaseModel):
    user_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    level: Optional[int] = None
    user_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ApproverResponse(ApproverBase):
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
