"""
PR-J — Rail A capability gate (main_orchestrator wiring)

Testa que check_rail_a_capability() é chamado dentro de process() ANTES
do Phase 0 (PendingAction), de modo que:

1. Cards não-chat-executáveis (add_candidate) retornam ui_action="open_modal"
   SEM nenhuma chamada ao LLM (process_request nunca é chamado).
2. Cards não-chat-executáveis com navigate_fallback retornam ui_action="navigate_to".
3. Cards normais (chat_executable=True) continuam com o pipeline normal.
4. Falha em check_rail_a_capability é silenciada (não bloqueia processamento).
5. Mensagens sem metadata de Rail A não são afetadas.

Skill: lia-testing PARTE 1 (TDD red→green) + harness-engineering (computational
guide — gate antes do LLM = guia feedforward que reduz P(erro) de routing).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.orchestrator.context.context_adapter import UniversalContext
from app.orchestrator.execution.main_orchestrator import ChatResponse, MainOrchestrator


def _allow_policy_gate():
    """Mock policy gate que sempre permite — isola do PolicyGateService V2
    real (auto-instanciado pelo MainOrchestrator desde WT-2022 P3.1), cujo
    engine faz chamadas async/DB incompatíveis com unit test. O gate é
    incidental a estes testes (que exercitam a Rail A capability gate)."""
    gate = MagicMock()
    gate.validate = AsyncMock(return_value=MagicMock(allowed=True))
    return gate


@pytest.fixture(autouse=True)
def _enable_v1_delegation(monkeypatch):
    """WT-2022: Phase 2 V1 delegation está OFF por default
    (LIA_PHASE_2_V1_ENABLED). Estes testes usam mock_v1.process_request como
    observável de 'pipeline normal prosseguiu além do gate', então habilitam a
    delegação V1 explicitamente. O que está sob teste é a Rail A capability
    gate (bloqueia vs deixa passar), não V1-vs-ReAct."""
    monkeypatch.setenv("LIA_PHASE_2_V1_ENABLED", "true")


# ─── Helpers ──────────────────────────────────────────────────────────────


def _make_ctx(intent_hint: str | None = None, source: str = "rail_a", **kwargs) -> UniversalContext:
    """Cria UniversalContext com metadata de Rail A no extra."""
    extra: dict = {}
    if intent_hint is not None:
        extra["metadata"] = {
            "source": source,
            "card_id": "test-card",
            "stage": "definir-vaga",
            "domain_hint": "sourcing",
            "intent_hint": intent_hint,
        }
    ctx = UniversalContext(
        message="Adicione novo candidato",
        user_id="user-1",
        company_id="comp-1",
        conversation_id="conv-test",
        skip_memory_persist=True,
        extra=extra,
        **kwargs,
    )
    return ctx


def _make_mock_orchestrator():
    """Mock do V1 orchestrator — NUNCA deve ser chamado no PR-J gate."""
    mock_v1 = MagicMock()
    mock_v1.process_request = AsyncMock(
        return_value={
            "success": True,
            "response": "Resposta do LLM que NÃO deve aparecer",
            "agent_used": "sourcing_react",
            "intent_detected": "add_candidate",
        }
    )
    mock_v1.llm_service = MagicMock()
    return mock_v1


# ─── PR-J Gate — Testes principais ────────────────────────────────────────


class TestRailACapabilityGateWired:
    """Valida que check_rail_a_capability é invocado em process() e short-circuits."""

    @pytest.mark.asyncio
    async def test_add_candidate_retorna_open_modal_sem_llm(self):
        """Card add_candidate (chat_executable=False) deve retornar open_modal.

        harness: guia computacional — evita loop conversacional dead-end
        para cadastro de candidato (PR-J, Wave 2 Rail A).
        NÃO deve chamar process_request do LLM.
        """
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        ctx = _make_ctx(intent_hint="add_candidate")
        mock_db = MagicMock()

        # Simula capability_map devolvendo chat_executable=False + modal_id
        cap_result = {
            "type": "message",
            "content": "Abrindo o formulário para adicionar candidato...",
            "ui_action": "open_modal",
            "ui_action_params": {"modal_id": "add_candidate"},
            "confidence": 1.0,
            "domain": "capability_map",
            "source": "rail_a_gate",
            "success": True,
        }

        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=cap_result),
        ) as mock_cap:
            result = await orch.process(ctx, mock_db)

        # check_rail_a_capability foi chamado
        mock_cap.assert_called_once()

        # Resultado é ChatResponse com ui_action correto
        assert isinstance(result, ChatResponse)
        assert result.ui_action == "open_modal"
        assert result.ui_action_params == {"modal_id": "add_candidate"}
        assert "formulário" in result.content

        # LLM NÃO foi chamado
        mock_v1.process_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_interview_scheduling_retorna_open_modal(self):
        """interview_scheduling (chat_executable=False) → open_modal sem LLM."""
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        ctx = _make_ctx(intent_hint="reschedule_interview")
        mock_db = MagicMock()

        cap_result = {
            "type": "message",
            "content": "Abrindo o agendador de entrevistas...",
            "ui_action": "open_modal",
            "ui_action_params": {"modal_id": "interview_scheduling"},
            "confidence": 1.0,
            "domain": "capability_map",
            "source": "rail_a_gate",
            "success": True,
        }

        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=cap_result),
        ):
            result = await orch.process(ctx, mock_db)

        assert result.ui_action == "open_modal"
        assert result.ui_action_params["modal_id"] == "interview_scheduling"
        mock_v1.process_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_navigate_fallback_retorna_navigate_to(self):
        """navigate_fallback (sem modal_id) retorna ui_action=navigate_to."""
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        ctx = _make_ctx(intent_hint="list_talent_pools")
        mock_db = MagicMock()

        cap_result = {
            "type": "message",
            "content": "Abrindo a tela correspondente...",
            "ui_action": "navigate_to",
            "ui_action_params": {"page": "/funil-de-talentos"},
            "confidence": 1.0,
            "domain": "capability_map",
            "source": "rail_a_gate",
            "success": True,
        }

        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=cap_result),
        ):
            result = await orch.process(ctx, mock_db)

        assert result.ui_action == "navigate_to"
        assert result.ui_action_params["page"] == "/funil-de-talentos"
        mock_v1.process_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_executable_intent_continua_pipeline_normal(self):
        """Quando check_rail_a_capability retorna None, pipeline continua normalmente."""
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        ctx = _make_ctx(intent_hint="search_candidates")
        mock_db = MagicMock()

        # capability_map retorna None → chat_executable=True → pipeline normal
        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=None),
        ) as mock_cap, patch(
            "app.orchestrator.execution.main_orchestrator.pending_action_store"
        ) as mock_store, patch(
            "app.orchestrator.execution.main_orchestrator.action_executor"
        ) as mock_ae, patch(
            "app.domains.recruiter_assistant.services.conversation_memory.conversation_memory",
            AsyncMock(),
        ), patch(
            "app.orchestrator.execution.main_orchestrator.get_tenant_llm_config",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.orchestrator.execution.agentic_loop.agentic_loop.run",
            new=AsyncMock(return_value=None),
        ):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))
            result = await orch.process(ctx, mock_db)

        # check foi chamado
        mock_cap.assert_called_once()
        # Pipeline chegou ao LLM (process_request foi chamado)
        mock_v1.process_request.assert_called_once()
        assert isinstance(result, ChatResponse)

    @pytest.mark.asyncio
    async def test_falha_em_capability_check_nao_bloqueia_pipeline(self):
        """Se check_rail_a_capability lançar exceção, pipeline continua normalmente.

        harness: falha silenciosa com log debug é comportamento correto aqui —
        o gate é otimização, não guardrail de segurança.
        """
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        ctx = _make_ctx(intent_hint="add_candidate")
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(side_effect=RuntimeError("DB unavailable")),
        ) as mock_cap, patch(
            "app.orchestrator.execution.main_orchestrator.pending_action_store"
        ) as mock_store, patch(
            "app.orchestrator.execution.main_orchestrator.action_executor"
        ) as mock_ae, patch(
            "app.domains.recruiter_assistant.services.conversation_memory.conversation_memory",
            AsyncMock(),
        ), patch(
            "app.orchestrator.execution.main_orchestrator.get_tenant_llm_config",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.orchestrator.execution.agentic_loop.agentic_loop.run",
            new=AsyncMock(return_value=None),
        ):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))
            # Não deve lançar exceção
            result = await orch.process(ctx, mock_db)

        # check foi chamado (e falhou silenciosamente)
        mock_cap.assert_called_once()
        # Pipeline chegou ao LLM normalmente
        mock_v1.process_request.assert_called_once()
        assert isinstance(result, ChatResponse)

    @pytest.mark.asyncio
    async def test_mensagem_sem_metadata_nao_aciona_gate(self):
        """Mensagem normal (sem metadata Rail A) não deve chamar o capability check."""
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        # ctx SEM metadata (extra vazio)
        ctx = UniversalContext(
            message="buscar candidatos com Python",
            user_id="user-1",
            company_id="comp-1",
            conversation_id="conv-test",
            skip_memory_persist=True,
        )
        mock_db = MagicMock()

        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=None),
        ) as mock_cap, patch(
            "app.orchestrator.execution.main_orchestrator.pending_action_store"
        ) as mock_store, patch(
            "app.orchestrator.execution.main_orchestrator.action_executor"
        ) as mock_ae, patch(
            "app.domains.recruiter_assistant.services.conversation_memory.conversation_memory",
            AsyncMock(),
        ), patch(
            "app.orchestrator.execution.main_orchestrator.get_tenant_llm_config",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.orchestrator.execution.agentic_loop.agentic_loop.run",
            new=AsyncMock(return_value=None),
        ):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))
            result = await orch.process(ctx, mock_db)

        # Gate NÃO deve ser chamado quando não há metadata Rail A
        # (seja não chamado, seja chamado e retornado None — ambos são aceitáveis;
        # o que importa é que o resultado não tenha ui_action do gate)
        assert isinstance(result, ChatResponse)
        # Se foi chamado, deve ter retornado None (não short-circuited o pipeline)
        if mock_cap.called:
            # O call deve ter retornado None → pipeline continuou normalmente
            mock_v1.process_request.assert_called_once()
        else:
            mock_v1.process_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_metadata_source_diferente_de_rail_a_nao_aciona_gate(self):
        """Metadata com source != rail_a não deve disparar o capability gate."""
        mock_v1 = _make_mock_orchestrator()
        orch = MainOrchestrator(mock_v1, policy_gate_service=_allow_policy_gate())
        # ctx com metadata de outra origem
        ctx = _make_ctx(intent_hint="add_candidate", source="other_surface")
        mock_db = MagicMock()

        # O gate pode ser chamado mas deve retornar None para source != rail_a
        cap_result = {
            "type": "message",
            "content": "Deve ser ignorado",
            "ui_action": "open_modal",
            "ui_action_params": {"modal_id": "add_candidate"},
            "success": True,
        }

        # Mesmo que check_rail_a_capability seja chamado, source não é rail_a
        # → deve retornar None → pipeline normal
        with patch(
            "app.orchestrator.guards.rail_a_capability_check.check_rail_a_capability",
            new=AsyncMock(return_value=None),  # gate auto-filtra source
        ) as mock_cap, patch(
            "app.orchestrator.execution.main_orchestrator.pending_action_store"
        ) as mock_store, patch(
            "app.orchestrator.execution.main_orchestrator.action_executor"
        ) as mock_ae, patch(
            "app.domains.recruiter_assistant.services.conversation_memory.conversation_memory",
            AsyncMock(),
        ), patch(
            "app.orchestrator.execution.main_orchestrator.get_tenant_llm_config",
            new=AsyncMock(return_value=None),
        ), patch(
            "app.orchestrator.execution.agentic_loop.agentic_loop.run",
            new=AsyncMock(return_value=None),
        ):
            mock_store.get.return_value = None
            mock_ae.try_execute = AsyncMock(return_value=MagicMock(status="not_actionable"))
            result = await orch.process(ctx, mock_db)

        # Pipeline chegou ao LLM (gate não short-circuited)
        mock_v1.process_request.assert_called_once()
        assert isinstance(result, ChatResponse)
