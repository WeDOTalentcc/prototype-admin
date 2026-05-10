"""
Tests WSI-6 — Big Five Pipeline F2.5→F3→F5→F6.6

Spec: F2.5 OCEAN scoring, F3 ranking, F5 seniority selection, F6.6 trait-specific question.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_generator():
    from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator
    gen = WSIQuestionGenerator.__new__(WSIQuestionGenerator)
    gen.llm = MagicMock()
    return gen


def _make_ocean_scores(scores: dict = None):
    from app.domains.cv_screening.services.wsi_service import OceanTraitScore
    defaults = {
        "openness": 80,
        "conscientiousness": 70,
        "extraversion": 60,
        "agreeableness": 50,
        "stability": 40,
    }
    merged = {**defaults, **(scores or {})}
    return [
        OceanTraitScore(trait=t, score=merged[t], confidence="medium")
        for t in merged
    ]


def _make_competency(name="Comunicação", ctype="behavioral", weight=1.0, is_critical=False, seniority_level="pleno", big_five_mapping=None):
    from app.domains.cv_screening.services.wsi_service import Competency
    return Competency(name=name, type=ctype, weight=weight, is_critical=is_critical, seniority_level=seniority_level, big_five_mapping=big_five_mapping)


# ---------------------------------------------------------------------------
# TestF25OceanExtraction
# ---------------------------------------------------------------------------

class TestF25OceanExtraction:
    @pytest.mark.asyncio
    async def test_result_has_five_traits(self):
        """F2.5 deve retornar exatamente 5 traits OCEAN."""
        from app.domains.cv_screening.services.wsi_service import WSIQuestionGenerator

        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "big_five_jd": {
                "openness":          {"score": 80, "evidence": ["liderança técnica"], "confidence": "high"},
                "conscientiousness": {"score": 70, "evidence": ["entrega rigorosa"], "confidence": "high"},
                "extraversion":      {"score": 60, "evidence": ["comunicação clara"], "confidence": "medium"},
                "agreeableness":     {"score": 50, "evidence": [],                    "confidence": "medium"},
                "stability":         {"score": 40, "evidence": [],                    "confidence": "low"}
            }
        }"""
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        result = await gen._extract_ocean_scores("Vaga de engenheiro sênior")
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_scores_between_0_and_100(self):
        """Todos os scores devem estar no intervalo 0-100."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "big_five_jd": {
                "openness":          {"score": 95,  "evidence": ["inovação contínua"], "confidence": "high"},
                "conscientiousness": {"score": 10,  "evidence": [],                    "confidence": "low"},
                "extraversion":      {"score": 55,  "evidence": ["comunicação"],       "confidence": "medium"},
                "agreeableness":     {"score": 0,   "evidence": [],                    "confidence": "low"},
                "stability":         {"score": 100, "evidence": ["alta pressão"],      "confidence": "high"}
            }
        }"""
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        result = await gen._extract_ocean_scores("Vaga de analista")
        for trait_score in result:
            assert 0 <= trait_score.score <= 100

    @pytest.mark.asyncio
    async def test_traits_sorted_descending(self):
        """Traits devem ser retornados ordenados por score decrescente."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "big_five_jd": {
                "openness":          {"score": 30, "evidence": [],                   "confidence": "low"},
                "conscientiousness": {"score": 90, "evidence": ["rigor em entregas"],"confidence": "high"},
                "extraversion":      {"score": 50, "evidence": ["reuniões"],         "confidence": "medium"},
                "agreeableness":     {"score": 70, "evidence": ["colaboração"],      "confidence": "high"},
                "stability":         {"score": 10, "evidence": [],                   "confidence": "low"}
            }
        }"""
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        result = await gen._extract_ocean_scores("Vaga de gerente")
        scores = [t.score for t in result]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_uses_temperature_04(self):
        """F2.5 deve chamar LLM com temperature=0.1 (safe_invoke)."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "big_five_jd": {
                "openness":          {"score": 60, "evidence": [], "confidence": "medium"},
                "conscientiousness": {"score": 60, "evidence": [], "confidence": "medium"},
                "extraversion":      {"score": 60, "evidence": [], "confidence": "medium"},
                "agreeableness":     {"score": 60, "evidence": [], "confidence": "medium"},
                "stability":         {"score": 60, "evidence": [], "confidence": "medium"}
            }
        }"""
        gen.llm.safe_invoke = AsyncMock(return_value=mock_response)

        await gen._extract_ocean_scores("descrição da vaga")

        gen.llm.safe_invoke.assert_called_once()
        call_kwargs = gen.llm.safe_invoke.call_args
        assert call_kwargs.kwargs.get("temperature") == 0.1 or (
            len(call_kwargs.args) >= 2 and call_kwargs.args[1] == 0.1
        )

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self):
        """Deve retornar 5 traits com score=60 quando LLM falha."""
        gen = _make_generator()
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(side_effect=Exception("LLM down"))

        result = await gen._extract_ocean_scores("qualquer vaga")
        assert len(result) == 5
        assert all(t.score == 60 for t in result)


# ---------------------------------------------------------------------------
# TestF5SenioritySelection
# ---------------------------------------------------------------------------

class TestF5SenioritySelection:
    def test_junior_selects_2(self):
        gen = _make_generator()
        traits = _make_ocean_scores()
        result = gen._select_traits_by_seniority(
            [t for t in sorted(traits, key=lambda x: x.score, reverse=True)], "junior"
        )
        assert len(result) == 2

    def test_pleno_selects_3(self):
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        traits = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        result = gen._select_traits_by_seniority(traits, "pleno")
        assert len(result) == 3

    def test_senior_selects_3(self):
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        traits = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        result = gen._select_traits_by_seniority(traits, "senior")
        assert len(result) == 3

    def test_lead_selects_4(self):
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        traits = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        result = gen._select_traits_by_seniority(traits, "lead")
        assert len(result) == 4

    def test_diretor_selects_5(self):
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        traits = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        result = gen._select_traits_by_seniority(traits, "diretor")
        assert len(result) == 5

    def test_unknown_seniority_defaults_to_3(self):
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        traits = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        result = gen._select_traits_by_seniority(traits, "indefinido")
        assert len(result) == 3


# ---------------------------------------------------------------------------
# TestF66TraitQuestion
# ---------------------------------------------------------------------------

class TestF66TraitQuestion:
    @pytest.mark.asyncio
    async def test_trait_label_in_prompt(self):
        """Quando ocean_trait fornecido, label PT deve estar no prompt enviado ao LLM."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "question_text": "Descreva uma situação...",
            "expected_signals": ["A", "B"],
            "scoring_criteria": {"score_5": "excelente"}
        }"""
        captured_prompt = []

        async def capture_ainvoke(prompt, **kwargs):
            captured_prompt.append(str(prompt))
            return mock_response

        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = capture_ainvoke

        comp = _make_competency()
        await gen._generate_bigfive_question(comp, ocean_trait="conscientiousness")

        assert len(captured_prompt) == 1
        assert "conscientiousness" in captured_prompt[0]
        assert "Organização" in captured_prompt[0] or "disciplina" in captured_prompt[0]

    @pytest.mark.asyncio
    async def test_ocean_trait_saved_in_scoring_criteria(self):
        """ocean_trait deve ser salvo em scoring_criteria da pergunta gerada."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "question_text": "Como você lida com prazos?",
            "expected_signals": ["prazo", "entrega"],
            "scoring_criteria": {"score_5": "perfeito"}
        }"""
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        comp = _make_competency()
        question = await gen._generate_bigfive_question(comp, ocean_trait="openness")

        assert question.scoring_criteria.get("ocean_trait") == "openness"

    @pytest.mark.asyncio
    async def test_backwards_compat_no_trait(self):
        """Sem ocean_trait, método deve funcionar normalmente sem ocean_trait no scoring_criteria."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = """{
            "question_text": "Descreva uma situação.",
            "expected_signals": ["A"],
            "scoring_criteria": {"score_5": "bom"}
        }"""
        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = AsyncMock(return_value=mock_response)

        comp = _make_competency()
        question = await gen._generate_bigfive_question(comp)

        assert "ocean_trait" not in question.scoring_criteria

    @pytest.mark.asyncio
    async def test_conscientiousness_label_in_prompt(self):
        """Trait conscientiousness deve incluir contexto de organização/entrega no prompt."""
        gen = _make_generator()
        mock_response = MagicMock()
        mock_response.content = '{"question_text": "X", "expected_signals": [], "scoring_criteria": {}}'
        captured = []

        async def capture_ainvoke2(p, **kwargs):
            captured.append(str(p))
            return mock_response

        gen.llm.claude = MagicMock()
        gen.llm.claude.bind.return_value.ainvoke = capture_ainvoke2

        comp = _make_competency()
        await gen._generate_bigfive_question(comp, ocean_trait="conscientiousness")

        assert "entrega" in captured[0].lower() or "organização" in captured[0].lower() or "método" in captured[0].lower()

    @pytest.mark.asyncio
    async def test_compact_generates_two_distinct_traits(self):
        """No modo compact com jd, as 2 perguntas BigFive devem usar traits distintos (top-2 do F5)."""
        gen = _make_generator()

        # Mock _extract_ocean_scores
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        ranked = [
            OceanTraitScore("conscientiousness", 90),
            OceanTraitScore("extraversion", 80),
            OceanTraitScore("openness", 70),
            OceanTraitScore("agreeableness", 60),
            OceanTraitScore("stability", 50),
        ]
        gen._extract_ocean_scores = AsyncMock(return_value=ranked)

        # Mock individual question generators
        async def fake_bigfive(comp, ocean_trait=None, **kwargs):
            from app.domains.cv_screening.services.wsi_service import WSIQuestion
            return WSIQuestion(
                id="q-" + (ocean_trait or "none"),
                competency=comp.name,
                framework="BigFive",
                question_type="situational",
                question_text=f"Conte sobre uma situação em que você demonstrou {ocean_trait or 'competência'} no seu trabalho e como esse comportamento influenciou os resultados da equipe.",
                weight=1.0,
                expected_signals=[],
                scoring_criteria={"ocean_trait": ocean_trait} if ocean_trait else {},
            )

        gen._generate_bigfive_question = fake_bigfive
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))

        technical = [_make_competency(f"Tech{i}", "technical", weight=0.8) for i in range(5)]
        behavioral = [_make_competency(f"Beh{i}", "behavioral", weight=0.7) for i in range(5)]

        questions = await gen.generate_all(
            technical + behavioral,
            mode="compact",
            job_description="Vaga de engenheiro",
            seniority="senior",
        )

        bigfive_qs = [q for q in questions if q.framework == "BigFive"]
        traits_used = [q.scoring_criteria.get("ocean_trait") for q in bigfive_qs]
        # junior selects top-2: conscientiousness and extraversion
        assert "conscientiousness" in traits_used
        assert "extraversion" in traits_used


def _stub_question(comp, framework):
    from app.domains.cv_screening.services.wsi_service import WSIQuestion
    return WSIQuestion(
        id=f"stub-{framework}-{comp.name}",
        competency=comp.name,
        framework=framework,
        question_type="contextual",
        question_text=f"Conte sobre uma situação em que você demonstrou {comp.name} no seu trabalho e como isso impactou o resultado.",
        weight=comp.weight,
        expected_signals=[],
        scoring_criteria={},
    )


# ---------------------------------------------------------------------------
# TestGenerateAllPipeline
# ---------------------------------------------------------------------------

class TestGenerateAllPipeline:
    @pytest.mark.asyncio
    async def test_without_jd_uses_positional_fallback(self):
        """Sem job_description, _extract_ocean_scores NÃO deve ser chamado."""
        gen = _make_generator()
        gen._extract_ocean_scores = AsyncMock()
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))
        gen._generate_bigfive_question = AsyncMock(side_effect=lambda c, ocean_trait=None, **kwargs: _stub_question(c, "BigFive"))

        technical = [_make_competency(f"T{i}", "technical", weight=0.8) for i in range(5)]
        behavioral = [_make_competency(f"B{i}", "behavioral", weight=0.7) for i in range(5)]

        await gen.generate_all(technical + behavioral, mode="compact")

        gen._extract_ocean_scores.assert_not_called()

    @pytest.mark.asyncio
    async def test_with_jd_calls_extract_ocean_scores(self):
        """Com job_description, _extract_ocean_scores deve ser chamado."""
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        ranked = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        gen._extract_ocean_scores = AsyncMock(return_value=ranked)
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))
        gen._generate_bigfive_question = AsyncMock(side_effect=lambda c, ocean_trait=None, **kwargs: _stub_question(c, "BigFive"))

        technical = [_make_competency(f"T{i}", "technical", weight=0.8) for i in range(5)]
        behavioral = [_make_competency(f"B{i}", "behavioral", weight=0.7) for i in range(5)]

        await gen.generate_all(technical + behavioral, mode="compact", job_description="JD texto")

        gen._extract_ocean_scores.assert_called_once()
        call_args = gen._extract_ocean_scores.call_args
        assert "JD texto" in call_args[0] or call_args[1].get("job_description") == "JD texto" or call_args[0][0] == "JD texto"

    @pytest.mark.asyncio
    async def test_compact_bigfive_count_is_2(self):
        """Modo compact deve gerar exatamente 2 perguntas BigFive."""
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        ranked = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        gen._extract_ocean_scores = AsyncMock(return_value=ranked)
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))
        gen._generate_bigfive_question = AsyncMock(side_effect=lambda c, ocean_trait=None, **kwargs: _stub_question(c, "BigFive"))

        technical = [_make_competency(f"T{i}", "technical", weight=0.8) for i in range(5)]
        behavioral = [_make_competency(f"B{i}", "behavioral", weight=0.7) for i in range(5)]

        questions = await gen.generate_all(
            technical + behavioral, mode="compact", job_description="JD", seniority="senior"
        )
        bigfive_count = sum(1 for q in questions if q.framework == "BigFive")
        assert bigfive_count == 2

    @pytest.mark.asyncio
    async def test_full_bigfive_count_is_2(self):
        """Modo full deve gerar exatamente 2 perguntas BigFive."""
        gen = _make_generator()
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        ranked = [OceanTraitScore(t, 60) for t in
                  ["openness", "conscientiousness", "extraversion", "agreeableness", "stability"]]
        gen._extract_ocean_scores = AsyncMock(return_value=ranked)
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))
        gen._generate_bigfive_question = AsyncMock(side_effect=lambda c, ocean_trait=None, **kwargs: _stub_question(c, "BigFive"))

        technical = [_make_competency(f"T{i}", "technical", weight=0.8) for i in range(7)]
        behavioral = [_make_competency(f"B{i}", "behavioral", weight=0.7) for i in range(7)]

        questions = await gen.generate_all(
            technical + behavioral, mode="full", job_description="JD"
        )
        bigfive_count = sum(1 for q in questions if q.framework == "BigFive")
        assert bigfive_count == 2


# ---------------------------------------------------------------------------
# TestF66TraitAffinity — WSI-7: seleção por afinidade de trait
# ---------------------------------------------------------------------------

class TestF66TraitAffinity:

    def test_select_comp_by_trait_exact_match(self):
        """_select_comp_by_trait deve retornar competência cujo big_five_mapping == trait."""
        gen = _make_generator()
        behavioral = [
            _make_competency("Colaboração", big_five_mapping="agreeableness"),
            _make_competency("Organização", big_five_mapping="conscientiousness"),
            _make_competency("Inovação", big_five_mapping="openness"),
        ]
        comp, idx = gen._select_comp_by_trait("conscientiousness", behavioral, set())
        assert comp.name == "Organização"
        assert idx == 1

    def test_select_comp_by_trait_fallback_positional(self):
        """Sem big_five_mapping correspondente, deve cair no fallback posicional."""
        gen = _make_generator()
        behavioral = [
            _make_competency("Comunicação"),  # sem big_five_mapping
            _make_competency("Liderança"),
        ]
        comp, idx = gen._select_comp_by_trait("stability", behavioral, set())
        # Fallback: primeira não usada
        assert idx == 0
        assert comp.name == "Comunicação"

    def test_select_comp_by_trait_skips_used_indices(self):
        """_select_comp_by_trait deve pular índices já usados mesmo no match exato."""
        gen = _make_generator()
        behavioral = [
            _make_competency("Organização", big_five_mapping="conscientiousness"),
            _make_competency("Disciplina", big_five_mapping="conscientiousness"),
        ]
        used = {0}  # idx 0 já usado
        comp, idx = gen._select_comp_by_trait("conscientiousness", behavioral, used)
        assert idx == 1
        assert comp.name == "Disciplina"

    def test_select_comp_by_trait_no_duplicates_two_traits(self):
        """Dois traits distintos devem retornar duas competências diferentes."""
        gen = _make_generator()
        behavioral = [
            _make_competency("Organização", big_five_mapping="conscientiousness"),
            _make_competency("Colaboração", big_five_mapping="agreeableness"),
            _make_competency("Comunicação", big_five_mapping="extraversion"),
        ]
        used: set = set()
        comp1, idx1 = gen._select_comp_by_trait("conscientiousness", behavioral, used)
        used.add(idx1)
        comp2, idx2 = gen._select_comp_by_trait("agreeableness", behavioral, used)
        used.add(idx2)
        assert comp1.name != comp2.name
        assert idx1 != idx2

    @pytest.mark.asyncio
    async def test_generate_all_compact_uses_trait_affinity(self):
        """compact mode: F6.6 deve usar competência com big_five_mapping=top_trait."""
        from app.domains.cv_screening.services.wsi_service import OceanTraitScore
        gen = _make_generator()

        ranked = [
            OceanTraitScore("conscientiousness", 90),
            OceanTraitScore("agreeableness", 80),
            OceanTraitScore("openness", 70),
        ]
        gen._extract_ocean_scores = AsyncMock(return_value=ranked)
        gen._generate_cbi_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "CBI"))
        gen._generate_dreyfus_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Dreyfus"))
        gen._generate_bloom_question = AsyncMock(side_effect=lambda c, **kwargs: _stub_question(c, "Bloom"))

        bigfive_calls = []
        async def capture_bigfive(comp, ocean_trait=None, **kwargs):
            bigfive_calls.append((comp.name, ocean_trait, comp.big_five_mapping))
            return _stub_question(comp, "BigFive")
        gen._generate_bigfive_question = capture_bigfive

        technical = [_make_competency(f"T{i}", "technical", weight=0.1) for i in range(5)]
        behavioral = [
            _make_competency("CBI-top", "behavioral", weight=0.2),
            _make_competency("Organização", "behavioral", weight=0.15, big_five_mapping="conscientiousness"),
            _make_competency("Colaboração", "behavioral", weight=0.12, big_five_mapping="agreeableness"),
            _make_competency("Inovação", "behavioral", weight=0.10, big_five_mapping="openness"),
            _make_competency("Comunicação", "behavioral", weight=0.08),
        ]

        await gen.generate_all(technical + behavioral, mode="compact", job_description="JD test", seniority="senior")

        assert len(bigfive_calls) == 2
        # primeira BigFive deve ter trait=conscientiousness → competência "Organização"
        assert bigfive_calls[0][1] == "conscientiousness"
        assert bigfive_calls[0][0] == "Organização"
        # segunda BigFive deve ter trait=agreeableness → competência "Colaboração"
        assert bigfive_calls[1][1] == "agreeableness"
        assert bigfive_calls[1][0] == "Colaboração"


# ---------------------------------------------------------------------------
# TestF1CBridge — WSI-7: _build_competencies_from_enriched_jd + _merge_with_enriched
# ---------------------------------------------------------------------------

class TestF1CBridge:

    def test_build_competencies_extracts_skills_obrigatorias(self):
        """Deve criar Competency(type=technical) para cada item de skills_obrigatorias."""
        from app.domains.cv_screening.services.wsi_service import WSIService
        enriched = {
            "skills_obrigatorias": [
                {"skill": "Python", "contexto": "APIs REST"},
                {"skill": "Docker", "contexto": "containerização"},
                {"skill": "PostgreSQL", "contexto": "banco principal"},
            ],
            "competencias_comportamentais": [],
        }
        comps, jd_ctx = WSIService._build_competencies_from_enriched_jd(enriched, "senior")
        technical = [c for c in comps if c.type == "technical"]
        assert len(technical) == 3
        assert technical[0].name == "Python"
        assert technical[0].is_critical is True   # top 3 são críticas
        assert technical[2].is_critical is False

    def test_build_competencies_extracts_behavioral_with_trait(self):
        """Deve criar Competency(type=behavioral) com big_five_mapping preenchido."""
        from app.domains.cv_screening.services.wsi_service import WSIService
        enriched = {
            "skills_obrigatorias": [],
            "competencias_comportamentais": [
                {"competencia": "Organização", "trait_big_five": "conscientiousness"},
                {"competencia": "Colaboração", "trait_big_five": "agreeableness"},
                {"competencia": "Inovação", "trait_big_five": "openness"},
            ],
        }
        comps, _ = WSIService._build_competencies_from_enriched_jd(enriched, "pleno")
        behavioral = [c for c in comps if c.type == "behavioral"]
        assert len(behavioral) == 3
        assert behavioral[0].big_five_mapping == "conscientiousness"
        assert behavioral[1].big_five_mapping == "agreeableness"
        assert behavioral[2].big_five_mapping == "openness"

    def test_build_competencies_jd_context_uses_about_role(self):
        """jd_context deve conter about_role e responsabilidades."""
        from app.domains.cv_screening.services.wsi_service import WSIService
        enriched = {
            "about_role": "Engenheiro responsável por APIs críticas.",
            "responsabilidades": ["Desenvolver APIs", "Revisar PRs"],
            "skills_obrigatorias": [],
            "competencias_comportamentais": [],
        }
        _, jd_ctx = WSIService._build_competencies_from_enriched_jd(enriched)
        assert "Engenheiro responsável por APIs críticas." in jd_ctx
        assert "Desenvolver APIs" in jd_ctx

    def test_merge_with_enriched_fills_missing_big_five_mapping(self):
        """_merge_with_enriched deve copiar big_five_mapping de enriquecida para original sem mapeamento."""
        from app.domains.cv_screening.services.wsi_service import WSIService
        original = [
            _make_competency("Organização", "behavioral"),        # sem big_five_mapping
            _make_competency("Colaboração", "behavioral", big_five_mapping="agreeableness"),  # já tem
        ]
        enriched = [
            _make_competency("Organização", "behavioral", big_five_mapping="conscientiousness"),
        ]
        merged = WSIService._merge_with_enriched(original, enriched)
        org = next(c for c in merged if c.name == "Organização")
        col = next(c for c in merged if c.name == "Colaboração")
        assert org.big_five_mapping == "conscientiousness"   # copiado do enriquecido
        assert col.big_five_mapping == "agreeableness"       # não sobrescrito

    def test_merge_with_enriched_adds_missing_behavioral(self):
        """_merge_with_enriched deve adicionar comportamentais do enriquecido ausentes no original."""
        from app.domains.cv_screening.services.wsi_service import WSIService
        original = [_make_competency("Comunicação", "behavioral")]
        enriched = [
            _make_competency("Comunicação", "behavioral", big_five_mapping="extraversion"),
            _make_competency("Inovação", "behavioral", big_five_mapping="openness"),  # nova
        ]
        merged = WSIService._merge_with_enriched(original, enriched)
        names = [c.name for c in merged]
        assert "Inovação" in names

    @pytest.mark.asyncio
    async def test_generate_screening_questions_with_enriched_jd(self):
        """generate_screening_questions com enriched_jd deve preencher big_five_mapping."""
        from app.domains.cv_screening.services.wsi_service import WSIService, OceanTraitScore
        service = WSIService.__new__(WSIService)

        captured_competencies = []
        async def mock_generate_all(comps, mode, job_description=None, seniority=None):
            captured_competencies.extend(comps)
            return []

        service.question_generator = MagicMock()
        service.question_generator.generate_all = mock_generate_all

        enriched_jd = {
            "about_role": "Vaga para dev Python sênior.",
            "responsabilidades": ["Desenvolver APIs REST"],
            "skills_obrigatorias": [{"skill": "Python", "contexto": "backend"}],
            "competencias_comportamentais": [
                {"competencia": "Organização", "trait_big_five": "conscientiousness"},
            ],
        }
        original_comps = [_make_competency("Organização", "behavioral")]

        await service.generate_screening_questions(
            competencies=original_comps,
            mode="compact",
            enriched_jd=enriched_jd,
            seniority="senior",
        )

        org = next((c for c in captured_competencies if c.name == "Organização"), None)
        assert org is not None
        assert org.big_five_mapping == "conscientiousness"
