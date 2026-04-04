import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface CandidateTableColumn {
  key: string
  label: string
  visible: boolean
  [key: string]: unknown
}

export interface CandidateColumnView {
  id: string
  name?: string
  columns?: unknown
  createdAt?: string
  [key: string]: unknown
}

export interface CriteriaPreset {
  id: string
  name: string
  criteria: Array<{ id: string; text: string; isPinned: boolean }>
}

interface UIPreferencesState {
  candidateTableColumns: CandidateTableColumn[] | null
  candidateColumnViews: CandidateColumnView[]
  candidateTableColumnOrder: string[] | null
  jobKanbanTableColumnOrder: string[] | null
  jobsTableColumnOrder: string[] | null
  jobsTableColumnWidths: Record<string, number> | null
  criteriaPresets: CriteriaPreset[]
  sharedSessionTokens: Record<string, string>
}

interface UIPreferencesActions {
  setCandidateTableColumns: (columns: CandidateTableColumn[]) => void
  setCandidateColumnViews: (views: CandidateColumnView[]) => void
  setCandidateTableColumnOrder: (order: string[]) => void
  setJobKanbanTableColumnOrder: (order: string[]) => void
  setJobsTableColumnOrder: (order: string[]) => void
  setJobsTableColumnWidths: (widths: Record<string, number>) => void
  setCriteriaPresets: (presets: CriteriaPreset[]) => void
  setSharedSessionToken: (token: string, sessionToken: string) => void
  getSharedSessionToken: (token: string) => string | null
  removeSharedSessionToken: (token: string) => void
}

export type UIPreferencesStore = UIPreferencesState & UIPreferencesActions

export const useUIPreferencesStore = create<UIPreferencesStore>()(
  devtools(
    persist(
      (set, get) => ({
        candidateTableColumns: null,
        candidateColumnViews: [],
        candidateTableColumnOrder: null,
        jobKanbanTableColumnOrder: null,
        jobsTableColumnOrder: null,
        jobsTableColumnWidths: null,
        criteriaPresets: [],
        sharedSessionTokens: {},

        setCandidateTableColumns: (columns) =>
          set({ candidateTableColumns: columns }, false, 'uiPrefs/setCandidateTableColumns'),

        setCandidateColumnViews: (views) =>
          set({ candidateColumnViews: views }, false, 'uiPrefs/setCandidateColumnViews'),

        setCandidateTableColumnOrder: (order) =>
          set({ candidateTableColumnOrder: order }, false, 'uiPrefs/setCandidateTableColumnOrder'),

        setJobKanbanTableColumnOrder: (order) =>
          set({ jobKanbanTableColumnOrder: order }, false, 'uiPrefs/setJobKanbanTableColumnOrder'),

        setJobsTableColumnOrder: (order) =>
          set({ jobsTableColumnOrder: order }, false, 'uiPrefs/setJobsTableColumnOrder'),

        setJobsTableColumnWidths: (widths) =>
          set({ jobsTableColumnWidths: widths }, false, 'uiPrefs/setJobsTableColumnWidths'),

        setCriteriaPresets: (presets) =>
          set({ criteriaPresets: presets }, false, 'uiPrefs/setCriteriaPresets'),

        setSharedSessionToken: (token, sessionToken) =>
          set(
            (state) => ({
              sharedSessionTokens: { ...state.sharedSessionTokens, [token]: sessionToken },
            }),
            false,
            'uiPrefs/setSharedSessionToken'
          ),

        getSharedSessionToken: (token) => {
          return get().sharedSessionTokens[token] || null
        },

        removeSharedSessionToken: (token) =>
          set(
            (state) => {
              const updated = { ...state.sharedSessionTokens }
              delete updated[token]
              return { sharedSessionTokens: updated }
            },
            false,
            'uiPrefs/removeSharedSessionToken'
          ),
      }),
      {
        name: 'lia-ui-preferences-store',
      }
    ),
    { name: 'UIPreferencesStore' }
  )
)
