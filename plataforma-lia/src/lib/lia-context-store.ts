/**
 * LIA Context Store — lightweight global singleton for agent context signals.
 *
 * Provides write APIs used by UI components:
 *   setLiaModal(name)          — call when any major modal opens/closes
 *   setLiaPagination(state)    — call when table pagination changes
 *   setLiaFilters(filters)     — call when active filters change (kanban, vagas)
 *
 * Read API used by getPageContext() in useChatMessages.ts:
 *   getLiaContextSnapshot()    — returns current signal values
 *
 * GAP-02-001: view_context was missing pagination, modal and filter state.
 * Backend format_view_context() already handles these fields when present.
 *
 * GAP-02-006: captured_at ISO timestamp added so BE can detect stale context
 * (e.g. user switched tabs without sending a new message). getLiaContextSnapshot()
 * always stamps the current time — it reflects when the snapshot was taken, not
 * when the last modal/pagination state was changed.
 *
 * P0-2 (2026-06-18): active_filters added. setLiaModal() and setLiaPagination()
 * were previously defined but never called (dead write paths). Now wired via:
 *   setLiaFilters → use-filters-persistence.ts + job-filters-store.ts
 *   setLiaModal   → useUniversalTransitionModal.tsx
 */

export interface LiaPaginationState {
  current_page: number
  total_pages: number
  page_size: number
  total_items: number
}

interface LiaContextState {
  active_modal: string | null
  pagination_state: LiaPaginationState | null
  active_filters: string[] | null
}

// Module-level singleton — survives React re-renders, no React dependency
const _state: LiaContextState = {
  active_modal: null,
  pagination_state: null,
  active_filters: null,
}

/** Set which modal is currently open. Pass null when all modals are closed. */
export function setLiaModal(name: string | null): void {
  _state.active_modal = name
}

/** Update pagination state when table page changes. */
export function setLiaPagination(state: LiaPaginationState | null): void {
  _state.pagination_state = state
}

/**
 * Update active filter descriptions for the current view.
 *
 * Pass a human-readable string array (e.g. ['busca: "python"', 'score ≥ 70']).
 * Pass null or empty array to clear. Backend format_view_context() renders these
 * as "Filtros ativos: ..." in the agent system prompt.
 */
export function setLiaFilters(filters: string[] | null): void {
  _state.active_filters = filters?.length ? filters : null
}

/**
 * Read current context snapshot — called by getPageContext() before each chat message.
 *
 * GAP-02-006: always includes captured_at = current ISO timestamp so the BE
 * can detect stale context (context older than 60s triggers a warning log).
 */
export function getLiaContextSnapshot(): Partial<LiaContextState> & { captured_at: string } {
  const result: Partial<LiaContextState> & { captured_at: string } = {
    captured_at: new Date().toISOString(),
  }
  if (_state.active_modal) result.active_modal = _state.active_modal
  if (_state.pagination_state) result.pagination_state = _state.pagination_state
  if (_state.active_filters?.length) result.active_filters = _state.active_filters
  return result
}
