"""
Sprint III.B tests — _route_via_services + feature flag granular.

Garante:
- Feature flag `LIA_V2_USE_PLAN_SERVICE` default OFF (backward compat)
- Quando flag ON + plan_service injetado + plan detected → V2 usa service
- Quando flag ON mas plan_service None → fallback to V1 delegation
- Quando flag ON + plan_service ON mas detect retorna None → fallback V1
- Quando service.execute crasha → fallback V1 (graceful)

Reference: ADR-019 — Sprint III.B
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.orchestrator.execution.main_orchestrator import (
    MainOrchestrator,
    _is_plan_service_enabled,
)


# ─────────────────────────────────────────────────────────────────────────────
# Feature flag tests
# ─────────────────────────────────────────────────────────────────────────────


class TestFeatureFlagPlanService:
    """LIA_V2_USE_PLAN_SERVICE env var parsing."""

    def test_default_is_false(self, monkeypatch):
        monkeypatch.delenv("LIA_V2_USE_PLAN_SERVICE", raising=False)
        assert _is_plan_service_enabled() is False

    @pytest.mark.parametrize("value", ["true", "True", "TRUE", "1", "yes", "YES"])
    def test_truthy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_V2_USE_PLAN_SERVICE", value)
        assert _is_plan_service_enabled() is True

    @pytest.mark.parametrize("value", ["false", "0", "no", "off", ""])
    def test_falsy_values(self, monkeypatch, value):
        monkeypatch.setenv("LIA_V2_USE_PLAN_SERVICE", value)
        assert _is_plan_service_enabled() is False


# ─────────────────────────────────────────────────────────────────────────────
# _try_plan_via_service tests
# ─────────────────────────────────────────────────────────────────────────────


def _make_v1_orchestrator():
    """Mock V1 com process_request que retorna shape válido."""
    v1 = MagicMock()
    v1.process_request = AsyncMock(
        return_value={
            "success": True,
            "message": "v1 response",
            "intent": "v1_intent",
            "agent": "v1_agent",
        }
    )
    v1.llm_service = MagicMock()
    return v1


def _make_ctx():
    """Mock UniversalContext."""
    ctx = MagicMock()
    ctx.user_id = "u1"
    ctx.message = "qualquer mensagem"
    ctx.company_id = "tenant-a"
    return ctx


class TestTryPlanViaServiceNoServiceInjected:
    """Quando plan_service é None, retorna None (caller faz V1 fallback)."""

    @pytest.mark.asyncio
    async def test_no_service_returns_none(self):
        v2 = MainOrchestrator(orchestrator=_make_v1_orchestrator(), plan_service=None)
        result = await v2._try_plan_via_service(_make_ctx(), "conv-1", {})
        # _try_plan_via_service não checa flag — apenas service None.
        # Mas chamado direto sem service injected — vai dar AttributeError em detect().
        # Test garante: caller deve checar service is not None ANTES.
        # Na prática route() faz isso via:
        #   if _is_plan_service_enabled() and self._plan_service is not None:
        # Então este test verifica boundary explicito.
        # (test passa mesmo que NoneType.detect crasha — caught no except)
        assert result is None


class TestTryPlanViaServiceNoPlanDetected:
    """Quando plan_service.detect retorna None, retorna None."""

    @pytest.mark.asyncio
    async def test_no_plan_detected_returns_none(self):
        plan_svc = MagicMock()
        plan_svc.detect = MagicMock(return_value=None)

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(), plan_service=plan_svc
        )
        result = await v2._try_plan_via_service(_make_ctx(), "conv-1", {})
        assert result is None
        plan_svc.detect.assert_called_once_with("qualquer mensagem")


class TestTryPlanViaServicePlanDetected:
    """Quando plan detected + executed, retorna dict V1-compatible."""

    @pytest.mark.asyncio
    async def test_plan_detected_returns_v1_compatible_dict(self):
        # Mock plan + plan_result
        detected = MagicMock()
        detected.detected_pattern = "publish_then_search"

        plan_result = MagicMock()
        plan_result.success = True
        plan_result.message = "Plano executado!"
        plan_result.data = {"jobs_published": 1, "candidates_found": 5}
        plan_result.suggestions = ["mais 5?", "outra vaga?"]
        plan_result.pattern = "publish_then_search"
        plan_result.summary = {"steps": 2, "completed": 2}

        plan_svc = MagicMock()
        plan_svc.detect = MagicMock(return_value=detected)
        plan_svc.execute = AsyncMock(return_value=plan_result)

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(), plan_service=plan_svc
        )
        result = await v2._try_plan_via_service(
            _make_ctx(), "conv-abc", {"company_id": "tenant-a"}
        )

        assert result is not None
        assert result["success"] is True
        assert result["conversation_id"] == "conv-abc"
        assert result["intent"] == "plan:publish_then_search"
        assert result["agent"] == "plan_executor"
        assert result["agent_type"] == "execution_plan"
        assert result["message"] == "Plano executado!"
        assert result["execution_plan"] == {"steps": 2, "completed": 2}
        assert result["suggested_prompts"] == ["mais 5?", "outra vaga?"]

    @pytest.mark.asyncio
    async def test_tenant_id_propagated_to_service_execute(self):
        """P0 LGPD: tenant_id (company_id) deve chegar no plan_service.execute."""
        detected = MagicMock()
        plan_result = MagicMock(
            success=True,
            message="ok",
            data={},
            suggestions=[],
            pattern="x",
            summary={},
        )

        plan_svc = MagicMock()
        plan_svc.detect = MagicMock(return_value=detected)
        plan_svc.execute = AsyncMock(return_value=plan_result)

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(), plan_service=plan_svc
        )

        ctx = _make_ctx()
        ctx.company_id = "tenant-isolation-x"

        await v2._try_plan_via_service(ctx, "conv-1", {})

        kwargs = plan_svc.execute.call_args.kwargs
        assert kwargs["tenant_id"] == "tenant-isolation-x"


class TestTryPlanViaServiceGracefulDegradation:
    """Service exception → returns None (caller fallback to V1)."""

    @pytest.mark.asyncio
    async def test_detect_exception_returns_none(self):
        plan_svc = MagicMock()
        plan_svc.detect = MagicMock(side_effect=RuntimeError("detect crashed"))

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(), plan_service=plan_svc
        )
        result = await v2._try_plan_via_service(_make_ctx(), "conv-1", {})
        # Exception caught — caller faz V1 fallback
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_exception_returns_none(self):
        detected = MagicMock()
        plan_svc = MagicMock()
        plan_svc.detect = MagicMock(return_value=detected)
        plan_svc.execute = AsyncMock(side_effect=RuntimeError("execute crashed"))

        v2 = MainOrchestrator(
            orchestrator=_make_v1_orchestrator(), plan_service=plan_svc
        )
        result = await v2._try_plan_via_service(_make_ctx(), "conv-1", {})
        # Exception em execute também caught — fallback V1
        assert result is None
