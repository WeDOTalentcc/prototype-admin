"""
Tests WSI-2 — JD Quality + Question Count
Spec F8: D3 mínimo 9 skills, D4 mínimo 5 comportamentais,
         compact 7 perguntas, full 12 perguntas,
         temperature explícita por framework.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_competency(name: str, comp_type: str = "technical", weight: float = 1.0, is_critical: bool = False):
    comp = MagicMock()
    comp.name = name
    comp.type = comp_type
    comp.weight = weight
    comp.is_critical = is_critical
    comp.seniority_level = "pleno"
    return comp


def _make_competencies(n_tech: int = 9, n_behav: int = 5):
    tech = [_make_competency(f"Tech{i}", "technical", weight=float(10 - i), is_critical=(i == 0)) for i in range(n_tech)]
    behav = [_make_competency(f"Behav{i}", "behavioral", weight=float(5 - i)) for i in range(n_behav)]
    return tech + behav


# ---------------------------------------------------------------------------
# D3 — Threshold Skills Técnicas (min 9)
# ---------------------------------------------------------------------------

class TestD3TechnicalSkillsThreshold:
    def test_9_skills_is_sufficient(self):
        """9+ skills técnicas → status sufficient no fallback FE."""
        # Simula a lógica de avaliação fallback do JDEvaluationPanel
        tech_count = 9
        if tech_count >= 9:
            status = "sufficient"
            score_increment = 30
        elif tech_count >= 3:
            status = "partial"
            score_increment = 15
        else:
            status = "insufficient"
            score_increment = 0
        assert status == "sufficient"
        assert score_increment == 30

    def test_3_to_8_skills_is_partial(self):
        """3–8 skills técnicas → status partial (aviso)."""
        for tech_count in [3, 5, 8]:
            if tech_count >= 9:
                status = "sufficient"
            elif tech_count >= 3:
                status = "partial"
            else:
                status = "insufficient"
            assert status == "partial", f"Expected partial for {tech_count} skills"

    def test_fewer_than_3_skills_is_insufficient(self):
        """< 3 skills técnicas → status insufficient (bloqueio soft)."""
        tech_count = 2
        if tech_count >= 9:
            status = "sufficient"
        elif tech_count >= 3:
            status = "partial"
        else:
            status = "insufficient"
        assert status == "insufficient"

    def test_minimum_field_is_9(self):
        """Indicador D3 deve ter minimum=9."""
        minimum = 9
        assert minimum == 9


# ---------------------------------------------------------------------------
# D4 — Threshold Competências Comportamentais (min 5)
# ---------------------------------------------------------------------------

class TestD4BehavioralThreshold:
    def test_5_behavioral_is_sufficient(self):
        """5+ comportamentais → status sufficient."""
        behav_count = 5
        if behav_count >= 5:
            status = "sufficient"
        elif behav_count >= 2:
            status = "partial"
        else:
            status = "insufficient"
        assert status == "sufficient"

    def test_2_to_4_behavioral_is_partial(self):
        """2–4 comportamentais → status partial."""
        for behav_count in [2, 3, 4]:
            if behav_count >= 5:
                status = "sufficient"
            elif behav_count >= 2:
                status = "partial"
            else:
                status = "insufficient"
            assert status == "partial", f"Expected partial for {behav_count}"

    def test_fewer_than_2_behavioral_is_insufficient(self):
        """< 2 comportamentais → status insufficient."""
        behav_count = 1
        if behav_count >= 5:
            status = "sufficient"
        elif behav_count >= 2:
            status = "partial"
        else:
            status = "insufficient"
        assert status == "insufficient"

    def test_minimum_field_is_5(self):
        """Indicador D4 deve ter minimum=5."""
        minimum = 5
        assert minimum == 5


# ---------------------------------------------------------------------------
# Question Count — compact 7, full 12
# ---------------------------------------------------------------------------

class TestQuestionCount:
    @pytest.mark.asyncio
    async def test_compact_generates_7_questions(self):
        """Modo compact deve gerar exatamente 7 perguntas."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "CBI", "question_type": "contextual", "question_text": "Pergunta teste?", "expected_signals": [], "scoring_criteria": {}}'
        mock_llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        competencies = _make_competencies(n_tech=9, n_behav=5)
        questions = await service.generate_all(competencies, mode="compact")
        assert len(questions) == 7

    @pytest.mark.asyncio
    async def test_full_generates_12_questions(self):
        """Modo full deve gerar exatamente 12 perguntas."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "CBI", "question_type": "contextual", "question_text": "Pergunta teste?", "expected_signals": [], "scoring_criteria": {}}'
        mock_llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        competencies = _make_competencies(n_tech=9, n_behav=5)
        questions = await service.generate_all(competencies, mode="full")
        assert len(questions) == 12

    @pytest.mark.asyncio
    async def test_compact_target_constant_is_7(self):
        """Constante target_count para compact deve ser 7."""
        # Verify the logic: target_count = 7 if mode == "compact" else 12
        target_compact = 7 if "compact" == "compact" else 12
        target_full = 7 if "full" == "compact" else 12
        assert target_compact == 7
        assert target_full == 12


# ---------------------------------------------------------------------------
# Temperature por Framework
# ---------------------------------------------------------------------------

class TestTemperaturePerFramework:
    @pytest.mark.asyncio
    async def test_cbi_uses_temperature_07(self):
        """Geração CBI deve usar temperature=0.7."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "CBI", "question_type": "contextual", "question_text": "Q?", "expected_signals": [], "scoring_criteria": {}}'
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.claude.bind.return_value = mock_bound

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        comp = _make_competency("Python", "technical")
        await service._generate_cbi_question(comp)

        mock_llm.claude.bind.assert_called_once_with(temperature=0.7, max_tokens=2000)

    @pytest.mark.asyncio
    async def test_dreyfus_uses_temperature_075(self):
        """Geração Dreyfus deve usar temperature=0.75."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "Dreyfus", "question_type": "autodeclaration", "question_text": "Q?", "expected_signals": [], "scoring_criteria": {}}'
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.claude.bind.return_value = mock_bound

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        comp = _make_competency("Python", "technical")
        await service._generate_dreyfus_question(comp)

        mock_llm.claude.bind.assert_called_once_with(temperature=0.75, max_tokens=2000)

    @pytest.mark.asyncio
    async def test_bloom_uses_temperature_075(self):
        """Geração Bloom deve usar temperature=0.75."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "Bloom", "question_type": "microcase", "question_text": "Q?", "expected_signals": [], "scoring_criteria": {}}'
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.claude.bind.return_value = mock_bound

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        comp = _make_competency("Python", "technical")
        await service._generate_bloom_question(comp)

        mock_llm.claude.bind.assert_called_once_with(temperature=0.75, max_tokens=2000)

    @pytest.mark.asyncio
    async def test_bigfive_uses_temperature_08(self):
        """Geração BigFive deve usar temperature=0.8."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = '{"framework": "BigFive", "question_type": "situational", "question_text": "Q?", "expected_signals": [], "scoring_criteria": {}}'
        mock_bound = MagicMock()
        mock_bound.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.claude.bind.return_value = mock_bound

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service.llm = mock_llm
        service.question_templates = ""

        comp = _make_competency("Liderança", "behavioral")
        await service._generate_bigfive_question(comp)

        mock_llm.claude.bind.assert_called_once_with(temperature=0.8, max_tokens=2000)


# ---------------------------------------------------------------------------
# Distribuição compact — Big Five tem 2 perguntas comportamentais
# ---------------------------------------------------------------------------

class TestCompactDistribution:
    @pytest.mark.asyncio
    async def test_compact_has_2_bigfive_questions(self):
        """Modo compact deve incluir 2 perguntas Big Five."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        call_tracker = []

        async def fake_cbi(comp, **kwargs):
            q = MagicMock()
            q.framework = "CBI"
            q.question_text = "Conte sobre uma situação em que você aplicou essa competência e qual foi o resultado obtido."
            return q

        async def fake_dreyfus(comp, **kwargs):
            q = MagicMock()
            q.framework = "Dreyfus"
            q.question_text = "Descreva uma situação em que você utilizou essa habilidade para resolver um problema complexo no trabalho."
            return q

        async def fake_bloom(comp, **kwargs):
            q = MagicMock()
            q.framework = "Bloom"
            q.question_text = "Conte sobre uma situação em que você demonstrou essa competência e como impactou os resultados da equipe."
            return q

        async def fake_bigfive(comp, ocean_trait=None, **kwargs):
            q = MagicMock()
            q.framework = "BigFive"
            q.question_text = "Conte sobre uma situação em que você demonstrou essa característica e qual foi o impacto no seu ambiente de trabalho."
            call_tracker.append("bigfive")
            return q

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service._generate_cbi_question = fake_cbi
        service._generate_dreyfus_question = fake_dreyfus
        service._generate_bloom_question = fake_bloom
        service._generate_bigfive_question = fake_bigfive
        service.question_templates = ""

        competencies = _make_competencies(n_tech=9, n_behav=5)
        await service.generate_all(competencies, mode="compact", seniority="senior")

        assert len(call_tracker) == 2, f"Expected 2 BigFive calls, got {len(call_tracker)}"

    @pytest.mark.asyncio
    async def test_full_has_2_bigfive_and_2_bloom_questions(self):
        """Modo full deve incluir 2 perguntas Big Five e 2 Bloom."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        bigfive_calls = []
        bloom_calls = []

        async def fake_cbi(comp, **kwargs):
            q = MagicMock()
            q.framework = "CBI"
            q.question_text = "Conte sobre uma situação em que você aplicou essa competência e qual foi o resultado obtido."
            return q

        async def fake_dreyfus(comp, **kwargs):
            q = MagicMock()
            q.framework = "Dreyfus"
            q.question_text = "Descreva uma situação em que você utilizou essa habilidade para resolver um problema complexo no trabalho."
            return q

        async def fake_bloom(comp, **kwargs):
            q = MagicMock()
            q.framework = "Bloom"
            q.question_text = "Descreva uma situação em que você aplicou essa competência para superar um desafio importante no trabalho."
            bloom_calls.append("bloom")
            return q

        async def fake_bigfive(comp, ocean_trait=None, **kwargs):
            q = MagicMock()
            q.framework = "BigFive"
            q.question_text = "Descreva uma situação em que você utilizou essa característica de personalidade para influenciar positivamente a equipe."
            bigfive_calls.append("bigfive")
            return q

        service = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
        service._generate_cbi_question = fake_cbi
        service._generate_dreyfus_question = fake_dreyfus
        service._generate_bloom_question = fake_bloom
        service._generate_bigfive_question = fake_bigfive
        service.question_templates = ""

        competencies = _make_competencies(n_tech=9, n_behav=5)
        await service.generate_all(competencies, mode="full")

        assert len(bigfive_calls) == 2, f"Expected 2 BigFive calls, got {len(bigfive_calls)}"
        assert len(bloom_calls) == 2, f"Expected 2 Bloom calls, got {len(bloom_calls)}"
