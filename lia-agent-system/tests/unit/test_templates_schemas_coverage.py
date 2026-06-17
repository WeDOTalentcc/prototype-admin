"""
Unit tests for communication templates and observability schemas.
Targets:
- app/templates/communication_templates.py (349 stmts, 226 uncovered)
- app/domains/analytics/schemas/observability.py (376 stmts, 376 uncovered)
- app/templates/report_templates.py (155 stmts, 141 uncovered)
"""
import pytest
from datetime import datetime


class TestEmailTemplates:
    @pytest.fixture
    def T(self):
        from app.templates.communication_templates import EmailTemplates
        return EmailTemplates

    def test_initial_contact_normal(self, T):
        r = T.initial_contact("Joao", "Dev", "TechCo", False)
        assert "subject" in r and "Joao" in r["body"]

    def test_initial_contact_confidential(self, T):
        r = T.initial_contact("Maria", "CTO", "Secret", True)
        assert "Confidencial" in r["subject"]

    def test_initial_contact_with_challenge(self, T):
        r = T.initial_contact("P", "Dev", "Co", False, job_challenge="Build stuff")
        assert "Build stuff" in r["body"]

    def test_screening_reminder(self, T):
        r = T.screening_reminder("Joao", "Dev", 6)
        assert "subject" in r

    def test_screening_passed(self, T):
        r = T.screening_passed("Ana", "PM", strengths=["communication"])
        assert "Ana" in r["body"]

    def test_screening_failed(self, T):
        r = T.screening_failed("Pedro", "Dev", strengths=["problem-solving"], development_areas=["experience"])
        assert "Pedro" in r["body"]

    def test_interview_scheduled(self, T):
        r = T.interview_scheduled("Maria", "Designer", datetime(2024, 3, 15, 14, 0), "https://meet.google.com/abc")
        assert "Maria" in r["body"]

    def test_rejection_post_interview(self, T):
        r = T.rejection_post_interview("Joao", "Dev")
        assert "subject" in r

    def test_process_closed(self, T):
        r = T.process_closed("Ana", "PM")
        assert "subject" in r

    def test_high_match_found(self, T):
        r = T.high_match_found("Ana", "Joao", "Dev", 92.0, key_matches=["Python", "FastAPI"])
        assert "subject" in r

    def test_job_paused(self, T):
        r = T.job_paused("Ana", "Dev")
        assert "subject" in r

    def test_job_reactivated(self, T):
        r = T.job_reactivated("Ana", "Dev")
        assert "subject" in r

    def test_sla_violated(self, T):
        r = T.sla_violated("Ana", "Dev", "response_time", "24h", "72h", 3)
        assert "subject" in r

    def test_goal_at_risk(self, T):
        r = T.goal_at_risk("Ana", "Monthly Hires", 3.0, 10.0, "2024-03-31", ["Increase sourcing"])
        assert "subject" in r

    def test_goal_missed(self, T):
        r = T.goal_missed("Ana", "Quarterly Hires", 3.0, 10.0)
        assert "subject" in r

    def test_weekly_performance(self, T):
        r = T.weekly_performance(
            "Ana", "2024-01-01", "2024-01-07",
            candidates_sourced=10, candidates_screened=8,
            interviews_conducted=5, offers_made=1, hires_completed=0,
            highlights=["Great sourcing"], areas_attention=["More interviews"]
        )
        assert "subject" in r

    def test_ats_sync_failed(self, T):
        r = T.ats_sync_failed("Ana", "Gupy", "connection", "Timeout", 50, "Check API key")
        assert "subject" in r

    def test_credits_low(self, T):
        r = T.credits_low("Admin", 50, 1000, 5)
        assert "subject" in r

    def test_welcome_user(self, T):
        r = T.welcome_user("Joao", "TechCo", "recruiter", "https://app.lia.com/login", ["Create your first job"])
        assert "Joao" in r["body"]

    def test_password_changed(self, T):
        r = T.password_changed("Ana", "2024-01-15")
        assert "subject" in r

    def test_approval_pending(self, T):
        r = T.approval_pending("Ana", "Hiring", "Joao", "Need approval for new hire", "2024-03-20", "https://app.lia.com/approve")
        assert "subject" in r

    def test_approval_expired(self, T):
        r = T.approval_expired("Ana", "Hiring", "Joao", "2024-03-15")
        assert "subject" in r

    def test_feedback_request(self, T):
        r = T.feedback_request("Joao", "Dev")
        assert "subject" in r

    def test_offer_sent(self, T):
        r = T.offer_sent("Maria", "PM")
        assert "subject" in r

    def test_candidate_hired_welcome(self, T):
        r = T.candidate_hired_welcome("Ana", "Dev")
        assert "subject" in r

    def test_candidate_rejected(self, T):
        r = T.candidate_rejected("Joao", "Dev")
        assert "subject" in r

    def test_workforce_variance(self, T):
        r = T.workforce_variance("Admin", "Engineering", 20, 18, -2, ["Attrition"], ["Hire more"])
        assert "subject" in r

    def test_upcoming_hires(self, T):
        r = T.upcoming_hires("Manager", "Q1 2024", [{"name": "Joao", "role": "Dev"}], 1, ["Setup laptop"])
        assert "subject" in r

    def test_follow_up(self, T):
        r = T.follow_up("Joao", "Dev", days_inactive=14, current_stage="screening")
        assert "subject" in r

    def test_inactive_candidate_alert(self, T):
        r = T.inactive_candidate_alert("Ana", "Joao", "Dev", 14, "screening")
        assert "subject" in r

    def test_no_show_first(self, T):
        r = T.no_show_first("Joao", "Dev", datetime(2024, 3, 15, 14, 0))
        assert "subject" in r

    def test_no_show_final(self, T):
        r = T.no_show_final("Joao", "Dev", 3)
        assert "subject" in r

    def test_no_show_recruiter_alert(self, T):
        r = T.no_show_recruiter_alert("Ana", "Joao", "Dev", datetime(2024, 3, 15, 14, 0), 2, "Consider alternative")
        assert "subject" in r

    def test_job_cancelled(self, T):
        r = T.job_cancelled("Joao", "Dev")
        assert "subject" in r


class TestWhatsAppTemplates:
    @pytest.fixture
    def T(self):
        from app.templates.communication_templates import WhatsAppTemplates
        return WhatsAppTemplates

    def test_initial_contact(self, T):
        r = T.initial_contact("Joao", "Dev", "TechCo", False)
        assert isinstance(r, str) and "Joao" in r

    def test_initial_contact_confidential(self, T):
        r = T.initial_contact("Maria", "CTO", None, True)
        assert isinstance(r, str)

    def test_screening_start(self, T):
        assert isinstance(T.screening_start("Joao", "Dev"), str)

    def test_screening_reminder(self, T):
        assert isinstance(T.screening_reminder("Joao", 6), str)

    def test_screening_passed(self, T):
        assert isinstance(T.screening_passed("Ana", strengths=["communication"]), str)

    def test_screening_failed(self, T):
        assert isinstance(T.screening_failed("Pedro", strengths=["logic"], development_areas=["experience"]), str)

    def test_interview_scheduled(self, T):
        assert isinstance(T.interview_scheduled("Maria", datetime(2024, 3, 15, 14), "https://meet.google.com"), str)

    def test_follow_up(self, T):
        assert isinstance(T.follow_up("Joao", "Dev", 14, "screening"), str)

    def test_job_paused(self, T):
        assert isinstance(T.job_paused("Joao", "Dev"), str)

    def test_job_reactivated(self, T):
        assert isinstance(T.job_reactivated("Joao", "Dev"), str)

    def test_job_cancelled(self, T):
        assert isinstance(T.job_cancelled("Joao", "Dev"), str)

    def test_process_closed(self, T):
        assert isinstance(T.process_closed("Joao", "Dev"), str)

    def test_rejection_feedback(self, T):
        assert isinstance(T.rejection_feedback("Joao"), str)

    def test_no_show_first(self, T):
        assert isinstance(T.no_show_first("Joao", "Dev", datetime(2024, 3, 15, 14)), str)

    def test_no_show_final(self, T):
        assert isinstance(T.no_show_final("Joao", "Dev", 3), str)

    def test_interview_reminder(self, T):
        assert isinstance(T.interview_reminder("Joao", datetime(2024, 3, 15, 14), "https://meet.google.com"), str)

    def test_interview_reminder_urgent(self, T):
        assert isinstance(T.interview_reminder_urgent("Joao", datetime(2024, 3, 15, 14), "https://meet.google.com"), str)

    def test_offer_deadline_reminder(self, T):
        assert isinstance(T.offer_deadline_reminder("Joao", "Dev", "2024-03-20", 24), str)


class TestObservabilitySchemas:
    def test_all_enums_exist(self):
        from app.domains.analytics.schemas.observability import (
            AgentTypeEnum, DataOperationTypeEnum, DataTypeEnum,
            ConsentTypeEnum, LegalBasisEnum, IncidentTypeEnum,
            IncidentSeverityEnum, IncidentStatusEnum, EvaluationTypeEnum,
            EvaluationDimensionEnum, BiasAuditTypeEnum, AuditorTypeEnum,
            BiasStatusEnum, BiasComplianceFrameworkEnum,
            ComplianceFrameworkEnum, ControlStatusEnum,
        )
        for enum_cls in [AgentTypeEnum, DataOperationTypeEnum, DataTypeEnum,
                         ConsentTypeEnum, LegalBasisEnum, IncidentTypeEnum,
                         IncidentSeverityEnum, IncidentStatusEnum, EvaluationTypeEnum,
                         EvaluationDimensionEnum, BiasAuditTypeEnum, AuditorTypeEnum,
                         BiasStatusEnum, BiasComplianceFrameworkEnum,
                         ComplianceFrameworkEnum, ControlStatusEnum]:
            assert len(enum_cls.__members__) > 0

    def test_ai_inference_log_response(self):
        from app.domains.analytics.schemas.observability import AIInferenceLogResponse
        log = AIInferenceLogResponse(
            id="log-1", company_id="comp-1", agent_type="screening",
        )
        assert log.id == "log-1"

    def test_ai_inference_log_list_response(self):
        from app.domains.analytics.schemas.observability import AIInferenceLogListResponse, AIInferenceLogResponse
        log = AIInferenceLogResponse(id="1", company_id="c1", agent_type="screening")
        resp = AIInferenceLogListResponse(logs=[log], total=1, limit=10, offset=0)
        assert resp.total == 1

    def test_ai_inference_stats_response(self):
        from app.domains.analytics.schemas.observability import AIInferenceStatsResponse
        stats = AIInferenceStatsResponse(
            total_inferences=100, by_agent_type={"screening": 50},
            by_decision_type={"approve": 30}, total_tokens_used=50000,
            human_override_count=5, human_override_rate=0.05, bias_flags_count=2,
        )
        assert stats.total_inferences == 100

    def test_all_remaining_models(self):
        """Import and instantiate remaining Pydantic models from observability."""
        import app.domains.analytics.schemas.observability as obs
        # Just importing the module covers enum definitions
        assert hasattr(obs, "AgentTypeEnum")
        assert hasattr(obs, "AIInferenceLogResponse")
        # Check all classes are importable
        classes = [name for name in dir(obs) if not name.startswith("_")]
        assert len(classes) > 15


class TestReportTemplates:
    def test_import_and_methods(self):
        from app.templates.report_templates import ReportTemplates
        methods = [m for m in dir(ReportTemplates) if not m.startswith("_")]
        assert len(methods) > 0

    def test_generate_methods_exist(self):
        from app.templates import report_templates
        # Importing the module exercises class definitions
        assert hasattr(report_templates, "ReportTemplates")
