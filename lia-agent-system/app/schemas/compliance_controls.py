"""
Pydantic schemas for Compliance Controls API.

Includes schemas for:
- Control Library (ISO 27001, SOC 2, SOX, etc.)
- Company Compliance Controls
- Compliance Audits
- SOX Controls
"""

from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class ComplianceFrameworkTypeEnum(StrEnum):
    """Compliance frameworks for control inventory."""
    ISO_27001 = "ISO_27001"
    SOC_2_TYPE_I = "SOC_2_TYPE_I"
    SOC_2_TYPE_II = "SOC_2_TYPE_II"
    SOX = "SOX"
    LGPD = "LGPD"
    GDPR = "GDPR"
    BACEN_4893 = "BACEN_4893"
    PCI_DSS = "PCI_DSS"


class CompanyControlStatusEnum(StrEnum):
    """Status of company's control implementation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NOT_APPLICABLE = "not_applicable"


class AuditResultTypeEnum(StrEnum):
    """Audit result types."""
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class AuditTypeEnum(StrEnum):
    """Types of compliance audits."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    CERTIFICATION = "certification"


class SOXSectionEnum(StrEnum):
    """SOX sections relevant to HR/Payroll."""
    SECTION_302 = "302"
    SECTION_404 = "404"
    SECTION_409 = "409"
    SECTION_802 = "802"


class SOXTestResultEnum(StrEnum):
    """SOX control test result."""
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    NOT_TESTED = "not_tested"


class SOXControlFrequencyEnum(StrEnum):
    """Frequency of SOX control execution."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ControlLibraryResponse(BaseModel):
    """Response schema for control library entry."""
    id: str
    framework: str
    control_id: str
    control_name: str
    control_description: str | None = None
    control_category: str | None = None
    domain: str | None = None
    is_mandatory: bool = True
    implementation_guidance: str | None = None
    evidence_requirements: list[str] = []
    related_controls: list[str] = []
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ControlLibraryListResponse(BaseModel):
    """Paginated list of control library entries."""
    controls: list[ControlLibraryResponse]
    total: int
    limit: int
    offset: int


class ControlLibraryCreate(WeDoBaseModel):
    """Schema for creating a control library entry."""
    framework: str = Field(..., description="Compliance framework (ISO_27001, SOC_2_TYPE_II, etc.)")
    control_id: str = Field(..., description="Control ID (e.g., A.5.1, CC6.1)")
    control_name: str = Field(..., description="Control name")
    control_description: str | None = Field(None, description="Control description")
    control_category: str | None = Field(None, description="Category (e.g., Access Control)")
    domain: str | None = Field(None, description="Domain/area")
    is_mandatory: bool = Field(True, description="Whether control is mandatory")
    implementation_guidance: str | None = Field(None, description="Implementation guidance")
    evidence_requirements: list[str] | None = Field(default=[], description="Required evidence")
    related_controls: list[str] | None = Field(default=[], description="Related control IDs")


class EvidenceFile(BaseModel):
    """Schema for evidence file."""
    filename: str
    url: str
    uploaded_at: datetime


class CompanyControlResponse(BaseModel):
    """Response schema for company compliance control."""
    id: str
    company_id: str
    control_library_id: str
    status: str
    implementation_date: date | None = None
    last_review_date: date | None = None
    next_review_date: date | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    notes: str | None = None
    evidence_files: list[dict[str, Any]] = []
    effectiveness_rating: int | None = None
    auditor_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    control: ControlLibraryResponse | None = None

    class Config:
        from_attributes = True


class CompanyControlListResponse(BaseModel):
    """Paginated list of company compliance controls."""
    controls: list[CompanyControlResponse]
    total: int
    limit: int
    offset: int


class CompanyControlCreate(WeDoBaseModel):
    """Schema for creating a company compliance control."""
    control_library_id: str = Field(..., description="Control library ID")
    status: str | None = Field("not_started", description="Implementation status")
    owner_name: str | None = Field(None, description="Control owner name")
    owner_email: str | None = Field(None, description="Control owner email")
    notes: str | None = Field(None, description="Implementation notes")


class CompanyControlUpdate(WeDoBaseModel):
    """Schema for updating a company compliance control."""
    status: str | None = Field(None, description="Implementation status")
    implementation_date: date | None = Field(None, description="Implementation date")
    last_review_date: date | None = Field(None, description="Last review date")
    next_review_date: date | None = Field(None, description="Next review date")
    owner_name: str | None = Field(None, description="Control owner name")
    owner_email: str | None = Field(None, description="Control owner email")
    notes: str | None = Field(None, description="Implementation notes")
    effectiveness_rating: int | None = Field(None, ge=0, le=100, description="Effectiveness rating (0-100)")
    auditor_notes: str | None = Field(None, description="Auditor notes")


class EvidenceUpload(BaseModel):
    """Schema for uploading evidence."""
    filename: str = Field(..., description="File name")
    url: str = Field(..., description="URL to the evidence file")


class ComplianceAuditResponse(BaseModel):
    """Response schema for compliance audit."""
    id: str
    company_id: str
    framework: str
    audit_type: str
    auditor_organization: str | None = None
    auditor_name: str | None = None
    audit_start_date: date | None = None
    audit_end_date: date | None = None
    scope_description: str | None = None
    findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    overall_result: str | None = None
    certificate_url: str | None = None
    report_url: str | None = None
    valid_until: date | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ComplianceAuditListResponse(BaseModel):
    """Paginated list of compliance audits."""
    audits: list[ComplianceAuditResponse]
    total: int
    limit: int
    offset: int


class ComplianceAuditCreate(WeDoBaseModel):
    """Schema for creating a compliance audit."""
    framework: str = Field(..., description="Compliance framework")
    audit_type: str = Field(..., description="Audit type (internal/external/certification)")
    auditor_organization: str | None = Field(None, description="Auditor organization")
    auditor_name: str | None = Field(None, description="Auditor name")
    audit_start_date: date | None = Field(None, description="Audit start date")
    audit_end_date: date | None = Field(None, description="Audit end date")
    scope_description: str | None = Field(None, description="Audit scope")


class ComplianceAuditUpdate(WeDoBaseModel):
    """Schema for updating a compliance audit."""
    auditor_organization: str | None = None
    auditor_name: str | None = None
    audit_end_date: date | None = None
    scope_description: str | None = None
    findings_count: int | None = None
    critical_findings: int | None = None
    high_findings: int | None = None
    medium_findings: int | None = None
    low_findings: int | None = None
    overall_result: str | None = None
    certificate_url: str | None = None
    report_url: str | None = None
    valid_until: date | None = None


class SOXControlResponse(BaseModel):
    """Response schema for SOX control."""
    id: str
    company_id: str
    section: str
    control_id: str
    control_name: str
    control_objective: str | None = None
    key_control: bool = False
    frequency: str | None = None
    control_owner: str | None = None
    last_test_date: date | None = None
    test_result: str = "not_tested"
    test_evidence: str | None = None
    remediation_plan: str | None = None
    remediation_due_date: date | None = None
    segregation_of_duties_verified: bool = False
    audit_trail_enabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class SOXControlListResponse(BaseModel):
    """Paginated list of SOX controls."""
    controls: list[SOXControlResponse]
    total: int
    limit: int
    offset: int


class SOXControlCreate(WeDoBaseModel):
    """Schema for creating a SOX control."""
    section: str = Field(..., description="SOX section (302/404/409/802)")
    control_id: str = Field(..., description="Control ID")
    control_name: str = Field(..., description="Control name")
    control_objective: str | None = Field(None, description="Control objective")
    key_control: bool = Field(False, description="Is key control")
    frequency: str | None = Field(None, description="Frequency (daily/weekly/monthly/quarterly/annual)")
    control_owner: str | None = Field(None, description="Control owner")


class SOXControlUpdate(WeDoBaseModel):
    """Schema for updating a SOX control."""
    control_objective: str | None = None
    key_control: bool | None = None
    frequency: str | None = None
    control_owner: str | None = None
    last_test_date: date | None = None
    test_result: str | None = None
    test_evidence: str | None = None
    remediation_plan: str | None = None
    remediation_due_date: date | None = None
    segregation_of_duties_verified: bool | None = None
    audit_trail_enabled: bool | None = None


class FrameworkStats(BaseModel):
    """Statistics for a single framework."""
    total_controls: int = 0
    implemented: int = 0
    in_progress: int = 0
    not_started: int = 0
    verified: int = 0
    not_applicable: int = 0
    compliance_percentage: float = 0.0


class ComplianceDashboardResponse(BaseModel):
    """Dashboard response with all frameworks status."""
    by_framework: dict[str, FrameworkStats] = {}
    total_controls: int = 0
    total_implemented: int = 0
    overall_compliance_percentage: float = 0.0
    upcoming_reviews: int = 0
    overdue_reviews: int = 0
    recent_audits: list[ComplianceAuditResponse] = []
    sox_summary: dict[str, Any] | None = None


class SeedDataResponse(BaseModel):
    """Response from seeding control data."""
    message: str
    iso_27001_controls: int = 0
    soc_2_controls: int = 0
    sox_controls: int = 0
    total_controls: int = 0
