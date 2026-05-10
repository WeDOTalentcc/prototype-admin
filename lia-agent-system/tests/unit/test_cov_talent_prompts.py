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
    def test_values_are_strings(self):
        for cmd in TalentCommandType:
            assert isinstance(cmd.value, str)

    def test_rankear_candidatos(self):
        assert TalentCommandType.RANKEAR_CANDIDATOS == "rankear_candidatos"

    def test_comparar_candidatos(self):
        assert TalentCommandType.COMPARAR_CANDIDATOS == "comparar_candidatos"


class TestTalentCommandTypesLookup:
    def test_lookup_by_value(self):
        cmd = TALENT_COMMAND_TYPES.get("rankear_candidatos")
        assert cmd == TalentCommandType.RANKEAR_CANDIDATOS

    def test_all_commands_in_lookup(self):
        for cmd in TalentCommandType:
            assert cmd.value in TALENT_COMMAND_TYPES


class TestCommandKeywords:
    def test_has_rankear(self):
        assert "rankear_candidatos" in COMMAND_KEYWORDS

    def test_has_comparar(self):
        assert "comparar_candidatos" in COMMAND_KEYWORDS

    def test_most_commands_have_keywords(self):
        # analise_geral can legitimately be empty (catch-all)
        commands_with_kws = [k for k, v in COMMAND_KEYWORDS.items() if len(v) > 0]
        assert len(commands_with_kws) >= 10


class TestIsNegated:
    def test_negated(self):
        assert _is_negated("nao quero rankear", "rankear") is True

    def test_not_negated(self):
        assert _is_negated("quero rankear", "rankear") is False

    def test_nao_preciso(self):
        assert _is_negated("nao preciso comparar", "comparar") is True

    def test_empty_string_returns_bool(self):
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

    def test_returns_tuple(self):
        result = detect_talent_command_type("o que voce acha?")
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)

    def test_analisar_detected(self):
        cmd, confidence = detect_talent_command_type("analise o perfil de Joao")
        assert cmd == "analisar_perfil"

    def test_skills_detected(self):
        cmd, confidence = detect_talent_command_type("quais as habilidades dos candidatos?")
        assert cmd == "skills_analysis"

    def test_top_candidatos_detected(self):
        cmd, confidence = detect_talent_command_type("quais os top candidatos?")
        assert cmd == "top_candidatos"

    def test_sourcing_strategy(self):
        cmd, confidence = detect_talent_command_type("estrategia de sourcing para esta vaga")
        assert isinstance(cmd, str)

    def test_market_insights(self):
        cmd, confidence = detect_talent_command_type("insights de mercado para desenvolvedores")
        assert isinstance(cmd, str)


class TestGetTalentSystemPrompt:
    def test_returns_string(self):
        result = get_talent_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 10

    def test_deterministic(self):
        r1 = get_talent_system_prompt()
        r2 = get_talent_system_prompt()
        assert r1 == r2


class TestGetTalentPromptTemplate:
    def test_rankear_template(self):
        result = get_talent_prompt_template("rankear_candidatos")
        assert isinstance(result, str)

    def test_comparar_template(self):
        result = get_talent_prompt_template("comparar_candidatos")
        assert isinstance(result, str)

    def test_analisar_template(self):
        result = get_talent_prompt_template("analisar_perfil")
        assert isinstance(result, str)

    def test_unknown_fallback(self):
        result = get_talent_prompt_template("xyz_unknown")
        assert isinstance(result, str)

    def test_all_command_types(self):
        for cmd in TalentCommandType:
            result = get_talent_prompt_template(cmd.value)
            assert isinstance(result, str)
