import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

interface CandidatesState {
  candidates: Record<string, unknown>[]
  isLoading: boolean
  isSearchActive: boolean
  selectedCandidates: Set<string>
}

interface CandidatesActions {
  setCandidates: (candidates: Record<string, unknown>[] | ((prev: Record<string, unknown>[]) => Record<string, unknown>[])) => void
  setIsLoading: (loading: boolean) => void
  setIsSearchActive: (active: boolean) => void
  toggleCandidateSelection: (candidateId: string) => void
  selectAllCandidates: (candidateIds: string[]) => void
  clearSelection: () => void
  resetStore: () => void
}

export type CandidatesStore = CandidatesState & CandidatesActions

const initialState: CandidatesState = {
  candidates: [],
  isLoading: false,
  isSearchActive: false,
  selectedCandidates: new Set<string>(),
}

export const useCandidatesStore = create<CandidatesStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setCandidates: (candidatesOrFn) => {
        if (typeof candidatesOrFn === 'function') {
          set((state) => ({ candidates: candidatesOrFn(state.candidates) }), false, 'candidates/setCandidates')
        } else {
          set({ candidates: candidatesOrFn }, false, 'candidates/setCandidates')
        }
      },

      setIsLoading: (loading) => set({ isLoading: loading }, false, 'candidates/setIsLoading'),

      setIsSearchActive: (active) => set({ isSearchActive: active }, false, 'candidates/setIsSearchActive'),

      toggleCandidateSelection: (candidateId) => {
        const current = get().selectedCandidates
        const next = new Set(current)
        if (next.has(candidateId)) {
          next.delete(candidateId)
        } else {
          next.add(candidateId)
        }
        set({ selectedCandidates: next }, false, 'candidates/toggleCandidateSelection')
      },

      selectAllCandidates: (candidateIds) => set({
        selectedCandidates: new Set(candidateIds),
      }, false, 'candidates/selectAllCandidates'),

      clearSelection: () => set({
        selectedCandidates: new Set<string>(),
      }, false, 'candidates/clearSelection'),

      resetStore: () => set(initialState, false, 'candidates/reset'),
    }),
    { name: 'CandidatesStore' }
  )
)

registerStoreReset(() => useCandidatesStore.getState().resetStore())
