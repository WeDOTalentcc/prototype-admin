"""
Pydantic schemas for Trust Center API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SubprocessorCategoryEnum(str, Enum):
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


class ResourceCategoryEnum(str, Enum):
    """Categories of trust center resources."""
    POLICY = "policy"
    REPORT = "report"
    CERTIFICATE = "certificate"
    WHITEPAPER = "whitepaper"
    OTHER = "other"


class UpdateCategoryEnum(str, Enum):
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
    company_description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = "#6366F1"
    is_public: bool = False
    custom_domain: Optional[str] = None
    show_certifications: bool = True
    show_controls: bool = True
    show_bias_audits: bool = True
    show_subprocessors: bool = True
    contact_email: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None


class TrustCenterSettingsCreate(TrustCenterSettingsBase):
    """Schema for creating trust center settings."""
    pass


class TrustCenterSettingsUpdate(BaseModel):
    """Schema for updating trust center settings."""
    company_slug: Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    is_public: Optional[bool] = None
    custom_domain: Optional[str] = None
    show_certifications: Optional[bool] = None
    show_controls: Optional[bool] = None
    show_bias_audits: Optional[bool] = None
    show_subprocessors: Optional[bool] = None
    contact_email: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None


class TrustCenterSettingsResponse(TrustCenterSettingsBase):
    """Schema for trust center settings response."""
    id: str
    company_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubprocessorBase(BaseModel):
    """Base schema for subprocessor."""
    name: str = Field(..., min_length=1, max_length=255)
    category: SubprocessorCategoryEnum = SubprocessorCategoryEnum.OTHER
    description: Optional[str] = None
    country: Optional[str] = None
    data_processed: Optional[str] = None
    is_public: bool = True


class SubprocessorCreate(SubprocessorBase):
    """Schema for creating a subprocessor."""
    pass


class SubprocessorResponse(SubprocessorBase):
    """Schema for subprocessor response."""
    id: str
    company_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubprocessorListResponse(BaseModel):
    """Schema for list of subprocessors."""
    subprocessors: List[SubprocessorResponse]
    total: int


class TrustCenterResourceBase(BaseModel):
    """Base schema for trust center resource."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
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
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrustCenterResourceListResponse(BaseModel):
    """Schema for list of resources."""
    resources: List[TrustCenterResourceResponse]
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
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TrustCenterUpdateListResponse(BaseModel):
    """Schema for list of updates."""
    updates: List[TrustCenterUpdateResponse]
    total: int


class CertificationInfo(BaseModel):
    """Schema for certification information."""
    name: str
    status: str
    issued_date: Optional[datetime] = None
    expires_date: Optional[datetime] = None
    description: Optional[str] = None
    badge_url: Optional[str] = None


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
    categories_evaluated: List[str]
    overall_result: str
    published_at: Optional[datetime] = None


class TrustCenterOverviewResponse(BaseModel):
    """Schema for trust center overview."""
    company_name: str
    company_description: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    contact_email: Optional[str] = None
    privacy_policy_url: Optional[str] = None
    terms_url: Optional[str] = None
    certifications_count: int = 0
    controls_summary: Optional[dict] = None
    last_updated: Optional[datetime] = None


class TrustCenterCertificationsResponse(BaseModel):
    """Schema for certifications listing."""
    certifications: List[CertificationInfo]
    total: int


class TrustCenterControlsResponse(BaseModel):
    """Schema for controls summary."""
    frameworks: List[ControlSummary]
    overall_compliance: float


class TrustCenterBiasAuditsResponse(BaseModel):
    """Schema for bias audits listing."""
    audits: List[BiasAuditSummary]
    total: int
    latest_audit_date: Optional[datetime] = None
