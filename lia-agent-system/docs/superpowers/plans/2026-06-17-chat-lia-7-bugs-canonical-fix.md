# Chat LIA — 7 Bugs Canonical Fix (P0+P1+P2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Fix 7 chat/UI bugs reported by Paulo on 2026-06-17, all stemming from 3 systemic defects: (1) ui_action allowlist filters 10 of 16 action types silently, (2) entity focus never clears on route change, (3) inline chat positioning/race condition.

**Architecture:** Fix-at-producer pattern per CLAUDE.md. Three BE allowlists must sync with FE canonical list. Entity lifecycle needs route-change cleanup. Inline chat needs DOM event ordering guard + viewport-aware positioning.

**Tech Stack:** Python (FastAPI, LangGraph), TypeScript (Next.js, React, Zustand), Replit SSH

**Constraints:**
- All code lives on Replit SSH replit-wedo-0405 at /home/runner/workspace/
- Branch: feat/benefits-prv-canonical
- Commits: ALWAYS pathspec git commit -- paths (REGRA 8)
- TDD: Red-Green-Refactor
- No git push without Paulo explicit permission

---

## Task 1: P0 — Expand _ACTIONABLE_TOOL_UI_ACTIONS allowlist (BE producer fix)

**Context:** The _ACTIONABLE_TOOL_UI_ACTIONS frozenset in agentic_loop.py:109 is the SINGLE producer that gates which ui_action types survive from LLM tool results to the FE. Currently has 6 types; FE canonical list has 16. Actions like settings_open_tab, open_panel, close_panel, close_modal, open_offer_review, wizard_step, scroll_to are filtered silently. This is the root cause of "LIA said she navigated but nothing happened".

Three downstream lists must sync: _FE_TOOL_UI_ACTIONS (main_orchestrator.py:276), _FALLBACK_ACTIONABLE (ui_action_sink.py:26), GLOBAL_UI_ACTION_TYPES (ws_message_schemas.py:217).

**Files:**
- Modify: lia-agent-system/app/orchestrator/execution/agentic_loop.py:109-111
- Modify: lia-agent-system/app/orchestrator/execution/main_orchestrator.py:276-280
- Modify: lia-agent-system/app/shared/ui_action_sink.py:26-28
- Modify: lia-agent-system/app/shared/websocket/ws_message_schemas.py:217-228
- Modify: lia-agent-system/tests/unit/orchestrator/test_ui_action_schema.py:30-38
- Create: lia-agent-system/tests/contract/test_ui_action_allowlist_sync.py

### Steps

- [ ] 1.1: Create contract test tests/contract/test_ui_action_allowlist_sync.py with 5 tests validating all 4 BE allowlists match FE canonical (16 types)
- [ ] 1.2: Run test — expect FAIL (10 missing types in _ACTIONABLE)
- [ ] 1.3: Expand _ACTIONABLE_TOOL_UI_ACTIONS in agentic_loop.py:109 from 6 to 16 types
- [ ] 1.4: Sync _FE_TOOL_UI_ACTIONS in main_orchestrator.py:276 from 3 to 16 types
- [ ] 1.5: Sync _FALLBACK_ACTIONABLE in ui_action_sink.py:26 from 4 to 16 types
- [ ] 1.6: Add 5 missing types to GLOBAL_UI_ACTION_TYPES in ws_message_schemas.py:217 (close_modal, close_panel, open_communication_modal, open_schedule_modal, open_screening_modal, start_wizard_seeded)
- [ ] 1.7: Update test_ui_action_schema.py:30 to expect 16 types instead of 8
- [ ] 1.8: Run all tests — expect GREEN
- [ ] 1.9: Commit with pathspec (6 files)

The 16 FE canonical types (from plataforma-lia/src/types/ui-action.ts):
navigate_to, open_modal, close_modal, open_offer_review, wizard_step, open_panel, close_panel, scroll_to, settings_open_tab, open_communication_modal, open_schedule_modal, open_screening_modal, apply_table_state, select_rows, bulk_execute, start_wizard_seeded

---

## Task 2: P1 — Fix stale focusedJob on route change (FE entity lifecycle)

**Context:** useFocusedJobStore (Zustand + localStorage persist) is set when user opens job kanban (JobDetailClient.tsx) but NEVER cleared on unmount or route change. Sidebar "Em Foco" card shows old job. LIA uses stale focusedJob as context.

Additionally, entityContext in lia-float-context.tsx is never cleared on route change — chat holds onto old entity.

**Files:**
- Modify: plataforma-lia/src/app/[locale]/(dashboard)/jobs/[id]/JobDetailClient.tsx:125-140
- Modify: plataforma-lia/src/contexts/lia-float-context.tsx:389-399

### Steps

- [ ] 2.1: In JobDetailClient.tsx, add useEffect cleanup that calls clearFocusedJob() on unmount. Destructure clearFocusedJob from useFocusedJobStore.
- [ ] 2.2: In lia-float-context.tsx:389, modify the route-change useEffect to also set entityContext to null when pathname changes.
- [ ] 2.3: Run tsc --noEmit and eslint on both files — expect no errors
- [ ] 2.4: Commit with pathspec (2 files, GIT_LITERAL_PATHSPECS=1 for [locale]/[id])

---

## Task 3: P1 — open_ui fail-loud for empty capability

**Context:** LLM sometimes sends capability="" despite enum constraint. Handler should fail loud.

**Files:**
- Modify: lia-agent-system/app/domains/recruiter_assistant/agents/ui_tool_registry.py
- Create: lia-agent-system/tests/unit/test_open_ui_empty_capability.py

### Steps

- [ ] 3.1: Create test with 2 cases: empty string and whitespace-only capability
- [ ] 3.2: Run test — expect FAIL
- [ ] 3.3: Add guard at top of _wrap_open_ui: if not capability.strip(), return error dict
- [ ] 3.4: Run test — expect GREEN
- [ ] 3.5: Run existing test_open_ui_tool.py — expect no regression
- [ ] 3.6: Commit with pathspec (2 files)

---

## Task 4: P1 — Add missing i18n key kanban.scheduleMessage

**Context:** Commit 6db3f958 added schedule messages feature but missed the i18n key.

**Files:**
- Modify: plataforma-lia/messages/pt-BR.json
- Modify: plataforma-lia/messages/en.json

### Steps

- [ ] 4.1: Add "scheduleMessage": "Agendar mensagem" to kanban namespace in pt-BR.json
- [ ] 4.2: Add "scheduleMessage": "Schedule message" to kanban namespace in en.json
- [ ] 4.3: Run npm run lint:i18n and verify kanban.scheduleMessage violation gone
- [ ] 4.4: Commit with pathspec (2 files)

---

## Task 5: P1 — Inline chat race condition + positioning

**Context:** Clicking on candidate card text fires card onClick (opening preview), killing text selection. Event chain: mousedown-mouseup-click. Also, inline chat popover overflows right panel and has no vertical flip.

**Files:**
- Modify: plataforma-lia/src/components/pages/pipeline-overview-page.tsx:1590
- Modify: plataforma-lia/src/components/shared/GlobalSelectionChat.tsx:68-92

### Steps

- [ ] 5.1: In pipeline-overview-page.tsx, wrap candidate card onClick with selection guard: if window.getSelection() is not collapsed, return early
- [ ] 5.2: In GlobalSelectionChat.tsx, account for right panel width in left clamping (query for panel element or use fixed offset)
- [ ] 5.3: Add vertical flip: when rect.top < 200, position chat below selection instead of above
- [ ] 5.4: Run tsc --noEmit and eslint — expect clean
- [ ] 5.5: Commit with pathspec (2 files)

---

## Task 6: P2 — Fix remaining 101 i18n violations

**Context:** i18n sensor reports 102 violations total (1 fixed in Task 4). Remaining in 3 files:
- src/app/candidate/status/[token]/page.tsx — 74 violations (candidateStatus.*)
- src/app/candidate/status/page.tsx — 18 violations (candidateStatus.*)
- src/components/settings/consumo/BillingTab.tsx — 8 violations (settings.billing.errors.*)

**Files:**
- Modify: plataforma-lia/messages/pt-BR.json
- Modify: plataforma-lia/messages/en.json

### Steps

- [ ] 6.1: Get exact violation list with npm run lint:i18n:json
- [ ] 6.2: Add all candidateStatus.* keys to both locales (92 keys)
- [ ] 6.3: Add all settings.billing.errors.* keys to both locales (8 keys)
- [ ] 6.4: Run npm run lint:i18n:blocking — expect exit 0
- [ ] 6.5: Commit with pathspec (2 files)

---

## Task 7: Final verification

- [ ] 7.1: Run BE contract + unit tests for ui_action
- [ ] 7.2: Run FE tsc + i18n blocking
- [ ] 7.3: Verify commit log shows clean atomic commits
