"""
TDD Red test: WizardOrchestrator system_prompt must NOT restart when ficha has data.

Canonical-fix: the root cause is that _SYSTEM_PROMPT_BASE does not have an
explicit "NEVER restart if ficha has filled fields" instruction. Without it,
the LLM intermittently ignores the ficha viva and generates fresh-start
responses ("vamos comecar do zero / qual e o titulo?") even when
parsed_title is already set.

Red: these tests FAIL against the current _SYSTEM_PROMPT_BASE.
Green: after adding the explicit no-restart guard to _SYSTEM_PROMPT_BASE.
"""
import pytest


class TestNeverRestartSystemPrompt:
    """The system_prompt MUST contain an explicit no-restart instruction."""

    def _get_prompt(self, state: dict) -> str:
        from app.domains.job_creation.orchestrator.wizard_orchestrator import (
            WizardOrchestrator,
        )
        orch = WizardOrchestrator()
        return orch._build_system_prompt(state)

    def test_no_restart_instruction_present_when_ficha_has_title(self):
        """When parsed_title is set, prompt must forbid restarting."""
        state = {"parsed_title": "Diretor de RH"}
        prompt = self._get_prompt(state)
        # Must contain an explicit no-restart guard (any of these phrases)
        has_guard = any([
            "nunca reinici" in prompt.lower(),
            "nao reinici" in prompt.lower(),
            "nunca comece do zero" in prompt.lower(),
            "nunca recomec" in prompt.lower(),
            "campos ja preenchidos" in prompt.lower(),
            "nao peca novamente" in prompt.lower(),
            "autoritativa" in prompt.lower(),
            "absolutamente proibido" in prompt.lower(),
            # normalized: remove accents via casefold
            "nunca reinici" in prompt.casefold(),
            "n\xe3o reinici" in prompt.lower(),
            "n\xe3o pe\xe7a novamente" in prompt.lower(),
        ])
        assert has_guard, (
            "system_prompt missing no-restart guard. "
            "Add explicit instruction: NUNCA reinicie coleta se ficha tem dados. "
            "Root cause: LLM ignores ficha viva and asks for title again."
        )

    def test_no_restart_instruction_present_when_ficha_empty(self):
        """Even with empty state the prompt must have the no-restart instruction."""
        state = {}
        prompt = self._get_prompt(state)
        has_guard = any([
            "nunca reinici" in prompt.lower(),
            "n\xe3o reinici" in prompt.lower(),
            "nunca recomec" in prompt.lower(),
            "autoritativa" in prompt.lower(),
        ])
        assert has_guard, (
            "No-restart guard must always be present in system_prompt "
            "(not just when state has data). "
            "Add it to _SYSTEM_PROMPT_BASE."
        )

    def test_ficha_positioned_prominently(self):
        """Ficha viva title must appear within the first 4000 chars of prompt."""
        state = {"parsed_title": "Diretor de RH", "parsed_model": "Hibrido"}
        prompt = self._get_prompt(state)
        ficha_pos = prompt.lower().find("estado real da vaga")
        assert ficha_pos != -1, "Ficha viva section not found in system_prompt"
        assert ficha_pos < 4000, (
            f"Ficha viva section appears too late in prompt (pos={ficha_pos}). "
            "Consider moving it closer to the start."
        )


class TestFichaVivaNeverRestartLanguage:
    """The ficha viva itself must reinforce the no restart concept."""

    def _get_ficha(self, state: dict) -> str:
        from app.domains.job_creation.internal.utils import _build_wizard_state_summary
        return _build_wizard_state_summary(state)

    def test_filled_fields_clearly_marked(self):
        """Fields that are filled must be clearly listed as Campos preenchidos."""
        state = {
            "parsed_title": "Gerente de Produto",
            "parsed_seniority": "pleno",
            "parsed_model": "remoto",
        }
        ficha = self._get_ficha(state)
        assert "Campos preenchidos" in ficha or "preenchido" in ficha.lower(), (
            "Ficha viva must explicitly list Campos preenchidos so the LLM "
            "knows not to ask for those fields again."
        )
        assert "Gerente de Produto" in ficha, "parsed_title not reflected in ficha"

    def test_ficha_shows_manager_name_when_present(self):
        """parsed_manager_name must appear in ficha so LLM knows it's registered."""
        state = {
            "parsed_title": "Analista de RH",
            "parsed_manager_name": "Jose Moreira",
            "parsed_manager_email": "jose.moreira@wedotalent.cc",
        }
        ficha = self._get_ficha(state)
        assert (
            "Jose Moreira" in ficha or "gestor responsavel" in ficha.lower()
            or "jose.moreira" in ficha.lower()
        ), (
            "parsed_manager_name must appear in ficha viva so LLM does not "
            "ask for the manager name again."
        )
