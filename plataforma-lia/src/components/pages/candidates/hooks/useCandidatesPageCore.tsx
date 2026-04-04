"use client"

// useCandidatesPageCore.tsx
// Orchestrator hook: composes all candidates-page sub-hooks and returns
// a single flat object consumed by CandidatesPage.
// Business logic lives in domain hooks — this file is pure composition.

import React, { useState, useEffect, useRef } from "react"
import { toast } from "sonner"
import { useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { classifyPercentageScore } from "@/lib/score-utils"

// ── Services & API ────────────────────────────────────────────────────────────
import { mapCandidateToInternal as _mapCandidateToInternal } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"

// ── UI components used for JSX returned from the hook ────────────────────────
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"
import { type ParsedEntities } from "@/components/search/smart-search-input"

// ── Global hooks ──────────────────────────────────────────────────────────────
import { useJWTAuth } from "@/contexts/auth-context"
import { useCandidatesStore } from "@/stores/candidates-store"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { useHideViewedCandidates } from "@/hooks/useHideViewedCandidates"
import { useCandidateFilters, type TableFilters, getDefaultTableFilters } from "@/hooks/use-candidate-filters"
import { useCandidateSelection } from "@/hooks/use-candidate-selection"
import { useTalentFunnel } from "@/hooks/use-talent-funnel"
import { useCandidatesSearchState } from "@/hooks/use-candidates-search-state"
import { useCandidatesViewState } from "@/hooks/use-candidates-view-state"

// ── Feature-level hooks ───────────────────────────────────────────────────────
import { createCellRenderer } from "@/components/pages/candidates/CandidateTableCellRenderer"
import { useCandidatesArchetypes } from "@/components/pages/candidates/hooks/useCandidatesArchetypes"
import { useCandidatesFilterSort } from "@/components/pages/candidates/hooks/useCandidatesFilterSort"
import { useRevealContact } from "@/components/pages/candidates/hooks/useRevealContact"
import { useCandidatesColumnConfig } from "@/components/pages/candidates/hooks/useCandidatesColumnConfig"
import { useCandidatesExecuteSearch } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
import { useCandidatesCVHandlers } from "@/components/pages/candidates/hooks/useCandidatesCVHandlers"
import { useCandidatesSearch } from "@/components/pages/candidates/hooks/useCandidatesSearch"
import { useCandidatesLIAHandlers } from "@/components/pages/candidates/hooks/useCandidatesLIAHandlers"
import { useCandidatesActions } from "@/components/pages/candidates/hooks/useCandidatesActions"
import type { Candidate } from "@/components/pages/candidates/types"

// ── Domain sub-hooks (extracted from this file) ───────────────────────────────
import { useCandidatesUIState, type SearchTab } from "./useCandidatesUIState"
import { useCandidatesNavigation } from "./useCandidatesNavigation"
import { useCandidatesInteractions } from "./useCandidatesInteractions"

// ── candidates-core (types, constants, data helpers) ─────────────────────────
import {
  type CandidatesPageCoreProps,
  CANDIDATES_TABS,
  SEARCH_TEMPLATES,
  LIA_ASSISTANT_TIPS_DEFAULT,
  useCandidatesData,
  getActiveTableFiltersCount,
  getActiveAdvancedFiltersCount,
  getActiveSearchFiltersCount,
  toggleTableFilterValue,
  type AdvancedFilters,
  DEFAULT_ADVANCED_FILTERS,
} from "./candidates-core"

export type { CandidatesPageCoreProps }

// Alias for backward compat — consumers receive `tabs` from the hook's return value
const tabs = CANDIDATES_TABS

// Dynamic imports (kept here as they are component-level lazy-loads, not business logic)
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
      .catch(() => ({ default: (() => null) as React.ComponentType<Record<string, unknown>> })),
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

  // ── Filter state ──────────────────────────────────────────────────────────
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

  const candidates = useCandidatesStore((s) => s.candidates) as Candidate[]
  const setCandidates = useCandidatesStore((s) => s.setCandidates) as unknown as React.Dispatch<React.SetStateAction<Candidate[]>>
  const isLoading = useCandidatesStore((s) => s.isLoading)
  const setIsLoading = useCandidatesStore((s) => s.setIsLoading)
  const isSearchActive = useCandidatesStore((s) => s.isSearchActive)
  const setIsSearchActive = useCandidatesStore((s) => s.setIsSearchActive)

  // ── Search state ──────────────────────────────────────────────────────────
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

  // ── View state ────────────────────────────────────────────────────────────
  const {
    state: {
      selectedCandidate, showPreview, isPreviewMaximized,
      showCandidatePage, showCandidatePreview, previewCandidate,
      showSidePreview, sidePreviewCandidate,
      selectedCandidateForLIA, showLIAPromptForCandidate,
      showExpandedLIA, liaPromptValue, userCollapsedLIA, talentConversationId,
      viewedCandidateIds,
      currentPage, crossTabFilter, showCrossTabBanner, viewingList,
      sortBy, sortOrder,
    },
    actions: {
      setSelectedCandidate, setShowPreview, setIsPreviewMaximized,
      setShowCandidatePage, setShowCandidatePreview, setPreviewCandidate,
      setShowSidePreview, setSidePreviewCandidate,
      setSelectedCandidateForLIA, setShowLIAPromptForCandidate,
      setShowExpandedLIA, setLiaPromptValue, setUserCollapsedLIA, setTalentConversationId,
      setViewedCandidateIds,
      setCurrentPage, setCrossTabFilter, setShowCrossTabBanner, setViewingList,
      setSortBy, setSortOrder,
    },
  } = useCandidatesViewState()

  // ── Data fetching ─────────────────────────────────────────────────────────
  const {
    candidateListsForModal, setCandidateListsForModal,
    bulkJobVacancies, bulkEmailTemplates,
    markCandidateAsViewed, refreshCandidates,
  } = useCandidatesData({
    onViewedIdsChange: setViewedCandidateIds,
    onCandidatesChange: setCandidates,
    onLoadingChange: setIsLoading,
    candidateIds: candidates.map(c => c.id),
    candidatesEnabled: candidates.length > 0,
  })

  const handleBulkActionComplete = refreshCandidates

  // ── Advanced filters ──────────────────────────────────────────────────────
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>(DEFAULT_ADVANCED_FILTERS)

  // ── UI state (modals, LIA flags, preview width, etc.) ─────────────────────
  const ui = useCandidatesUIState()
  const {
    liaPromptEntities, setLiaPromptEntities,
    showLiaSuggestions, setShowLiaSuggestions,
    showLiaAssistant, setShowLiaAssistant,
    liaIsParsingEntities, setLiaIsParsingEntities,
    liaSuggestions, setLiaSuggestions,
    liaAssistantTips, setLiaAssistantTips,
    activeSearchTab, setActiveSearchTab,
    liaWidth, setLiaWidth,
    isResizingLIA, setIsResizingLIA,
    isLiaSuperChat, setIsLiaSuperChat,
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

  // ── Derived ───────────────────────────────────────────────────────────────
  const unsavedPearchCandidates = candidates.filter(c => c.source === 'pearch')
  const hasUnsavedPearchCandidates = unsavedPearchCandidates.length > 0 && showSearchResults
  const searchTemplates = SEARCH_TEMPLATES
  const [itemsPerPage] = useState(50)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  // ── Navigation / URL effects ──────────────────────────────────────────────
  useCandidatesNavigation({
    setPreviewCandidate,
    setShowCandidatePreview,
    activeTab,
    lastSearchQuery,
    searchSource,
    setSearchSource,
    searchExecutionId,
    lastSearchEntities: lastSearchEntities as ParsedEntities | null,
    setTableFilters,
    candidates,
    pendingCandidateOpen,
    onCandidateOpened,
    showGlobalSearchOptions,
    setShowSearchResults,
    setDisplayedResultsCount,
    setActiveTab,
    setCrossTabFilter,
    setShowCrossTabBanner,
    setSearchTerm,
    setQuickFilters,
  })

  // ── Reset page when filters change ───────────────────────────────────────
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setCurrentPage(1) }, [searchTerm, quickFilters, advancedFilters, columnFilters, tableFilters])

  // ── Talent funnel ─────────────────────────────────────────────────────────
  const talentFunnel = useTalentFunnel()
  const favorites = talentFunnel.getFavoriteIds()
  const pinnedCandidates = talentFunnel.getPinnedIds()
  const favoriteNotes = talentFunnel.getFavoriteNotes()

  // ── Auto-expand LIA sidebar when candidates selected ──────────────────────
  const prevSelectedCountRef = useRef(0)
  useEffect(() => {
    const currentCount = selectedCandidatesForBatch.size
    const prevCount = prevSelectedCountRef.current
    if (currentCount > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
      if (currentCount !== prevCount) {
        const names = candidates
          .filter(c => selectedCandidatesForBatch.has(c.id))
          .slice(0, 3)
          .map(c => c.name)
        const preview = names.join(', ') + (currentCount > 3 ? ` e mais ${currentCount - 3}` : '')
        const plural = currentCount > 1
        setChatMessages(prev => [
          ...prev,
          {
            id: `lia-selection-${Date.now()}`,
            type: 'lia' as const,
            content: `Você selecionou **${currentCount} candidato${plural ? 's' : ''}**: ${preview}.\n\nPosso analisar ${plural ? 'estes candidatos' : 'este candidato'} para você:\n\n• **Analisar potencial de crescimento**\n• **Definir tipo de perfil** (executor, estratégico, etc)\n• **Resumo executivo do perfil**`,
            timestamp: new Date(),
          },
        ])
      }
    }
    prevSelectedCountRef.current = currentCount
  }, [selectedCandidatesForBatch.size, userCollapsedLIA, candidates, selectedCandidatesForBatch])

  // ── LIA entity parsing with debounce ─────────────────────────────────────
  useEffect(() => {
    const emptyEntities = {
      job_title: undefined, location: undefined, skills: [],
      years_experience: undefined, industry: undefined, seniority: undefined, company: undefined,
    }
    if (!liaPromptValue.trim()) { setLiaPromptEntities(emptyEntities); setLiaSuggestions([]); return }
    const timer = setTimeout(async () => {
      setLiaIsParsingEntities(true)
      try {
        const res = await fetch('/api/backend-proxy/search/parse-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: liaPromptValue }),
        })
        if (res.ok) {
          const data = await res.json()
          const e = data.entities || data
          setLiaPromptEntities({
            job_title: e.job_title || undefined, location: e.location || undefined,
            skills: e.skills || [], years_experience: e.years_experience || undefined,
            industry: e.industry || undefined, seniority: e.seniority || undefined,
            company: e.company || undefined,
          })
          setLiaSuggestions(Array.isArray(data.suggestions) ? data.suggestions : [])
        }
      } catch {} finally { setLiaIsParsingEntities(false) }
    }, 500)
    return () => clearTimeout(timer)
  }, [liaPromptValue])

  // ── Open LIA panel on mount ───────────────────────────────────────────────
  useEffect(() => { setShowExpandedLIA(true) }, [])

  // ── Archetypes ────────────────────────────────────────────────────────────
  const archetypesHook = useCandidatesArchetypes({
    searchSource, pearchSearchOptions,
    setCandidates, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount,
    setLastSearchQuery, setLastSearchMode,
    setActiveSearchTab: (_v: string) => setActiveSearchTab(_v as SearchTab),
    setLiaPromptValue, setChatMessages,
  })
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

  // ── Reveal contact ────────────────────────────────────────────────────────
  const revealContactHook = useRevealContact({
    setCreditsRemaining: (fn) =>
      setCreditsRemaining(typeof fn === 'function' ? fn(creditsRemaining) : fn),
  })
  const { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing } = revealContactHook.state
  const { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact } = revealContactHook.actions

  // ── Execute search ────────────────────────────────────────────────────────
  const { executeSearch } = useCandidatesExecuteSearch({
    searchSource, pearchSearchOptions, searchThreadId, setSearchThreadId,
    hideViewedCandidatesFilter: hideViewedCandidates.filterCandidates,
    talentFunnel,
    setCandidates, setSearchResults, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount, setCreditsUsedInSearch,
    setCreditsRemaining: (fn) =>
      setCreditsRemaining(typeof fn === 'function' ? fn(creditsRemaining ?? 0) : fn),
    setShowSearchResults, setDisplayedResultsCount, setCurrentSearchSource,
    setHasSearched, setLastSearchEntities, setLastSearchMetadata, setLastSearchUsedPearch,
    setSearchExecutionId, setShowExpandGlobalOption, setShowExpandedLIA, setUserCollapsedLIA,
    setLastSuccessfulQuery, setChatMessages, setIsLoading, setIsSearchActive,
  })

  // ── CV handlers ───────────────────────────────────────────────────────────
  const cvHandlers = useCandidatesCVHandlers({
    setCandidates, setIsDroppingCV, setCvUploadLoading,
    setHasSearchResults, setSearchResultsCount, setShowSearchResults,
    setDisplayedResultsCount, setChatMessages,
  })
  const handleCVDrop = cvHandlers.handleCVDrop
  const handleCVDragOver = cvHandlers.handleCVDragOver
  const handleCVDragLeave = cvHandlers.handleCVDragLeave

  // ── Search handlers ───────────────────────────────────────────────────────
  const searchHandlers = useCandidatesSearch({
    candidates, setCandidates,
    searchResults, setSearchResults,
    searchTerm,
    lastSearchQuery, lastSearchEntities, lastSearchMode, lastSearchMetadata, lastSearchUsedPearch,
    searchSource, setSearchSource, currentSearchSource, setCurrentSearchSource,
    openCreditModals, setOpenCreditModals,
    pearchSearchOptions, setPearchSearchOptions,
    creditsRemaining, setCreditsRemaining,
    creditsUsedInSearch, setCreditsUsedInSearch,
    pearchResultsCount, setPearchResultsCount,
    localResultsCount, setLocalResultsCount,
    searchResultsCount, setSearchResultsCount,
    showSearchResults, setShowSearchResults,
    hasSearchResults, setHasSearchResults,
    showGlobalExpansionConfirm, setShowGlobalExpansionConfirm,
    isExpandingToGlobal, setIsExpandingToGlobal,
    displayedResultsCount, setDisplayedResultsCount,
    isLoadingMore, setIsLoadingMore,
    searchFeedbacks, setSearchFeedbacks,
    hasSearched, lastSuccessfulQuery,
    setSearchThreadId, searchThreadId,
    showExpandGlobalOption, setShowExpandGlobalOption,
    setChatMessages,
    showSourceChangeModal, setShowSourceChangeModal,
    pendingSourceChange, setPendingSourceChange,
    showContactFilterModal, setShowContactFilterModal,
    pendingContactFilter, setPendingContactFilter,
    showCreditConfirmation, setShowCreditConfirmation,
    pendingSearchRequest, setPendingSearchRequest,
    activeSearchFilters, setActiveSearchFilters,
    setSelectedTemplate,
    executeSearch,
user,
  })
  const handleConfirmPearchSearch = searchHandlers.handleConfirmPearchSearch
  const handleSourceChange = searchHandlers.handleSourceChange
  const confirmSourceChange = searchHandlers.confirmSourceChange
  const handleContactFilterChange = searchHandlers.handleContactFilterChange
  const confirmContactFilterChange = searchHandlers.confirmContactFilterChange
  const handleSearchFeedbackChange = searchHandlers.handleSearchFeedbackChange
  const handleLoadMore = searchHandlers.handleLoadMore
  const handleExpandToGlobal = searchHandlers.handleExpandToGlobal
  const handleApplyAdvancedFilters = searchHandlers.handleApplyAdvancedFilters
  const buildQueryFromFilters = searchHandlers.buildQueryFromFilters
  const handleTemplateSelection = searchHandlers.handleTemplateSelection

  // ── Column config ─────────────────────────────────────────────────────────
  const columnConfigHook = useCandidatesColumnConfig()
  const {
    showColumnConfig, tableColumns, savedColumnViews, columnSearchTerm,
    columnWidths, draggedColumnId, dragOverColumnId, columnOrder,
    visibleTableColumns,
  } = columnConfigHook.state
  const {
    setShowColumnConfig, setTableColumns, setSavedColumnViews, setColumnSearchTerm,
    setColumnWidths, setDraggedColumnId, setDragOverColumnId, setColumnOrder,
    isColumnVisible, handleToggleColumnConfig, handleSaveColumns,
    handleSaveColumnView, handleLoadColumnView, handleDeleteColumnView,
    startResize,
    handleColumnDragStart, handleColumnDragOver, handleColumnDragLeave,
    handleColumnDrop, handleColumnDragEnd,
  } = columnConfigHook.actions

  // ── Cell renderer ─────────────────────────────────────────────────────────
  const renderCellValue = createCellRenderer({
    searchFeedbacks,
    revealedContacts,
    searchQuery: searchResults.query,
    viewedCandidateIds,
    expandedRows,
    onSearchFeedbackChange: handleSearchFeedbackChange,
    onRevealContact: openRevealModal,
    onToggleExpandedRow: (candidateId) =>
      setExpandedRows(prev => {
        const newSet = new Set(prev)
        if (newSet.has(candidateId)) newSet.delete(candidateId)
        else newSet.add(candidateId)
        return newSet
      }),
  })

  // ── Filter/sort ───────────────────────────────────────────────────────────
  const {
    filteredCandidates, sortedCandidates, paginatedCandidates,
    searchDisplayCandidates, visibleCandidates, getPaginatedCandidates,
  } = useCandidatesFilterSort({
    candidates, searchTerm, hasSearchResults, quickFilters, columnFilters,
    advancedFilters, tableFilters, sortBy, sortOrder, searchSortBy, searchFeedbacks,
    displayedResultsCount, showSearchResults, currentPage, itemsPerPage,
    showOnlyNew, viewedCandidateIds,
  })

  // ── Candidate actions ─────────────────────────────────────────────────────
  const candidatesActions = useCandidatesActions({
    candidates, setCandidates,
    activeTab, setActiveTab,
    viewingList, setViewingList,
    candidateListsForModal,
    selectedCandidatesForBatch, setSelectedCandidatesForBatch,
    isSavingToBase, setIsSavingToBase,
    isAddingToList, setIsAddingToList,
    showAddToListModal, setShowAddToListModal,
    addToListCandidateIds, setAddToListCandidateIds,
    addToListCandidateNames, setAddToListCandidateNames,
    showUnsavedWarningModal, setShowUnsavedWarningModal,
    pendingTabChange, setPendingTabChange,
    hasUnsavedPearchCandidates, unsavedPearchCandidates,
    showSearchResults, setShowSearchResults,
    lastSearchQuery, deselectAllCandidates: () => setSelectedCandidatesForBatch(new Set()),
user,
  })
  const handleSaveToLocalBase = candidatesActions.handleSaveToLocalBase
  const handleAddToList = candidatesActions.handleAddToList
  const handleTabChangeWithWarning = candidatesActions.handleTabChangeWithWarning
  const handleSaveAllAndExit = candidatesActions.handleSaveAllAndExit
  const handleExitWithoutSaving = candidatesActions.handleExitWithoutSaving

  const selectedPearchCount = candidates.filter(
    c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
  ).length

  // ── Favorite / pin helpers ────────────────────────────────────────────────
  const handleToggleFavorite = (candidateId: string, note?: string) => { talentFunnel.toggleFavoriteCandidate(candidateId, note) }
  const handleUpdateFavoriteNote = (candidateId: string, note: string) => { talentFunnel.updateFavoriteNote(candidateId, note) }
  const handleTogglePin = (candidateId: string) => { talentFunnel.togglePinnedCandidate(candidateId) }

  // ── LIA chat stubs ────────────────────────────────────────────────────────
  const liaHandlersRef = React.useRef<ReturnType<typeof useCandidatesLIAHandlers> | null>(null)
  const handleLIAChatMessage = async (message: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleLIAChatMessage(message)
  }
  const handleAICommand = async (command: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleAICommand(command)
  }

  // ── Candidate interactions (click, preview, communications) ───────────────
  const interactions = useCandidatesInteractions({
    candidates,
    setCandidates,
    sortedCandidates,
    selectedCandidatesForBatch,
    setSelectedCandidatesForBatch,
    setPreviewCandidate,
    setShowCandidatePreview,
    setIsPreviewMaximized,
    isPreviewMaximized,
    setShowPreview,
    setSelectedCandidate,
    setShowCandidatePage,
    setShowSidePreview,
    setSidePreviewCandidate,
    setSelectedCandidateForLIA,
    setShowLIAPromptForCandidate,
    previewWidth,
    setPreviewWidth,
    setUnifiedModalCandidate,
    setUnifiedModalType,
    setUnifiedModalOpen,
    setShowScheduleModal,
    setShowContactModal,
    setSelectedCandidateForAction,
    setShowComparisonModal,
    setShowQuickViewModal,
    setShowBatchApproval,
    setParsedCVData,
    setShowCVPreviewModal,
    onAddRecentItem,
    markCandidateAsViewed,
    handleBulkActionComplete,
    handleAICommand,
    deselectAllCandidates: () => setSelectedCandidatesForBatch(new Set()),
  })

  const {
    openUnifiedModal,
    handleCandidateClick,
    handleCloseCandidatePreview,
    handleTogglePreviewMaximize,
    handleCandidatePageOpen,
    handleCloseSidePreview,
    handleClosePreview,
    handleToggleMaximize,
    handleCloseCandidatePage,
    handleCandidateSelection,
    selectAllCandidates,
    handleLIAClick,
    handlePreviewResize,
    handleNavigateToFullProfile,
    handleScheduleInterview,
    handleContactCandidate,
    handleSendMessage,
    handleScheduleComplete,
    handleSendEmail,
    handleSendWhatsApp,
    handleSendTriagem,
    handleSendAgendamento,
    handleSendFeedback,
    handleBulkEmail,
    handleBulkWSIScreening,
    handleBulkScheduleInterview,
    handleBulkFeedback,
    handleUnifiedModalClose,
    handleUnifiedModalSend,
    handleBatchApprovalComplete,
    handleWSIScreeningComplete,
    handleCVParsed,
    handleCVConfirmed,
    getCandidateQuickActions,
    getComparisonCandidates,
    convertCandidatesForBatch,
  } = interactions

  const handleAddCandidate = (newCandidate: Record<string, unknown>) => {
    interactions.handleAddCandidate(newCandidate, setShowAddCandidateModal)
  }

  const deselectAllCandidates = () => setSelectedCandidatesForBatch(new Set())

  // ── WSI helpers (modal open) ──────────────────────────────────────────────
  const handleStartWSITextScreening = (candidate: Candidate) => { setWsiInviteCandidate(candidate); setShowWSIInviteModal(true) }
  const handleOpenWSIModal = (candidate: Candidate) => { setWsiCandidateForScreening(candidate); setShowWSITextModal(true) }
  const handleStartWSIVoiceScreening = (candidate: Candidate) => { setWsiCandidateForScreening(candidate); setShowWSIVoiceModal(true) }

  // ── LIA handlers (wired last — needs openUnifiedModal, executeSearch, etc) ─
  const liaHandlers = useCandidatesLIAHandlers({
    candidates, setCandidates,
    chatMessages, setChatMessages,
    liaPromptValue, setLiaPromptValue,
    liaWidth, setLiaWidth,
    activeSearchTab, setActiveSearchTab,
    talentConversationId, setTalentConversationId,
    liaIsParsingEntities, setLiaIsParsingEntities,
    liaSuggestions, setLiaSuggestions,
    showLiaSuggestions, setShowLiaSuggestions,
    showLiaAssistant, setShowLiaAssistant,
    selectedCandidatesForBatch, setSelectedCandidatesForBatch,
    searchResults, lastSearchQuery,
    activeSearchFilters,
    liaPromptEntities, setLiaPromptEntities,
    setShowExpandedLIA, userCollapsedLIA, setUserCollapsedLIA,
    selectedCandidateForLIA, setSelectedCandidateForLIA,
    showLIAPromptForCandidate, setShowLIAPromptForCandidate,
    selectedCandidate, setSelectedCandidate,
    showQuickViewModal, setShowQuickViewModal,
    showComparisonModal, setShowComparisonModal,
    setShowScheduleModal,
    setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen,
    setShowAddToListModal,
    isLIAThinking, setIsLIAThinking,
    handleStartWSITextScreening, handleOpenWSIModal,
    openUnifiedModal, handleCandidateClick,
    executeSearch, talentFunnel,
user, router,
  })
  liaHandlersRef.current = liaHandlers
  const handleQuickAction = liaHandlers.handleQuickAction
  const handleOrchestratedTalentMessage = liaHandlers.handleOrchestratedTalentMessage
  const handleTalentUIAction = liaHandlers.handleTalentUIAction
  const handleCalibrationLike = liaHandlers.handleCalibrationLike
  const handleCalibrationDislike = liaHandlers.handleCalibrationDislike

  // ── Sort helpers ──────────────────────────────────────────────────────────
  const handleSort = (field: string) => {
    if (sortBy === field) setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    else { setSortBy(field); setSortOrder('desc') }
  }
  const getSortIcon = (field: string) => {
    if (sortBy !== field) return <ArrowUpDown className="w-3 h-3 ml-1" />
    return sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
  }

  // ── Filter count / clear helpers ──────────────────────────────────────────
  const _getActiveTableFiltersCount = () => getActiveTableFiltersCount(tableFilters)
  const _getActiveAdvancedFiltersCount = () => getActiveAdvancedFiltersCount(advancedFilters)
  const _getActiveSearchFiltersCount = () => getActiveSearchFiltersCount(quickFilters, advancedFilters)
  const toggleTableFilter = (category: keyof TableFilters, value: string) => {
    setTableFilters(prev => toggleTableFilterValue(prev, category, value))
  }
  const clearAllTableFilters = () => setTableFilters(getDefaultTableFilters())
  const clearAllFilters = () => {
    setSearchTerm('')
    setQuickFilters(new Set())
    setSelectedTemplate('')
    setColumnFilters({
      position: [], company: [], location: [], scoreRange: [],
      bigFive: { openness: '', conscientiousness: '', extraversion: '', agreeableness: '', neuroticism: '' },
    })
    clearAllTableFilters()
  }
  const clearCrossTabFilter = () => {
    setCrossTabFilter(null)
    setShowCrossTabBanner(false)
    setSearchTerm('')
    setQuickFilters(new Set())
    window.history.replaceState({}, '', window.location.pathname)
  }
  const saveCurrentSearch = () => {
    sessionStorage.setItem(
      'current-search-data',
      JSON.stringify({ name: `Busca ${new Date().toLocaleDateString()}`, searchTerm, quickFilters: Array.from(quickFilters), timestamp: new Date().toISOString() })
    )
    setActiveTab('saved-searches')
    toast.success('Busca salva', { description: `${sortedCandidates.length} candidatos encontrados` })
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

  const mapCandidateToInternal = _mapCandidateToInternal

  // ── RETURN — same public shape; do not rename anything ───────────────────
  return {
    activeSearchFilters, activeSearchTab, activeTab, addToListCandidateIds, addToListCandidateNames, bulkJobVacancies,
    candidateListsForModal, candidates, chatMessages, clearAllFilters, clearAllTableFilters, clearCrossTabFilter,
    columnSearchTerm, columnWidths, confirmContactFilterChange, confirmSourceChange, contactModalAction, contactModalCandidate,
    convertCandidatesForBatch, creditEstimate, deselectAllCandidates, emailCandidateSelected, executeSearch, favoriteNotes,
    favorites, getActiveAdvancedFiltersCount: _getActiveAdvancedFiltersCount, getActiveSearchFiltersCount: _getActiveSearchFiltersCount, getActiveTableFiltersCount: _getActiveTableFiltersCount, getPaginatedCandidates, handleAICommand,
    handleAddCandidate, handleAddToList, handleBatchApprovalComplete, handleBulkEmail, handleBulkWSIScreening, handleCVConfirmed,
    handleCVDragLeave, handleCVDragOver, handleCVDrop, handleCalibrationDislike, handleCalibrationLike, handleCandidateClick,
    handleCandidatePageOpen, handleCloseCandidatePage, handleCloseCandidatePreview, handleConfirmPearchSearch, handleContactCandidate, handleExitWithoutSaving,
    handleExpandToGlobal, handleLIAChatMessage, handleLIAClick, handleLoadMore, handleNavigateToFullProfile, handlePreviewResize,
    handleQuickAction, handleRevealContact, handleSaveAllAndExit, handleSaveToLocalBase, handleScheduleComplete, handleScheduleInterview,
    handleSendAgendamento, handleSendEmail, handleSendFeedback, handleSendMessage, handleSendTriagem, handleSendWhatsApp,
    handleStartWSITextScreening, handleTabChangeWithWarning, handleToggleColumnConfig, handleToggleFavorite, handleTogglePin, handleTogglePreviewMaximize,
    handleUnifiedModalClose, handleUnifiedModalSend, handleUpdateFavoriteNote, handleWSIScreeningComplete, hideViewedCandidates, isAddingToList,
    isLIAThinking, isLiaSuperChat, isLoading, isResizingLIA, isSavingToBase, isSearchActive,
    liaWidth, newCertificationFilter, newSoftSkillFilter, parsedCVData, pearchSearchOptions, pendingContactFilter,
    pendingSourceChange, pinnedCandidates, preSelectedListForModal, previewWidth, renderCellValue, revealCandidate,
    revealType, rubricCandidate, rubricEvaluationData, saveCurrentSearch, searchResults,
    selectAllCandidates, selectedCandidateForAction, selectedCandidatesForBatch, selectedListForVacancies, selectedPearchCount, setActiveSearchFilters,
    setActiveSearchTab, setActiveTab, setAddToListCandidateIds, setAddToListCandidateNames, setCandidateListsForModal, setCandidates,
    setChatMessages, setColumnSearchTerm, setColumnWidths, setContactModalAction, setContactModalCandidate, setEmailCandidateSelected,
    setIsLiaSuperChat, setIsLoading, setIsResizingLIA, setLiaWidth, setNewCertificationFilter, setNewSoftSkillFilter,
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
    setShowExpandedLIA, setShowGlobalExpansionConfirm, setShowSaveAsArchetypeModal, setShowSearchResults, setSortBy, setSortOrder,
    setUserArchetypes, setUserCollapsedLIA, setViewingList, showCrossTabBanner, showEditQueryModal, showExpandedLIA,
    showGlobalExpansionConfirm, showSaveAsArchetypeModal, showSearchResults, sortBy, sortOrder, viewingList,
    showCandidatePage, showCandidatePreview,
  }
}
