"""Extended thinking (2026-06-04): chunker that turns streamed Claude thinking
into emittable reasoning_step cards. Pure-function sensor."""
import os

from app.domains.ai.services.llm import (
    _drain_thinking_steps,
    _extended_thinking_budget,
    _extended_thinking_enabled,
)


class TestDrainThinkingSteps:
    def test_splits_on_sentence_keeps_incomplete_tail(self):
        rem, steps = _drain_thinking_steps(
            "Primeiro analiso a pergunta do recrutador. "
            "Depois consulto o contexto da empresa. E entao"
        )
        assert any("Primeiro analiso a pergunta" in s for s in steps)
        assert any("Depois consulto o contexto" in s for s in steps)
        assert rem.strip() == "E entao"

    def test_splits_on_newline(self):
        rem, steps = _drain_thinking_steps("Passo um da analise\nPasso dois continua")
        assert any("Passo um da analise" in s for s in steps)
        assert rem == "Passo dois continua"

    def test_no_boundary_buffers_all(self):
        rem, steps = _drain_thinking_steps("ainda raciocinando sem fim de frase")
        assert steps == []
        assert rem == "ainda raciocinando sem fim de frase"

    def test_short_fragments_skipped(self):
        _rem, steps = _drain_thinking_steps("Ok. ")
        assert steps == []

    def test_trailing_number_buffered_not_split(self):
        # trailing "3" (no boundary) stays buffered — not emitted mid-thought
        rem, steps = _drain_thinking_steps("Vou considerar 3")
        assert rem == "Vou considerar 3"
        assert steps == []

    def test_steps_capped_at_200_chars(self):
        long = "x" * 500 + ". tail"
        _rem, steps = _drain_thinking_steps(long)
        assert all(len(s) <= 200 for s in steps)


class TestThinkingFlag:
    def test_disabled_by_default(self, monkeypatch):
        monkeypatch.delenv("LIA_EXTENDED_THINKING", raising=False)
        # sentinel may exist in dev; only assert env-path here
        if not os.path.exists("/tmp/lia_extended_thinking_on"):
            assert _extended_thinking_enabled() is False

    def test_enabled_via_env(self, monkeypatch):
        monkeypatch.setenv("LIA_EXTENDED_THINKING", "1")
        assert _extended_thinking_enabled() is True

    def test_budget_floor_1024(self, monkeypatch):
        monkeypatch.setenv("LIA_EXTENDED_THINKING_BUDGET", "100")
        assert _extended_thinking_budget() == 1024

    def test_budget_default(self, monkeypatch):
        monkeypatch.delenv("LIA_EXTENDED_THINKING_BUDGET", raising=False)
        assert _extended_thinking_budget() == 2000
