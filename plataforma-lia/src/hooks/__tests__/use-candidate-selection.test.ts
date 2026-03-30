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
import { useCandidateSelection } from '../use-candidate-selection'

const IDS = ['a', 'b', 'c', 'd', 'e']

describe('useCandidateSelection', () => {
  // ── Initial state ─────────────────────────────────────────────────────────

  it('starts with empty selection', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(result.current.selectedCandidates.size).toBe(0)
    expect(result.current.selectedCount).toBe(0)
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  it('isAllSelected is false initially', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(result.current.isAllSelected).toBe(false)
  })

  it('isSelected returns false for any id initially', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(result.current.isSelected('candidate-1')).toBe(false)
  })

  // ── selectCandidate — basic toggle ────────────────────────────────────────

  it('selectCandidate adds a candidate to the selection', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    expect(result.current.selectedCandidates.has('a')).toBe(true)
    expect(result.current.selectedCount).toBe(1)
  })

  it('selectCandidate toggles — removes already-selected candidate', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    act(() => result.current.selectCandidate('a'))
    expect(result.current.selectedCandidates.has('a')).toBe(false)
    expect(result.current.selectedCount).toBe(0)
  })

  it('selecting multiple candidates accumulates them', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    act(() => result.current.selectCandidate('b'))
    act(() => result.current.selectCandidate('c'))
    expect(result.current.selectedCount).toBe(3)
  })

  it('isSelected returns true for selected candidate', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('x'))
    expect(result.current.isSelected('x')).toBe(true)
    expect(result.current.isSelected('y')).toBe(false)
  })

  // ── lastSelectedIndex tracking ────────────────────────────────────────────

  it('updates lastSelectedIndex when index is provided', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a', false, 2, IDS))
    expect(result.current.lastSelectedIndex).toBe(2)
  })

  it('lastSelectedIndex stays null when index is not provided', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  // ── Shift-click range selection ───────────────────────────────────────────

  it('shift-click selects a range of candidates', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('b', false, 1, IDS))
    act(() => result.current.selectCandidate('d', true, 3, IDS))
    expect(result.current.selectedCandidates.has('b')).toBe(true)
    expect(result.current.selectedCandidates.has('c')).toBe(true)
    expect(result.current.selectedCandidates.has('d')).toBe(true)
    expect(result.current.selectedCount).toBe(3)
  })

  it('shift-click works in reverse direction', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('d', false, 3, IDS))
    act(() => result.current.selectCandidate('b', true, 1, IDS))
    expect(result.current.selectedCandidates.has('b')).toBe(true)
    expect(result.current.selectedCandidates.has('c')).toBe(true)
    expect(result.current.selectedCandidates.has('d')).toBe(true)
  })

  it('shift-click without prior anchor falls back to toggle', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('c', true, 2, IDS))
    expect(result.current.selectedCandidates.has('c')).toBe(true)
    expect(result.current.selectedCount).toBe(1)
  })

  // ── deselectCandidate ────────────────────────────────────────────────────

  it('deselectCandidate removes a specific candidate', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    act(() => result.current.selectCandidate('b'))
    act(() => result.current.deselectCandidate('a'))
    expect(result.current.selectedCandidates.has('a')).toBe(false)
    expect(result.current.selectedCandidates.has('b')).toBe(true)
    expect(result.current.selectedCount).toBe(1)
  })

  it('deselectCandidate is a no-op for unselected candidate', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.deselectCandidate('not-selected'))
    expect(result.current.selectedCount).toBe(0)
  })

  // ── toggleSelectAll ───────────────────────────────────────────────────────

  it('toggleSelectAll selects all when none are selected', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.toggleSelectAll(IDS))
    expect(result.current.selectedCount).toBe(IDS.length)
    IDS.forEach(id => expect(result.current.selectedCandidates.has(id)).toBe(true))
  })

  it('toggleSelectAll deselects all when all are already selected', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.toggleSelectAll(IDS))
    act(() => result.current.toggleSelectAll(IDS))
    expect(result.current.selectedCount).toBe(0)
  })

  it('toggleSelectAll selects all when only some are selected', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('a'))
    act(() => result.current.toggleSelectAll(IDS))
    expect(result.current.selectedCount).toBe(IDS.length)
  })

  it('toggleSelectAll resets lastSelectedIndex to null', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('b', false, 1, IDS))
    act(() => result.current.toggleSelectAll(IDS))
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  it('toggleSelectAll with empty list results in empty selection', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.toggleSelectAll([]))
    expect(result.current.selectedCount).toBe(0)
  })

  // ── clearSelection ────────────────────────────────────────────────────────

  it('clearSelection empties the selection', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.toggleSelectAll(IDS))
    act(() => result.current.clearSelection())
    expect(result.current.selectedCount).toBe(0)
    expect(result.current.selectedCandidates.size).toBe(0)
  })

  it('clearSelection resets lastSelectedIndex', () => {
    const { result } = renderHook(() => useCandidateSelection())
    act(() => result.current.selectCandidate('c', false, 2, IDS))
    act(() => result.current.clearSelection())
    expect(result.current.lastSelectedIndex).toBeNull()
  })

  it('clearSelection on empty set is a no-op', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(() => act(() => result.current.clearSelection())).not.toThrow()
    expect(result.current.selectedCount).toBe(0)
  })

  // ── Returned interface stability ──────────────────────────────────────────

  it('exposes setSelectedCandidates for external overrides', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(typeof result.current.setSelectedCandidates).toBe('function')
  })

  it('selectedCandidates is a Set instance', () => {
    const { result } = renderHook(() => useCandidateSelection())
    expect(result.current.selectedCandidates).toBeInstanceOf(Set)
  })
})
