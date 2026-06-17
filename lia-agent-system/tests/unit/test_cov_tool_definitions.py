"""Coverage tests for shared/tools modules — testing the pure get_*_tools() factory functions.

Targets:
  - app/shared/tools/proactive_tools.py  (95 stmts)
  - app/shared/tools/predictive_tools.py (212 stmts)
"""
import pytest


# ===========================================================================
# app/shared/tools/proactive_tools.py
# ===========================================================================
from app.shared.tools.proactive_tools import get_proactive_tools


class TestProactiveTools:
    def test_returns_list(self):
        tools = get_proactive_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tool_names(self):
        tools = get_proactive_tools()
        names = {t.name for t in tools}
        assert "check_stagnant_candidates" in names
        assert "check_pending_offers" in names
        assert "check_overdue_tasks" in names
        assert "check_pipeline_risks" in names

    def test_tool_has_description(self):
        tools = get_proactive_tools()
        for t in tools:
            assert t.description
            assert len(t.description) > 5

    def test_tool_has_parameters(self):
        tools = get_proactive_tools()
        for t in tools:
            assert t.parameters is not None
            assert "type" in t.parameters

    def test_tool_has_function(self):
        tools = get_proactive_tools()
        for t in tools:
            assert callable(t.function)

    def test_all_four_tools(self):
        tools = get_proactive_tools()
        assert len(tools) == 4


# ===========================================================================
# app/shared/tools/predictive_tools.py
# ===========================================================================
from app.shared.tools.predictive_tools import (
    get_predictive_tools,
    STAGE_ORDER,
)


class TestPredictiveTools:
    def test_returns_list(self):
        tools = get_predictive_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0

    def test_tool_names(self):
        tools = get_predictive_tools()
        names = {t.name for t in tools}
        assert "predict_dropout_risk" in names
        assert "predict_time_to_fill" in names
        assert "get_pipeline_forecast" in names
        assert "get_strategic_recommendations" in names

    def test_tool_has_description(self):
        tools = get_predictive_tools()
        for t in tools:
            assert t.description
            assert len(t.description) > 5

    def test_tool_has_parameters(self):
        tools = get_predictive_tools()
        for t in tools:
            assert t.parameters is not None
            assert "type" in t.parameters

    def test_tool_has_function(self):
        tools = get_predictive_tools()
        for t in tools:
            assert callable(t.function)

    def test_all_four_tools(self):
        tools = get_predictive_tools()
        assert len(tools) == 4

    def test_stage_order_defined(self):
        assert isinstance(STAGE_ORDER, list)
        assert len(STAGE_ORDER) > 0
        assert "hired" in STAGE_ORDER
        assert "applied" in STAGE_ORDER

    def test_stage_order_logical_progression(self):
        # applied should come before hired
        applied_idx = STAGE_ORDER.index("applied")
        hired_idx = STAGE_ORDER.index("hired")
        assert applied_idx < hired_idx
