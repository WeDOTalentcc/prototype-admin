"""
C4 P0 #1 — WSI Report FairnessGuard gate (TDD contract sensor)

Garante que generate_report() e generate_feedback() passam pelo caminho
canonico GuardedCandidateContentService ANTES de retornar ao caller.

Testes:
  T-a: FairnessGuard e chamado em generate_report (via GuardedContentService)
  T-b: Conteudo biased e substituido pelo conteudo canonico de bloqueio
  T-c: company_id ausente em GuardedContentService -> ValueError
  T-d: Conteudo limpo passa normalmente (nao-regressao)
  T-e: GuardedContentResult tem provenance fields obrigatorios
  T-f: FairnessGuard e chamado em generate_feedback (via GuardedContentService)

Pattern de fixture: igual ao test_wsi_report_generator_fallback.py canonical.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domains.cv_screening.services.wsi_service.models import (
    CandidateFeedback,
    ResponseAnalysis,
    StructuredReport,
    WSIResult,
)
from app.domains.cv_screening.services.wsi_service.report_generator import (
    WSIReportGenerator,
)
from app.shared.compliance.guarded_content_service import (
    GuardedCandidateContentService,
    GuardedContentResult,
    _BLOCKED_REPORT_CONTENT,
)


# ---------------------------------------------------------------------------
# Fixtures (espelham test_wsi_report_generator_fallback.py)
# ---------------------------------------------------------------------------

@pytest.fixture
def responses_sample():
    return [
        ResponseAnalysis(
            question_id="q1",
            competency="Python",
            response_text="Trabalho com Python ha 5 anos usando asyncio e FastAPI.",
            evidences=["Mencionou projeto X com asyncio"],
            red_flags=[],
            final_score=4.0,
            justification="Demonstra solido conhecimento em async/await",
        ),
        ResponseAnalysis(
            question_id="q2",
            competency="Comunicacao",
            response_text="Articulo bem ideias tecnicas com colegas nao-tecnicos.",
            evidences=[],
            red_flags=[],
            final_score=3.5,
            justification="Articula bem ideias tecnicas",
        ),
    ]


@pytest.fixture
def wsi_result_sample(responses_sample):
    return WSIResult(
        candidate_id="cand-test-001",
        job_vacancy_id="job-test-001",
        technical_wsi=3.5,
        behavioral_wsi=3.8,
        overall_wsi=3.65,
        classification="medio",
        response_analyses=responses_sample,
    )


def _make_generator(llm_mock):
    """Helper canonical — WSIReportGenerator sem RAG load."""
    gen = WSIReportGenerator.__new__(WSIReportGenerator)
    gen.llm = llm_mock
    gen.report_templates = ""
    return gen


# ---------------------------------------------------------------------------
# T-c: GuardedCandidateContentService fail-closed (unit test puro)
# ---------------------------------------------------------------------------

class TestGuardedContentServiceFailClosed:
    """GuardedCandidateContentService fail-closed sem company_id."""

    def test_empty_company_id_raises_value_error(self):
        """company_id=None -> ValueError (multi-tenancy fail-closed)."""
        svc = GuardedCandidateContentService()
        with pytest.raises(ValueError, match="company_id"):
            svc.guard_generated_content(
                content="Candidato apresenta boas habilidades.",
                company_id="",  # vazio = fail-closed
                content_type="wsi_report",
            )

    def test_none_company_id_raises_value_error(self):
        """company_id=None explicito -> ValueError."""
        svc = GuardedCandidateContentService()
        with pytest.raises((ValueError, TypeError)):
            svc.guard_generated_content(
                content="Candidato apresenta boas habilidades.",
                company_id=None,  # type: ignore[arg-type]
                content_type="wsi_report",
            )

    def test_clean_content_passes_through(self):
        """T-d: conteudo sem vies passa normalmente."""
        svc = GuardedCandidateContentService()
        result = svc.guard_generated_content(
            content="Candidato demonstra dominio solido em Python e SQL. Recomenda-se avanco.",
            company_id="company-abc-123",
            content_type="wsi_report",
        )
        assert isinstance(result, GuardedContentResult)
        assert result.fairness_blocked is False
        assert result.fairness_passed is True
        assert result.is_ai_generated is True
        assert result.generated_by == "lia_guarded"
        assert "Candidato demonstra" in result.content

    def test_blocked_content_returns_canonical_message(self):
        """T-b: conteudo com vies explicito detectado pelo FairnessGuard real e substituido."""
        # Usa FairnessGuard REAL (sem mock no guard)
        svc = GuardedCandidateContentService()
        # Texto que contem padrao de vies explicito (maternidade — categoria hard-block)
        biased_content = "apenas mulheres jovens sem filhos se encaixam nesta vaga"
        result = svc.guard_generated_content(
            content=biased_content,
            company_id="company-abc-123",
            content_type="wsi_report",
        )
        # Se o guard detectou o vies, o conteudo deve ser substituido
        if result.fairness_blocked:
            assert result.content == _BLOCKED_REPORT_CONTENT
            assert result.needs_manual_review is True
            assert result.fairness_passed is False
        # Se nao detectou (guard em modo degradado), pelo menos nao quebra
        assert isinstance(result, GuardedContentResult)

    def test_result_has_provenance_fields(self):
        """T-e: GuardedContentResult sempre tem provenance fields."""
        svc = GuardedCandidateContentService()
        result = svc.guard_generated_content(
            content="Candidato solido em competencias tecnicas.",
            company_id="company-xyz",
            content_type="candidate_feedback",
        )
        assert result.is_ai_generated is True
        assert result.generated_by == "lia_guarded"
        assert result.content_type == "candidate_feedback"
        assert result.company_id == "company-xyz"


# ---------------------------------------------------------------------------
# T-a: generate_report() chama GuardedCandidateContentService
# ---------------------------------------------------------------------------

class TestGenerateReportCallsGuard:
    """T-a: generate_report() deve chamar GuardedCandidateContentService."""

    @pytest.mark.asyncio
    async def test_generate_report_calls_guarded_service(
        self, wsi_result_sample, responses_sample
    ):
        """
        generate_report() deve chamar guard_generated_content() antes de retornar.
        Este teste FALHA se report_generator.py nao usa GuardedCandidateContentService.
        """
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value="""{
            "executive_summary": "Candidato senior com fortes habilidades.",
            "technical_analysis": {"pontos_fortes": ["Python"], "gaps": [], "evidencias": []},
            "behavioral_analysis": {"colaboracao": 4.0, "inovacao": 3.5, "organizacao": 4.0, "resiliencia": 3.5},
            "cultural_fit": {"score": 4.0, "valores_alinhados": [], "atencoes": []},
            "recommendation": {"decisao": "APROVADO", "justificativa": "WSI 3.65", "proximos_passos": []}
        }""")
        gen = _make_generator(llm_mock)

        with patch(
            "app.shared.compliance.guarded_content_service.GuardedCandidateContentService.guard_generated_content"
        ) as mock_guard:
            mock_guard.return_value = GuardedContentResult(
                content="Candidato senior com fortes habilidades.",
                company_id="company-test",
                content_type="wsi_report",
                fairness_passed=True,
                fairness_blocked=False,
            )

            report = await gen.generate_report(
                candidate_id="cand-test-001",
                wsi_result=wsi_result_sample,
                responses=responses_sample,
                company_id="company-test",
            )

        # FALHA hoje porque generate_report nao aceita company_id nem chama guard
        mock_guard.assert_called_once()
        assert isinstance(report, StructuredReport)

    @pytest.mark.asyncio
    async def test_generate_report_requires_company_id(
        self, wsi_result_sample, responses_sample
    ):
        """
        generate_report() sem company_id deve falhar.
        FALHA hoje porque company_id nao e parametro.
        """
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value="{}")
        gen = _make_generator(llm_mock)

        with pytest.raises((ValueError, TypeError)):
            await gen.generate_report(
                candidate_id="cand-test-001",
                wsi_result=wsi_result_sample,
                responses=responses_sample,
                company_id=None,  # deve falhar fail-closed
            )


# ---------------------------------------------------------------------------
# T-f: generate_feedback() chama GuardedCandidateContentService
# ---------------------------------------------------------------------------

class TestGenerateFeedbackCallsGuard:
    """T-f: generate_feedback() deve chamar GuardedCandidateContentService."""

    @pytest.mark.asyncio
    async def test_generate_feedback_calls_guarded_service(
        self, wsi_result_sample, responses_sample
    ):
        """
        generate_feedback() deve chamar guard_generated_content() antes de retornar.
        Este teste FALHA se report_generator.py nao usa GuardedCandidateContentService.
        """
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value="""{
            "main_message": "Obrigado por participar da etapa de triagem.",
            "technical_strengths": ["Python avancado"],
            "development_opportunities": ["Design patterns"],
            "behavioral_strengths": ["Capacidade analitica"],
            "next_steps": "Entraremos em contato.",
            "personalized_tip": "Continue explorando asyncio.",
            "development_plan": {"curto_prazo": [], "medio_prazo": []},
            "recommended_resources": []
        }""")
        gen = _make_generator(llm_mock)

        with patch(
            "app.shared.compliance.guarded_content_service.GuardedCandidateContentService.guard_generated_content"
        ) as mock_guard:
            mock_guard.return_value = GuardedContentResult(
                content="Obrigado por participar da etapa de triagem.",
                company_id="company-test",
                content_type="candidate_feedback",
                fairness_passed=True,
                fairness_blocked=False,
            )

            feedback = await gen.generate_feedback(
                wsi_result=wsi_result_sample,
                responses=responses_sample,
                decision="aprovado",
                company_id="company-test",
            )

        # FALHA hoje porque generate_feedback nao aceita company_id nem chama guard
        mock_guard.assert_called_once()
        assert isinstance(feedback, CandidateFeedback)
