"""Coverage tests for app/schemas/observability.py — Pydantic models."""
import pytest
from app.schemas.observability import (
    AIInferenceLogResponse,
    AIInferenceLogListResponse,
    AIInferenceStatsResponse,
    BiasAuditCreate,
    BiasAuditPublish,
    BiasAuditReportResponse,
    BiasAuditReportListResponse,
    BiasAuditSummaryResponse,
    BiasResultItem,
    ComplianceControlResponse,
    ComplianceControlListResponse,
    ComplianceControlUpdate,
    ComplianceSummaryResponse,
    ConsentCreate,
    ConsentRecordResponse,
    ConsentRecordListResponse,
    ConsentRevoke,
    DataAccessLogResponse,
    DataAccessLogListResponse,
    DataAccessStatsResponse,
    IncidentCreate,
    IncidentReportResponse,
    IncidentReportListResponse,
    IncidentResolve,
    IncidentUpdate,
    ModelEvaluationResponse,
    ModelEvaluationListResponse,
    ModelEvaluationSummaryResponse,
    ObservabilityDashboardResponse,
)


class TestBiasResultItem:
    def test_basic(self):
        m = BiasResultItem(score=0.85, status="clear")
        assert m.score == pytest.approx(0.85)
        assert m.status == "clear"

    def test_concern(self):
        m = BiasResultItem(score=0.45, status="concern")
        assert m.status == "concern"

    def test_consider(self):
        m = BiasResultItem(score=0.65, status="consider")
        assert m.status == "consider"


class TestAIInferenceLogResponse:
    def test_basic(self):
        m = AIInferenceLogResponse(
            id="log-001",
            company_id="co-001",
            agent_type="screening",
        )
        assert m.id == "log-001"
        assert m.agent_type == "screening"

    def test_optional_fields(self):
        m = AIInferenceLogResponse(
            id="log-002",
            company_id="co-002",
            agent_type="ranking",
        )
        assert m.id == "log-002"


class TestAIInferenceLogListResponse:
    def test_empty(self):
        m = AIInferenceLogListResponse(logs=[], total=0, limit=20, offset=0)
        assert m.logs == []
        assert m.total == 0

    def test_with_logs(self):
        log = AIInferenceLogResponse(
            id="l1", company_id="co-001", agent_type="bias_check"
        )
        m = AIInferenceLogListResponse(logs=[log], total=1, limit=10, offset=0)
        assert m.total == 1


class TestAIInferenceStatsResponse:
    def test_basic(self):
        m = AIInferenceStatsResponse(
            total_inferences=500,
            by_agent_type={"screening": 300, "ranking": 200},
            by_decision_type={"auto": 400, "human": 100},
            total_tokens_used=150000,
            human_override_count=50,
            human_override_rate=0.1,
            bias_flags_count=5,
        )
        assert m.total_inferences == 500
        assert m.human_override_rate == pytest.approx(0.1)
        assert m.bias_flags_count == 5


class TestBiasAuditCreate:
    def test_basic(self):
        m = BiasAuditCreate(
            audit_type="demographic_parity",
            audit_date="2024-06-01",
            auditor="Ana Silva",
        )
        assert m.audit_type == "demographic_parity"
        assert m.auditor == "Ana Silva"

    def test_with_findings(self):
        m = BiasAuditCreate(
            audit_type="equalized_odds",
            audit_date="2024-07-01",
            auditor="Carlos",
            overall_score=0.92,
            recommendations=["Improve data diversity"],
        )
        assert m.overall_score == pytest.approx(0.92)
        assert len(m.recommendations) == 1


class TestBiasAuditPublish:
    def test_empty(self):
        m = BiasAuditPublish()
        assert m is not None


class TestBiasAuditReportResponse:
    def test_basic(self):
        m = BiasAuditReportResponse(
            id="audit-001",
            company_id="co-001",
            audit_type="demographic_parity",
            auditor="Ana",
        )
        assert m.id == "audit-001"
        assert m.audit_type == "demographic_parity"


class TestBiasAuditReportListResponse:
    def test_empty(self):
        m = BiasAuditReportListResponse(audits=[], total=0, limit=20, offset=0)
        assert m.audits == []

    def test_with_items(self):
        audit = BiasAuditReportResponse(
            id="a1", company_id="co-001", audit_type="dp", auditor="Ana"
        )
        m = BiasAuditReportListResponse(audits=[audit], total=1, limit=10, offset=0)
        assert m.total == 1


class TestBiasAuditSummaryResponse:
    def test_basic(self):
        m = BiasAuditSummaryResponse(total_audits=10)
        assert m.total_audits == 10

    def test_full(self):
        m = BiasAuditSummaryResponse(
            total_audits=5,
            latest_overall_score=0.88,
            by_audit_type={"demographic": 3, "equalized": 2},
            compliance_coverage=["LGPD", "SOC2"],
            public_audits_count=2,
        )
        assert m.latest_overall_score == pytest.approx(0.88)
        assert m.public_audits_count == 2


class TestComplianceControlResponse:
    def test_basic(self):
        m = ComplianceControlResponse(
            id="ctrl-001",
            framework="LGPD",
            control_id="LGPD-001",
            control_name="Data Protection Officer",
            status="implemented",
        )
        assert m.id == "ctrl-001"
        assert m.status == "implemented"


class TestComplianceControlListResponse:
    def test_empty(self):
        m = ComplianceControlListResponse(controls=[], total=0, limit=20, offset=0)
        assert m.controls == []


class TestComplianceControlUpdate:
    def test_empty(self):
        m = ComplianceControlUpdate()
        assert m is not None

    def test_update(self):
        m = ComplianceControlUpdate(status="partial", evidence_url="https://docs.co.com/doc.pdf")
        assert m.status == "partial"
        assert m.evidence_url == "https://docs.co.com/doc.pdf"


class TestComplianceSummaryResponse:
    def test_basic(self):
        m = ComplianceSummaryResponse(
            total_controls=100,
            by_framework={"LGPD": {"implemented": 20, "partial": 10}, "SOC2": {"implemented": 50, "pending": 20}},
            by_status={"implemented": 70, "partial": 20, "pending": 10},
            overdue_reviews=5,
            upcoming_reviews=10,
        )
        assert m.total_controls == 100
        assert m.overdue_reviews == 5


class TestConsentCreate:
    def test_basic(self):
        m = ConsentCreate(
            candidate_id="cand-001",
            consent_type="data_processing",
        )
        assert m.candidate_id == "cand-001"
        assert m.consent_type == "data_processing"

    def test_with_version(self):
        m = ConsentCreate(
            candidate_id="cand-002",
            consent_type="marketing",
            version="v2.0",
            source="web",
        )
        assert m.version == "v2.0"
        assert m.source == "web"


class TestConsentRecordResponse:
    def test_basic(self):
        m = ConsentRecordResponse(
            id="cons-001",
            company_id="co-001",
            candidate_id="cand-001",
            consent_type="data_processing",
        )
        assert m.id == "cons-001"
        assert m.consent_type == "data_processing"


class TestConsentRecordListResponse:
    def test_empty(self):
        m = ConsentRecordListResponse(consents=[], total=0, limit=20, offset=0)
        assert m.consents == []

    def test_with_items(self):
        c = ConsentRecordResponse(
            id="c1", company_id="co-001", candidate_id="cand-001",
            consent_type="data_processing",
        )
        m = ConsentRecordListResponse(consents=[c], total=1, limit=10, offset=0)
        assert m.total == 1


class TestConsentRevoke:
    def test_empty(self):
        m = ConsentRevoke()
        assert m is not None

    def test_with_reason(self):
        m = ConsentRevoke(reason="Candidate request")
        assert m.reason == "Candidate request"


class TestDataAccessLogResponse:
    def test_basic(self):
        m = DataAccessLogResponse(
            id="dal-001",
            company_id="co-001",
            user_id="user-001",
            data_type="candidate_profile",
            operation="read",
        )
        assert m.id == "dal-001"
        assert m.operation == "read"


class TestDataAccessLogListResponse:
    def test_empty(self):
        m = DataAccessLogListResponse(logs=[], total=0, limit=20, offset=0)
        assert m.logs == []


class TestDataAccessStatsResponse:
    def test_basic(self):
        m = DataAccessStatsResponse(
            total_accesses=1000,
            by_data_type={"candidate_profile": 600, "job": 400},
            by_operation={"read": 900, "write": 100},
            by_legal_basis={"consent": 800, "legitimate_interest": 200},
            unique_users=25,
            unique_data_subjects=300,
        )
        assert m.total_accesses == 1000
        assert m.unique_users == 25


class TestIncidentCreate:
    def test_basic(self):
        m = IncidentCreate(
            incident_type="data_breach",
            severity="high",
            description="Unauthorized access detected",
        )
        assert m.incident_type == "data_breach"
        assert m.severity == "high"

    def test_low_severity(self):
        m = IncidentCreate(
            incident_type="policy_violation",
            severity="low",
            description="Minor config misconfiguration",
        )
        assert m.severity == "low"


class TestIncidentReportResponse:
    def test_basic(self):
        m = IncidentReportResponse(
            id="inc-001",
            incident_type="data_breach",
            severity="critical",
            description="Breach detected",
        )
        assert m.id == "inc-001"
        assert m.severity == "critical"


class TestIncidentReportListResponse:
    def test_empty(self):
        m = IncidentReportListResponse(incidents=[], total=0, limit=20, offset=0)
        assert m.incidents == []

    def test_with_items(self):
        inc = IncidentReportResponse(
            id="i1", incident_type="breach", severity="high",
            description="desc",
        )
        m = IncidentReportListResponse(incidents=[inc], total=1, limit=10, offset=0)
        assert m.total == 1


class TestIncidentResolve:
    def test_empty(self):
        m = IncidentResolve()
        assert m is not None

    def test_with_notes(self):
        m = IncidentResolve(
            root_cause="Misconfigured IAM policy",
            remediation_actions=["Revoke tokens", "Audit access"],
            resolution_notes="Fixed by rotating credentials",
        )
        assert m.resolution_notes == "Fixed by rotating credentials"
        assert len(m.remediation_actions) == 2


class TestIncidentUpdate:
    def test_empty(self):
        m = IncidentUpdate()
        assert m is not None

    def test_update(self):
        m = IncidentUpdate(status="resolved", severity="low")
        assert m.status == "resolved"


class TestModelEvaluationResponse:
    def test_basic(self):
        m = ModelEvaluationResponse(
            id="eval-001",
            model_version="v1.2.3",
            evaluation_type="fairness",
            metric_name="demographic_parity",
        )
        assert m.id == "eval-001"
        assert m.metric_name == "demographic_parity"


class TestModelEvaluationListResponse:
    def test_empty(self):
        m = ModelEvaluationListResponse(evaluations=[], total=0, limit=20, offset=0)
        assert m.evaluations == []


class TestModelEvaluationSummaryResponse:
    def test_basic(self):
        m = ModelEvaluationSummaryResponse(
            total_evaluations=50,
            by_dimension={"fairness": {"pass": 18, "fail": 2}, "accuracy": {"pass": 28, "fail": 2}},
            by_evaluation_type={"automated": 40, "human": 10},
            pass_rate=0.88,
        )
        assert m.total_evaluations == 50
        assert m.pass_rate == pytest.approx(0.88)


class TestObservabilityDashboardResponse:
    def test_basic(self):
        m = ObservabilityDashboardResponse(
            ai_inference={"total_inferences": 100, "by_agent_type": {}},
            data_access={"total_accesses": 200, "unique_users": 10},
            consents={"total": 100, "active": 80},
            incidents={"total": 2, "open": 1},
            evaluations={"total_evaluations": 20, "pass_rate": 0.9},
            compliance={"total_controls": 50, "overdue_reviews": 0},
            alerts=[],
        )
        assert m.ai_inference["total_inferences"] == 100
        assert m.data_access["unique_users"] == 10
        assert m.compliance["total_controls"] == 50
        assert m.alerts == []
