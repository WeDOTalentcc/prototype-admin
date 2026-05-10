"""Coverage tests for talent_assistant_prompts.py — pure text classification."""
import pytest
from app.domains.recruiter_assistant.prompts.talent_assistant_prompts import (
    TalentCommandType,
    TALENT_COMMAND_TYPES,
    COMMAND_KEYWORDS,
    _is_negated,
    detect_talent_command_type,
    get_talent_system_prompt,
    get_talent_prompt_template,
)


class TestTalentCommandType:
    def test_all_values_are_strings(self):
        for cmd in TalentCommandType:
            assert isinstance(cmd.value, str)

    def test_rankear_candidatos_exists(self):
        assert TalentCommandType.RANKEAR_CANDIDATOS == "rankear_candidatos"

    def test_comparar_candidatos_exists(self):
        assert TalentCommandType.COMPARAR_CANDIDATOS == "comparar_candidatos"

    def test_analise_geral_exists(self):
        assert TalentCommandType.ANALISE_GERAL == "analise_geral"


class TestTalentCommandTypes:
    def test_lookup_by_value(self):
        cmd = TALENT_COMMAND_TYPES.get("rankear_candidatos")
        assert cmd == TalentCommandType.RANKEAR_CANDIDATOS

    def test_all_commands_present(self):
        for cmd in TalentCommandType:
            assert cmd.value in TALENT_COMMAND_TYPES


class TestCommandKeywords:
    def test_has_expected_commands(self):
        assert "rankear_candidatos" in COMMAND_KEYWORDS
        assert "comparar_candidatos" in COMMAND_KEYWORDS

    def test_each_command_has_keywords(self):
        for cmd, keywords in COMMAND_KEYWORDS.items():
            assert len(keywords) > 0


class TestIsNegated:
    def test_nao_quero_rankear(self):
        assert _is_negated("nao quero rankear", "rankear") is True

    def test_sem_negacao(self):
        assert _is_negated("quero rankear", "rankear") is False

    def test_nao_preciso(self):
        assert _is_negated("nao preciso comparar", "comparar") is True

    def test_empty_string(self):
        result = _is_negated("", "rankear")
        assert isinstance(result, bool)


class TestDetectTalentCommandType:
    def test_rankear_detected(self):
        cmd, confidence = detect_talent_command_type("rankear os candidatos por fit")
        assert cmd == "rankear_candidatos"
        assert confidence > 0

    def test_comparar_detected(self):
        cmd, confidence = detect_talent_command_type("compare Ana com Bruno")
        assert cmd == "comparar_candidatos"
        assert confidence > 0

    def test_analise_geral_fallback(self):
        cmd, confidence = detect_talent_command_type("o que você acha?")
        assert isinstance(cmd, str)
        assert isinstance(confidence, float)

    def test_returns_tuple(self):
        result = detect_talent_command_type("analise o perfil de Ana")
        assert len(result) == 2

    def test_analisar_detected(self):
        cmd, confidence = detect_talent_command_type("analise o perfil de João")
        assert cmd == "analisar_perfil"

    def test_skills_detected(self):
        cmd, confidence = detect_talent_command_type("quais as habilidades dos candidatos?")
        assert cmd == "skills_analysis"

    def test_top_candidatos_detected(self):
        cmd, confidence = detect_talent_command_type("quais os top candidatos?")
        assert cmd == "top_candidatos"


class TestGetTalentSystemPrompt:
    def test_returns_string(self):
        result = get_talent_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 10

    def test_called_twice_same_result(self):
        r1 = get_talent_system_prompt()
        r2 = get_talent_system_prompt()
        assert r1 == r2


class TestGetTalentPromptTemplate:
    def test_rankear_returns_string(self):
        result = get_talent_prompt_template("rankear_candidatos")
        assert isinstance(result, str)

    def test_comparar_returns_string(self):
        result = get_talent_prompt_template("comparar_candidatos")
        assert isinstance(result, str)

    def test_unknown_command_returns_string(self):
        result = get_talent_prompt_template("unknown_xyz")
        assert isinstance(result, str)

    def test_analise_geral_returns_string(self):
        result = get_talent_prompt_template("analise_geral")
        assert isinstance(result, str)
