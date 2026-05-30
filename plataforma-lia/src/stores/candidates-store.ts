import { create } from zustand
import { devtools, persist } from zustand/middleware
import { registerStoreReset } from ./auth-store
import type { ParsedEntities, SearchMetadata } from @/components/search/smart-search-input

/**
 * Pagination canonical (Quiet Operator — page size adapta ao viewport).
 *
 * ROW_HEIGHT: altura aproximada do <tr> em UnifiedCandidateTable com padding canonical.
 * CHROME: header + controles + filtros + footer + safety margin do recrutador desktop.
 * MIN/MAX: clamp pra evitar payloads absurdos.
 *
 * Single source of truth — todos os call sites (store init, search reset, navigation
 * reset, CV upload reset, execute search reset) leem daqui. Load-more incrementa por
 * LOAD_MORE_STEP. Trocar o número aqui propaga sozinho.
 */
const PAGINATION_ROW_HEIGHT = 56
const PAGINATION_CHROME = 280
const PAGINATION_MIN = 10
const PAGINATION_MAX = 40

export const LOAD_MORE_STEP = 10

export function getInitialDisplayedResultsCount(): number {
  if (typeof window === "undefined") return PAGINATION_MIN
  const fit = Math.floor((window.innerHeight - PAGINATION_CHROME) / PAGINATION_ROW_HEIGHT)
  return Math.min(PAGINATION_MAX, Math.max(PAGINATION_MIN, fit))
}

// TTL de 8h — evita restaurar contexto de busca stale de um dia anterior
const PERSIST_TTL_MS = 8 * 60 * 60 * 1000

type SearchSource = local | global | hybrid
type ActiveTab = search | favorites | lists | history | saved-searches | agents

interface CreditModalsState {
  hybrid: boolean
  global: boolean
  email: boolean
  phone: boolean
}

interface CandidatesCoreState {
  candidates: Record<string, unknown>[]
  isLoading: boolean
  isSearchActive: boolean
}

interface CandidatesViewState {
  selectedCandidate: Record<string, unknown> | null
  showPreview: boolean
  isPreviewMaximized: boolean
  showCandidatePage: boolean
  showCandidatePreview: boolean
  previewCandidate: Record<string, unknown> | null
  showSidePreview: boolean
  sidePreviewCandidate: Record<string, unknown> | null
  liaPromptValue: string
  talentConversationId: string | undefined
  viewedCandidateIds: Set<string>
  currentPage: number
  crossTabFilter: Record<string, unknown> | null
  showCrossTabBanner: boolean
  viewingList: { id: string; name: string; color?: string } | null
  sortBy: string
  sortOrder: asc | desc
}

interface CandidatesSearchState {
  searchTerm: string
  quickFilters: Set<string>
  activeTab: ActiveTab
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  lastSearchMode: string
  lastSearchMetadata: SearchMetadata | undefined
  lastSearchUsedPearch: boolean
  hasSearchResults: boolean
  searchResultsCount: number
  localResultsCount: number
  pearchResultsCount: number
  creditsUsedInSearch: number
  creditsRemaining: number | null
  showExpandGlobalOption: boolean
  openCreditModals: CreditModalsState
  showEditQueryModal: boolean
  editQueryValue: string
  showSearchResults: boolean
  searchSource: SearchSource
  currentSearchSource: SearchSource
  showGlobalExpansionConfirm: boolean
  hasSearched: boolean
  isExpandingToGlobal: boolean
  searchExecutionId: number
  searchSortBy: string
  searchFeedbacks: Record<string, like | dislike>
  displayedResultsCount: number
  isLoadingMore: boolean
  showOnlyNew: boolean
  isDroppingCV: boolean
  cvUploadLoading: boolean
}

interface CandidatesSelectionState {
  selectedCandidates: Set<string>
  lastSelectedIndex: number | null
}

type CandidatesFullState = CandidatesCoreState & CandidatesViewState & CandidatesSearchState & CandidatesSelectionState

interface CandidatesActions {
  setCandidates: (v: Record<string, unknown>[] | ((prev: Record<string, unknown>[]) => Record<string, unknown>[])) => void
  setIsLoading: (v: boolean) => void
  setIsSearchActive: (v: boolean) => void

  setSelectedCandidate: (v: Record<string, unknown> | null) => void
  setShowPreview: (v: boolean) => void
  setIsPreviewMaximized: (v: boolean) => void
  setShowCandidatePage: (v: boolean) => void
  setShowCandidatePreview: (v: boolean) => void
  setPreviewCandidate: (v: Record<string, unknown> | null) => void
  setShowSidePreview: (v: boolean) => void
  setSidePreviewCandidate: (v: Record<string, unknown> | null) => void
  setLiaPromptValue: (v: string) => void
  setTalentConversationId: (v: string | undefined) => void
  setViewedCandidateIds: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setCurrentPage: (v: number) => void
  setCrossTabFilter: (v: Record<string, unknown> | null) => void
  setShowCrossTabBanner: (v: boolean) => void
  setViewingList: (v: { id: string; name: string; color?: string } | null) => void
  setSortBy: (v: string) => void
  setSortOrder: (v: asc | desc) => void

  setSearchTerm: (v: string) => void
  setQuickFilters: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setActiveTab: (v: ActiveTab) => void
  setLastSearchQuery: (v: string) => void
  setLastSearchEntities: (v: ParsedEntities | null) => void
  setLastSearchMode: (v: string) => void
  setLastSearchMetadata: (v: SearchMetadata | undefined) => void
  setLastSearchUsedPearch: (v: boolean) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setCreditsUsedInSearch: (v: number) => void
  setCreditsRemaining: (v: number | null) => void
  setShowExpandGlobalOption: (v: boolean) => void
  setOpenCreditModals: (v: CreditModalsState | ((prev: CreditModalsState) => CreditModalsState)) => void
  setShowEditQueryModal: (v: boolean) => void
  setEditQueryValue: (v: string) => void
  setShowSearchResults: (v: boolean) => void
  setSearchSource: (v: SearchSource) => void
  setCurrentSearchSource: (v: SearchSource) => void
  setShowGlobalExpansionConfirm: (v: boolean) => void
  setHasSearched: (v: boolean) => void
  setIsExpandingToGlobal: (v: boolean) => void
  setSearchExecutionId: (v: number | ((prev: number) => number)) => void
  setSearchSortBy: (v: string) => void
  setSearchFeedbacks: (v: Record<string, like | dislike> | ((prev: Record<string, like | dislike>) => Record<string, like | dislike>)) => void
  setDisplayedResultsCount: (v: number) => void
  setIsLoadingMore: (v: boolean) => void
  setShowOnlyNew: (v: boolean) => void
  setIsDroppingCV: (v: boolean) => void
  setCvUploadLoading: (v: boolean) => void

  setSelectedCandidates: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setLastSelectedIndex: (v: number | null) => void
  toggleCandidateSelection: (candidateId: string) => void
  selectAllCandidates: (candidateIds: string[]) => void
  clearSelection: () => void

  resetStore: () => void
}

export type CandidatesStore = CandidatesFullState & CandidatesActions

const initialState: CandidatesFullState = {
  candidates: [],
  isLoading: false,
  isSearchActive: false,

  selectedCandidate: null,
  showPreview: false,
  isPreviewMaximized: false,
  showCandidatePage: false,
  showCandidatePreview: false,
  previewCandidate: null,
  showSidePreview: false,
  sidePreviewCandidate: null,
  liaPromptValue: ,
  talentConversationId: undefined,
  viewedCandidateIds: new Set<string>(),
  currentPage: 1,
  crossTabFilter: null,
  showCrossTabBanner: false,
  viewingList: null,
  sortBy: score,
  sortOrder: desc,

  searchTerm: ,
  quickFilters: new Set<string>(),
  activeTab: search,
  lastSearchQuery: ,
  lastSearchEntities: null,
  lastSearchMode: ,
  lastSearchMetadata: undefined,
  lastSearchUsedPearch: false,
  hasSearchResults: false,
  searchResultsCount: 0,
  localResultsCount: 0,
  pearchResultsCount: 0,
  creditsUsedInSearch: 0,
  creditsRemaining: null,
  showExpandGlobalOption: false,
  openCreditModals: { hybrid: false, global: false, email: false, phone: false },
  showEditQueryModal: false,
  editQueryValue: ,
  showSearchResults: false,
  searchSource: hybrid,
  currentSearchSource: local,
  showGlobalExpansionConfirm: false,
  hasSearched: false,
  isExpandingToGlobal: false,
  searchExecutionId: 0,
  searchSortBy: relevance,
  searchFeedbacks: {},
  displayedResultsCount: getInitialDisplayedResultsCount(),
  isLoadingMore: false,
  showOnlyNew: false,
  isDroppingCV: false,
  cvUploadLoading: false,

  selectedCandidates: new Set<string>(),
  lastSelectedIndex: null,
}

function setOrUpdate<T>(
   
  set: (partial: any, replace?: any, actionName?: any) => void,
  key: keyof CandidatesFullState,
  actionName: string,
) {
  return (v: T | ((prev: T) => T)) => {
    if (typeof v === function) {
      set((state: CandidatesFullState) => ({ [key]: (v as (prev: T) => T)(state[key] as T) }), false, actionName)
    } else {
      set({ [key]: v } as Partial<CandidatesFullState>, false, actionName)
    }
  }
}

export const useCandidatesStore = create<CandidatesStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setCandidates: (v) => {
          if (typeof v === function) {
            set((s) => ({ candidates: v(s.candidates) }), false, candidates/setCandidates)
          } else {
            set({ candidates: v }, false, candidates/setCandidates)
          }
        },
        setIsLoading: (v) => set({ isLoading: v }, false, candidates/setIsLoading),
        setIsSearchActive: (v) => set({ isSearchActive: v }, false, candidates/setIsSearchActive),

        setSelectedCandidate: (v) => set({ selectedCandidate: v }, false, view/setSelectedCandidate),
        setShowPreview: (v) => set({ showPreview: v }, false, view/setShowPreview),
        setIsPreviewMaximized: (v) => set({ isPreviewMaximized: v }, false, view/setIsPreviewMaximized),
        setShowCandidatePage: (v) => set({ showCandidatePage: v }, false, view/setShowCandidatePage),
        setShowCandidatePreview: (v) => set({ showCandidatePreview: v }, false, view/setShowCandidatePreview),
        setPreviewCandidate: (v) => set({ previewCandidate: v }, false, view/setPreviewCandidate),
        setShowSidePreview: (v) => set({ showSidePreview: v }, false, view/setShowSidePreview),
        setSidePreviewCandidate: (v) => set({ sidePreviewCandidate: v }, false, view/setSidePreviewCandidate),
        setLiaPromptValue: (v) => set({ liaPromptValue: v }, false, view/setLiaPromptValue),
        setTalentConversationId: (v) => set({ talentConversationId: v }, false, view/setTalentConversationId),
        setViewedCandidateIds: setOrUpdate<Set<string>>(set, viewedCandidateIds, view/setViewedCandidateIds),
        setCurrentPage: (v) => set({ currentPage: v }, false, view/setCurrentPage),
        setCrossTabFilter: (v) => set({ crossTabFilter: v }, false, view/setCrossTabFilter),
        setShowCrossTabBanner: (v) => set({ showCrossTabBanner: v }, false, view/setShowCrossTabBanner),
        setViewingList: (v) => set({ viewingList: v }, false, view/setViewingList),
        setSortBy: (v) => set({ sortBy: v }, false, view/setSortBy),
        setSortOrder: (v) => set({ sortOrder: v }, false, view/setSortOrder),

        setSearchTerm: (v) => set({ searchTerm: v }, false, search/setSearchTerm),
        setQuickFilters: setOrUpdate<Set<string>>(set, quickFilters, search/setQuickFilters),
        setActiveTab: (v) => set({ activeTab: v }, false, search/setActiveTab),
        setLastSearchQuery: (v) => set({ lastSearchQuery: v }, false, search/setLastSearchQuery),
        setLastSearchEntities: (v) => set({ lastSearchEntities: v }, false, search/setLastSearchEntities),
        setLastSearchMode: (v) => set({ lastSearchMode: v }, false, search/setLastSearchMode),
        setLastSearchMetadata: (v) => set({ lastSearchMetadata: v }, false, search/setLastSearchMetadata),
        setLastSearchUsedPearch: (v) => set({ lastSearchUsedPearch: v }, false, search/setLastSearchUsedPearch),
        setHasSearchResults: (v) => set({ hasSearchResults: v }, false, search/setHasSearchResults),
        setSearchResultsCount: (v) => set({ searchResultsCount: v }, false, search/setSearchResultsCount),
        setLocalResultsCount: (v) => set({ localResultsCount: v }, false, search/setLocalResultsCount),
        setPearchResultsCount: (v) => set({ pearchResultsCount: v }, false, search/setPearchResultsCount),
        setCreditsUsedInSearch: (v) => set({ creditsUsedInSearch: v }, false, search/setCreditsUsedInSearch),
        setCreditsRemaining: (v) => set({ creditsRemaining: v }, false, search/setCreditsRemaining),
        setShowExpandGlobalOption: (v) => set({ showExpandGlobalOption: v }, false, search/setShowExpandGlobalOption),
        setOpenCreditModals: setOrUpdate<CreditModalsState>(set, openCreditModals, search/setOpenCreditModals),
        setShowEditQueryModal: (v) => set({ showEditQueryModal: v }, false, search/setShowEditQueryModal),
        setEditQueryValue: (v) => set({ editQueryValue: v }, false, search/setEditQueryValue),
        setShowSearchResults: (v) => set({ showSearchResults: v }, false, search/setShowSearchResults),
        setSearchSource: (v) => set({ searchSource: v }, false, search/setSearchSource),
        setCurrentSearchSource: (v) => set({ currentSearchSource: v }, false, search/setCurrentSearchSource),
        setShowGlobalExpansionConfirm: (v) => set({ showGlobalExpansionConfirm: v }, false, search/setShowGlobalExpansionConfirm),
        setHasSearched: (v) => set({ hasSearched: v }, false, search/setHasSearched),
        setIsExpandingToGlobal: (v) => set({ isExpandingToGlobal: v }, false, search/setIsExpandingToGlobal),
        setSearchExecutionId: setOrUpdate<number>(set, searchExecutionId, search/setSearchExecutionId),
        setSearchSortBy: (v) => set({ searchSortBy: v }, false, search/setSearchSortBy),
        setSearchFeedbacks: setOrUpdate<Record<string, like | dislike>>(set, searchFeedbacks, search/setSearchFeedbacks),
        setDisplayedResultsCount: (v) => set({ displayedResultsCount: v }, false, search/setDisplayedResultsCount),
        setIsLoadingMore: (v) => set({ isLoadingMore: v }, false, search/setIsLoadingMore),
        setShowOnlyNew: (v) => set({ showOnlyNew: v }, false, search/setShowOnlyNew),
        setIsDroppingCV: (v) => set({ isDroppingCV: v }, false, search/setIsDroppingCV),
        setCvUploadLoading: (v) => set({ cvUploadLoading: v }, false, search/setCvUploadLoading),

        setSelectedCandidates: setOrUpdate<Set<string>>(set, selectedCandidates, selection/setSelectedCandidates),
        setLastSelectedIndex: (v) => set({ lastSelectedIndex: v }, false, selection/setLastSelectedIndex),

        toggleCandidateSelection: (candidateId) => {
          const current = get().selectedCandidates
          const next = new Set(current)
          if (next.has(candidateId)) {
            next.delete(candidateId)
          } else {
            next.add(candidateId)
          }
          set({ selectedCandidates: next }, false, selection/toggle)
        },

        selectAllCandidates: (candidateIds) => set({
          selectedCandidates: new Set(candidateIds),
        }, false, selection/selectAll),

        clearSelection: () => set({
          selectedCandidates: new Set<string>(),
          lastSelectedIndex: null,
        }, false, selection/clear),

        resetStore: () => set(initialState, false, candidates/reset),
      }),
      {
        name: lia-candidates-search-context,
        // Persiste apenas o contexto de busca (strings/numbers/booleans).
        // Sets (quickFilters, viewedCandidateIds, selectedCandidates) e arrays grandes
        // (candidates) são excluídos — não são serializáveis de forma confiável via
        // JSON.stringify e podem conter dados stale ou sensíveis.
        partialize: (state) => ({
          lastSearchQuery: state.lastSearchQuery,
          lastSearchMode: state.lastSearchMode,
          searchSource: state.searchSource,
          activeTab: state.activeTab,
          sortBy: state.sortBy,
          sortOrder: state.sortOrder,
          searchSortBy: state.searchSortBy,
          showOnlyNew: state.showOnlyNew,
          hasSearched: state.hasSearched,
          _persistedAt: Date.now(),
        }),
        onRehydrateStorage: () => (state) => {
          if (!state) return
          // Descarta estado persistido com mais de 8h (evita contexto stale)
          const persistedAt = (state as any)._persistedAt as number | undefined
          if (persistedAt && Date.now() - persistedAt > PERSIST_TTL_MS) {
            useCandidatesStore.getState().resetStore()
          }
        },
      }
    ),
    { name: CandidatesStore }
  )
)

registerStoreReset(() => useCandidatesStore.getState().resetStore())
