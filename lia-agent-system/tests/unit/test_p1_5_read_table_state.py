"""
tests/unit/test_p1_5_read_table_state.py

P1-5 (2026-06-18): read_table_state tool — ContextVar bridge
TDD Red→Green: sensor que a tool lê view_context via ContextVar e retorna
os campos esperados.
"""
import asyncio
from unittest.mock import AsyncMock

import pytest


def test_read_table_state_empty_context():
    """Com ContextVar vazio, retorna campos com defaults."""
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        _wrap_read_table_state,
    )
    from app.middleware.auth_enforcement import _lia_view_context

    # Garante ContextVar vazio para este teste
    token = _lia_view_context.set(None)
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _wrap_read_table_state()
        )
    finally:
        _lia_view_context.reset(token)

    assert result["success"] is True
    data = result["data"]
    assert data["active_filters"] == []
    assert data["pagination"] is None
    assert data["active_modal"] is None
    assert data["page_type"] is None


def test_read_table_state_with_full_view_context():
    """Com ContextVar populado, retorna dados corretos."""
    from app.domains.recruiter_assistant.agents.ui_tool_registry import (
        _wrap_read_table_state,
    )
    from app.middleware.auth_enforcement import _lia_view_context

    view_ctx = {
        "page_type": "candidates",
        "active_filters": ["senior", "backend"],
        "filters_active": {"seniority": "senior", "tech": "backend"},
        "active_modal": "bulk-action",
        "pagination_state": {
            "current_page": 3,
            "total_pages": 10,
            "page_size": 20,
            "total_items": 198,
        },
        "entity_focus": {"type": "candidate", "id": "abc-123", "label": "João Silva"},
        "visible_ids": ["id1", "id2", "id3"],
        "captured_at": "2026-06-18T10:00:00Z",
    }

    token = _lia_view_context.set(view_ctx)
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _wrap_read_table_state()
        )
    finally:
        _lia_view_context.reset(token)

    assert result["success"] is True
    data = result["data"]
    assert data["page_type"] == "candidates"
    assert data["active_filters"] == ["senior", "backend"]
    assert data["active_modal"] == "bulk-action"
    assert data["pagination"]["current_page"] == 3
    assert data["pagination"]["total_items"] == 198
    assert data["entity_focus"]["id"] == "abc-123"
    assert data["visible_ids_count"] == 3
    assert data["captured_at"] == "2026-06-18T10:00:00Z"


def test_read_table_state_registered_in_ui_tools():
    """read_table_state aparece na lista de get_ui_tools()."""
    from app.domains.recruiter_assistant.agents.ui_tool_registry import get_ui_tools

    tools = get_ui_tools()
    names = [t.name for t in tools]
    assert "read_table_state" in names, (
        f"read_table_state ausente de get_ui_tools(). Presentes: {names}"
    )


def test_read_table_state_in_interface_category():
    """read_table_state está registrado como INTERFACE em categories.py."""
    from app.tools.categories import TOOL_TO_CATEGORY, ToolCategory

    assert "read_table_state" in TOOL_TO_CATEGORY, (
        "read_table_state ausente de TOOL_TO_CATEGORY"
    )
    assert TOOL_TO_CATEGORY["read_table_state"] == ToolCategory.INTERFACE
