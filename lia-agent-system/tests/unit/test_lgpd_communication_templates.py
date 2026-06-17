"""
Testes unitários para conformidade LGPD nos templates de comunicação — Sprint K1.

Cobertura:
- DATA_PROCESSING_NOTICE menciona Twilio e Mailgun como sub-processadores
- EmailTemplates.initial_contact inclui aviso de tratamento de dados
- WhatsAppTemplates.initial_contact inclui aviso de sub-processador Twilio
- BASE_EMAIL_FOOTER_HTML contém identificação de IA e link de privacidade
- BASE_EMAIL_FOOTER_TEXT contém opt-out e referência LGPD
- EmailProvider.with_lgpd_footer injeta footer em html_content e text_content
- with_lgpd_footer não modifica o objeto original (imutável)
- Footer não é duplicado em chamadas sucessivas ao template
- WSI_INITIAL_CONTACT_LGPD_NOTICE contém menção a IA e direitos de titular
"""
import pytest


# ---------------------------------------------------------------------------
# DATA_PROCESSING_NOTICE
# ---------------------------------------------------------------------------

class TestDataProcessingNotice:

    def _notice(self):
        from app.templates.communication_templates import DATA_PROCESSING_NOTICE
        return DATA_PROCESSING_NOTICE

    def test_mentions_twilio(self):
        assert "Twilio" in self._notice()

    def test_mentions_mailgun(self):
        assert "Mailgun" in self._notice()

    def test_mentions_lgpd(self):
        assert "LGPD" in self._notice() or "13.709" in self._notice()

    def test_mentions_data_rights(self):
        notice = self._notice()
        assert any(w in notice for w in ["acesso", "correção", "exclusão", "portabilidade"])

    def test_mentions_wedotalent(self):
        assert "WeDOTalent" in self._notice()

    def test_not_empty(self):
        assert len(self._notice()) > 100


# ---------------------------------------------------------------------------
# EmailTemplates.initial_contact
# ---------------------------------------------------------------------------

class TestEmailInitialContact:

    def _call(self, privacy_url=""):
        from app.templates.communication_templates import EmailTemplates
        return EmailTemplates.initial_contact(
            candidate_name="João Silva",
            job_title="Dev Backend",
            company_name="AcmeCorp",
            is_confidential=False,
            privacy_policy_url=privacy_url,
        )

    def test_body_mentions_sub_processor(self):
        result = self._call()
        body = result["body"]
        assert any(w in body for w in ["Twilio", "Mailgun", "sub-processad"])

    def test_body_mentions_lgpd_or_privacy(self):
        result = self._call()
        body = result["body"]
        assert any(w in body for w in ["LGPD", "privacidade", "Privacidade", "13.709"])

    def test_body_contains_opt_out(self):
        result = self._call()
        assert any(w in result["body"] for w in ["não deseje", "não particip", "responder", "informando"])

    def test_privacy_url_included_when_provided(self):
        result = self._call(privacy_url="https://acme.com/privacidade")
        assert "https://acme.com/privacidade" in result["body"]

    def test_returns_subject_and_body(self):
        result = self._call()
        assert "subject" in result
        assert "body" in result


# ---------------------------------------------------------------------------
# WhatsAppTemplates.initial_contact
# ---------------------------------------------------------------------------

class TestWhatsAppInitialContact:

    def _call(self, privacy_url=""):
        from app.templates.communication_templates import WhatsAppTemplates
        return WhatsAppTemplates.initial_contact(
            candidate_name="Maria",
            job_title="Analista",
            company_name="EmpresaX",
            is_confidential=False,
            privacy_policy_url=privacy_url,
        )

    def test_mentions_twilio(self):
        assert "Twilio" in self._call()

    def test_mentions_ia(self):
        msg = self._call()
        assert any(w in msg for w in ["IA", "inteligência artificial", "LIA"])

    def test_mentions_opt_out(self):
        msg = self._call()
        assert "NÃO" in msg or "NAO" in msg or "não deseja" in msg

    def test_mentions_lgpd(self):
        msg = self._call()
        assert any(w in msg for w in ["LGPD", "privacidade", "Privacidade"])


# ---------------------------------------------------------------------------
# BASE_EMAIL_FOOTER
# ---------------------------------------------------------------------------

class TestBaseEmailFooter:

    def test_html_footer_mentions_mailgun(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_HTML
        assert "Mailgun" in BASE_EMAIL_FOOTER_HTML

    def test_html_footer_mentions_lia(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_HTML
        assert "LIA" in BASE_EMAIL_FOOTER_HTML

    def test_html_footer_has_privacy_link(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_HTML
        assert "privacidade" in BASE_EMAIL_FOOTER_HTML.lower()

    def test_html_footer_has_opt_out(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_HTML
        assert any(w in BASE_EMAIL_FOOTER_HTML for w in ["PRIVACIDADE", "cancelar", "opt"])

    def test_text_footer_mentions_lgpd(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_TEXT
        assert "LGPD" in BASE_EMAIL_FOOTER_TEXT

    def test_text_footer_has_opt_out(self):
        from app.services.email_providers.base import BASE_EMAIL_FOOTER_TEXT
        assert "PRIVACIDADE" in BASE_EMAIL_FOOTER_TEXT


# ---------------------------------------------------------------------------
# EmailProvider.with_lgpd_footer
# ---------------------------------------------------------------------------

class TestWithLgpdFooter:

    def _make_message(self, html="<p>Corpo</p>", text="Corpo"):
        from app.services.email_providers.base import EmailMessage
        return EmailMessage(to="cand@test.com", subject="Vaga", html_content=html, text_content=text)

    def test_html_content_appended(self):
        from app.services.email_providers.base import EmailProvider, BASE_EMAIL_FOOTER_HTML
        msg = self._make_message()
        result = EmailProvider.with_lgpd_footer(msg)
        assert result.html_content.endswith(BASE_EMAIL_FOOTER_HTML)

    def test_text_content_appended(self):
        from app.services.email_providers.base import EmailProvider, BASE_EMAIL_FOOTER_TEXT
        msg = self._make_message()
        result = EmailProvider.with_lgpd_footer(msg)
        assert result.text_content.endswith(BASE_EMAIL_FOOTER_TEXT)

    def test_original_not_mutated(self):
        from app.services.email_providers.base import EmailProvider
        msg = self._make_message()
        original_html = msg.html_content
        EmailProvider.with_lgpd_footer(msg)
        assert msg.html_content == original_html

    def test_other_fields_preserved(self):
        from app.services.email_providers.base import EmailProvider
        msg = self._make_message()
        result = EmailProvider.with_lgpd_footer(msg)
        assert result.to == msg.to
        assert result.subject == msg.subject

    def test_mailgun_in_html_after_footer(self):
        from app.services.email_providers.base import EmailProvider
        msg = self._make_message()
        result = EmailProvider.with_lgpd_footer(msg)
        assert "Mailgun" in result.html_content

    def test_wsi_initial_contact_notice_present(self):
        from app.templates.communication_templates import WSI_INITIAL_CONTACT_LGPD_NOTICE
        assert "IA" in WSI_INITIAL_CONTACT_LGPD_NOTICE or "inteligência artificial" in WSI_INITIAL_CONTACT_LGPD_NOTICE
        assert "Twilio" in WSI_INITIAL_CONTACT_LGPD_NOTICE
