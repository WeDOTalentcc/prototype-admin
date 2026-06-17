"""
RED tests — Domain validation: só permite compartilhar com emails do mesmo domínio da organização.

Art. 7 II (legítimo interesse): compartilhamento restrito ao domínio da própria empresa.
Cenários:
1. Destinatário mesmo domínio → permitido (sem raise)
2. Destinatário domínio externo → ValueError domain_not_allowed
3. Múltiplos destinatários, um cross-domain → ValueError com o domínio culpado
4. Usuário sem email (edge case) → falhar de forma fail-safe (bloqueia tudo)
"""
import pytest
from unittest.mock import MagicMock


class TestValidateRecipientDomains:
    """_validate_recipient_domains deve impedir cross-domain recipients."""

    def test_same_domain_passes(self):
        """Destinatário do mesmo domínio: sem exceção."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        _validate_recipient_domains(
            requester_email="recruiter@wedotalent.cc",
            recipient_emails=["manager@wedotalent.cc"],
        )  # não deve levantar

    def test_cross_domain_raises(self):
        """Destinatário de domínio externo: ValueError com código domain_not_allowed."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        with pytest.raises(ValueError) as exc_info:
            _validate_recipient_domains(
                requester_email="recruiter@wedotalent.cc",
                recipient_emails=["external@gmail.com"],
            )
        assert "domain_not_allowed" in str(exc_info.value)
        assert "wedotalent.cc" in str(exc_info.value)

    def test_mixed_recipients_one_cross_domain(self):
        """Um destinatário cross-domain entre vários basta para rejeitar."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        with pytest.raises(ValueError):
            _validate_recipient_domains(
                requester_email="recruiter@wedotalent.cc",
                recipient_emails=["ok@wedotalent.cc", "bad@external.com"],
            )

    def test_no_recipients_passes(self):
        """Lista vazia de destinatários: sem exceção."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        _validate_recipient_domains(
            requester_email="recruiter@wedotalent.cc",
            recipient_emails=[],
        )

    def test_requester_no_email_fail_safe(self):
        """Quando requester não tem email: bloqueia (fail-safe)."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        with pytest.raises(ValueError) as exc_info:
            _validate_recipient_domains(
                requester_email=None,
                recipient_emails=["anyone@anywhere.com"],
            )
        assert "domain_not_allowed" in str(exc_info.value)

    def test_case_insensitive_domain(self):
        """Comparação de domínio case-insensitive."""
        from app.api.v1.shared_searches import _validate_recipient_domains
        _validate_recipient_domains(
            requester_email="recruiter@WedoTalent.CC",
            recipient_emails=["manager@wedotalent.cc"],
        )  # não deve levantar
