"""Coverage tests for communication_templates.py — EmailTemplates + WhatsAppTemplates."""
import pytest
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
        assert "subject" in result
        assert "body" in result
        assert "Ana" in result["body"]

    def test_confidential(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Bruno",
            job_title="Gerente",
            company_name=None,
            is_confidential=True
        )
        assert "confidencial" in result["subject"].lower() or "Confidencial" in result["subject"]

    def test_with_challenge(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Carlos",
            job_title="Designer",
            company_name="XYZ",
            is_confidential=False,
            job_challenge="Criar interfaces incríveis"
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

    def test_returns_dict_with_subject_body(self):
        result = EmailTemplates.initial_contact(
            candidate_name="Eduardo",
            job_title="Dev",
            company_name="Co",
            is_confidential=False
        )
        assert isinstance(result, dict)
        assert "subject" in result
        assert "body" in result


class TestEmailTemplatesFollowUp:
    def test_returns_dict(self):
        result = EmailTemplates.follow_up(
            candidate_name="Ana",
            job_title="Dev",
            company_name="Co",
            is_confidential=False
        )
        assert isinstance(result, dict)
        assert "subject" in result or len(result) > 0


class TestEmailTemplatesRejection:
    def test_returns_dict(self):
        result = EmailTemplates.rejection(
            candidate_name="Bruno",
            job_title="Designer",
            company_name="Co",
            is_confidential=False
        )
        assert isinstance(result, dict)


class TestEmailTemplatesInterview:
    def test_returns_dict(self):
        result = EmailTemplates.interview_invitation(
            candidate_name="Carlos",
            job_title="PM",
            company_name="ACME",
            is_confidential=False,
            interview_date="15/05/2026",
            interview_time="10:00",
            interview_type="video",
            interview_link="https://meet.google.com/test"
        )
        assert isinstance(result, dict)
        assert "10:00" in str(result.get("body", "")) or "10:00" in str(result)


class TestWhatsAppTemplatesInitialContact:
    def test_returns_string(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Ana",
            job_title="Desenvolvedor",
            company_name="TechCo",
            is_confidential=False,
            recruiter_name="Paulo"
        )
        assert isinstance(result, str)
        assert "Ana" in result

    def test_confidential_no_company(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Bruno",
            job_title="Gerente",
            company_name=None,
            is_confidential=True
        )
        assert isinstance(result, str)

    def test_short_enough_for_whatsapp(self):
        result = WhatsAppTemplates.initial_contact(
            candidate_name="Carlos",
            job_title="Dev",
            company_name="Co",
            is_confidential=False
        )
        assert len(result) < 2000


class TestWhatsAppTemplatesFollowUp:
    def test_returns_string(self):
        result = WhatsAppTemplates.follow_up(
            candidate_name="Diana",
            job_title="Designer"
        )
        assert isinstance(result, str)
        assert "Diana" in result


class TestWhatsAppTemplatesRejection:
    def test_returns_string(self):
        result = WhatsAppTemplates.rejection(
            candidate_name="Eduardo",
            job_title="PM"
        )
        assert isinstance(result, str)
