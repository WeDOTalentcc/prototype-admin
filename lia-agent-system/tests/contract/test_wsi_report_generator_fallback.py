"""P0.D contract sensor (audit 2026-05-21) — wsi report_generator
fallback envelope canonical.

Garante que silent fallback no antigo pattern try/except foi eliminado:

1. ``generate_report`` em sucesso: ``fallback_used=False``,
   ``llm_failure_mode=None``, content vem do LLM.
2. ``generate_report`` em LLM exception: ``fallback_used=True``,
   ``needs_manual_review=True``, ``llm_failure_mode`` classificado,
   content = template fallback canonical (NOT silent fake claim).
3. ``generate_feedback`` em sucesso: idem item 1.
4. ``generate_feedback`` em LLM exception: ``fallback_used=True``,
   ``needs_manual_review=False`` (feedback é template neutro stock,
   nao requer revisao obrigatoria), ``llm_failure_mode`` classificado.
5. JSON parse error (LLM retorna malformed): ``safe_json_parse`` aplica
   fallback INTERNO (path canonical), envelope marca success=True
   (LLM call em si sucedeu, mas parse caiu pra fallback do parser).
   Diferente de LLM exception — distinção pra observabilidade.
6. Backward-compat: caller que NAO consulta ``fallback_used`` ainda
   recebe StructuredReport / CandidateFeedback completo com content
   stock — apenas perde visibilidade. Nao quebra producao.

Pattern canonical: app.shared.llm.safe_response.safe_llm_with_flag_async +
LLMResponseEnvelope. Replica filosofia REGRA 4 CLAUDE.md.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domains.cv_screening.services.wsi_service.models import (
    CandidateFeedback,
    ResponseAnalysis,
    StructuredReport,
    WSIResult,
)
from app.domains.cv_screening.services.wsi_service.report_generator import (
    WSIReportGenerator,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def responses_sample() -> list[ResponseAnalysis]:
    """Sample of analyzed responses (medio classification range)."""
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
def wsi_result_sample(responses_sample) -> WSIResult:
    """Canonical WSI result sample (medio classification — valid literal)."""
    return WSIResult(
        candidate_id="cand-test-001",
        job_vacancy_id="job-test-001",
        technical_wsi=3.5,
        behavioral_wsi=3.8,
        overall_wsi=3.65,
        classification="medio",
        response_analyses=responses_sample,
    )


@pytest.fixture
def llm_success_response() -> str:
    """Valid JSON response from LLM (success path)."""
    return """{
        "executive_summary": "Candidato senior com fortes habilidades tecnicas e boa comunicacao.",
        "technical_analysis": {
            "pontos_fortes": ["Python avancado", "Arquitetura async"],
            "gaps": [],
            "evidencias": ["Mencionou projeto X com asyncio"]
        },
        "behavioral_analysis": {
            "colaboracao": 4.0,
            "inovacao": 3.5,
            "organizacao": 4.0,
            "resiliencia": 3.5
        },
        "cultural_fit": {
            "score": 4.0,
            "valores_alinhados": ["Excelencia tecnica"],
            "atencoes": []
        },
        "recommendation": {
            "decisao": "APROVADO",
            "justificativa": "WSI 3.65 e fit cultural positivo",
            "proximos_passos": ["Agendar entrevista tecnica"]
        }
    }"""


@pytest.fixture
def llm_feedback_response() -> str:
    """Valid JSON candidate feedback from LLM."""
    return """{
        "main_message": "Obrigado por participar da etapa de triagem. Sua contribuicao foi valiosa e demonstrou pontos fortes consistentes ao longo do processo.",
        "technical_strengths": ["Python avancado (4.0/5)", "Comunicacao tecnica clara"],
        "development_opportunities": ["Aprofundar arquiteturas distribuidas"],
        "behavioral_strengths": ["Demonstrou capacidade analitica"],
        "next_steps": "A equipe de recrutamento analisara seu desempenho e entrara em contato.",
        "personalized_tip": "Continue explorando padroes async em projetos pessoais.",
        "development_plan": {"curto_prazo": ["Estudar arquiteturas distribuidas"], "medio_prazo": ["Contribuir em open source"]},
        "recommended_resources": ["Designing Data-Intensive Applications", "Curso de System Design"]
    }"""


def _make_generator(llm_mock):
    """Helper canonical para criar WSIReportGenerator com llm mockado."""
    gen = WSIReportGenerator.__new__(WSIReportGenerator)
    gen.llm = llm_mock
    gen.report_templates = ""  # skip RAG load
    return gen


# ---------------------------------------------------------------------------
# Tests — generate_report
# ---------------------------------------------------------------------------

class TestGenerateReportEnvelope:
    """P0.D envelope canonical em generate_report."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, wsi_result_sample, responses_sample, llm_success_response
    ):
        """Sucesso LLM: fallback_used=False, sem failure_mode."""
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value=llm_success_response)
        gen = _make_generator(llm_mock)

        report = await gen.generate_report(
            candidate_id="cand-test-001",
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        assert isinstance(report, StructuredReport)
        assert report.fallback_used is False
        assert report.needs_manual_review is False
        assert report.llm_failure_mode is None
        assert report.llm_error_message is None
        # Content vem do LLM, nao stock
        assert "Candidato senior" in report.executive_summary
        assert report.recommendation["decisao"] == "APROVADO"

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged(
        self, wsi_result_sample, responses_sample
    ):
        """LLM raise Exception: fallback_used=True + needs_manual_review=True."""
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(
            side_effect=RuntimeError("Anthropic timeout 30s")
        )
        gen = _make_generator(llm_mock)

        report = await gen.generate_report(
            candidate_id="cand-test-001",
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        assert isinstance(report, StructuredReport)
        assert report.fallback_used is True  # P0.D canonical
        assert report.needs_manual_review is True  # parecer fallback merece revisao
        assert report.llm_failure_mode is not None
        assert "timeout" in (report.llm_error_message or "").lower()
        # Fallback content stock canonical (back-compat preserved)
        assert "Análise detalhada não disponível" in report.executive_summary
        assert report.recommendation["decisao"] == "AGUARDANDO"
        # P0.D pin: justificativa NAO eh fake claim de analise real
        assert "revisar manualmente" in report.recommendation["justificativa"].lower()


# ---------------------------------------------------------------------------
# Tests — generate_feedback
# ---------------------------------------------------------------------------

class TestGenerateFeedbackEnvelope:
    """P0.D envelope canonical em generate_feedback."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, wsi_result_sample, responses_sample, llm_feedback_response
    ):
        """Sucesso LLM: fallback_used=False."""
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value=llm_feedback_response)
        gen = _make_generator(llm_mock)

        feedback = await gen.generate_feedback(
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            decision="aprovado",
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        assert isinstance(feedback, CandidateFeedback)
        assert feedback.fallback_used is False
        assert feedback.needs_manual_review is False
        assert feedback.llm_failure_mode is None
        # Content vem do LLM
        assert "Sua contribuicao foi valiosa" in feedback.main_message

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged_no_manual_review(
        self, wsi_result_sample, responses_sample
    ):
        """LLM raise Exception: fallback_used=True mas needs_manual_review=False.

        Feedback fallback eh template canonical NEUTRO (preserva tom
        construtivo independente de decisao interna). Nao requer revisao
        obrigatoria como o parecer (StructuredReport).
        """
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(
            side_effect=ConnectionError("Network refused")
        )
        gen = _make_generator(llm_mock)

        feedback = await gen.generate_feedback(
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            decision="aguardando",
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        assert isinstance(feedback, CandidateFeedback)
        assert feedback.fallback_used is True  # P0.D canonical
        assert feedback.needs_manual_review is False  # template neutro stock
        assert feedback.llm_failure_mode is not None
        assert "network" in (feedback.llm_error_message or "").lower()
        # Fallback content stock canonical (neutralidade preservada)
        assert "Obrigado por participar" in feedback.main_message

    @pytest.mark.asyncio
    async def test_decision_preserved_in_fallback_path(
        self, wsi_result_sample, responses_sample
    ):
        """Decision interna (audit trail) preservada mesmo em fallback."""
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(side_effect=ValueError("bad response"))
        gen = _make_generator(llm_mock)

        feedback = await gen.generate_feedback(
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            decision="nao_aprovado",
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        # decision eh audit trail interno — preservado independente de fallback
        assert feedback.decision == "nao_aprovado"
        # Mas main_message NEUTRO (nao revela decisao ao candidato)
        assert "Infelizmente" not in feedback.main_message
        assert "Parabéns" not in feedback.main_message


# ---------------------------------------------------------------------------
# Tests — backward-compat
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """Garante que caller que nao consulta fallback_used continua funcionando."""

    @pytest.mark.asyncio
    async def test_report_caller_ignores_fallback_field_still_works(
        self, wsi_result_sample, responses_sample, llm_success_response
    ):
        """Caller que so consulta content fields ainda recebe StructuredReport completo."""
        llm_mock = MagicMock()
        llm_mock.safe_invoke = AsyncMock(return_value=llm_success_response)
        gen = _make_generator(llm_mock)

        report = await gen.generate_report(
            candidate_id="cand-test-001",
            wsi_result=wsi_result_sample,
            responses=responses_sample,
            company_id="test-company-001",  # C4 P0 #1: obrigatorio
        )

        # Caller legacy soh consulta content
        assert report.executive_summary
        assert report.technical_analysis
        assert report.recommendation
        # fallback_used existe mas eh False — caller pode ignorar safely
        assert hasattr(report, "fallback_used")
