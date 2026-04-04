/**
 * Tests — useCandidateSelection
 *
 * Covers:
 * - Initial state (empty selection)
 * - Toggle selection (add / remove)
 * - Shift-click range selection
 * - Deselect a candidate
 * - Toggle select-all / deselect-all
 * - Clear selection
 * - isSelected predicate
 * - selectedCount accuracy
 * - lastSelectedIndex tracking
 */
import { renderHook, act } from '@testing-library/react'
import { useState, useCallback, useRef } from 'react'

let _selectedCandidates = new Set<string>()
let _lastSelectedIndex: number | null = null

vi.mock('@/stores/candidates-store', () => {
  return {
    useCandidatesStore: (selector: (s: Record<string, unknown>) => unknown) => {
      const state = {
        selectedCandidates: _selectedCandidates,
        lastSelectedIndex: _lastSelectedIndex,
        setSelectedCandidates: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => {
          if (typeof v === 'function') {
            _selectedCandidates = v(_selectedCandidates)
          } else {
            _selectedCandidates = v
          }
        },
        setLastSelectedIndex: (v: number | null) => {
          _lastSelectedIndex = v
        },
      }
      return selector(state)
    },
  }
})

import { useCandidateSelection } from '../use-candidate-selection'

const IDS = ['a', 'b', 'c', 'd', 'e']

function useSelectionWithRerender() {
  const [, forceUpdate] = useState(0)
  const selection = useCandidateSelection()
  const originalSelectCandidate = selection.selectCandidate
  const originalDeselectCandidate = selection.deselectCandidate
  const originalToggleSelectAll = selection.toggleSelectAll
  const originalClearSelection = selection.clearSelection
  return {
    ...selection,
    get selectedCandidates() { return _selectedCandidates },
    get lastSelectedIndex() { return _lastSelectedIndex },
    get selectedCount() { return _selectedCandidates.size },
    isSelected: (id: string) => _selectedCandidates.has(id),
    selectCandidate: (...args: Parameters<typeof originalSelectCandidate>) => {
      originalSelectCandidate(...args)
      forceUpdate(c => c + 1)
    },
    deselectCandidate: (...args: Parameters<typeof originalDeselectCandidate>) => {
      originalDeselectCandidate(...args)
      forceUpdate(c => c + 1)
    },
    toggleSelectAll: (...args: Parameters<typeof originalToggleSelectAll>) => {
      originalToggleSelectAll(...args)
      forceUpdate(c => c + 1)
    },
    clearSelection: () => {
      originalClearSelection()
      forceUpdate(c => c + 1)
    },
  }
}

describe('useCandidateSelection', () => {
  beforeEach(() => {
    _selectedCandidates = new Set<string>()
    _lastSelectedIndex = null
  })

  // ── Initial state ─────────────────────────────────────────────────────────

  it('starts with empty selection', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    expect(result.current.selectedCandidates.size).toBe(0)
    expect(result.current.selectedCount).toBe(0)
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  it('isAllSelected is false initially', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    expect(result.current.isAllSelected).toBe(false)
  })

  // ── selectCandidate (toggle) ──────────────────────────────────────────────

  it('adds a candidate when it was not selected', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('a') })
    expect(result.current.selectedCandidates.has('a')).toBe(true)
    expect(result.current.selectedCount).toBe(1)
  })

  it('removes a candidate when it was already selected', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('a') })
    act(() => { result.current.selectCandidate('a') })
    expect(result.current.selectedCandidates.has('a')).toBe(false)
    expect(result.current.selectedCount).toBe(0)
  })

  it('tracks lastSelectedIndex when index is provided', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('b', false, 1) })
    expect(result.current.lastSelectedIndex).toBe(1)
  })

  // ── Shift-click range ─────────────────────────────────────────────────────

  it('selects a range with shift-click', () => {
    const { result } = renderHook(() => useSelectionWithRerender())

    act(() => { result.current.selectCandidate('a', false, 0, IDS) })
    act(() => { result.current.selectCandidate('d', true, 3, IDS) })

    expect(result.current.selectedCandidates.size).toBe(4)
    ;['a', 'b', 'c', 'd'].forEach(id => {
      expect(result.current.selectedCandidates.has(id)).toBe(true)
    })
    expect(result.current.selectedCandidates.has('e')).toBe(false)
  })

  it('shift-click without prior index behaves as toggle', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('c', true, 2, IDS) })
    expect(result.current.selectedCandidates.size).toBe(1)
    expect(result.current.selectedCandidates.has('c')).toBe(true)
  })

  // ── deselectCandidate ─────────────────────────────────────────────────────

  it('deselects a specific candidate', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('a') })
    act(() => { result.current.selectCandidate('b') })
    act(() => { result.current.deselectCandidate('a') })

    expect(result.current.selectedCandidates.has('a')).toBe(false)
    expect(result.current.selectedCandidates.has('b')).toBe(true)
    expect(result.current.selectedCount).toBe(1)
  })

  it('deselecting a non-selected id is a no-op', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.deselectCandidate('x') })
    expect(result.current.selectedCount).toBe(0)
  })

  // ── toggleSelectAll ───────────────────────────────────────────────────────

  it('selects all when not fully selected', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('a') })
    act(() => { result.current.toggleSelectAll(IDS) })

    expect(result.current.selectedCandidates.size).toBe(IDS.length)
    IDS.forEach(id => {
      expect(result.current.selectedCandidates.has(id)).toBe(true)
    })
  })

  it('deselects all when every id is selected', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.toggleSelectAll(IDS) })
    act(() => { result.current.toggleSelectAll(IDS) })

    expect(result.current.selectedCandidates.size).toBe(0)
  })

  it('resets lastSelectedIndex after toggleSelectAll', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('b', false, 1) })
    act(() => { result.current.toggleSelectAll(IDS) })
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  // ── clearSelection ────────────────────────────────────────────────────────

  it('clears all selections', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('a') })
    act(() => { result.current.selectCandidate('c') })
    act(() => { result.current.clearSelection() })

    expect(result.current.selectedCount).toBe(0)
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  // ── isSelected ────────────────────────────────────────────────────────────

  it('isSelected returns true for selected ids', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    act(() => { result.current.selectCandidate('d') })

    expect(result.current.isSelected('d')).toBe(true)
    expect(result.current.isSelected('a')).toBe(false)
  })

  // ── selectedCount ─────────────────────────────────────────────────────────

  it('selectedCount tracks the number of selected candidates', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    expect(result.current.selectedCount).toBe(0)

    act(() => { result.current.selectCandidate('a') })
    expect(result.current.selectedCount).toBe(1)

    act(() => { result.current.selectCandidate('b') })
    expect(result.current.selectedCount).toBe(2)

    act(() => { result.current.selectCandidate('a') })
    expect(result.current.selectedCount).toBe(1)
  })

  // ── Misc / edge-cases ─────────────────────────────────────────────────────

  it('exposes setSelectedCandidates for external overrides', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    expect(typeof result.current.setSelectedCandidates).toBe('function')
  })

  it('selectedCandidates is a Set instance', () => {
    const { result } = renderHook(() => useSelectionWithRerender())
    expect(result.current.selectedCandidates).toBeInstanceOf(Set)
  })
})
