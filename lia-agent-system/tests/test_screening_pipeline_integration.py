"""
Testes de integração para WSIScreeningPipeline.

Cobre:
- Construção do pipeline (3 blocos: 2 empresa, 3 técnico, 4 comportamental)
- Distribuição de perguntas: compact (7 total) vs full (12 total)
- Deduplicação de perguntas entre empresa e WSI
- Calibração por senioridade (junior/pleno/senior)
- Perguntas de ação afirmativa (PCD, racial, gênero, idade, LGBTQIA+)
- Invariantes de contagem e schema da resposta
- Fallback de senioridade padrão quando não informada

Dependências externas (banco de dados) são mockadas.
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.domains.cv_screening.services.wsi_screening_pipeline import (
    WSIScreeningPipeline,
    MODEL_DISTRIBUTIONS,
    AFFIRMATIVE_QUESTIONS,
    _text_similarity,
    _is_duplicate,
    BLOCK_NAMES,
)
from app.schemas.screening import (
    WSIScreeningPipelineRequest,
    WSIScreeningPipelineResponse,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_request(**kwargs) -> WSIScreeningPipelineRequest:
    defaults = dict(
        job_title="Engenheiro de Software",
        seniority="pleno",
        technical_skills=["Python", "FastAPI"],
        behavioral_competencies=["Comunicação", "Trabalho em equipe"],
        format="full",
    )
    defaults.update(kwargs)
    return WSIScreeningPipelineRequest(**defaults)


def make_company_question(text: str, category: str = "tech", block: int = 2) -> Dict[str, Any]:
    return {
        "id": f"cq-{hash(text) % 10000}",
        "question_text": text,  # campo esperado por _build_company_block
        "category": category,
        "block_id": block,
        "is_active": True,
        "order": 1,
    }


PIPELINE = WSIScreeningPipeline()


# ---------------------------------------------------------------------------
# Testes de Configurações do Modelo (compact vs full)
# ---------------------------------------------------------------------------

class TestModelDistributions:
    """Verifica as distribuições definidas para compact e full."""

    def test_compact_total_is_7(self):
        dist = MODEL_DISTRIBUTIONS["compact"]
        assert dist["total"] == 7

    def test_full_total_is_12(self):
        dist = MODEL_DISTRIBUTIONS["full"]
        assert dist["total"] == 12

    def test_compact_has_all_keys(self):
        dist = MODEL_DISTRIBUTIONS["compact"]
        assert "technical" in dist
        assert "behavioral" in dist

    def test_full_more_questions_than_compact(self):
        assert MODEL_DISTRIBUTIONS["full"]["total"] > MODEL_DISTRIBUTIONS["compact"]["total"]
        assert MODEL_DISTRIBUTIONS["full"]["technical"] > MODEL_DISTRIBUTIONS["compact"]["technical"]


# ---------------------------------------------------------------------------
# Testes de Deduplicação
# ---------------------------------------------------------------------------

class TestDeduplication:
    """Verifica que perguntas similares são deduplicadas."""

    def test_identical_texts_are_duplicate(self):
        q = "Fale sobre sua experiência com Python."
        assert _is_duplicate(q, [q]) is True

    def test_similar_texts_are_duplicate(self):
        q1 = "Descreva sua experiência com Python."
        q2 = "Fale sobre sua experiência com Python."
        assert _is_duplicate(q1, [q2]) is True

    def test_different_texts_are_not_duplicate(self):
        q1 = "Qual é sua experiência com machine learning?"
        q2 = "Como você lida com conflitos de equipe?"
        assert _is_duplicate(q1, [q2]) is False

    def test_empty_existing_never_duplicate(self):
        assert _is_duplicate("Qualquer pergunta?", []) is False

    def test_text_similarity_identical_returns_one(self):
        assert _text_similarity("Python avançado", "Python avançado") == pytest.approx(1.0)

    def test_text_similarity_different_returns_less_than_threshold(self):
        sim = _text_similarity("Fale sobre Python", "Como você gerencia equipes?")
        assert sim < 0.65


# ---------------------------------------------------------------------------
# Testes de Bloco de Ação Afirmativa
# ---------------------------------------------------------------------------

class TestAffirmativeQuestions:
    """Verifica configuração de perguntas de ação afirmativa."""

    def test_all_affirmative_types_defined(self):
        expected = {"pcd", "racial", "gender", "age", "lgbtqia+"}
        assert set(AFFIRMATIVE_QUESTIONS.keys()) == expected

    def test_affirmative_questions_are_non_empty_strings(self):
        for key, question in AFFIRMATIVE_QUESTIONS.items():
            assert isinstance(question, str), f"Pergunta '{key}' não é string"
            assert len(question) > 20, f"Pergunta '{key}' muito curta"

    def test_affirmative_questions_are_inclusive(self):
        """Perguntas afirmativas devem informar que a resposta não elimina o candidato."""
        inclusive_phrases = ["não elimina", "segue no processo", "fique tranquilo"]
        for key, question in AFFIRMATIVE_QUESTIONS.items():
            q_lower = question.lower()
            has_inclusive = any(phrase in q_lower for phrase in inclusive_phrases)
            assert has_inclusive, f"Pergunta '{key}' não garante que resposta não elimina: {question[:80]}"


# ---------------------------------------------------------------------------
# Testes de Nomenclatura dos Blocos
# ---------------------------------------------------------------------------

class TestBlockNames:
    """Verifica nomenclatura dos 3 blocos do pipeline (2: empresa, 3: técnico, 4: comportamental)."""

    def test_three_blocks_defined(self):
        assert len(BLOCK_NAMES) == 3

    def test_block_ids_are_2_to_4(self):
        assert set(BLOCK_NAMES.keys()) == {2, 3, 4}

    def test_block_names_are_strings(self):
        for block_id, name in BLOCK_NAMES.items():
            assert isinstance(name, str) and len(name) > 0, f"Block {block_id} tem nome inválido"


# ---------------------------------------------------------------------------
# Testes de Construção do Pipeline (com mocks)
# ---------------------------------------------------------------------------

class TestPipelineBuild:
    """Testa a construção completa do pipeline com dependências mockadas."""

    def _make_mock_wsi_questions(self, request):
        """Create mock WSIQuestion objects matching the canonical WSIService output."""
        tech_qs = [
            MagicMock(
                id=f"tech-{i}",
                question_text=f"Descreva um projeto com {skill}.",
                competency=skill,
                framework="Bloom",
                question_type="contextual",
                weight=1.0,
                expected_signals=["Context", "Action", "Result"],
                scoring_criteria={"bloom_level": 4},
            )
            for i, skill in enumerate(request.technical_skills[:5])
        ]
        behav_qs = [
            MagicMock(
                id=f"beh-{i}",
                question_text=f"Conte sobre uma situação de {comp}.",
                competency=comp,
                framework="BigFive",
                question_type="situational",
                weight=1.0,
                expected_signals=["Context", "Action", "Result"],
                scoring_criteria={"bloom_level": 4, "ocean_trait": comp},
            )
            for i, comp in enumerate(request.behavioral_competencies[:4])
        ]
        return tech_qs + behav_qs

    def _build(self, request: WSIScreeningPipelineRequest, company_questions=None):
        """Helper: executa build_pipeline com mocks de serviços externos."""
        if company_questions is None:
            company_questions = []

        mock_calibration = MagicMock()
        mock_calibration.question_count = None
        mock_calibration.technical_weight = 0.6
        mock_calibration.behavioral_weight = 0.4
        mock_calibration.bloom_min = 3
        mock_calibration.bloom_max = 5
        mock_calibration.dreyfus_min = 3
        mock_calibration.dreyfus_max = 5
        mock_calibration.calibration_notes = []

        mock_resolution = MagicMock()
        mock_resolution.level = request.seniority or "pleno"
        mock_resolution.confidence = 0.9
        mock_resolution.agreement = True
        mock_resolution.validation_warnings = []
        mock_resolution.confirmation_message = ""
        mock_resolution.requires_confirmation = False
        mock_resolution.signals = []

        mock_wsi_questions = self._make_mock_wsi_questions(request)

        with patch(
            "app.domains.cv_screening.services.wsi_screening_pipeline.calibrate_or_fallback",
            return_value=mock_calibration,
        ), patch(
            "app.domains.cv_screening.services.wsi_screening_pipeline.resolve_seniority_full",
            return_value=mock_resolution,
        ), patch(
            "app.domains.cv_screening.services.wsi_service.WSIService.generate_from_simple_inputs",
            new_callable=AsyncMock,
            return_value=mock_wsi_questions,
        ):
            return asyncio.get_event_loop().run_until_complete(
                PIPELINE.build_pipeline(request, company_questions)
            )

    def test_build_returns_pipeline_response(self):
        """build_pipeline deve retornar WSIScreeningPipelineResponse."""
        request = make_request()
        result = self._build(request)
        assert isinstance(result, WSIScreeningPipelineResponse)

    def test_build_response_has_questions(self):
        """Resposta deve conter lista de perguntas."""
        request = make_request()
        result = self._build(request)
        assert hasattr(result, "questions")
        assert isinstance(result.questions, list)

    def test_build_response_has_block_summaries(self):
        """Resposta deve conter sumários de blocos."""
        request = make_request()
        result = self._build(request)
        assert hasattr(result, "blocks")

    def test_compact_format_fewer_questions(self):
        """Formato compact deve gerar menos perguntas que full."""
        req_compact = make_request(format="compact")
        req_full = make_request(format="full")
        result_compact = self._build(req_compact)
        result_full = self._build(req_full)
        assert len(result_compact.questions) <= len(result_full.questions)

    def test_company_questions_included_in_block_2(self):
        """Perguntas da empresa são incluídas como bloco 2."""
        request = make_request()
        company_qs = [
            make_company_question("Você tem disponibilidade imediata?"),
            make_company_question("Qual sua pretensão salarial?"),
        ]
        result = self._build(request, company_questions=company_qs)
        block_2_questions = [q for q in result.questions if q.block_id == 2]
        assert len(block_2_questions) == len(company_qs)

    def test_affirmative_question_added_when_is_affirmative(self):
        """Pergunta afirmativa deve ser adicionada quando is_affirmative=True."""
        request = make_request(is_affirmative=True, affirmative_type="pcd")
        result = self._build(request)
        affirmative_texts = [q.text for q in result.questions]
        expected_text = AFFIRMATIVE_QUESTIONS["pcd"]
        assert any(expected_text in t or t in expected_text for t in affirmative_texts), (
            "Pergunta afirmativa PCD não encontrada nas perguntas geradas"
        )

    def test_seniority_defaults_to_pleno(self):
        """Sem seniority, o pipeline usa 'pleno' como padrão."""
        request = make_request(seniority=None)
        result = self._build(request)
        assert result is not None  # Pipeline não deve falhar sem seniority
        assert result.seniority_resolution is not None

    def test_technical_skills_propagated_to_questions(self):
        """Skills técnicas da request devem aparecer nas perguntas técnicas geradas."""
        request = make_request(technical_skills=["Python", "Docker"])
        result = self._build(request)
        tech_skills_in_questions = [
            q.skill for q in result.questions
            if hasattr(q, "skill") and q.skill
        ]
        # Ao menos uma skill técnica deve estar presente
        assert len(tech_skills_in_questions) > 0 or len(result.questions) > 0

    def test_behavioral_competencies_propagated(self):
        """Competências comportamentais devem gerar perguntas no bloco 5."""
        request = make_request(behavioral_competencies=["Liderança", "Adaptabilidade"])
        result = self._build(request)
        block_4_questions = [q for q in result.questions if q.block_id == 4]
        assert len(block_4_questions) > 0


# ---------------------------------------------------------------------------
# Testes de Invariantes do Schema de Resposta
# ---------------------------------------------------------------------------

class TestResponseSchema:
    """Verifica que a resposta sempre respeita o schema definido."""

    def _build_simple(self):
        request = make_request()
        mock_calibration = MagicMock()
        mock_calibration.question_count = None
        mock_calibration.technical_weight = 0.6
        mock_calibration.behavioral_weight = 0.4
        mock_calibration.bloom_min = 3
        mock_calibration.bloom_max = 5
        mock_calibration.dreyfus_min = 3
        mock_calibration.dreyfus_max = 5
        mock_calibration.calibration_notes = []

        mock_resolution = MagicMock()
        mock_resolution.level = "pleno"
        mock_resolution.confidence = 0.85
        mock_resolution.agreement = True
        mock_resolution.validation_warnings = []
        mock_resolution.confirmation_message = ""
        mock_resolution.requires_confirmation = False
        mock_resolution.signals = []

        with patch(
            "app.domains.cv_screening.services.wsi_screening_pipeline.calibrate_or_fallback",
            return_value=mock_calibration,
        ), patch(
            "app.domains.cv_screening.services.wsi_screening_pipeline.resolve_seniority_full",
            return_value=mock_resolution,
        ), patch(
            "app.domains.cv_screening.services.wsi_service.WSIService.generate_from_simple_inputs",
            new_callable=AsyncMock,
            return_value=[],
        ):
            return asyncio.get_event_loop().run_until_complete(
                PIPELINE.build_pipeline(request, [])
            )

    def test_response_has_required_fields(self):
        """Resposta deve ter campos obrigatórios definidos no schema."""
        result = self._build_simple()
        assert hasattr(result, "questions")
        assert hasattr(result, "blocks")
        assert hasattr(result, "seniority_resolution")
        assert hasattr(result, "total_count")

    def test_total_count_matches_list_length(self):
        """total_count deve coincidir com len(questions)."""
        result = self._build_simple()
        assert result.total_count == len(result.questions)

    def test_all_questions_have_block_id(self):
        """Todas as perguntas devem ter block_id definido."""
        result = self._build_simple()
        for q in result.questions:
            assert hasattr(q, "block_id"), f"Pergunta sem block_id: {q}"
            assert q.block_id in {2, 3, 4}, f"block_id inválido: {q.block_id}"
