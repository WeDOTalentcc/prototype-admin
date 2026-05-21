"""
Pydantic schemas for Recruiter Personalization.
"""
from datetime import datetime, time
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict
from app.shared.types import WeDoBaseModel


class RecruiterProfileBase(BaseModel):
    """Base schema for recruiter profiles."""
    recruiter_id: str
    company_id: str
    
    total_jobs_created: int = 0
    avg_creation_time_seconds: int | None = None
    preferred_start_time: time | None = None
    
    preferred_seniorities: list[str] = Field(default_factory=list)
    preferred_departments: list[str] = Field(default_factory=list)
    typical_salary_percentile: int | None = None
    
    fields_often_corrected: dict[str, float] = Field(default_factory=dict)
    fields_rarely_changed: dict[str, float] = Field(default_factory=dict)
    avg_correction_rate: float | None = None
    
    prefers_detailed_explanations: bool = True
    prefers_quick_flow: bool = False
    skips_optional_steps: bool = False
    uses_jd_import: bool = False
    
    custom_confidence_thresholds: dict[str, float] = Field(default_factory=dict)
    
    communication_style: str = "professional"
    preferred_language: str = "pt-BR"


class RecruiterProfileCreate(RecruiterProfileBase):
    """Schema for creating a recruiter profile."""
    pass


class RecruiterProfileUpdate(WeDoBaseModel):
    """Schema for updating a recruiter profile."""
    total_jobs_created: int | None = None
    avg_creation_time_seconds: int | None = None
    preferred_start_time: time | None = None
    
    preferred_seniorities: list[str] | None = None
    preferred_departments: list[str] | None = None
    typical_salary_percentile: int | None = None
    
    fields_often_corrected: dict[str, float] | None = None
    fields_rarely_changed: dict[str, float] | None = None
    avg_correction_rate: float | None = None
    
    prefers_detailed_explanations: bool | None = None
    prefers_quick_flow: bool | None = None
    skips_optional_steps: bool | None = None
    uses_jd_import: bool | None = None
    
    custom_confidence_thresholds: dict[str, float] | None = None
    
    communication_style: str | None = None
    preferred_language: str | None = None


class RecruiterProfileResponse(RecruiterProfileBase):
    """Response schema for recruiter profiles."""
    id: UUID
    first_job_at: datetime | None = None
    last_job_at: datetime | None = None
    profile_calculated_at: datetime | None = None
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
    typical_correction_direction: str | None = None
    avg_correction_magnitude: float | None = None
    common_corrections: dict[str, Any] = Field(default_factory=dict)
    personal_confidence_threshold: float | None = None


class RecruiterFieldPreferenceResponse(RecruiterFieldPreferenceBase):
    """Response schema for field preferences."""
    id: UUID
    last_interaction_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PersonalizationEventCreate(WeDoBaseModel):
    """Schema for creating personalization events."""
    recruiter_id: str
    company_id: str
    job_id: UUID | None = None
    event_type: str
    field_name: str | None = None
    suggested_value: Any | None = None
    final_value: Any | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    time_to_decision_ms: int | None = None


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
    consent_version: str | None = None


class PersonalizationSettingsUpdate(WeDoBaseModel):
    """Schema for updating personalization settings."""
    enable_personalization: bool | None = None
    enable_learning: bool | None = None
    learn_from_corrections: bool | None = None
    learn_from_time_patterns: bool | None = None
    adapt_communication_style: bool | None = None
    show_personalization_indicators: bool | None = None
    explain_why_suggested: bool | None = None


class PersonalizationSettingsResponse(PersonalizationSettingsBase):
    """Response schema for personalization settings."""
    recruiter_id: str
    consent_given_at: datetime | None = None
    consent_version: str | None = None
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
    confidence_thresholds: dict[str, float] = Field(default_factory=dict)


class PersonalizedDefaults(BaseModel):
    """Personalized default values for wizard."""
    seniority: str | None = None
    department: str | None = None
    work_model: str | None = None
    salary_percentile_hint: int | None = None
    suggested_skills: list[str] = Field(default_factory=list)


class RecruiterPersonalizationContext(BaseModel):
    """Full personalization context for a recruiter."""
    model_config = ConfigDict(extra='forbid')

    recruiter_id: str
    profile: RecruiterProfileResponse | None = None
    settings: PersonalizationSettingsResponse | None = None
    flow_config: WizardFlowConfig = Field(default_factory=WizardFlowConfig)
    personalized_defaults: PersonalizedDefaults = Field(default_factory=PersonalizedDefaults)
    field_preferences: dict[str, RecruiterFieldPreferenceResponse] = Field(default_factory=dict)
    is_new_user: bool = True
    personalization_level: str = "none"
