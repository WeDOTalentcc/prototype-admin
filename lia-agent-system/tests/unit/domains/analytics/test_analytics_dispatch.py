"""
Unit tests for AnalyticsDispatchService — extraction follow-up.

Tests:
- Template command path (execute_command)
- Natural query path (analyze_natural_query)
- Exception handling (returns success=False)
- is_template_command helper

Reference: ADR-019 — process_analytics_request extraction
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.analytics.services.analytics_dispatch import AnalyticsDispatchService


def _make_result_obj(command="cmd", response="resp"):
    """Mock result object com attributes V1-compatible."""
    r = MagicMock()
    r.command = command
    r.agent_used = "analytics_agent"
    r.response = response
    r.data = {"key": "value"}
    r.charts = ["chart1"]
    r.suggestions = ["s1", "s2"]
    r.metadata = {"meta": "data"}
    return r


# ─────────────────────────────────────────────────────────────────────────────
# Initialization
# ─────────────────────────────────────────────────────────────────────────────


class TestInit:
    def test_requires_both_args(self):
        with pytest.raises(TypeError):
            AnalyticsDispatchService()  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            AnalyticsDispatchService(analytics_service=MagicMock())  # type: ignore[call-arg]

    def test_stores_dependencies(self):
        svc = MagicMock()
        templates = {"cmd1": {}}
        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates=templates
        )
        assert adp._service is svc
        assert adp._templates is templates


# ─────────────────────────────────────────────────────────────────────────────
# Template command path
# ─────────────────────────────────────────────────────────────────────────────


class TestTemplateCommand:
    @pytest.mark.asyncio
    async def test_template_command_uses_execute_command(self):
        svc = MagicMock()
        svc.execute_command = AsyncMock(return_value=_make_result_obj("cmd1", "resp1"))
        svc.analyze_natural_query = AsyncMock()  # não deve ser chamado

        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates={"cmd1": {}}
        )
        result = await adp.dispatch("cmd1", {"company_id": "t1"})

        svc.execute_command.assert_called_once_with("cmd1", {"company_id": "t1"})
        svc.analyze_natural_query.assert_not_called()
        assert result["success"] is True
        assert result["response"] == "resp1"

    @pytest.mark.asyncio
    async def test_response_shape_v1_compatible(self):
        svc = MagicMock()
        svc.execute_command = AsyncMock(
            return_value=_make_result_obj("analyze", "got it")
        )
        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates={"analyze": {}}
        )

        result = await adp.dispatch("analyze", {"company_id": "t1"})

        # Todos os 8 campos do shape V1
        for key in (
            "success",
            "command",
            "agent_used",
            "response",
            "data",
            "charts",
            "suggestions",
            "metadata",
        ):
            assert key in result


# ─────────────────────────────────────────────────────────────────────────────
# Natural query path
# ─────────────────────────────────────────────────────────────────────────────


class TestNaturalQuery:
    @pytest.mark.asyncio
    async def test_unknown_command_uses_natural_query(self):
        svc = MagicMock()
        svc.execute_command = AsyncMock()  # não deve ser chamado
        svc.analyze_natural_query = AsyncMock(
            return_value=_make_result_obj("natural", "ok")
        )
        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates={"known_cmd": {}}
        )

        result = await adp.dispatch(
            "tell me about hiring trends", {"company_id": "t1"}
        )

        svc.analyze_natural_query.assert_called_once_with(
            "tell me about hiring trends", {"company_id": "t1"}
        )
        svc.execute_command.assert_not_called()
        assert result["success"] is True


# ─────────────────────────────────────────────────────────────────────────────
# Exception handling
# ─────────────────────────────────────────────────────────────────────────────


class TestExceptionHandling:
    @pytest.mark.asyncio
    async def test_execute_command_exception_returns_failure(self):
        svc = MagicMock()
        svc.execute_command = AsyncMock(side_effect=RuntimeError("backend down"))
        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates={"cmd": {}}
        )

        result = await adp.dispatch("cmd", {"company_id": "t1"})

        assert result["success"] is False
        assert "backend down" in result["error"]

    @pytest.mark.asyncio
    async def test_natural_query_exception_returns_failure(self):
        svc = MagicMock()
        svc.analyze_natural_query = AsyncMock(side_effect=ValueError("invalid"))
        adp = AnalyticsDispatchService(
            analytics_service=svc, command_templates={}  # nada match
        )

        result = await adp.dispatch("anything", {"company_id": "t1"})

        assert result["success"] is False
        assert "invalid" in result["error"]


# ─────────────────────────────────────────────────────────────────────────────
# is_template_command helper
# ─────────────────────────────────────────────────────────────────────────────


class TestIsTemplateCommand:
    def test_returns_true_for_template_command(self):
        adp = AnalyticsDispatchService(
            analytics_service=MagicMock(),
            command_templates={"hiring_funnel": {}, "salary": {}},
        )
        assert adp.is_template_command("hiring_funnel") is True
        assert adp.is_template_command("salary") is True

    def test_returns_false_for_unknown_command(self):
        adp = AnalyticsDispatchService(
            analytics_service=MagicMock(),
            command_templates={"hiring_funnel": {}},
        )
        assert adp.is_template_command("random_query") is False
