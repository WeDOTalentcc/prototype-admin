/**
 * LIA Context Store — lightweight global singleton for agent context signals.
 *
 * Provides two write APIs used by UI components:
 *   setLiaModal(name)          — call when any major modal opens/closes
 *   setLiaPagination(state)    — call when table pagination changes
 *
 * Read API used by getPageContext() in useChatMessages.ts:
 *   getLiaContextSnapshot()    — returns current signal values
 *
 * GAP-02-001: view_context was missing pagination and modal state.
 * Backend format_view_context() already handles these fields when present.
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
}

// Module-level singleton — survives React re-renders, no React dependency
const _state: LiaContextState = {
  active_modal: null,
  pagination_state: null,
}

/** Set which modal is currently open. Pass null when all modals are closed. */
export function setLiaModal(name: string | null): void {
  _state.active_modal = name
}

/** Update pagination state when table page changes. */
export function setLiaPagination(state: LiaPaginationState | null): void {
  _state.pagination_state = state
}

/** Read current context snapshot — called by getPageContext() before each chat message. */
export function getLiaContextSnapshot(): Partial<LiaContextState> {
  const result: Partial<LiaContextState> = {}
  if (_state.active_modal) result.active_modal = _state.active_modal
  if (_state.pagination_state) result.pagination_state = _state.pagination_state
  return result
}
