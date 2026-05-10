"""Coverage tests for app/schemas/lgpd_compliance.py — enums and Pydantic models."""
import pytest
from datetime import date, datetime
from app.schemas.lgpd_compliance import (
    BreachSeverityEnum,
    BreachStatusEnum,
    DecisionTypeEnum,
    DPORegistryCreate,
    DPORegistryUpdate,
    BreachNotificationCreate,
    BreachNotificationUpdate,
    ANPDNotification,
    SubjectsNotification,
    BreachResolution,
    AutomatedDecisionCreate,
    HumanReviewRequest,
    HumanReviewComplete,
    LGPDComplianceStats,
)


class TestBreachSeverityEnum:
    def test_low(self):
        assert BreachSeverityEnum.LOW == "low"

    def test_medium(self):
        assert BreachSeverityEnum.MEDIUM == "medium"

    def test_high(self):
        assert BreachSeverityEnum.HIGH == "high"

    def test_critical(self):
        assert BreachSeverityEnum.CRITICAL == "critical"


class TestBreachStatusEnum:
    def test_detected(self):
        assert BreachStatusEnum.DETECTED == "detected"

    def test_investigating(self):
        assert BreachStatusEnum.INVESTIGATING == "investigating"

    def test_notified(self):
        assert BreachStatusEnum.NOTIFIED == "notified"

    def test_resolved(self):
        assert BreachStatusEnum.RESOLVED == "resolved"


class TestDecisionTypeEnum:
    def test_screening(self):
        assert DecisionTypeEnum.SCREENING == "screening"

    def test_ranking(self):
        assert DecisionTypeEnum.RANKING == "ranking"

    def test_rejection(self):
        assert DecisionTypeEnum.REJECTION == "rejection"


class TestDPORegistryCreate:
    def test_basic(self):
        m = DPORegistryCreate(
            dpo_name="Maria Silva",
            dpo_email="dpo@company.com.br",
            appointment_date=date(2024, 1, 15),
        )
        assert m.dpo_name == "Maria Silva"
        assert m.dpo_email == "dpo@company.com.br"
        assert m.appointment_date == date(2024, 1, 15)

    def test_with_optional(self):
        m = DPORegistryCreate(
            dpo_name="João DPO",
            dpo_email="joao@empresa.com",
            appointment_date=date(2024, 6, 1),
            dpo_phone="+55 11 99999-0000",
            public_contact_url="https://empresa.com/contato",
        )
        assert m.dpo_phone == "+55 11 99999-0000"
        assert m.public_contact_url == "https://empresa.com/contato"

    def test_phone_is_optional(self):
        m = DPORegistryCreate(
            dpo_name="Ana DPO",
            dpo_email="ana@company.com",
            appointment_date=date(2025, 1, 1),
        )
        assert m.dpo_phone is None


class TestDPORegistryUpdate:
    def test_all_optional(self):
        m = DPORegistryUpdate()
        assert m.dpo_name is None

    def test_update_email(self):
        m = DPORegistryUpdate(dpo_email="new@company.com")
        assert m.dpo_email == "new@company.com"


class TestBreachNotificationCreate:
    def test_basic(self):
        m = BreachNotificationCreate(
            breach_detected_at=datetime(2024, 3, 15, 10, 30),
            breach_description="Unauthorized access detected on candidate database",
        )
        assert m.breach_description.startswith("Unauthorized")
        assert m.severity == BreachSeverityEnum.MEDIUM  # default

    def test_with_affected_count(self):
        m = BreachNotificationCreate(
            breach_detected_at=datetime(2024, 5, 1, 8, 0),
            breach_description="SQL injection attack exposed personal data of candidates",
            affected_data_types=["personal_info", "cv", "contact_info"],
            affected_count=250,
            severity=BreachSeverityEnum.HIGH,
        )
        assert m.affected_count == 250
        assert m.severity == BreachSeverityEnum.HIGH
        assert "personal_info" in m.affected_data_types

    def test_default_data_types_empty(self):
        m = BreachNotificationCreate(
            breach_detected_at=datetime(2024, 1, 1),
            breach_description="Minor unauthorized access to non-sensitive logs",
        )
        assert m.affected_data_types == []
        assert m.affected_count is None


class TestBreachNotificationUpdate:
    def test_all_optional(self):
        m = BreachNotificationUpdate()
        assert m.status is None

    def test_update_status(self):
        m = BreachNotificationUpdate(status=BreachStatusEnum.RESOLVED)
        assert m.status == "resolved"


class TestANPDNotification:
    def test_empty(self):
        m = ANPDNotification()
        assert m.protocol_number is None
        assert m.notification_details is None

    def test_with_protocol(self):
        m = ANPDNotification(
            protocol_number="ANPD-2024-001",
            notification_details="Notified via portal.anpd.gov.br",
        )
        assert m.protocol_number == "ANPD-2024-001"
        assert "portal" in m.notification_details


class TestSubjectsNotification:
    def test_empty(self):
        m = SubjectsNotification()
        assert m.notification_method is None
        assert m.subjects_notified_count is None

    def test_with_data(self):
        m = SubjectsNotification(
            notification_method="email",
            subjects_notified_count=150,
        )
        assert m.subjects_notified_count == 150
        assert m.notification_method == "email"


class TestBreachResolution:
    def test_empty(self):
        m = BreachResolution()
        assert m.resolution_notes is None
        assert m.remediation_actions is None

    def test_with_notes(self):
        m = BreachResolution(
            resolution_notes="Vulnerability patched, access revoked",
            remediation_actions=["patch_applied", "passwords_reset", "audit_logs_reviewed"],
        )
        assert "patched" in m.resolution_notes
        assert "patch_applied" in m.remediation_actions


class TestAutomatedDecisionCreate:
    def test_basic(self):
        m = AutomatedDecisionCreate(
            decision_type=DecisionTypeEnum.SCREENING,
        )
        assert m.decision_type == "screening"

    def test_with_candidate(self):
        m = AutomatedDecisionCreate(
            decision_type=DecisionTypeEnum.RANKING,
            candidate_id="cand-001",
            vacancy_id="vac-002",
            ai_model_used="claude-3-sonnet",
            input_criteria={"score": 85},
            decision_criteria={"threshold": 70},
            explanation_text="Candidate meets minimum criteria",
        )
        assert m.candidate_id == "cand-001"
        assert m.ai_model_used == "claude-3-sonnet"
        assert m.explanation_text == "Candidate meets minimum criteria"

    def test_defaults(self):
        m = AutomatedDecisionCreate(
            decision_type=DecisionTypeEnum.REJECTION,
        )
        assert m.input_criteria == {}
        assert m.decision_criteria == {}
        assert m.candidate_id is None


class TestHumanReviewRequest:
    def test_empty(self):
        m = HumanReviewRequest()
        assert m.reason is None
        assert m.requested_by is None

    def test_with_data(self):
        m = HumanReviewRequest(
            reason="Candidate appeals screening decision",
            requested_by="user-manager-001",
        )
        assert m.reason == "Candidate appeals screening decision"
        assert m.requested_by == "user-manager-001"


class TestHumanReviewComplete:
    def test_basic(self):
        m = HumanReviewComplete(
            decision="approved",
            reviewer_id="user-001",
        )
        assert m.decision == "approved"
        assert m.reviewer_id == "user-001"

    def test_with_notes(self):
        m = HumanReviewComplete(
            decision="rejected",
            reviewer_id="user-002",
            notes="Does not meet criteria despite high score",
        )
        assert m.notes == "Does not meet criteria despite high score"


class TestLGPDComplianceStats:
    def test_basic(self):
        m = LGPDComplianceStats(
            dpo_registered=True,
            dpo_active=True,
            total_breaches=2,
            open_breaches=0,
            breaches_pending_anpd=0,
            breaches_deadline_exceeded=0,
            total_automated_decisions=100,
            pending_human_reviews=5,
            completed_human_reviews=15,
        )
        assert m.dpo_registered is True
        assert m.total_automated_decisions == 100
        assert m.pending_human_reviews == 5

    def test_no_dpo(self):
        m = LGPDComplianceStats(
            dpo_registered=False,
            dpo_active=False,
            total_breaches=0,
            open_breaches=0,
            breaches_pending_anpd=0,
            breaches_deadline_exceeded=0,
            total_automated_decisions=0,
            pending_human_reviews=0,
            completed_human_reviews=0,
        )
        assert m.dpo_registered is False
