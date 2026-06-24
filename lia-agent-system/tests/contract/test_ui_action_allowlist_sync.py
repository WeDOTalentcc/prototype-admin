"""
Contract sensor: all BE ui_action allowlists must be in sync with FE canonical list.
Prevents silent filtering of actions that the FE knows how to handle.

FE canonical source: plataforma-lia/src/types/ui-action.ts GLOBAL_UI_ACTION_TYPES
"""

FE_CANONICAL: frozenset = frozenset({
    "navigate_to",
    "open_modal",
    "close_modal",
    "open_offer_review",
    "wizard_step",
    "open_panel",
    "close_panel",
    "scroll_to",
    "settings_open_tab",
    "open_communication_modal",
    "open_schedule_modal",
    "open_screening_modal",
    "apply_table_state",
    "select_rows",
    "bulk_execute",
    "start_wizard_seeded",
})


def test_actionable_allowlist_covers_all_fe_types():
    from app.orchestrator.execution.agentic_loop import _ACTIONABLE_TOOL_UI_ACTIONS
    missing = FE_CANONICAL - _ACTIONABLE_TOOL_UI_ACTIONS
    assert not missing, (
        f"_ACTIONABLE_TOOL_UI_ACTIONS is missing {missing} -- "
        f"these actions will be silently filtered and never reach the FE"
    )


def test_fe_tool_ui_actions_matches_actionable():
    from app.orchestrator.execution.agentic_loop import _ACTIONABLE_TOOL_UI_ACTIONS
    from app.orchestrator.execution.main_orchestrator import _FE_TOOL_UI_ACTIONS
    fe_set = frozenset(_FE_TOOL_UI_ACTIONS)
    missing = _ACTIONABLE_TOOL_UI_ACTIONS - fe_set
    assert not missing, (
        f"_FE_TOOL_UI_ACTIONS is missing {missing} from canonical allowlist -- "
        f"supervisor path will silently filter these"
    )


def test_fallback_actionable_matches_canonical():
    from app.shared.ui_action_sink import _FALLBACK_ACTIONABLE
    from app.orchestrator.execution.agentic_loop import _ACTIONABLE_TOOL_UI_ACTIONS
    assert _FALLBACK_ACTIONABLE == _ACTIONABLE_TOOL_UI_ACTIONS, (
        f"_FALLBACK_ACTIONABLE drifted from canonical. "
        f"Missing: {_ACTIONABLE_TOOL_UI_ACTIONS - _FALLBACK_ACTIONABLE}, "
        f"Extra: {_FALLBACK_ACTIONABLE - _ACTIONABLE_TOOL_UI_ACTIONS}"
    )


def test_global_ui_action_types_covers_fe():
    from app.shared.websocket.ws_message_schemas import GLOBAL_UI_ACTION_TYPES
    be_set = frozenset(GLOBAL_UI_ACTION_TYPES)
    missing = FE_CANONICAL - be_set
    assert not missing, (
        f"GLOBAL_UI_ACTION_TYPES is missing {missing} from FE canonical"
    )


def test_no_be_only_types():
    """_ACTIONABLE is allowed to have PAGE_SPECIFIC_UI_ACTION_TYPES beyond FE_CANONICAL.
    GLOBAL_UI_ACTION_TYPES (WebSocket schema) must equal FE_CANONICAL exactly (no extras).
    Updated 2026-06-20: canonical now has two tiers (global + page-specific).
    """
    from app.orchestrator.execution.agentic_loop import _ACTIONABLE_TOOL_UI_ACTIONS
    from app.shared.websocket.ws_message_schemas import GLOBAL_UI_ACTION_TYPES
    from app.shared.ui_action_canonical import PAGE_SPECIFIC_UI_ACTION_TYPES

    # _ACTIONABLE = FE_CANONICAL + PAGE_SPECIFIC -- all are legitimate.
    # Anything beyond that would be unrecognized by both FE tiers.
    expected_actionable = FE_CANONICAL | PAGE_SPECIFIC_UI_ACTION_TYPES
    be_only_actionable = _ACTIONABLE_TOOL_UI_ACTIONS - expected_actionable
    assert not be_only_actionable, (
        f"BE-only in _ACTIONABLE (not in global OR page-specific canonical): {be_only_actionable}"
    )

    # GLOBAL_UI_ACTION_TYPES (WS schema) must equal FE_CANONICAL exactly.
    # Page-specific types are NOT in the WS schema (they flow via ChatResponse.ui_action only).
    be_only_global = frozenset(GLOBAL_UI_ACTION_TYPES) - FE_CANONICAL
    assert not be_only_global, f"BE-only in GLOBAL_UI_ACTION_TYPES (WS schema): {be_only_global}"
