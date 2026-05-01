"""
P0-D — Testes do pre-call budget check em ReActLoop.run().

SKIPPED: ReActLoop foi removido — agentes usam LangGraph nativo (create_react_agent).
Budget check agora é responsabilidade da camada LangGraphReActBase.
"""
import pytest
pytestmark = pytest.mark.skip(reason="ReActLoop removido — agentes usam LangGraph nativo")
from unittest.mock import AsyncMock, MagicMock, patch

from lia_agents_core.react_loop import ReActConfig, ReActLoop, ToolDefinition
from lia_agents_core.working_memory import WorkingMemoryService


def _make_config(**kwargs):
    defaults = dict(
        system_prompt="Você é a LIA.",
        domain="test_domain",
        available_tools=[],
    )
    defaults.update(kwargs)
    return ReActConfig(**defaults)


def _make_loop(config=None):
    cfg = config or _make_config()
    wm = MagicMock(spec=WorkingMemoryService)
    wm.increment_iteration = AsyncMock()
    wm.get_memory_context = AsyncMock(return_value="")
    return ReActLoop(config=cfg, working_memory_service=wm)


@pytest.fixture
def base_context():
    return {"user_id": "user-1", "company_id": "company-abc"}


class TestPreCallBudgetCheck:

    async def test_limite_excedido_retorna_sem_chamar_llm(self, base_context):
        """Quando limites estão excedidos, retorna resposta de budget imediatamente."""
        mock_tracking = MagicMock()
        mock_tracking.check_limits = AsyncMock(
            return_value=(False, "Limite diário de tokens atingido")
        )

        loop = _make_loop()

        with patch("lia_agents_core.react_loop.settings") as mock_settings:
            mock_settings.REACT_TOKEN_BUDGET_ENABLED = True
            mock_settings.REACT_MAX_ITERATIONS_DEFAULT = 5
            mock_settings.REACT_TOKEN_BUDGET_DEFAULT = None

            with patch(
                "app.services.token_tracking_service.token_tracking_service",
                mock_tracking,
            ):
                state = await loop.run(
                    message="me dê um ranking",
                    context=base_context,
                    session_id="sess-1",
                )

        assert state.should_respond is True
        assert "Limite de uso atingido" in state.final_response
        assert "Limite diário de tokens atingido" in state.final_response
        # LLM não deve ter sido chamado (nenhuma iteração executada)
        assert state.iteration == 0

    async def test_sem_company_id_skip_check(self):
        """Sem company_id no context, check é ignorado e loop prossegue."""
        loop = _make_loop()
        context_sem_company = {"user_id": "user-1"}  # sem company_id

        mock_reason = AsyncMock(return_value='{"thought":"ok","action":"respond","response":"Resposta"}')
        with patch.object(loop, "_reason", mock_reason):
            with patch("lia_agents_core.react_loop.settings") as mock_settings:
                mock_settings.REACT_TOKEN_BUDGET_ENABLED = True
                mock_settings.REACT_MAX_ITERATIONS_DEFAULT = 1
                mock_settings.REACT_TOKEN_BUDGET_DEFAULT = None
                state = await loop.run(
                    message="olá",
                    context=context_sem_company,
                    session_id="sess-2",
                )

        # Deve ter executado normalmente (sem bloquear)
        assert state.final_response is not None

    async def test_budget_disabled_skip_check(self, base_context):
        """Com REACT_TOKEN_BUDGET_ENABLED=False, pre-check não é executado."""
        mock_tracking = MagicMock()
        mock_tracking.check_limits = AsyncMock(
            return_value=(False, "Limite excedido")
        )

        loop = _make_loop()
        mock_reason = AsyncMock(return_value='{"thought":"ok","action":"respond","response":"OK"}')

        with patch.object(loop, "_reason", mock_reason):
            with patch("lia_agents_core.react_loop.settings") as mock_settings:
                mock_settings.REACT_TOKEN_BUDGET_ENABLED = False
                mock_settings.REACT_MAX_ITERATIONS_DEFAULT = 1
                mock_settings.REACT_TOKEN_BUDGET_DEFAULT = None
                with patch(
                    "app.services.token_tracking_service.token_tracking_service",
                    mock_tracking,
                ):
                    state = await loop.run(
                        message="teste",
                        context=base_context,
                        session_id="sess-3",
                    )

        # Mesmo com mock retornando False, check não roda → loop executa
        mock_tracking.check_limits.assert_not_called()

    async def test_servico_indisponivel_fail_safe(self, base_context):
        """Se token_tracking_service lançar exceção, loop prossegue normalmente."""
        loop = _make_loop()
        mock_reason = AsyncMock(return_value='{"thought":"ok","action":"respond","response":"OK"}')

        with patch.object(loop, "_reason", mock_reason):
            with patch("lia_agents_core.react_loop.settings") as mock_settings:
                mock_settings.REACT_TOKEN_BUDGET_ENABLED = True
                mock_settings.REACT_MAX_ITERATIONS_DEFAULT = 1
                mock_settings.REACT_TOKEN_BUDGET_DEFAULT = None
                # Simula exceção no serviço — deve ser silenciosa (fail-safe)
                with patch(
                    "app.services.token_tracking_service.token_tracking_service",
                    side_effect=Exception("Redis unavailable"),
                ):
                    state = await loop.run(
                        message="teste",
                        context=base_context,
                        session_id="sess-4",
                    )

        # Fail-safe: loop executou normalmente
        assert state.final_response is not None
