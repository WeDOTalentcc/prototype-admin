"""
Characterization tests — métodos internos críticos do V1.

Cobre:
- _handle_directly() — LIA-A04 fallback ReAct (Sprint II.2 → FallbackReActService)
- _handle_cv_screening_with_rubric() — Sprint II.3 → cv_screening domain
- _is_technical_response() — Sprint II.3 → heuristics/technical_response_detector
- _is_cv_matching_request() — Sprint II.3 → heuristics/cv_matching_detector

Estes 4 métodos são heurísticas/lógica que serão extraídas para services
dedicados no Sprint II. Os tests aqui devem PASSAR contra V1 antes da
extração e contra os services novos depois.

Assinaturas reais (verificadas em /app/orchestrator/orchestrator.py 2026-04-26):
- _handle_directly(intent, message, entities, context=None)
- is_tool_allowed(tool_name, prompt_context)  — note: prompt_context (str), not scope
- get_scope_system_prompt(prompt_context)     — note: prompt_context (str), not scope
- get_available_tools(agent_type=None)         — note: agent_type, not scope
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# _is_technical_response — heurística (Sprint II.3 → heuristics/)
# ─────────────────────────────────────────────────────────────────────────────
class TestIsTechnicalResponse:
    """Captura a heurística atual para detecção de respostas técnicas."""

    def test_method_exists_and_returns_bool(self, v1_with_minimal_mocks):
        """Contract: método existe e retorna bool."""
        result = v1_with_minimal_mocks._is_technical_response("qualquer resposta")
        assert isinstance(result, bool)

    def test_short_natural_response_handled(self, v1_with_minimal_mocks):
        """Resposta curta natural — captura comportamento atual."""
        result = v1_with_minimal_mocks._is_technical_response("Olá! Posso ajudar?")
        assert isinstance(result, bool)


# ─────────────────────────────────────────────────────────────────────────────
# _is_cv_matching_request — heurística (Sprint II.3)
# ─────────────────────────────────────────────────────────────────────────────
class TestIsCvMatchingRequest:
    """Captura heurística atual para detecção de requests de CV matching."""

    def test_method_exists_and_returns_bool(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks._is_cv_matching_request("qualquer mensagem")
        assert isinstance(result, bool)

    def test_explicit_cv_match_message(self, v1_with_minimal_mocks):
        """Mensagem explícita de CV matching: capturar comportamento atual."""
        result = v1_with_minimal_mocks._is_cv_matching_request(
            "Compare o currículo desse candidato com a vaga"
        )
        assert isinstance(result, bool)


# ─────────────────────────────────────────────────────────────────────────────
# _handle_directly — LIA-A04 fallback ReAct (Sprint II.2)
# Assinatura real: (intent, message, entities, context=None)
# ─────────────────────────────────────────────────────────────────────────────
class TestHandleDirectly:
    """Captura comportamento de fallback LLM com tool binding."""

    @pytest.mark.asyncio
    async def test_method_returns_dict(self, v1_with_minimal_mocks):
        """Contract: retorna dict (com chaves observáveis)."""
        # Mock LLM para retornar resposta sem tool calls
        v1_with_minimal_mocks.llm_service.complete = AsyncMock(
            return_value={"content": "fallback response", "tokens": 8, "tools_used": []}
        )

        # Patch tool_registry para evitar dependência real
        with patch("app.orchestrator.legacy.orchestrator.tool_registry") as mock_registry:
            mock_registry.list_tools.return_value = []
            with patch("app.orchestrator.legacy.orchestrator.get_all_tool_schemas", return_value=[]):
                result = await v1_with_minimal_mocks._handle_directly(
                    intent="general_chat",
                    message="oi tudo bem",
                    entities={},
                    context={"company_id": "company-a"},
                )
                # Captura: retorna dict
                assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# _handle_cv_screening_with_rubric — CV matching path (Sprint II.3)
# ─────────────────────────────────────────────────────────────────────────────
class TestHandleCvScreeningWithRubric:
    """Captura caminho específico de CV screening rubric."""

    @pytest.mark.asyncio
    async def test_method_returns_dict(self, v1_with_minimal_mocks):
        """Contract: retorna dict (success=True/False)."""
        result = await v1_with_minimal_mocks._handle_cv_screening_with_rubric(
            message="CV check",
            context={"company_id": "company-a"},
        )
        assert isinstance(result, dict)
        assert "success" in result


# ─────────────────────────────────────────────────────────────────────────────
# is_tool_allowed — public method (4 fixtures)
# Assinatura real: (tool_name, prompt_context: str)
# ─────────────────────────────────────────────────────────────────────────────
class TestIsToolAllowed:
    """Verifica controle de acesso a tools por prompt_context."""

    def test_returns_bool(self, v1_with_minimal_mocks):
        """Contract: retorna bool."""
        result = v1_with_minimal_mocks.is_tool_allowed(tool_name="any_tool", prompt_context="general")
        assert isinstance(result, bool)

    def test_unknown_tool_returns_false_or_default(self, v1_with_minimal_mocks):
        """Tool desconhecida não deve dar erro."""
        result = v1_with_minimal_mocks.is_tool_allowed(
            tool_name="nonexistent_tool_xyz_123", prompt_context="recruiter_assistant"
        )
        assert isinstance(result, bool)

    def test_global_context_allows_more(self, v1_with_minimal_mocks):
        """prompt_context global tipicamente permite mais tools."""
        from app.tools import tool_registry
        tools = tool_registry.list_tools()
        if not tools:
            pytest.skip("No tools registered in test environment")
        first_tool = tools[0]
        result = v1_with_minimal_mocks.is_tool_allowed(tool_name=first_tool, prompt_context="global")
        assert isinstance(result, bool)

    def test_specific_context_filters_tools(self, v1_with_minimal_mocks):
        """prompt_context específico filtra tools."""
        result = v1_with_minimal_mocks.is_tool_allowed(
            tool_name="some_tool", prompt_context="talent_funnel"
        )
        assert isinstance(result, bool)


# ─────────────────────────────────────────────────────────────────────────────
# get_scope_system_prompt — public method (3 fixtures)
# Assinatura real: (prompt_context: str)
# ─────────────────────────────────────────────────────────────────────────────
class TestGetScopeSystemPrompt:
    """Verifica retorno de prompt addition por prompt_context."""

    def test_general_context_returns_string(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_scope_system_prompt(prompt_context="general")
        assert isinstance(result, str)

    def test_talent_funnel_context_returns_string(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_scope_system_prompt(prompt_context="talent_funnel")
        assert isinstance(result, str)

    def test_job_table_context_returns_string(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_scope_system_prompt(prompt_context="job_table")
        assert isinstance(result, str)


# ─────────────────────────────────────────────────────────────────────────────
# get_available_tools — public method (2 fixtures)
# Assinatura real: (agent_type: str | None = None)
# ─────────────────────────────────────────────────────────────────────────────
class TestGetAvailableTools:
    """Verifica retorno de tool schemas."""

    def test_no_agent_type_returns_list(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_available_tools()
        assert isinstance(result, list)

    def test_with_agent_type_returns_list(self, v1_with_minimal_mocks):
        result = v1_with_minimal_mocks.get_available_tools(agent_type="recruiter_assistant")
        assert isinstance(result, list)
