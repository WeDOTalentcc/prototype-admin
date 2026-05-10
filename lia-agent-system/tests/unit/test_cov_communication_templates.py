"""Coverage tests for app/templates/communication_templates.py — all static methods."""
import pytest
from datetime import datetime
_DT = datetime(2025, 6, 15, 14, 0)
from app.templates.communication_templates import (
    DATA_PROCESSING_NOTICE,
    WSI_INITIAL_CONTACT_LGPD_NOTICE,
    EmailTemplates,
    WhatsAppTemplates,
)


class TestModuleConstants:
    def test_data_processing_notice_exists(self):
        assert DATA_PROCESSING_NOTICE
        assert "LGPD" in DATA_PROCESSING_NOTICE
        assert "WeDOTalent" in DATA_PROCESSING_NOTICE

    def test_wsi_lgpd_notice(self):
        assert WSI_INITIAL_CONTACT_LGPD_NOTICE
        assert "IA" in WSI_INITIAL_CONTACT_LGPD_NOTICE


class TestEmailTemplatesInitialContact:
    def test_non_confidential(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Ana Silva",
            job_title="Engenheira de Software",
            company_name="TechCorp",
            is_confidential=False,
        )
        assert "subject" in result
        assert "body" in result
        assert "Ana Silva" in result["body"]
        assert "TechCorp" in result["body"]

    def test_confidential(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Carlos",
            job_title="CTO",
            company_name=None,
            is_confidential=True,
        )
        assert "subject" in result
        assert "confidencial" in result["body"].lower() or "líder" in result["body"].lower()

    def test_with_job_challenge(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Maria",
            job_title="Product Manager",
            company_name="StartupX",
            is_confidential=False,
            job_challenge="Build the next unicorn product",
        )
        assert "Build the next unicorn product" in result["body"]

    def test_with_recruiter_name(self):
        result = EmailTemplates.initial_contact(
            candidate_name="João",
            job_title="Designer",
            company_name="DesignCo",
            is_confidential=False,
            recruiter_name="Paula Recrutadora",
        )
        assert "Paula Recrutadora" in result["body"]


class TestEmailTemplatesScreening:
    def test_screening_passed(self):
        result = EmailTemplates.screening_passed(
            candidate_name="Ana",
            job_title="Dev Senior",
            strengths=["Python", "FastAPI"],
            company_name="TechCo",
        )
        assert "subject" in result
        assert "body" in result
        assert "Ana" in result["body"]

    def test_screening_passed_no_company(self):
        result = EmailTemplates.screening_passed(
            candidate_name="Carlos",
            job_title="Engenheiro",
            strengths=["Java", "Spring"],
        )
        assert "Carlos" in result["body"]

    def test_screening_failed(self):
        result = EmailTemplates.screening_failed(
            candidate_name="Pedro",
            job_title="Analista",
            strengths=["Comunicação"],
            development_areas=["Programação", "SQL"],
        )
        assert "subject" in result
        assert "Pedro" in result["body"]

    def test_screening_reminder(self):
        result = EmailTemplates.screening_reminder(
            candidate_name="Lucia",
            job_title="Recrutadora",
        )
        assert "Lucia" in result["body"]

    def test_screening_reminder_with_hours(self):
        result = EmailTemplates.screening_reminder(
            candidate_name="Ricardo",
            job_title="Analista",
            hours_remaining=24,
        )
        assert "Ricardo" in result["body"]


class TestEmailTemplatesInterview:
    def test_interview_scheduled(self):
        result = EmailTemplates.interview_scheduled(
            candidate_name="Sofia",
            job_title="Designer UX",
            interview_date=_DT,
            interview_link="https://meet.example.com/abc",
        )
        assert "Sofia" in result["body"]

    def test_no_show_first(self):
        result = EmailTemplates.no_show_first(
            candidate_name="Rafael",
            job_title="Backend Dev",
            interview_datetime=_DT,
        )
        assert "Rafael" in result["body"]

    def test_no_show_first_with_link(self):
        result = EmailTemplates.no_show_first(
            candidate_name="Mariana",
            job_title="Analista",
            interview_datetime=_DT,
            reschedule_link="https://cal.example.com",
        )
        assert "Mariana" in result["body"]

    def test_no_show_final(self):
        result = EmailTemplates.no_show_final(
            candidate_name="Fernando",
            job_title="Sales",
            no_show_count=3,
        )
        assert "Fernando" in result["body"]

    def test_no_show_recruiter_alert(self):
        result = EmailTemplates.no_show_recruiter_alert(
            recruiter_name="Ana Recrutadora",
            candidate_name="Bruno",
            job_title="Dev",
            interview_datetime=_DT,
            no_show_count=2,
            recommendation="Desconsiderar candidato",
        )
        assert "Bruno" in result["body"]
        assert "Ana Recrutadora" in result["body"]

    def test_rejection_post_interview(self):
        result = EmailTemplates.rejection_post_interview(
            candidate_name="Camila",
            job_title="Frontend Dev",
        )
        assert "Camila" in result["body"]

    def test_rejection_post_interview_with_feedback(self):
        result = EmailTemplates.rejection_post_interview(
            candidate_name="Diego",
            job_title="Dev",
            feedback="Strong technical skills but communication needs improvement",
        )
        assert "Diego" in result["body"]


class TestEmailTemplatesOfferAndHire:
    def test_offer_sent_minimal(self):
        result = EmailTemplates.offer_sent(
            candidate_name="Elena",
            job_title="Senior Dev",
        )
        assert "Elena" in result["body"]

    def test_offer_sent_full(self):
        result = EmailTemplates.offer_sent(
            candidate_name="Felipe",
            job_title="CTO",
            salary_offered=25000.0,
            start_date="01/07/2025",
            response_deadline="20/06/2025",
            offer_details={"beneficios": "VR + VT", "modalidade": "Remoto"},
            company_name="BigCorp",
        )
        assert "Felipe" in result["body"]
        assert "25" in result["body"]

    def test_candidate_hired_welcome(self):
        result = EmailTemplates.candidate_hired_welcome(
            candidate_name="Gabriela",
            job_title="PM Sênior",
        )
        assert "Gabriela" in result["body"]

    def test_candidate_hired_welcome_full(self):
        result = EmailTemplates.candidate_hired_welcome(
            candidate_name="Henrique",
            job_title="Dev",
            hire_date="01/07/2025",
            department="Engenharia",
            company_name="TechCo",
        )
        assert "Henrique" in result["body"]
        assert "Engenharia" in result["body"]

    def test_candidate_rejected_minimal(self):
        result = EmailTemplates.candidate_rejected(
            candidate_name="Isabela",
            job_title="Designer",
        )
        assert "Isabela" in result["body"]

    def test_candidate_rejected_full(self):
        result = EmailTemplates.candidate_rejected(
            candidate_name="Jorge",
            job_title="Analista",
            rejection_reason="Perfil não adequado",
            rejection_stage="entrevista",
            company_name="Empresa X",
        )
        assert "Jorge" in result["body"]


class TestEmailTemplatesJobStatus:
    def test_job_paused(self):
        result = EmailTemplates.job_paused(
            candidate_name="Karla",
            job_title="Dev",
        )
        assert "Karla" in result["body"]

    def test_job_cancelled(self):
        result = EmailTemplates.job_cancelled(
            candidate_name="Lucas",
            job_title="Analista",
        )
        assert "Lucas" in result["body"]

    def test_job_reactivated_minimal(self):
        result = EmailTemplates.job_reactivated(
            candidate_name="Mariana",
            job_title="Engenheira",
        )
        assert "Mariana" in result["body"]

    def test_job_reactivated_with_steps(self):
        result = EmailTemplates.job_reactivated(
            candidate_name="Nelson",
            job_title="PM",
            next_steps="Entrevista na próxima semana",
        )
        assert "Nelson" in result["body"]

    def test_process_closed(self):
        result = EmailTemplates.process_closed(
            candidate_name="Olivia",
            job_title="Designer",
        )
        assert "Olivia" in result["body"]

    def test_feedback_request(self):
        result = EmailTemplates.feedback_request(
            candidate_name="Paulo",
            job_title="Dev Senior",
        )
        assert "Paulo" in result["body"]


class TestEmailTemplatesAlerts:
    def test_high_match_found(self):
        result = EmailTemplates.high_match_found(
            recruiter_name="Rita Recrutadora",
            candidate_name="Silvia",
            job_title="Frontend Dev",
            match_score=92,
            key_matches=["React", "TypeScript", "Testing"],
        )
        assert "Silvia" in result["body"]
        assert "92" in result["body"]

    def test_inactive_candidate_alert(self):
        result = EmailTemplates.inactive_candidate_alert(
            recruiter_name="Tiago",
            candidate_name="Ursula",
            job_title="Dev",
            days_inactive=14,
            current_stage="triagem",
        )
        assert "Ursula" in result["body"]
        assert "14" in result["body"]

    def test_follow_up(self):
        result = EmailTemplates.follow_up(
            candidate_name="Vanessa",
            job_title="PM",
            days_inactive=7,
            current_stage="entrevista",
        )
        assert "Vanessa" in result["body"]

    def test_credits_low(self):
        result = EmailTemplates.credits_low(
            user_name="William Admin",
            credits_remaining=50,
            credits_limit=1000,
            estimated_days_remaining=3,
        )
        assert "William" in result["body"]
        assert "50" in result["body"]

    def test_ats_sync_failed(self):
        result = EmailTemplates.ats_sync_failed(
            recruiter_name="Xavier",
            ats_name="Greenhouse",
            error_type="AUTH_FAILED",
            error_details="Token expired",
            affected_records=150,
            action_required="Reconectar integração",
        )
        assert "Xavier" in result["body"]
        assert "Greenhouse" in result["body"]


class TestEmailTemplatesPerformance:
    def test_weekly_performance(self):
        result = EmailTemplates.weekly_performance(
            recruiter_name="Yasmin",
            week_start="09/06/2025",
            week_end="15/06/2025",
            candidates_sourced=25,
            candidates_screened=18,
            interviews_conducted=5,
            offers_made=2,
            hires_completed=1,
            highlights=["Fechou 1 posição senior"],
            areas_attention=["Aumentar sourcing"],
        )
        assert "Yasmin" in result["body"]
        assert "25" in result["body"]

    def test_goal_at_risk(self):
        result = EmailTemplates.goal_at_risk(
            recruiter_name="Zara",
            goal_name="20 contratações no mês",
            current_progress=8,
            target=20,
            deadline="30/06/2025",
            suggestions=["Aumentar sourcing", "Acelerar triagem"],
        )
        assert "Zara" in result["body"]

    def test_goal_missed(self):
        result = EmailTemplates.goal_missed(
            recruiter_name="Aaron",
            goal_name="15 contratações",
            achieved=10,
            target=15,
        )
        assert "Aaron" in result["body"]

    def test_sla_violated(self):
        result = EmailTemplates.sla_violated(
            recruiter_name="Bianca",
            job_title="Dev Sênior",
            sla_type="time_to_screen",
            expected_time="48h",
            actual_time="72h",
            candidates_affected=5,
        )
        assert "Bianca" in result["body"]

    def test_upcoming_hires(self):
        result = EmailTemplates.upcoming_hires(
            manager_name="Clara",
            period="Julho 2025",
            hires=[{"name": "Dev A", "start": "01/07"}],
            total_hires=1,
            onboarding_checklist=["Preparar acesso", "Agendar onboarding"],
        )
        assert "Clara" in result["body"]

    def test_workforce_variance(self):
        result = EmailTemplates.workforce_variance(
            manager_name="Daniel",
            department="Engenharia",
            planned_headcount=10,
            actual_headcount=8,
            variance=-2,
            variance_reasons=["Licença inesperada"],
            recommendations=["Contratar 2 pessoas"],
        )
        assert "Daniel" in result["body"]
        assert "Engenharia" in result["body"]


class TestEmailTemplatesAdminNotifications:
    def test_welcome_user(self):
        result = EmailTemplates.welcome_user(
            user_name="Eduardo",
            company_name="FinTech SA",
            role="recruiter",
            login_link="https://app.example.com/login",
            quick_start_tips=["Complete seu perfil", "Crie sua primeira vaga"],
        )
        assert "Eduardo" in result["body"]
        assert "FinTech SA" in result["body"]

    def test_approval_pending(self):
        result = EmailTemplates.approval_pending(
            approver_name="Fernanda",
            request_type="Oferta de emprego",
            requester_name="Recrutador João",
            request_details="Oferta para candidato X",
            deadline="20/06/2025",
            approval_link="https://app.example.com/approve/123",
        )
        assert "Fernanda" in result["body"]

    def test_approval_expired(self):
        result = EmailTemplates.approval_expired(
            approver_name="Gustavo",
            request_type="Aprovação de oferta",
            requester_name="Recrutador",
            original_deadline="15/06/2025",
        )
        assert "Gustavo" in result["body"]

    def test_password_changed(self):
        result = EmailTemplates.password_changed(
            user_name="Helena",
            change_date="10/06/2025 14:30",
        )
        assert "Helena" in result["body"]

    def test_password_changed_with_ip(self):
        result = EmailTemplates.password_changed(
            user_name="Igor",
            change_date="10/06/2025",
            ip_address="192.168.1.1",
        )
        assert "Igor" in result["body"]


class TestWhatsAppTemplates:
    def test_initial_contact_non_confidential(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Juliana",
            job_title="Analista de Dados",
            company_name="DataCo",
            is_confidential=False,
        )
        assert isinstance(result, str)
        assert "Juliana" in result

    def test_initial_contact_confidential(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Kevin",
            job_title="CTO",
            company_name="ConfidentialCo",
            is_confidential=True,
        )
        assert isinstance(result, str)
        assert "Kevin" in result

    def test_initial_contact_with_privacy_url(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Laura",
            job_title="Dev",
            company_name="TechCo",
            is_confidential=False,
            privacy_policy_url="https://privacy.example.com",
        )
        assert "Laura" in result

    def test_interview_scheduled(self):
        result = WhatsAppTemplates.interview_scheduled(
            candidate_name="Marcos",
            interview_date=_DT,
            interview_link="https://meet.example.com/abc",
        )
        assert "Marcos" in result

    def test_interview_reminder(self):
        result = WhatsAppTemplates.interview_reminder(
            candidate_name="Natalia",
            interview_date=_DT,
            interview_link="https://meet.example.com/xyz",
        )
        assert "Natalia" in result

    def test_interview_reminder_urgent(self):
        result = WhatsAppTemplates.interview_reminder_urgent(
            candidate_name="Otavio",
            interview_date=_DT,
            interview_link="https://meet.example.com/urg",
        )
        assert "Otavio" in result

    def test_screening_passed(self):
        result = WhatsAppTemplates.screening_passed(
            candidate_name="Priscila",
            strengths=["Python", "Machine Learning"],
        )
        assert "Priscila" in result

    def test_screening_failed(self):
        result = WhatsAppTemplates.screening_failed(
            candidate_name="Quentin",
            strengths=["Comunicação"],
            development_areas=["Programação"],
        )
        assert "Quentin" in result

    def test_screening_start(self):
        result = WhatsAppTemplates.screening_start(
            candidate_name="Roberta",
            job_title="Analista de Marketing",
        )
        assert "Roberta" in result
        assert "Analista de Marketing" in result

    def test_screening_reminder(self):
        result = WhatsAppTemplates.screening_reminder(
            candidate_name="Sergio",
            hours_remaining=4,
        )
        assert "Sergio" in result
        assert "4" in result

    def test_no_show_first(self):
        result = WhatsAppTemplates.no_show_first(
            candidate_name="Tatiana",
            job_title="Designer",
            interview_datetime=_DT,
        )
        assert "Tatiana" in result

    def test_no_show_first_with_link(self):
        result = WhatsAppTemplates.no_show_first(
            candidate_name="Ulysses",
            job_title="Dev",
            interview_datetime=_DT,
            reschedule_link="https://cal.example.com/book",
        )
        assert "Ulysses" in result

    def test_no_show_final(self):
        result = WhatsAppTemplates.no_show_final(
            candidate_name="Valentina",
            job_title="Analista",
            no_show_count=3,
        )
        assert "Valentina" in result

    def test_follow_up(self):
        result = WhatsAppTemplates.follow_up(
            candidate_name="Wilson",
            job_title="Engenheiro",
            days_inactive=5,
            current_stage="triagem",
        )
        assert "Wilson" in result

    def test_job_paused(self):
        result = WhatsAppTemplates.job_paused(
            candidate_name="Ximena",
            job_title="PM",
        )
        assert "Ximena" in result

    def test_job_cancelled(self):
        result = WhatsAppTemplates.job_cancelled(
            candidate_name="Yago",
            job_title="Analista",
        )
        assert "Yago" in result

    def test_job_reactivated(self):
        result = WhatsAppTemplates.job_reactivated(
            candidate_name="Zara",
            job_title="Dev",
        )
        assert "Zara" in result

    def test_process_closed(self):
        result = WhatsAppTemplates.process_closed(
            candidate_name="Alexandre",
            job_title="Analista",
        )
        assert "Alexandre" in result

    def test_rejection_feedback(self):
        result = WhatsAppTemplates.rejection_feedback(
            candidate_name="Beatriz",
        )
        assert "Beatriz" in result

    def test_rejection_feedback_with_custom(self):
        result = WhatsAppTemplates.rejection_feedback(
            candidate_name="Caio",
            custom_feedback="Perfil muito promissor, mas precisamos de alguém com mais Python.",
        )
        assert "Caio" in result

    def test_offer_deadline_reminder(self):
        result = WhatsAppTemplates.offer_deadline_reminder(
            candidate_name="Diana",
            job_title="Senior Dev",
            deadline="20/06/2025",
            hours_remaining=48,
        )
        assert "Diana" in result
        assert "48" in result
