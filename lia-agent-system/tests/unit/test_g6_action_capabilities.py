"""G6 canonical contract — action tools awareness in system prompt.

Tests that the system prompt now explicitly grants the LLM persona
the capability to call action tools, preventing the "I'm just text"
refusal pattern Paulo encountered (turn 18 in the Phase A audit chat:
"consegue preencher campos dessa página?" → LIA refused).
"""
from __future__ import annotations

import pytest

from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


class TestActionCapabilitiesInPrompt:
    def test_acoes_section_present(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        assert "### Capabilities — Ações" in prompt, (
            "Capabilities — Ações section missing — LLM raw path will "
            "continue to refuse actions ('sou apenas um assistente de "
            "texto') contradicting the actual tool registry."
        )

    def test_lists_core_categories(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        # Major categories the user expects (per Paulo's Phase A vision)
        for category in [
            "**VAGAS**",
            "**CANDIDATOS**",
            "**COMUNICAÇÃO**",
            "**AGENDAMENTO**",
            "**EMPRESA / CONFIG**",
            "**ANALYTICS / RELATÓRIOS**",
        ]:
            assert category in prompt, (
                f"Action category {category} missing from Capabilities — Ações"
            )

    def test_lists_specific_action_tools(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        # Sample action tools that Paulo's questions implied existed
        sample_tools = [
            "update_candidate_stage",
            "reject_candidate",
            "send_email",
            "send_whatsapp",
            "close_job",
            "schedule_interview",
            "save_hiring_policy",
            "search_candidates",
            "analyze_cv_match",
            "generate_report",
        ]
        for tool in sample_tools:
            assert tool in prompt, (
                f"Action tool `{tool}` not mentioned in Capabilities — "
                f"Ações. LLM may refuse to call it."
            )

    def test_includes_nl_to_tool_examples(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        # Examples in PT-BR that map natural language to tool name
        assert "rejeite o candidato" in prompt
        assert "mande um email" in prompt
        assert "fecha a vaga" in prompt
        assert "agenda entrevista" in prompt

    def test_includes_never_refuse_rule(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        # The hard rule that fixes the "I can't" refusal
        assert "NUNCA recuse uma ação" in prompt
        assert "sou apenas um assistente de texto" in prompt.lower() or \
               "sou apenas um" in prompt.lower()

    def test_includes_confirmation_rule_for_destructive(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        assert "SEMPRE confirme antes de ações destrutivas" in prompt

    def test_section_order_navegacao_before_acoes(self):
        """G3 Navegação section must come before G6 Ações section so
        navigation requests resolve first (they're usually simpler)."""
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        nav_idx = prompt.find("### Capabilities — Navegação")
        act_idx = prompt.find("### Capabilities — Ações")
        assert nav_idx != -1 and act_idx != -1
        assert nav_idx < act_idx, (
            "Navegação section must precede Ações for canonical order"
        )

    def test_acoes_section_with_page_context_does_not_explode(self):
        """Building with any context_page must still emit the Ações section
        (it is invariant across pages — tools are tenant-wide)."""
        from app.shared.canonical_pages import CanonicalPage
        for page in [
            CanonicalPage.CONFIGURACOES.value,
            CanonicalPage.FUNIL_TALENTOS.value,
            CanonicalPage.VAGAS.value,
            CanonicalPage.GENERAL.value,
        ]:
            prompt = SystemPromptBuilder.build(
                agent_type="orchestrator",
                context_page=page,
            )
            assert "### Capabilities — Ações" in prompt, (
                f"Ações section missing for context_page={page!r}"
            )
