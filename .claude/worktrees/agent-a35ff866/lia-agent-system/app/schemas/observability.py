"""
Pydantic schemas for Observability and Governance API.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class AgentTypeEnum(str, Enum):
    """Types of AI agents."""
    SCREENING = "screening"
    SCORING = "scoring"
    INTERVIEW = "interview"
    MATCHING = "matching"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class DataOperationTypeEnum(str, Enum):
    """Types of data operations."""
    VIEW = "view"
    EXPORT = "export"
    DELETE = "delete"
    UPDATE = "update"
    CREATE = "create"
    ANONYMIZE = "anonymize"


class DataTypeEnum(str, Enum):
    """Types of data accessed."""
    CV = "cv"
    SCORE = "score"
    PARECER = "parecer"
    PERSONAL_INFO = "personal_info"
    CONTACT_INFO = "contact_info"
    INTERVIEW_NOTES = "interview_notes"
    ASSESSMENT_RESULTS = "assessment_results"


class ConsentTypeEnum(str, Enum):
    """Types of consent."""
    DATA_PROCESSING = "data_processing"
    AI_SCORING = "ai_scoring"
    MARKETING = "marketing"
    DATA_SHARING = "data_sharing"
    AUTOMATED_DECISION = "automated_decision"
    PROFILE_ENRICHMENT = "profile_enrichment"


class LegalBasisEnum(str, Enum):
    """LGPD legal bases."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    PUBLIC_INTEREST = "public_interest"
    VITAL_INTEREST = "vital_interest"


class IncidentTypeEnum(str, Enum):
    """Types of incidents."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_FAILURE = "system_failure"
    BIAS_DETECTED = "bias_detected"
    SLA_VIOLATION = "sla_violation"
    POLICY_VIOLATION = "policy_violation"
    PRIVACY_VIOLATION = "privacy_violation"


class IncidentSeverityEnum(str, Enum):
    """Severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatusEnum(str, Enum):
    """Incident status options."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvaluationTypeEnum(str, Enum):
    """Types of model evaluations."""
    BIAS_CHECK = "bias_check"
    FAIRNESS_AUDIT = "fairness_audit"
    ACCURACY_TEST = "accuracy_test"
    CALIBRATION_CHECK = "calibration_check"
    DRIFT_DETECTION = "drift_detection"


class EvaluationDimensionEnum(str, Enum):
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


class BiasAuditTypeEnum(str, Enum):
    """Types of bias audits."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


class AuditorTypeEnum(str, Enum):
    """Types of auditors."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    THIRD_PARTY = "third_party"


class BiasStatusEnum(str, Enum):
    """Status levels for bias results."""
    CLEAR = "clear"
    CONSIDER = "consider"
    CONCERN = "concern"


class BiasComplianceFrameworkEnum(str, Enum):
    """Compliance frameworks for bias auditing."""
    NYC_LL144 = "NYC_LL144"
    CO_SB205 = "CO_SB205"
    EU_AI_ACT = "EU_AI_ACT"
    CA_FEHA = "CA_FEHA"
    LGPD_BRAZIL = "LGPD_BRAZIL"


class ComplianceFrameworkEnum(str, Enum):
    """Compliance frameworks."""
    ISO27001 = "ISO27001"
    SOC2 = "SOC2"
    LGPD = "LGPD"
    GDPR = "GDPR"
    AI_ETHICS = "AI_ETHICS"


class ControlStatusEnum(str, Enum):
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
    candidate_id: Optional[str] = None
    vacancy_id: Optional[str] = None
    model_version: Optional[str] = None
    decision_type: Optional[str] = None
    confidence_score: Optional[float] = None
    latency_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    human_override: bool = False
    feature_attributions: Dict[str, Any] = {}
    bias_flags: List[Any] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AIInferenceLogListResponse(BaseModel):
    """Paginated list of AI inference logs."""
    logs: List[AIInferenceLogResponse]
    total: int
    limit: int
    offset: int


class AIInferenceStatsResponse(BaseModel):
    """Statistics for AI inference logs."""
    total_inferences: int
    by_agent_type: Dict[str, int]
    by_decision_type: Dict[str, int]
    avg_latency_ms: Optional[float] = None
    avg_confidence: Optional[float] = None
    total_tokens_used: int
    human_override_count: int
    human_override_rate: float
    bias_flags_count: int


class DataAccessLogResponse(BaseModel):
    """Response schema for data access log."""
    id: str
    company_id: str
    user_id: str
    data_subject_id: Optional[str] = None
    data_type: str
    operation: str
    pii_fields: List[str] = []
    purpose: Optional[str] = None
    legal_basis: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DataAccessLogListResponse(BaseModel):
    """Paginated list of data access logs."""
    logs: List[DataAccessLogResponse]
    total: int
    limit: int
    offset: int


class DataAccessStatsResponse(BaseModel):
    """Statistics for data access logs."""
    total_accesses: int
    by_data_type: Dict[str, int]
    by_operation: Dict[str, int]
    by_legal_basis: Dict[str, int]
    unique_users: int
    unique_data_subjects: int


class ConsentRecordResponse(BaseModel):
    """Response schema for consent record."""
    id: str
    company_id: str
    candidate_id: str
    consent_type: str
    version: Optional[str] = None
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_active: bool = True
    source: Optional[str] = None
    legal_basis: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConsentRecordListResponse(BaseModel):
    """Paginated list of consent records."""
    consents: List[ConsentRecordResponse]
    total: int
    limit: int
    offset: int


class ConsentCreate(BaseModel):
    """Schema for creating a consent record."""
    candidate_id: str = Field(..., description="Candidate ID")
    consent_type: str = Field(..., description="Type of consent")
    version: Optional[str] = Field(None, description="Consent version")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    ip_address: Optional[str] = Field(None, description="IP address")
    source: Optional[str] = Field(None, description="Source of consent")
    legal_basis: Optional[str] = Field(None, description="Legal basis")
    consent_text: Optional[str] = Field(None, description="Consent text shown")

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
    reason: Optional[str] = Field(None, description="Reason for revocation")

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Candidate requested data deletion"
            }
        }


class IncidentReportResponse(BaseModel):
    """Response schema for incident report."""
    id: str
    company_id: Optional[str] = None
    incident_type: str
    severity: str
    description: str
    affected_resources: List[Any] = []
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    root_cause: Optional[str] = None
    remediation_actions: List[str] = []
    notified_parties: List[str] = []
    status: str = "open"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentReportListResponse(BaseModel):
    """Paginated list of incident reports."""
    incidents: List[IncidentReportResponse]
    total: int
    limit: int
    offset: int


class IncidentCreate(BaseModel):
    """Schema for creating an incident."""
    incident_type: str = Field(..., description="Type of incident")
    severity: str = Field(..., description="Severity level")
    description: str = Field(..., description="Incident description")
    affected_resources: Optional[List[Dict[str, Any]]] = Field(default=[], description="Affected resources")
    detected_at: Optional[datetime] = Field(None, description="When incident was detected")

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


class IncidentUpdate(BaseModel):
    """Schema for updating an incident."""
    severity: Optional[str] = Field(None, description="Severity level")
    description: Optional[str] = Field(None, description="Incident description")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    remediation_actions: Optional[List[str]] = Field(None, description="Actions taken")
    notified_parties: Optional[List[str]] = Field(None, description="Parties notified")
    status: Optional[str] = Field(None, description="Incident status")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")


class IncidentResolve(BaseModel):
    """Schema for resolving an incident."""
    root_cause: Optional[str] = Field(None, description="Root cause")
    remediation_actions: Optional[List[str]] = Field(None, description="Actions taken")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")

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
    company_id: Optional[str] = None
    model_version: str
    evaluation_type: str
    dimension: Optional[str] = None
    metric_name: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    passed: Optional[bool] = None
    sample_size: Optional[int] = None
    evaluation_date: Optional[date] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ModelEvaluationListResponse(BaseModel):
    """Paginated list of model evaluations."""
    evaluations: List[ModelEvaluationResponse]
    total: int
    limit: int
    offset: int


class ModelEvaluationSummaryResponse(BaseModel):
    """Summary of model evaluations by dimension."""
    total_evaluations: int
    by_dimension: Dict[str, Dict[str, Any]]
    by_evaluation_type: Dict[str, int]
    pass_rate: float
    latest_evaluation_date: Optional[date] = None


class ComplianceControlResponse(BaseModel):
    """Response schema for compliance control."""
    id: str
    company_id: Optional[str] = None
    framework: str
    control_id: str
    control_name: str
    description: Optional[str] = None
    status: str
    evidence_url: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    owner: Optional[str] = None
    risk_level: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceControlListResponse(BaseModel):
    """Paginated list of compliance controls."""
    controls: List[ComplianceControlResponse]
    total: int
    limit: int
    offset: int


class ComplianceSummaryResponse(BaseModel):
    """Summary of compliance controls by framework."""
    total_controls: int
    by_framework: Dict[str, Dict[str, int]]
    by_status: Dict[str, int]
    overdue_reviews: int
    upcoming_reviews: int


class ComplianceControlUpdate(BaseModel):
    """Schema for updating a compliance control."""
    status: Optional[str] = Field(None, description="Control status")
    evidence_url: Optional[str] = Field(None, description="Evidence URL")
    evidence_notes: Optional[str] = Field(None, description="Evidence notes")
    owner: Optional[str] = Field(None, description="Control owner")
    owner_email: Optional[str] = Field(None, description="Owner email")
    next_review_at: Optional[datetime] = Field(None, description="Next review date")

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
    ai_inference: Dict[str, Any]
    data_access: Dict[str, Any]
    consents: Dict[str, Any]
    incidents: Dict[str, Any]
    evaluations: Dict[str, Any]
    compliance: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class BiasResultItem(BaseModel):
    """Individual bias result for a category."""
    score: float = Field(..., ge=0, le=1, description="Bias score (0-1)")
    status: BiasStatusEnum = Field(..., description="Status: clear/consider/concern")
    details: Optional[str] = Field(None, description="Details about the bias analysis")


class BiasAuditReportResponse(BaseModel):
    """Response schema for bias audit report."""
    id: str
    company_id: str
    audit_type: str
    audit_date: Optional[date] = None
    sample_size: Optional[int] = None
    auditor: str
    auditor_name: Optional[str] = None
    auditor_organization: Optional[str] = None
    bias_results: Dict[str, Any] = {}
    overall_score: Optional[float] = None
    clear_count: int = 0
    consider_count: int = 0
    concern_count: int = 0
    compliance_frameworks: List[str] = []
    report_url: Optional[str] = None
    is_public: bool = False
    notes: Optional[str] = None
    recommendations: List[str] = []
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BiasAuditReportListResponse(BaseModel):
    """Paginated list of bias audit reports."""
    audits: List[BiasAuditReportResponse]
    total: int
    limit: int
    offset: int


class BiasAuditCreate(BaseModel):
    """Schema for creating a bias audit report."""
    audit_type: str = Field(..., description="Type of audit: monthly/quarterly/annual/on_demand")
    audit_date: date = Field(..., description="Date of the audit")
    sample_size: Optional[int] = Field(None, description="Number of candidates/decisions analyzed")
    auditor: str = Field(..., description="Type of auditor: internal/external/third_party")
    auditor_name: Optional[str] = Field(None, description="Name of the auditor")
    auditor_organization: Optional[str] = Field(None, description="Organization of the auditor")
    bias_results: Dict[str, Any] = Field(default_factory=dict, description="Results for all 11 bias categories")
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="Overall bias score (0-100)")
    compliance_frameworks: Optional[List[str]] = Field(default=[], description="Applicable compliance frameworks")
    report_url: Optional[str] = Field(None, description="URL to full audit report")
    notes: Optional[str] = Field(None, description="Additional notes")
    recommendations: Optional[List[str]] = Field(default=[], description="Audit recommendations")

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
    report_url: Optional[str] = Field(None, description="URL to the public report")

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
    latest_audit_date: Optional[date] = None
    latest_overall_score: Optional[float] = None
    by_audit_type: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    compliance_coverage: List[str] = []
    public_audits_count: int = 0
