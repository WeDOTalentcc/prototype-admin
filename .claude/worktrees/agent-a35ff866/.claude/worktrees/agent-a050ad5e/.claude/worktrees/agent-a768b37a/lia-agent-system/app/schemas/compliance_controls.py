"""
Pydantic schemas for Compliance Controls API.

Includes schemas for:
- Control Library (ISO 27001, SOC 2, SOX, etc.)
- Company Compliance Controls
- Compliance Audits
- SOX Controls
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ComplianceFrameworkTypeEnum(str, Enum):
    """Compliance frameworks for control inventory."""
    ISO_27001 = "ISO_27001"
    SOC_2_TYPE_I = "SOC_2_TYPE_I"
    SOC_2_TYPE_II = "SOC_2_TYPE_II"
    SOX = "SOX"
    LGPD = "LGPD"
    GDPR = "GDPR"
    BACEN_4893 = "BACEN_4893"
    PCI_DSS = "PCI_DSS"


class CompanyControlStatusEnum(str, Enum):
    """Status of company's control implementation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NOT_APPLICABLE = "not_applicable"


class AuditResultTypeEnum(str, Enum):
    """Audit result types."""
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class AuditTypeEnum(str, Enum):
    """Types of compliance audits."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    CERTIFICATION = "certification"


class SOXSectionEnum(str, Enum):
    """SOX sections relevant to HR/Payroll."""
    SECTION_302 = "302"
    SECTION_404 = "404"
    SECTION_409 = "409"
    SECTION_802 = "802"


class SOXTestResultEnum(str, Enum):
    """SOX control test result."""
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    NOT_TESTED = "not_tested"


class SOXControlFrequencyEnum(str, Enum):
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
    control_description: Optional[str] = None
    control_category: Optional[str] = None
    domain: Optional[str] = None
    is_mandatory: bool = True
    implementation_guidance: Optional[str] = None
    evidence_requirements: List[str] = []
    related_controls: List[str] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ControlLibraryListResponse(BaseModel):
    """Paginated list of control library entries."""
    controls: List[ControlLibraryResponse]
    total: int
    limit: int
    offset: int


class ControlLibraryCreate(BaseModel):
    """Schema for creating a control library entry."""
    framework: str = Field(..., description="Compliance framework (ISO_27001, SOC_2_TYPE_II, etc.)")
    control_id: str = Field(..., description="Control ID (e.g., A.5.1, CC6.1)")
    control_name: str = Field(..., description="Control name")
    control_description: Optional[str] = Field(None, description="Control description")
    control_category: Optional[str] = Field(None, description="Category (e.g., Access Control)")
    domain: Optional[str] = Field(None, description="Domain/area")
    is_mandatory: bool = Field(True, description="Whether control is mandatory")
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    evidence_requirements: Optional[List[str]] = Field(default=[], description="Required evidence")
    related_controls: Optional[List[str]] = Field(default=[], description="Related control IDs")


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
    implementation_date: Optional[date] = None
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    notes: Optional[str] = None
    evidence_files: List[Dict[str, Any]] = []
    effectiveness_rating: Optional[int] = None
    auditor_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    control: Optional[ControlLibraryResponse] = None

    class Config:
        from_attributes = True


class CompanyControlListResponse(BaseModel):
    """Paginated list of company compliance controls."""
    controls: List[CompanyControlResponse]
    total: int
    limit: int
    offset: int


class CompanyControlCreate(BaseModel):
    """Schema for creating a company compliance control."""
    control_library_id: str = Field(..., description="Control library ID")
    status: Optional[str] = Field("not_started", description="Implementation status")
    owner_name: Optional[str] = Field(None, description="Control owner name")
    owner_email: Optional[str] = Field(None, description="Control owner email")
    notes: Optional[str] = Field(None, description="Implementation notes")


class CompanyControlUpdate(BaseModel):
    """Schema for updating a company compliance control."""
    status: Optional[str] = Field(None, description="Implementation status")
    implementation_date: Optional[date] = Field(None, description="Implementation date")
    last_review_date: Optional[date] = Field(None, description="Last review date")
    next_review_date: Optional[date] = Field(None, description="Next review date")
    owner_name: Optional[str] = Field(None, description="Control owner name")
    owner_email: Optional[str] = Field(None, description="Control owner email")
    notes: Optional[str] = Field(None, description="Implementation notes")
    effectiveness_rating: Optional[int] = Field(None, ge=0, le=100, description="Effectiveness rating (0-100)")
    auditor_notes: Optional[str] = Field(None, description="Auditor notes")


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
    auditor_organization: Optional[str] = None
    auditor_name: Optional[str] = None
    audit_start_date: Optional[date] = None
    audit_end_date: Optional[date] = None
    scope_description: Optional[str] = None
    findings_count: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    overall_result: Optional[str] = None
    certificate_url: Optional[str] = None
    report_url: Optional[str] = None
    valid_until: Optional[date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceAuditListResponse(BaseModel):
    """Paginated list of compliance audits."""
    audits: List[ComplianceAuditResponse]
    total: int
    limit: int
    offset: int


class ComplianceAuditCreate(BaseModel):
    """Schema for creating a compliance audit."""
    framework: str = Field(..., description="Compliance framework")
    audit_type: str = Field(..., description="Audit type (internal/external/certification)")
    auditor_organization: Optional[str] = Field(None, description="Auditor organization")
    auditor_name: Optional[str] = Field(None, description="Auditor name")
    audit_start_date: Optional[date] = Field(None, description="Audit start date")
    audit_end_date: Optional[date] = Field(None, description="Audit end date")
    scope_description: Optional[str] = Field(None, description="Audit scope")


class ComplianceAuditUpdate(BaseModel):
    """Schema for updating a compliance audit."""
    auditor_organization: Optional[str] = None
    auditor_name: Optional[str] = None
    audit_end_date: Optional[date] = None
    scope_description: Optional[str] = None
    findings_count: Optional[int] = None
    critical_findings: Optional[int] = None
    high_findings: Optional[int] = None
    medium_findings: Optional[int] = None
    low_findings: Optional[int] = None
    overall_result: Optional[str] = None
    certificate_url: Optional[str] = None
    report_url: Optional[str] = None
    valid_until: Optional[date] = None


class SOXControlResponse(BaseModel):
    """Response schema for SOX control."""
    id: str
    company_id: str
    section: str
    control_id: str
    control_name: str
    control_objective: Optional[str] = None
    key_control: bool = False
    frequency: Optional[str] = None
    control_owner: Optional[str] = None
    last_test_date: Optional[date] = None
    test_result: str = "not_tested"
    test_evidence: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_due_date: Optional[date] = None
    segregation_of_duties_verified: bool = False
    audit_trail_enabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SOXControlListResponse(BaseModel):
    """Paginated list of SOX controls."""
    controls: List[SOXControlResponse]
    total: int
    limit: int
    offset: int


class SOXControlCreate(BaseModel):
    """Schema for creating a SOX control."""
    section: str = Field(..., description="SOX section (302/404/409/802)")
    control_id: str = Field(..., description="Control ID")
    control_name: str = Field(..., description="Control name")
    control_objective: Optional[str] = Field(None, description="Control objective")
    key_control: bool = Field(False, description="Is key control")
    frequency: Optional[str] = Field(None, description="Frequency (daily/weekly/monthly/quarterly/annual)")
    control_owner: Optional[str] = Field(None, description="Control owner")


class SOXControlUpdate(BaseModel):
    """Schema for updating a SOX control."""
    control_objective: Optional[str] = None
    key_control: Optional[bool] = None
    frequency: Optional[str] = None
    control_owner: Optional[str] = None
    last_test_date: Optional[date] = None
    test_result: Optional[str] = None
    test_evidence: Optional[str] = None
    remediation_plan: Optional[str] = None
    remediation_due_date: Optional[date] = None
    segregation_of_duties_verified: Optional[bool] = None
    audit_trail_enabled: Optional[bool] = None


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
    by_framework: Dict[str, FrameworkStats] = {}
    total_controls: int = 0
    total_implemented: int = 0
    overall_compliance_percentage: float = 0.0
    upcoming_reviews: int = 0
    overdue_reviews: int = 0
    recent_audits: List[ComplianceAuditResponse] = []
    sox_summary: Optional[Dict[str, Any]] = None


class SeedDataResponse(BaseModel):
    """Response from seeding control data."""
    message: str
    iso_27001_controls: int = 0
    soc_2_controls: int = 0
    sox_controls: int = 0
    total_controls: int = 0
