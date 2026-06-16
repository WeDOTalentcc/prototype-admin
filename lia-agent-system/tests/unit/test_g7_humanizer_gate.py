"""G7 canonical contract — humanizer gate at chat_adapter.

The gate is the single point that all chat responses pass through before
reaching chat.py:send_message. It strips technical artifacts and leaked
markers so the user never sees a raw dict dump or backstage instruction.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.orchestrator.context.chat_adapter import (
    ChatAdapter,
    _humanize_content,
    _TECHNICAL_FALLBACK,
)


class TestHumanizeContent:
    def test_empty_passthrough(self):
        assert _humanize_content("") == ""
        assert _humanize_content("   ") == "   "

    def test_natural_text_passthrough(self):
        text = "Olá! Como posso te ajudar hoje?"
        assert _humanize_content(text) == text

    def test_inline_navigate_marker_stripped(self):
        """G3 marker leaking through gets cleaned here as defense-in-depth."""
        text = "Te levando! [NAVIGATE:configuracoes]"
        result = _humanize_content(text)
        assert "[NAVIGATE:" not in result
        assert "Te levando" in result

    def test_inline_contexto_marker_stripped(self):
        """G5 settings note leaking through backend gets cleaned here."""
        text = "Tudo bem? [contexto] Recrutador editou via UI"
        result = _humanize_content(text)
        assert "[contexto]" not in result
        assert "Tudo bem?" in result

    def test_role_prefix_stripped(self):
        """LLM occasionally echoes 'assistant: ' or 'LIA: ' prefix."""
        cases = [
            ("assistant: Olá!", "Olá!"),
            ("LIA: Como vai?", "Como vai?"),
            ("System: Configurações abertas", "Configurações abertas"),
            ("Model: Vou ajudar", "Vou ajudar"),
        ]
        for raw, expected_substring in cases:
            result = _humanize_content(raw)
            assert expected_substring in result
            assert not result.lower().startswith(("assistant:", "lia:", "system:", "model:"))

    def test_bare_json_dump_returns_fallback(self):
        """Bare {...} dump → user sees neutral fallback, not raw data."""
        result = _humanize_content('{"status": "ok", "count": 47}')
        assert result == _TECHNICAL_FALLBACK
        assert "{" not in result
        assert "status" not in result

    def test_bare_array_dump_returns_fallback(self):
        result = _humanize_content("[1, 2, 3]")
        assert result == _TECHNICAL_FALLBACK

    def test_bare_code_block_returns_fallback(self):
        result = _humanize_content("```python\nprint('hi')\n```")
        assert result == _TECHNICAL_FALLBACK

    def test_idempotent(self):
        """humanize(humanize(x)) == humanize(x) for any x."""
        cases = [
            "Olá",
            "Vou te ajudar [NAVIGATE:vagas]",
            "{}",
            "",
        ]
        for raw in cases:
            once = _humanize_content(raw)
            twice = _humanize_content(once)
            assert once == twice, (
                f"Not idempotent for {raw!r}: once={once!r}, twice={twice!r}"
            )

    def test_natural_text_with_inline_json_preserved(self):
        """Mixed prose + json snippet (e.g. example in answer) — keep both
        (the leading text proves it is not a bare dump)."""
        text = 'Veja o exemplo: {"status": "ok"} pronto!'
        result = _humanize_content(text)
        # Not technical-only — content has prose
        assert result != _TECHNICAL_FALLBACK
        assert "exemplo" in result


class TestChatAdapterAppliesHumanizer:
    """End-to-end: every response coming out of _convert_response is
    humanized — no need to humanize at each ChatResponse emit site."""

    def _make_adapter(self):
        return ChatAdapter.__new__(ChatAdapter)

    def test_navigate_marker_stripped_via_g3_and_gate(self):
        """G3 strips marker first, gate confirms no leak."""
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
        assert "[NAVIGATE:" not in result["response"]

    def test_technical_dump_replaced_with_fallback(self):
        """If upstream emits a raw dict dump as content, gate replaces it."""
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = '{"vacancy_id": "x", "status": "ok"}'
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
        assert result["response"] == _TECHNICAL_FALLBACK

    def test_contexto_leak_stripped(self):
        """Backend-side defense-in-depth for G5 frontend leak."""
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = "Tudo bem [contexto] editou perfil"
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
        assert "[contexto]" not in result["response"]
        assert "Tudo bem" in result["response"]

    def test_natural_response_passes_through(self):
        adapter = self._make_adapter()
        orch = MagicMock()
        orch.content = "Aqui estão as vagas ativas: 5 vagas encontradas."
        orch.intent_detected = "list_jobs"
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
        assert result["response"] == "Aqui estão as vagas ativas: 5 vagas encontradas."
