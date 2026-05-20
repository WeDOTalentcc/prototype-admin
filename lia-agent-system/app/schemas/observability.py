"""
Pydantic schemas for Observability and Governance API.
"""

from datetime import date, datetime
from enum import Enum, StrEnum
from typing import Any

from pydantic import BaseModel, Field
from app.shared.types import WeDoBaseModel


class AgentTypeEnum(StrEnum):
    """Types of AI agents."""
    SCREENING = "screening"
    SCORING = "scoring"
    INTERVIEW = "interview"
    MATCHING = "matching"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class DataOperationTypeEnum(StrEnum):
    """Types of data operations."""
    VIEW = "view"
    EXPORT = "export"
    DELETE = "delete"
    UPDATE = "update"
    CREATE = "create"
    ANONYMIZE = "anonymize"


class DataTypeEnum(StrEnum):
    """Types of data accessed."""
    CV = "cv"
    SCORE = "score"
    PARECER = "parecer"
    PERSONAL_INFO = "personal_info"
    CONTACT_INFO = "contact_info"
    INTERVIEW_NOTES = "interview_notes"
    ASSESSMENT_RESULTS = "assessment_results"


class ConsentTypeEnum(StrEnum):
    """Types of consent."""
    DATA_PROCESSING = "data_processing"
    AI_SCORING = "ai_scoring"
    MARKETING = "marketing"
    DATA_SHARING = "data_sharing"
    AUTOMATED_DECISION = "automated_decision"
    PROFILE_ENRICHMENT = "profile_enrichment"


class LegalBasisEnum(StrEnum):
    """LGPD legal bases."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    PUBLIC_INTEREST = "public_interest"
    VITAL_INTEREST = "vital_interest"


class IncidentTypeEnum(StrEnum):
    """Types of incidents."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_FAILURE = "system_failure"
    BIAS_DETECTED = "bias_detected"
    SLA_VIOLATION = "sla_violation"
    POLICY_VIOLATION = "policy_violation"
    PRIVACY_VIOLATION = "privacy_violation"


class IncidentSeverityEnum(StrEnum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatusEnum(StrEnum):
    """Incident status options."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvaluationTypeEnum(StrEnum):
    """Types of model evaluations."""
    BIAS_CHECK = "bias_check"
    FAIRNESS_AUDIT = "fairness_audit"
    ACCURACY_TEST = "accuracy_test"
    CALIBRATION_CHECK = "calibration_check"
    DRIFT_DETECTION = "drift_detection"


class EvaluationDimensionEnum(StrEnum):
    """Dimensions for bias/fairness evaluation - Tezi AI 11 categories."""
    SEX_BIAS = "sex_bias"
    RACE_ETHNICITY_BIAS = "race_ethnicity_bias"
    AGE_BIAS = "age_bias"
    DISABILITY_BIAS = "disability_bias"
    RELIGION_BIAS = "religion_bias"
    SEXUAL_ORIENTATION_BIAS = "sexual_orientation_bias"
    VETERAN_STATUS_BIAS = "veteran_status_bias"
    LANGUAGE_PROFICIENCY_BIAS = "language_proficiency_bias"
    PREGNANCY_STATUS_BIAS = "pregnancy_status_bias"
    NATIONAL_ORIGIN_BIAS = "national_origin_bias"
    INTERSECTIONAL_BIAS = "intersectional_bias"


class BiasAuditTypeEnum(StrEnum):
    """Types of bias audits."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


class AuditorTypeEnum(StrEnum):
    """Types of auditors."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    THIRD_PARTY = "third_party"


class BiasStatusEnum(StrEnum):
    """Status levels for bias results."""
    CLEAR = "clear"
    CONSIDER = "consider"
    CONCERN = "concern"


class BiasComplianceFrameworkEnum(StrEnum):
    """Compliance frameworks for bias auditing."""
    NYC_LL144 = "NYC_LL144"
    CO_SB205 = "CO_SB205"
    EU_AI_ACT = "EU_AI_ACT"
    CA_FEHA = "CA_FEHA"
    LGPD_BRAZIL = "LGPD_BRAZIL"


class ComplianceFrameworkEnum(StrEnum):
    """Compliance frameworks."""
    ISO27001 = "ISO27001"
    SOC2 = "SOC2"
    LGPD = "LGPD"
    GDPR = "GDPR"
    AI_ETHICS = "AI_ETHICS"


class ControlStatusEnum(StrEnum):
    """Status of compliance controls."""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"


class AIInferenceLogResponse(BaseModel):
    """Response schema for AI inference log."""
    id: str
    company_id: str
    agent_type: str
    candidate_id: str | None = None
    vacancy_id: str | None = None
    model_version: str | None = None
    decision_type: str | None = None
    confidence_score: float | None = None
    latency_ms: int | None = None
    tokens_used: int | None = None
    human_override: bool = False
    feature_attributions: dict[str, Any] = {}
    bias_flags: list[Any] = []
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class AIInferenceLogListResponse(BaseModel):
    """Paginated list of AI inference logs."""
    logs: list[AIInferenceLogResponse]
    total: int
    limit: int
    offset: int


class AIInferenceStatsResponse(BaseModel):
    """Statistics for AI inference logs."""
    total_inferences: int
    by_agent_type: dict[str, int]
    by_decision_type: dict[str, int]
    avg_latency_ms: float | None = None
    avg_confidence: float | None = None
    total_tokens_used: int
    human_override_count: int
    human_override_rate: float
    bias_flags_count: int


class DataAccessLogResponse(BaseModel):
    """Response schema for data access log."""
    id: str
    company_id: str
    user_id: str
    data_subject_id: str | None = None
    data_type: str
    operation: str
    pii_fields: list[str] = []
    purpose: str | None = None
    legal_basis: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DataAccessLogListResponse(BaseModel):
    """Paginated list of data access logs."""
    logs: list[DataAccessLogResponse]
    total: int
    limit: int
    offset: int


class DataAccessStatsResponse(BaseModel):
    """Statistics for data access logs."""
    total_accesses: int
    by_data_type: dict[str, int]
    by_operation: dict[str, int]
    by_legal_basis: dict[str, int]
    unique_users: int
    unique_data_subjects: int


class ConsentRecordResponse(BaseModel):
    """Response schema for consent record."""
    id: str
    company_id: str
    candidate_id: str
    consent_type: str
    version: str | None = None
    granted_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    is_active: bool = True
    source: str | None = None
    legal_basis: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ConsentRecordListResponse(BaseModel):
    """Paginated list of consent records."""
    consents: list[ConsentRecordResponse]
    total: int
    limit: int
    offset: int


class ConsentCreate(WeDoBaseModel):
    """Schema for creating a consent record."""
    candidate_id: str = Field(..., description="Candidate ID")
    consent_type: str = Field(..., description="Type of consent")
    version: str | None = Field(None, description="Consent version")
    expires_at: datetime | None = Field(None, description="Expiration date")
    ip_address: str | None = Field(None, description="IP address")
    source: str | None = Field(None, description="Source of consent")
    legal_basis: str | None = Field(None, description="Legal basis")
    consent_text: str | None = Field(None, description="Consent text shown")

    class Config:
        json_schema_extra = {
            "example": {
                "candidate_id": "550e8400-e29b-41d4-a716-446655440000",
                "consent_type": "data_processing",
                "version": "1.0",
                "source": "web_form",
                "legal_basis": "consent"
            }
        }


class ConsentRevoke(BaseModel):
    """Schema for revoking consent."""
    reason: str | None = Field(None, description="Reason for revocation")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Candidate requested data deletion"
            }
        }


class IncidentReportResponse(BaseModel):
    """Response schema for incident report."""
    id: str
    company_id: str | None = None
    incident_type: str
    severity: str
    description: str
    affected_resources: list[Any] = []
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    root_cause: str | None = None
    remediation_actions: list[str] = []
    notified_parties: list[str] = []
    status: str = "open"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class IncidentReportListResponse(BaseModel):
    """Paginated list of incident reports."""
    incidents: list[IncidentReportResponse]
    total: int
    limit: int
    offset: int


class IncidentCreate(WeDoBaseModel):
    """Schema for creating an incident."""
    incident_type: str = Field(..., description="Type of incident")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Incident description")
    affected_resources: list[dict[str, Any]] | None = Field(default=[], description="Affected resources")
    detected_at: datetime | None = Field(None, description="When incident was detected")

    class Config:
        json_schema_extra = {
            "example": {
                "incident_type": "bias_detected",
                "severity": "medium",
                "description": "Bias detected in scoring model for age dimension",
                "affected_resources": [{"type": "model", "id": "scoring-v2"}],
                "detected_at": "2024-01-15T10:30:00Z"
            }
        }


class IncidentUpdate(WeDoBaseModel):
    """Schema for updating an incident."""
    severity: str | None = Field(None, description="Severity level")
    description: str | None = Field(None, description="Incident description")
    root_cause: str | None = Field(None, description="Root cause analysis")
    remediation_actions: list[str] | None = Field(None, description="Actions taken")
    notified_parties: list[str] | None = Field(None, description="Parties notified")
    status: str | None = Field(None, description="Incident status")
    assigned_to: str | None = Field(None, description="Assigned user ID")


class IncidentResolve(BaseModel):
    """Schema for resolving an incident."""
    root_cause: str | None = Field(None, description="Root cause")
    remediation_actions: list[str] | None = Field(None, description="Actions taken")
    resolution_notes: str | None = Field(None, description="Resolution notes")

    class Config:
        json_schema_extra = {
            "example": {
                "root_cause": "Training data imbalance",
                "remediation_actions": ["Retrained model with balanced data", "Added bias monitoring"],
                "resolution_notes": "Model retrained and validated"
            }
        }


class ModelEvaluationResponse(BaseModel):
    """Response schema for model evaluation."""
    id: str
    company_id: str | None = None
    model_version: str
    evaluation_type: str
    dimension: str | None = None
    metric_name: str
    metric_value: float | None = None
    threshold: float | None = None
    passed: bool | None = None
    sample_size: int | None = None
    evaluation_date: date | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ModelEvaluationListResponse(BaseModel):
    """Paginated list of model evaluations."""
    evaluations: list[ModelEvaluationResponse]
    total: int
    limit: int
    offset: int


class ModelEvaluationSummaryResponse(BaseModel):
    """Summary of model evaluations by dimension."""
    total_evaluations: int
    by_dimension: dict[str, dict[str, Any]]
    by_evaluation_type: dict[str, int]
    pass_rate: float
    latest_evaluation_date: date | None = None


class ComplianceControlResponse(BaseModel):
    """Response schema for compliance control."""
    id: str
    company_id: str | None = None
    framework: str
    control_id: str
    control_name: str
    description: str | None = None
    status: str
    evidence_url: str | None = None
    last_reviewed_at: datetime | None = None
    next_review_at: datetime | None = None
    owner: str | None = None
    risk_level: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ComplianceControlListResponse(BaseModel):
    """Paginated list of compliance controls."""
    controls: list[ComplianceControlResponse]
    total: int
    limit: int
    offset: int


class ComplianceSummaryResponse(BaseModel):
    """Summary of compliance controls by framework."""
    total_controls: int
    by_framework: dict[str, dict[str, int]]
    by_status: dict[str, int]
    overdue_reviews: int
    upcoming_reviews: int


class ComplianceControlUpdate(WeDoBaseModel):
    """Schema for updating a compliance control."""
    status: str | None = Field(None, description="Control status")
    evidence_url: str | None = Field(None, description="Evidence URL")
    evidence_notes: str | None = Field(None, description="Evidence notes")
    owner: str | None = Field(None, description="Control owner")
    owner_email: str | None = Field(None, description="Owner email")
    next_review_at: datetime | None = Field(None, description="Next review date")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "implemented",
                "evidence_url": "https://docs.example.com/evidence/control-123",
                "owner": "Security Team"
            }
        }


class ObservabilityDashboardResponse(BaseModel):
    """Consolidated dashboard data for observability."""
    ai_inference: dict[str, Any]
    data_access: dict[str, Any]
    consents: dict[str, Any]
    incidents: dict[str, Any]
    evaluations: dict[str, Any]
    compliance: dict[str, Any]
    alerts: list[dict[str, Any]]


class BiasResultItem(BaseModel):
    """Individual bias result for a category."""
    score: float = Field(..., ge=0, le=1, description="Bias score (0-1)")
    status: BiasStatusEnum = Field(..., description="Status: clear/consider/concern")
    details: str | None = Field(None, description="Details about the bias analysis")


class BiasAuditReportResponse(BaseModel):
    """Response schema for bias audit report."""
    id: str
    company_id: str
    audit_type: str
    audit_date: date | None = None
    sample_size: int | None = None
    auditor: str
    auditor_name: str | None = None
    auditor_organization: str | None = None
    bias_results: dict[str, Any] = {}
    overall_score: float | None = None
    clear_count: int = 0
    consider_count: int = 0
    concern_count: int = 0
    compliance_frameworks: list[str] = []
    report_url: str | None = None
    is_public: bool = False
    notes: str | None = None
    recommendations: list[str] = []
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class BiasAuditReportListResponse(BaseModel):
    """Paginated list of bias audit reports."""
    audits: list[BiasAuditReportResponse]
    total: int
    limit: int
    offset: int


class BiasAuditCreate(WeDoBaseModel):
    """Schema for creating a bias audit report."""
    audit_type: str = Field(..., description="Type of audit: monthly/quarterly/annual/on_demand")
    audit_date: date = Field(..., description="Date of the audit")
    sample_size: int | None = Field(None, description="Number of candidates/decisions analyzed")
    auditor: str = Field(..., description="Type of auditor: internal/external/third_party")
    auditor_name: str | None = Field(None, description="Name of the auditor")
    auditor_organization: str | None = Field(None, description="Organization of the auditor")
    bias_results: dict[str, Any] = Field(default_factory=dict, description="Results for all 11 bias categories")
    overall_score: float | None = Field(None, ge=0, le=100, description="Overall bias score (0-100)")
    compliance_frameworks: list[str] | None = Field(default=[], description="Applicable compliance frameworks")
    report_url: str | None = Field(None, description="URL to full audit report")
    notes: str | None = Field(None, description="Additional notes")
    recommendations: list[str] | None = Field(default=[], description="Audit recommendations")

    class Config:
        json_schema_extra = {
            "example": {
                "audit_type": "quarterly",
                "audit_date": "2024-12-15",
                "sample_size": 1500,
                "auditor": "third_party",
                "auditor_name": "Jane Doe",
                "auditor_organization": "Bias Auditors Inc.",
                "bias_results": {
                    "sex_bias": {"score": 0.02, "status": "clear", "details": "No significant bias detected"},
                    "race_ethnicity_bias": {"score": 0.03, "status": "clear", "details": "Within acceptable range"},
                    "age_bias": {"score": 0.08, "status": "consider", "details": "Minor age-related patterns observed"},
                    "disability_bias": {"score": 0.01, "status": "clear", "details": "No bias detected"},
                    "religion_bias": {"score": 0.02, "status": "clear", "details": "No bias detected"},
                    "sexual_orientation_bias": {"score": 0.01, "status": "clear", "details": "No bias detected"},
                    "veteran_status_bias": {"score": 0.01, "status": "clear", "details": "N/A for Brazil"},
                    "language_proficiency_bias": {"score": 0.05, "status": "clear", "details": "Within acceptable range"},
                    "pregnancy_status_bias": {"score": 0.02, "status": "clear", "details": "No bias detected"},
                    "national_origin_bias": {"score": 0.03, "status": "clear", "details": "No bias detected"},
                    "intersectional_bias": {"score": 0.04, "status": "clear", "details": "No intersectional patterns"}
                },
                "overall_score": 95.5,
                "compliance_frameworks": ["NYC_LL144", "LGPD_BRAZIL"],
                "recommendations": ["Continue monitoring age-related patterns", "Increase sample diversity"]
            }
        }


class BiasAuditPublish(BaseModel):
    """Schema for publishing a bias audit."""
    is_public: bool = Field(True, description="Whether to make the audit public")
    report_url: str | None = Field(None, description="URL to the public report")

    class Config:
        json_schema_extra = {
            "example": {
                "is_public": True,
                "report_url": "https://company.com/bias-audit-q4-2024"
            }
        }


class BiasAuditSummaryResponse(BaseModel):
    """Summary of bias audit reports."""
    total_audits: int
    latest_audit_date: date | None = None
    latest_overall_score: float | None = None
    by_audit_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    compliance_coverage: list[str] = []
    public_audits_count: int = 0
