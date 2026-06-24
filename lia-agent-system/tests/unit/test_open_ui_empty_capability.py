"""Sensor: open_ui tool rejects empty/blank capability with clear error."""
import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_open_ui_rejects_empty_capability():
    from app.domains.recruiter_assistant.agents.ui_tool_registry import _wrap_open_ui
    result = await _wrap_open_ui(capability="", company_id="test-co")
    assert result["success"] is False
    assert "required" in result["message"].lower() or "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_open_ui_rejects_whitespace_capability():
    from app.domains.recruiter_assistant.agents.ui_tool_registry import _wrap_open_ui
    result = await _wrap_open_ui(capability="   ", company_id="test-co")
    assert result["success"] is False
    assert "required" in result["message"].lower() or "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_open_ui_rejects_none_capability():
    from app.domains.recruiter_assistant.agents.ui_tool_registry import _wrap_open_ui
    result = await _wrap_open_ui(capability=None, company_id="test-co")
    assert result["success"] is False
