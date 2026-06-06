"""G3 canonical contract — navigation capability unified across paths.

Tests:
1. system_prompt_builder.build() includes Navegação capability section.
2. _extract_navigate_marker correctly strips marker + extracts page.
3. Unknown page in marker → no ui_action emitted (graceful).
4. ChatAdapter._convert_response promotes marker to ui_action shape.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.orchestrator.context.chat_adapter import (
    ChatAdapter,
    _extract_navigate_marker,
)
from app.shared.canonical_pages import CanonicalPage
from app.shared.prompts.system_prompt_builder import SystemPromptBuilder


class TestSystemPromptIncludesNavegacao:
    def test_navegacao_section_present(self):
        """The Capabilities — Navegação section must be in every orchestrator prompt."""
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        assert "### Capabilities — Navegação" in prompt, (
            "Navegação section missing — LLM raw path will continue to refuse "
            "navigation ('não consigo navegar') contradicting the ACTIONABLE_INTENTS "
            "and Rail A paths that DO navigate."
        )

    def test_navegacao_lists_canonical_pages(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        # Should mention the canonical identifiers
        for page in [
            "vagas", "funil_talentos", "configuracoes",
            "agent_studio", "recrutar", "dashboard",
        ]:
            assert f"`{page}`" in prompt, (
                f"Canonical page `{page}` missing from Navegação section"
            )

    def test_navegacao_documents_marker_format(self):
        prompt = SystemPromptBuilder.build(agent_type="orchestrator")
        assert "[NAVIGATE:" in prompt, (
            "Marker syntax [NAVIGATE:<page>] must be documented in the prompt "
            "so the LLM knows the convention."
        )


class TestExtractNavigateMarker:
    def test_marker_present_canonical_page(self):
        text = "Te levando para Configurações! 🚀 [NAVIGATE:configuracoes]"
        result = _extract_navigate_marker(text)
        assert result is not None
        clean, page, _params = result
        assert page == "configuracoes"
        assert "[NAVIGATE:" not in clean
        assert "Te levando" in clean

    def test_marker_present_with_whitespace(self):
        text = "Vou pra Funil [NAVIGATE: funil_talentos ]"
        result = _extract_navigate_marker(text)
        assert result is not None
        clean, page, _params = result
        assert page == "funil_talentos"
        assert "[NAVIGATE:" not in clean

    def test_marker_case_insensitive(self):
        text = "OK [navigate:vagas]"
        result = _extract_navigate_marker(text)
        assert result is not None
        _, page, _params = result
        assert page == "vagas"

    def test_marker_with_legacy_alias(self):
        """Legacy alias in marker normalizes to canonical."""
        text = "Indo pro kanban [NAVIGATE:kanban]"
        result = _extract_navigate_marker(text)
        assert result is not None
        clean, page, _params = result
        # Legacy 'kanban' → canonical 'pipeline_kanban'
        assert page == CanonicalPage.PIPELINE_KANBAN.value
        assert "[NAVIGATE:" not in clean

    def test_no_marker(self):
        text = "Como posso te ajudar?"
        assert _extract_navigate_marker(text) is None

    def test_unknown_page_strips_marker_no_action(self):
        """Unknown page → strip marker silently, still no ui_action contract."""
        text = "Indo [NAVIGATE:totally-fake-page]"
        result = _extract_navigate_marker(text)
        # Marker stripped, but page is GENERAL (caller skips ui_action)
        assert result is not None
        clean, page, _params = result
        assert page == CanonicalPage.GENERAL.value
        assert "[NAVIGATE:" not in clean


class TestChatAdapterPromotesMarker:
    def _make_adapter(self):
        adapter = ChatAdapter.__new__(ChatAdapter)
        return adapter

    def test_marker_in_content_promotes_to_ui_action(self):
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = "Te levando! [NAVIGATE:configuracoes]"
        orch.intent_detected = "general"
        orch.agent_used = "test"
        orch.fairness_warnings = []
        orch.from_cache = False
        orch.structured_data = None
        orch.action_result = None
        orch.pending_action_id = None
        orch.needs_confirmation = False
        orch.needs_params = False
        orch.success = True

        result = adapter._convert_response(orch)

        assert result.get("ui_action") == "navigate_to"
        assert result.get("ui_action_params") == {"page": "configuracoes"}
        assert "[NAVIGATE:" not in result["response"]
        assert "Te levando" in result["response"]

    def test_no_marker_no_ui_action_promoted(self):
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = "Resposta normal sem marker"
        orch.intent_detected = "general"
        orch.agent_used = "test"
        orch.fairness_warnings = []
        orch.from_cache = False
        orch.structured_data = None
        orch.action_result = None
        orch.pending_action_id = None
        orch.needs_confirmation = False
        orch.needs_params = False
        orch.success = True

        result = adapter._convert_response(orch)

        # No ui_action_promoted when no marker
        assert "ui_action" not in result or result.get("ui_action") != "navigate_to"

    def test_unknown_page_marker_stripped_no_ui_action(self):
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = "Hmm [NAVIGATE:fake-page]"
        orch.intent_detected = "general"
        orch.agent_used = "test"
        orch.fairness_warnings = []
        orch.from_cache = False
        orch.structured_data = None
        orch.action_result = None
        orch.pending_action_id = None
        orch.needs_confirmation = False
        orch.needs_params = False
        orch.success = True

        result = adapter._convert_response(orch)

        # Marker stripped from response
        assert "[NAVIGATE:" not in result["response"]
        # GENERAL → no ui_action (silently degraded)
        assert "ui_action" not in result or result.get("ui_action") != "navigate_to"



def test_navegacao_id_form_vaga_especifica():
    """Fix #6 (2026-06-06): abrir VAGA/CANDIDATO especifico precisa da forma
    com id no prompt -- senao o agente nao abre a vaga certa (so a lista)."""
    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert "[NAVIGATE:vaga_detalhe:<id>]" in prompt
    assert "candidato_detalhe:<id>" in prompt


def test_navegacao_navega_direto_sem_perguntar():
    """Fix #5 (2026-06-06): pedido explicito -> navegar DIRETO, sem
    'posso te levar?' (so pergunta se a decisao for da IA)."""
    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert "navegue DIRETO" in prompt


def test_navegacao_nao_oferece_quando_nao_pedido():
    """Over-nav P2 (2026-06-06): o agente NAO deve oferecer/perguntar 'posso
    te levar para X?' nem navegar para responder pergunta de DADOS -- so quando
    o usuario pede explicitamente. (Paulo: oferta de navegacao nao-solicitada
    e indevida; a decisao de trocar de tela e do usuario.)"""
    prompt = SystemPromptBuilder.build(agent_type="orchestrator")
    assert "NUNCA OFERECA navegar" in prompt
    assert "NAO e pedido" in prompt
