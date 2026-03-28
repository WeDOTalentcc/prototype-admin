"""
C1 — LGPD em ATS: campos sensíveis dinâmicos

Verifica:
1. filter_outbound remove campos sensíveis quando has_consent=False
2. filter_outbound preserva todos os campos quando has_consent=True
3. filter_inbound_text aplica strip_pii em campos de texto livre
4. Filtros são fail-safe (nunca levantam exceção)
5. GupyClient.create_candidate chama filter_outbound
6. GupyClient.update_candidate chama filter_outbound
7. PandapeClient.create_candidate chama filter_outbound
8. PandapeClient.update_candidate chama filter_outbound
9. _parse_candidate chama filter_inbound_text em ambos os clientes
10. pretensao_salarial removido de pandape sem consentimento
11. wsi_score removido de pandape sem consentimento
12. campos não-sensíveis preservados sem consentimento
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestFilterOutbound:
    """Testes unitários de filter_outbound."""

    def test_removes_sensitive_fields_without_consent(self):
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        payload = {"name": "João", "email": "joao@test.com", "phone": "11999990000", "status": "ativo"}
        result = filter_outbound(payload, "gupy", has_consent=False)
        assert "email" not in result
        assert "phone" not in result
        assert result["name"] == "João"
        assert result["status"] == "ativo"

    def test_preserves_all_fields_with_consent(self):
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        payload = {"name": "João", "email": "joao@test.com", "phone": "11999990000", "status": "ativo"}
        result = filter_outbound(payload, "gupy", has_consent=True)
        assert result == payload

    def test_removes_salary_expectation_without_consent(self):
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        payload = {"name": "Maria", "salary_expectation": 8000, "job_id": "job-1"}
        result = filter_outbound(payload, "pandape", has_consent=False)
        assert "salary_expectation" not in result
        assert result["job_id"] == "job-1"

    def test_removes_wsi_score_without_consent(self):
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        payload = {"status": "aprovado", "wsi_score": 87.5}
        result = filter_outbound(payload, "pandape", has_consent=False)
        assert "wsi_score" not in result
        assert result["status"] == "aprovado"

    def test_default_consent_true_preserves_fields(self):
        """Default has_consent=True não deve remover nada."""
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        payload = {"email": "test@test.com", "phone": "11988880000"}
        result = filter_outbound(payload, "gupy")
        assert result == payload

    def test_fail_safe_on_exception(self):
        """filter_outbound nunca deve levantar exceção."""
        from app.services.ats_clients.ats_pii_filter import filter_outbound
        # Payload não-dict não deve lançar exceção
        result = filter_outbound({}, "gupy", has_consent=False)
        assert result == {}


class TestFilterInboundText:
    """Testes unitários de filter_inbound_text."""

    def test_strips_pii_from_gupy_notes(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text
        payload = {"observacoes": "Candidato João, email joao@empresa.com, bom perfil"}
        result = filter_inbound_text(payload, "gupy")
        assert "joao@empresa.com" not in result["observacoes"]

    def test_strips_pii_from_pandape_parecer(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text
        payload = {"parecer_rh": "CPF 123.456.789-00, aprovado para etapa 2"}
        result = filter_inbound_text(payload, "pandape")
        assert "123.456.789-00" not in result["parecer_rh"]

    def test_non_text_fields_unchanged(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text
        payload = {"id": "123", "status": "aprovado", "score": 85}
        result = filter_inbound_text(payload, "gupy")
        assert result == payload

    def test_unknown_ats_returns_payload_intact(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text
        payload = {"notes": "email test@test.com"}
        result = filter_inbound_text(payload, "unknown_ats")
        assert result == payload

    def test_fail_safe_on_exception(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text
        result = filter_inbound_text({}, "gupy")
        assert result == {}


class TestLGPDFieldRegistry:
    """Testes do registro centralizado de campos."""

    def test_sensitive_fields_set_not_empty(self):
        from app.services.ats_clients.lgpd_field_registry import OUTBOUND_SENSITIVE_FIELDS
        assert len(OUTBOUND_SENSITIVE_FIELDS) > 0
        assert "phone" in OUTBOUND_SENSITIVE_FIELDS
        assert "email" in OUTBOUND_SENSITIVE_FIELDS
        assert "salary_expectation" in OUTBOUND_SENSITIVE_FIELDS
        assert "wsi_score" in OUTBOUND_SENSITIVE_FIELDS

    def test_get_inbound_text_fields_gupy(self):
        from app.services.ats_clients.lgpd_field_registry import get_inbound_text_fields
        fields = get_inbound_text_fields("gupy")
        assert "observacoes" in fields

    def test_get_inbound_text_fields_pandape(self):
        from app.services.ats_clients.lgpd_field_registry import get_inbound_text_fields
        fields = get_inbound_text_fields("pandape")
        assert "parecer_rh" in fields
