"""
Canonical registry of UI action type strings -- single source of truth.

P-SSOT: every allowlist in the system MUST import from here.
Adding a string here is the ONLY place that matters for backend gate coverage.

Two tiers:
- GLOBAL_UI_ACTION_TYPES_CORE  -- 16 types handled by useUIAction.ts global switch
- PAGE_SPECIFIC_UI_ACTION_TYPES -- 3 types dispatched via lia:unhandled_ui_action
                                   to page-specific handlers (Kanban, Talent, Wizard)
- ALL_ACTIONABLE_UI_ACTION_TYPES -- union; what the backend gates check

TypeScript sync: GLOBAL_UI_ACTION_TYPES_CORE must match the GlobalUIAction discriminated
union in plataforma-lia/src/types/ui-action.ts. Enforced by:
  python3 scripts/check_ui_action_ts_sync.py   (CI: warn-only)
"""
from __future__ import annotations

# 16 types handled by the global useUIAction.ts switch.
# These are reflected in the TypeScript GlobalUIAction discriminated union.
GLOBAL_UI_ACTION_TYPES_CORE: frozenset[str] = frozenset({
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

# 3 page-specific types that reach the frontend via ChatResponse ui_action field
# but are handled by page-level listeners on the lia:unhandled_ui_action CustomEvent
# (default branch in useUIAction.ts switch -> dispatchOrEmit).
# They are NOT in the TypeScript GlobalUIAction union -- the TS switch default handles them.
PAGE_SPECIFIC_UI_ACTION_TYPES: frozenset[str] = frozenset({
    "suggest_pipeline_template",   # WizardPipelineTemplateCard (useWizardFlow.ts)
    "move_candidate",              # Kanban stage move (useKanbanLIAHandlers.ts)
    "switch_search_mode",          # Talent funnel toggle (useLIAQuickActions.ts)
})

# Union: every string that is ALLOWED to pass through the backend gates.
ALL_ACTIONABLE_UI_ACTION_TYPES: frozenset[str] = (
    GLOBAL_UI_ACTION_TYPES_CORE | PAGE_SPECIFIC_UI_ACTION_TYPES
)
