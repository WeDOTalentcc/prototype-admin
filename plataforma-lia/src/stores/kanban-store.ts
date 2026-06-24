import type { KanbanSortField, KanbanSortOrder } from '@/components/pages/job-kanban/utils/kanbanHelpers'
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

interface KanbanState {
  viewMode: 'kanban' | 'table'
  activeTab: 'management' | 'edit' | 'agents'
  searchQuery: string
  selectedCandidates: Set<string>
  selectedCandidate: Record<string, unknown> | null
  showExpandedMetrics: boolean
  candidatesData: Record<string, Record<string, unknown>[]>
  isLoadingCandidates: boolean
  kanbanSortBy: KanbanSortField
  kanbanSortOrder: KanbanSortOrder
}

interface KanbanActions {
  setViewMode: (mode: 'kanban' | 'table') => void
  setActiveTab: (tab: 'management' | 'edit' | 'agents') => void
  setSearchQuery: (query: string) => void
  setSelectedCandidates: (candidates: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setSelectedCandidate: (candidate: Record<string, unknown> | null) => void
  setShowExpandedMetrics: (show: boolean) => void
  setCandidatesData: (data: Record<string, Record<string, unknown>[]> | ((prev: Record<string, Record<string, unknown>[]>) => Record<string, Record<string, unknown>[]>)) => void
  setIsLoadingCandidates: (loading: boolean) => void
  setKanbanSortBy: (field: KanbanSortField) => void
  setKanbanSortOrder: (order: KanbanSortOrder) => void
  toggleCandidateSelection: (candidateId: string) => void
  selectAllCandidates: (candidateIds: string[]) => void
  clearSelection: () => void
  resetStore: () => void
}

export type KanbanStore = KanbanState & KanbanActions

const initialState: KanbanState = {
  viewMode: 'kanban',
  activeTab: 'management',
  searchQuery: '',
  selectedCandidates: new Set<string>(),
  selectedCandidate: null,
  showExpandedMetrics: false,
  candidatesData: {},
  isLoadingCandidates: false,
  kanbanSortBy: 'score' as KanbanSortField,
  kanbanSortOrder: 'desc' as KanbanSortOrder,
}

export const useKanbanStore = create<KanbanStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setViewMode: (mode) => set({ viewMode: mode }, false, 'kanban/setViewMode'),

      setActiveTab: (tab) => set({ activeTab: tab }, false, 'kanban/setActiveTab'),

      setSearchQuery: (query) => set({ searchQuery: query }, false, 'kanban/setSearchQuery'),

      setSelectedCandidates: (candidatesOrFn) => {
        if (typeof candidatesOrFn === 'function') {
          set((state) => ({ selectedCandidates: candidatesOrFn(state.selectedCandidates) }), false, 'kanban/setSelectedCandidates')
        } else {
          set({ selectedCandidates: candidatesOrFn }, false, 'kanban/setSelectedCandidates')
        }
      },

      setSelectedCandidate: (candidate) => set({ selectedCandidate: candidate }, false, 'kanban/setSelectedCandidate'),

      setShowExpandedMetrics: (show) => set({ showExpandedMetrics: show }, false, 'kanban/setShowExpandedMetrics'),

      setCandidatesData: (dataOrFn) => {
        if (typeof dataOrFn === 'function') {
          set((state) => ({ candidatesData: dataOrFn(state.candidatesData) }), false, 'kanban/setCandidatesData')
        } else {
          set({ candidatesData: dataOrFn }, false, 'kanban/setCandidatesData')
        }
      },

      setIsLoadingCandidates: (loading) => set({ isLoadingCandidates: loading }, false, 'kanban/setIsLoadingCandidates'),

      setKanbanSortBy: (field) => set({ kanbanSortBy: field }, false, 'kanban/setKanbanSortBy'),

      setKanbanSortOrder: (order) => set({ kanbanSortOrder: order }, false, 'kanban/setKanbanSortOrder'),

      toggleCandidateSelection: (candidateId) => {
        const current = get().selectedCandidates
        const next = new Set(current)
        if (next.has(candidateId)) {
          next.delete(candidateId)
        } else {
          next.add(candidateId)
        }
        set({ selectedCandidates: next }, false, 'kanban/toggleCandidateSelection')
      },

      selectAllCandidates: (candidateIds) => set({
        selectedCandidates: new Set(candidateIds),
      }, false, 'kanban/selectAllCandidates'),

      clearSelection: () => set({
        selectedCandidates: new Set<string>(),
      }, false, 'kanban/clearSelection'),

      resetStore: () => set(initialState, false, 'kanban/reset'),
    }),
    { name: 'KanbanStore' }
  )
)

registerStoreReset(() => useKanbanStore.getState().resetStore())
