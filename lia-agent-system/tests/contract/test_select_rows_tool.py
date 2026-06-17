"""Fase 2 — select_rows tool (surface candidates closure).
Sensor: (1) emite ui_action select_rows com params corretos; (2) modos set/add/clear;
(3) validação fail-high (mode inválido, ids ausentes pra set/add); (4) no HITL gate;
(5) tool em get_table_state_tools; (6) na allowlist do agentic_loop.
"""
from __future__ import annotations
import asyncio
import inspect
import pytest
from unittest.mock import patch


# --- fixture de tenant ---
@pytest.fixture
def _tenant():
    with patch(
        "app.shared.runtime_context.RuntimeContext.from_contextvars",
        return_value=type("C", (), {"company_id": "test-co-001"})(),
    ):
        yield


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSelectRowsTool:

    def test_mode_set_emits_correct_action(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="set",
            candidate_ids=["id-1", "id-2"],
            company_id="test-co-001",
        ))
        assert result["success"] is True
        data = result["data"]
        assert data["ui_action"] == "select_rows"
        params = data["ui_action_params"]
        assert params["surface"] == "candidates"
        assert params["mode"] == "set"
        assert params["ids"] == ["id-1", "id-2"]

    def test_mode_clear_emits_correct_action(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="clear",
            company_id="test-co-001",
        ))
        assert result["success"] is True
        data = result["data"]
        assert data["ui_action"] == "select_rows"
        params = data["ui_action_params"]
        assert params["mode"] == "clear"
        # clear: ids não deve aparecer nos params
        assert "ids" not in params

    def test_mode_add_emits_correct_action(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="add",
            candidate_ids=["id-3"],
            company_id="test-co-001",
        ))
        assert result["success"] is True
        params = result["data"]["ui_action_params"]
        assert params["mode"] == "add"
        assert params["ids"] == ["id-3"]

    def test_invalid_mode_rejected(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="delete",
            company_id="test-co-001",
        ))
        assert result["success"] is False
        assert "mode" in result.get("error", "").lower() or "mode" in result.get("message", "").lower()

    def test_ids_required_for_set(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="set",
            company_id="test-co-001",
        ))
        assert result["success"] is False

    def test_ids_required_for_add(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="add",
            candidate_ids=[],
            company_id="test-co-001",
        ))
        assert result["success"] is False

    def test_too_many_ids_rejected(self, _tenant):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            _wrap_select_rows,
        )
        big_list = [f"id-{i}" for i in range(201)]
        result = _run(_wrap_select_rows(
            surface="candidates",
            mode="set",
            candidate_ids=big_list,
            company_id="test-co-001",
        ))
        assert result["success"] is False
        combined = result.get("error", "") + result.get("message", "")
        assert "200" in combined or "máximo" in combined.lower() or "max" in combined.lower()

    def test_tool_in_get_table_state_tools(self):
        from app.domains.recruiter_assistant.agents.ui_tool_registry import (
            get_table_state_tools,
        )
        names = [t.name for t in get_table_state_tools()]
        assert "select_rows" in names

    def test_tool_in_actionable_allowlist(self):
        from app.orchestrator.execution.agentic_loop import (
            _ACTIONABLE_TOOL_UI_ACTIONS,
        )
        assert "select_rows" in _ACTIONABLE_TOOL_UI_ACTIONS

    def test_not_hitl_gated(self):
        """select_rows é estado UI puro — sem HITL gate (hitl_preflight)."""
        import inspect
        from app.domains.recruiter_assistant.agents import ui_tool_registry
        source = inspect.getsource(ui_tool_registry)
        # Extrair só a função _wrap_select_rows
        lines = source.split("\n")
        in_func = False
        func_lines = []
        for line in lines:
            if "async def _wrap_select_rows" in line:
                in_func = True
            if in_func:
                func_lines.append(line)
                # Parar quando encontrar próxima definição de função/classe
                if len(func_lines) > 1 and (
                    line.startswith("async def ") or
                    line.startswith("def ") or
                    line.startswith("class ")
                ) and "select_rows" not in line:
                    break
        func_source = "\n".join(func_lines)
        assert "hitl_preflight" not in func_source, (
            "select_rows é estado UI puro — não deve ter HITL gate"
        )
