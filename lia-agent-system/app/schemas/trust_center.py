"""
Pydantic schemas for Trust Center API.
"""
from datetime import datetime
from enum import Enum, StrEnum

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class SubprocessorCategoryEnum(StrEnum):
    """Categories of data subprocessors."""
    CLOUD_HOSTING = "cloud_hosting"
    CRM = "crm"
    ANALYTICS = "analytics"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    SECURITY = "security"
    STORAGE = "storage"
    AI_ML = "ai_ml"
    OTHER = "other"


class ResourceCategoryEnum(StrEnum):
    """Categories of trust center resources."""
    POLICY = "policy"
    REPORT = "report"
    CERTIFICATE = "certificate"
    WHITEPAPER = "whitepaper"
    OTHER = "other"


class UpdateCategoryEnum(StrEnum):
    """Categories of trust center updates."""
    GENERAL = "general"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    CERTIFICATION = "certification"
    POLICY = "policy"


class TrustCenterSettingsBase(BaseModel):
    """Base schema for trust center settings."""
    company_slug: str = Field(..., min_length=2, max_length=100)
    company_name: str = Field(..., min_length=1, max_length=255)
    company_description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = "#6366F1"
    is_public: bool = False
    custom_domain: str | None = None
    show_certifications: bool = True
    show_controls: bool = True
    show_bias_audits: bool = True
    show_subprocessors: bool = True
    contact_email: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None


class TrustCenterSettingsCreate(TrustCenterSettingsBase):
    """Schema for creating trust center settings."""
    pass


class TrustCenterSettingsUpdate(WeDoBaseModel):
    """Schema for updating trust center settings."""
    company_slug: str | None = Field(None, min_length=2, max_length=100)
    company_name: str | None = Field(None, min_length=1, max_length=255)
    company_description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    is_public: bool | None = None
    custom_domain: str | None = None
    show_certifications: bool | None = None
    show_controls: bool | None = None
    show_bias_audits: bool | None = None
    show_subprocessors: bool | None = None
    contact_email: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None


class TrustCenterSettingsResponse(TrustCenterSettingsBase):
    """Schema for trust center settings response."""
    id: str
    company_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SubprocessorBase(BaseModel):
    """Base schema for subprocessor."""
    name: str = Field(..., min_length=1, max_length=255)
    category: SubprocessorCategoryEnum = SubprocessorCategoryEnum.OTHER
    description: str | None = None
    country: str | None = None
    data_processed: str | None = None
    is_public: bool = True


class SubprocessorCreate(SubprocessorBase):
    """Schema for creating a subprocessor."""
    pass


class SubprocessorResponse(SubprocessorBase):
    """Schema for subprocessor response."""
    id: str
    company_id: str
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class SubprocessorListResponse(BaseModel):
    """Schema for list of subprocessors."""
    subprocessors: list[SubprocessorResponse]
    total: int


class TrustCenterResourceBase(BaseModel):
    """Base schema for trust center resource."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: ResourceCategoryEnum = ResourceCategoryEnum.OTHER
    file_url: str
    is_public: bool = True
    requires_nda: bool = False


class TrustCenterResourceCreate(TrustCenterResourceBase):
    """Schema for creating a resource."""
    pass


class TrustCenterResourceResponse(TrustCenterResourceBase):
    """Schema for resource response."""
    id: str
    company_id: str
    download_count: int = 0
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TrustCenterResourceListResponse(BaseModel):
    """Schema for list of resources."""
    resources: list[TrustCenterResourceResponse]
    total: int


class TrustCenterUpdateBase(BaseModel):
    """Base schema for trust center update."""
    title: str = Field(..., min_length=1, max_length=255)
    content: str
    category: UpdateCategoryEnum = UpdateCategoryEnum.GENERAL
    is_published: bool = False


class TrustCenterUpdateCreate(TrustCenterUpdateBase):
    """Schema for creating an update."""
    pass


class TrustCenterUpdateResponse(TrustCenterUpdateBase):
    """Schema for update response."""
    id: str
    company_id: str
    published_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class TrustCenterUpdateListResponse(BaseModel):
    """Schema for list of updates."""
    updates: list[TrustCenterUpdateResponse]
    total: int


class CertificationInfo(BaseModel):
    """Schema for certification information."""
    name: str
    status: str
    issued_date: datetime | None = None
    expires_date: datetime | None = None
    description: str | None = None
    badge_url: str | None = None


class ControlSummary(BaseModel):
    """Schema for high-level control summary."""
    framework: str
    total_controls: int
    implemented: int
    partial: int
    not_implemented: int
    compliance_percentage: float


class BiasAuditSummary(BaseModel):
    """Schema for public bias audit summary."""
    audit_period: str
    audit_type: str
    status: str
    categories_evaluated: list[str]
    overall_result: str
    published_at: datetime | None = None


class TrustCenterOverviewResponse(BaseModel):
    """Schema for trust center overview."""
    company_name: str
    company_description: str | None = None
    logo_url: str | None = None
    primary_color: str | None = None
    contact_email: str | None = None
    privacy_policy_url: str | None = None
    terms_url: str | None = None
    certifications_count: int = 0
    controls_summary: dict | None = None
    last_updated: datetime | None = None


class TrustCenterCertificationsResponse(BaseModel):
    """Schema for certifications listing."""
    certifications: list[CertificationInfo]
    total: int


class TrustCenterControlsResponse(BaseModel):
    """Schema for controls summary."""
    frameworks: list[ControlSummary]
    overall_compliance: float


class TrustCenterBiasAuditsResponse(BaseModel):
    """Schema for bias audits listing."""
    audits: list[BiasAuditSummary]
    total: int
    latest_audit_date: datetime | None = None
