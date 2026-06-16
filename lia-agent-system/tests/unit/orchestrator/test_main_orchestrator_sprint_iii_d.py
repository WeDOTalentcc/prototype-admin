"""
Sprint III.D tests — _try_fallback_react_substitute + LIA_V2_USE_FALLBACK_REACT.

Garante:
- Flag default OFF
- Quando V1 retorna technical → service substitui (se ON + injected)
- Quando V1 retorna não-technical → mantém V1
- Service exception → mantém V1 (graceful)
- Service injetado None → mantém V1 (sem chamar)

Reference: ADR-019 — Sprint III.D
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator.execution.main_orchestrator import (
    MainOrchestrator,
    _is_fallback_react_enabled,
)


# ─────────────────────────────────────────────────────────────────────────────
# Feature flag tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFeatureFlagFallbackReact:
    """LIA_V2_USE_FALLBACK_REACT env var parsing."""

    def test_default_is_false(self, monkeypatch):
        monkeypatch.delenv("LIA_V2_USE_FALLBACK_REACT", raising=False)
        assert _is_fallback_react_enabled() is False

    @pytest.mark.parametrize("value", ["true", "True", "1", "yes"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_V2_USE_FALLBACK_REACT", value)
        assert _is_fallback_react_enabled() is True

    @pytest.mark.parametrize("value", ["false", "0", "no", ""])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_V2_USE_FALLBACK_REACT", value)
        assert _is_fallback_react_enabled() is False


# ─────────────────────────────────────────────────────────────────────────────
# _try_fallback_react_substitute tests
# ─────────────────────────────────────────────────────────────────────────────


def _make_v1_orchestrator():
    v1 = MagicMock()
    v1.process_request = AsyncMock()
    v1.llm_service = MagicMock()
    return v1


def _make_ctx():
    ctx = MagicMock()
    ctx.message = "qualquer mensagem"
    ctx.company_id = "tenant-a"
    return ctx


class TestTryFallbackReactSubstitute:
    """Late-intercept logic — V1 result inspection + substitution."""

    @pytest.mark.asyncio
    async def test_non_technical_response_preserved(self):
        """V1 retorna resposta natural → service NÃO é chamado."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock()

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {
            "success": True,
            "message": "Olá! Como posso ajudar?",  # natural, não-técnica
            "intent": "general_chat",
            "result": {"data": {}},
        }

        result = await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        # V1 result preservado
        assert result is v1_result
        assert result["message"] == "Olá! Como posso ajudar?"
        # Service NÃO foi chamado
        fb_svc.handle_directly.assert_not_called()

    @pytest.mark.asyncio
    async def test_technical_response_substituted(self):
        """V1 retorna 'Processado com sucesso.' → service substitui."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock(
            return_value={
                "success": True,
                "message": "Resposta natural do fallback service",
                "agent_used": "LIA Orchestrator",
                "agent_type": "orchestrator",
                "data": {"tool_calls_requested": []},
            }
        )

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {
            "success": True,
            "message": "Processado com sucesso.",  # TECHNICAL
            "intent": "candidate_search",
            "result": {"data": {"entities": {"candidate_id": "c1"}}},
            "conversation_id": "conv-1",
        }

        result = await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        # Mensagem substituída
        assert result["message"] == "Resposta natural do fallback service"
        # Marker para audit
        assert result["_fallback_substituted"] is True
        # Metadata V1 preservada (intent, conversation_id)
        assert result["intent"] == "candidate_search"
        assert result["conversation_id"] == "conv-1"
        # Service foi chamado com intent + entities corretos
        fb_svc.handle_directly.assert_called_once()
        call_kwargs = fb_svc.handle_directly.call_args.kwargs
        assert call_kwargs["intent"] == "candidate_search"
        assert call_kwargs["entities"] == {"candidate_id": "c1"}

    @pytest.mark.asyncio
    async def test_service_exception_preserves_v1_result(self):
        """P1 graceful: any exception preserva V1 result."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock(side_effect=RuntimeError("LLM down"))

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {
            "success": True,
            "message": "Processado com sucesso.",  # technical
            "intent": "x",
            "result": {"data": {}},
        }

        result = await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        # V1 result preservado mesmo com exception no service
        assert result["message"] == "Processado com sucesso."
        assert "_fallback_substituted" not in result

    @pytest.mark.asyncio
    async def test_service_returns_failure_preserves_v1(self):
        """Se service retorna success=False → mantém V1."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock(
            return_value={"success": False, "message": "fallback errored"}
        )

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {
            "success": True,
            "message": "Processado com sucesso.",
            "intent": "x",
            "result": {"data": {}},
        }

        result = await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        # V1 preservado
        assert result["message"] == "Processado com sucesso."
        assert "_fallback_substituted" not in result

    @pytest.mark.asyncio
    async def test_empty_message_treated_as_non_technical(self):
        """Mensagem vazia não é technical → service não chamado."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock()

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {"success": True, "message": "", "intent": "x"}

        result = await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        # is_technical_response("") → False → não substitui
        assert result is v1_result
        fb_svc.handle_directly.assert_not_called()

    @pytest.mark.asyncio
    async def test_intent_default_general_chat_when_missing(self):
        """Quando V1 não retorna intent → service usa 'general_chat'."""
        fb_svc = MagicMock()
        fb_svc.handle_directly = AsyncMock(
            return_value={"success": True, "message": "ok"}
        )

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(),
            fallback_react_service=fb_svc,
        )

        v1_result = {
            "success": True,
            "message": "Processado com sucesso.",  # technical
            # intent ausente!
        }

        await v2._try_fallback_react_substitute(
            v1_result, _make_ctx(), {"company_id": "t1"}
        )

        kwargs = fb_svc.handle_directly.call_args.kwargs
        assert kwargs["intent"] == "general_chat"
