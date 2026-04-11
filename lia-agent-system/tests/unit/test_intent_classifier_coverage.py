"""
Unit tests for IntentClassifierService — Sprint I4 (coverage gate 40%).

Cobre funções puras sem dependência de LLM:
  - IntentType enum values
  - ClassificationResult model validation
  - _quick_classify: CORRECTION, DEVIATION, QUESTION, REUSE_VACANCY, None
  - _extract_entities: salary (k, R$, mil), work_model, location, seniority, skills
  - classify() com use_llm=False: empty input, quick path, entities
  - ENTITY_PATTERNS, CORRECTION_INDICATORS, DEVIATION_INDICATORS constants
"""
import pytest

pytestmark = pytest.mark.easy

from app.shared.services.intent_classifier import (
    IntentType,
    ClassificationResult,
    IntentClassifierService,
)


@pytest.fixture
def classifier():
    return IntentClassifierService()


# ── IntentType enum ────────────────────────────────────────────────────────────

class TestIntentTypeEnum:
    def test_values_exist(self):
        assert IntentType.DATA_INPUT == "DATA_INPUT"
        assert IntentType.QUESTION == "QUESTION"
        assert IntentType.CORRECTION == "CORRECTION"
        assert IntentType.DEVIATION == "DEVIATION"
        assert IntentType.REUSE_VACANCY == "REUSE_VACANCY"

    def test_is_str_enum(self):
        assert isinstance(IntentType.DATA_INPUT, str)

    def test_all_five_values(self):
        assert len(list(IntentType)) == 5


# ── ClassificationResult model ─────────────────────────────────────────────────

class TestClassificationResult:
    def test_required_fields(self):
        result = ClassificationResult(
            intent_type=IntentType.DATA_INPUT,
            confidence=0.9,
            extracted_entities={},
            original_text="test",
        )
        assert result.intent_type == IntentType.DATA_INPUT
        assert result.confidence == 0.9
        assert result.original_text == "test"
        assert result.extracted_entities == {}

    def test_confidence_bounds_zero(self):
        result = ClassificationResult(
            intent_type=IntentType.QUESTION,
            confidence=0.0,
            extracted_entities={},
            original_text="",
        )
        assert result.confidence == 0.0

    def test_confidence_bounds_one(self):
        result = ClassificationResult(
            intent_type=IntentType.CORRECTION,
            confidence=1.0,
            extracted_entities={"key": "val"},
            original_text="x",
        )
        assert result.confidence == 1.0

    def test_optional_reasoning(self):
        result = ClassificationResult(
            intent_type=IntentType.DEVIATION,
            confidence=0.5,
            extracted_entities={},
            original_text="pula",
            reasoning="Rule-based",
        )
        assert result.reasoning == "Rule-based"

    def test_reasoning_defaults_none(self):
        result = ClassificationResult(
            intent_type=IntentType.DEVIATION,
            confidence=0.5,
            extracted_entities={},
            original_text="x",
        )
        assert result.reasoning is None


# ── _quick_classify ────────────────────────────────────────────────────────────

class TestQuickClassify:
    def test_correction_na_verdade(self, classifier):
        assert classifier._quick_classify("na verdade é 10k") == IntentType.CORRECTION

    def test_correction_errei(self, classifier):
        assert classifier._quick_classify("errei o salário") == IntentType.CORRECTION

    def test_correction_corrijo(self, classifier):
        assert classifier._quick_classify("corrijo: são 3 vagas") == IntentType.CORRECTION

    def test_correction_nao_e(self, classifier):
        assert classifier._quick_classify("não é isso, é remoto") == IntentType.CORRECTION

    def test_reuse_vacancy_fast_track(self, classifier):
        assert classifier._quick_classify("fast track dessa vaga") == IntentType.REUSE_VACANCY

    def test_reuse_vacancy_aproveitar(self, classifier):
        assert classifier._quick_classify("aproveitar vaga anterior") == IntentType.REUSE_VACANCY

    def test_reuse_vacancy_clonar(self, classifier):
        assert classifier._quick_classify("clonar vaga do mês passado") == IntentType.REUSE_VACANCY

    def test_deviation_pula(self, classifier):
        assert classifier._quick_classify("pula essa etapa") == IntentType.DEVIATION

    def test_deviation_skip(self, classifier):
        assert classifier._quick_classify("skip") == IntentType.DEVIATION

    def test_deviation_proximo(self, classifier):
        assert classifier._quick_classify("próximo") == IntentType.DEVIATION

    def test_question_ends_with_question_mark(self, classifier):
        assert classifier._quick_classify("qual é o salário?") == IntentType.QUESTION

    def test_question_starts_with_como(self, classifier):
        assert classifier._quick_classify("como funciona?") == IntentType.QUESTION

    def test_question_starts_with_qual(self, classifier):
        assert classifier._quick_classify("qual o formato?") == IntentType.QUESTION

    def test_question_quanto(self, classifier):
        assert classifier._quick_classify("quanto é o budget?") == IntentType.QUESTION

    def test_returns_none_for_data_input(self, classifier):
        assert classifier._quick_classify("Engenheiro Python, 15k, remoto") is None

    def test_returns_none_for_generic_text(self, classifier):
        assert classifier._quick_classify("A vaga é para São Paulo") is None

    def test_empty_string_returns_none(self, classifier):
        # Empty text — not matched by any indicator
        result = classifier._quick_classify("")
        assert result is None

    def test_deviation_not_matched_when_ends_with_question(self, classifier):
        # "pula?" — deviation indicator but ends with "?" — should be QUESTION or None
        result = classifier._quick_classify("pula?")
        assert result == IntentType.QUESTION


# ── _extract_entities ──────────────────────────────────────────────────────────

class TestExtractEntities:
    def test_salary_k_notation(self, classifier):
        entities = classifier._extract_entities("salário de 15k por mês")
        assert "salary" in entities
        assert entities["salary"] == 15.0

    def test_salary_reais_notation(self, classifier):
        entities = classifier._extract_entities("R$ 8.000")
        assert "salary" in entities

    def test_salary_mil_notation(self, classifier):
        entities = classifier._extract_entities("20 mil reais")
        assert "salary" in entities
        assert entities["salary"] == 20.0

    def test_work_model_remoto(self, classifier):
        entities = classifier._extract_entities("trabalho remoto")
        assert entities.get("work_model") == "remoto"

    def test_work_model_hibrido(self, classifier):
        entities = classifier._extract_entities("modelo híbrido")
        assert entities.get("work_model") == "híbrido"

    def test_work_model_presencial(self, classifier):
        entities = classifier._extract_entities("trabalho presencial")
        assert entities.get("work_model") == "presencial"

    def test_location_state_abbrev(self, classifier):
        entities = classifier._extract_entities("localização em SP")
        assert "location" in entities

    def test_seniority_senior(self, classifier):
        entities = classifier._extract_entities("vaga para senior")
        assert entities.get("seniority") in ("senior", "sênior", "sênior".lower())

    def test_seniority_junior(self, classifier):
        entities = classifier._extract_entities("nível júnior")
        assert "seniority" in entities

    def test_seniority_pleno(self, classifier):
        entities = classifier._extract_entities("desenvolvedor pleno")
        assert entities.get("seniority") == "pleno"

    def test_skill_python(self, classifier):
        entities = classifier._extract_entities("precisa saber Python e Docker")
        assert "skills" in entities
        assert "Python" in entities["skills"]

    def test_skill_react(self, classifier):
        entities = classifier._extract_entities("React e TypeScript obrigatórios")
        assert "skills" in entities
        assert "React" in entities["skills"]

    def test_multiple_skills(self, classifier):
        entities = classifier._extract_entities("Python, Docker e Kubernetes")
        assert "skills" in entities
        assert len(entities["skills"]) >= 2

    def test_no_entities_plain_text(self, classifier):
        entities = classifier._extract_entities("olá, tudo bem?")
        assert entities == {}

    def test_skills_deduplicated(self, classifier):
        entities = classifier._extract_entities("Python Python Python")
        assert entities.get("skills", []).count("Python") == 1


# ── classify() with use_llm=False ─────────────────────────────────────────────

class TestClassifyRuleBased:
    @pytest.mark.asyncio
    async def test_empty_input_returns_data_input(self, classifier):
        result = await classifier.classify("", use_llm=False)
        assert result.intent_type == IntentType.DATA_INPUT
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_whitespace_input_returns_data_input(self, classifier):
        result = await classifier.classify("   ", use_llm=False)
        assert result.intent_type == IntentType.DATA_INPUT

    @pytest.mark.asyncio
    async def test_correction_indicator_classified(self, classifier):
        result = await classifier.classify("na verdade o salário é 12k", use_llm=False)
        assert result.intent_type == IntentType.CORRECTION

    @pytest.mark.asyncio
    async def test_deviation_indicator_classified(self, classifier):
        result = await classifier.classify("pula essa parte", use_llm=False)
        assert result.intent_type == IntentType.DEVIATION

    @pytest.mark.asyncio
    async def test_reuse_vacancy_classified(self, classifier):
        result = await classifier.classify("fast track da vaga anterior", use_llm=False)
        assert result.intent_type == IntentType.REUSE_VACANCY

    @pytest.mark.asyncio
    async def test_original_text_preserved(self, classifier):
        text = "errei, é presencial"
        result = await classifier.classify(text, use_llm=False)
        assert result.original_text == text

    @pytest.mark.asyncio
    async def test_entities_included_in_result(self, classifier):
        result = await classifier.classify("salário de 20k remoto", use_llm=False)
        assert isinstance(result.extracted_entities, dict)


# ── Constants integrity ────────────────────────────────────────────────────────

class TestConstants:
    def test_correction_indicators_non_empty(self, classifier):
        assert len(classifier.CORRECTION_INDICATORS) >= 5

    def test_deviation_indicators_non_empty(self, classifier):
        assert len(classifier.DEVIATION_INDICATORS) >= 5

    def test_reuse_vacancy_indicators_non_empty(self, classifier):
        assert len(classifier.REUSE_VACANCY_INDICATORS) >= 10

    def test_entity_patterns_has_salary(self, classifier):
        assert "salary" in classifier.ENTITY_PATTERNS

    def test_entity_patterns_has_skills(self, classifier):
        assert "skills" in classifier.ENTITY_PATTERNS

    def test_entity_patterns_has_work_model(self, classifier):
        assert "work_model" in classifier.ENTITY_PATTERNS

    def test_entity_patterns_has_seniority(self, classifier):
        assert "seniority" in classifier.ENTITY_PATTERNS

    def test_entity_patterns_has_location(self, classifier):
        assert "location" in classifier.ENTITY_PATTERNS
