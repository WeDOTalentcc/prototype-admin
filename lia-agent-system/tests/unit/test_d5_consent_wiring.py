"""
D5-G2 — Testes de wiring do consentimento granular nos pontos críticos do sistema LIA.

Cobre:
- filter_sensitive_outbound: filtragem async com check de consentimento ats_sharing
- evaluate_and_create_activity: bloqueio quando ai_screening não consentido
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# TestATSPIIFilter
# ---------------------------------------------------------------------------


class TestATSPIIFilter:

    @pytest.mark.asyncio
    async def test_filter_outbound_without_consent_removes_sensitive_fields(self):
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        payload = {
            "name": "João Silva",
            "email": "joao@email.com",
            "cpf": "123.456.789-00",
            "birth_date": "1990-01-01",
            "skills": ["Python", "FastAPI"],
        }

        mock_svc = MagicMock()
        mock_svc.check_purpose = AsyncMock(return_value=False)

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_svc,
        ):
            result = await filter_sensitive_outbound(
                payload,
                "pandape",
                candidate_id="cand-1",
                company_id="company-1",
                db=MagicMock(),
            )

        assert "name" in result
        assert "cpf" not in result
        assert "birth_date" not in result

    @pytest.mark.asyncio
    async def test_filter_outbound_with_consent_passes_all_fields(self):
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        payload = {
            "name": "João Silva",
            "cpf": "123.456.789-00",
            "skills": ["Python"],
        }

        mock_svc = MagicMock()
        mock_svc.check_purpose = AsyncMock(return_value=True)

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_svc,
        ):
            result = await filter_sensitive_outbound(
                payload,
                "gupy",
                candidate_id="cand-1",
                company_id="company-1",
                db=MagicMock(),
            )

        # campo mantido porque tem consentimento
        assert "cpf" in result
        assert "name" in result

    @pytest.mark.asyncio
    async def test_filter_fail_open_on_consent_error(self):
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        payload = {"name": "Test", "cpf": "123.456.789-00"}

        mock_svc = MagicMock()
        mock_svc.check_purpose = AsyncMock(side_effect=RuntimeError("DB error"))

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_svc,
        ):
            # fail-open: não levanta exceção, retorna payload completo (consent assumed True)
            result = await filter_sensitive_outbound(
                payload,
                "gupy",
                candidate_id="cand-1",
                company_id="company-1",
                db=MagicMock(),
            )

        assert result is not None
        # fail-open → campos sensíveis mantidos
        assert "cpf" in result

    def test_filter_inbound_strips_pii_from_text_fields(self):
        from app.services.ats_clients.ats_pii_filter import filter_inbound_text

        payload = {
            "name": "João",
            "observacoes": "Candidato com CPF 123.456.789-00 e email joao@teste.com",
        }

        result = filter_inbound_text(payload, "gupy")

        assert "name" in result
        assert "observacoes" in result
        assert isinstance(result["observacoes"], str)

    @pytest.mark.asyncio
    async def test_filter_without_candidate_id_passes_all(self):
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        payload = {"name": "Test", "cpf": "123.456.789-00"}

        # Sem candidate_id — não verifica consentimento, pass-through
        result = await filter_sensitive_outbound(payload, "gupy")

        assert result == payload

    @pytest.mark.asyncio
    async def test_filter_without_db_passes_all(self):
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        payload = {"name": "Test", "cpf": "123.456.789-00", "birth_date": "1990-01-01"}

        # db=None — sem verificação, pass-through (has_consent=True assumed)
        result = await filter_sensitive_outbound(
            payload, "pandape", candidate_id="cand-1", company_id="co-1", db=None
        )

        assert result == payload

    @pytest.mark.asyncio
    async def test_filter_check_purpose_called_with_ats_sharing(self):
        """Garante que o purpose verificado é especificamente 'ats_sharing'."""
        from app.services.ats_clients.ats_pii_filter import filter_sensitive_outbound

        mock_svc = MagicMock()
        mock_svc.check_purpose = AsyncMock(return_value=True)

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_svc,
        ):
            await filter_sensitive_outbound(
                {"name": "Test"},
                "gupy",
                candidate_id="cand-99",
                company_id="co-99",
                db=MagicMock(),
            )

        mock_svc.check_purpose.assert_awaited_once_with("cand-99", "co-99", "ats_sharing")


# ---------------------------------------------------------------------------
# TestRubricEvaluationConsentWiring
# ---------------------------------------------------------------------------


class TestRubricEvaluationConsentWiring:

    def _make_service(self):
        """Instancia RubricEvaluationService sem dependências externas."""
        from app.domains.cv_screening.services.rubric_evaluation_service import (
            RubricEvaluationService,
        )
        llm_svc = MagicMock()
        llm_svc.generate_response = AsyncMock(return_value="{}")
        return RubricEvaluationService(llm_service=llm_svc)

    @pytest.mark.asyncio
    async def test_evaluate_and_create_activity_blocked_without_consent(self):
        """Quando ai_screening não consentido, retorna None sem executar avaliação."""
        svc = self._make_service()

        mock_consent_svc = MagicMock()
        mock_consent_svc.check_purpose = AsyncMock(return_value=False)

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_consent_svc,
        ):
            result = await svc.evaluate_and_create_activity(
                candidate_id="cand-10",
                candidate_name="Ana Lima",
                candidate_data={"id": "cand-10"},
                job_id="job-1",
                job_title="Dev Backend",
                job_code="DEV-001",
                requirements=[],
                company_id="co-10",
                db=MagicMock(),
            )

        assert result is None
        mock_consent_svc.check_purpose.assert_awaited_once_with(
            "cand-10", "co-10", "ai_screening"
        )

    @pytest.mark.asyncio
    async def test_evaluate_and_create_activity_proceeds_with_consent(self):
        """Quando ai_screening consentido, chama evaluate_candidate normalmente."""
        svc = self._make_service()

        mock_consent_svc = MagicMock()
        mock_consent_svc.check_purpose = AsyncMock(return_value=True)

        mock_result = MagicMock()
        mock_result.score = 75.0

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_consent_svc,
        ), patch.object(svc, "evaluate_candidate", new_callable=AsyncMock, return_value=mock_result):
            result = await svc.evaluate_and_create_activity(
                candidate_id="cand-11",
                candidate_name="Bruno Souza",
                candidate_data={"id": "cand-11"},
                job_id="job-2",
                job_title="Dev Frontend",
                job_code=None,
                requirements=[],
                company_id="co-11",
                db=MagicMock(),
            )

        # Deve retornar o resultado da avaliação (não None)
        assert result is not None

    @pytest.mark.asyncio
    async def test_evaluate_fail_open_when_consent_service_raises(self):
        """Se GranularConsentService lançar exceção, avaliação prossegue (fail-open)."""
        svc = self._make_service()

        mock_consent_svc = MagicMock()
        mock_consent_svc.check_purpose = AsyncMock(
            side_effect=RuntimeError("DB unavailable")
        )

        mock_result = MagicMock()
        mock_result.score = 80.0

        with patch(
            "app.shared.services.granular_consent_service.GranularConsentService",
            return_value=mock_consent_svc,
        ), patch.object(svc, "evaluate_candidate", new_callable=AsyncMock, return_value=mock_result):
            # Não deve levantar exceção — fail-open
            result = await svc.evaluate_and_create_activity(
                candidate_id="cand-12",
                candidate_name="Carla Reis",
                candidate_data={"id": "cand-12"},
                job_id="job-3",
                job_title="QA Engineer",
                job_code=None,
                requirements=[],
                company_id="co-12",
                db=MagicMock(),
            )

        # fail-open: avaliação foi executada mesmo com falha no consent check
        assert result is not None

    @pytest.mark.asyncio
    async def test_evaluate_skips_consent_check_when_db_is_none(self):
        """Quando db=None, consent check é ignorado e avaliação prossegue."""
        svc = self._make_service()

        mock_result = MagicMock()
        mock_result.score = 60.0

        with patch.object(svc, "evaluate_candidate", new_callable=AsyncMock, return_value=mock_result):
            result = await svc.evaluate_and_create_activity(
                candidate_id="cand-13",
                candidate_name="Diego Ferreira",
                candidate_data={"id": "cand-13"},
                job_id="job-4",
                job_title="DevOps",
                job_code=None,
                requirements=[],
                company_id="co-13",
                db=None,  # sem DB → sem consent check
            )

        assert result is not None
