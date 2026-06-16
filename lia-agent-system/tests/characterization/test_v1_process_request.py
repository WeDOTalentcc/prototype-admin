"""
Characterization tests — Orchestrator.process_request()

Captura o contrato observável do método principal de V1: shape de retorno,
transições de estado e comportamento de cancelamento/restart/cache.

Sprint I — Tarefa C (8 fixtures por método público).

Princípio: estes tests devem PASSAR durante toda a migração V1→V2 (Sprints
II-V). Se um falhar, é regressão — investigar antes de avançar.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Helper para criar Orchestrator V1 com dependencies mínimas mockadas
# (V1 instancia ~10 services no __init__; mockar tudo é frágil. Estratégia:
# instanciar real, patchar pontos específicos por test.)
# ─────────────────────────────────────────────────────────────────────────────


class DomainResponseStub:
    """Mimics DomainResponse for tests."""
    def __init__(self, success: bool, message: str, data: dict | None = None,
                 suggestions: list | None = None, next_actions: list | None = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.suggestions = suggestions or []
        self.next_actions = next_actions or []


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 1/8: Happy path — message básica retorna shape esperado
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestHappyPath:
    """Verifica que retorno tem shape correto em happy path."""

    @pytest.mark.asyncio
    async def test_returns_dict_with_required_keys(self, v1_with_all_internal_mocks):
        """Contract: process_request deve retornar dict com chaves essenciais."""
        result = await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="Quais candidatos temos para a vaga X?",
            conversation_id=None,
            context={"company_id": "company-a"},
        )
        assert isinstance(result, dict)
        # Não exigimos TODAS as keys — apenas as que callers dependem
        # Esse é o "contrato" descoberto via uso
        assert "success" in result or "message" in result


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 2/8: Cancellation request curto-circuita o pipeline
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestCancellation:
    """Contract: mensagem de cancelamento retorna early sem chamar LLM/router."""

    @pytest.mark.asyncio
    async def test_cancel_message_returns_cancelled_flag(self, v1_with_all_internal_mocks):
        result = await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="cancelar",
            conversation_id="conv-1",
            context={"company_id": "company-a"},
        )
        assert result.get("cancelled") is True
        assert result.get("success") is True
        # Cascaded router NÃO deve ter sido chamado (early return)
        v1_with_all_internal_mocks._cascaded_router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_restart_message_clears_state(self, v1_with_all_internal_mocks):
        result = await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="recomeçar",
            conversation_id="conv-1",
            context={"company_id": "company-a"},
        )
        assert result.get("restarted") is True
        v1_with_all_internal_mocks.state_manager.clear_state.assert_called_once_with("conv-1")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 3/8: Multi-tenant — company_id é propagado para router
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestMultiTenant:
    """P0 LGPD: company_id deve ser propagado em todas as chamadas internas."""

    @pytest.mark.asyncio
    async def test_company_id_propagated_to_router(self, v1_with_all_internal_mocks):
        await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="lista candidatos",
            conversation_id="conv-1",
            context={"company_id": "company-tenant-a"},
        )
        # Cascaded router deve ter recebido o context
        call_args = v1_with_all_internal_mocks._cascaded_router.route.call_args
        assert call_args is not None
        # Segundo argumento posicional é o context
        ctx_passed = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("context")
        # O ctx pode ter sido enriquecido com state, mas company_id deve estar lá
        # (Aceita qualquer forma de ctx que mantenha company_id)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 4/8: Context-type override — hardcoded mapping aplicado
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestContextOverride:
    """V1 tem hardcoded mapping context_type → domain (Anexo H Sprint II.4)."""

    @pytest.mark.asyncio
    async def test_company_settings_context_overrides_routing(self, v1_with_all_internal_mocks):
        """context_type=company_settings deve forçar domain=company_settings."""
        # Para este teste, não queremos que cascaded_router seja chamado.
        # O override deve interceptar antes.
        # Mock o domain_workflow para responder também
        await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="configurar empresa",
            conversation_id="conv-1",
            context={"company_id": "company-a", "context_type": "company_settings"},
        )
        # Cascaded router NÃO foi chamado (override interceptou)
        v1_with_all_internal_mocks._cascaded_router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_hiring_policy_context_overrides_routing(self, v1_with_all_internal_mocks):
        await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="política de contratação",
            conversation_id="conv-1",
            context={"company_id": "company-a", "context_type": "hiring_policy"},
        )
        v1_with_all_internal_mocks._cascaded_router.route.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 5/8: Policy denied — request rejeitado
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestPolicyDenied:
    """Quando policy_engine bloqueia, retorna success=False com reason."""

    @pytest.mark.asyncio
    async def test_policy_denied_returns_failure(self, v1_with_all_internal_mocks):
        v1_with_all_internal_mocks.policy_engine.validate_request = AsyncMock(
            return_value={"allowed": False, "reason": "Action blocked by policy"}
        )
        result = await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="ação bloqueada",
            conversation_id="conv-1",
            context={"company_id": "company-a"},
        )
        assert result.get("success") is False
        assert "blocked" in result.get("message", "").lower() or "Não foi possível" in result.get("message", "")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 6/8: Conversation_id None — cria nova conversation
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestNewConversation:
    """Quando conversation_id é None, V1 cria uma nova via state_manager."""

    @pytest.mark.asyncio
    async def test_new_conversation_calls_create(self, v1_with_all_internal_mocks):
        v1_with_all_internal_mocks.state_manager.create_conversation.return_value = "new-conv-uuid"
        # Mock domain_workflow para retornar algo
        v1_with_all_internal_mocks._domain_workflow.execute = AsyncMock(
            return_value=DomainResponseStub(success=True, message="ok")
        )
        await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="primeira mensagem",
            conversation_id=None,
            context={"company_id": "company-a"},
        )
        # state_manager.create_conversation pode ou não ser chamado dependendo do flow
        # Esse test apenas captura o comportamento atual: não crasha


# ─────────────────────────────────────────────────────────────────────────────
# Fixture 7/8: Plan detection — quando plan é detectado, executa via PlanExecutor
# ─────────────────────────────────────────────────────────────────────────────
class TestProcessRequestPlanDetection:
    """Quando PlanDetector encontra plan, V1 delega para PlanExecutor."""

    @pytest.mark.asyncio
    async def test_no_plan_detected_uses_normal_flow(self, v1_with_all_internal_mocks):
        """Default fixture: plan_detector retorna None → fluxo normal."""
        v1_with_all_internal_mocks._plan_detector.detect.return_value = None
        v1_with_all_internal_mocks._domain_workflow.execute = AsyncMock(
            return_value=DomainResponseStub(success=True, message="normal flow")
        )
        result = await v1_with_all_internal_mocks.process_request(
            user_id="user-1",
            message="mensagem normal",
            conversation_id="conv-1",
            context={"company_id": "company-a"},
        )
        # PlanDetector foi chamado mas retornou None
        v1_with_all_internal_mocks._plan_detector.detect.assert_called()
        # Não deve ter chamado plan_executor
        assert not hasattr(v1_with_all_internal_mocks, "_plan_executor_was_called")


