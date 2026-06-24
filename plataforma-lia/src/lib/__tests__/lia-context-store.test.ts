/**
 * Tests for lia-context-store.ts — TDD P0-2 (2026-06-18)
 *
 * These are the RED tests written BEFORE the implementation.
 * They validate that write APIs correctly populate getLiaContextSnapshot().
 *
 * Sensor: if any test here fails, a write path has regressed.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import {
  setLiaModal,
  setLiaPagination,
  setLiaFilters,
  getLiaContextSnapshot,
} from '../lia-context-store'

// Reset singleton state between tests — module-level singleton must be clean
function resetStore() {
  setLiaModal(null)
  setLiaPagination(null)
  setLiaFilters(null)
}

describe('lia-context-store', () => {
  beforeEach(resetStore)

  // ── active_modal ──────────────────────────────────────────────────────────

  it('snapshot inclui active_modal quando modal está aberto', () => {
    setLiaModal('kanban-transition')
    const snap = getLiaContextSnapshot()
    expect(snap.active_modal).toBe('kanban-transition')
  })

  it('snapshot NÃO inclui active_modal quando null', () => {
    setLiaModal(null)
    const snap = getLiaContextSnapshot()
    expect('active_modal' in snap).toBe(false)
  })

  it('setLiaModal sobrescreve valor anterior', () => {
    setLiaModal('modal-a')
    setLiaModal('modal-b')
    expect(getLiaContextSnapshot().active_modal).toBe('modal-b')
  })

  // ── active_filters ────────────────────────────────────────────────────────

  it('snapshot inclui active_filters após setLiaFilters com valores', () => {
    setLiaFilters(['busca: "python"', 'score ≥ 70'])
    const snap = getLiaContextSnapshot()
    expect(snap.active_filters).toEqual(['busca: "python"', 'score ≥ 70'])
  })

  it('snapshot NÃO inclui active_filters quando setLiaFilters(null)', () => {
    setLiaFilters(null)
    const snap = getLiaContextSnapshot()
    expect('active_filters' in snap).toBe(false)
  })

  it('snapshot NÃO inclui active_filters quando array vazio', () => {
    setLiaFilters([])
    const snap = getLiaContextSnapshot()
    expect('active_filters' in snap).toBe(false)
  })

  it('setLiaFilters limpa filtros anteriores ao receber null', () => {
    setLiaFilters(['busca: "python"'])
    setLiaFilters(null)
    expect('active_filters' in getLiaContextSnapshot()).toBe(false)
  })

  // ── pagination_state ──────────────────────────────────────────────────────

  it('snapshot inclui pagination_state após setLiaPagination', () => {
    const pag = { current_page: 2, total_pages: 5, page_size: 20, total_items: 98 }
    setLiaPagination(pag)
    const snap = getLiaContextSnapshot()
    expect(snap.pagination_state).toEqual(pag)
  })

  it('snapshot NÃO inclui pagination_state quando null', () => {
    setLiaPagination(null)
    const snap = getLiaContextSnapshot()
    expect('pagination_state' in snap).toBe(false)
  })

  // ── captured_at ───────────────────────────────────────────────────────────

  it('snapshot sempre inclui captured_at como string ISO', () => {
    const snap = getLiaContextSnapshot()
    expect(typeof snap.captured_at).toBe('string')
    expect(() => new Date(snap.captured_at)).not.toThrow()
  })
})
