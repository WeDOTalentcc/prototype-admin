"""
Pydantic schemas for Data Subject Requests API (Portal do Titular LGPD).

Supports LGPD Art. 18 rights including:
- Access, Correction, Deletion, Portability, Objection, Restriction, Explanation
"""

from datetime import datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class RequestTypeEnum(StrEnum):
    """Types of data subject requests under LGPD Art. 18."""
    ACCESS = "access"
    CORRECTION = "correction"
    DELETION = "deletion"
    PORTABILITY = "portability"
    OBJECTION = "objection"
    RESTRICTION = "restriction"
    EXPLANATION = "explanation"


class RequestStatusEnum(StrEnum):
    """Status of data subject requests."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class SourceChannelEnum(StrEnum):
    """Source channel for data subject requests."""
    PORTAL = "portal"
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    IN_PERSON = "in_person"
    API = "api"


class DataSubjectRequestCreate(WeDoBaseModel):
    """Schema for creating a new data subject request (public endpoint)."""
    company_id: str = Field(..., description="Company ID (tenant) receiving the request")
    subject_name: str = Field(..., min_length=2, max_length=255, description="Full name of the data subject")
    subject_email: str = Field(..., description="Email of the data subject")
    subject_phone: str | None = Field(None, max_length=50, description="Phone number of the data subject")
    subject_identifier: str = Field(..., min_length=5, max_length=50, description="CPF or other identifier of the data subject")
    request_type: RequestTypeEnum = Field(..., description="Type of LGPD request")
    description: str = Field(..., min_length=10, description="Detailed description of the request")
    source_channel: SourceChannelEnum = Field(default=SourceChannelEnum.PORTAL, description="Channel through which request was submitted")
    data_categories: list[str] | None = Field(default=[], description="Specific data categories affected")

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "550e8400-e29b-41d4-a716-446655440000",
                "subject_name": "João da Silva",
                "subject_email": "joao.silva@email.com",
                "subject_phone": "+55 11 99999-9999",
                "subject_identifier": "123.456.789-00",
                "request_type": "access",
                "description": "Solicito acesso completo aos meus dados pessoais armazenados na plataforma, incluindo histórico de candidaturas e avaliações.",
                "source_channel": "portal",
                "data_categories": ["personal_info", "cv", "assessment_results"]
            }
        }


class DataSubjectRequestResponse(BaseModel):
    """Response schema for a data subject request."""
    id: str
    company_id: str
    request_type: str
    status: str
    subject_name: str
    subject_email: str
    subject_phone: str | None = None
    subject_identifier: str
    identity_verified: bool = False
    identity_verification_method: str | None = None
    identity_verified_at: datetime | None = None
    description: str
    response: str | None = None
    data_categories: list[str] = []
    legal_basis: str | None = None
    assigned_to: str | None = None
    sla_deadline: datetime | None = None
    sla_met: bool | None = None
    completed_at: datetime | None = None
    rejection_reason: str | None = None
    evidence_files: list[dict[str, Any]] = []
    audit_trail: list[dict[str, Any]] = []
    source_channel: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    days_remaining: int | None = None
    is_overdue: bool | None = None

    class Config:
        from_attributes = True


class DataSubjectRequestListResponse(BaseModel):
    """Paginated list of data subject requests."""
    requests: list[DataSubjectRequestResponse]
    total: int
    skip: int
    limit: int


class DataSubjectRequestPublicCreate(WeDoBaseModel):
    """Public response after creating a request (limited info for security)."""
    id: str
    status: str
    request_type: str
    sla_deadline: datetime | None = None
    created_at: datetime | None = None
    message: str = "Sua solicitação foi registrada com sucesso. Use o ID fornecido para acompanhar o status."


class DataSubjectRequestPublicTrack(BaseModel):
    """Public tracking response (limited info for security)."""
    id: str
    status: str
    request_type: str
    created_at: datetime | None = None
    sla_deadline: datetime | None = None
    days_remaining: int | None = None
    is_overdue: bool | None = None
    response: str | None = None
    completed_at: datetime | None = None


class DataSubjectRequestAssign(BaseModel):
    """Schema for assigning a request to a user."""
    assigned_to: str = Field(..., description="User ID to assign the request to")

    class Config:
        json_schema_extra = {
            "example": {
                "assigned_to": "770e8400-e29b-41d4-a716-446655440002"
            }
        }


class DataSubjectRequestVerifyIdentity(BaseModel):
    """Schema for verifying data subject identity."""
    identity_verification_method: str = Field(..., description="Method used to verify identity (e.g., 'document', 'video_call', 'email_confirmation')")
    verified: bool = Field(..., description="Whether identity was successfully verified")

    class Config:
        json_schema_extra = {
            "example": {
                "identity_verification_method": "document",
                "verified": True
            }
        }


class DataSubjectRequestComplete(BaseModel):
    """Schema for completing a request."""
    response: str = Field(..., min_length=10, description="Response text to the data subject")
    evidence_files: list[dict[str, Any]] | None = Field(default=[], description="Evidence files attached to the response")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Conforme solicitado, segue anexo o relatório completo contendo todos os seus dados pessoais armazenados em nossa plataforma, incluindo histórico de candidaturas e avaliações realizadas.",
                "evidence_files": [
                    {"name": "dados_pessoais.pdf", "url": "/files/abc123.pdf"}
                ]
            }
        }


class DataSubjectRequestReject(BaseModel):
    """Schema for rejecting a request."""
    rejection_reason: str = Field(..., min_length=10, description="Reason for rejecting the request")

    class Config:
        json_schema_extra = {
            "example": {
                "rejection_reason": "A solicitação não pode ser atendida pois não foi possível confirmar a identidade do titular. Por favor, entre em contato através do nosso canal de atendimento para nova verificação."
            }
        }


class DataSubjectRequestStats(BaseModel):
    """Statistics for data subject requests dashboard."""
    total_requests: int = 0
    pending_requests: int = 0
    in_review_requests: int = 0
    processing_requests: int = 0
    completed_requests: int = 0
    rejected_requests: int = 0
    cancelled_requests: int = 0
    overdue_requests: int = 0
    sla_compliance_rate: float = 0.0
    avg_resolution_days: float | None = None
    requests_by_type: dict[str, int] = {}
    requests_by_channel: dict[str, int] = {}
