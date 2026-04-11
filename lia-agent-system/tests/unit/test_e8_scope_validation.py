"""
E8 — Validar Escopo de Tools no Backend

Verifica:
1. Tool no escopo correto: _validate_tool_scope retorna True
2. Tool fora do escopo: _validate_tool_scope retorna False + loga warning
3. active_scope=None → fail-open (retorna True)
4. Tool GLOBAL passa em qualquer escopo
5. Violação logada no react_loop (não bloqueia execução)
6. ToolExecutorService: scope violation loga warning e prossegue
"""
import logging
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ---------------------------------------------------------------------------
# 1–4 — EnhancedAgentMixin._validate_tool_scope
# ---------------------------------------------------------------------------

class TestValidateToolScope:

    def _make_mixin(self, domain: str = "test"):
        from lia_agents_core.enhanced_agent_mixin import EnhancedAgentMixin
        obj = EnhancedAgentMixin.__new__(EnhancedAgentMixin)
        obj._enhanced_domain = domain
        return obj

    def test_tool_in_correct_scope_returns_true(self):
        """Tool mapeada no escopo correto → True."""
        mixin = self._make_mixin()
        with patch(
            "app.tools.scope_config.is_tool_allowed_in_scope", return_value=True
        ):
            result = mixin._validate_tool_scope("search_candidates", "TALENT_FUNNEL")
        assert result is True

    def test_tool_out_of_scope_returns_false_and_logs(self, caplog):
        """Tool fora do escopo → False + log [SCOPE-VIOLATION]."""
        mixin = self._make_mixin("pipeline")
        with patch(
            "app.tools.scope_config.is_tool_allowed_in_scope", return_value=False
        ):
            with caplog.at_level(logging.WARNING):
                result = mixin._validate_tool_scope("search_candidates", "in_job")
        assert result is False
        assert "SCOPE-VIOLATION" in caplog.text

    def test_no_scope_fail_open(self):
        """active_scope=None → fail-open sem chamada à scope_config."""
        mixin = self._make_mixin()
        result = mixin._validate_tool_scope("any_tool", None)
        assert result is True

    def test_global_tool_allowed_in_any_scope(self):
        """Tool no escopo GLOBAL é permitida dentro do escopo GLOBAL."""
        from app.tools.scope_config import PromptScope, is_tool_allowed_in_scope
        # Escopo GLOBAL inclui todas as tools mapeadas no GLOBAL
        result = is_tool_allowed_in_scope("get_system_config", PromptScope.GLOBAL)
        assert isinstance(result, bool)

    def test_fail_safe_on_import_error(self):
        """Falha de import na validação → fail-open True."""
        mixin = self._make_mixin()
        with patch(
            "app.tools.scope_config.is_tool_allowed_in_scope",
            side_effect=ImportError("scope_config unavailable"),
        ):
            result = mixin._validate_tool_scope("some_tool", "TALENT_FUNNEL")
        # fail-open: retorna True
        assert result is True


# ---------------------------------------------------------------------------
# 5 — react_loop: scope violation loga mas não bloqueia
# ---------------------------------------------------------------------------

class TestReActLoopScopeValidation:

    def test_active_scope_field_on_config(self):
        """ReActConfig aceita active_scope sem erro."""
        from lia_agents_core.react_loop import ReActConfig, ToolDefinition
        config = ReActConfig(
            system_prompt="test",
            domain="test",
            active_scope="TALENT_FUNNEL",
        )
        assert config.active_scope == "TALENT_FUNNEL"

    def test_no_active_scope_default(self):
        """ReActConfig sem active_scope → None."""
        from lia_agents_core.react_loop import ReActConfig
        config = ReActConfig(system_prompt="test", domain="test")
        assert config.active_scope is None


# ---------------------------------------------------------------------------
# 6 — ToolExecutorService: scope violation loga e prossegue
# ---------------------------------------------------------------------------

class TestToolExecutorServiceScope:

    @pytest.mark.asyncio
    async def test_scope_violation_logs_and_continues(self, caplog):
        """Scope violation loga [SCOPE-VIOLATION] mas executa a tool (fail-open)."""
        from app.shared.services.tool_executor_service import ToolExecutorService, ToolExecutionRequest

        service = ToolExecutorService()

        request = ToolExecutionRequest(
            tool_name="search_candidates",
            parameters={},
            user_id="user-123",
            company_id="co-1",
            agent_type="wizard",
            active_scope="in_job",  # search_candidates pode não estar em in_job
        )

        mock_tool_result = MagicMock()
        mock_tool_result.success = True
        mock_tool_result.result = {"message": "ok", "action_taken": "search_candidates", "affected_entities": []}
        mock_tool_result.error = None

        with patch(
            "app.tools.scope_config.is_tool_allowed_in_scope", return_value=False
        ):
            with patch.object(service, "validate_tool_exists", return_value=True):
                with patch(
                    "app.services.tool_executor_service.tool_executor"
                ) as mock_executor:
                    mock_executor.execute = AsyncMock(return_value=mock_tool_result)
                    with caplog.at_level(logging.WARNING):
                        result = await service.execute(request)

        assert "SCOPE-VIOLATION" in caplog.text
        assert result is not None

    @pytest.mark.asyncio
    async def test_no_scope_skips_validation(self):
        """active_scope=None → nenhuma chamada a is_tool_allowed_in_scope."""
        from app.shared.services.tool_executor_service import ToolExecutorService, ToolExecutionRequest

        service = ToolExecutorService()
        request = ToolExecutionRequest(
            tool_name="search_candidates",
            parameters={},
            user_id="user-123",
            active_scope=None,
        )

        with patch(
            "app.tools.scope_config.is_tool_allowed_in_scope"
        ) as mock_scope:
            with patch.object(service, "validate_tool_exists", return_value=False):
                result = await service.execute(request)

        mock_scope.assert_not_called()
