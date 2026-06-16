"""
Pydantic schemas for Insurance Management API (BCB 498/2025).

Includes schemas for:
- Insurance Policies (cyber insurance)
- Coverages (data breach, ransomware, etc.)
- Documents (policy attachments)
- Claims/Sinistros
- Dashboard and Alerts
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class InsurancePolicyStatusEnum(str, Enum):
    """Status of cyber insurance policies for BCB 498/2025 compliance."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING_RENEWAL = "pending_renewal"


class InsuranceCoverageTypeEnum(str, Enum):
    """Types of cyber insurance coverages per BCB 498/2025."""
    DATA_BREACH = "data_breach"
    RANSOMWARE = "ransomware"
    BUSINESS_INTERRUPTION = "business_interruption"
    REGULATORY_DEFENSE = "regulatory_defense"
    CYBER_LIABILITY = "cyber_liability"
    FORENSICS = "forensics"
    NOTIFICATION_COSTS = "notification_costs"
    CRISIS_MANAGEMENT = "crisis_management"


class InsuranceDocumentTypeEnum(str, Enum):
    """Types of insurance-related documents."""
    POLICY = "policy"
    ENDORSEMENT = "endorsement"
    CERTIFICATE = "certificate"
    CLAIM = "claim"
    CORRESPONDENCE = "correspondence"


class InsuranceClaimStatusEnum(str, Enum):
    """Status of insurance claims/sinistros."""
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    SETTLED = "settled"
    CLOSED = "closed"


class InsurancePolicyCreate(BaseModel):
    """Schema for creating a new insurance policy."""
    policy_number: str = Field(..., min_length=1, max_length=100, description="Unique policy number")
    insurer_name: str = Field(..., min_length=1, max_length=255, description="Insurance company name")
    insurer_cnpj: Optional[str] = Field(None, max_length=18, description="Insurer CNPJ")
    broker_name: Optional[str] = Field(None, max_length=255, description="Insurance broker name")
    broker_contact: Optional[str] = Field(None, max_length=255, description="Broker contact info")
    coverage_start: date = Field(..., description="Start date of coverage")
    coverage_end: date = Field(..., description="End date of coverage")
    total_coverage_amount: float = Field(..., gt=0, description="Total coverage amount")
    currency: str = Field(default="BRL", max_length=3, description="Currency code")
    premium_amount: float = Field(..., ge=0, description="Premium amount")
    deductible_amount: float = Field(default=0, ge=0, description="Deductible amount")

    class Config:
        json_schema_extra = {
            "example": {
                "policy_number": "CYB-2025-001234",
                "insurer_name": "Seguradora XYZ S.A.",
                "insurer_cnpj": "12.345.678/0001-90",
                "broker_name": "Corretor ABC Ltda.",
                "broker_contact": "contato@corretorabc.com.br",
                "coverage_start": "2025-01-01",
                "coverage_end": "2026-01-01",
                "total_coverage_amount": 5000000.00,
                "currency": "BRL",
                "premium_amount": 25000.00,
                "deductible_amount": 50000.00
            }
        }


class InsurancePolicyUpdate(BaseModel):
    """Schema for updating an insurance policy."""
    policy_number: Optional[str] = Field(None, min_length=1, max_length=100)
    insurer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    insurer_cnpj: Optional[str] = Field(None, max_length=18)
    broker_name: Optional[str] = None
    broker_contact: Optional[str] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    total_coverage_amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    premium_amount: Optional[float] = Field(None, ge=0)
    deductible_amount: Optional[float] = Field(None, ge=0)
    status: Optional[InsurancePolicyStatusEnum] = None


class InsuranceCoverageResponse(BaseModel):
    """Response schema for insurance coverage."""
    id: str
    policy_id: str
    coverage_type: str
    description: Optional[str] = None
    coverage_limit: Optional[float] = None
    sub_limit: Optional[float] = None
    deductible: Optional[float] = None
    is_included: bool = True
    exclusions: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InsuranceDocumentResponse(BaseModel):
    """Response schema for insurance document."""
    id: str
    policy_id: str
    document_type: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InsurancePolicyResponse(BaseModel):
    """Response schema for insurance policy."""
    id: str
    company_id: str
    policy_number: str
    insurer_name: str
    insurer_cnpj: Optional[str] = None
    broker_name: Optional[str] = None
    broker_contact: Optional[str] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    total_coverage_amount: Optional[float] = None
    currency: str = "BRL"
    premium_amount: Optional[float] = None
    deductible_amount: Optional[float] = None
    status: str
    renewal_reminder_sent: bool = False
    last_renewal_reminder_at: Optional[datetime] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    days_until_expiry: Optional[int] = None
    coverages: Optional[List[InsuranceCoverageResponse]] = None
    documents: Optional[List[InsuranceDocumentResponse]] = None

    class Config:
        from_attributes = True


class InsurancePolicyListResponse(BaseModel):
    """Paginated list of insurance policies."""
    policies: List[InsurancePolicyResponse]
    total: int
    limit: int
    offset: int


class InsuranceCoverageCreate(BaseModel):
    """Schema for creating insurance coverage."""
    coverage_type: InsuranceCoverageTypeEnum = Field(..., description="Type of coverage")
    description: Optional[str] = Field(None, description="Coverage description")
    coverage_limit: float = Field(..., gt=0, description="Coverage limit amount")
    sub_limit: Optional[float] = Field(None, ge=0, description="Sub-limit if applicable")
    deductible: Optional[float] = Field(None, ge=0, description="Deductible for this coverage")
    is_included: bool = Field(default=True, description="Whether coverage is included")
    exclusions: Optional[str] = Field(None, description="Coverage exclusions")
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        json_schema_extra = {
            "example": {
                "coverage_type": "data_breach",
                "description": "Cobertura para incidentes de vazamento de dados",
                "coverage_limit": 1000000.00,
                "sub_limit": 500000.00,
                "deductible": 10000.00,
                "is_included": True,
                "exclusions": "Não cobre atos dolosos",
                "notes": "Inclui custos de notificação LGPD"
            }
        }


class InsuranceCoverageUpdate(BaseModel):
    """Schema for updating insurance coverage."""
    coverage_type: Optional[InsuranceCoverageTypeEnum] = None
    description: Optional[str] = None
    coverage_limit: Optional[float] = Field(None, gt=0)
    sub_limit: Optional[float] = Field(None, ge=0)
    deductible: Optional[float] = Field(None, ge=0)
    is_included: Optional[bool] = None
    exclusions: Optional[str] = None
    notes: Optional[str] = None


class InsuranceDocumentCreate(BaseModel):
    """Schema for creating/uploading insurance document."""
    document_type: InsuranceDocumentTypeEnum = Field(..., description="Type of document")
    file_name: str = Field(..., min_length=1, max_length=500, description="Original file name")
    file_url: str = Field(..., max_length=1000, description="URL to the uploaded file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    mime_type: str = Field(..., max_length=100, description="MIME type of the file")

    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "policy",
                "file_name": "apolice_cyber_2025.pdf",
                "file_url": "/uploads/insurance/apolice_cyber_2025.pdf",
                "file_size": 1048576,
                "mime_type": "application/pdf"
            }
        }


class InsuranceClaimCreate(BaseModel):
    """Schema for creating an insurance claim/sinistro."""
    policy_id: str = Field(..., description="ID of the related policy")
    claim_number: str = Field(..., min_length=1, max_length=100, description="Claim number")
    incident_date: date = Field(..., description="Date the incident occurred")
    reported_date: date = Field(..., description="Date the claim was reported")
    description: str = Field(..., min_length=10, description="Description of the incident")
    estimated_loss: float = Field(..., gt=0, description="Estimated loss amount")
    claimed_amount: float = Field(..., gt=0, description="Amount claimed")
    related_incident_id: Optional[str] = Field(None, description="Related incident report ID")

    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "550e8400-e29b-41d4-a716-446655440000",
                "claim_number": "SIN-2025-001",
                "incident_date": "2025-01-15",
                "reported_date": "2025-01-16",
                "description": "Ataque ransomware resultou em criptografia de dados críticos",
                "estimated_loss": 500000.00,
                "claimed_amount": 450000.00,
                "related_incident_id": "660e8400-e29b-41d4-a716-446655440001"
            }
        }


class InsuranceClaimUpdate(BaseModel):
    """Schema for updating an insurance claim."""
    claim_number: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10)
    estimated_loss: Optional[float] = Field(None, gt=0)
    claimed_amount: Optional[float] = Field(None, gt=0)
    settled_amount: Optional[float] = Field(None, ge=0)
    status: Optional[InsuranceClaimStatusEnum] = None
    related_incident_id: Optional[str] = None


class InsuranceClaimResponse(BaseModel):
    """Response schema for insurance claim."""
    id: str
    policy_id: str
    claim_number: str
    incident_date: Optional[date] = None
    reported_date: Optional[date] = None
    description: str
    estimated_loss: Optional[float] = None
    claimed_amount: Optional[float] = None
    settled_amount: Optional[float] = None
    status: str
    related_incident_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    recovery_rate: Optional[float] = None

    class Config:
        from_attributes = True


class InsuranceClaimListResponse(BaseModel):
    """Paginated list of insurance claims."""
    claims: List[InsuranceClaimResponse]
    total: int
    limit: int
    offset: int


class CoverageStatus(BaseModel):
    """Status of a specific coverage type."""
    coverage_type: str
    covered: bool
    coverage_limit: Optional[float] = None
    policy_id: Optional[str] = None


class InsuranceCoverageChecklist(BaseModel):
    """Checklist of required BCB 498/2025 coverages."""
    coverages: List[CoverageStatus]
    total_required: int = 8
    total_covered: int
    compliance_percentage: float


class InsuranceAlert(BaseModel):
    """Alert for insurance renewal or compliance issues."""
    alert_type: str
    severity: str
    message: str
    policy_id: Optional[str] = None
    policy_number: Optional[str] = None
    days_until_expiry: Optional[int] = None
    missing_coverages: Optional[List[str]] = None
    created_at: datetime


class InsuranceAlertListResponse(BaseModel):
    """List of insurance alerts."""
    alerts: List[InsuranceAlert]
    total: int


class InsuranceDashboard(BaseModel):
    """Dashboard summary for insurance management."""
    active_policy: Optional[InsurancePolicyResponse] = None
    days_until_expiry: Optional[int] = None
    total_coverage_amount: Optional[float] = None
    total_premium: Optional[float] = None
    coverages_by_type: Dict[str, float] = {}
    coverage_gaps: List[str] = []
    pending_claims_count: int = 0
    pending_claims_amount: Optional[float] = None
    total_claims_count: int = 0
    total_settled_amount: Optional[float] = None
    compliance_status: InsuranceCoverageChecklist
