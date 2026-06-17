"""
Testes unitários para AuditCallback.on_llm_call — Sprint H1.

Cobertura:
- campos prompt_full e reasoning_full são persistidos sem truncamento
- campos prompt_preview e response_preview mantêm truncamento em 500 chars
- backward compat: chamada sem prompt_full/reasoning_full continua funcionando
- entry não inclui chaves full quando não fornecidas (sem None no dict)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_callback():
    """Instancia AuditCallback com mocks mínimos."""
    from lia_audit.audit_callback import AuditCallback

    cb = AuditCallback(
        user_id="test-user",
        company_id="test-company",
        session_id="test-session",
        domain="test",
        agent_type="react",
    )
    return cb


class TestOnLlmCallBackwardCompat:
    """Garantia de backward compat: chamadas sem os novos campos."""

    def test_basic_call_without_full_fields(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="prompt curto",
            response_preview="resposta curta",
            latency_ms=123.0,
            model="claude-sonnet",
        )
        assert len(cb.entries) == 1
        entry = cb.entries[0]
        assert entry["type"] == "llm_call"
        assert entry["prompt_preview"] == "prompt curto"
        assert entry["response_preview"] == "resposta curta"
        assert entry["latency_ms"] == 123.0
        assert entry["model"] == "claude-sonnet"

    def test_full_fields_absent_when_not_provided(self):
        """Sem prompt_full/reasoning_full fornecidos, chaves não devem existir no entry."""
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="x",
            response_preview="y",
            latency_ms=1.0,
        )
        entry = cb.entries[0]
        assert "prompt_full" not in entry
        assert "reasoning_full" not in entry


class TestOnLlmCallFullContent:
    """Novos campos prompt_full e reasoning_full — Sprint H1."""

    def test_prompt_full_persisted_without_truncation(self):
        cb = _make_callback()
        long_prompt = "A" * 2000
        cb.on_llm_call(
            prompt_preview=long_prompt[:500],
            response_preview="resposta",
            latency_ms=50.0,
            prompt_full=long_prompt,
        )
        entry = cb.entries[0]
        assert entry["prompt_full"] == long_prompt
        assert len(entry["prompt_full"]) == 2000

    def test_reasoning_full_persisted_without_truncation(self):
        cb = _make_callback()
        long_reasoning = "R" * 3000
        cb.on_llm_call(
            prompt_preview="prompt",
            response_preview=long_reasoning[:500],
            latency_ms=50.0,
            reasoning_full=long_reasoning,
        )
        entry = cb.entries[0]
        assert entry["reasoning_full"] == long_reasoning
        assert len(entry["reasoning_full"]) == 3000

    def test_both_full_fields_together(self):
        cb = _make_callback()
        long_prompt = "P" * 1500
        long_reasoning = "R" * 2500
        cb.on_llm_call(
            prompt_preview=long_prompt[:500],
            response_preview=long_reasoning[:500],
            latency_ms=80.0,
            model="claude-haiku",
            prompt_full=long_prompt,
            reasoning_full=long_reasoning,
        )
        entry = cb.entries[0]
        assert entry["prompt_full"] == long_prompt
        assert entry["reasoning_full"] == long_reasoning
        # Preview continua truncado
        assert len(entry["prompt_preview"]) == 500
        assert len(entry["response_preview"]) == 500

    def test_preview_still_truncated_at_500(self):
        """Preview deve continuar truncado em 500 mesmo quando full é fornecido."""
        cb = _make_callback()
        long_text = "X" * 1000
        cb.on_llm_call(
            prompt_preview=long_text,
            response_preview=long_text,
            latency_ms=10.0,
            prompt_full=long_text,
            reasoning_full=long_text,
        )
        entry = cb.entries[0]
        assert len(entry["prompt_preview"]) == 500
        assert len(entry["response_preview"]) == 500
        assert len(entry["prompt_full"]) == 1000
        assert len(entry["reasoning_full"]) == 1000

    def test_only_reasoning_full_provided(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="prompt",
            response_preview="resposta",
            latency_ms=10.0,
            reasoning_full="raciocínio completo",
        )
        entry = cb.entries[0]
        assert "prompt_full" not in entry
        assert entry["reasoning_full"] == "raciocínio completo"

    def test_only_prompt_full_provided(self):
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="prompt",
            response_preview="resposta",
            latency_ms=10.0,
            prompt_full="prompt completo",
        )
        entry = cb.entries[0]
        assert entry["prompt_full"] == "prompt completo"
        assert "reasoning_full" not in entry

    def test_multiple_calls_accumulate_entries(self):
        cb = _make_callback()
        for i in range(3):
            cb.on_llm_call(
                prompt_preview=f"prompt {i}",
                response_preview=f"resposta {i}",
                latency_ms=float(i * 10),
                prompt_full=f"prompt completo {i}",
                reasoning_full=f"raciocínio completo {i}",
            )
        assert len(cb.entries) == 3
        for i, entry in enumerate(cb.entries):
            assert entry["prompt_full"] == f"prompt completo {i}"
            assert entry["reasoning_full"] == f"raciocínio completo {i}"

    def test_entry_structure_complete(self):
        """Entry deve ter todas as chaves esperadas."""
        cb = _make_callback()
        cb.on_llm_call(
            prompt_preview="preview",
            response_preview="response",
            latency_ms=42.5,
            model="claude-sonnet",
            tokens_total=1500,
            prompt_full="prompt full",
            reasoning_full="reasoning full",
        )
        entry = cb.entries[0]
        assert entry["type"] == "llm_call"
        assert "timestamp" in entry
        assert entry["model"] == "claude-sonnet"
        assert entry["tokens_total"] == 1500
        assert entry["latency_ms"] == 42.5
        assert entry["prompt_full"] == "prompt full"
        assert entry["reasoning_full"] == "reasoning full"
