"""
W7.1 — PII strip antes do router LLM cascade.

Verifica que LLMCascadeRouter._call_model() strip PII do user message
ANTES de interpolar no routing prompt — cobrindo Gemini (não coberto pelo bootstrap Anthropic).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PII_MODULE = "app.shared.pii_masking"


class TestLLMCascadePIIStrip:
    """W7.1: user message deve ter PII stripada antes de ser enviada ao LLM de roteamento."""

    @pytest.mark.asyncio
    async def test_cpf_stripped_from_routing_prompt(self):
        """CPF no user message deve ser substituído antes do LLM call."""
        from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

        router = LLMCascadeRouter()
        captured_prompts: list[str] = []

        async def _fake_generate(prompt: str, **kwargs) -> str:
            captured_prompts.append(prompt)
            return '{"domain": "cv_screening", "confidence": 0.9, "reason": "test"}'

        with (
            patch(
                "app.orchestrator.routing.llm_cascade.llm_service.generate",
                side_effect=_fake_generate,
            ),
            patch(
                f"{_PII_MODULE}.strip_pii_for_llm_prompt",
                side_effect=lambda t: t.replace("123.456.789-00", "[CPF]"),
            ),
        ):
            msg_with_pii = "Candidato João Silva, CPF 123.456.789-00, aprovado na triagem?"
            result, _ = await router._call_model(msg_with_pii, "claude-haiku-4-5")

        assert captured_prompts, "LLM was not called"
        routing_prompt = captured_prompts[0]
        assert "123.456.789-00" not in routing_prompt, "CPF reached LLM — PII strip failed"
        assert "[CPF]" in routing_prompt or "123.456.789-00" not in routing_prompt

    @pytest.mark.asyncio
    async def test_email_stripped_from_routing_prompt(self):
        """Email no user message deve ser substituído antes do LLM call."""
        from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

        router = LLMCascadeRouter()
        captured_prompts: list[str] = []

        async def _fake_generate(prompt: str, **kwargs) -> str:
            captured_prompts.append(prompt)
            return '{"domain": "recruiter_assistant", "confidence": 0.85, "reason": "test"}'

        with (
            patch(
                "app.orchestrator.routing.llm_cascade.llm_service.generate",
                side_effect=_fake_generate,
            ),
            patch(
                f"{_PII_MODULE}.strip_pii_for_llm_prompt",
                side_effect=lambda t: t.replace("joao@empresa.com", "[EMAIL]"),
            ),
        ):
            result, _ = await router._call_model(
                "Status do candidato joao@empresa.com?", "claude-haiku-4-5"
            )

        assert captured_prompts
        assert "joao@empresa.com" not in captured_prompts[0]

    @pytest.mark.asyncio
    async def test_pii_strip_failure_falls_back_to_original(self):
        """Se strip_pii_for_llm_prompt levantar exceção, deve fazer fail-open e continuar."""
        from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

        router = LLMCascadeRouter()
        called = []

        async def _fake_generate(prompt: str, **kwargs) -> str:
            called.append(prompt)
            return '{"domain": "recruiter_assistant", "confidence": 0.9, "reason": "ok"}'

        with (
            patch(
                "app.orchestrator.routing.llm_cascade.llm_service.generate",
                side_effect=_fake_generate,
            ),
            patch(
                f"{_PII_MODULE}.strip_pii_for_llm_prompt",
                side_effect=RuntimeError("PII module down"),
            ),
        ):
            # Should NOT raise — fail-open behavior
            result, tokens = await router._call_model("mensagem segura", "claude-haiku-4-5")

        assert result is not None
        assert called  # LLM was still called despite PII module error

    @pytest.mark.asyncio
    async def test_safe_message_passes_through_unchanged(self):
        """Mensagem sem PII deve ser enviada ao LLM sem modificação."""
        from app.orchestrator.routing.llm_cascade import LLMCascadeRouter

        router = LLMCascadeRouter()
        captured: list[str] = []

        async def _fake_generate(prompt: str, **kwargs) -> str:
            captured.append(prompt)
            return '{"domain": "sourcing", "confidence": 0.92, "reason": "ok"}'

        safe_msg = "Quero ver candidatos para a vaga de Engenheiro de Software"

        with (
            patch(
                "app.orchestrator.routing.llm_cascade.llm_service.generate",
                side_effect=_fake_generate,
            ),
            patch(
                f"{_PII_MODULE}.strip_pii_for_llm_prompt",
                side_effect=lambda t: t,  # identity — no PII to strip
            ),
        ):
            result, tokens = await router._call_model(safe_msg, "claude-haiku-4-5")

        assert captured
        assert safe_msg[:50] in captured[0]  # message present (possibly truncated)
        assert result is not None
