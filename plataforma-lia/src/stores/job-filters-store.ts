import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

export interface JobFiltersState {
  selectedStatusFilter: string
  selectedDaysFilter: string
  advancedFilters: { [key: string]: string[] }
  booleanSearch: string
  searchTerm: string
}

export interface SavedSearch {
  id: string
  name: string
  query: string
  filters: JobFiltersState
  createdAt: string
  isShared?: boolean
}

function createDefaultAdvancedFilters(): { [key: string]: string[] } {
  return {
    job_titles: [],
    departments: [],
    locations: [],
    work_models: [],
    job_types: [],
    seniority_levels: [],
    salary_ranges: [],
    status: [],
    stages: [],
    priorities: [],
    managers: [],
    benefits: [],
    requirements: [],
    industries: [],
    budget_ranges: [],
    urgency_levels: [],
    contract_duration: [],
    team_size: []
  }
}

function createDefaultFiltersState(): JobFiltersState {
  return {
    selectedStatusFilter: 'todas',
    selectedDaysFilter: 'todas',
    advancedFilters: createDefaultAdvancedFilters(),
    booleanSearch: '',
    searchTerm: ''
  }
}

const MAX_SAVED_SEARCHES = 10

interface JobFiltersStoreState {
  filtersState: JobFiltersState
  savedSearches: SavedSearch[]
}

interface JobFiltersStoreActions {
  setFiltersState: (state: JobFiltersState) => void
  updateFilter: <K extends keyof JobFiltersState>(key: K, value: JobFiltersState[K]) => void
  updateAdvancedFilter: (key: string, value: string[]) => void
  clearAllFilters: () => void
  setSavedSearches: (searches: SavedSearch[]) => void
  saveCurrentSearch: (name: string) => SavedSearch
  applySavedSearch: (searchId: string) => boolean
  deleteSavedSearch: (searchId: string) => void
  renameSavedSearch: (searchId: string, newName: string) => void
  toggleSearchSharing: (searchId: string) => void
  getActiveFiltersCount: () => number
  hasActiveFilters: () => boolean
}

export type JobFiltersStore = JobFiltersStoreState & JobFiltersStoreActions

export const useJobFiltersStore = create<JobFiltersStore>()(
  devtools(
    persist(
      (set, get) => ({
        filtersState: createDefaultFiltersState(),
        savedSearches: [],

        setFiltersState: (state) =>
          set({ filtersState: state }, false, 'jobFilters/setFiltersState'),

        updateFilter: (key, value) =>
          set(
            (s) => ({ filtersState: { ...s.filtersState, [key]: value } }),
            false,
            'jobFilters/updateFilter'
          ),

        updateAdvancedFilter: (key, value) =>
          set(
            (s) => ({
              filtersState: {
                ...s.filtersState,
                advancedFilters: { ...s.filtersState.advancedFilters, [key]: [...value] }
              }
            }),
            false,
            'jobFilters/updateAdvancedFilter'
          ),

        clearAllFilters: () =>
          set({ filtersState: createDefaultFiltersState() }, false, 'jobFilters/clearAllFilters'),

        setSavedSearches: (searches) =>
          set({ savedSearches: searches.slice(0, MAX_SAVED_SEARCHES) }, false, 'jobFilters/setSavedSearches'),

        saveCurrentSearch: (name) => {
          const { filtersState, savedSearches } = get()
          const newSearch: SavedSearch = {
            id: `search_${Date.now()}`,
            name,
            query: filtersState.searchTerm,
            filters: {
              ...filtersState,
              advancedFilters: { ...filtersState.advancedFilters }
            },
            createdAt: new Date().toISOString(),
            isShared: false
          }
          set(
            { savedSearches: [newSearch, ...savedSearches].slice(0, MAX_SAVED_SEARCHES) },
            false,
            'jobFilters/saveCurrentSearch'
          )
          return newSearch
        },

        applySavedSearch: (searchId) => {
          const { savedSearches } = get()
          const search = savedSearches.find(s => s.id === searchId)
          if (search) {
            set({
              filtersState: {
                selectedStatusFilter: search.filters.selectedStatusFilter || 'todas',
                selectedDaysFilter: search.filters.selectedDaysFilter || 'todas',
                booleanSearch: search.filters.booleanSearch || '',
                searchTerm: search.filters.searchTerm || search.query || '',
                advancedFilters: {
                  ...createDefaultAdvancedFilters(),
                  ...(search.filters.advancedFilters || {})
                }
              }
            }, false, 'jobFilters/applySavedSearch')
            return true
          }
          return false
        },

        deleteSavedSearch: (searchId) =>
          set(
            (s) => ({ savedSearches: s.savedSearches.filter(ss => ss.id !== searchId) }),
            false,
            'jobFilters/deleteSavedSearch'
          ),

        renameSavedSearch: (searchId, newName) =>
          set(
            (s) => ({
              savedSearches: s.savedSearches.map(ss =>
                ss.id === searchId ? { ...ss, name: newName } : ss
              )
            }),
            false,
            'jobFilters/renameSavedSearch'
          ),

        toggleSearchSharing: (searchId) =>
          set(
            (s) => ({
              savedSearches: s.savedSearches.map(ss =>
                ss.id === searchId ? { ...ss, isShared: !ss.isShared } : ss
              )
            }),
            false,
            'jobFilters/toggleSearchSharing'
          ),

        getActiveFiltersCount: () => {
          const { filtersState } = get()
          let count = 0
          if (filtersState.selectedStatusFilter !== 'todas') count++
          if (filtersState.selectedDaysFilter !== 'todas') count++
          if (filtersState.booleanSearch.trim()) count++
          if (filtersState.searchTerm.trim()) count++
          Object.values(filtersState.advancedFilters).forEach(arr => {
            if (arr.length > 0) count++
          })
          return count
        },

        hasActiveFilters: () => {
          return get().getActiveFiltersCount() > 0
        },
      }),
      {
        name: 'wedotalent_job_filters',
      }
    ),
    { name: 'JobFiltersStore' }
  )
)
