"""
Unit tests for PlanOrchestrationService — Sprint II.1 of LIA-D06 migration.

Tests cobrem:
- Detection wrapping (graceful failure → None)
- Execution delegation com WS callback
- Multi-tenant: tenant_id propagado
- WebSocket progress callback (presença + ausência)
- WS failure não bloqueia execução
- PlanExecutionResult shape

Reference: ADR-019 — Sprint II.1
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator.services.plan_orchestration_service import (
    PlanExecutionResult,
    PlanOrchestrationService,
)


def _make_executed_plan_mock(
    success: bool = True, pattern: str = "test_pattern", plan_id: str = "p1"
) -> MagicMock:
    """Build a mock for executed_plan."""
    executed = MagicMock()
    executed.detected_pattern = pattern
    executed.plan_id = plan_id
    executed.get_summary = MagicMock(return_value={"steps": 1, "completed": 1})
    return executed


def _make_consolidated_mock(
    success: bool = True,
    message: str = "Plano executado.",
    data: dict | None = None,
    suggestions: list | None = None,
) -> MagicMock:
    """Build a mock for build_consolidated_response result."""
    consolidated = MagicMock()
    consolidated.success = success
    consolidated.message = message
    consolidated.data = data or {}
    consolidated.suggestions = suggestions or []
    return consolidated


# ─────────────────────────────────────────────────────────────────────────────
# PlanExecutionResult — dataclass
# ─────────────────────────────────────────────────────────────────────────────


class TestPlanExecutionResult:
    """Validação do dataclass."""

    def test_is_frozen(self):
        """PlanExecutionResult é imutável."""
        result = PlanExecutionResult(
            executed_plan=None,
            success=True,
            message="ok",
            data={},
            suggestions=[],
            pattern="x",
            plan_id="p1",
            summary={},
        )
        with pytest.raises(Exception):
            result.success = False  # type: ignore[misc]

    def test_required_fields(self):
        """Todos os 8 campos obrigatórios."""
        fields = PlanExecutionResult.__dataclass_fields__
        expected = {
            "executed_plan",
            "success",
            "message",
            "data",
            "suggestions",
            "pattern",
            "plan_id",
            "summary",
        }
        assert set(fields.keys()) == expected


# ─────────────────────────────────────────────────────────────────────────────
# PlanOrchestrationService.detect — wraps PlanDetector.detect
# ─────────────────────────────────────────────────────────────────────────────


class TestDetect:
    """Detection wrapping com graceful failure."""

    def test_detect_returns_plan_when_detector_finds_one(self):
        detected = MagicMock()
        detector = MagicMock()
        detector.detect = MagicMock(return_value=detected)

        service = PlanOrchestrationService(
            plan_detector=detector, plan_executor=MagicMock()
        )
        result = service.detect("publica essa vaga e busca candidatos")
        assert result is detected
        detector.detect.assert_called_once_with("publica essa vaga e busca candidatos")

    def test_detect_returns_none_when_no_plan(self):
        detector = MagicMock()
        detector.detect = MagicMock(return_value=None)

        service = PlanOrchestrationService(
            plan_detector=detector, plan_executor=MagicMock()
        )
        assert service.detect("oi tudo bem?") is None

    def test_detect_exception_returns_none(self):
        """Exceção no detector → None (graceful, non-blocking)."""
        detector = MagicMock()
        detector.detect = MagicMock(side_effect=RuntimeError("detector crashed"))

        service = PlanOrchestrationService(
            plan_detector=detector, plan_executor=MagicMock()
        )
        # Should not raise
        result = service.detect("any message")
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# PlanOrchestrationService.execute — wraps PlanExecutor + WS
# ─────────────────────────────────────────────────────────────────────────────


class TestExecute:
    """Execution delegation."""

    @pytest.mark.asyncio
    async def test_execute_returns_plan_execution_result(self):
        executed = _make_executed_plan_mock()
        consolidated = _make_consolidated_mock(message="ok plan")

        executor = MagicMock()
        executor.execute = AsyncMock(return_value=executed)
        executor.build_consolidated_response = MagicMock(return_value=consolidated)

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        result = await service.execute(
            detected_plan=MagicMock(),
            user_id="user-1",
            session_id="sess-1",
            tenant_id="tenant-a",
            base_context={"company_id": "tenant-a"},
        )

        assert isinstance(result, PlanExecutionResult)
        assert result.success is True
        assert result.message == "ok plan"

    @pytest.mark.asyncio
    async def test_execute_propagates_tenant_id(self):
        """P0 LGPD: tenant_id deve ser propagado ao PlanExecutor."""
        executed = _make_executed_plan_mock()
        consolidated = _make_consolidated_mock()

        executor = MagicMock()
        executor.execute = AsyncMock(return_value=executed)
        executor.build_consolidated_response = MagicMock(return_value=consolidated)

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="s1",
            tenant_id="tenant-isolation-test",
            base_context={},
        )

        kwargs = executor.execute.call_args.kwargs
        assert kwargs["tenant_id"] == "tenant-isolation-test"

    @pytest.mark.asyncio
    async def test_execute_passes_user_id_and_session_id(self):
        executor = MagicMock()
        executor.execute = AsyncMock(return_value=_make_executed_plan_mock())
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="user-abc",
            session_id="conv-xyz",
            tenant_id=None,
            base_context={},
        )

        kwargs = executor.execute.call_args.kwargs
        assert kwargs["user_id"] == "user-abc"
        assert kwargs["session_id"] == "conv-xyz"

    @pytest.mark.asyncio
    async def test_execute_default_message_when_consolidated_empty(self):
        """Se consolidated.message é vazio, usa default 'Plano executado.'"""
        consolidated = _make_consolidated_mock(message="")

        executor = MagicMock()
        executor.execute = AsyncMock(return_value=_make_executed_plan_mock())
        executor.build_consolidated_response = MagicMock(return_value=consolidated)

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        result = await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="s1",
            tenant_id="t1",
            base_context={},
        )

        assert result.message == "Plano executado."

    @pytest.mark.asyncio
    async def test_execute_extracts_pattern_and_plan_id(self):
        executed = _make_executed_plan_mock(
            pattern="publish_then_search", plan_id="p-12345"
        )
        consolidated = _make_consolidated_mock()

        executor = MagicMock()
        executor.execute = AsyncMock(return_value=executed)
        executor.build_consolidated_response = MagicMock(return_value=consolidated)

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        result = await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="s1",
            tenant_id="t1",
            base_context={},
        )

        assert result.pattern == "publish_then_search"
        assert result.plan_id == "p-12345"

    @pytest.mark.asyncio
    async def test_execute_passes_default_empty_base_context(self):
        executor = MagicMock()
        executor.execute = AsyncMock(return_value=_make_executed_plan_mock())
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="s1",
            tenant_id="t1",
            base_context=None,  # explicit None
        )

        kwargs = executor.execute.call_args.kwargs
        assert kwargs["base_context"] == {}


# ─────────────────────────────────────────────────────────────────────────────
# WebSocket progress callback
# ─────────────────────────────────────────────────────────────────────────────


class TestWebSocketCallback:
    """WS progress callback é construído quando ws_manager presente."""

    @pytest.mark.asyncio
    async def test_no_ws_manager_callback_is_none(self):
        executor = MagicMock()
        executor.execute = AsyncMock(return_value=_make_executed_plan_mock())
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor, ws_manager=None
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="s1",
            tenant_id=None,
            base_context={},
        )

        kwargs = executor.execute.call_args.kwargs
        assert kwargs["progress_callback"] is None

    @pytest.mark.asyncio
    async def test_empty_session_id_callback_is_none(self):
        """session_id vazia → callback None mesmo com ws_manager."""
        ws = MagicMock()
        ws.send_to_session = AsyncMock()

        executor = MagicMock()
        executor.execute = AsyncMock(return_value=_make_executed_plan_mock())
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor, ws_manager=ws
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="",  # empty
            tenant_id=None,
            base_context={},
        )

        kwargs = executor.execute.call_args.kwargs
        assert kwargs["progress_callback"] is None

    @pytest.mark.asyncio
    async def test_ws_callback_sends_progress_event(self):
        """Callback emite payload com type=plan_progress + event + data."""
        ws = MagicMock()
        ws.send_to_session = AsyncMock()

        captured_callback = []

        executor = MagicMock()

        async def _exec(**kwargs):
            captured_callback.append(kwargs.get("progress_callback"))
            return _make_executed_plan_mock()

        executor.execute = _exec
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor, ws_manager=ws
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="conv-1",
            tenant_id=None,
            base_context={},
        )

        callback = captured_callback[0]
        assert callback is not None
        # Invoke callback to verify shape
        await callback("step_started", {"step": 1})

        ws.send_to_session.assert_called_once_with(
            "conv-1",
            {"type": "plan_progress", "event": "step_started", "step": 1},
        )

    @pytest.mark.asyncio
    async def test_ws_failure_does_not_propagate(self):
        """P1: WS send failure não bloqueia plan execution."""
        ws = MagicMock()
        ws.send_to_session = AsyncMock(side_effect=ConnectionError("WS down"))

        captured_callback = []

        executor = MagicMock()

        async def _exec(**kwargs):
            captured_callback.append(kwargs.get("progress_callback"))
            return _make_executed_plan_mock()

        executor.execute = _exec
        executor.build_consolidated_response = MagicMock(
            return_value=_make_consolidated_mock()
        )

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor, ws_manager=ws
        )

        await service.execute(
            detected_plan=MagicMock(),
            user_id="u1",
            session_id="conv-1",
            tenant_id=None,
            base_context={},
        )

        callback = captured_callback[0]
        # Invoke callback — should NOT raise
        try:
            await callback("step_started", {"step": 1})
        except ConnectionError:
            pytest.fail("WS failure should be caught — plan execution must not block")


# ─────────────────────────────────────────────────────────────────────────────
# Fix #6 & WSManagerProtocol validation
# ─────────────────────────────────────────────────────────────────────────────


class TestExecutorExceptionPropagation:
    """P1 fix: PlanExecutor.execute exception propaga para caller."""

    @pytest.mark.asyncio
    async def test_executor_exception_propagates(self):
        """Service nao captura RuntimeError do executor — propaga."""
        executor = MagicMock()
        executor.execute = AsyncMock(side_effect=RuntimeError("executor crash"))

        service = PlanOrchestrationService(
            plan_detector=MagicMock(), plan_executor=executor
        )

        with pytest.raises(RuntimeError, match="executor crash"):
            await service.execute(
                detected_plan=MagicMock(),
                user_id="u1",
                session_id="s1",
                tenant_id="t1",
                base_context={},
            )


class TestWSManagerValidation:
    """P1 fix: WSManagerProtocol validation no __init__."""

    def test_invalid_ws_manager_raises_typeerror(self):
        """Objeto sem send_to_session leva a TypeError — fail-fast."""
        invalid_ws = object()  # sem send_to_session method

        with pytest.raises(TypeError, match="send_to_session"):
            PlanOrchestrationService(
                plan_detector=MagicMock(),
                plan_executor=MagicMock(),
                ws_manager=invalid_ws,
            )

    def test_none_ws_manager_is_ok(self):
        """ws_manager None nao gera erro (e o default)."""
        service = PlanOrchestrationService(
            plan_detector=MagicMock(),
            plan_executor=MagicMock(),
            ws_manager=None,
        )
        assert service._ws_manager is None

    def test_valid_ws_manager_accepted(self):
        """WS manager com send_to_session method e aceito."""
        ws = MagicMock()
        ws.send_to_session = AsyncMock()
        service = PlanOrchestrationService(
            plan_detector=MagicMock(),
            plan_executor=MagicMock(),
            ws_manager=ws,
        )
        assert service._ws_manager is ws
