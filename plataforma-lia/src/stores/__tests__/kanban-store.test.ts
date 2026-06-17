vi.mock('../auth-store', () => ({
  registerStoreReset: vi.fn(),
}))

import { useKanbanStore } from '../kanban-store'
import { act } from '@testing-library/react'

const { getState, setState } = useKanbanStore

const initialSnapshot = () => ({
  viewMode: 'kanban' as const,
  activeTab: 'management' as const,
  searchQuery: '',
  selectedCandidates: new Set<string>(),
  selectedCandidate: null,
  showExpandedMetrics: false,
  candidatesData: {},
  isLoadingCandidates: false,
})

beforeEach(() => {
  act(() => setState(initialSnapshot()))
})

describe('kanban-store', () => {
  it('starts with default values', () => {
    const s = getState()
    expect(s.viewMode).toBe('kanban')
    expect(s.activeTab).toBe('management')
    expect(s.searchQuery).toBe('')
    expect(s.selectedCandidates.size).toBe(0)
    expect(s.selectedCandidate).toBeNull()
    expect(s.isLoadingCandidates).toBe(false)
  })

  it('setViewMode toggles between kanban and table', () => {
    act(() => getState().setViewMode('table'))
    expect(getState().viewMode).toBe('table')
    act(() => getState().setViewMode('kanban'))
    expect(getState().viewMode).toBe('kanban')
  })

  it('setActiveTab toggles between management and edit', () => {
    act(() => getState().setActiveTab('edit'))
    expect(getState().activeTab).toBe('edit')
  })

  it('setSearchQuery updates search text', () => {
    act(() => getState().setSearchQuery('Maria'))
    expect(getState().searchQuery).toBe('Maria')
  })

  it('toggleCandidateSelection adds and removes candidates', () => {
    act(() => getState().toggleCandidateSelection('c-1'))
    expect(getState().selectedCandidates.has('c-1')).toBe(true)

    act(() => getState().toggleCandidateSelection('c-1'))
    expect(getState().selectedCandidates.has('c-1')).toBe(false)
  })

  it('selectAllCandidates replaces the entire selection', () => {
    act(() => getState().toggleCandidateSelection('old'))
    act(() => getState().selectAllCandidates(['a', 'b', 'c']))
    expect(getState().selectedCandidates.size).toBe(3)
    expect(getState().selectedCandidates.has('old')).toBe(false)
  })

  it('clearSelection empties the set', () => {
    act(() => getState().selectAllCandidates(['x', 'y']))
    act(() => getState().clearSelection())
    expect(getState().selectedCandidates.size).toBe(0)
  })

  it('setSelectedCandidate stores candidate detail', () => {
    const candidate = { id: 'c-1', name: 'Ana' }
    act(() => getState().setSelectedCandidate(candidate))
    expect(getState().selectedCandidate).toEqual(candidate)
  })

  it('setCandidatesData with object sets data directly', () => {
    const data = { triagem: [{ id: '1', name: 'João' }] }
    act(() => getState().setCandidatesData(data))
    expect(getState().candidatesData).toEqual(data)
  })

  it('setCandidatesData with function merges data', () => {
    act(() => getState().setCandidatesData({ triagem: [{ id: '1' }] }))
    act(() =>
      getState().setCandidatesData((prev) => ({
        ...prev,
        entrevista: [{ id: '2' }],
      }))
    )
    expect(Object.keys(getState().candidatesData)).toEqual(['triagem', 'entrevista'])
  })

  it('setIsLoadingCandidates toggles loading', () => {
    act(() => getState().setIsLoadingCandidates(true))
    expect(getState().isLoadingCandidates).toBe(true)
    act(() => getState().setIsLoadingCandidates(false))
    expect(getState().isLoadingCandidates).toBe(false)
  })

  it('resetStore returns to initial state', () => {
    act(() => {
      getState().setViewMode('table')
      getState().setSearchQuery('test')
      getState().toggleCandidateSelection('c-1')
    })
    act(() => getState().resetStore())
    const s = getState()
    expect(s.viewMode).toBe('kanban')
    expect(s.searchQuery).toBe('')
    expect(s.selectedCandidates.size).toBe(0)
  })

  it('simulates stage transition by moving candidate between stages', () => {
    const initial = {
      sourcing: [{ id: '1', name: 'Ana' }],
      entrevista_rh: [],
    }
    act(() => getState().setCandidatesData(initial))
    expect(getState().candidatesData.sourcing).toHaveLength(1)
    expect(getState().candidatesData.entrevista_rh).toHaveLength(0)

    act(() =>
      getState().setCandidatesData((prev) => {
        const candidate = prev.sourcing[0]
        return {
          ...prev,
          sourcing: prev.sourcing.filter(c => c.id !== '1'),
          entrevista_rh: [...prev.entrevista_rh, { ...candidate, stage: 'entrevista_rh' }],
        }
      })
    )
    expect(getState().candidatesData.sourcing).toHaveLength(0)
    expect(getState().candidatesData.entrevista_rh).toHaveLength(1)
    expect(getState().candidatesData.entrevista_rh[0].name).toBe('Ana')
  })

  it('bulk selection and clear simulates bulk action flow', () => {
    act(() => getState().selectAllCandidates(['c-1', 'c-2', 'c-3', 'c-4', 'c-5']))
    expect(getState().selectedCandidates.size).toBe(5)

    act(() => {
      const selected = getState().selectedCandidates
      expect(selected.has('c-1')).toBe(true)
      expect(selected.has('c-5')).toBe(true)
    })

    act(() => getState().clearSelection())
    expect(getState().selectedCandidates.size).toBe(0)
  })

  it('setSelectedCandidates with function applies partial update', () => {
    act(() => getState().setSelectedCandidates(new Set(['a', 'b'])))
    expect(getState().selectedCandidates.size).toBe(2)

    act(() =>
      getState().setSelectedCandidates((prev) => {
        const next = new Set(prev)
        next.delete('a')
        next.add('c')
        return next
      })
    )
    expect(getState().selectedCandidates.has('a')).toBe(false)
    expect(getState().selectedCandidates.has('b')).toBe(true)
    expect(getState().selectedCandidates.has('c')).toBe(true)
  })
})
