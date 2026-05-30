"use client"

import React, { useCallback } from "react"
import type { Dispatch, SetStateAction } from "react"
import type { ParsedEntities, SearchMode, SearchMetadata } from "@/components/search/smart-search-input"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { Candidate } from "@/components/pages/candidates/types"
import type { ChatMessage, PearchSearchOptions } from "./candidates-core"
import type { SearchTab } from "./useCandidatesUIState"
import { useCandidatesArchetypes } from "./useCandidatesArchetypes"
import { useRevealContact } from "./useRevealContact"
import { useCandidatesExecuteSearch } from "./useCandidatesExecuteSearch"
import { useCandidatesCVHandlers } from "./useCandidatesCVHandlers"
import { useCandidatesSearch } from "./useCandidatesSearch"
import type { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"
import type { useHideViewedCandidates } from "@/hooks/candidates/useHideViewedCandidates"

type SearchSource = 'local' | 'global' | 'hybrid'

interface CreditModalsState {
  hybrid: boolean
  global: boolean
  email: boolean
  phone: boolean
}

interface SearchResults {
  local: Candidate[]
  global: Candidate[]
  localCount: number
  globalCount: number
  query: string
  isLoading: boolean
  showGlobalResults: boolean
  globalDismissed: boolean
  isEnrichingContacts: boolean
  filteredNoContact: number
  enrichmentAttempted: number
  filteredCandidates: import('./useCandidatesExecuteSearch').DiscardedCandidate[]
}

interface PendingSearchRequest {
  query: string
  entities?: ParsedEntities
  mode?: SearchMode
  metadata?: SearchMetadata
}

export interface UseCandidatesSearchCompositionParams {
  searchSource: SearchSource
  pearchSearchOptions: PearchSearchOptions
  setCandidates: (v: Candidate[] | ((prev: Candidate[]) => Candidate[])) => void
  setHasSearchResults: (v: boolean) => void
  setSearchResultsCount: (v: number) => void
  setLocalResultsCount: (v: number) => void
  setPearchResultsCount: (v: number) => void
  setLastSearchQuery: (v: string) => void
  setLastSearchMode: (v: string) => void
  setActiveSearchTab: (v: SearchTab) => void
  setLiaPromptValue: (v: string) => void
  setChatMessages: Dispatch<SetStateAction<ChatMessage[]>>
  creditsRemaining: number | null
  setCreditsRemaining: (v: number | null) => void
  searchThreadId: string | undefined
  setSearchThreadId: (id: string | undefined) => void
  setSearchFingerprint: (fp: string | undefined) => void
  hideViewedCandidatesFilter: ReturnType<typeof useHideViewedCandidates>['filterCandidates']
  talentFunnel: ReturnType<typeof useTalentFunnel>
  setSearchResults: Dispatch<SetStateAction<SearchResults>>
  setShowSearchResults: (v: boolean) => void
  setDisplayedResultsCount: (v: number) => void
  setCurrentSearchSource: (v: SearchSource) => void
  setHasSearched: (v: boolean) => void
  setLastSearchEntities: (v: ParsedEntities | null) => void
  setLastSearchMetadata: (v: SearchMetadata | undefined) => void
  setLastSearchUsedPearch: (v: boolean) => void
  setSearchExecutionId: (v: number | ((prev: number) => number)) => void
  setShowExpandGlobalOption: (v: boolean) => void
  setIsLoading: (v: boolean) => void
  setIsSearchActive: (v: boolean) => void
  setIsDroppingCV: (v: boolean) => void
  setCvUploadLoading: (v: boolean) => void
  candidates: Candidate[]
  searchResults: SearchResults
  searchTerm: string
  lastSearchQuery: string
  lastSearchEntities: ParsedEntities | null
  lastSearchMode: string
  lastSearchMetadata: SearchMetadata | undefined
  lastSearchUsedPearch: boolean
  currentSearchSource: SearchSource
  openCreditModals: CreditModalsState
  setOpenCreditModals: Dispatch<SetStateAction<CreditModalsState>>
  setPearchSearchOptions: Dispatch<SetStateAction<PearchSearchOptions>>
  creditsUsedInSearch: number
  setCreditsUsedInSearch: (v: number) => void
  pearchResultsCount: number
  localResultsCount: number
  searchResultsCount: number
  showSearchResults: boolean
  hasSearchResults: boolean
  showGlobalExpansionConfirm: boolean
  setShowGlobalExpansionConfirm: (v: boolean) => void
  isExpandingToGlobal: boolean
  setIsExpandingToGlobal: (v: boolean) => void
  displayedResultsCount: number
  isLoadingMore: boolean
  setIsLoadingMore: (v: boolean) => void
  searchFeedbacks: Record<string, 'like' | 'dislike'>
  setSearchFeedbacks: Dispatch<SetStateAction<Record<string, 'like' | 'dislike'>>>
  hasSearched: boolean
  showExpandGlobalOption: boolean
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: 'hybrid' | 'global' | null
  setPendingSourceChange: (v: 'hybrid' | 'global' | null) => void
  showContactFilterModal: boolean
  setShowContactFilterModal: (v: boolean) => void
  pendingContactFilter: 'email' | 'phone' | null
  setPendingContactFilter: (v: 'email' | 'phone' | null) => void
  showCreditConfirmation: boolean
  setShowCreditConfirmation: (v: boolean) => void
  pendingSearchRequest: PendingSearchRequest | null
  setPendingSearchRequest: Dispatch<SetStateAction<PendingSearchRequest | null>>
  activeSearchFilters: SearchFilters
  setActiveSearchFilters: Dispatch<SetStateAction<SearchFilters>>
  setSelectedTemplate: (v: string) => void
  setSearchSource: (v: SearchSource) => void
  searchExecutionId: number
  user: Record<string, unknown> | null
}

export function useCandidatesSearchComposition(params: UseCandidatesSearchCompositionParams) {
  const archetypesHook = useCandidatesArchetypes({
    searchSource: params.searchSource,
    pearchSearchOptions: params.pearchSearchOptions,
    setCandidates: params.setCandidates,
    setHasSearchResults: params.setHasSearchResults,
    setSearchResultsCount: params.setSearchResultsCount,
    setLocalResultsCount: params.setLocalResultsCount,
    setPearchResultsCount: params.setPearchResultsCount,
    setLastSearchQuery: params.setLastSearchQuery,
    setLastSearchMode: params.setLastSearchMode,
    setActiveSearchTab: (_v: string) => params.setActiveSearchTab(_v as SearchTab),
    setLiaPromptValue: params.setLiaPromptValue,
    setChatMessages: params.setChatMessages,
  })

  const revealContactHook = useRevealContact({
    setCreditsRemaining: (fn) =>
      params.setCreditsRemaining(typeof fn === 'function' ? fn(params.creditsRemaining ?? 0) : fn),
  })

  const { setLastSuccessfulQuery: archetypeSetLastSuccessfulQuery } = archetypesHook.actions

  const { executeSearch } = useCandidatesExecuteSearch({
    searchSource: params.searchSource,
    pearchSearchOptions: params.pearchSearchOptions,
    searchThreadId: params.searchThreadId,
    setSearchThreadId: params.setSearchThreadId,
    setSearchFingerprint: params.setSearchFingerprint,
    setSearchFeedbacks: params.setSearchFeedbacks,
    hideViewedCandidatesFilter: params.hideViewedCandidatesFilter,
    talentFunnel: params.talentFunnel as unknown as { addToHistory: (entry: Record<string, unknown>) => void },
    setCandidates: params.setCandidates,
    setSearchResults: params.setSearchResults as Parameters<typeof useCandidatesExecuteSearch>[0]['setSearchResults'],
    setHasSearchResults: params.setHasSearchResults,
    setSearchResultsCount: params.setSearchResultsCount,
    setLocalResultsCount: params.setLocalResultsCount,
    setPearchResultsCount: params.setPearchResultsCount,
    setCreditsUsedInSearch: params.setCreditsUsedInSearch,
    setCreditsRemaining: (fn) =>
      params.setCreditsRemaining(typeof fn === 'function' ? fn(params.creditsRemaining ?? 0) : fn),
    setShowSearchResults: params.setShowSearchResults,
    setDisplayedResultsCount: params.setDisplayedResultsCount,
    setCurrentSearchSource: (s: string) => params.setCurrentSearchSource(s as typeof params.currentSearchSource),
    setHasSearched: params.setHasSearched,
    setLastSearchEntities: params.setLastSearchEntities,
    setLastSearchMetadata: params.setLastSearchMetadata,
    setLastSearchUsedPearch: params.setLastSearchUsedPearch,
    setSearchExecutionId: params.setSearchExecutionId,
    setShowExpandGlobalOption: params.setShowExpandGlobalOption,
    setLastSuccessfulQuery: archetypeSetLastSuccessfulQuery,
    setChatMessages: params.setChatMessages,
    setIsLoading: params.setIsLoading,
    setIsSearchActive: params.setIsSearchActive,
  })

  const cvHandlers = useCandidatesCVHandlers({
    setCandidates: params.setCandidates,
    setIsDroppingCV: params.setIsDroppingCV,
    setCvUploadLoading: params.setCvUploadLoading,
    setHasSearchResults: params.setHasSearchResults,
    setSearchResultsCount: params.setSearchResultsCount,
    setShowSearchResults: params.setShowSearchResults,
    setDisplayedResultsCount: params.setDisplayedResultsCount,
    setChatMessages: params.setChatMessages,
  })

  const searchHandlers = useCandidatesSearch({
    candidates: params.candidates,
    setCandidates: params.setCandidates,
    searchResults: params.searchResults,
    setSearchResults: params.setSearchResults as Parameters<typeof useCandidatesSearch>[0]['setSearchResults'],
    searchTerm: params.searchTerm,
    lastSearchQuery: params.lastSearchQuery,
    lastSearchEntities: params.lastSearchEntities,
    lastSearchMode: params.lastSearchMode,
    lastSearchMetadata: params.lastSearchMetadata,
    lastSearchUsedPearch: params.lastSearchUsedPearch,
    searchSource: params.searchSource,
    setSearchSource: params.setSearchSource,
    currentSearchSource: params.currentSearchSource,
    setCurrentSearchSource: params.setCurrentSearchSource,
    openCreditModals: params.openCreditModals,
    setOpenCreditModals: params.setOpenCreditModals,
    pearchSearchOptions: params.pearchSearchOptions,
    setPearchSearchOptions: params.setPearchSearchOptions,
    creditsRemaining: params.creditsRemaining,
    setCreditsRemaining: params.setCreditsRemaining,
    creditsUsedInSearch: params.creditsUsedInSearch,
    setCreditsUsedInSearch: params.setCreditsUsedInSearch,
    pearchResultsCount: params.pearchResultsCount,
    setPearchResultsCount: params.setPearchResultsCount,
    localResultsCount: params.localResultsCount,
    setLocalResultsCount: params.setLocalResultsCount,
    searchResultsCount: params.searchResultsCount,
    setSearchResultsCount: params.setSearchResultsCount,
    showSearchResults: params.showSearchResults,
    setShowSearchResults: params.setShowSearchResults,
    hasSearchResults: params.hasSearchResults,
    setHasSearchResults: params.setHasSearchResults,
    showGlobalExpansionConfirm: params.showGlobalExpansionConfirm,
    setShowGlobalExpansionConfirm: params.setShowGlobalExpansionConfirm,
    isExpandingToGlobal: params.isExpandingToGlobal,
    setIsExpandingToGlobal: params.setIsExpandingToGlobal,
    displayedResultsCount: params.displayedResultsCount,
    setDisplayedResultsCount: params.setDisplayedResultsCount as unknown as (v: number | ((prev: number) => number)) => void,
    isLoadingMore: params.isLoadingMore,
    setIsLoadingMore: params.setIsLoadingMore,
    searchFeedbacks: params.searchFeedbacks,
    setSearchFeedbacks: params.setSearchFeedbacks,
    hasSearched: params.hasSearched,
    lastSuccessfulQuery: archetypesHook.state.lastSuccessfulQuery,
    setSearchThreadId: params.setSearchThreadId,
    setSearchFingerprint: params.setSearchFingerprint,
    searchThreadId: params.searchThreadId,
    showExpandGlobalOption: params.showExpandGlobalOption,
    setShowExpandGlobalOption: params.setShowExpandGlobalOption,
    setChatMessages: params.setChatMessages as unknown as (v: unknown[] | ((prev: unknown[]) => unknown[])) => void,
    showSourceChangeModal: params.showSourceChangeModal,
    setShowSourceChangeModal: params.setShowSourceChangeModal,
    pendingSourceChange: params.pendingSourceChange,
    setPendingSourceChange: params.setPendingSourceChange,
    showContactFilterModal: params.showContactFilterModal,
    setShowContactFilterModal: params.setShowContactFilterModal,
    pendingContactFilter: params.pendingContactFilter,
    setPendingContactFilter: params.setPendingContactFilter,
    showCreditConfirmation: params.showCreditConfirmation,
    setShowCreditConfirmation: params.setShowCreditConfirmation,
    pendingSearchRequest: params.pendingSearchRequest,
    setPendingSearchRequest: params.setPendingSearchRequest,
    activeSearchFilters: params.activeSearchFilters,
    setActiveSearchFilters: params.setActiveSearchFilters,
    setSelectedTemplate: params.setSelectedTemplate,
    executeSearch: (query: string, entities?: import("@/components/search/smart-search-input").ParsedEntities | null, mode?: import("@/components/search/smart-search-input").SearchMode, metadata?: import("@/components/search/smart-search-input").SearchMetadata, usePearch?: boolean) => executeSearch(query, entities ?? undefined, mode, metadata, usePearch),
    user: params.user,
  })

  return {
    archetypesHook,
    revealContactHook,
    executeSearch,
    cvHandlers,
    searchHandlers,
  }
}
