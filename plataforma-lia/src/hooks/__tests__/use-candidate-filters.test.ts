/**
 * Tests — useCandidateFilters
 *
 * Covers:
 * - Initial state
 * - showTableFiltersPanel toggle
 * - resetFilters restores defaults
 * - hasActiveFilters computed value
 * - columnFilters initial structure
 * - newSoftSkillFilter / newCertificationFilter state
 * - openFilterDropdown state
 */
import { renderHook, act } from '@testing-library/react'
import { useCandidateFilters } from '../use-candidate-filters'

describe('useCandidateFilters', () => {
  // ── Initial state ─────────────────────────────────────────────────────────

  it('starts with empty array filters', () => {
    const { result } = renderHook(() => useCandidateFilters())
    const f = result.current.tableFilters
    expect(f.statuses).toEqual([])
    expect(f.tags).toEqual([])
    expect(f.skills).toEqual([])
    expect(f.locations).toEqual([])
  })

  it('starts with boolean filters false', () => {
    const { result } = renderHook(() => useCandidateFilters())
    const f = result.current.tableFilters
    expect(f.remoteOnly).toBe(false)
    expect(f.hasEmail).toBe(false)
    expect(f.hasPhone).toBe(false)
    expect(f.hasLinkedin).toBe(false)
    expect(f.isOpenToWork).toBe(false)
    expect(f.isDecisionMaker).toBe(false)
  })

  it('starts with showTableFiltersPanel false', () => {
    const { result } = renderHook(() => useCandidateFilters())
    expect(result.current.showTableFiltersPanel).toBe(false)
  })

  it('starts with hasActiveFilters false', () => {
    const { result } = renderHook(() => useCandidateFilters())
    expect(result.current.hasActiveFilters).toBe(false)
  })

  it('starts with empty soft-skill and certification inputs', () => {
    const { result } = renderHook(() => useCandidateFilters())
    expect(result.current.newSoftSkillFilter).toBe('')
    expect(result.current.newCertificationFilter).toBe('')
  })

  it('starts with openFilterDropdown as null', () => {
    const { result } = renderHook(() => useCandidateFilters())
    expect(result.current.openFilterDropdown).toBeNull()
  })

  // ── showTableFiltersPanel ─────────────────────────────────────────────────

  it('setShowTableFiltersPanel toggles panel visibility', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setShowTableFiltersPanel(true))
    expect(result.current.showTableFiltersPanel).toBe(true)
    act(() => result.current.setShowTableFiltersPanel(false))
    expect(result.current.showTableFiltersPanel).toBe(false)
  })

  // ── tableFilters mutation ─────────────────────────────────────────────────

  it('setTableFilters applies partial updates', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, statuses: ['active'] }))
    )
    expect(result.current.tableFilters.statuses).toEqual(['active'])
  })

  // ── hasActiveFilters ──────────────────────────────────────────────────────

  it('hasActiveFilters is true when statuses is non-empty', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, statuses: ['hired'] }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  it('hasActiveFilters is true when tags are set', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, tags: ['vip'] }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  it('hasActiveFilters is true when remoteOnly is true', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, remoteOnly: true }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  it('hasActiveFilters is true when hasEmail is true', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, hasEmail: true }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  it('hasActiveFilters is true when isOpenToWork is true', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, isOpenToWork: true }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  it('hasActiveFilters is true when softSkills are set', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, softSkills: ['leadership'] }))
    )
    expect(result.current.hasActiveFilters).toBe(true)
  })

  // ── resetFilters ──────────────────────────────────────────────────────────

  it('resetFilters restores default table filters', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({
        ...prev,
        statuses: ['hired'],
        remoteOnly: true,
        skills: ['TypeScript'],
      }))
    )
    act(() => result.current.resetFilters())
    const f = result.current.tableFilters
    expect(f.statuses).toEqual([])
    expect(f.remoteOnly).toBe(false)
    expect(f.skills).toEqual([])
  })

  it('resetFilters clears soft-skill input', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setNewSoftSkillFilter('communication'))
    act(() => result.current.resetFilters())
    expect(result.current.newSoftSkillFilter).toBe('')
  })

  it('resetFilters clears certification input', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setNewCertificationFilter('AWS'))
    act(() => result.current.resetFilters())
    expect(result.current.newCertificationFilter).toBe('')
  })

  it('resetFilters sets openFilterDropdown to null', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setOpenFilterDropdown('status'))
    act(() => result.current.resetFilters())
    expect(result.current.openFilterDropdown).toBeNull()
  })

  it('hasActiveFilters is false after resetFilters', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setTableFilters(prev => ({ ...prev, statuses: ['applied'] }))
    )
    act(() => result.current.resetFilters())
    expect(result.current.hasActiveFilters).toBe(false)
  })

  // ── columnFilters ─────────────────────────────────────────────────────────

  it('columnFilters has initial structure with empty arrays', () => {
    const { result } = renderHook(() => useCandidateFilters())
    const cf = result.current.columnFilters
    expect(Array.isArray(cf.position)).toBe(true)
    expect(Array.isArray(cf.company)).toBe(true)
    expect(Array.isArray(cf.location)).toBe(true)
  })

  it('setColumnFilters updates column filters', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() =>
      result.current.setColumnFilters(prev => ({ ...prev, position: ['Engineer'] }))
    )
    expect(result.current.columnFilters.position).toEqual(['Engineer'])
  })

  // ── openFilterDropdown ────────────────────────────────────────────────────

  it('setOpenFilterDropdown opens a dropdown', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setOpenFilterDropdown('location'))
    expect(result.current.openFilterDropdown).toBe('location')
  })

  it('setOpenFilterDropdown can close by setting to null', () => {
    const { result } = renderHook(() => useCandidateFilters())
    act(() => result.current.setOpenFilterDropdown('status'))
    act(() => result.current.setOpenFilterDropdown(null))
    expect(result.current.openFilterDropdown).toBeNull()
  })
})
