"""
TDD Red tests for P2-1: Pipeline Stage Management tools (rename/reorder/delete).
These tests FAIL until the tools are registered in the tool_registry.
"""
import pytest


def test_rename_pipeline_stage_registered():
    """rename_pipeline_stage deve existir no tool_registry global após initialize_tools."""
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    names = tool_registry.list_tools()
    assert "rename_pipeline_stage" in names, "rename_pipeline_stage not registered"


def test_reorder_pipeline_stages_registered():
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    names = tool_registry.list_tools()
    assert "reorder_pipeline_stages" in names, "reorder_pipeline_stages not registered"


def test_delete_pipeline_stage_registered():
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    names = tool_registry.list_tools()
    assert "delete_pipeline_stage" in names, "delete_pipeline_stage not registered"


def test_pipeline_stage_tools_have_required_schema():
    from app.tools import initialize_tools
    from app.tools.registry import tool_registry
    initialize_tools()
    for name in ["rename_pipeline_stage", "reorder_pipeline_stages", "delete_pipeline_stage"]:
        td = tool_registry.get_tool(name)
        assert td is not None, f"{name} not found"
        assert td.parameters_schema.get("type") == "object"
        assert "properties" in td.parameters_schema
