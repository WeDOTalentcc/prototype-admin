import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'
import { registerStoreReset } from './auth-store'

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

interface JobColumnConfigData {
  columns: Array<{ id: string; label: string; category: string; visible: boolean; order: number }>
  savedViews: Array<{ id: string; name: string; columns: string[]; createdAt: string }>
}

interface RecruiterContextData {
  openJobsWithoutCandidates?: number
  stalledCandidates?: number
  upcomingInterviews?: number
  pendingApprovals?: number
}

export interface TableColumnConfigEntry {
  id: string
  visible: boolean
  order: number
}

export interface StoredAdminClient {
  id: string
  name: string
  tradeName?: string
  cnpj?: string
  status: string
  planId?: string
  logoUrl?: string
}

export interface StoredGlobalSearchSettings {
  defaultLimit: number
  searchType: 'fast'
  showEmails: boolean
  showPhoneNumbers: boolean
  highFreshness: boolean
  autoExpandGlobal: boolean
  confirmBeforeSearch: boolean
  globalSearchEnabled: boolean
}

export interface LiaRecentItem {
  id: string
  type: string
  title: string
  timestamp: number
  lastMessage?: string
  mode?: string
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
  settingsSidebarWidth: number
  jobColumnConfig: JobColumnConfigData | null
  recruiterContext: RecruiterContextData | null
  cookieConsent: 'accepted' | 'declined' | null
  sidebarCollapsed: boolean
  sidebarWidth: number
  promptSuggestionsPosition: { top: number; right: number }
  tableColumnConfigs: Record<string, TableColumnConfigEntry[]>
  kanbanFiltersMap: Record<string, Record<string, unknown>>
  kanbanColumnOrders: Record<string, string[]>
  customPresetsMap: Record<string, unknown[]>
  globalSearchSettingsCache: StoredGlobalSearchSettings | null
  adminSelectedClient: StoredAdminClient | null
  liaRecentItems: LiaRecentItem[]
  liaFavorites: string[]
  liaPrompt: string | null
  pipelineOverviewMode: 'vagas' | 'candidatos'
  jobsViewMode: 'table' | 'kanban'
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
  setSettingsSidebarWidth: (width: number) => void
  setJobColumnConfig: (config: JobColumnConfigData | null) => void
  setRecruiterContext: (context: RecruiterContextData | null) => void
  setCookieConsent: (consent: 'accepted' | 'declined') => void
  setSidebarCollapsed: (collapsed: boolean) => void
  setSidebarWidth: (width: number) => void
  setPromptSuggestionsPosition: (position: { top: number; right: number }) => void
  setTableColumnConfig: (key: string, config: TableColumnConfigEntry[]) => void
  getTableColumnConfig: (key: string) => TableColumnConfigEntry[] | null
  removeTableColumnConfig: (key: string) => void
  setKanbanFilters: (key: string, filters: Record<string, unknown>) => void
  getKanbanFilters: (key: string) => Record<string, unknown> | null
  removeKanbanFilters: (key: string) => void
  setKanbanColumnOrder: (key: string, order: string[]) => void
  getKanbanColumnOrder: (key: string) => string[] | null
  removeKanbanColumnOrder: (key: string) => void
  setCustomPresets: (key: string, presets: unknown[]) => void
  getCustomPresets: (key: string) => unknown[]
  setGlobalSearchSettingsCache: (settings: StoredGlobalSearchSettings | null) => void
  setAdminSelectedClient: (client: StoredAdminClient | null) => void
  setLiaRecentItems: (items: LiaRecentItem[]) => void
  setLiaFavorites: (favorites: string[]) => void
  toggleLiaFavorite: (id: string) => void
  setLiaPrompt: (prompt: string | null) => void
  setPipelineOverviewMode: (mode: 'vagas' | 'candidatos') => void
  setJobsViewMode: (mode: 'table' | 'kanban') => void
  resetSessionData: () => void
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
        settingsSidebarWidth: 256,
        jobColumnConfig: null,
        recruiterContext: null,
        cookieConsent: null,
        sidebarCollapsed: false,
        sidebarWidth: 256,
        promptSuggestionsPosition: { top: 80, right: 24 },
        tableColumnConfigs: {},
        kanbanFiltersMap: {},
        kanbanColumnOrders: {},
        customPresetsMap: {},
        globalSearchSettingsCache: null,
        adminSelectedClient: null,
        liaRecentItems: [],
        liaFavorites: [],
        liaPrompt: null,
        pipelineOverviewMode: 'vagas',
        jobsViewMode: 'table',

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

        setSettingsSidebarWidth: (width) =>
          set({ settingsSidebarWidth: width }, false, 'uiPrefs/setSettingsSidebarWidth'),

        setJobColumnConfig: (config) =>
          set({ jobColumnConfig: config }, false, 'uiPrefs/setJobColumnConfig'),

        setRecruiterContext: (context) =>
          set({ recruiterContext: context }, false, 'uiPrefs/setRecruiterContext'),

        setCookieConsent: (consent) =>
          set({ cookieConsent: consent }, false, 'uiPrefs/setCookieConsent'),

        setSidebarCollapsed: (collapsed) =>
          set({ sidebarCollapsed: collapsed }, false, 'uiPrefs/setSidebarCollapsed'),

        setSidebarWidth: (width) =>
          set({ sidebarWidth: width }, false, 'uiPrefs/setSidebarWidth'),

        setPromptSuggestionsPosition: (position) =>
          set({ promptSuggestionsPosition: position }, false, 'uiPrefs/setPromptSuggestionsPosition'),

        setTableColumnConfig: (key, config) =>
          set(
            (state) => ({
              tableColumnConfigs: { ...state.tableColumnConfigs, [key]: config },
            }),
            false,
            'uiPrefs/setTableColumnConfig'
          ),

        getTableColumnConfig: (key) => get().tableColumnConfigs[key] || null,

        removeTableColumnConfig: (key) =>
          set(
            (state) => {
              const updated = { ...state.tableColumnConfigs }
              delete updated[key]
              return { tableColumnConfigs: updated }
            },
            false,
            'uiPrefs/removeTableColumnConfig'
          ),

        setKanbanFilters: (key, filters) =>
          set(
            (state) => ({
              kanbanFiltersMap: { ...state.kanbanFiltersMap, [key]: filters },
            }),
            false,
            'uiPrefs/setKanbanFilters'
          ),

        getKanbanFilters: (key) =>
          (get().kanbanFiltersMap[key] as Record<string, unknown>) || null,

        removeKanbanFilters: (key) =>
          set(
            (state) => {
              const updated = { ...state.kanbanFiltersMap }
              delete updated[key]
              return { kanbanFiltersMap: updated }
            },
            false,
            'uiPrefs/removeKanbanFilters'
          ),

        setKanbanColumnOrder: (key, order) =>
          set(
            (state) => ({
              kanbanColumnOrders: { ...state.kanbanColumnOrders, [key]: order },
            }),
            false,
            'uiPrefs/setKanbanColumnOrder'
          ),

        getKanbanColumnOrder: (key) => get().kanbanColumnOrders[key] || null,

        removeKanbanColumnOrder: (key) =>
          set(
            (state) => {
              const updated = { ...state.kanbanColumnOrders }
              delete updated[key]
              return { kanbanColumnOrders: updated }
            },
            false,
            'uiPrefs/removeKanbanColumnOrder'
          ),

        setCustomPresets: (key, presets) =>
          set(
            (state) => ({
              customPresetsMap: { ...state.customPresetsMap, [key]: presets },
            }),
            false,
            'uiPrefs/setCustomPresets'
          ),

        getCustomPresets: (key) => get().customPresetsMap[key] || [],

        setGlobalSearchSettingsCache: (settings) =>
          set({ globalSearchSettingsCache: settings }, false, 'uiPrefs/setGlobalSearchSettingsCache'),

        setAdminSelectedClient: (client) =>
          set({ adminSelectedClient: client }, false, 'uiPrefs/setAdminSelectedClient'),

        setLiaRecentItems: (items) =>
          set({ liaRecentItems: items }, false, 'uiPrefs/setLiaRecentItems'),

        setLiaFavorites: (favorites) =>
          set({ liaFavorites: favorites }, false, 'uiPrefs/setLiaFavorites'),

        toggleLiaFavorite: (id) =>
          set(
            (state) => {
              const current = new Set(state.liaFavorites)
              if (current.has(id)) {
                current.delete(id)
              } else {
                current.add(id)
              }
              return { liaFavorites: Array.from(current) }
            },
            false,
            'uiPrefs/toggleLiaFavorite'
          ),

        setLiaPrompt: (prompt) =>
          set({ liaPrompt: prompt }, false, 'uiPrefs/setLiaPrompt'),

        setPipelineOverviewMode: (mode) =>
          set({ pipelineOverviewMode: mode }, false, 'uiPrefs/setPipelineOverviewMode'),

        setJobsViewMode: (mode) =>
          set({ jobsViewMode: mode }, false, 'uiPrefs/setJobsViewMode'),

        resetSessionData: () =>
          set(
            (state) => ({
              ...state,
              kanbanFiltersMap: {},
              customPresetsMap: {},
              globalSearchSettingsCache: null,
              adminSelectedClient: null,
              sharedSessionTokens: {},
              kanbanColumnOrders: {},
              tableColumnConfigs: {},
              liaPrompt: null,
            }),
            false,
            'uiPrefs/resetSessionData'
          ),
      }),
      {
        name: 'lia-ui-preferences-store',
      }
    ),
    { name: 'UIPreferencesStore' }
  )
)

registerStoreReset(() => useUIPreferencesStore.getState().resetSessionData())
