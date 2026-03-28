/**
 * use-candidates-search-state.ts — Sprint 4.11
 *
 * Centraliza todos os estados relacionados à busca de candidatos,
 * extraídos de CandidatesPage para reduzir o tamanho do componente.
 *
 * Portabilidade Vue: retorna { state, actions } → mapeia para data() + methods() em Vue 3.
 */

import { useState } from "react"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type SearchSource = "local" | "global" | "hybrid"

interface CreditModalsState {
  hybrid: boolean
  global: boolean
  email: boolean
  phone: boolean
}

interface SearchState {
  searchTerm: string
  quickFilters: Set<string>
  activeTab: "search" | "favorites" | "lists" | "history" | "saved-searches" | "agents"
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
  searchFeedbacks: Record<string, "like" | "dislike">
  displayedResultsCount: number
  isLoadingMore: boolean
  showOnlyNew: boolean
  isDroppingCV: boolean
  cvUploadLoading: boolean
}

interface SearchActions {
  setSearchTerm: (v: string) => void
  setQuickFilters: (v: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setActiveTab: (v: SearchState["activeTab"]) => void
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
  setSearchFeedbacks: (v: Record<string, "like" | "dislike"> | ((prev: Record<string, "like" | "dislike">) => Record<string, "like" | "dislike">)) => void
  setDisplayedResultsCount: (v: number) => void
  setIsLoadingMore: (v: boolean) => void
  setShowOnlyNew: (v: boolean) => void
  setIsDroppingCV: (v: boolean) => void
  setCvUploadLoading: (v: boolean) => void
}

interface UseCandidatesSearchStateReturn {
  state: SearchState
  actions: SearchActions
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCandidatesSearchState(): UseCandidatesSearchStateReturn {
  const [searchTerm, setSearchTerm] = useState<string>("")
  const [quickFilters, setQuickFilters] = useState<Set<string>>(new Set())

  const [activeTab, setActiveTab] = useState<SearchState["activeTab"]>("search")
  const [lastSearchQuery, setLastSearchQuery] = useState<string>("")
  const [lastSearchEntities, setLastSearchEntities] = useState<ParsedEntities | null>(null)
  const [lastSearchMode, setLastSearchMode] = useState<string>("")
  const [lastSearchMetadata, setLastSearchMetadata] = useState<SearchMetadata | undefined>(undefined)
  const [lastSearchUsedPearch, setLastSearchUsedPearch] = useState<boolean>(false)
  const [hasSearchResults, setHasSearchResults] = useState<boolean>(false)
  const [searchResultsCount, setSearchResultsCount] = useState<number>(0)
  const [localResultsCount, setLocalResultsCount] = useState<number>(0)
  const [pearchResultsCount, setPearchResultsCount] = useState<number>(0)
  const [creditsUsedInSearch, setCreditsUsedInSearch] = useState<number>(0)
  const [creditsRemaining, setCreditsRemaining] = useState<number | null>(null)
  const [showExpandGlobalOption, setShowExpandGlobalOption] = useState<boolean>(false)

  const [openCreditModals, setOpenCreditModals] = useState<CreditModalsState>({
    hybrid: false,
    global: false,
    email: false,
    phone: false,
  })

  const [showEditQueryModal, setShowEditQueryModal] = useState<boolean>(false)
  const [editQueryValue, setEditQueryValue] = useState<string>("")

  const [showSearchResults, setShowSearchResults] = useState<boolean>(false)
  const [searchSource, setSearchSource] = useState<SearchSource>("hybrid")

  const [currentSearchSource, setCurrentSearchSource] = useState<SearchSource>("local")
  const [showGlobalExpansionConfirm, setShowGlobalExpansionConfirm] = useState<boolean>(false)
  const [hasSearched, setHasSearched] = useState<boolean>(false)
  const [isExpandingToGlobal, setIsExpandingToGlobal] = useState<boolean>(false)

  const [searchExecutionId, setSearchExecutionId] = useState<number>(0)

  const [searchSortBy, setSearchSortBy] = useState<string>("relevance")
  const [searchFeedbacks, setSearchFeedbacks] = useState<Record<string, "like" | "dislike">>({})
  const [displayedResultsCount, setDisplayedResultsCount] = useState<number>(10)
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false)

  const [showOnlyNew, setShowOnlyNew] = useState<boolean>(false)
  const [isDroppingCV, setIsDroppingCV] = useState<boolean>(false)
  const [cvUploadLoading, setCvUploadLoading] = useState<boolean>(false)

  return {
    state: {
      searchTerm,
      quickFilters,
      activeTab,
      lastSearchQuery,
      lastSearchEntities,
      lastSearchMode,
      lastSearchMetadata,
      lastSearchUsedPearch,
      hasSearchResults,
      searchResultsCount,
      localResultsCount,
      pearchResultsCount,
      creditsUsedInSearch,
      creditsRemaining,
      showExpandGlobalOption,
      openCreditModals,
      showEditQueryModal,
      editQueryValue,
      showSearchResults,
      searchSource,
      currentSearchSource,
      showGlobalExpansionConfirm,
      hasSearched,
      isExpandingToGlobal,
      searchExecutionId,
      searchSortBy,
      searchFeedbacks,
      displayedResultsCount,
      isLoadingMore,
      showOnlyNew,
      isDroppingCV,
      cvUploadLoading,
    },
    actions: {
      setSearchTerm,
      setQuickFilters,
      setActiveTab,
      setLastSearchQuery,
      setLastSearchEntities,
      setLastSearchMode,
      setLastSearchMetadata,
      setLastSearchUsedPearch,
      setHasSearchResults,
      setSearchResultsCount,
      setLocalResultsCount,
      setPearchResultsCount,
      setCreditsUsedInSearch,
      setCreditsRemaining,
      setShowExpandGlobalOption,
      setOpenCreditModals,
      setShowEditQueryModal,
      setEditQueryValue,
      setShowSearchResults,
      setSearchSource,
      setCurrentSearchSource,
      setShowGlobalExpansionConfirm,
      setHasSearched,
      setIsExpandingToGlobal,
      setSearchExecutionId,
      setSearchSortBy,
      setSearchFeedbacks,
      setDisplayedResultsCount,
      setIsLoadingMore,
      setShowOnlyNew,
      setIsDroppingCV,
      setCvUploadLoading,
    },
  }
}
