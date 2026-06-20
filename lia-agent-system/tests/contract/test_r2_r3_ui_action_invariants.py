"""
R2 (P-SSOT) + R3 (P-FAILLOUD) — UI action invariants.

T-R2-a: the 3 page-specific strings ARE in gate 2 (reach FE). Fails now.
T-R2-b: gate1 and gate2 both derive from canonical. Fails now (canonical doesnt exist).
T-R2-c: GLOBAL_UI_ACTION_TYPES subset _UI_ACTION_PARAMS_BY_TYPE. Fails now (5 missing).
T-R3-a: unknown ui_action at gate 1 -> logger.warning called. Fails now (silent drop).
T-sync: py canonical == ts GlobalUIAction types. Sensor exists and passes.
"""
from __future__ import annotations
import pytest


_PAGE_SPECIFIC = frozenset({
    "suggest_pipeline_template",
    "move_candidate",
    "switch_search_mode",
})


def test_r2a_gate2_includes_page_specific_actions():
    """Gate 2 (_FE_TOOL_UI_ACTIONS) must include the 3 page-specific actions.
    They have FE handlers via lia:unhandled_ui_action -- they must reach the FE."""
    from app.orchestrator.execution.main_orchestrator import _FE_TOOL_UI_ACTIONS
    missing = _PAGE_SPECIFIC - set(_FE_TOOL_UI_ACTIONS)
    assert not missing, (
        f"Gate 2 silently drops {missing}. These have FE handlers via lia:unhandled_ui_action "
        "but never reach the frontend. Add them to _FE_TOOL_UI_ACTIONS."
    )


def test_r2b_gate1_gate2_from_single_canonical_source():
    """gate1 and gate2 must derive from ONE canonical source -- divergence is structurally impossible."""
    from app.shared.ui_action_canonical import ALL_ACTIONABLE_UI_ACTION_TYPES  # must exist
    from app.orchestrator.execution.agentic_loop import _ACTIONABLE_TOOL_UI_ACTIONS
    from app.orchestrator.execution.main_orchestrator import _FE_TOOL_UI_ACTIONS

    assert _ACTIONABLE_TOOL_UI_ACTIONS == ALL_ACTIONABLE_UI_ACTION_TYPES, (
        "gate1 diverges from canonical"
    )
    assert set(_FE_TOOL_UI_ACTIONS) == ALL_ACTIONABLE_UI_ACTION_TYPES, (
        "gate2 diverges from canonical"
    )


def test_r2c_param_schema_covers_all_global_types():
    """Every string in GLOBAL_UI_ACTION_TYPES must have an entry in _UI_ACTION_PARAMS_BY_TYPE."""
    from app.shared.websocket.ws_message_schemas import (
        GLOBAL_UI_ACTION_TYPES,
        _UI_ACTION_PARAMS_BY_TYPE,
    )
    missing = [t for t in GLOBAL_UI_ACTION_TYPES if t not in _UI_ACTION_PARAMS_BY_TYPE]
    assert not missing, (
        f"No param schema for: {missing}. Add minimal None entries to _UI_ACTION_PARAMS_BY_TYPE."
    )


@pytest.mark.asyncio
async def test_r3a_gate1_unknown_action_logs_warning():
    """Unknown ui_action string arriving at gate 1 must emit logger.warning (not silent drop)."""
    from unittest.mock import patch, MagicMock

    # Build a minimal ToolResult-like object that _extract_tool_directive expects
    fake_result = MagicMock()
    fake_result.success = True

    # Find exact dict structure by reading what _extract_tool_directive checks
    # Based on agentic_loop.py: it reads result.data -> payload -> ui_action
    fake_result.result = {
        "data": {"ui_action": "totally_unknown_string_xyz", "other": "data"},
    }

    with patch("app.orchestrator.execution.agentic_loop.logger") as mock_logger:
        from app.orchestrator.execution.agentic_loop import _extract_tool_directive
        result = _extract_tool_directive(fake_result)

    assert result is None, "Unknown action must still return None (not passed through)"
    # Warning MUST be emitted -- not silent
    assert mock_logger.warning.called or mock_logger.warn.called, (
        "Gate 1 silently drops unknown ui_action. Must log warning for observability."
    )


def test_sync_canonical_py_matches_ts_union():
    """Sync sensor: GLOBAL_UI_ACTION_TYPES_CORE (py) must match GlobalUIAction union (ts).
    Run via: python3 scripts/check_ui_action_ts_sync.py"""
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "scripts/check_ui_action_ts_sync.py"],
        cwd="/home/runner/workspace/lia-agent-system",
        capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"TS sync sensor failed:\n{result.stdout}\n{result.stderr}"
    )
