"""Sensor: apply_table_state alcancavel no caminho supervisor (Phase 1.5).

Garante (1) registro no tool_registry global com categoria canonica (sensor J:
sem OTHER), (2) apply_table_state na constante de ui_actions propagadas pro FE
pelo MainOrchestrator.
"""
from __future__ import annotations


def test_apply_table_state_mapped_to_canonical_category():
    from app.tools.categories import category_for_tool, ToolCategory
    assert category_for_tool("apply_table_state") == ToolCategory.INTERFACE


def test_register_ui_tools_global_registers_apply_table_state():
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        register_ui_tools_global,
    )
    from app.tools.registry import tool_registry

    n = register_ui_tools_global()
    assert n == 2, "registra open_ui + apply_table_state"
    for name in ("apply_table_state", "open_ui"):
        td = tool_registry._tools.get(name)
        assert td is not None, f"{name} deveria estar no registry global"
        from app.tools.categories import ToolCategory as _TC
        assert td.category == _TC.INTERFACE, "sensor J: categoria INTERFACE (nao OTHER)"
        assert td.handler is not None


def test_apply_table_state_in_fe_propagated_actions():
    from app.orchestrator.execution.main_orchestrator import _FE_TOOL_UI_ACTIONS
    assert "apply_table_state" in _FE_TOOL_UI_ACTIONS
    # open_ui (modal/nav) continua propagando
    assert "open_modal" in _FE_TOOL_UI_ACTIONS
    assert "navigate_to" in _FE_TOOL_UI_ACTIONS
