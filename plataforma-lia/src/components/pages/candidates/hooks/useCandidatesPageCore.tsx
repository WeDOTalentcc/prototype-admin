"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { type ParsedEntities, type SmartSearchInputProps } from "@/components/search/smart-search-input"

import { useJWTAuth } from "@/contexts/auth-context"
import { useCandidatesStore } from "@/stores/candidates-store"
import { useLoadingWatchdog } from "@/hooks/shared/use-loading-watchdog"
import { useGlobalSearchSettings } from "@/hooks/search/useGlobalSearchSettings"
import { useHideViewedCandidates } from "@/hooks/candidates/useHideViewedCandidates"
import { useCandidateFilters, getDefaultTableFilters } from "@/hooks/candidates/use-candidate-filters"
import { useCandidateSelection } from "@/hooks/candidates/use-candidate-selection"
import { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"
import { useCandidatesSearchState } from "@/hooks/candidates/use-candidates-search-state"
import { useCandidatesViewState } from "@/hooks/candidates/use-candidates-view-state"
import type { Candidate } from "@/components/pages/candidates/types"

import { useCandidatesUIState } from "./useCandidatesUIState"
import { useCandidatesNavigation } from "./useCandidatesNavigation"
import { useCandidatesPageEffects } from "./useCandidatesPageEffects"
import { useCandidatesSearchComposition } from "./useCandidatesSearchComposition"
import { useCandidatesViewComposition } from "./useCandidatesViewComposition"
import {
  type CandidatesPageCoreProps,
  CANDIDATES_TABS,
  SEARCH_TEMPLATES,
  useCandidatesData,
  type AdvancedFilters,
  DEFAULT_ADVANCED_FILTERS,
} from "./candidates-core"

export type { CandidatesPageCoreProps }

const tabs = CANDIDATES_TABS

const CandidatePreview = dynamic(
  () => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })),
  { ssr: false }
)
const CandidatePage = dynamic(
  () => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })),
  { ssr: false }
)
const SmartSearchInput = dynamic(
  () =>
    import("@/components/search/smart-search-input")
      .then(m => ({ default: m.SmartSearchInput }))
      .catch(() => ({ default: (() => null) as unknown as React.ComponentType<SmartSearchInputProps> })),
  {
    ssr: false,
    loading: () => (
      <div className="h-12 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none" />
    ),
  }
)
const AdvancedFiltersModal = dynamic(
  () => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })),
  { ssr: false }
)

export function useCandidatesPageCore({
  onAddRecentItem,
  pendingCandidateOpen,
  onCandidateOpened,
}: CandidatesPageCoreProps = {}) {
  const router = useRouter()
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const { user } = useJWTAuth()
  const hideViewedCandidates = useHideViewedCandidates({
    userId: user?.id,
    companyId: (user as Record<string, unknown> | null)?.company_id as string | undefined,
    userEmail: user?.email,
  })

  const {
    tableFilters, setTableFilters,
    showTableFiltersPanel, setShowTableFiltersPanel,
    newSoftSkillFilter, setNewSoftSkillFilter,
    newCertificationFilter, setNewCertificationFilter,
    columnFilters, setColumnFilters,
    openFilterDropdown, setOpenFilterDropdown,
  } = useCandidateFilters()

  const {
    selectedCandidates: selectedCandidatesForBatch,
    setSelectedCandidates: setSelectedCandidatesForBatch,
  } = useCandidateSelection()

  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled

  const candidates = useCandidatesStore((s) => s.candidates) as unknown as Candidate[]
  const storeCandidatesSetter = useCandidatesStore((s) => s.setCandidates)
  const setCandidates = useCallback((v: Candidate[] | ((prev: Candidate[]) => Candidate[])) => {
    storeCandidatesSetter(v as unknown as Record<string, unknown>[] | ((prev: Record<string, unknown>[]) => Record<string, unknown>[]))
  }, [storeCandidatesSetter])
  const isLoading = useCandidatesStore((s) => s.isLoading)
  const setIsLoading = useCandidatesStore((s) => s.setIsLoading)
  const isSearchActive = useCandidatesStore((s) => s.isSearchActive)
  const setIsSearchActive = useCandidatesStore((s) => s.setIsSearchActive)
  const resetCandidatesStore = useCandidatesStore((s) => s.resetStore)
  useEffect(() => {
    return () => { resetCandidatesStore() }
  }, [resetCandidatesStore])

  // BUG #275: rede de segurança. Se `isSearchActive` ficar true por mais de
  // 45s (caso algum caminho patológico escape do try/catch/finally de
  // `useCandidatesExecuteSearch`), forçamos reset da UI para evitar que a
  // animação "LIA está buscando..." fique girando para sempre.
  useLoadingWatchdog(isSearchActive, () => {
    console.warn('[candidates] watchdog: isSearchActive preso por 45s — forçando reset da UI')
    setIsSearchActive(false)
    setIsLoading(false)
  }, 45_000)

  const {
    state: {
      searchTerm, quickFilters, activeTab,
      lastSearchQuery, lastSearchEntities, lastSearchMode, lastSearchMetadata, lastSearchUsedPearch,
      hasSearchResults, searchResultsCount, localResultsCount, pearchResultsCount,
      creditsUsedInSearch, creditsRemaining, showExpandGlobalOption,
      openCreditModals, showEditQueryModal, editQueryValue,
      showSearchResults, searchSource, currentSearchSource,
      showGlobalExpansionConfirm, hasSearched, isExpandingToGlobal,
      searchExecutionId, searchSortBy, searchFeedbacks,
      displayedResultsCount, isLoadingMore, showOnlyNew,
      isDroppingCV, cvUploadLoading,
    },
    actions: {
      setSearchTerm, setQuickFilters, setActiveTab,
      setLastSearchQuery, setLastSearchEntities, setLastSearchMode,
      setLastSearchMetadata, setLastSearchUsedPearch,
      setHasSearchResults, setSearchResultsCount, setLocalResultsCount, setPearchResultsCount,
      setCreditsUsedInSearch, setCreditsRemaining, setShowExpandGlobalOption,
      setOpenCreditModals, setShowEditQueryModal, setEditQueryValue,
      setShowSearchResults, setSearchSource, setCurrentSearchSource,
      setShowGlobalExpansionConfirm, setHasSearched, setIsExpandingToGlobal,
      setSearchExecutionId, setSearchSortBy, setSearchFeedbacks,
      setDisplayedResultsCount, setIsLoadingMore, setShowOnlyNew,
      setIsDroppingCV, setCvUploadLoading,
    },
  } = useCandidatesSearchState()

  const {
    state: {
      selectedCandidate, showPreview, isPreviewMaximized,
      showCandidatePage, showCandidatePreview, previewCandidate,
      showSidePreview, sidePreviewCandidate,
      liaPromptValue, talentConversationId,
      viewedCandidateIds,
      currentPage, crossTabFilter, showCrossTabBanner, viewingList,
      sortBy, sortOrder,
    },
    actions: {
      setSelectedCandidate, setShowPreview, setIsPreviewMaximized,
      setShowCandidatePage, setShowCandidatePreview, setPreviewCandidate,
      setShowSidePreview, setSidePreviewCandidate,
      setLiaPromptValue, setTalentConversationId,
      setViewedCandidateIds,
      setCurrentPage, setCrossTabFilter, setShowCrossTabBanner, setViewingList,
      setSortBy, setSortOrder,
    },
  } = useCandidatesViewState()

  const [candidatesError, setCandidatesError] = useState<string | null>(null)

  const {
    candidateListsForModal, setCandidateListsForModal,
    bulkJobVacancies, bulkEmailTemplates,
    markCandidateAsViewed, refreshCandidates, refreshCandidatesList,
  } = useCandidatesData({
    onViewedIdsChange: setViewedCandidateIds,
    onCandidatesChange: setCandidates,
    onLoadingChange: setIsLoading,
    onErrorChange: setCandidatesError,
    candidateIds: candidates.map(c => c.id),
    candidatesEnabled: candidates.length > 0,
  })

  const handleBulkActionComplete = refreshCandidates
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>(DEFAULT_ADVANCED_FILTERS)

  const ui = useCandidatesUIState()
  const {
    liaPromptEntities, setLiaPromptEntities,
    showLiaSuggestions, setShowLiaSuggestions,
    showLiaAssistant, setShowLiaAssistant,
    liaIsParsingEntities, setLiaIsParsingEntities,
    liaSuggestions, setLiaSuggestions,
    liaAssistantTips, setLiaAssistantTips,
    activeSearchTab, setActiveSearchTab,
    isLIAThinking, setIsLIAThinking,
    chatMessages, setChatMessages,
    pearchSearchOptions, setPearchSearchOptions,
    activeSearchFilters, setActiveSearchFilters,
    searchResults, setSearchResults,
    selectedTemplate, setSelectedTemplate,
    searchThreadId, setSearchThreadId,
    creditEstimate, setCreditEstimate,
    pendingSearchRequest, setPendingSearchRequest,
    previewWidth, setPreviewWidth,
    expandedRows, setExpandedRows,
    showBatchApproval, setShowBatchApproval,
    showContactModal, setShowContactModal,
    contactModalAction, setContactModalAction,
    contactModalCandidate, setContactModalCandidate,
    showScheduleModal, setShowScheduleModal,
    unifiedModalOpen, setUnifiedModalOpen,
    unifiedModalType, setUnifiedModalType,
    unifiedModalCandidate, setUnifiedModalCandidate,
    showQuickViewModal, setShowQuickViewModal,
    showComparisonModal, setShowComparisonModal,
    selectedCandidateForAction, setSelectedCandidateForAction,
    showAddCandidateModal, setShowAddCandidateModal,
    preSelectedListForModal, setPreSelectedListForModal,
    showWSITextModal, setShowWSITextModal,
    showWSIVoiceModal, setShowWSIVoiceModal,
    wsiCandidateForScreening, setWsiCandidateForScreening,
    showWSIInviteModal, setShowWSIInviteModal,
    wsiInviteCandidate, setWsiInviteCandidate,
    showRubricModal, setShowRubricModal,
    rubricCandidate, setRubricCandidate,
    rubricEvaluationData, setRubricEvaluationData,
    showSendEmailModal, setShowSendEmailModal,
    emailCandidateSelected, setEmailCandidateSelected,
    showCVPreviewModal, setShowCVPreviewModal,
    parsedCVData, setParsedCVData,
    showAddToListModal, setShowAddToListModal,
    addToListCandidateIds, setAddToListCandidateIds,
    addToListCandidateNames, setAddToListCandidateNames,
    showAddListToVacanciesModal, setShowAddListToVacanciesModal,
    selectedListForVacancies, setSelectedListForVacancies,
    showAddToVacancyModal, setShowAddToVacancyModal,
    showShareSearchModal, setShowShareSearchModal,
    shareSearchCandidates, setShareSearchCandidates,
    shareSearchTitle, setShareSearchTitle,
    showCreditConfirmation, setShowCreditConfirmation,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    showContactFilterModal, setShowContactFilterModal,
    pendingContactFilter, setPendingContactFilter,
    isSavingToBase, setIsSavingToBase,
    isAddingToList, setIsAddingToList,
    showUnsavedWarningModal, setShowUnsavedWarningModal,
    showAdvancedSearch, setShowAdvancedSearch,
    pendingTabChange, setPendingTabChange,
  } = ui

  const unsavedPearchCandidates = candidates.filter(c => c.source === 'pearch')
  const hasUnsavedPearchCandidates = unsavedPearchCandidates.length > 0 && showSearchResults
  const searchTemplates = SEARCH_TEMPLATES
  const [itemsPerPage] = useState(50)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  useCandidatesNavigation({
    setPreviewCandidate, setShowCandidatePreview,
    activeTab, lastSearchQuery, searchSource, setSearchSource,
    searchExecutionId, lastSearchEntities: lastSearchEntities as ParsedEntities | null,
    setTableFilters, candidates, pendingCandidateOpen, onCandidateOpened,
    showGlobalSearchOptions, setShowSearchResults, setDisplayedResultsCount,
    setActiveTab, setCrossTabFilter, setShowCrossTabBanner,
    setSearchTerm, setQuickFilters,
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setCurrentPage(1) }, [searchTerm, quickFilters, advancedFilters, columnFilters, tableFilters])

  const talentFunnel = useTalentFunnel()
  const favorites = talentFunnel.getFavoriteIds()
  const pinnedCandidates = talentFunnel.getPinnedIds()
  const favoriteNotes = talentFunnel.getFavoriteNotes()

  useCandidatesPageEffects({
    liaPromptValue,
    setLiaPromptEntities, setLiaSuggestions, setLiaIsParsingEntities,
  })

  const searchComposition = useCandidatesSearchComposition({
    searchSource, pearchSearchOptions, setCandidates,
    setHasSearchResults, setSearchResultsCount, setLocalResultsCount, setPearchResultsCount,
    setLastSearchQuery, setLastSearchMode, setActiveSearchTab, setLiaPromptValue, setChatMessages,
    creditsRemaining, setCreditsRemaining,
    searchThreadId, setSearchThreadId,
    hideViewedCandidatesFilter: hideViewedCandidates.filterCandidates,
    talentFunnel, setSearchResults, setShowSearchResults, setDisplayedResultsCount,
    setCurrentSearchSource, setHasSearched, setLastSearchEntities, setLastSearchMetadata,
    setLastSearchUsedPearch, setSearchExecutionId, setShowExpandGlobalOption,
    setIsLoading, setIsSearchActive, setIsDroppingCV, setCvUploadLoading,
    candidates, searchResults, searchTerm, lastSearchQuery,
    lastSearchEntities: lastSearchEntities as ParsedEntities | null,
    lastSearchMode, lastSearchMetadata, lastSearchUsedPearch,
    currentSearchSource, openCreditModals, setOpenCreditModals,
    setPearchSearchOptions, creditsUsedInSearch, setCreditsUsedInSearch,
    pearchResultsCount, localResultsCount, searchResultsCount,
    showSearchResults, hasSearchResults,
    showGlobalExpansionConfirm, setShowGlobalExpansionConfirm,
    isExpandingToGlobal, setIsExpandingToGlobal,
    displayedResultsCount, isLoadingMore, setIsLoadingMore,
    searchFeedbacks, setSearchFeedbacks,
    hasSearched,
    showExpandGlobalOption, showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    showContactFilterModal, setShowContactFilterModal,
    pendingContactFilter, setPendingContactFilter,
    showCreditConfirmation, setShowCreditConfirmation,
    pendingSearchRequest, setPendingSearchRequest,
    activeSearchFilters, setActiveSearchFilters,
    setSelectedTemplate, setSearchSource, searchExecutionId,
    user: user as Record<string, unknown> | null,
  })

  const { archetypesHook, revealContactHook, executeSearch: _rawExecuteSearch, cvHandlers, searchHandlers } = searchComposition

  const executeSearch = useCallback(async (...args: Parameters<typeof _rawExecuteSearch>) => {
    setTableFilters(getDefaultTableFilters())
    return _rawExecuteSearch(...args)
  }, [_rawExecuteSearch, setTableFilters])
  const {
    state: {
      backendArchetypes, isLoadingArchetypes, archetypesLoadError,
      isSearchingByArchetype, userArchetypes, isCreatingArchetype,
      archetypeCreationStep, newArchetypeData, archetypeJobDescription,
      archetypeLibraryTab, showSaveAsArchetypeModal, lastSuccessfulQuery,
      previewSuggestion, previewingUserArchetype,
      archetypeToDelete, isDeletingArchetype,
    },
    actions: {
      setBackendArchetypes, setIsLoadingArchetypes, setArchetypesLoadError,
      setIsSearchingByArchetype, setUserArchetypes, setIsCreatingArchetype,
      setArchetypeCreationStep, setNewArchetypeData, setArchetypeJobDescription,
      setArchetypeLibraryTab, setShowSaveAsArchetypeModal, setLastSuccessfulQuery,
      setPreviewSuggestion, setPreviewingUserArchetype,
      setArchetypeToDelete, setIsDeletingArchetype,
      buildFiltersFromTags, loadArchetypesFromBackend, executeArchetypeSearch,
    },
  } = archetypesHook
  const { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing } = revealContactHook.state
  const { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact } = revealContactHook.actions
  const handleCVDrop = cvHandlers.handleCVDrop
  const handleCVDragOver = cvHandlers.handleCVDragOver
  const handleCVDragLeave = cvHandlers.handleCVDragLeave
  const handleConfirmPearchSearch = searchHandlers.handleConfirmPearchSearch
  const handleSourceChange = searchHandlers.handleSourceChange
  const confirmSourceChange = searchHandlers.confirmSourceChange
  const handleContactFilterChange = searchHandlers.handleContactFilterChange
  const confirmContactFilterChange = searchHandlers.confirmContactFilterChange
  const handleSearchFeedbackChange = (candidateId: string, candidateName: string, feedback: 'like' | 'dislike' | null) => { searchHandlers.handleSearchFeedbackChange(candidateId, feedback) }
  const handleLoadMore = searchHandlers.handleLoadMore
  const handleExpandToGlobal = searchHandlers.handleExpandToGlobal
  const handleApplyAdvancedFilters = searchHandlers.handleApplyAdvancedFilters
  const buildQueryFromFilters = searchHandlers.buildQueryFromFilters
  const handleTemplateSelection = searchHandlers.handleTemplateSelection

  const handleToggleFavorite = (candidateId: string, note?: string) => { talentFunnel.toggleFavoriteCandidate(candidateId, note) }
  const handleUpdateFavoriteNote = (candidateId: string, note: string) => { talentFunnel.updateFavoriteNote(candidateId, note) }
  const handleTogglePin = (candidateId: string) => { talentFunnel.togglePinnedCandidate(candidateId) }

  const viewComposition = useCandidatesViewComposition({
    candidates, setCandidates, searchResults, searchTerm, hasSearchResults,
    quickFilters, columnFilters: columnFilters as { position: string[]; company: string[]; location: string[]; scoreRange: string[]; bigFive?: Record<string, string> }, advancedFilters, tableFilters, setTableFilters,
    sortBy, setSortBy, sortOrder, setSortOrder, searchSortBy, searchFeedbacks,
    displayedResultsCount, showSearchResults, setShowSearchResults, currentPage, itemsPerPage,
    showOnlyNew, viewedCandidateIds, activeTab, setActiveTab,
    viewingList, setViewingList, candidateListsForModal,
    selectedCandidatesForBatch, setSelectedCandidatesForBatch,
    isSavingToBase, setIsSavingToBase, isAddingToList, setIsAddingToList,
    showAddToListModal, setShowAddToListModal,
    addToListCandidateIds, setAddToListCandidateIds,
    addToListCandidateNames, setAddToListCandidateNames,
    showUnsavedWarningModal, setShowUnsavedWarningModal,
    pendingTabChange, setPendingTabChange,
    hasUnsavedPearchCandidates, unsavedPearchCandidates, lastSearchQuery,
    revealedContacts, expandedRows, setExpandedRows,
    isPreviewMaximized, setIsPreviewMaximized, previewWidth, setPreviewWidth,
    setPreviewCandidate, setShowCandidatePreview, setShowPreview,
    setSelectedCandidate, setShowCandidatePage, setShowSidePreview, setSidePreviewCandidate,
    setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen,
    setShowScheduleModal, setShowContactModal, setSelectedCandidateForAction,
    setShowComparisonModal, setShowQuickViewModal, setShowBatchApproval,
    setParsedCVData, setShowCVPreviewModal, setShowAddCandidateModal,
    onAddRecentItem, markCandidateAsViewed, handleBulkActionComplete,
    chatMessages, setChatMessages, liaPromptValue, setLiaPromptValue,
    activeSearchTab, setActiveSearchTab,
    talentConversationId, setTalentConversationId,
    liaIsParsingEntities, setLiaIsParsingEntities,
    liaSuggestions, setLiaSuggestions,
    showLiaSuggestions, setShowLiaSuggestions,
    showLiaAssistant, setShowLiaAssistant,
    activeSearchFilters, liaPromptEntities, setLiaPromptEntities,
    selectedCandidate,
    showQuickViewModal, showComparisonModal,
    isLIAThinking, setIsLIAThinking,
    setWsiInviteCandidate, setShowWSIInviteModal,
    setWsiCandidateForScreening, setShowWSITextModal, setShowWSIVoiceModal,
    setShowRubricModal, executeSearch, talentFunnel,
    user: user as Record<string, unknown> | null, router,
    openRevealModal, handleSearchFeedbackChange, pearchSearchOptions,
    setSearchTerm, setQuickFilters, setSelectedTemplate, setColumnFilters,
  })

  const {
    columnConfigHook, renderCellValue, filterSort, candidatesActions, interactions, liaHandlers,
    handleLIAChatMessage, handleAICommand, handleAddCandidate,
    handleStartWSITextScreening, handleOpenWSIModal, handleStartWSIVoiceScreening,
    handleSort, getSortIcon, toggleTableFilter,
    clearAllTableFilters, clearAllFilters, saveCurrentSearch, getScoreColor, mapCandidateToInternal,
  } = viewComposition
  const getActiveTableFiltersCount = viewComposition.getActiveTableFiltersCount
  const getActiveAdvancedFiltersCount = viewComposition.getActiveAdvancedFiltersCount
  const getActiveSearchFiltersCount = viewComposition.getActiveSearchFiltersCount

  const { filteredCandidates, sortedCandidates, paginatedCandidates, searchDisplayCandidates, visibleCandidates, getPaginatedCandidates } = filterSort
  const {
    showColumnConfig, tableColumns, savedColumnViews, columnSearchTerm,
    columnWidths, draggedColumnId, dragOverColumnId, columnOrder, visibleTableColumns,
  } = columnConfigHook.state
  const {
    setShowColumnConfig, setTableColumns, setSavedColumnViews, setColumnSearchTerm,
    setColumnWidths, setDraggedColumnId, setDragOverColumnId, setColumnOrder,
    isColumnVisible, handleToggleColumnConfig, handleSaveColumns,
    handleSaveColumnView, handleLoadColumnView, handleDeleteColumnView,
    startResize, handleColumnDragStart, handleColumnDragOver, handleColumnDragLeave,
    handleColumnDrop, handleColumnDragEnd,
  } = columnConfigHook.actions

  const handleSaveToLocalBase = candidatesActions.handleSaveToLocalBase
  const handleAddToList = candidatesActions.handleAddToList
  const handleTabChangeWithWarning = candidatesActions.handleTabChangeWithWarning
  const handleSaveAllAndExit = candidatesActions.handleSaveAllAndExit
  const handleExitWithoutSaving = candidatesActions.handleExitWithoutSaving

  const selectedPearchCount = candidates.filter(
    c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
  ).length

  const {
    openUnifiedModal, handleCandidateClick, handleCloseCandidatePreview,
    handleTogglePreviewMaximize, handleCandidatePageOpen, handleCloseSidePreview,
    handleClosePreview, handleToggleMaximize, handleCloseCandidatePage,
    handleCandidateSelection, selectAllCandidates, handleLIAClick,
    handlePreviewResize, handleNavigateToFullProfile, handleScheduleInterview,
    handleContactCandidate, handleSendMessage, handleScheduleComplete,
    handleSendEmail, handleSendWhatsApp, handleSendTriagem, handleSendAgendamento,
    handleSendFeedback, handleBulkEmail, handleBulkWSIScreening,
    handleBulkScheduleInterview, handleBulkFeedback,
    handleUnifiedModalClose, handleUnifiedModalSend,
    handleBatchApprovalComplete, handleWSIScreeningComplete,
    handleCVParsed, handleCVConfirmed, getCandidateQuickActions,
    getComparisonCandidates, convertCandidatesForBatch,
  } = interactions

  const handleQuickAction = liaHandlers.handleQuickAction
  const handleOrchestratedTalentMessage = liaHandlers.handleOrchestratedTalentMessage
  const handleTalentUIAction = liaHandlers.handleTalentUIAction
  const handleCalibrationLike = liaHandlers.handleCalibrationLike
  const handleCalibrationDislike = liaHandlers.handleCalibrationDislike

  const deselectAllCandidates = () => setSelectedCandidatesForBatch(new Set())

  const clearCrossTabFilter = () => {
    setCrossTabFilter(null)
    setShowCrossTabBanner(false)
    setSearchTerm('')
    setQuickFilters(new Set())
    window.history.replaceState({}, '', window.location.pathname)
  }

  return {
    activeSearchFilters, activeSearchTab, activeTab, addToListCandidateIds, addToListCandidateNames, bulkJobVacancies,
    candidateListsForModal, candidates, chatMessages, clearAllFilters, clearAllTableFilters, clearCrossTabFilter,
    columnSearchTerm, columnWidths, confirmContactFilterChange, confirmSourceChange, contactModalAction, contactModalCandidate,
    convertCandidatesForBatch, creditEstimate, deselectAllCandidates, emailCandidateSelected, executeSearch, favoriteNotes,
    favorites, getActiveAdvancedFiltersCount, getActiveSearchFiltersCount, getActiveTableFiltersCount, getPaginatedCandidates, handleAICommand,
    handleAddCandidate, handleAddToList, handleBatchApprovalComplete, handleBulkEmail, handleBulkWSIScreening, handleCVConfirmed,
    handleCVDragLeave, handleCVDragOver, handleCVDrop, handleCalibrationDislike, handleCalibrationLike, handleCandidateClick,
    handleCandidatePageOpen, handleCloseCandidatePage, handleCloseCandidatePreview, handleConfirmPearchSearch, handleContactCandidate, handleExitWithoutSaving,
    handleExpandToGlobal, handleLIAChatMessage, handleLIAClick, handleLoadMore, handleNavigateToFullProfile, handlePreviewResize,
    handleQuickAction, handleRevealContact, handleSaveAllAndExit, handleSaveToLocalBase, handleScheduleComplete, handleScheduleInterview,
    handleSendAgendamento, handleSendEmail, handleSendFeedback, handleSendMessage, handleSendTriagem, handleSendWhatsApp,
    handleStartWSITextScreening, handleTabChangeWithWarning, handleToggleColumnConfig, handleToggleFavorite, handleTogglePin, handleTogglePreviewMaximize,
    handleUnifiedModalClose, handleUnifiedModalSend, handleUpdateFavoriteNote, handleWSIScreeningComplete, hideViewedCandidates, isAddingToList,
    isLIAThinking, isLoading, isSavingToBase, isSearchActive,
    newCertificationFilter, newSoftSkillFilter, parsedCVData, pearchSearchOptions, pendingContactFilter,
    pendingSourceChange, pinnedCandidates, preSelectedListForModal, previewWidth, renderCellValue, revealCandidate,
    revealType, rubricCandidate, rubricEvaluationData, saveCurrentSearch, searchResults,
    selectAllCandidates, selectedCandidateForAction, selectedCandidatesForBatch, selectedListForVacancies, selectedPearchCount, setActiveSearchFilters,
    setActiveSearchTab, setActiveTab, setAddToListCandidateIds, setAddToListCandidateNames, setCandidateListsForModal, setCandidates,
    setChatMessages, setColumnSearchTerm, setColumnWidths, setContactModalAction, setContactModalCandidate, setEmailCandidateSelected,
    setIsLoading, setNewCertificationFilter, setNewSoftSkillFilter,
    setParsedCVData, setPearchSearchOptions, setPendingContactFilter, setPendingSearchRequest, setPendingSourceChange, setPendingTabChange,
    setPreSelectedListForModal, setRevealCandidate, setRubricCandidate, setRubricEvaluationData, setSearchResults, setSelectedCandidateForAction,
    setSelectedCandidatesForBatch, setSelectedListForVacancies, setShareSearchCandidates, setShareSearchTitle, setShowAddCandidateModal, setShowAddListToVacanciesModal,
    setShowAddToListModal, setShowAddToVacancyModal, setShowAdvancedSearch, setShowBatchApproval, setShowCVPreviewModal, setShowColumnConfig,
    setShowComparisonModal, setShowContactFilterModal, setShowContactModal, setShowCreditConfirmation, setShowRevealModal, setShowRubricModal,
    setShowScheduleModal, setShowSendEmailModal, setShowShareSearchModal, setShowSourceChangeModal, setShowTableFiltersPanel, setShowUnsavedWarningModal,
    setShowWSIInviteModal, setShowWSITextModal, setShowWSIVoiceModal, setTableColumns, setTableFilters, setWsiCandidateForScreening,
    setWsiInviteCandidate, shareSearchCandidates, shareSearchTitle, showAddCandidateModal, showAddListToVacanciesModal, showAddToListModal,
    showAddToVacancyModal, showAdvancedSearch, showBatchApproval, showCVPreviewModal, showColumnConfig, showComparisonModal,
    showContactFilterModal, showContactModal, showCreditConfirmation, showRevealModal, showRubricModal, showScheduleModal,
    showSendEmailModal, showShareSearchModal, showSourceChangeModal, showTableFiltersPanel, showUnsavedWarningModal, showWSIInviteModal,
    showWSITextModal, showWSIVoiceModal, sortedCandidates, tableColumns, tableContainerRef, tableFilters,
    talentFunnel, toggleTableFilter, unifiedModalCandidate, unifiedModalOpen, unifiedModalType,
    unsavedPearchCandidates, user, visibleCandidates, visibleTableColumns, wsiCandidateForScreening, wsiInviteCandidate,
    tabs,
    archetypeCreationStep, archetypeToDelete, buildFiltersFromTags, crossTabFilter, currentPage, currentSearchSource,
    cvUploadLoading, displayedResultsCount, editQueryValue, isCreatingArchetype, isDroppingCV, isExpandingToGlobal,
    isLoadingMore, isPreviewMaximized, itemsPerPage, lastSearchEntities, lastSearchQuery, lastSuccessfulQuery,
    liaPromptValue, localResultsCount, newArchetypeData, previewCandidate, previewingUserArchetype, previewSuggestion,
    quickFilters, searchSortBy, searchSource, searchTerm, selectedCandidate,
    setArchetypeCreationStep, setArchetypeToDelete, setCurrentPage, setDisplayedResultsCount, setEditQueryValue,
    setHasSearchResults, setIsCreatingArchetype, setLastSearchEntities, setLastSearchMetadata, setLastSearchMode, setLastSearchQuery,
    setLiaPromptValue, setLocalResultsCount, setNewArchetypeData, setPearchResultsCount, setPreviewCandidate, setPreviewingUserArchetype,
    setPreviewSuggestion, setSearchResultsCount, setSearchSortBy, setSearchSource, setSearchTerm, setShowEditQueryModal,
    setShowGlobalExpansionConfirm, setShowSaveAsArchetypeModal, setShowSearchResults, setSortBy, setSortOrder,
    setUserArchetypes, setViewingList, showCrossTabBanner, showEditQueryModal,
    showGlobalExpansionConfirm, showSaveAsArchetypeModal, showSearchResults, sortBy, sortOrder, viewingList,
    showCandidatePage, showCandidatePreview,
    candidatesError, refreshCandidatesList,
  }
}
