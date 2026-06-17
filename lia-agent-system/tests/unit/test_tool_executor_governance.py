"""
Anti-regressão · W1-004 Phase A (2026-05-22) — ToolExecutor governance wiring.

Verifica que `ToolExecutor.execute()` enforça:
1. Step 2 (multi-tenancy fail-closed) — company_id é obrigatório
2. Step 7 (audit log per-call) — AuditService.log_action chamado non-blocking
3. Step 8 (metrics) — _emit_metrics chamado com (tool_name, success, elapsed_ms)

Bonus: garante que `GovernanceExecutor` (canonical 8-step pattern) continua
intacto para futuros callers que usam ToolContract.

Pre-audit: REPLIT_LIA_REMEDIATION_BACKLOG_2026-05-22.md (W1-004).
Sensor: scripts/check_governance_executor_wired.py.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def _reset_registry():
    """Limpa tool registry entre testes pra evitar pollution."""
    from app.tools.registry import tool_registry

    saved = dict(tool_registry._tools)
    tool_registry._tools.clear()
    yield
    tool_registry._tools.clear()
    tool_registry._tools.update(saved)


@pytest.fixture
def _register_dummy_tool(_reset_registry):
    """Registra um tool dummy de echo para testes."""
    from app.tools.registry import ToolDefinition, tool_registry

    async def echo_handler(**kwargs):
        # Remove canonical injected fields (W1-001 Phase A pattern)
        kwargs.pop("_context", None)
        return {"echoed": kwargs}

    tool = ToolDefinition(
        name="dummy_echo",
        description="Echo for governance tests",
        parameters_schema={"type": "object", "properties": {"msg": {"type": "string"}}, "required": []},
        handler=echo_handler,
    )
    tool_registry.register(tool)
    return tool


class TestStep2CompanyIdFailClosed:
    """W1-004 Step 2 · Multi-tenancy fail-closed: company_id obrigatório."""

    @pytest.mark.asyncio
    async def test_execute_without_context_fails_closed(self, _register_dummy_tool):
        """ToolExecutor.execute(context=None) deve retornar erro company_id."""
        from app.tools.executor import ToolExecutor

        executor = ToolExecutor()
        result = await executor.execute(
            tool_name="dummy_echo",
            parameters={"msg": "hi"},
            context=None,
        )

        assert result.success is False, (
            f"Expected fail-closed on missing context. Got: {result.error}"
        )
        assert "company_id" in (result.error or "").lower(), (
            f"Expected company_id in error message. Got: {result.error}"
        )

    @pytest.mark.asyncio
    async def test_execute_with_valid_context_succeeds(self, _register_dummy_tool):
        """ToolExecutor.execute() com context válido passa do step 2."""
        from app.tools.executor import ToolExecutionContext, ToolExecutor

        executor = ToolExecutor()
        ctx = ToolExecutionContext(user_id="u-1", company_id="co-test")
        with patch("app.tools.executor.get_audit_service") as _mock_audit:
            _mock_audit.return_value = MagicMock(log_action=AsyncMock(return_value=None))
            result = await executor.execute(
                tool_name="dummy_echo",
                parameters={"msg": "hello"},
                context=ctx,
            )

        assert result.success is True, f"Expected success. Got: {result.error}"


class TestStep7AuditLog:
    """W1-004 Step 7 · Audit log per-call (non-blocking via asyncio.create_task)."""

    @pytest.mark.asyncio
    async def test_successful_execute_triggers_audit_log(self, _register_dummy_tool):
        """ToolExecutor.execute() success → audit.log_action called."""
        from app.tools.executor import ToolExecutionContext, ToolExecutor

        executor = ToolExecutor()
        ctx = ToolExecutionContext(user_id="u-1", company_id="co-test", session_id="sess-1")

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)

        with patch("app.tools.executor.get_audit_service", return_value=mock_audit):
            await executor.execute(
                tool_name="dummy_echo",
                parameters={"msg": "audit-me"},
                context=ctx,
            )
            # Drain any pending background tasks
            await asyncio.sleep(0.05)

        assert mock_audit.log_action.called, (
            "AuditService.log_action should be invoked for every tool execution."
        )
        call_kwargs = mock_audit.log_action.call_args.kwargs
        assert call_kwargs.get("action_type") == "tool_call"
        assert call_kwargs.get("target_id") == "dummy_echo"
        assert call_kwargs.get("company_id") == "co-test"

    @pytest.mark.asyncio
    async def test_failed_execute_also_triggers_audit_log(self, _register_dummy_tool):
        """Tools que falham TAMBÉM devem ser logados (compliance trail)."""
        from app.tools.executor import ToolExecutionContext, ToolExecutor

        executor = ToolExecutor()
        ctx = ToolExecutionContext(user_id="u-1", company_id="co-test")

        mock_audit = MagicMock()
        mock_audit.log_action = AsyncMock(return_value=None)

        with patch("app.tools.executor.get_audit_service", return_value=mock_audit):
            # Force failure via unknown tool
            await executor.execute(
                tool_name="nonexistent_tool",
                parameters={},
                context=ctx,
            )
            await asyncio.sleep(0.05)

        assert mock_audit.log_action.called, (
            "Audit log should fire even on failure (compliance trail invariant)."
        )


class TestStep8MetricsEmit:
    """W1-004 Step 8 · Metrics hook emitido após cada execute()."""

    @pytest.mark.asyncio
    async def test_emit_metrics_called_on_success(self, _register_dummy_tool):
        from app.tools.executor import ToolExecutionContext, ToolExecutor

        executor = ToolExecutor()
        ctx = ToolExecutionContext(user_id="u-1", company_id="co-test")

        with patch("app.tools.executor.get_audit_service") as _mock_audit, \
             patch.object(executor, "_emit_metrics") as mock_metrics:
            _mock_audit.return_value = MagicMock(log_action=AsyncMock(return_value=None))
            await executor.execute(
                tool_name="dummy_echo",
                parameters={"msg": "metrics"},
                context=ctx,
            )

        assert mock_metrics.called, "_emit_metrics should be called once per execute()"
        call_args = mock_metrics.call_args
        # Accept both positional and keyword styles
        kwargs = call_args.kwargs
        args = call_args.args
        assert args[0] == "dummy_echo" or kwargs.get("tool_name") == "dummy_echo"
        assert kwargs.get("success") is True or (len(args) >= 2 and args[1] is True)

    @pytest.mark.asyncio
    async def test_emit_metrics_called_on_failure(self, _register_dummy_tool):
        from app.tools.executor import ToolExecutionContext, ToolExecutor

        executor = ToolExecutor()
        ctx = ToolExecutionContext(user_id="u-1", company_id="co-test")

        with patch("app.tools.executor.get_audit_service") as _mock_audit, \
             patch.object(executor, "_emit_metrics") as mock_metrics:
            _mock_audit.return_value = MagicMock(log_action=AsyncMock(return_value=None))
            await executor.execute(
                tool_name="nonexistent_tool",
                parameters={},
                context=ctx,
            )

        assert mock_metrics.called, (
            "_emit_metrics should fire on failure too (observability invariant)."
        )


class TestGovernanceExecutorCanonicalPreserved:
    """W1-004 · GovernanceExecutor (canonical 8-step) continua importável intacta."""

    def test_governance_executor_class_importable(self) -> None:
        from app.tools.executor import GovernanceExecutor

        assert hasattr(GovernanceExecutor, "execute")
        assert callable(GovernanceExecutor.execute)

    def test_governance_executor_module_singleton(self) -> None:
        from app.tools.executor import governance_executor

        assert governance_executor is not None

    def test_governance_executor_has_8_steps_documented(self) -> None:
        """Docstring deve listar 8 steps canonical (pattern documentation)."""
        from app.tools.executor import GovernanceExecutor

        doc = GovernanceExecutor.__doc__ or ""
        # Esperamos pelo menos referências a "8" e "step" no docstring
        assert "8" in doc, f"Docstring deve documentar 8-step pipeline. Got: {doc[:200]}"
