"""P0.D SIBLINGS contract sensor (audit 2026-05-21) — wsi question_generator
fallback envelope canonical.

Garante que silent fallback foi eliminado dos 4 sites do
``question_generator.py``:

1. ``_generate_cbi_question`` em sucesso: ``fallback_used=False``,
   ``llm_failure_mode=None``, content vem do LLM.
2. ``_generate_cbi_question`` em LLM exception: ``fallback_used=True``,
   ``llm_failure_mode`` classificado, content = template fallback canonical
   (NOT silent fake claim).
3. Idem 1+2 pra ``_generate_dreyfus_question``,
   ``_generate_bloom_question``, ``_generate_bigfive_question``.
4. ``needs_manual_review=False`` em fallback (campo eh usado por F6.8
   ancoragem JD, sinal de LLM failure vive em ``fallback_used`` separado).
5. Backward-compat: caller que NAO consulta ``fallback_used`` ainda
   recebe WSIQuestion completo com content stock — apenas perde
   visibilidade. Nao quebra producao.
6. DRY helper ``_generate_question_with_envelope`` chamado pelos 4 sites
   (asserted via spy).

Pattern canonical: app.shared.llm.safe_response.safe_llm_with_flag_async +
LLMResponseEnvelope. Replica filosofia REGRA 4 CLAUDE.md.
SIBLING de C19 ``test_wsi_report_generator_fallback.py``.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domains.cv_screening.services.wsi_service.models import (
    Competency,
    WSIQuestion,
)
from app.domains.cv_screening.services.wsi_service.question_generator import (
    WSIQuestionGenerator,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def technical_competency() -> Competency:
    """Sample technical competency (Python senior)."""
    return Competency(
        name="Python",
        type="technical",
        weight=0.4,
        seniority_level="senior",
        is_critical=True,
    )


@pytest.fixture
def behavioral_competency() -> Competency:
    """Sample behavioral competency (Comunicação)."""
    return Competency(
        name="Comunicação",
        type="behavioral",
        weight=0.3,
        seniority_level="senior",
        is_critical=False,
        big_five_mapping="extraversion",
    )


@pytest.fixture
def llm_success_cbi() -> str:
    """Valid JSON CBI response from LLM."""
    return """{
        "framework": "CBI",
        "question_type": "contextual",
        "question_text": "Conte sobre um projeto Python complexo que voce liderou nos ultimos 12 meses. Qual foi o contexto, sua acao tecnica e o resultado mensuravel?",
        "expected_signals": ["Projeto real", "Decisoes tecnicas", "Resultado quantificado"],
        "scoring_criteria": {
            "score_5": "Lideranca tecnica + impacto quantificado",
            "score_3": "Projeto real + ação tecnica documentada",
            "score_1": "Projeto vago"
        }
    }"""


@pytest.fixture
def llm_success_dreyfus() -> str:
    """Valid JSON Dreyfus response from LLM."""
    return """{
        "framework": "Dreyfus",
        "question_type": "autodeclaration",
        "question_text": "De 1 a 5, quanto voce domina Python? Cite um projeto recente.",
        "expected_signals": ["Autodeclaracao honesta", "Projeto real"],
        "scoring_criteria": {
            "score_5": "Expert com impacto mensuravel",
            "score_3": "Competente com aplicacao pratica",
            "score_1": "Iniciante teorico"
        }
    }"""


@pytest.fixture
def llm_success_bloom() -> str:
    """Valid JSON Bloom response from LLM."""
    return """{
        "framework": "Bloom",
        "question_type": "microcase",
        "question_text": "Como voce diagnosticaria gargalo de performance em um endpoint Python sob carga 10x?",
        "expected_signals": ["Diagnose metodico", "Trade-offs", "Profiling"],
        "scoring_criteria": {
            "score_5": "Solucao completa + trade-offs explicitos",
            "score_3": "Solucao funcional",
            "score_1": "Conhecimento teorico apenas"
        }
    }"""


@pytest.fixture
def llm_success_bigfive() -> str:
    """Valid JSON BigFive response from LLM."""
    return """{
        "framework": "BigFive",
        "question_type": "situational",
        "question_text": "Descreva uma situacao recente em que voce precisou comunicar uma decisao tecnica controversa.",
        "expected_signals": ["Situacao real", "Comportamento especifico", "Resultado"],
        "scoring_criteria": {
            "score_5": "Situacao complexa + impacto mensuravel",
            "score_3": "Situacao clara + resultado satisfatorio",
            "score_1": "Situacao vaga"
        }
    }"""


def _make_generator(llm_response_or_exception):
    """Helper canonical para criar WSIQuestionGenerator com llm.claude.bind mockado.

    Args:
        llm_response_or_exception: str (success path), Exception (failure path).

    A cadeia ``self.llm.claude.bind(**kwargs).ainvoke(prompt)`` é mockada
    pra retornar um objeto com ``.content`` (success) ou levantar
    a exception fornecida.
    """
    gen = WSIQuestionGenerator.__new__(WSIQuestionGenerator)

    bind_mock = MagicMock()
    if isinstance(llm_response_or_exception, Exception):
        bind_mock.ainvoke = AsyncMock(side_effect=llm_response_or_exception)
    else:
        # Mock LLM response object with .content attribute
        response_obj = type("R", (), {"content": llm_response_or_exception})()
        bind_mock.ainvoke = AsyncMock(return_value=response_obj)

    claude_mock = MagicMock()
    claude_mock.bind = MagicMock(return_value=bind_mock)
    llm_mock = MagicMock()
    llm_mock.claude = claude_mock
    gen.llm = llm_mock
    # Skip RAG load — set placeholder
    gen.question_templates = ""
    return gen


# ---------------------------------------------------------------------------
# Tests — _generate_cbi_question
# ---------------------------------------------------------------------------

class TestGenerateCbiQuestionEnvelope:
    """P0.D envelope canonical em _generate_cbi_question."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, technical_competency, llm_success_cbi
    ):
        """Sucesso LLM: fallback_used=False, sem failure_mode."""
        gen = _make_generator(llm_success_cbi)

        question = await gen._generate_cbi_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "CBI"
        assert question.fallback_used is False
        assert question.llm_failure_mode is None
        assert question.llm_error_message is None
        # Content vem do LLM, nao stock
        assert "projeto Python complexo" in question.question_text

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged(self, technical_competency):
        """LLM raise Exception: fallback_used=True + failure_mode classificado."""
        gen = _make_generator(RuntimeError("Anthropic timeout 30s"))

        question = await gen._generate_cbi_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "CBI"
        assert question.fallback_used is True  # P0.D canonical
        assert question.llm_failure_mode is not None
        assert "timeout" in (question.llm_error_message or "").lower()
        # F6.8 needs_manual_review NAO eh afetado por LLM failure
        assert question.needs_manual_review is False
        # Fallback content stock canonical (back-compat preserved)
        assert "Python" in question.question_text


# ---------------------------------------------------------------------------
# Tests — _generate_dreyfus_question
# ---------------------------------------------------------------------------

class TestGenerateDreyfusQuestionEnvelope:
    """P0.D envelope canonical em _generate_dreyfus_question."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, technical_competency, llm_success_dreyfus
    ):
        """Sucesso LLM: fallback_used=False."""
        gen = _make_generator(llm_success_dreyfus)

        question = await gen._generate_dreyfus_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "Dreyfus"
        assert question.fallback_used is False
        assert question.llm_failure_mode is None
        # Content vem do LLM
        assert "domina Python" in question.question_text

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged(self, technical_competency):
        """LLM raise Exception: fallback_used=True."""
        gen = _make_generator(ConnectionError("Network refused"))

        question = await gen._generate_dreyfus_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "Dreyfus"
        assert question.fallback_used is True
        assert question.llm_failure_mode is not None
        assert "network" in (question.llm_error_message or "").lower()
        # Fallback content stock canonical
        assert "Python" in question.question_text


# ---------------------------------------------------------------------------
# Tests — _generate_bloom_question
# ---------------------------------------------------------------------------

class TestGenerateBloomQuestionEnvelope:
    """P0.D envelope canonical em _generate_bloom_question."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, technical_competency, llm_success_bloom
    ):
        """Sucesso LLM: fallback_used=False."""
        gen = _make_generator(llm_success_bloom)

        question = await gen._generate_bloom_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "Bloom"
        assert question.fallback_used is False
        assert question.llm_failure_mode is None
        # Content vem do LLM
        assert "gargalo de performance" in question.question_text

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged(self, technical_competency):
        """LLM raise Exception: fallback_used=True."""
        gen = _make_generator(ValueError("bad LLM response"))

        question = await gen._generate_bloom_question(technical_competency)

        assert isinstance(question, WSIQuestion)
        assert question.framework == "Bloom"
        assert question.fallback_used is True
        assert question.llm_failure_mode is not None
        # Fallback content stock canonical
        assert "Python" in question.question_text


# ---------------------------------------------------------------------------
# Tests — _generate_bigfive_question
# ---------------------------------------------------------------------------

class TestGenerateBigfiveQuestionEnvelope:
    """P0.D envelope canonical em _generate_bigfive_question."""

    @pytest.mark.asyncio
    async def test_success_path_no_fallback_flag(
        self, behavioral_competency, llm_success_bigfive
    ):
        """Sucesso LLM: fallback_used=False."""
        gen = _make_generator(llm_success_bigfive)

        question = await gen._generate_bigfive_question(
            behavioral_competency, ocean_trait="extraversion"
        )

        assert isinstance(question, WSIQuestion)
        assert question.framework == "BigFive"
        assert question.fallback_used is False
        assert question.llm_failure_mode is None
        # Content vem do LLM
        assert "decisao tecnica controversa" in question.question_text
        # ocean_trait injected em scoring_criteria
        assert question.scoring_criteria.get("ocean_trait") == "extraversion"

    @pytest.mark.asyncio
    async def test_llm_exception_fallback_flagged(self, behavioral_competency):
        """LLM raise Exception: fallback_used=True. ocean_trait preserved."""
        gen = _make_generator(TimeoutError("LLM call timeout"))

        question = await gen._generate_bigfive_question(
            behavioral_competency, ocean_trait="extraversion"
        )

        assert isinstance(question, WSIQuestion)
        assert question.framework == "BigFive"
        assert question.fallback_used is True
        assert question.llm_failure_mode is not None
        # ocean_trait audit trail preservado em fallback path
        assert question.scoring_criteria.get("ocean_trait") == "extraversion"
        # Fallback content stock canonical
        assert "Comunicação" in question.question_text


# ---------------------------------------------------------------------------
# Tests — DRY helper compartilhado
# ---------------------------------------------------------------------------

class TestDryHelperShared:
    """Garante que os 4 sites usam o helper canonical
    ``_generate_question_with_envelope`` (DRY)."""

    @pytest.mark.asyncio
    async def test_helper_called_by_all_4_sites(
        self,
        technical_competency,
        behavioral_competency,
        llm_success_cbi,
        llm_success_dreyfus,
        llm_success_bloom,
        llm_success_bigfive,
    ):
        """Cada uma das 4 funcoes _generate_X_question chama o helper DRY."""
        # CBI
        gen = _make_generator(llm_success_cbi)
        gen._generate_question_with_envelope = AsyncMock(
            wraps=gen._generate_question_with_envelope
        )
        await gen._generate_cbi_question(technical_competency)
        assert gen._generate_question_with_envelope.call_count == 1
        # framework_label kwarg deve ser CBI
        assert (
            gen._generate_question_with_envelope.call_args.kwargs["framework_label"]
            == "CBI"
        )

        # Dreyfus
        gen = _make_generator(llm_success_dreyfus)
        gen._generate_question_with_envelope = AsyncMock(
            wraps=gen._generate_question_with_envelope
        )
        await gen._generate_dreyfus_question(technical_competency)
        assert (
            gen._generate_question_with_envelope.call_args.kwargs["framework_label"]
            == "Dreyfus"
        )

        # Bloom
        gen = _make_generator(llm_success_bloom)
        gen._generate_question_with_envelope = AsyncMock(
            wraps=gen._generate_question_with_envelope
        )
        await gen._generate_bloom_question(technical_competency)
        assert (
            gen._generate_question_with_envelope.call_args.kwargs["framework_label"]
            == "Bloom"
        )

        # BigFive
        gen = _make_generator(llm_success_bigfive)
        gen._generate_question_with_envelope = AsyncMock(
            wraps=gen._generate_question_with_envelope
        )
        await gen._generate_bigfive_question(behavioral_competency)
        assert (
            gen._generate_question_with_envelope.call_args.kwargs["framework_label"]
            == "BigFive"
        )


# ---------------------------------------------------------------------------
# Tests — backward-compat
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    """Garante que caller que nao consulta fallback_used continua funcionando."""

    @pytest.mark.asyncio
    async def test_caller_ignores_fallback_field_still_works(
        self, technical_competency, llm_success_cbi
    ):
        """Caller que so consulta content fields ainda recebe WSIQuestion completo."""
        gen = _make_generator(llm_success_cbi)

        question = await gen._generate_cbi_question(technical_competency)

        # Caller legacy soh consulta content
        assert question.id
        assert question.question_text
        assert question.expected_signals
        assert question.scoring_criteria
        # fallback_used existe mas eh False — caller pode ignorar safely
        assert hasattr(question, "fallback_used")
        assert hasattr(question, "llm_failure_mode")
        assert hasattr(question, "llm_error_message")

    @pytest.mark.asyncio
    async def test_f68_needs_manual_review_independent_of_fallback(
        self, technical_competency
    ):
        """needs_manual_review (F6.8 ancoragem JD) eh independente de
        LLM fallback. Pin canonical pra evitar regression."""
        gen = _make_generator(RuntimeError("LLM down"))

        question = await gen._generate_cbi_question(technical_competency)

        # LLM falhou (fallback_used=True) MAS needs_manual_review (F6.8) NAO
        # eh setado automaticamente — campo serve a outra ancoragem JD,
        # nao a LLM failure.
        assert question.fallback_used is True
        assert question.needs_manual_review is False
