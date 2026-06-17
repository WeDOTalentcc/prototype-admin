"use client"

import { useCandidatesStore } from "@/stores/candidates-store"
import type { ParsedEntities, SearchMetadata } from "@/components/search/smart-search-input"

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
  canLoadMore: boolean
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
  setCanLoadMore: (v: boolean) => void
  setShowOnlyNew: (v: boolean) => void
  setIsDroppingCV: (v: boolean) => void
  setCvUploadLoading: (v: boolean) => void
}

interface UseCandidatesSearchStateReturn {
  state: SearchState
  actions: SearchActions
}

export function useCandidatesSearchState(): UseCandidatesSearchStateReturn {
  const store = useCandidatesStore()

  return {
    state: {
      searchTerm: store.searchTerm,
      quickFilters: store.quickFilters,
      activeTab: store.activeTab,
      lastSearchQuery: store.lastSearchQuery,
      lastSearchEntities: store.lastSearchEntities,
      lastSearchMode: store.lastSearchMode,
      lastSearchMetadata: store.lastSearchMetadata,
      lastSearchUsedPearch: store.lastSearchUsedPearch,
      hasSearchResults: store.hasSearchResults,
      searchResultsCount: store.searchResultsCount,
      localResultsCount: store.localResultsCount,
      pearchResultsCount: store.pearchResultsCount,
      creditsUsedInSearch: store.creditsUsedInSearch,
      creditsRemaining: store.creditsRemaining,
      showExpandGlobalOption: store.showExpandGlobalOption,
      openCreditModals: store.openCreditModals,
      showEditQueryModal: store.showEditQueryModal,
      editQueryValue: store.editQueryValue,
      showSearchResults: store.showSearchResults,
      searchSource: store.searchSource,
      currentSearchSource: store.currentSearchSource,
      showGlobalExpansionConfirm: store.showGlobalExpansionConfirm,
      hasSearched: store.hasSearched,
      isExpandingToGlobal: store.isExpandingToGlobal,
      searchExecutionId: store.searchExecutionId,
      searchSortBy: store.searchSortBy,
      searchFeedbacks: store.searchFeedbacks,
      displayedResultsCount: store.displayedResultsCount,
      isLoadingMore: store.isLoadingMore,
      canLoadMore: store.canLoadMore,
      showOnlyNew: store.showOnlyNew,
      isDroppingCV: store.isDroppingCV,
      cvUploadLoading: store.cvUploadLoading,
    },
    actions: {
      setSearchTerm: store.setSearchTerm,
      setQuickFilters: store.setQuickFilters,
      setActiveTab: store.setActiveTab,
      setLastSearchQuery: store.setLastSearchQuery,
      setLastSearchEntities: store.setLastSearchEntities,
      setLastSearchMode: store.setLastSearchMode,
      setLastSearchMetadata: store.setLastSearchMetadata,
      setLastSearchUsedPearch: store.setLastSearchUsedPearch,
      setHasSearchResults: store.setHasSearchResults,
      setSearchResultsCount: store.setSearchResultsCount,
      setLocalResultsCount: store.setLocalResultsCount,
      setPearchResultsCount: store.setPearchResultsCount,
      setCreditsUsedInSearch: store.setCreditsUsedInSearch,
      setCreditsRemaining: store.setCreditsRemaining,
      setShowExpandGlobalOption: store.setShowExpandGlobalOption,
      setOpenCreditModals: store.setOpenCreditModals,
      setShowEditQueryModal: store.setShowEditQueryModal,
      setEditQueryValue: store.setEditQueryValue,
      setShowSearchResults: store.setShowSearchResults,
      setSearchSource: store.setSearchSource,
      setCurrentSearchSource: store.setCurrentSearchSource,
      setShowGlobalExpansionConfirm: store.setShowGlobalExpansionConfirm,
      setHasSearched: store.setHasSearched,
      setIsExpandingToGlobal: store.setIsExpandingToGlobal,
      setSearchExecutionId: store.setSearchExecutionId,
      setSearchSortBy: store.setSearchSortBy,
      setSearchFeedbacks: store.setSearchFeedbacks,
      setDisplayedResultsCount: store.setDisplayedResultsCount,
      setIsLoadingMore: store.setIsLoadingMore,
      setCanLoadMore: store.setCanLoadMore,
      setShowOnlyNew: store.setShowOnlyNew,
      setIsDroppingCV: store.setIsDroppingCV,
      setCvUploadLoading: store.setCvUploadLoading,
    },
  }
}
