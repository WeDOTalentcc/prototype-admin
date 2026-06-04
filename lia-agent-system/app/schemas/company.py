"""
Pydantic schemas for Company Setup endpoints.
"""
import re
from decimal import Decimal
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from app.shared.types import WeDoBaseModel


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


class DepartmentUpdate(WeDoBaseModel):
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


class DepartmentMemberUpdate(WeDoBaseModel):
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


class BenefitUpdate(WeDoBaseModel):
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


class CultureValueUpdate(WeDoBaseModel):
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



def _validate_cnpj_mod11(cnpj: str) -> bool:
    """Valida CNPJ pelo algoritmo mod11. cnpj deve ter exatamente 14 digitos."""
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj[i]) * weights1[i] for i in range(12))
    remainder = total % 11
    digit1 = 0 if remainder < 2 else 11 - remainder
    if int(cnpj[12]) != digit1:
        return False
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(cnpj[i]) * weights2[i] for i in range(13))
    remainder = total % 11
    digit2 = 0 if remainder < 2 else 11 - remainder
    return int(cnpj[13]) == digit2


class CnpjMixin:
    """Mixin que fornece validacao mod11 de CNPJ para schemas Pydantic."""

    @field_validator("cnpj", mode="before")
    @classmethod
    def validate_cnpj(cls, v):
        if v is None:
            return None
        # Remove formatacao: pontos, barras, hifens
        digits = re.sub(r"[.\-/]", "", str(v))
        if len(digits) != 14:
            raise ValueError(
                f"CNPJ deve ter 14 digitos numericos (recebido: {len(digits)})"
            )
        if not digits.isdigit():
            raise ValueError("CNPJ deve conter apenas digitos numericos")
        if len(set(digits)) == 1:
            raise ValueError("CNPJ invalido: sequencia de digitos repetidos")
        if not _validate_cnpj_mod11(digits):
            raise ValueError("CNPJ invalido: digitos verificadores incorretos (mod11)")
        return digits


class CompanyProfileBase(CnpjMixin, BaseModel):
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
    main_email: EmailStr | None = None
    hr_email: EmailStr | None = None
    linkedin_url: str | None = None
    glassdoor_url: str | None = None
    employee_count: int | None = None
    revenue_range: str | None = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(CnpjMixin, WeDoBaseModel):
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
    main_email: EmailStr | None = None
    hr_email: EmailStr | None = None
    linkedin_url: str | None = None
    glassdoor_url: str | None = None
    employee_count: int | None = None
    revenue_range: str | None = None
    is_active: bool | None = None
    additional_data: dict[str, Any] | None = None


class CompanyProfileResponse(CompanyProfileBase):
    id: UUID
    is_active: bool
    # PR-B (Task #1016) — default defensivo `False` para tolerar rows
    # legados em que `company_profiles.is_default` ficou NULL antes da
    # migration `128_company_profile_is_default_not_null`. NÃO virar
    # `Optional[bool]`: o contrato do domínio diz "todo profile sabe se
    # é o default ou não". O default só protege a leitura enquanto o
    # backfill da migration não roda em todos os ambientes.
    is_default: bool = False
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
    
    @field_validator('culture_analyzed', 'ats_history_analyzed', 'is_default', 'is_active', mode='before')
    @classmethod
    def convert_none_to_false(cls, v):
        # Task #1016 (PR-B) + Task #1017 — `is_default` e `is_active`
        # foram declarados `Boolean` (sem `nullable=False`) no model
        # `CompanyProfile`, então linhas legadas/seeded podem ter
        # `NULL`. Sem este coerce o GET /profile responde 500 (Pydantic
        # v2 rejeita None pra `bool`) e o frontend interpreta como
        # "save falhou". O round-trip PATCH→GET com `is_default=NULL` é
        # coberto por `tests/test_company_profile_roundtrip_t1017.py`.
        # A migration `128_company_profile_is_default_not_null` faz o
        # backfill no DB; este validator protege o rollout misto até
        # a migration rodar em todos os ambientes.
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


class IdealProfileUpdate(WeDoBaseModel):
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


class BigFiveQuestionBase(BaseModel):
    text: str
    text_en: str | None = None
    trait: str
    facet: str | None = None
    polarity: str | None = "positive"
    scale_min: int | None = 1
    scale_max: int | None = 5
    scale_labels: dict[str, str] | None = {}
    category: str | None = "general"
    role_specific: list[str] | None = []
    weight: float | None = 1.0
    is_core: bool | None = False
    order: int | None = 0


class BigFiveQuestionCreate(BigFiveQuestionBase):
    pass


class BigFiveQuestionUpdate(WeDoBaseModel):
    text: str | None = None
    text_en: str | None = None
    trait: str | None = None
    facet: str | None = None
    polarity: str | None = None
    scale_min: int | None = None
    scale_max: int | None = None
    scale_labels: dict[str, str] | None = None
    category: str | None = None
    role_specific: list[str] | None = None
    weight: float | None = None
    is_core: bool | None = None
    is_active: bool | None = None
    order: int | None = None


class BigFiveQuestionResponse(BigFiveQuestionBase):
    id: UUID
    is_active: bool
    ai_generated: bool
    validation_stats: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BigFiveRoleProfileBase(BaseModel):
    name: str
    description: str | None = None
    role_category: str | None = None
    seniority_level: str | None = None
    openness_min: float | None = 1.0
    openness_max: float | None = 5.0
    openness_ideal: float | None = 3.0
    openness_weight: float | None = 1.0
    conscientiousness_min: float | None = 1.0
    conscientiousness_max: float | None = 5.0
    conscientiousness_ideal: float | None = 3.0
    conscientiousness_weight: float | None = 1.0
    extroversion_min: float | None = 1.0
    extroversion_max: float | None = 5.0
    extroversion_ideal: float | None = 3.0
    extroversion_weight: float | None = 1.0
    agreeableness_min: float | None = 1.0
    agreeableness_max: float | None = 5.0
    agreeableness_ideal: float | None = 3.0
    agreeableness_weight: float | None = 1.0
    neuroticism_min: float | None = 1.0
    neuroticism_max: float | None = 5.0
    neuroticism_ideal: float | None = 3.0
    neuroticism_weight: float | None = 1.0
    facet_requirements: dict[str, Any] | None = {}


class BigFiveRoleProfileCreate(BigFiveRoleProfileBase):
    company_id: UUID | None = None


class BigFiveRoleProfileUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    role_category: str | None = None
    seniority_level: str | None = None
    openness_min: float | None = None
    openness_max: float | None = None
    openness_ideal: float | None = None
    openness_weight: float | None = None
    conscientiousness_min: float | None = None
    conscientiousness_max: float | None = None
    conscientiousness_ideal: float | None = None
    conscientiousness_weight: float | None = None
    extroversion_min: float | None = None
    extroversion_max: float | None = None
    extroversion_ideal: float | None = None
    extroversion_weight: float | None = None
    agreeableness_min: float | None = None
    agreeableness_max: float | None = None
    agreeableness_ideal: float | None = None
    agreeableness_weight: float | None = None
    neuroticism_min: float | None = None
    neuroticism_max: float | None = None
    neuroticism_ideal: float | None = None
    neuroticism_weight: float | None = None
    facet_requirements: dict[str, Any] | None = None
    is_active: bool | None = None


class BigFiveRoleProfileResponse(BigFiveRoleProfileBase):
    id: UUID
    company_id: UUID | None
    is_active: bool
    is_template: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True


class TechnicalQuestionBase(BaseModel):
    title: str
    description: str | None = None
    question_type: str
    difficulty: str | None = "medium"
    estimated_time: int | None = 5
    area: str
    tags: list[str] | None = []
    options: list[dict[str, Any]] | None = []
    correct_answer: dict[str, Any] | None = None
    explanation: str | None = None
    code_template: str | None = None
    code_solution: str | None = None
    code_language: str | None = None
    test_cases: list[dict[str, Any]] | None = []
    rubric: dict[str, Any] | None = {}
    ai_correction_enabled: bool | None = True


class TechnicalQuestionCreate(TechnicalQuestionBase):
    pass


class TechnicalQuestionUpdate(WeDoBaseModel):
    title: str | None = None
    description: str | None = None
    question_type: str | None = None
    difficulty: str | None = None
    estimated_time: int | None = None
    area: str | None = None
    tags: list[str] | None = None
    options: list[dict[str, Any]] | None = None
    correct_answer: dict[str, Any] | None = None
    explanation: str | None = None
    code_template: str | None = None
    code_solution: str | None = None
    code_language: str | None = None
    test_cases: list[dict[str, Any]] | None = None
    rubric: dict[str, Any] | None = None
    ai_correction_enabled: bool | None = None
    is_active: bool | None = None
    is_public: bool | None = None


class TechnicalQuestionResponse(TechnicalQuestionBase):
    id: UUID
    ai_generated: bool
    is_active: bool
    is_public: bool
    usage_count: int
    avg_score: float | None
    avg_time: float | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True


class TechnicalTestTemplateBase(BaseModel):
    name: str
    description: str | None = None
    area: str | None = None
    role_type: str | None = None
    seniority_level: str | None = None
    question_ids: list[UUID] | None = []
    question_config: dict[str, Any] | None = {}
    total_time: int | None = 60
    passing_score: float | None = 70.0
    instructions: str | None = None
    instructions_en: str | None = None
    randomize_questions: bool | None = True
    randomize_options: bool | None = True
    show_score: bool | None = True
    proctoring_enabled: bool | None = False
    webcam_required: bool | None = False
    ai_correction_enabled: bool | None = True
    ai_correction_prompt: str | None = None


class TechnicalTestTemplateCreate(TechnicalTestTemplateBase):
    company_id: UUID | None = None


class TechnicalTestTemplateUpdate(WeDoBaseModel):
    name: str | None = None
    description: str | None = None
    area: str | None = None
    role_type: str | None = None
    seniority_level: str | None = None
    question_ids: list[UUID] | None = None
    question_config: dict[str, Any] | None = None
    total_time: int | None = None
    passing_score: float | None = None
    instructions: str | None = None
    instructions_en: str | None = None
    randomize_questions: bool | None = None
    randomize_options: bool | None = None
    show_score: bool | None = None
    proctoring_enabled: bool | None = None
    webcam_required: bool | None = None
    ai_correction_enabled: bool | None = None
    ai_correction_prompt: str | None = None
    is_active: bool | None = None
    is_public: bool | None = None


class TechnicalTestTemplateResponse(TechnicalTestTemplateBase):
    id: UUID
    company_id: UUID | None
    is_active: bool
    is_public: bool
    usage_count: int
    avg_score: float | None
    completion_rate: float | None
    created_at: datetime
    updated_at: datetime
    created_by: str | None
    
    class Config:
        from_attributes = True


class CultureAnalysisRequest(WeDoBaseModel):
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


class IdealProfileGenerateRequest(WeDoBaseModel):
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


class BigFiveGenerateRequest(WeDoBaseModel):
    trait: str
    count: int | None = 5
    role_specific: list[str] | None = None


class BigFiveGenerateResponse(BaseModel):
    success: bool
    questions: list[BigFiveQuestionBase]
    trait: str


class TechnicalQuestionsGenerateRequest(WeDoBaseModel):
    area: str
    difficulty: str
    question_type: str
    count: int | None = 5
    context: str | None = None


class TechnicalQuestionsGenerateResponse(BaseModel):
    success: bool
    questions: list[TechnicalQuestionBase]
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


class GlobalSearchSettingsUpdate(WeDoBaseModel):
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
    # P0.D2 (audit Wave 2 2026-05-22): per-department routing + amount threshold.
    # Both NULL = backward-compat (company-wide, any-amount approver).
    department_id: UUID | None = None
    can_approve_above_amount: Decimal | None = None


class ApproverCreate(WeDoBaseModel):
    # R1 canonical: extra=forbid via WeDoBaseModel (audit 2026-05-20 + 2026-05-22).
    # R2 canonical: NO company_id field — vem do JWT via Depends(require_company_id).
    user_name: str
    email: str
    role: str | None = None
    level: int = 1
    user_id: UUID | None = None
    department_id: UUID | None = None
    can_approve_above_amount: Decimal | None = None


class ApproverUpdate(WeDoBaseModel):
    user_name: str | None = None
    email: str | None = None
    role: str | None = None
    level: int | None = None
    user_id: UUID | None = None
    department_id: UUID | None = None
    can_approve_above_amount: Decimal | None = None
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


class CompanyEnrichRequest(WeDoBaseModel):
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
    """# T-06 R2 fix canonical: OnboardingData company_id field removed.

    Multi-tenancy via Depends(require_company_id) in submit_onboarding handler.
    """
    model_config = ConfigDict(extra='forbid')

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
    performance_score: int | None = None  # P2-5: nao fabricar (era hash ficticio)


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
