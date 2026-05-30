"""
Unit tests for FallbackReActService — Sprint II.2 of LIA-D06 migration.

Tests cobrem:
- Construção de system prompt com structured addenda (C-05/C-06)
- Conversation history injection (max 10 turns)
- Tool binding controlado por env var LIA_FALLBACK_BIND_TOOLS
- Response shape compatível com V1._handle_directly
- Graceful error handling (success=True mesmo em exception)
- Multi-tenant: tenant_context_snippet propagado ao SystemPromptBuilder

Reference: ADR-019 — Sprint II.2
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

@pytest.fixture(autouse=True)
def _isolate_from_tenant_strict_mode(monkeypatch):
    """Unit isolation (canonical-fix): o producer resolve_tenant_snippet_for_non_react
    fail-closes em strict-mode sem tenant_context_snippet (hardening T-F).
    Estes testes exercitam a invocação LLM / addenda / shape — NÃO a
    resolução de tenant, que é coberta (a) no producer tenant_aware_agent e
    (b) no teste test_tenant_context_snippet_passed_to_builder (provê snippet
    explícito). Desliga strict-mode só nesta camada de teste."""
    monkeypatch.setattr(
        "app.shared.agents.tenant_aware_agent.is_tenant_strict_mode",
        lambda: False,
    )


from app.orchestrator.services.fallback_react_service import (
    AGENT_TYPE_LABEL,
    AGENT_USED_LABEL,
    MAX_HISTORY_MESSAGES,
    STRUCTURED_INTENT_ADDENDA,
    TOOL_BIND_ENV_VAR,
    FallbackReActService,
    _is_tool_binding_enabled,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build mock LLM that returns predictable response
# ─────────────────────────────────────────────────────────────────────────────


def _make_mock_llm_service(
    response_content: str = "fallback response",
    tool_calls: list | None = None,
) -> MagicMock:
    """Cria mock LLM service com método get_audited_model."""
    # Build response object (LangChain BaseMessage-like)
    response = MagicMock()
    response.content = response_content
    response.tool_calls = tool_calls or []

    # LLM model mock — supports prompt | llm chaining and ainvoke
    model = MagicMock()
    model.bind_tools = MagicMock(return_value=model)

    # Chain mock — pretende ser `prompt | llm`. Devolve `response` em ainvoke.
    chain = MagicMock()
    chain.ainvoke = AsyncMock(return_value=response)

    # __ror__ é o que o `prompt | llm` aciona — mas só chamamos via ChatPromptTemplate
    # Mais simples: patchar ChatPromptTemplate.from_messages para retornar prompt cujo
    # __or__ retorna chain mock.
    model.__or__ = MagicMock(return_value=chain)

    # service mock
    service = MagicMock()
    service.get_audited_model = MagicMock(return_value=model)
    return service


# ─────────────────────────────────────────────────────────────────────────────
# Constants tests
# ─────────────────────────────────────────────────────────────────────────────


class TestConstants:
    """Constantes canônicas estáveis."""

    def test_structured_addenda_has_cv_screening(self):
        assert "cv_screening" in STRUCTURED_INTENT_ADDENDA
        # C-05: deve mencionar match_score
        assert "match_score" in STRUCTURED_INTENT_ADDENDA["cv_screening"]

    def test_structured_addenda_has_salary_benchmark(self):
        assert "salary_benchmark" in STRUCTURED_INTENT_ADDENDA
        # C-06: deve mencionar formato salarial
        assert "R$" in STRUCTURED_INTENT_ADDENDA["salary_benchmark"]

    def test_max_history_is_10(self):
        """V1 hard-coded em 10 — não mudar sem coordenação."""
        assert MAX_HISTORY_MESSAGES == 10

    def test_agent_labels(self):
        """Labels visíveis ao usuário — não mudar sem UX review."""
        assert AGENT_USED_LABEL == "LIA Orchestrator"
        assert AGENT_TYPE_LABEL == "orchestrator"

    def test_env_var_name(self):
        assert TOOL_BIND_ENV_VAR == "LIA_FALLBACK_BIND_TOOLS"


# ─────────────────────────────────────────────────────────────────────────────
# _is_tool_binding_enabled — env var parsing
# ─────────────────────────────────────────────────────────────────────────────


class TestToolBindingEnvVar:
    """Parsing do env var LIA_FALLBACK_BIND_TOOLS."""

    def test_default_is_true_when_unset(self, monkeypatch):
        monkeypatch.delenv(TOOL_BIND_ENV_VAR, raising=False)
        assert _is_tool_binding_enabled() is True

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "YES"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, value)
        assert _is_tool_binding_enabled() is True

    @pytest.mark.parametrize("value", ["false", "False", "0", "no", "off", "anything_else"])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, value)
        assert _is_tool_binding_enabled() is False


# ─────────────────────────────────────────────────────────────────────────────
# FallbackReActService — initialization
# ─────────────────────────────────────────────────────────────────────────────


class TestFallbackReActServiceInit:
    """Construção do service."""

    def test_init_with_default_addenda(self):
        llm = _make_mock_llm_service()
        service = FallbackReActService(llm_service=llm)
        # Default usa STRUCTURED_INTENT_ADDENDA canônico
        assert service._structured_addenda is STRUCTURED_INTENT_ADDENDA

    def test_init_with_custom_addenda(self):
        custom = {"my_intent": "my addendum"}
        service = FallbackReActService(
            llm_service=_make_mock_llm_service(), structured_addenda=custom
        )
        assert service._structured_addenda is custom


# ─────────────────────────────────────────────────────────────────────────────
# FallbackReActService.handle_directly — success path
# ─────────────────────────────────────────────────────────────────────────────


class TestHandleDirectlySuccess:
    """Happy path: LLM responde, response shape correto."""

    @pytest.mark.asyncio
    async def test_returns_dict_with_required_keys(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")  # skip tool binding
        llm = _make_mock_llm_service(response_content="ok")
        service = FallbackReActService(llm_service=llm)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="system prompt",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_response = MagicMock()
                mock_response.content = "ok"
                mock_response.tool_calls = []
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                result = await service.handle_directly(
                    intent="general_chat",
                    message="hello",
                    entities={},
                    context={"company_id": "tenant-a"},
                )

        # Required keys
        assert result["message"] == "ok"
        assert result["success"] is True
        assert result["requires_user_input"] is True
        assert result["suggested_prompts"] == []
        assert result["next_actions"] == []
        assert result["agent_used"] == AGENT_USED_LABEL
        assert result["agent_type"] == AGENT_TYPE_LABEL
        assert "data" in result

    @pytest.mark.asyncio
    async def test_extracts_tool_calls_from_response(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        service = FallbackReActService(llm_service=_make_mock_llm_service())

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="prompt",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_response = MagicMock()
                mock_response.content = "I will call tools"
                mock_response.tool_calls = [
                    {"name": "search_candidates"},
                    {"name": "rank_candidates"},
                ]
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)
                mock_prompt = MagicMock()
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                result = await service.handle_directly(
                    intent="x", message="m", entities={}, context={}
                )

        assert result["data"]["tool_calls_requested"] == [
            "search_candidates",
            "rank_candidates",
        ]

    @pytest.mark.asyncio
    async def test_response_content_none_falls_back_to_str(self, monkeypatch):
        """P1 fix: response.content None nao gera message=None."""
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        service = FallbackReActService(llm_service=_make_mock_llm_service())

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="prompt",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_response = MagicMock()
                mock_response.content = None  # P1 edge case
                mock_response.tool_calls = []
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)
                mock_prompt = MagicMock()
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                result = await service.handle_directly(
                    intent="x", message="m", entities={}, context={}
                )

        # Message NAO eh None — fallback para str(response)
        assert result["message"] is not None
        assert isinstance(result["message"], str)

    @pytest.mark.asyncio
    async def test_tool_calls_filters_empty_names(self, monkeypatch):
        """P1 fix: empty/None tool names sao filtrados (nao adicionados a lista)."""
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        service = FallbackReActService(llm_service=_make_mock_llm_service())

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="prompt",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_response = MagicMock()
                mock_response.content = "result"
                # Mix: nome valido, nome vazio, nome None
                mock_response.tool_calls = [
                    {"name": "valid_tool"},
                    {"name": ""},
                    {"name": None},
                    {},  # sem name
                ]
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(return_value=mock_response)
                mock_prompt = MagicMock()
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                result = await service.handle_directly(
                    intent="x", message="m", entities={}, context={}
                )

        # Apenas o tool valido aparece — empty/None filtrados
        assert result["data"]["tool_calls_requested"] == ["valid_tool"]

    @pytest.mark.asyncio
    async def test_cancelled_error_propagates(self, monkeypatch):
        """P1 fix: asyncio.CancelledError nao eh capturada — propaga para caller."""
        import asyncio as _asyncio

        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        llm_svc = MagicMock()
        llm_svc.get_audited_model = MagicMock(side_effect=_asyncio.CancelledError())
        service = FallbackReActService(llm_service=llm_svc)

        with pytest.raises(_asyncio.CancelledError):
            await service.handle_directly(
                intent="x", message="m", entities={}, context={}
            )


# ─────────────────────────────────────────────────────────────────────────────
# FallbackReActService — error handling
# ─────────────────────────────────────────────────────────────────────────────


class TestHandleDirectlyErrorHandling:
    """Em erro, retorna resposta amigável com success=True."""

    @pytest.mark.asyncio
    async def test_exception_returns_friendly_response(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        # LLM service que sempre crasha em get_audited_model
        llm = MagicMock()
        llm.get_audited_model = MagicMock(side_effect=RuntimeError("LLM unavailable"))
        service = FallbackReActService(llm_service=llm)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build_error_response",
            return_value="Desculpe, tive um problema. Tente novamente.",
        ):
            result = await service.handle_directly(
                intent="x", message="m", entities={}, context={"user_name": "Paulo"}
            )

        # P1: success=True mesmo em erro (UX friendly degradation)
        assert result["success"] is True
        assert "Desculpe" in result["message"]
        assert result["agent_used"] == AGENT_USED_LABEL

    @pytest.mark.asyncio
    async def test_error_response_uses_user_name_from_context(self):
        llm = MagicMock()
        llm.get_audited_model = MagicMock(side_effect=Exception("any"))
        service = FallbackReActService(llm_service=llm)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build_error_response"
        ) as mock_err:
            mock_err.return_value = "err"
            await service.handle_directly(
                intent="x", message="m", entities={}, context={"user_name": "Maria"}
            )
            # build_error_response chamado com user_name="Maria"
            mock_err.assert_called_once_with(user_name="Maria")


# ─────────────────────────────────────────────────────────────────────────────
# Tool binding integration
# ─────────────────────────────────────────────────────────────────────────────


class TestToolBindingIntegration:
    """Verifica que tool binding respeita env var."""

    @pytest.mark.asyncio
    async def test_tool_binding_disabled_does_not_bind(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")

        llm_model = MagicMock()
        llm_model.bind_tools = MagicMock()
        chain = MagicMock()
        chain.ainvoke = AsyncMock(return_value=MagicMock(content="ok", tool_calls=[]))
        llm_model.__or__ = MagicMock(return_value=chain)

        llm_svc = MagicMock()
        llm_svc.get_audited_model = MagicMock(return_value=llm_model)

        service = FallbackReActService(llm_service=llm_svc)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ):
            with patch("langchain_core.prompts.ChatPromptTemplate.from_messages"):
                await service.handle_directly(
                    intent="x", message="m", entities={}, context={}
                )

        llm_model.bind_tools.assert_not_called()

    @pytest.mark.asyncio
    async def test_tool_binding_failure_continues_gracefully(self, monkeypatch):
        """Se bind_tools falha, log warning + continua sem tools."""
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "true")

        llm_model = MagicMock()
        llm_model.bind_tools = MagicMock(side_effect=Exception("bind fail"))
        chain = MagicMock()
        chain.ainvoke = AsyncMock(return_value=MagicMock(content="ok", tool_calls=[]))
        llm_model.__or__ = MagicMock(return_value=chain)

        llm_svc = MagicMock()
        llm_svc.get_audited_model = MagicMock(return_value=llm_model)
        service = FallbackReActService(llm_service=llm_svc)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ):
            with patch("langchain_core.prompts.ChatPromptTemplate.from_messages"):
                with patch("app.tools.get_all_tool_schemas", return_value=[{"a": 1}]):
                    result = await service.handle_directly(
                        intent="x", message="m", entities={}, context={}
                    )

        # Result still success despite bind_tools fail
        assert result["success"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Conversation history injection
# ─────────────────────────────────────────────────────────────────────────────


class TestConversationHistoryInjection:
    """Histórico last 10 mensagens injetado como turns reais."""

    @pytest.mark.asyncio
    async def test_history_truncated_to_max(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        llm = _make_mock_llm_service()
        service = FallbackReActService(llm_service=llm)

        # Build 15 mensagens (deve usar só últimas 10)
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(15)
        ]

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                await service.handle_directly(
                    intent="x",
                    message="latest",
                    entities={},
                    context={"conversation_history": history},
                )

                # Inspect args passed to from_messages
                call_args = mock_tpl.call_args
                messages_passed = call_args.args[0]
                # 1 system + last 10 history + 1 final human = 12
                assert len(messages_passed) == 12

    @pytest.mark.asyncio
    async def test_history_invalid_items_skipped(self, monkeypatch):
        """Items que não são dict são skipados (defensive)."""
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        llm = _make_mock_llm_service()
        service = FallbackReActService(llm_service=llm)

        history = [
            {"role": "user", "content": "valid"},
            "invalid string",  # não é dict
            None,  # None
            {"role": "assistant", "content": "valid"},
        ]

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ):
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                # Should not crash
                result = await service.handle_directly(
                    intent="x",
                    message="m",
                    entities={},
                    context={"conversation_history": history},
                )

        assert result["success"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Multi-tenant context propagation
# ─────────────────────────────────────────────────────────────────────────────


class TestMultiTenantPropagation:
    """P0 LGPD: tenant_context_snippet propagado ao prompt builder."""

    @pytest.mark.asyncio
    async def test_tenant_context_snippet_passed_to_builder(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        llm = _make_mock_llm_service()
        service = FallbackReActService(llm_service=llm)

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ) as mock_build:
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                await service.handle_directly(
                    intent="general_chat",
                    message="hi",
                    entities={"job_id": "j1"},
                    context={
                        "tenant_context_snippet": "Empresa: Acme Inc.",
                        "user_name": "Paulo",
                        "user_role": "recruiter",
                        "company_id": "acme",
                    },
                )

        # build called with tenant_context_snippet
        kwargs = mock_build.call_args.kwargs
        assert kwargs["tenant_context_snippet"] == "Empresa: Acme Inc."
        assert kwargs["user_name"] == "Paulo"
        assert kwargs["user_role"] == "recruiter"
        assert kwargs["entities"] == {"job_id": "j1"}


# ─────────────────────────────────────────────────────────────────────────────
# Structured addenda per intent
# ─────────────────────────────────────────────────────────────────────────────


class TestStructuredAddenda:
    """Addenda C-05/C-06 injetadas conforme intent."""

    @pytest.mark.asyncio
    async def test_cv_screening_intent_uses_c05_addendum(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        service = FallbackReActService(llm_service=_make_mock_llm_service())

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ) as mock_build:
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                await service.handle_directly(
                    intent="cv_screening", message="m", entities={}, context={}
                )

        kwargs = mock_build.call_args.kwargs
        assert "match_score" in kwargs["extra_instructions"]

    @pytest.mark.asyncio
    async def test_unknown_intent_no_addendum(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        service = FallbackReActService(llm_service=_make_mock_llm_service())

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ) as mock_build:
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                await service.handle_directly(
                    intent="unknown_xyz", message="m", entities={}, context={}
                )

        kwargs = mock_build.call_args.kwargs
        assert kwargs["extra_instructions"] == ""

    @pytest.mark.asyncio
    async def test_custom_addenda_overrides_default(self, monkeypatch):
        monkeypatch.setenv(TOOL_BIND_ENV_VAR, "false")
        custom = {"my_intent": "custom rule"}
        service = FallbackReActService(
            llm_service=_make_mock_llm_service(), structured_addenda=custom
        )

        with patch(
            "app.orchestrator.services.fallback_react_service.SystemPromptBuilder.build",
            return_value="p",
        ) as mock_build:
            with patch(
                "langchain_core.prompts.ChatPromptTemplate.from_messages"
            ) as mock_tpl:
                mock_prompt = MagicMock()
                mock_chain = MagicMock()
                mock_chain.ainvoke = AsyncMock(
                    return_value=MagicMock(content="ok", tool_calls=[])
                )
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)
                mock_tpl.return_value = mock_prompt

                await service.handle_directly(
                    intent="my_intent", message="m", entities={}, context={}
                )

        kwargs = mock_build.call_args.kwargs
        assert kwargs["extra_instructions"] == "custom rule"
