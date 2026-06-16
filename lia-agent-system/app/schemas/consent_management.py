"""
Pydantic schemas for Consent Management API.

Includes schemas for:
- ConsentVersion - Versioned consent terms
- ConsentEvent - Consent events (grant, revoke, renew, expire)
- Statistics and history
"""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class ConsentEventTypeEnum(StrEnum):
    """Types of consent events."""
    GRANTED = "granted"
    REVOKED = "revoked"
    RENEWED = "renewed"
    EXPIRED = "expired"


class ConsentChannelEnum(StrEnum):
    """Channels for consent collection."""
    WEB = "web"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    API = "api"
    PORTAL = "portal"


class ConsentVersionCreate(WeDoBaseModel):
    """Schema for creating a new consent version."""
    consent_type: str = Field(..., min_length=1, max_length=50, description="Type of consent (e.g., data_processing, ai_scoring)")
    version: str = Field(..., min_length=1, max_length=20, description="Version string (e.g., 1.0, 2.0)")
    title: str = Field(..., min_length=1, max_length=500, description="Title of the consent term")
    content_html: str = Field(..., min_length=10, description="HTML content of the consent term")
    content_text: str = Field(..., min_length=10, description="Plain text content of the consent term")
    effective_from: datetime = Field(..., description="Date/time when this version becomes effective")
    requires_explicit_consent: bool = Field(default=True, description="Whether explicit consent is required")
    renewal_period_days: int | None = Field(None, ge=1, description="Days until consent expires and needs renewal")

    class Config:
        json_schema_extra = {
            "example": {
                "consent_type": "data_processing",
                "version": "2.0",
                "title": "Termo de Consentimento para Processamento de Dados",
                "content_html": "<h1>Consentimento LGPD</h1><p>Autorizo o processamento dos meus dados...</p>",
                "content_text": "Consentimento LGPD\n\nAutorizo o processamento dos meus dados...",
                "effective_from": "2024-01-15T00:00:00Z",
                "requires_explicit_consent": True,
                "renewal_period_days": 365
            }
        }


class ConsentVersionResponse(BaseModel):
    """Response schema for consent version."""
    id: str
    company_id: str
    consent_type: str
    version: str
    title: str
    content_html: str
    content_text: str
    hash: str
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    is_current: bool = True
    requires_explicit_consent: bool = True
    renewal_period_days: int | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ConsentVersionListResponse(BaseModel):
    """Paginated list of consent versions."""
    versions: list[ConsentVersionResponse]
    total: int
    limit: int
    offset: int


class ConsentEventCreate(WeDoBaseModel):
    """Schema for creating a consent event."""
    consent_version_id: str = Field(..., description="ID of the consent version")
    subject_email: str = Field(..., description="Email of the data subject")
    subject_identifier: str = Field(..., max_length=50, description="CPF or other identifier of the data subject")
    event_type: ConsentEventTypeEnum = Field(..., description="Type of consent event")
    consent_given: bool = Field(..., description="Whether consent was given")
    ip_address: str | None = Field(None, max_length=45, description="IP address of the subject")
    user_agent: str | None = Field(None, max_length=500, description="User agent string")
    device_info: dict[str, Any] | None = Field(default={}, description="Device information")
    channel: ConsentChannelEnum = Field(default=ConsentChannelEnum.WEB, description="Channel used for consent")

    class Config:
        json_schema_extra = {
            "example": {
                "consent_version_id": "550e8400-e29b-41d4-a716-446655440000",
                "subject_email": "joao.silva@email.com",
                "subject_identifier": "123.456.789-00",
                "event_type": "granted",
                "consent_given": True,
                "ip_address": "189.123.45.67",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "device_info": {"os": "Windows", "browser": "Chrome"},
                "channel": "whatsapp"
            }
        }


class ConsentEventResponse(BaseModel):
    """Response schema for consent event."""
    id: str
    company_id: str
    consent_version_id: str
    subject_id: str | None = None
    subject_email: str
    subject_identifier: str
    event_type: str
    consent_given: bool
    ip_address: str | None = None
    user_agent: str | None = None
    device_info: dict[str, Any] = {}
    location_country: str | None = None
    channel: str
    proof_hash: str
    expires_at: datetime | None = None
    created_at: datetime | None = None
    is_expired: bool | None = None
    days_until_expiry: int | None = None

    class Config:
        from_attributes = True


class ConsentEventListResponse(BaseModel):
    """Paginated list of consent events."""
    events: list[ConsentEventResponse]
    total: int
    limit: int
    offset: int


class ConsentSubjectEvent(BaseModel):
    """Consent event for subject history."""
    id: str
    consent_type: str
    consent_version: str
    event_type: str
    consent_given: bool
    channel: str
    created_at: datetime | None = None
    expires_at: datetime | None = None
    is_expired: bool = False
    is_current: bool = False


class ConsentSubjectHistory(BaseModel):
    """Complete consent history for a data subject."""
    subject_identifier: str
    subject_email: str
    events: list[ConsentSubjectEvent]
    current_consents: dict[str, bool] = {}
    total_events: int


class ConsentRevokeRequest(WeDoBaseModel):
    """Schema for revoking consent."""
    subject_identifier: str = Field(..., max_length=50, description="CPF or other identifier of the data subject")
    consent_type: str | None = Field(None, max_length=50, description="Type of consent to revoke (optional)")
    consent_version_id: str | None = Field(None, description="Specific consent version ID to revoke (optional)")
    ip_address: str | None = Field(None, max_length=45, description="IP address of the subject")
    user_agent: str | None = Field(None, max_length=500, description="User agent string")
    channel: ConsentChannelEnum = Field(default=ConsentChannelEnum.WEB, description="Channel used for revocation")

    class Config:
        json_schema_extra = {
            "example": {
                "subject_identifier": "123.456.789-00",
                "consent_type": "data_processing",
                "ip_address": "189.123.45.67",
                "channel": "portal"
            }
        }


class ConsentTypeStats(BaseModel):
    """Statistics for a single consent type."""
    consent_type: str
    total_granted: int = 0
    total_revoked: int = 0
    total_expired: int = 0
    total_active: int = 0
    consent_rate: float = 0.0


class ConsentStats(BaseModel):
    """Overall consent statistics."""
    total_consent_versions: int = 0
    total_consent_events: int = 0
    total_subjects: int = 0
    total_granted: int = 0
    total_revoked: int = 0
    total_expired: int = 0
    by_type: list[ConsentTypeStats] = []
    by_channel: dict[str, int] = {}
