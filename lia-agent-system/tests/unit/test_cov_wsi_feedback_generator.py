"""Coverage tests for wsi_feedback_generator.py — pure helper methods."""
import pytest
from app.domains.cv_screening.services.wsi_feedback_generator import (
    WSIFeedbackGenerator,
    get_feedback_generator,
    BLOOM_STRENGTH_PHRASES,
    BLOOM_DEVELOPMENT_PHRASES,
    DREYFUS_DEVELOPMENT_PHRASES,
)


@pytest.fixture
def gen():
    return WSIFeedbackGenerator()


SAMPLE_SCORES = [
    {
        "competency": "technical_skills",
        "bloom_level": 3,
        "dreyfus_level": 2,
        "evidences": ["Explicou como otimizou uma query SQL reduzindo tempo em 40%"],
    },
    {
        "competency": "problem_solving",
        "bloom_level": 3,
        "dreyfus_level": 3,
        "evidences": ["Descreveu abordagem de diagnóstico de bugs em produção"],
    },
    {
        "competency": "interpersonal_skills",
        "bloom_level": 2,
        "dreyfus_level": 2,
        "evidences": [],
    },
    {
        "competency": "motivation",
        "bloom_level": 4,
        "dreyfus_level": 3,
        "evidences": [],
    },
]


class TestAvg:
    def test_simple_average(self, gen):
        scores = [{"bloom_level": 2}, {"bloom_level": 4}]
        assert gen._avg(scores, "bloom_level") == 3

    def test_missing_key_uses_default(self, gen):
        scores = [{"other_key": 5}]
        assert gen._avg(scores, "bloom_level", default=2) == 2

    def test_empty_list_uses_default(self, gen):
        assert gen._avg([], "bloom_level", default=3) == 3

    def test_rounds_to_int(self, gen):
        scores = [{"v": 1}, {"v": 2}, {"v": 2}]
        result = gen._avg(scores, "v")
        assert isinstance(result, int)

    def test_single_item(self, gen):
        scores = [{"x": 5}]
        assert gen._avg(scores, "x") == 5


class TestStrengthPhrase:
    def test_returns_string(self, gen):
        result = gen._strength_phrase(3, 2, [])
        assert isinstance(result, str)
        assert len(result) > 10

    def test_starts_with_voce(self, gen):
        result = gen._strength_phrase(3, 2, [])
        assert result.startswith("Você")

    def test_dreyfus_4_shows_estrategica(self, gen):
        result = gen._strength_phrase(3, 4, [])
        assert "estratégica" in result

    def test_dreyfus_3_shows_autonomia(self, gen):
        result = gen._strength_phrase(3, 3, [])
        assert "autonomia" in result

    def test_dreyfus_2_shows_crescente(self, gen):
        result = gen._strength_phrase(3, 2, [])
        assert "crescente" in result

    def test_dreyfus_1_shows_potencial(self, gen):
        result = gen._strength_phrase(3, 1, [])
        assert "potencial" in result

    def test_with_evidence_included(self, gen):
        evidences = ["Resolveu problema de performance em 2 horas"]
        result = gen._strength_phrase(3, 2, evidences)
        assert "Resolveu" in result

    def test_evidence_truncated_at_110_chars(self, gen):
        long_ev = "A" * 200
        result = gen._strength_phrase(3, 2, [long_ev])
        # Evidence is truncated before inclusion
        assert len(result) < 400


class TestDevelopmentPhrase:
    def test_returns_string(self, gen):
        result = gen._development_phrase(3, 2, 4)
        assert isinstance(result, str)

    def test_bloom_at_or_above_expected(self, gen):
        result = gen._development_phrase(4, 3, 4)
        assert "continuar evoluindo" in result

    def test_bloom_below_expected(self, gen):
        result = gen._development_phrase(2, 2, 4)
        assert "crescimento" in result

    def test_bloom_6_at_max(self, gen):
        result = gen._development_phrase(6, 4, 4)
        assert isinstance(result, str)

    def test_includes_dreyfus_tip_when_below_expected(self, gen):
        result = gen._development_phrase(2, 2, 5)
        # Should include dreyfus development tip
        assert len(result) > 50


class TestSuggestion:
    def test_returns_string(self, gen):
        result = gen._suggestion("technical_skills", 3)
        assert isinstance(result, str)
        assert len(result) > 5

    def test_unknown_competency_uses_default(self, gen):
        result = gen._suggestion("unknown_competency_xyz", 3)
        assert isinstance(result, str)

    def test_bloom_level_1(self, gen):
        result = gen._suggestion("technical_skills", 1)
        assert isinstance(result, str)

    def test_bloom_level_6(self, gen):
        result = gen._suggestion("technical_skills", 6)
        assert isinstance(result, str)

    def test_different_competencies(self, gen):
        for comp in ["problem_solving", "interpersonal_skills", "motivation", "_communication"]:
            result = gen._suggestion(comp, 3)
            assert isinstance(result, str)


class TestIntro:
    def test_contains_first_name(self, gen):
        tone_cfg = {"intro_opener": "Ficamos felizes com sua participação.", "bloom_expectation": 3, "tone": "encouraging"}
        result = gen._intro("Ana", "Backend Engineer", tone_cfg)
        assert "Ana" in result

    def test_contains_job_title(self, gen):
        tone_cfg = {"intro_opener": "Obrigado pela participação.", "bloom_expectation": 4, "tone": "professional"}
        result = gen._intro("Bruno", "Data Scientist", tone_cfg)
        assert "Data Scientist" in result

    def test_contains_feedback_word(self, gen):
        tone_cfg = {"intro_opener": "Obrigado!", "bloom_expectation": 3, "tone": "friendly"}
        result = gen._intro("Carlos", "DevOps", tone_cfg)
        assert "feedback" in result.lower()


class TestClosing:
    def test_contains_first_name(self, gen):
        result = gen._closing("Diana")
        assert "Diana" in result

    def test_contains_revisao_instruction(self, gen):
        result = gen._closing("Eduardo")
        assert "revisão" in result.lower() or "e-mail" in result

    def test_returns_string_of_decent_length(self, gen):
        result = gen._closing("Fernanda")
        assert len(result) > 50


class TestGroupByCompetency:
    def test_groups_correctly(self, gen):
        scores = [
            {"competency": "technical_skills", "bloom_level": 3},
            {"competency": "technical_skills", "bloom_level": 4},
            {"competency": "problem_solving", "bloom_level": 2},
        ]
        groups = gen._group_by_competency(scores)
        assert len(groups["technical_skills"]) == 2
        assert len(groups["problem_solving"]) == 1

    def test_missing_competency_uses_general(self, gen):
        scores = [{"bloom_level": 3}]
        groups = gen._group_by_competency(scores)
        assert "general" in groups

    def test_empty_returns_empty(self, gen):
        assert gen._group_by_competency([]) == {}


class TestPlainText:
    def test_returns_string(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "senior", "Ana Silva")
        assert isinstance(report["plain_text"], str)

    def test_contains_ai_disclaimer(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "senior", "Ana Silva")
        assert "IA" in report["plain_text"]

    def test_contains_dimension_titles(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "senior", "Ana Silva")
        assert "##" in report["plain_text"]


class TestWhatsAppText:
    def test_returns_string(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "junior", "Bruno Costa")
        assert isinstance(report["whatsapp_text"], str)

    def test_contains_first_name(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "junior", "Bruno Costa")
        assert "Bruno" in report["whatsapp_text"]

    def test_contains_email_reference(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "junior", "Bruno Costa")
        assert "e-mail" in report["whatsapp_text"]

    def test_max_3_dimensions(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Dev", "pleno", "Carlos")
        text = report["whatsapp_text"]
        # Should not have more than 3 dimension titles
        assert text.count("*") <= 20  # rough check


class TestChatText:
    def test_returns_string(self, gen):
        report = gen.generate(SAMPLE_SCORES, "PM", "pleno", "Diana")
        assert isinstance(report["chat_text"], str)

    def test_contains_ai_disclaimer(self, gen):
        report = gen.generate(SAMPLE_SCORES, "PM", "pleno", "Diana")
        assert "IA" in report["chat_text"]


class TestGenerate:
    def test_returns_dict_with_all_keys(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Backend Engineer", "senior", "Ana Silva")
        for key in ["candidate_name", "first_name", "job_title", "seniority_level",
                    "tone", "dimensions", "intro", "closing",
                    "plain_text", "whatsapp_text", "chat_text"]:
            assert key in report

    def test_first_name_extracted(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Dev", "junior", "Carlos Eduardo")
        assert report["first_name"] == "Carlos"

    def test_invalid_seniority_defaults_junior(self, gen):
        report = gen.generate(SAMPLE_SCORES, "Dev", "xyz_unknown", "Ana")
        assert report["seniority_level"] == "junior"

    def test_seniority_fuzzy_match(self, gen):
        # "lead" contains "lead" literally, so should match
        report = gen.generate(SAMPLE_SCORES, "Dev", "tech-lead", "Ana")
        assert report["seniority_level"] == "lead"

    def test_empty_scores_generates_report(self, gen):
        report = gen.generate([], "Dev", "junior", "Bruno")
        assert report is not None
        assert "dimensions" in report

    def test_all_seniority_levels(self, gen):
        for level in ["estagiario", "junior", "pleno", "senior", "lead"]:
            report = gen.generate(SAMPLE_SCORES, "Dev", level, "Test")
            assert report["seniority_level"] == level


class TestGetFeedbackGenerator:
    def test_returns_instance(self):
        gen_instance = get_feedback_generator()
        assert isinstance(gen_instance, WSIFeedbackGenerator)

    def test_returns_singleton(self):
        gen1 = get_feedback_generator()
        gen2 = get_feedback_generator()
        assert gen1 is gen2


class TestLanguageTables:
    def test_bloom_strength_all_levels(self):
        for level in range(1, 7):
            assert level in BLOOM_STRENGTH_PHRASES
            assert isinstance(BLOOM_STRENGTH_PHRASES[level], str)

    def test_bloom_development_all_levels(self):
        for level in range(1, 7):
            assert level in BLOOM_DEVELOPMENT_PHRASES

    def test_dreyfus_development_all_levels(self):
        for level in range(1, 5):
            assert level in DREYFUS_DEVELOPMENT_PHRASES
