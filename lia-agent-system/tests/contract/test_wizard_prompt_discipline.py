"""Sensor: wizard orchestrator system prompt must contain canonical values.

Harness engineering — guide computacional. Validates that the system prompt
includes screening canonical values, tool-calling discipline, auto-fill
instructions, and PII mask token suppression.

Prevents regression: LLM inventing screening numbers, hallucinating benefits,
reproducing [PERSON REMOVIDO] tokens, or ignoring company data.
"""
import pytest


def _get_system_prompt_base():
    from app.domains.job_creation.orchestrator.wizard_orchestrator import (
        _SYSTEM_PROMPT_BASE,
    )
    return _SYSTEM_PROMPT_BASE


class TestWizardPromptCanonicalValues:
    """Pin canonical screening values in the system prompt."""

    def test_compact_mode_7_questions(self):
        prompt = _get_system_prompt_base()
        assert "COMPACTO: 7 perguntas" in prompt or "COMPACTO: 7" in prompt, (
            "System prompt must state compact mode = 7 questions (canonical). "
            "Fix: add '- Modo COMPACTO: 7 perguntas (5 tecnicas + 2 comportamentais)' "
            "to _SYSTEM_PROMPT_BASE in wizard_orchestrator.py"
        )

    def test_full_mode_12_questions(self):
        prompt = _get_system_prompt_base()
        assert "COMPLETO: 12 perguntas" in prompt or "COMPLETO: 12" in prompt, (
            "System prompt must state full mode = 12 questions (canonical). "
            "Fix: add '- Modo COMPLETO: 12 perguntas (8 tecnicas + 4 comportamentais)' "
            "to _SYSTEM_PROMPT_BASE in wizard_orchestrator.py"
        )

    def test_values_match_screening_mode_config(self):
        from app.domains.job_creation.helpers.screening_mode_config import (
            SCREENING_MODE_CONFIG,
        )
        prompt = _get_system_prompt_base()
        compact_q = SCREENING_MODE_CONFIG["compact"]["total_questions"]
        full_q = SCREENING_MODE_CONFIG["full"]["total_questions"]
        assert str(compact_q) in prompt, (
            f"System prompt must contain compact total_questions={compact_q} "
            f"from screening_mode_config.py"
        )
        assert str(full_q) in prompt, (
            f"System prompt must contain full total_questions={full_q} "
            f"from screening_mode_config.py"
        )


class TestWizardPromptToolDiscipline:
    """Pin tool-calling discipline instructions."""

    def test_set_job_fields_immediate(self):
        prompt = _get_system_prompt_base()
        assert "set_job_fields" in prompt and "IMEDIATAMENTE" in prompt, (
            "System prompt must instruct immediate set_job_fields on data receipt. "
            "Fix: add tool-calling discipline section to _SYSTEM_PROMPT_BASE"
        )

    def test_never_invent_benefits(self):
        prompt = _get_system_prompt_base()
        assert "suggest_benefits" in prompt, (
            "System prompt must reference suggest_benefits tool. "
            "Fix: add instruction to call suggest_benefits before citing benefits"
        )

    def test_never_invent_salary(self):
        prompt = _get_system_prompt_base()
        assert "suggest_salary" in prompt, (
            "System prompt must reference suggest_salary tool"
        )


class TestWizardPromptPIIMaskSuppression:
    """Pin PII mask token suppression in output."""

    def test_pii_tokens_suppressed(self):
        prompt = _get_system_prompt_base()
        for token in ["EMAIL REMOVIDO", "CPF REMOVIDO", "PERSON REMOVIDO"]:
            assert token in prompt, (
                f"System prompt must mention [{token}] suppression. "
                f"LLM must never reproduce PII mask tokens in visible output."
            )

    def test_ficha_viva_reference(self):
        prompt = _get_system_prompt_base()
        assert "parsed_manager_email" in prompt or "ficha viva" in prompt, (
            "System prompt must reference ficha viva for PII data access"
        )


class TestWizardPromptAutoFill:
    """Pin proactive auto-fill instruction."""

    def test_proactive_autofill_instruction(self):
        prompt = _get_system_prompt_base()
        assert "proativamente" in prompt.lower() or "proativo" in prompt.lower(), (
            "System prompt must instruct proactive auto-fill from company context"
        )
