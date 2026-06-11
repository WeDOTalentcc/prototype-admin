"use client"

import React from "react"
import type { Dispatch, SetStateAction } from "react"
import { useTranslations } from "next-intl"
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import { toast } from "sonner"
import type { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime"
import { classifyPercentageScore } from "@/lib/score-utils"
import { buildSavedSearchPayload } from "@/components/pages/candidates/saved-search-utils"
import type { SearchFilters } from "@/components/search/advanced-filters-modal"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
import type { ParsedCVResponse } from "@/components/cv"
import { createCellRenderer } from "@/components/pages/candidates/CandidateTableCellRenderer"
import { useContactValidation } from "@/hooks/candidates/useContactValidation"
import { useCandidatesColumnConfig } from "./useCandidatesColumnConfig"
import { useCandidatesFilterSort } from "./useCandidatesFilterSort"
import { useCandidatesActions } from "./useCandidatesActions"
import { useCandidatesInteractions } from "./useCandidatesInteractions"
import { useCandidatesLIAHandlers } from "./useCandidatesLIAHandlers"
import { mapCandidateToInternal as _mapCandidateToInternal } from "./useCandidatesExecuteSearch"
import type { Candidate } from "@/components/pages/candidates/types"
import type { RevealedContacts } from "@/stores/candidates-store"
import type { ChatMessage, PearchSearchOptions } from "./candidates-core"
import type { SearchTab } from "./useCandidatesUIState"
import type { TableFilters } from "@/hooks/candidates/use-candidate-filters"
import { getDefaultTableFilters } from "@/hooks/candidates/use-candidate-filters"
import {
  getActiveTableFiltersCount,
  getActiveAdvancedFiltersCount,
  getActiveSearchFiltersCount,
  toggleTableFilterValue,
  type AdvancedFilters,
} from "./candidates-core"
import type { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"

export interface UseCandidatesViewCompositionParams {
  candidates: Candidate[]
  setCandidates: (v: Candidate[] | ((prev: Candidate[]) => Candidate[])) => void
  searchResults: {
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }
  searchTerm: string
  hasSearchResults: boolean
  quickFilters: Set<string>
  columnFilters: { position: string[]; company: string[]; location: string[]; scoreRange: string[]; bigFive?: Record<string, string> }
  advancedFilters: AdvancedFilters
  tableFilters: TableFilters
  setTableFilters: Dispatch<SetStateAction<TableFilters>>
  sortBy: string
  setSortBy: (v: string) => void
  sortOrder: 'asc' | 'desc'
  setSortOrder: (v: 'asc' | 'desc') => void
  searchSortBy: string
  searchFeedbacks: Record<string, 'like' | 'dislike'>
  displayedResultsCount: number
  showSearchResults: boolean
  setShowSearchResults: (v: boolean) => void
  currentPage: number
  itemsPerPage: number
  showOnlyNew: boolean
  viewedCandidateIds: Set<string>
  activeTab: 'search' | 'history' | 'favorites' | 'lists' | 'saved-searches' | 'agents'
  setActiveTab: (v: 'search' | 'history' | 'favorites' | 'lists' | 'saved-searches' | 'agents') => void
  viewingList: { id: string; name: string; color?: string } | null
  setViewingList: (v: { id: string; name: string; color?: string } | null) => void
  candidateListsForModal: Array<{ id: string; name: string }>
  selectedCandidatesForBatch: Set<string>
  setSelectedCandidatesForBatch: Dispatch<SetStateAction<Set<string>>>
  isSavingToBase: boolean
  setIsSavingToBase: (v: boolean) => void
  isAddingToList: boolean
  setIsAddingToList: (v: boolean) => void
  showAddToListModal: boolean
  setShowAddToListModal: (v: boolean) => void
  addToListCandidateIds: string[]
  setAddToListCandidateIds: Dispatch<SetStateAction<string[]>>
  addToListCandidateNames: string[]
  setAddToListCandidateNames: Dispatch<SetStateAction<string[]>>
  showUnsavedWarningModal: boolean
  setShowUnsavedWarningModal: (v: boolean) => void
  pendingTabChange: string | null
  setPendingTabChange: (v: string | null) => void
  hasUnsavedPearchCandidates: boolean
  unsavedPearchCandidates: Candidate[]
  lastSearchQuery: string
  revealedContacts: RevealedContacts
  expandedRows: Set<string>
  setExpandedRows: Dispatch<SetStateAction<Set<string>>>
  isPreviewMaximized: boolean
  setIsPreviewMaximized: (v: boolean) => void
  previewWidth: number
  setPreviewWidth: (v: number) => void
  setPreviewCandidate: (v: Candidate | null) => void
  setShowCandidatePreview: (v: boolean) => void
  setShowPreview: (v: boolean) => void
  setSelectedCandidate: (v: Candidate | null) => void
  setShowCandidatePage: (v: boolean) => void
  setShowSidePreview: (v: boolean) => void
  setSidePreviewCandidate: (v: Candidate | null) => void
  setUnifiedModalCandidate: (v: Candidate | null) => void
  setUnifiedModalSelectedCandidates: (v: Array<{ id: string; name: string; email?: string; phone?: string; avatar?: string }>) => void
  setUnifiedModalType: (v: CommunicationType) => void
  setUnifiedModalOpen: (v: boolean) => void
  setShowScheduleModal: (v: boolean) => void
  setShowContactModal: (v: boolean) => void
  setSelectedCandidateForAction: (v: Candidate | null) => void
  setShowComparisonModal: (v: boolean) => void
  setShowQuickViewModal: (v: boolean) => void
  setShowBatchApproval: (v: boolean) => void
  setParsedCVData: (v: ParsedCVResponse | null) => void
  setShowCVPreviewModal: (v: boolean) => void
  setShowAddCandidateModal: (v: boolean) => void
  onAddRecentItem?: (item: { id: string; type: 'chat' | 'vaga' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  markCandidateAsViewed: (id: string) => void
  handleBulkActionComplete: () => void
  chatMessages: ChatMessage[]
  setChatMessages: Dispatch<SetStateAction<ChatMessage[]>>
  liaPromptValue: string
  setLiaPromptValue: (v: string) => void
  activeSearchTab: SearchTab
  setActiveSearchTab: (v: SearchTab) => void
  talentConversationId: string | undefined
  setTalentConversationId: (v: string | undefined) => void
  liaIsParsingEntities: boolean
  setLiaIsParsingEntities: (v: boolean) => void
  liaSuggestions: string[]
  setLiaSuggestions: (v: string[]) => void
  showLiaSuggestions: boolean
  setShowLiaSuggestions: (v: boolean) => void
  showLiaAssistant: boolean
  setShowLiaAssistant: (v: boolean) => void
  activeSearchFilters: SearchFilters
  liaPromptEntities: import('@/components/search/smart-search-input').ParsedEntities
  setLiaPromptEntities: (v: import('@/components/search/smart-search-input').ParsedEntities) => void
  selectedCandidate: Candidate | null
  showQuickViewModal: boolean
  showComparisonModal: boolean
  isLIAThinking: boolean
  setIsLIAThinking: (v: boolean) => void
  setWsiInviteCandidate: (v: Candidate | null) => void
  setShowWSIInviteModal: (v: boolean) => void
  setWsiCandidateForScreening: (v: Candidate | null) => void
  setShowWSITextModal: (v: boolean) => void
  setShowWSIVoiceModal: (v: boolean) => void
  setShowRubricModal: (v: boolean) => void
  executeSearch: (query: string, entities?: import('@/components/search/smart-search-input').ParsedEntities, mode?: import('@/components/search/smart-search-input').SearchMode, metadata?: import('@/components/search/smart-search-input').SearchMetadata, usePearch?: boolean) => Promise<void>
  talentFunnel: ReturnType<typeof useTalentFunnel>
  user: Record<string, unknown> | null
  router: AppRouterInstance
  openRevealModal: (candidate: Candidate, type: 'email' | 'phone') => void
  handleSearchFeedbackChange: (candidateId: string, candidateName: string, feedback: 'like' | 'dislike' | null) => void
  pearchSearchOptions: PearchSearchOptions
  setSearchTerm: (v: string) => void
  setQuickFilters: Dispatch<SetStateAction<Set<string>>>
  setSelectedTemplate: (v: string) => void
  setColumnFilters: Dispatch<SetStateAction<Record<string, unknown>>>
}

export function useCandidatesViewComposition(params: UseCandidatesViewCompositionParams) {
  const columnConfigHook = useCandidatesColumnConfig()
  const tCells = useTranslations('candidates.cells')
  const tView = useTranslations('candidates.viewComposition')

  const _contactsToValidate = React.useMemo(() => {
    const out: { candidate_id: string; email?: string | null; phone?: string | null }[] = []
    for (const cand of params.candidates) {
      const rc = params.revealedContacts[cand.id] || {}
      const email = rc.email || cand.email
      const phone = rc.phone || cand.phone || cand.mobile_phone
      if (email || phone) out.push({ candidate_id: cand.id, email: email || null, phone: phone || null })
    }
    return out
  }, [params.candidates, params.revealedContacts])
  const { validity: _contactValidity } = useContactValidation(_contactsToValidate)

  const renderCellValue = createCellRenderer({
    searchFeedbacks: params.searchFeedbacks,
    revealedContacts: params.revealedContacts,
    searchQuery: params.searchResults.query,
    viewedCandidateIds: params.viewedCandidateIds,
    expandedRows: params.expandedRows,
    onSearchFeedbackChange: params.handleSearchFeedbackChange,
    contactValidity: _contactValidity,
    onRevealContact: params.openRevealModal,
    onToggleExpandedRow: (candidateId: string) =>
      params.setExpandedRows(prev => {
        const newSet = new Set(prev)
        if (newSet.has(candidateId)) newSet.delete(candidateId)
        else newSet.add(candidateId)
        return newSet
      }),
    t: tCells as unknown as (key: string, params?: Record<string, unknown>) => string,
  })

  const filterSort = useCandidatesFilterSort({
    candidates: params.candidates,
    searchTerm: params.searchTerm,
    hasSearchResults: params.hasSearchResults,
    quickFilters: params.quickFilters,
    columnFilters: params.columnFilters,
    advancedFilters: params.advancedFilters as unknown as Record<string, string[]>,
    tableFilters: params.tableFilters,
    sortBy: params.sortBy,
    sortOrder: params.sortOrder,
    searchSortBy: params.searchSortBy,
    searchFeedbacks: params.searchFeedbacks,
    displayedResultsCount: params.displayedResultsCount,
    showSearchResults: params.showSearchResults,
    currentPage: params.currentPage,
    itemsPerPage: params.itemsPerPage,
    showOnlyNew: params.showOnlyNew,
    viewedCandidateIds: params.viewedCandidateIds,
  })

  const candidatesActions = useCandidatesActions({
    candidates: params.candidates,
    revealedContacts: params.revealedContacts,
    setCandidates: params.setCandidates,
    activeTab: params.activeTab,
    setActiveTab: (v: string) => params.setActiveTab(v as 'search' | 'history' | 'favorites' | 'lists' | 'saved-searches' | 'agents'),
    viewingList: params.viewingList,
    setViewingList: params.setViewingList,
    candidateListsForModal: params.candidateListsForModal,
    selectedCandidatesForBatch: params.selectedCandidatesForBatch,
    setSelectedCandidatesForBatch: params.setSelectedCandidatesForBatch,
    isSavingToBase: params.isSavingToBase,
    setIsSavingToBase: params.setIsSavingToBase,
    isAddingToList: params.isAddingToList,
    setIsAddingToList: params.setIsAddingToList,
    showAddToListModal: params.showAddToListModal,
    setShowAddToListModal: params.setShowAddToListModal,
    addToListCandidateIds: params.addToListCandidateIds,
    setAddToListCandidateIds: params.setAddToListCandidateIds,
    addToListCandidateNames: params.addToListCandidateNames,
    setAddToListCandidateNames: params.setAddToListCandidateNames,
    showUnsavedWarningModal: params.showUnsavedWarningModal,
    setShowUnsavedWarningModal: params.setShowUnsavedWarningModal,
    pendingTabChange: params.pendingTabChange,
    setPendingTabChange: params.setPendingTabChange,
    hasUnsavedPearchCandidates: params.hasUnsavedPearchCandidates,
    unsavedPearchCandidates: params.unsavedPearchCandidates,
    showSearchResults: params.showSearchResults,
    setShowSearchResults: params.setShowSearchResults,
    lastSearchQuery: params.lastSearchQuery,
    deselectAllCandidates: () => params.setSelectedCandidatesForBatch(new Set()),
    user: params.user,
  })

  const handleAICommand = async (command: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleAICommand(command)
  }

  const interactions = useCandidatesInteractions({
    candidates: params.candidates,
    setCandidates: params.setCandidates,
    sortedCandidates: filterSort.sortedCandidates,
    selectedCandidatesForBatch: params.selectedCandidatesForBatch,
    setSelectedCandidatesForBatch: params.setSelectedCandidatesForBatch,
    setPreviewCandidate: params.setPreviewCandidate,
    setShowCandidatePreview: params.setShowCandidatePreview,
    setIsPreviewMaximized: (fn: ((prev: boolean) => boolean) | boolean) => params.setIsPreviewMaximized(typeof fn === 'function' ? fn(false) : fn),
    isPreviewMaximized: params.isPreviewMaximized,
    setShowPreview: params.setShowPreview,
    setSelectedCandidate: params.setSelectedCandidate,
    setShowCandidatePage: params.setShowCandidatePage,
    setShowSidePreview: params.setShowSidePreview,
    setSidePreviewCandidate: params.setSidePreviewCandidate,
    previewWidth: params.previewWidth,
    setPreviewWidth: params.setPreviewWidth,
    setUnifiedModalCandidate: params.setUnifiedModalCandidate,
    setUnifiedModalSelectedCandidates: params.setUnifiedModalSelectedCandidates,
    setUnifiedModalType: params.setUnifiedModalType,
    setUnifiedModalOpen: params.setUnifiedModalOpen,
    setShowScheduleModal: params.setShowScheduleModal,
    setShowContactModal: params.setShowContactModal,
    setSelectedCandidateForAction: params.setSelectedCandidateForAction,
    setShowComparisonModal: params.setShowComparisonModal,
    setShowQuickViewModal: params.setShowQuickViewModal,
    setShowBatchApproval: params.setShowBatchApproval,
    setParsedCVData: params.setParsedCVData,
    setShowCVPreviewModal: params.setShowCVPreviewModal,
    onAddRecentItem: params.onAddRecentItem,
    markCandidateAsViewed: params.markCandidateAsViewed,
    handleBulkActionComplete: params.handleBulkActionComplete,
    handleAICommand,
    deselectAllCandidates: () => params.setSelectedCandidatesForBatch(new Set()),
  })

  const handleStartWSITextScreening = (candidate: Candidate) => { params.setWsiInviteCandidate(candidate); params.setShowWSIInviteModal(true) }
  const handleOpenWSIModal = (candidate: Candidate) => { params.setWsiCandidateForScreening(candidate); params.setShowWSITextModal(true) }
  const handleStartWSIVoiceScreening = (candidate: Candidate) => { params.setWsiCandidateForScreening(candidate); params.setShowWSIVoiceModal(true) }

  const liaHandlersRef = React.useRef<ReturnType<typeof useCandidatesLIAHandlers> | null>(null)
  const handleLIAChatMessage = async (message: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleLIAChatMessage(message)
  }

  const liaHandlers = useCandidatesLIAHandlers({
    candidates: params.candidates,
    setCandidates: params.setCandidates,
    chatMessages: params.chatMessages,
    setChatMessages: params.setChatMessages,
    liaPromptValue: params.liaPromptValue,
    setLiaPromptValue: params.setLiaPromptValue,
    activeSearchTab: params.activeSearchTab,
    setActiveSearchTab: params.setActiveSearchTab,
    talentConversationId: params.talentConversationId,
    setTalentConversationId: params.setTalentConversationId,
    liaIsParsingEntities: params.liaIsParsingEntities,
    setLiaIsParsingEntities: params.setLiaIsParsingEntities,
    liaSuggestions: params.liaSuggestions,
    setLiaSuggestions: params.setLiaSuggestions,
    showLiaSuggestions: params.showLiaSuggestions,
    setShowLiaSuggestions: params.setShowLiaSuggestions,
    showLiaAssistant: params.showLiaAssistant,
    setShowLiaAssistant: params.setShowLiaAssistant,
    selectedCandidatesForBatch: params.selectedCandidatesForBatch,
    setSelectedCandidatesForBatch: params.setSelectedCandidatesForBatch,
    searchResults: params.searchResults,
    lastSearchQuery: params.lastSearchQuery,
    activeSearchFilters: params.activeSearchFilters,
    liaPromptEntities: params.liaPromptEntities,
    setLiaPromptEntities: params.setLiaPromptEntities,
    selectedCandidate: params.selectedCandidate,
    setSelectedCandidate: params.setSelectedCandidate,
    showQuickViewModal: params.showQuickViewModal,
    setShowQuickViewModal: params.setShowQuickViewModal,
    showComparisonModal: params.showComparisonModal,
    setShowComparisonModal: params.setShowComparisonModal,
    setShowScheduleModal: params.setShowScheduleModal,
    setUnifiedModalCandidate: params.setUnifiedModalCandidate,
    setUnifiedModalType: params.setUnifiedModalType,
    setUnifiedModalOpen: params.setUnifiedModalOpen,
    setShowAddToListModal: params.setShowAddToListModal,
    isLIAThinking: params.isLIAThinking,
    setIsLIAThinking: params.setIsLIAThinking,
    handleStartWSITextScreening,
    handleOpenWSIModal,
    openUnifiedModal: interactions.openUnifiedModal,
    handleCandidateClick: interactions.handleCandidateClick,
    executeSearch: params.executeSearch,
    talentFunnel: params.talentFunnel,
    user: params.user,
    router: params.router,
  })
  liaHandlersRef.current = liaHandlers

  const handleAddCandidate = (newCandidate: Record<string, unknown>) => {
    interactions.handleAddCandidate(newCandidate, params.setShowAddCandidateModal)
  }

  const handleSort = (field: string) => {
    if (params.sortBy === field) params.setSortOrder(params.sortOrder === 'asc' ? 'desc' : 'asc')
    else { params.setSortBy(field); params.setSortOrder('desc') }
  }
  const getSortIcon = (field: string) => {
    if (params.sortBy !== field) return <ArrowUpDown className="w-3 h-3 ml-1" />
    return params.sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
  }

  const _getActiveTableFiltersCount = () => getActiveTableFiltersCount(params.tableFilters)
  const _getActiveAdvancedFiltersCount = () => getActiveAdvancedFiltersCount(params.advancedFilters)
  const _getActiveSearchFiltersCount = () => getActiveSearchFiltersCount(params.quickFilters, params.advancedFilters)
  const toggleTableFilter = (category: keyof TableFilters, value: string) => {
    params.setTableFilters(prev => toggleTableFilterValue(prev, category, value))
  }
  const clearAllTableFilters = () => params.setTableFilters(getDefaultTableFilters())
  const clearAllFilters = () => {
    params.setSearchTerm('')
    params.setQuickFilters(new Set())
    params.setSelectedTemplate('')
    params.setColumnFilters({
      position: [], company: [], location: [], scoreRange: [],
      bigFive: { openness: '', conscientiousness: '', extraversion: '', agreeableness: '', neuroticism: '' },
    })
    clearAllTableFilters()
  }

  const saveCurrentSearch = () => {
    // P1-7: persiste no produtor canonico (addSavedSearch) que a aba Buscas
    // Salvas le — antes gravava em sessionStorage('current-search-data') morto.
    params.talentFunnel.addSavedSearch(
      buildSavedSearchPayload({
        searchTerm: params.searchTerm,
        quickFilters: Array.from(params.quickFilters),
        dateLabel: new Date().toLocaleDateString(),
        namePrefix: tView('searchNamePrefix'),
      })
    )
    params.setActiveTab('saved-searches')
    toast.success(tView('searchSaved'), { description: tView('candidatesFound', { count: filterSort.sortedCandidates.length }) })
  }

  const getScoreColor = (score: number) => {
    const cls = classifyPercentageScore(score)
    switch (cls.level) {
      case 'excellent': return 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success border-status-success/30 dark:border-status-success/30'
      case 'good': return 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-subtle'
      case 'satisfactory': return 'bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning border-status-warning/30 dark:border-status-warning/30'
      default: return 'bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error border-status-error/30 dark:border-status-error/30'
    }
  }

  return {
    columnConfigHook,
    renderCellValue,
    filterSort,
    candidatesActions,
    interactions,
    liaHandlers,
    handleLIAChatMessage,
    handleAICommand,
    handleAddCandidate,
    handleStartWSITextScreening,
    handleOpenWSIModal,
    handleStartWSIVoiceScreening,
    handleSort,
    getSortIcon,
    getActiveTableFiltersCount: _getActiveTableFiltersCount,
    getActiveAdvancedFiltersCount: _getActiveAdvancedFiltersCount,
    getActiveSearchFiltersCount: _getActiveSearchFiltersCount,
    toggleTableFilter,
    clearAllTableFilters,
    clearAllFilters,
    saveCurrentSearch,
    getScoreColor,
    mapCandidateToInternal: _mapCandidateToInternal,
  }
}
