import { beforeEach, describe, expect, it, vi } from 'vitest'

const localStorageMock = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value },
    removeItem: (key: string) => { delete store[key] },
    clear: () => { store = {} },
  }
})()

Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

vi.mock('@/stores/auth-store', () => ({
  registerStoreReset: vi.fn(),
}))

vi.mock('@/components/search/smart-search-input', () => ({}))

describe('candidates-store — persist middleware', () => {
  beforeEach(() => {
    localStorageMock.clear()
    vi.resetModules()
  })

  it('persiste lastSearchQuery no localStorage', async () => {
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().setLastSearchQuery('engenheiro ruby senior')
    const raw = localStorageMock.getItem('lia-candidates-search-context')
    expect(raw).not.toBeNull()
    const parsed = JSON.parse(raw!)
    expect(parsed.state.lastSearchQuery).toBe('engenheiro ruby senior')
  })

  it('persiste searchSource, activeTab, sortBy', async () => {
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().setSearchSource('global')
    useCandidatesStore.getState().setActiveTab('favorites')
    useCandidatesStore.getState().setSortBy('name')
    const raw = localStorageMock.getItem('lia-candidates-search-context')
    const parsed = JSON.parse(raw!)
    expect(parsed.state.searchSource).toBe('global')
    expect(parsed.state.activeTab).toBe('favorites')
    expect(parsed.state.sortBy).toBe('name')
  })

  it('NAO persiste candidates array', async () => {
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().setCandidates([{ id: '1', name: 'Joao' }])
    const raw = localStorageMock.getItem('lia-candidates-search-context')
    const parsed = JSON.parse(raw!)
    expect(parsed.state.candidates).toBeUndefined()
  })

  it('NAO persiste selectedCandidates', async () => {
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().toggleCandidateSelection('candidate-123')
    const raw = localStorageMock.getItem('lia-candidates-search-context')
    const parsed = JSON.parse(raw!)
    expect(parsed.state.selectedCandidates).toBeUndefined()
  })

  it('resetStore limpa selectedCandidates para Set vazio', async () => {
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().toggleCandidateSelection('c1')
    useCandidatesStore.getState().resetStore()
    const { selectedCandidates } = useCandidatesStore.getState()
    expect(selectedCandidates).toBeInstanceOf(Set)
    expect(selectedCandidates.size).toBe(0)
  })

  it('inclui _persistedAt para TTL', async () => {
    const before = Date.now()
    const { useCandidatesStore } = await import('../candidates-store')
    useCandidatesStore.getState().setLastSearchQuery('test')
    const raw = localStorageMock.getItem('lia-candidates-search-context')
    const parsed = JSON.parse(raw!)
    expect(parsed.state._persistedAt).toBeGreaterThanOrEqual(before)
  })
})
