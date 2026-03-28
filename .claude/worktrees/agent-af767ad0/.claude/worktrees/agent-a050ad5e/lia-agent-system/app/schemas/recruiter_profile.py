"""
Pydantic schemas for Recruiter Personalization.
"""
from datetime import datetime, time
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class RecruiterProfileBase(BaseModel):
    """Base schema for recruiter profiles."""
    recruiter_id: str
    company_id: str
    
    total_jobs_created: int = 0
    avg_creation_time_seconds: Optional[int] = None
    preferred_start_time: Optional[time] = None
    
    preferred_seniorities: List[str] = Field(default_factory=list)
    preferred_departments: List[str] = Field(default_factory=list)
    typical_salary_percentile: Optional[int] = None
    
    fields_often_corrected: Dict[str, float] = Field(default_factory=dict)
    fields_rarely_changed: Dict[str, float] = Field(default_factory=dict)
    avg_correction_rate: Optional[float] = None
    
    prefers_detailed_explanations: bool = True
    prefers_quick_flow: bool = False
    skips_optional_steps: bool = False
    uses_jd_import: bool = False
    
    custom_confidence_thresholds: Dict[str, float] = Field(default_factory=dict)
    
    communication_style: str = "professional"
    preferred_language: str = "pt-BR"


class RecruiterProfileCreate(RecruiterProfileBase):
    """Schema for creating a recruiter profile."""
    pass


class RecruiterProfileUpdate(BaseModel):
    """Schema for updating a recruiter profile."""
    total_jobs_created: Optional[int] = None
    avg_creation_time_seconds: Optional[int] = None
    preferred_start_time: Optional[time] = None
    
    preferred_seniorities: Optional[List[str]] = None
    preferred_departments: Optional[List[str]] = None
    typical_salary_percentile: Optional[int] = None
    
    fields_often_corrected: Optional[Dict[str, float]] = None
    fields_rarely_changed: Optional[Dict[str, float]] = None
    avg_correction_rate: Optional[float] = None
    
    prefers_detailed_explanations: Optional[bool] = None
    prefers_quick_flow: Optional[bool] = None
    skips_optional_steps: Optional[bool] = None
    uses_jd_import: Optional[bool] = None
    
    custom_confidence_thresholds: Optional[Dict[str, float]] = None
    
    communication_style: Optional[str] = None
    preferred_language: Optional[str] = None


class RecruiterProfileResponse(RecruiterProfileBase):
    """Response schema for recruiter profiles."""
    id: UUID
    first_job_at: Optional[datetime] = None
    last_job_at: Optional[datetime] = None
    profile_calculated_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecruiterFieldPreferenceBase(BaseModel):
    """Base schema for field preferences."""
    recruiter_id: str
    field_name: str
    times_seen: int = 0
    times_corrected: int = 0
    times_accepted: int = 0
    typical_correction_direction: Optional[str] = None
    avg_correction_magnitude: Optional[float] = None
    common_corrections: Dict[str, Any] = Field(default_factory=dict)
    personal_confidence_threshold: Optional[float] = None


class RecruiterFieldPreferenceResponse(RecruiterFieldPreferenceBase):
    """Response schema for field preferences."""
    id: UUID
    last_interaction_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonalizationEventCreate(BaseModel):
    """Schema for creating personalization events."""
    recruiter_id: str
    company_id: str
    job_id: Optional[UUID] = None
    event_type: str
    field_name: Optional[str] = None
    suggested_value: Optional[Any] = None
    final_value: Optional[Any] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    time_to_decision_ms: Optional[int] = None


class PersonalizationEventResponse(PersonalizationEventCreate):
    """Response schema for personalization events."""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PersonalizationSettingsBase(BaseModel):
    """Base schema for personalization settings."""
    enable_personalization: bool = True
    enable_learning: bool = True
    learn_from_corrections: bool = True
    learn_from_time_patterns: bool = True
    adapt_communication_style: bool = True
    show_personalization_indicators: bool = True
    explain_why_suggested: bool = True


class PersonalizationSettingsCreate(PersonalizationSettingsBase):
    """Schema for creating personalization settings."""
    recruiter_id: str
    consent_version: Optional[str] = None


class PersonalizationSettingsUpdate(BaseModel):
    """Schema for updating personalization settings."""
    enable_personalization: Optional[bool] = None
    enable_learning: Optional[bool] = None
    learn_from_corrections: Optional[bool] = None
    learn_from_time_patterns: Optional[bool] = None
    adapt_communication_style: Optional[bool] = None
    show_personalization_indicators: Optional[bool] = None
    explain_why_suggested: Optional[bool] = None


class PersonalizationSettingsResponse(PersonalizationSettingsBase):
    """Response schema for personalization settings."""
    recruiter_id: str
    consent_given_at: Optional[datetime] = None
    consent_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WizardFlowConfig(BaseModel):
    """Configuration for personalized wizard flow."""
    show_detailed_explanations: bool = True
    skip_optional_confirmations: bool = False
    auto_expand_sections: bool = True
    suggest_jd_import: bool = False
    confidence_thresholds: Dict[str, float] = Field(default_factory=dict)


class PersonalizedDefaults(BaseModel):
    """Personalized default values for wizard."""
    seniority: Optional[str] = None
    department: Optional[str] = None
    work_model: Optional[str] = None
    salary_percentile_hint: Optional[int] = None
    suggested_skills: List[str] = Field(default_factory=list)


class RecruiterPersonalizationContext(BaseModel):
    """Full personalization context for a recruiter."""
    recruiter_id: str
    profile: Optional[RecruiterProfileResponse] = None
    settings: Optional[PersonalizationSettingsResponse] = None
    flow_config: WizardFlowConfig = Field(default_factory=WizardFlowConfig)
    personalized_defaults: PersonalizedDefaults = Field(default_factory=PersonalizedDefaults)
    field_preferences: Dict[str, RecruiterFieldPreferenceResponse] = Field(default_factory=dict)
    is_new_user: bool = True
    personalization_level: str = "none"
