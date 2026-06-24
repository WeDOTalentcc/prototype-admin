"""TDD: close_panel tool — simetrico ao close_ui/open_ui."""
import asyncio
import pytest
from app.domains.recruiter_assistant.agents.ui_tool_registry import (
    _wrap_close_panel,
    _build_close_panel_definition,
    get_ui_tools,
    get_open_ui_tools,
)


def test_wrap_close_panel_returns_close_panel_action():
    result = asyncio.get_event_loop().run_until_complete(_wrap_close_panel())
    assert result["success"] is True
    assert result["data"]["ui_action"] == "close_panel"
    assert result["data"]["ui_action_params"] == {}


def test_close_panel_definition_name():
    defn = _build_close_panel_definition()
    assert defn.name == "close_panel"
    assert defn.parameters["properties"] == {}
    assert defn.parameters["required"] == []


def test_get_ui_tools_includes_close_panel():
    names = [td.name for td in get_ui_tools()]
    assert "close_panel" in names
    assert "open_ui" in names
    assert "close_ui" in names


def test_get_open_ui_tools_includes_close_panel():
    names = [td.name for td in get_open_ui_tools()]
    assert "close_panel" in names
    assert "open_ui" in names
    assert "close_ui" in names
