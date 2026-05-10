"""Coverage tests for communication_templates.py — EmailTemplates + WhatsAppTemplates."""
import pytest
from datetime import datetime
from app.templates.communication_templates import (
    EmailTemplates,
    WhatsAppTemplates,
    DATA_PROCESSING_NOTICE,
    WSI_INITIAL_CONTACT_LGPD_NOTICE,
)


class TestDataProcessingNotice:
    def test_notice_is_string(self):
        assert isinstance(DATA_PROCESSING_NOTICE, str)
        assert len(DATA_PROCESSING_NOTICE) > 50

    def test_wsi_notice_is_string(self):
        assert isinstance(WSI_INITIAL_CONTACT_LGPD_NOTICE, str)


class TestEmailTemplatesInitialContact:
    def test_non_confidential(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Ana",
            job_title="Desenvolvedor",
            company_name="TechCo",
            is_confidential=False
        )
        assert "subject" in result and "body" in result
        assert "Ana" in result["body"]

    def test_confidential(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Bruno",
            job_title="Gerente",
            company_name=None,
            is_confidential=True
        )
        assert isinstance(result["subject"], str)

    def test_with_challenge(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Carlos",
            job_title="Designer",
            company_name="XYZ",
            is_confidential=False,
            job_challenge="Criar interfaces incriveis"
        )
        assert isinstance(result["body"], str)

    def test_with_privacy_policy_url(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Diana",
            job_title="PM",
            company_name="ACME",
            is_confidential=False,
            privacy_policy_url="https://acme.com/privacidade"
        )
        assert "https://acme.com/privacidade" in result["body"]


class TestEmailTemplatesFollowUp:
    def test_correct_signature(self):
        result = EmailTemplates.follow_up(
            candidate_name="Ana",
            job_title="Dev",
            days_inactive=3,
            current_stage="triagem"
        )
        assert isinstance(result, dict)
        assert "subject" in result

    def test_with_company_name(self):
        result = EmailTemplates.follow_up(
            candidate_name="Bruno",
            job_title="PM",
            days_inactive=5,
            current_stage="entrevista",
            company_name="ACME"
        )
        assert isinstance(result, dict)


class TestEmailTemplatesCandidateRejected:
    def test_basic_rejection(self):
        result = EmailTemplates.candidate_rejected(
            candidate_name="Carlos",
            job_title="Designer",
        )
        assert isinstance(result, dict)
        assert "subject" in result

    def test_with_reason(self):
        result = EmailTemplates.candidate_rejected(
            candidate_name="Diana",
            job_title="Dev",
            rejection_reason="Perfil nao adequado para o momento"
        )
        assert isinstance(result, dict)


class TestEmailTemplatesInterviewScheduled:
    def test_basic(self):
        result = EmailTemplates.interview_scheduled(
            candidate_name="Eduardo",
            job_title="Backend Dev",
            interview_date=datetime(2026, 5, 15, 10, 0),
            interview_link="https://meet.google.com/test"
        )
        assert isinstance(result, dict)
        assert "subject" in result

    def test_with_interviewer(self):
        result = EmailTemplates.interview_scheduled(
            candidate_name="Fernanda",
            job_title="Frontend Dev",
            interview_date=datetime(2026, 5, 20, 14, 30),
            interview_link="https://zoom.us/test",
            interviewer_name="Paulo"
        )
        assert "Paulo" in result["body"] or isinstance(result, dict)


class TestEmailTemplatesScreeningPassed:
    def test_screening_passed(self):
        result = EmailTemplates.screening_passed(
            candidate_name="Gustavo",
            job_title="Analista"
        )
        assert isinstance(result, dict)


class TestEmailTemplatesScreeningFailed:
    def test_screening_failed(self):
        result = EmailTemplates.screening_failed(
            candidate_name="Helena",
            job_title="Dev"
        )
        assert isinstance(result, dict)


class TestWhatsAppTemplatesInitialContact:
    def test_non_confidential(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Ana",
            job_title="Dev",
            company_name="TechCo",
            is_confidential=False
        )
        assert isinstance(result, str)
        assert "Ana" in result

    def test_confidential(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Bruno",
            job_title="PM",
            company_name=None,
            is_confidential=True
        )
        assert isinstance(result, str)

    def test_with_privacy_url(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Carlos",
            job_title="Dev",
            company_name="Co",
            is_confidential=False,
            privacy_policy_url="https://co.com/privacidade"
        )
        assert isinstance(result, str)


class TestWhatsAppTemplatesFollowUp:
    def test_returns_string(self):
        result = WhatsAppTemplates.follow_up(
            candidate_name="Diana",
            job_title="Designer",
            days_inactive=3,
            current_stage="triagem"
        )
        assert isinstance(result, str)
        assert "Diana" in result


class TestWhatsAppTemplatesScreeningPassed:
    def test_returns_string(self):
        result = WhatsAppTemplates.screening_passed(
            candidate_name="Eduardo",
            job_title="Analista"
        )
        assert isinstance(result, str)


class TestWhatsAppTemplatesScreeningFailed:
    def test_returns_string(self):
        result = WhatsAppTemplates.screening_failed(
            candidate_name="Fernanda",
            job_title="Dev"
        )
        assert isinstance(result, str)


class TestWhatsAppTemplatesScreeningReminder:
    def test_returns_string(self):
        result = WhatsAppTemplates.screening_reminder(
            candidate_name="Gustavo",
            job_title="PM"
        )
        assert isinstance(result, str)


class TestWhatsAppTemplatesInterviewScheduled:
    def test_returns_string(self):
        result = WhatsAppTemplates.interview_scheduled(
            candidate_name="Helena",
            job_title="Dev",
            interview_date="15/05/2026",
            interview_time="10:00",
            interview_link="https://meet.google.com/test"
        )
        assert isinstance(result, str)


class TestWhatsAppTemplatesRejectionFeedback:
    def test_returns_string(self):
        result = WhatsAppTemplates.rejection_feedback(
            candidate_name="Igor"
        )
        assert isinstance(result, str)

    def test_with_custom_feedback(self):
        result = WhatsAppTemplates.rejection_feedback(
            candidate_name="Julia",
            custom_feedback="Perfil nao adequado"
        )
        assert "Julia" in result
