"""
Observability and Compliance models for AI Governance.

This module provides comprehensive models for:
- AI Inference Logging (explainability)
- Data Access Logging (LGPD compliance)
- Consent Records (LGPD/GDPR)
- Incident Reports (SOC2, ISO27001)
- Model Evaluations (AI Ethics, bias/fairness)
- Compliance Controls (ISO27001, SOC2, LGPD)
"""
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, DateTime, Date, Text, JSON, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from lia_config.database import Base
import enum
import uuid


class AgentType(str, enum.Enum):
    """Types of AI agents in the system."""
    SCREENING = "screening"
    SCORING = "scoring"
    INTERVIEW = "interview"
    MATCHING = "matching"
    RECOMMENDATION = "recommendation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"


class DataOperationType(str, enum.Enum):
    """Types of data operations for LGPD logging."""
    VIEW = "view"
    EXPORT = "export"
    DELETE = "delete"
    UPDATE = "update"
    CREATE = "create"
    ANONYMIZE = "anonymize"


class DataType(str, enum.Enum):
    """Types of data accessed."""
    CV = "cv"
    SCORE = "score"
    PARECER = "parecer"
    PERSONAL_INFO = "personal_info"
    CONTACT_INFO = "contact_info"
    INTERVIEW_NOTES = "interview_notes"
    ASSESSMENT_RESULTS = "assessment_results"


class ConsentType(str, enum.Enum):
    """Types of consent for LGPD compliance."""
    DATA_PROCESSING = "data_processing"
    AI_SCORING = "ai_scoring"
    MARKETING = "marketing"
    DATA_SHARING = "data_sharing"
    AUTOMATED_DECISION = "automated_decision"
    PROFILE_ENRICHMENT = "profile_enrichment"


class LegalBasis(str, enum.Enum):
    """LGPD legal bases for data processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    LEGITIMATE_INTEREST = "legitimate_interest"
    PUBLIC_INTEREST = "public_interest"
    VITAL_INTEREST = "vital_interest"


class IncidentType(str, enum.Enum):
    """Types of security/compliance incidents."""
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_FAILURE = "system_failure"
    BIAS_DETECTED = "bias_detected"
    SLA_VIOLATION = "sla_violation"
    POLICY_VIOLATION = "policy_violation"
    PRIVACY_VIOLATION = "privacy_violation"


class IncidentSeverity(str, enum.Enum):
    """Severity levels for incidents."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvaluationType(str, enum.Enum):
    """Types of model evaluations."""
    BIAS_CHECK = "bias_check"
    FAIRNESS_AUDIT = "fairness_audit"
    ACCURACY_TEST = "accuracy_test"
    CALIBRATION_CHECK = "calibration_check"
    DRIFT_DETECTION = "drift_detection"


class EvaluationDimension(str, enum.Enum):
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


class BiasAuditType(str, enum.Enum):
    """Types of bias audits."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


class AuditorType(str, enum.Enum):
    """Types of auditors for bias audits."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    THIRD_PARTY = "third_party"


class BiasStatus(str, enum.Enum):
    """Status levels for bias results."""
    CLEAR = "clear"
    CONSIDER = "consider"
    CONCERN = "concern"


class BiasComplianceFramework(str, enum.Enum):
    """Compliance frameworks for bias auditing."""
    NYC_LL144 = "NYC_LL144"
    CO_SB205 = "CO_SB205"
    EU_AI_ACT = "EU_AI_ACT"
    CA_FEHA = "CA_FEHA"
    LGPD_BRAZIL = "LGPD_BRAZIL"


class ComplianceFramework(str, enum.Enum):
    """Compliance frameworks supported."""
    ISO27001 = "ISO27001"
    SOC2 = "SOC2"
    LGPD = "LGPD"
    GDPR = "GDPR"
    AI_ETHICS = "AI_ETHICS"


class ControlStatus(str, enum.Enum):
    """Status of compliance controls."""
    IMPLEMENTED = "implemented"
    PARTIAL = "partial"
    NOT_IMPLEMENTED = "not_implemented"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"


class AIInferenceLog(Base):
    """
    Detailed logs for AI inference operations.
    
    Tracks every AI decision with full explainability data including:
    - Input/output summaries (with privacy-preserving hashes)
    - Feature attributions for explainability
    - Bias flags for ethical AI compliance
    - Human override tracking
    """
    __tablename__ = "ai_inference_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    agent_type = Column(String(50), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    model_version = Column(String(20), nullable=True)
    input_hash = Column(String(64), nullable=True)
    input_preview = Column(Text, nullable=True)
    output_summary = Column(JSON, default=dict)
    
    decision_type = Column(String(50), nullable=True)
    confidence_score = Column(Numeric(5, 4), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    human_override = Column(Boolean, default=False)
    override_reason = Column(Text, nullable=True)
    override_by = Column(UUID(as_uuid=True), nullable=True)
    
    feature_attributions = Column(JSON, default=dict)
    bias_flags = Column(JSON, default=list)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AIInferenceLog {self.id} - {self.agent_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "agent_type": self.agent_type,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "vacancy_id": str(self.vacancy_id) if self.vacancy_id else None,
            "model_version": self.model_version,
            "decision_type": self.decision_type,
            "confidence_score": float(self.confidence_score) if self.confidence_score else None,
            "latency_ms": self.latency_ms,
            "tokens_used": self.tokens_used,
            "human_override": self.human_override,
            "feature_attributions": self.feature_attributions,
            "bias_flags": self.bias_flags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DataAccessLog(Base):
    """
    LGPD-compliant data access logging.
    
    Tracks all access to personal data including:
    - Who accessed the data
    - What data was accessed
    - Why it was accessed (purpose and legal basis)
    - What PII fields were involved
    """
    __tablename__ = "data_access_logs"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    data_subject_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    data_type = Column(String(50), nullable=False)
    operation = Column(String(20), nullable=False)
    pii_fields = Column(ARRAY(String), default=list)
    
    purpose = Column(String(100), nullable=True)
    legal_basis = Column(String(50), nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<DataAccessLog {self.id} - {self.operation} on {self.data_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "user_id": str(self.user_id),
            "data_subject_id": str(self.data_subject_id) if self.data_subject_id else None,
            "data_type": self.data_type,
            "operation": self.operation,
            "pii_fields": self.pii_fields,
            "purpose": self.purpose,
            "legal_basis": self.legal_basis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ConsentRecord(Base):
    """
    LGPD/GDPR consent records.
    
    Tracks consent for data processing with:
    - Consent type and version
    - Grant, expiration, and revocation dates
    - Source and legal basis
    """
    __tablename__ = "consent_records"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    consent_type = Column(String(50), nullable=False, index=True)
    version = Column(String(10), nullable=True)
    
    granted_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    source = Column(String(50), nullable=True)
    legal_basis = Column(String(50), nullable=True)
    
    consent_text = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Phase 1a LGPD Consent — canal, user_agent, processo_id, vaga_id, versao_disclaimer (2026-06-11)
    canal = Column(String(20), nullable=True)  # chat_web | whatsapp | chamada_online | chamada_telefonica
    user_agent = Column(Text, nullable=True)
    processo_id = Column(UUID(as_uuid=True), nullable=True)  # FK to triagem_sessions (processo seletivo)
    vaga_id = Column(UUID(as_uuid=True), nullable=True)  # FK to job_vacancies
    versao_disclaimer = Column(String(10), nullable=True)  # configurable disclaimer version
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ConsentRecord {self.id} - {self.consent_type} for candidate {self.candidate_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "candidate_id": str(self.candidate_id),
            "consent_type": self.consent_type,
            "version": self.version,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_active": self.is_active,
            "source": self.source,
            "legal_basis": self.legal_basis,
            "canal": self.canal,
            "user_agent": self.user_agent,
            "processo_id": str(self.processo_id) if self.processo_id else None,
            "vaga_id": str(self.vaga_id) if self.vaga_id else None,
            "versao_disclaimer": self.versao_disclaimer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class IncidentReport(Base):
    """
    Security and compliance incident reports.
    
    Tracks incidents with:
    - Type, severity, and description
    - Affected resources
    - Resolution and remediation actions
    - Notification tracking
    """
    __tablename__ = "incident_reports"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - incident_reports aggregated cross-tenant for system health metrics (no PII per row, NULL=platform-wide incident)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    incident_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    affected_resources = Column(JSON, default=list)
    
    detected_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    
    root_cause = Column(Text, nullable=True)
    remediation_actions = Column(ARRAY(String), default=list)
    notified_parties = Column(ARRAY(String), default=list)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), nullable=True)
    
    status = Column(String(20), default="open", index=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<IncidentReport {self.id} - {self.incident_type} ({self.severity})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "affected_resources": self.affected_resources,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "root_cause": self.root_cause,
            "remediation_actions": self.remediation_actions,
            "notified_parties": self.notified_parties,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ModelEvaluation(Base):
    """
    AI model bias and fairness evaluations.
    
    Tracks evaluations with:
    - Evaluation type and dimension (gender, age, etc.)
    - Metric values and thresholds
    - Pass/fail status
    - Sample sizes for statistical validity
    """
    __tablename__ = "model_evaluations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - model_evaluations aggregated cross-tenant for global ML model quality metrics (ADR-LGPD-001 anonymization, NULL=platform-wide eval)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    model_version = Column(String(20), nullable=False, index=True)
    evaluation_type = Column(String(50), nullable=False, index=True)
    dimension = Column(String(50), nullable=True)
    
    metric_name = Column(String(50), nullable=False)
    metric_value = Column(Numeric(10, 6), nullable=True)
    threshold = Column(Numeric(10, 6), nullable=True)
    passed = Column(Boolean, nullable=True)
    
    sample_size = Column(Integer, nullable=True)
    confidence_interval = Column(JSON, nullable=True)
    
    evaluation_date = Column(Date, nullable=False)
    evaluated_by = Column(UUID(as_uuid=True), nullable=True)
    
    details = Column(JSON, default=dict)
    recommendations = Column(ARRAY(String), default=list)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ModelEvaluation {self.id} - {self.model_version} {self.evaluation_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "model_version": self.model_version,
            "evaluation_type": self.evaluation_type,
            "dimension": self.dimension,
            "metric_name": self.metric_name,
            "metric_value": float(self.metric_value) if self.metric_value else None,
            "threshold": float(self.threshold) if self.threshold else None,
            "passed": self.passed,
            "sample_size": self.sample_size,
            "evaluation_date": self.evaluation_date.isoformat() if self.evaluation_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ComplianceControl(Base):
    """
    Compliance control status tracking.
    
    Tracks controls for various frameworks (ISO27001, SOC2, LGPD) with:
    - Control ID and name per framework
    - Implementation status
    - Evidence and review dates
    - Ownership
    """
    __tablename__ = "compliance_controls"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # WT-2022 P0.TENANT: TENANT-EXEMPT TENANT-NULLABLE-DELIBERATE - compliance_controls global framework definitions (NULL=platform-wide control like LGPD/SOX baseline, UUID=per-company override)
    company_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    framework = Column(String(50), nullable=False, index=True)
    control_id = Column(String(50), nullable=False, index=True)
    control_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    status = Column(String(20), nullable=False, default="not_implemented")
    evidence_url = Column(String(500), nullable=True)
    evidence_notes = Column(Text, nullable=True)
    
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    
    owner = Column(String(255), nullable=True)
    owner_email = Column(String(255), nullable=True)
    
    risk_level = Column(String(20), nullable=True)
    priority = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ComplianceControl {self.id} - {self.framework}:{self.control_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id) if self.company_id else None,
            "framework": self.framework,
            "control_id": self.control_id,
            "control_name": self.control_name,
            "description": self.description,
            "status": self.status,
            "evidence_url": self.evidence_url,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "next_review_at": self.next_review_at.isoformat() if self.next_review_at else None,
            "owner": self.owner,
            "risk_level": self.risk_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BiasAuditReport(Base):
    """
    Bias Audit Report for AI Ethics and Compliance.
    
    Tracks comprehensive bias audits with all 11 Tezi AI categories:
    - sex_bias, race_ethnicity_bias, age_bias, disability_bias, religion_bias
    - sexual_orientation_bias, veteran_status_bias, language_proficiency_bias
    - pregnancy_status_bias, national_origin_bias, intersectional_bias
    
    Supports compliance frameworks: NYC_LL144, CO_SB205, EU_AI_ACT, CA_FEHA, LGPD_BRAZIL
    """
    __tablename__ = "bias_audit_reports"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    audit_type = Column(String(20), nullable=False, index=True)
    audit_date = Column(Date, nullable=False, index=True)
    sample_size = Column(Integer, nullable=True)
    
    auditor = Column(String(20), nullable=False)
    auditor_name = Column(String(255), nullable=True)
    auditor_organization = Column(String(255), nullable=True)
    
    bias_results = Column(JSON, nullable=False, default=dict)
    
    overall_score = Column(Numeric(5, 2), nullable=True)
    clear_count = Column(Integer, default=0)
    consider_count = Column(Integer, default=0)
    concern_count = Column(Integer, default=0)
    
    compliance_frameworks = Column(ARRAY(String), default=list)
    
    report_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False)
    
    notes = Column(Text, nullable=True)
    recommendations = Column(ARRAY(String), default=list)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BiasAuditReport {self.id} - {self.audit_type} on {self.audit_date}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "audit_type": self.audit_type,
            "audit_date": self.audit_date.isoformat() if self.audit_date else None,
            "sample_size": self.sample_size,
            "auditor": self.auditor,
            "auditor_name": self.auditor_name,
            "auditor_organization": self.auditor_organization,
            "bias_results": self.bias_results,
            "overall_score": float(self.overall_score) if self.overall_score else None,
            "clear_count": self.clear_count,
            "consider_count": self.consider_count,
            "concern_count": self.concern_count,
            "compliance_frameworks": self.compliance_frameworks or [],
            "report_url": self.report_url,
            "is_public": self.is_public,
            "notes": self.notes,
            "recommendations": self.recommendations or [],
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BreachSeverity(str, enum.Enum):
    """Severity levels for data breaches."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachStatus(str, enum.Enum):
    """Status of breach notification workflow."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    NOTIFIED = "notified"
    RESOLVED = "resolved"


# R-053: DUPLICATE DecisionType — different variants (SCREENING/RANKING/REJECTION) from
# canonical in libs/models/lia_models/audit_log.py. No callers import this version.
# Action: if LGPD Article 20 needs its own type, rename to LgpdDecisionType and import
# from audit_log; otherwise remove this class.
class DecisionType(str, enum.Enum):
    """Types of automated decisions for LGPD Article 20."""
    SCREENING = "screening"
    RANKING = "ranking"
    REJECTION = "rejection"


class DPORegistry(Base):
    """
    Data Protection Officer (DPO) Registry for LGPD compliance.
    
    Tracks DPO information per company including:
    - Contact information
    - Appointment details
    - Public contact URL for data subjects
    """
    __tablename__ = "dpo_registry"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    
    dpo_name = Column(String(255), nullable=False)
    dpo_email = Column(String(255), nullable=False)
    dpo_phone = Column(String(50), nullable=True)
    
    appointment_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    
    public_contact_url = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DPORegistry {self.id} - {self.dpo_name} for company {self.company_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "dpo_name": self.dpo_name,
            "dpo_email": self.dpo_email,
            "dpo_phone": self.dpo_phone,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "is_active": self.is_active,
            "public_contact_url": self.public_contact_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class BreachNotification(Base):
    """
    Data Breach Notification tracking for LGPD 48h requirement.
    
    Tracks data breaches with:
    - Breach detection and description
    - Affected data types and count
    - ANPD notification status (required within 48h)
    - Data subject notification status
    - Remediation actions and resolution
    """
    __tablename__ = "breach_notifications"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    breach_detected_at = Column(DateTime, nullable=False)
    breach_description = Column(Text, nullable=False)
    affected_data_types = Column(ARRAY(String), default=list)
    affected_count = Column(Integer, nullable=True)
    
    severity = Column(String(20), nullable=False, default="medium", index=True)
    
    notification_sent_to_anpd = Column(Boolean, default=False)
    anpd_notification_at = Column(DateTime, nullable=True)
    
    notification_sent_to_subjects = Column(Boolean, default=False)
    subjects_notification_at = Column(DateTime, nullable=True)
    
    remediation_actions = Column(ARRAY(String), default=list)
    
    status = Column(String(20), nullable=False, default="detected", index=True)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<BreachNotification {self.id} - {self.severity} ({self.status})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "breach_detected_at": self.breach_detected_at.isoformat() if self.breach_detected_at else None,
            "breach_description": self.breach_description,
            "affected_data_types": self.affected_data_types,
            "affected_count": self.affected_count,
            "severity": self.severity,
            "notification_sent_to_anpd": self.notification_sent_to_anpd,
            "anpd_notification_at": self.anpd_notification_at.isoformat() if self.anpd_notification_at else None,
            "notification_sent_to_subjects": self.notification_sent_to_subjects,
            "subjects_notification_at": self.subjects_notification_at.isoformat() if self.subjects_notification_at else None,
            "remediation_actions": self.remediation_actions,
            "status": self.status,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "hours_since_detection": self._hours_since_detection(),
            "anpd_deadline_exceeded": self._anpd_deadline_exceeded(),
        }
    
    def _hours_since_detection(self):
        """Calculate hours since breach was detected."""
        if self.breach_detected_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.breach_detected_at.tzinfo else datetime.utcnow()
            delta = now - self.breach_detected_at
            return round(delta.total_seconds() / 3600, 1)
        return None
    
    def _anpd_deadline_exceeded(self):
        """Check if 48h ANPD notification deadline has been exceeded."""
        if not self.notification_sent_to_anpd:
            hours = self._hours_since_detection()
            if hours and hours > 48:
                return True
        return False


class AutomatedDecisionExplanation(Base):
    """
    Article 20 LGPD compliance for AI automated decisions.
    
    Tracks automated decisions with:
    - Decision type and context (candidate, vacancy)
    - AI model and criteria used
    - Explanation text for data subject
    - Human review request and resolution
    """
    __tablename__ = "automated_decision_explanations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    decision_type = Column(String(50), nullable=False, index=True)
    candidate_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    vacancy_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    ai_model_used = Column(String(100), nullable=True)
    input_criteria = Column(JSON, default=dict)
    decision_criteria = Column(JSON, default=dict)
    explanation_text = Column(Text, nullable=True)
    
    explanation_requested_at = Column(DateTime, nullable=True)
    explanation_provided_at = Column(DateTime, nullable=True)
    
    human_review_requested = Column(Boolean, default=False)
    human_review_completed_at = Column(DateTime, nullable=True)
    human_review_decision = Column(Text, nullable=True)
    human_reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AutomatedDecisionExplanation {self.id} - {self.decision_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "decision_type": self.decision_type,
            "candidate_id": str(self.candidate_id) if self.candidate_id else None,
            "vacancy_id": str(self.vacancy_id) if self.vacancy_id else None,
            "ai_model_used": self.ai_model_used,
            "input_criteria": self.input_criteria,
            "decision_criteria": self.decision_criteria,
            "explanation_text": self.explanation_text,
            "explanation_requested_at": self.explanation_requested_at.isoformat() if self.explanation_requested_at else None,
            "explanation_provided_at": self.explanation_provided_at.isoformat() if self.explanation_provided_at else None,
            "human_review_requested": self.human_review_requested,
            "human_review_completed_at": self.human_review_completed_at.isoformat() if self.human_review_completed_at else None,
            "human_review_decision": self.human_review_decision,
            "human_reviewer_id": str(self.human_reviewer_id) if self.human_reviewer_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ComplianceFrameworkType(str, enum.Enum):
    """Extended compliance frameworks for control inventory."""
    ISO_27001 = "ISO_27001"
    SOC_2_TYPE_I = "SOC_2_TYPE_I"
    SOC_2_TYPE_II = "SOC_2_TYPE_II"
    SOX = "SOX"
    LGPD = "LGPD"
    GDPR = "GDPR"
    BACEN_4893 = "BACEN_4893"
    PCI_DSS = "PCI_DSS"


class CompanyControlStatus(str, enum.Enum):
    """Status of company's control implementation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    IMPLEMENTED = "implemented"
    VERIFIED = "verified"
    NOT_APPLICABLE = "not_applicable"


class AuditResultType(str, enum.Enum):
    """Audit result types."""
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class AuditType(str, enum.Enum):
    """Types of compliance audits."""
    INTERNAL = "internal"
    EXTERNAL = "external"
    CERTIFICATION = "certification"


class SOXSection(str, enum.Enum):
    """SOX sections relevant to HR/Payroll."""
    SECTION_302 = "302"
    SECTION_404 = "404"
    SECTION_409 = "409"
    SECTION_802 = "802"


class SOXTestResult(str, enum.Enum):
    """SOX control test result."""
    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"
    NOT_TESTED = "not_tested"


class SOXControlFrequency(str, enum.Enum):
    """Frequency of SOX control execution."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class ComplianceControlLibrary(Base):
    """
    Master control catalog for compliance frameworks.
    
    Contains the canonical list of controls for ISO 27001, SOC 2, SOX, etc.
    Companies implement these controls through CompanyComplianceControl.
    """
    __tablename__ = "compliance_control_library"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework = Column(String(50), nullable=False, index=True)
    control_id = Column(String(50), nullable=False, index=True)
    control_name = Column(String(500), nullable=False)
    control_description = Column(Text, nullable=True)
    control_category = Column(String(100), nullable=True, index=True)
    domain = Column(String(100), nullable=True)
    is_mandatory = Column(Boolean, default=True)
    implementation_guidance = Column(Text, nullable=True)
    evidence_requirements = Column(JSON, default=list)
    related_controls = Column(JSON, default=list)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ComplianceControlLibrary {self.framework}:{self.control_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "framework": self.framework,
            "control_id": self.control_id,
            "control_name": self.control_name,
            "control_description": self.control_description,
            "control_category": self.control_category,
            "domain": self.domain,
            "is_mandatory": self.is_mandatory,
            "implementation_guidance": self.implementation_guidance,
            "evidence_requirements": self.evidence_requirements or [],
            "related_controls": self.related_controls or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CompanyComplianceControl(Base):
    """
    Company's control implementation status.
    
    Links a company to controls from the master library and tracks
    implementation status, evidence, and review dates.
    """
    __tablename__ = "company_compliance_controls"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    control_library_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="not_started", index=True)
    implementation_date = Column(Date, nullable=True)
    last_review_date = Column(Date, nullable=True)
    next_review_date = Column(Date, nullable=True)
    owner_name = Column(String(255), nullable=True)
    owner_email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    evidence_files = Column(JSON, default=list)
    effectiveness_rating = Column(Integer, nullable=True)
    auditor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<CompanyComplianceControl {self.id} - {self.status}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "control_library_id": str(self.control_library_id),
            "status": self.status,
            "implementation_date": self.implementation_date.isoformat() if self.implementation_date else None,
            "last_review_date": self.last_review_date.isoformat() if self.last_review_date else None,
            "next_review_date": self.next_review_date.isoformat() if self.next_review_date else None,
            "owner_name": self.owner_name,
            "owner_email": self.owner_email,
            "notes": self.notes,
            "evidence_files": self.evidence_files or [],
            "effectiveness_rating": self.effectiveness_rating,
            "auditor_notes": self.auditor_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ComplianceAudit(Base):
    """
    Track SOC 2, ISO 27001, and other compliance audits.
    
    Records audit details including scope, findings, and results.
    """
    __tablename__ = "compliance_audits"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    framework = Column(String(50), nullable=False, index=True)
    audit_type = Column(String(30), nullable=False, index=True)
    auditor_organization = Column(String(255), nullable=True)
    auditor_name = Column(String(255), nullable=True)
    audit_start_date = Column(Date, nullable=True)
    audit_end_date = Column(Date, nullable=True)
    scope_description = Column(Text, nullable=True)
    findings_count = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    overall_result = Column(String(30), nullable=True)
    certificate_url = Column(String(500), nullable=True)
    report_url = Column(String(500), nullable=True)
    valid_until = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ComplianceAudit {self.id} - {self.framework} ({self.audit_type})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "framework": self.framework,
            "audit_type": self.audit_type,
            "auditor_organization": self.auditor_organization,
            "auditor_name": self.auditor_name,
            "audit_start_date": self.audit_start_date.isoformat() if self.audit_start_date else None,
            "audit_end_date": self.audit_end_date.isoformat() if self.audit_end_date else None,
            "scope_description": self.scope_description,
            "findings_count": self.findings_count,
            "critical_findings": self.critical_findings,
            "high_findings": self.high_findings,
            "medium_findings": self.medium_findings,
            "low_findings": self.low_findings,
            "overall_result": self.overall_result,
            "certificate_url": self.certificate_url,
            "report_url": self.report_url,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SOXControl(Base):
    """
    SOX-specific controls for HR/Payroll processes.
    
    Tracks SOX Section 302, 404, 409, 802 controls with testing and remediation.
    """
    __tablename__ = "sox_controls"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    section = Column(String(10), nullable=False, index=True)
    control_id = Column(String(50), nullable=False, index=True)
    control_name = Column(String(500), nullable=False)
    control_objective = Column(Text, nullable=True)
    key_control = Column(Boolean, default=False)
    frequency = Column(String(20), nullable=True)
    control_owner = Column(String(255), nullable=True)
    last_test_date = Column(Date, nullable=True)
    test_result = Column(String(20), default="not_tested")
    test_evidence = Column(Text, nullable=True)
    remediation_plan = Column(Text, nullable=True)
    remediation_due_date = Column(Date, nullable=True)
    segregation_of_duties_verified = Column(Boolean, default=False)
    audit_trail_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SOXControl {self.section}-{self.control_id}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "section": self.section,
            "control_id": self.control_id,
            "control_name": self.control_name,
            "control_objective": self.control_objective,
            "key_control": self.key_control,
            "frequency": self.frequency,
            "control_owner": self.control_owner,
            "last_test_date": self.last_test_date.isoformat() if self.last_test_date else None,
            "test_result": self.test_result,
            "test_evidence": self.test_evidence,
            "remediation_plan": self.remediation_plan,
            "remediation_due_date": self.remediation_due_date.isoformat() if self.remediation_due_date else None,
            "segregation_of_duties_verified": self.segregation_of_duties_verified,
            "audit_trail_enabled": self.audit_trail_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DataSubjectRequestTypeEnum(str, enum.Enum):
    """Types of data subject requests under LGPD Art. 18."""
    ACCESS = "access"
    CORRECTION = "correction"
    DELETION = "deletion"
    PORTABILITY = "portability"
    OBJECTION = "objection"
    RESTRICTION = "restriction"
    EXPLANATION = "explanation"


class DataSubjectRequestStatusEnum(str, enum.Enum):
    """Status of data subject requests."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DataSubjectRequest(Base):
    """
    Data Subject Request for LGPD Portal do Titular.
    
    Tracks requests from data subjects (candidates) exercising their rights
    under LGPD Art. 18 including:
    - Access to personal data
    - Correction of inaccurate data
    - Deletion/anonymization of data
    - Data portability
    - Objection to processing
    - Restriction of processing
    - Explanation of automated decisions
    
    Multi-tenant: company_id identifies the data controller (tenant).
    SLA: 15 days legal deadline per LGPD.
    """
    __tablename__ = "data_subject_requests"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    request_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    subject_name = Column(String(255), nullable=False)
    subject_email = Column(String(255), nullable=False, index=True)
    subject_phone = Column(String(50), nullable=True)
    subject_identifier = Column(String(50), nullable=False, index=True)
    
    identity_verified = Column(Boolean, default=False)
    identity_verification_method = Column(String(50), nullable=True)
    identity_verified_at = Column(DateTime, nullable=True)
    
    description = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    
    data_categories = Column(ARRAY(String), default=list)
    legal_basis = Column(String(50), nullable=True)
    
    assigned_to = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    sla_deadline = Column(DateTime, nullable=False)
    sla_met = Column(Boolean, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    rejection_reason = Column(Text, nullable=True)
    
    evidence_files = Column(JSON, default=list)
    audit_trail = Column(JSON, default=list)
    
    source_channel = Column(String(20), nullable=False, default="portal")
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DataSubjectRequest {self.id} - {self.request_type} ({self.status})>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "request_type": self.request_type,
            "status": self.status,
            "subject_name": self.subject_name,
            "subject_email": self.subject_email,
            "subject_phone": self.subject_phone,
            "subject_identifier": self.subject_identifier,
            "identity_verified": self.identity_verified,
            "identity_verification_method": self.identity_verification_method,
            "identity_verified_at": self.identity_verified_at.isoformat() if self.identity_verified_at else None,
            "description": self.description,
            "response": self.response,
            "data_categories": self.data_categories or [],
            "legal_basis": self.legal_basis,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "sla_met": self.sla_met,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rejection_reason": self.rejection_reason,
            "evidence_files": self.evidence_files or [],
            "audit_trail": self.audit_trail or [],
            "source_channel": self.source_channel,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "days_remaining": self._days_remaining(),
            "is_overdue": self._is_overdue(),
        }
    
    def _days_remaining(self):
        """Calculate days remaining until SLA deadline."""
        if self.sla_deadline and self.status not in ["completed", "rejected", "cancelled"]:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.sla_deadline.tzinfo else datetime.utcnow()
            delta = self.sla_deadline - now
            return max(0, delta.days)
        return None
    
    def _is_overdue(self):
        """Check if request is past SLA deadline."""
        if self.sla_deadline and self.status not in ["completed", "rejected", "cancelled"]:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.sla_deadline.tzinfo else datetime.utcnow()
            return now > self.sla_deadline
        return False


class ConsentEventTypeEnum(str, enum.Enum):
    """Types of consent events for advanced LGPD consent management."""
    GRANTED = "granted"
    REVOKED = "revoked"
    RENEWED = "renewed"
    EXPIRED = "expired"


class ConsentVersion(Base):
    """
    Versioned consent terms for advanced LGPD compliance.
    
    Tracks consent term versions with:
    - Full HTML and text content
    - Content hash for integrity verification
    - Effective date ranges
    - Renewal configuration
    - Explicit consent requirements
    
    Multi-tenant: company_id identifies the data controller (tenant).
    Reuses ConsentType enum for consent categorization.
    """
    __tablename__ = "consent_versions"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    consent_type = Column(String(50), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    
    content_html = Column(Text, nullable=False)
    content_text = Column(Text, nullable=False)
    hash = Column(String(64), nullable=False, index=True)
    
    effective_from = Column(DateTime, nullable=False, index=True)
    effective_until = Column(DateTime, nullable=True)
    
    is_current = Column(Boolean, default=True, index=True)
    requires_explicit_consent = Column(Boolean, default=True)
    renewal_period_days = Column(Integer, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ConsentVersion {self.id} - {self.consent_type} v{self.version}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "consent_type": self.consent_type,
            "version": self.version,
            "title": self.title,
            "content_html": self.content_html,
            "content_text": self.content_text,
            "hash": self.hash,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "effective_until": self.effective_until.isoformat() if self.effective_until else None,
            "is_current": self.is_current,
            "requires_explicit_consent": self.requires_explicit_consent,
            "renewal_period_days": self.renewal_period_days,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ConsentEvent(Base):
    """
    Consent events for advanced LGPD consent tracking.
    
    Tracks all consent events including:
    - Consent granted, revoked, renewed, or expired
    - Full IP/device tracking for proof
    - Channel tracking (web, whatsapp, email, api)
    - Proof hash for legal evidence
    - Expiration dates for renewal workflows
    
    Multi-tenant: company_id identifies the data controller (tenant).
    Links to ConsentVersion for term versioning.
    Compatible with existing ConsentRecord model.
    """
    __tablename__ = "consent_events"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    consent_version_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    subject_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    subject_email = Column(String(255), nullable=False, index=True)
    subject_identifier = Column(String(50), nullable=False, index=True)
    
    event_type = Column(String(20), nullable=False, index=True)
    consent_given = Column(Boolean, nullable=False)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_info = Column(JSON, default=dict)
    location_country = Column(String(100), nullable=True)
    
    channel = Column(String(50), nullable=False, default="web")
    proof_hash = Column(String(64), nullable=False, index=True)
    
    expires_at = Column(DateTime, nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ConsentEvent {self.id} - {self.event_type} for {self.subject_email}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "consent_version_id": str(self.consent_version_id),
            "subject_id": str(self.subject_id) if self.subject_id else None,
            "subject_email": self.subject_email,
            "subject_identifier": self.subject_identifier,
            "event_type": self.event_type,
            "consent_given": self.consent_given,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_info": self.device_info or {},
            "location_country": self.location_country,
            "channel": self.channel,
            "proof_hash": self.proof_hash,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_expired": self._is_expired(),
            "days_until_expiry": self._days_until_expiry(),
        }
    
    def _is_expired(self):
        """Check if consent has expired."""
        if self.expires_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.expires_at.tzinfo else datetime.utcnow()
            return now > self.expires_at
        return False
    
    def _days_until_expiry(self):
        """Calculate days until consent expires."""
        if self.expires_at:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.expires_at.tzinfo else datetime.utcnow()
            delta = self.expires_at - now
            return max(0, delta.days)
        return None


class InsurancePolicyStatusEnum(str, enum.Enum):
    """Status of cyber insurance policies for BCB 498/2025 compliance."""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING_RENEWAL = "pending_renewal"


class InsuranceCoverageTypeEnum(str, enum.Enum):
    """Types of cyber insurance coverages per BCB 498/2025."""
    DATA_BREACH = "data_breach"
    RANSOMWARE = "ransomware"
    BUSINESS_INTERRUPTION = "business_interruption"
    REGULATORY_DEFENSE = "regulatory_defense"
    CYBER_LIABILITY = "cyber_liability"
    FORENSICS = "forensics"
    NOTIFICATION_COSTS = "notification_costs"
    CRISIS_MANAGEMENT = "crisis_management"


class InsuranceDocumentTypeEnum(str, enum.Enum):
    """Types of insurance-related documents."""
    POLICY = "policy"
    ENDORSEMENT = "endorsement"
    CERTIFICATE = "certificate"
    CLAIM = "claim"
    CORRESPONDENCE = "correspondence"


class InsuranceClaimStatusEnum(str, enum.Enum):
    """Status of insurance claims/sinistros."""
    REPORTED = "reported"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DENIED = "denied"
    SETTLED = "settled"
    CLOSED = "closed"


class InsurancePolicy(Base):
    """
    Cyber Insurance Policy for BCB 498/2025 compliance.
    
    Tracks cyber insurance policies required by financial institutions
    under Resolução BCB 498/2025, including:
    - Policy details and insurer information
    - Coverage amounts and dates
    - Premium and deductible values
    - Renewal tracking
    
    Multi-tenant: company_id identifies the financial institution (tenant).
    """
    __tablename__ = "insurance_policies"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    policy_number = Column(String(100), nullable=False, index=True)
    insurer_name = Column(String(255), nullable=False)
    insurer_cnpj = Column(String(18), nullable=True)
    
    broker_name = Column(String(255), nullable=True)
    broker_contact = Column(String(255), nullable=True)
    
    coverage_start = Column(Date, nullable=False, index=True)
    coverage_end = Column(Date, nullable=False, index=True)
    
    total_coverage_amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="BRL")
    premium_amount = Column(Numeric(18, 2), nullable=False)
    deductible_amount = Column(Numeric(18, 2), nullable=False, default=0)
    
    status = Column(String(20), nullable=False, default="active", index=True)
    
    renewal_reminder_sent = Column(Boolean, default=False)
    last_renewal_reminder_at = Column(DateTime, nullable=True)
    
    created_by = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<InsurancePolicy {self.policy_number} - {self.insurer_name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "policy_number": self.policy_number,
            "insurer_name": self.insurer_name,
            "insurer_cnpj": self.insurer_cnpj,
            "broker_name": self.broker_name,
            "broker_contact": self.broker_contact,
            "coverage_start": self.coverage_start.isoformat() if self.coverage_start else None,
            "coverage_end": self.coverage_end.isoformat() if self.coverage_end else None,
            "total_coverage_amount": float(self.total_coverage_amount) if self.total_coverage_amount else None,
            "currency": self.currency,
            "premium_amount": float(self.premium_amount) if self.premium_amount else None,
            "deductible_amount": float(self.deductible_amount) if self.deductible_amount else None,
            "status": self.status,
            "renewal_reminder_sent": self.renewal_reminder_sent,
            "last_renewal_reminder_at": self.last_renewal_reminder_at.isoformat() if self.last_renewal_reminder_at else None,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self._is_active(),
            "days_until_expiry": self._days_until_expiry(),
        }
    
    def _is_active(self):
        """Check if policy is currently active."""
        if self.status != "active":
            return False
        if self.coverage_start and self.coverage_end:
            today = date.today()
            return self.coverage_start <= today <= self.coverage_end
        return False
    
    def _days_until_expiry(self):
        """Calculate days until policy expires."""
        if self.coverage_end:
            today = date.today()
            delta = self.coverage_end - today
            return delta.days
        return None


class InsuranceCoverage(Base):
    """
    Insurance Coverage Details for BCB 498/2025 compliance.
    
    Tracks specific coverage types within a cyber insurance policy:
    - Coverage type (data breach, ransomware, etc.)
    - Coverage limits and sub-limits
    - Deductibles per coverage type
    - Exclusions and notes
    
    References InsurancePolicy via policy_id.
    """
    __tablename__ = "insurance_coverages"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    coverage_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    coverage_limit = Column(Numeric(18, 2), nullable=False)
    sub_limit = Column(Numeric(18, 2), nullable=True)
    deductible = Column(Numeric(18, 2), nullable=True)
    
    is_included = Column(Boolean, default=True)
    exclusions = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<InsuranceCoverage {self.id} - {self.coverage_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "policy_id": str(self.policy_id),
            "coverage_type": self.coverage_type,
            "description": self.description,
            "coverage_limit": float(self.coverage_limit) if self.coverage_limit else None,
            "sub_limit": float(self.sub_limit) if self.sub_limit else None,
            "deductible": float(self.deductible) if self.deductible else None,
            "is_included": self.is_included,
            "exclusions": self.exclusions,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class InsuranceDocument(Base):
    """
    Insurance Document Attachments for BCB 498/2025 compliance.
    
    Tracks documents attached to insurance policies:
    - Policy documents and endorsements
    - Certificates of insurance
    - Claim-related documents
    - Correspondence with insurer/broker
    
    References InsurancePolicy via policy_id.
    """
    __tablename__ = "insurance_documents"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    document_type = Column(String(50), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    uploaded_by = Column(UUID(as_uuid=True), nullable=True)
    uploaded_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<InsuranceDocument {self.id} - {self.document_type}: {self.file_name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "policy_id": str(self.policy_id),
            "document_type": self.document_type,
            "file_name": self.file_name,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "uploaded_by": str(self.uploaded_by) if self.uploaded_by else None,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


class InsuranceClaim(Base):
    """
    Insurance Claims/Sinistros for BCB 498/2025 compliance.
    
    Tracks claims filed against cyber insurance policies:
    - Incident and reporting dates
    - Loss estimates and claimed amounts
    - Settlement status and amounts
    - Links to related incident reports
    
    References InsurancePolicy via policy_id.
    Optionally references IncidentReport via related_incident_id.
    """
    __tablename__ = "insurance_claims"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    claim_number = Column(String(100), nullable=False, index=True)
    incident_date = Column(Date, nullable=False, index=True)
    reported_date = Column(Date, nullable=False)
    
    description = Column(Text, nullable=False)
    
    estimated_loss = Column(Numeric(18, 2), nullable=False)
    claimed_amount = Column(Numeric(18, 2), nullable=False)
    settled_amount = Column(Numeric(18, 2), nullable=True)
    
    status = Column(String(20), nullable=False, default="reported", index=True)
    
    related_incident_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<InsuranceClaim {self.claim_number} - {self.status}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "policy_id": str(self.policy_id),
            "claim_number": self.claim_number,
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "reported_date": self.reported_date.isoformat() if self.reported_date else None,
            "description": self.description,
            "estimated_loss": float(self.estimated_loss) if self.estimated_loss else None,
            "claimed_amount": float(self.claimed_amount) if self.claimed_amount else None,
            "settled_amount": float(self.settled_amount) if self.settled_amount else None,
            "status": self.status,
            "related_incident_id": str(self.related_incident_id) if self.related_incident_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "recovery_rate": self._recovery_rate(),
        }
    
    def _recovery_rate(self):
        """Calculate recovery rate (settled/claimed)."""
        if self.settled_amount and self.claimed_amount and self.claimed_amount > 0:
            return float(self.settled_amount / self.claimed_amount * 100)
        return None


class RiskCategory(str, enum.Enum):
    """Risk categories for ISO 27001 and SOX compliance."""
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    TECHNOLOGY = "technology"
    CYBER = "cyber"
    THIRD_PARTY = "third_party"
    REPUTATIONAL = "reputational"


class RiskLikelihood(str, enum.Enum):
    """Risk likelihood levels (1-5 scale)."""
    RARE = "rare"
    UNLIKELY = "unlikely"
    POSSIBLE = "possible"
    LIKELY = "likely"
    ALMOST_CERTAIN = "almost_certain"


class RiskImpact(str, enum.Enum):
    """Risk impact levels (1-5 scale)."""
    INSIGNIFICANT = "insignificant"
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CATASTROPHIC = "catastrophic"


class RiskStatus(str, enum.Enum):
    """Risk lifecycle status."""
    IDENTIFIED = "identified"
    ASSESSED = "assessed"
    MITIGATING = "mitigating"
    ACCEPTED = "accepted"
    CLOSED = "closed"


class RiskTreatmentType(str, enum.Enum):
    """Risk treatment strategies (ISO 27001)."""
    AVOID = "avoid"
    TRANSFER = "transfer"
    MITIGATE = "mitigate"
    ACCEPT = "accept"


class RiskEntry(Base):
    """
    Risk Register Entry for ISO 27001 and SOX compliance.
    
    Tracks identified risks with:
    - Risk categorization and scoring (inherent vs residual)
    - Likelihood and impact assessment (5x5 matrix)
    - Risk ownership and mitigation tracking
    - Links to compliance controls
    
    Multi-tenant: company_id identifies the organization (tenant).
    """
    __tablename__ = "risk_entries"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    risk_id = Column(String(50), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    
    likelihood = Column(String(20), nullable=False)
    impact = Column(String(20), nullable=False)
    inherent_risk_score = Column(Integer, nullable=True)
    residual_risk_score = Column(Integer, nullable=True)
    
    risk_owner = Column(String(255), nullable=True)
    risk_owner_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    mitigation_plan = Column(Text, nullable=True)
    mitigation_status = Column(String(50), nullable=True)
    
    controls_linked = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    review_date = Column(Date, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)
    
    status = Column(String(20), nullable=False, default="identified", index=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RiskEntry {self.risk_id} - {self.title}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "risk_id": self.risk_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "inherent_risk_score": self.inherent_risk_score,
            "residual_risk_score": self.residual_risk_score,
            "risk_owner": self.risk_owner,
            "risk_owner_id": str(self.risk_owner_id) if self.risk_owner_id else None,
            "mitigation_plan": self.mitigation_plan,
            "mitigation_status": self.mitigation_status,
            "controls_linked": [str(c) for c in self.controls_linked] if self.controls_linked else [],
            "review_date": self.review_date.isoformat() if self.review_date else None,
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "risk_level": self._calculate_risk_level(),
        }
    
    def _calculate_risk_level(self):
        """Calculate risk level based on inherent score."""
        if self.inherent_risk_score:
            if self.inherent_risk_score >= 20:
                return "critical"
            elif self.inherent_risk_score >= 12:
                return "high"
            elif self.inherent_risk_score >= 6:
                return "medium"
            else:
                return "low"
        return None


class RiskTreatment(Base):
    """
    Risk Treatment Actions for ISO 27001 compliance.
    
    Tracks treatment actions for identified risks:
    - Treatment type (avoid, transfer, mitigate, accept)
    - Responsible party and due dates
    - Evidence and status tracking
    
    References RiskEntry via risk_id.
    """
    __tablename__ = "risk_treatments"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    treatment_type = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    responsible = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    
    status = Column(String(50), nullable=False, default="pending")
    
    evidence_files = Column(JSON, default=list)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<RiskTreatment {self.id} - {self.treatment_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "risk_id": str(self.risk_id),
            "treatment_type": self.treatment_type,
            "description": self.description,
            "responsible": self.responsible,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "status": self.status,
            "evidence_files": self.evidence_files or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_overdue": self._is_overdue(),
        }
    
    def _is_overdue(self):
        """Check if treatment is past due date."""
        if self.due_date and self.status not in ["completed", "cancelled"]:
            return date.today() > self.due_date
        return False


class SoDConflictType(str, enum.Enum):
    """Types of Segregation of Duties conflicts (SOX 404)."""
    AUTHORIZATION_EXECUTION = "authorization_execution"
    CUSTODY_RECORDING = "custody_recording"
    AUTHORIZATION_CUSTODY = "authorization_custody"
    INITIATION_APPROVAL = "initiation_approval"


class SoDRole(Base):
    """
    Segregation of Duties Role Definition for SOX 404 compliance.
    
    Defines roles with their permissions for SoD analysis:
    - Role identification and department
    - Permission sets
    - Critical role flagging
    
    Multi-tenant: company_id identifies the organization (tenant).
    """
    __tablename__ = "sod_roles"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    role_code = Column(String(50), nullable=False, index=True)
    role_name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    
    permissions = Column(ARRAY(String), default=list)
    
    is_critical = Column(Boolean, default=False)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SoDRole {self.role_code} - {self.role_name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "role_code": self.role_code,
            "role_name": self.role_name,
            "department": self.department,
            "permissions": self.permissions or [],
            "is_critical": self.is_critical,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SoDConflict(Base):
    """
    Segregation of Duties Conflict Definition for SOX 404 compliance.
    
    Defines conflicts between roles/permissions:
    - Role pair with conflict type
    - Risk assessment and exception handling
    - Periodic review requirements
    
    Multi-tenant: company_id identifies the organization (tenant).
    References SoDRole via role_a_id and role_b_id.
    """
    __tablename__ = "sod_conflicts"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    role_a_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role_b_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    conflict_type = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    risk_level = Column(String(20), nullable=False, default="medium")
    
    is_approved_exception = Column(Boolean, default=False)
    approval_reason = Column(Text, nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    review_required_by = Column(Date, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SoDConflict {self.id} - {self.conflict_type}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "role_a_id": str(self.role_a_id),
            "role_b_id": str(self.role_b_id),
            "conflict_type": self.conflict_type,
            "description": self.description,
            "risk_level": self.risk_level,
            "is_approved_exception": self.is_approved_exception,
            "approval_reason": self.approval_reason,
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "review_required_by": self.review_required_by.isoformat() if self.review_required_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "needs_review": self._needs_review(),
        }
    
    def _needs_review(self):
        """Check if conflict needs periodic review."""
        if self.review_required_by:
            return date.today() >= self.review_required_by
        return False


class SoDViolation(Base):
    """
    Segregation of Duties Violation Detection for SOX 404 compliance.
    
    Tracks detected violations when users have conflicting roles:
    - Violation detection and resolution
    - User identification
    - Resolution tracking
    
    References SoDConflict via conflict_id.
    """
    __tablename__ = "sod_violations"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conflict_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    
    detected_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SoDViolation {self.id} - User {self.user_name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "conflict_id": str(self.conflict_id),
            "user_id": str(self.user_id),
            "user_name": self.user_name,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "days_open": self._days_open(),
        }
    
    def _days_open(self):
        """Calculate days since violation was detected."""
        if self.detected_at and not self.resolved:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc) if self.detected_at.tzinfo else datetime.utcnow()
            delta = now - self.detected_at
            return delta.days
        return None


class CriticalityLevel(str, enum.Enum):
    """Business process criticality levels (BCB 498, ISO 22301)."""
    TIER_1_CRITICAL = "tier_1_critical"
    TIER_2_ESSENTIAL = "tier_2_essential"
    TIER_3_IMPORTANT = "tier_3_important"
    TIER_4_STANDARD = "tier_4_standard"


class DRPlanStatus(str, enum.Enum):
    """Disaster Recovery Plan status."""
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    RETIRED = "retired"


class ContinuityTestType(str, enum.Enum):
    """Types of business continuity tests (ISO 22301)."""
    TABLETOP = "tabletop"
    WALKTHROUGH = "walkthrough"
    SIMULATION = "simulation"
    FULL_TEST = "full_test"


class ContinuityTestStatus(str, enum.Enum):
    """Status of continuity tests."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BusinessProcess(Base):
    """
    Business Process for BCN/PRD (BCB 498, ISO 22301).
    
    Tracks critical business processes with:
    - Process identification and criticality
    - Recovery objectives (RTO, RPO, MTPD)
    - Dependencies and backup procedures
    - Test tracking
    
    Multi-tenant: company_id identifies the organization (tenant).
    """
    __tablename__ = "business_processes"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    process_code = Column(String(50), nullable=False, index=True)
    process_name = Column(String(500), nullable=False)
    department = Column(String(255), nullable=True)
    
    criticality = Column(String(20), nullable=False, default="tier_4_standard", index=True)
    
    rto_hours = Column(Integer, nullable=True)
    rpo_hours = Column(Integer, nullable=True)
    mtpd_hours = Column(Integer, nullable=True)
    
    dependencies = Column(ARRAY(UUID(as_uuid=True)), default=list)
    
    responsible_team = Column(String(255), nullable=True)
    backup_procedures = Column(Text, nullable=True)
    
    last_tested_at = Column(DateTime, nullable=True)
    next_test_due = Column(Date, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<BusinessProcess {self.process_code} - {self.process_name}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "process_code": self.process_code,
            "process_name": self.process_name,
            "department": self.department,
            "criticality": self.criticality,
            "rto_hours": self.rto_hours,
            "rpo_hours": self.rpo_hours,
            "mtpd_hours": self.mtpd_hours,
            "dependencies": [str(d) for d in self.dependencies] if self.dependencies else [],
            "responsible_team": self.responsible_team,
            "backup_procedures": self.backup_procedures,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "next_test_due": self.next_test_due.isoformat() if self.next_test_due else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "test_overdue": self._test_overdue(),
        }
    
    def _test_overdue(self):
        """Check if process test is overdue."""
        if self.next_test_due:
            return date.today() > self.next_test_due
        return False


class DisasterRecoveryPlan(Base):
    """
    Disaster Recovery Plan for BCB 498 and ISO 22301 compliance.
    
    Tracks DR plans with:
    - Plan versioning and approval workflow
    - Recovery steps and contact lists
    - Test history and results
    
    Multi-tenant: company_id identifies the organization (tenant).
    """
    __tablename__ = "disaster_recovery_plans"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    plan_name = Column(String(500), nullable=False)
    version = Column(String(20), nullable=False)
    
    status = Column(String(20), nullable=False, default="draft", index=True)
    
    scope = Column(Text, nullable=True)
    recovery_steps = Column(JSON, default=list)
    contact_list = Column(JSON, default=list)
    
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    last_tested_at = Column(DateTime, nullable=True)
    test_results = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<DisasterRecoveryPlan {self.plan_name} v{self.version}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "plan_name": self.plan_name,
            "version": self.version,
            "status": self.status,
            "scope": self.scope,
            "recovery_steps": self.recovery_steps or [],
            "contact_list": self.contact_list or [],
            "approved_by": str(self.approved_by) if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "test_results": self.test_results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_approved": self.status in ["approved", "active"],
        }


class ContinuityTest(Base):
    """
    Business Continuity Test for BCB 498 and ISO 22301 compliance.
    
    Tracks continuity/DR tests with:
    - Test scheduling and execution
    - Participant tracking
    - Findings and improvement actions
    
    Multi-tenant: company_id identifies the organization (tenant).
    Optionally references DisasterRecoveryPlan via plan_id.
    """
    __tablename__ = "continuity_tests"
    __table_args__ = {"extend_existing": True}  # canonical 2026-05-24 — defense-in-depth contra hot-reload re-import
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    plan_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    test_type = Column(String(20), nullable=False, index=True)
    test_name = Column(String(500), nullable=False)
    
    scheduled_date = Column(Date, nullable=False)
    executed_date = Column(Date, nullable=True)
    
    status = Column(String(20), nullable=False, default="scheduled", index=True)
    
    participants = Column(ARRAY(String), default=list)
    
    findings = Column(Text, nullable=True)
    improvements_identified = Column(JSON, default=list)
    next_steps = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ContinuityTest {self.test_name} - {self.status}>"
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "company_id": str(self.company_id),
            "plan_id": str(self.plan_id) if self.plan_id else None,
            "test_type": self.test_type,
            "test_name": self.test_name,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "executed_date": self.executed_date.isoformat() if self.executed_date else None,
            "status": self.status,
            "participants": self.participants or [],
            "findings": self.findings,
            "improvements_identified": self.improvements_identified or [],
            "next_steps": self.next_steps,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_overdue": self._is_overdue(),
        }
    
    def _is_overdue(self):
        """Check if test is past scheduled date and not executed."""
        if self.scheduled_date and self.status == "scheduled":
            return date.today() > self.scheduled_date
        return False
