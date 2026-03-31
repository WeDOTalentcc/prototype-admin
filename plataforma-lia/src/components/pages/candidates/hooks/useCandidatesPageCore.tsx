// @ts-nocheck
"use client"

// useCandidatesPageCore.tsx
// Orchestrator hook: composes all candidates-page sub-hooks and returns
// a single flat object consumed by CandidatesPage.
// Target: under 500 lines. Pure composition — no business logic lives here.

import React, { useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import dynamic from "next/dynamic"

// ── Services & API ────────────────────────────────────────────────────────────
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { mapCandidateToInternal as _mapCandidateToInternal } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"

// ── UI components (used only for JSX in helpers returned from hook) ────────────
import {
  ArrowUpDown, ArrowUp, ArrowDown, ChevronsLeftRight, Target,
  Calendar, CheckCircle, Mail, MessageSquare,
} from "lucide-react"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type QuickAction } from "@/components/ui/quick-action-chips"
import { type ParsedEntities, type SearchMode, type SearchMetadata } from "@/components/search/smart-search-input"
import { type SearchFilters } from "@/components/search/advanced-filters-modal"
import { type ParsedCVResponse } from "@/components/cv"
import { JobVacancy, EmailTemplate } from "@/services/lia-api"
import type { TableColumn, TableSortConfig } from "@/components/tables/types"
import type { CalibrationCandidate } from "@/components/calibration-card"
import type { ReviewCandidate, Criterion } from "@/components/pages/candidate-review-modal"
import { type CreditEstimate } from "@/lib/api/candidate-search"

// ── Sub-hooks (business logic) ────────────────────────────────────────────────
import { useJWTAuth } from "@/contexts/auth-context"
import { useToast } from "@/hooks/use-toast"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { useHideViewedCandidates } from "@/hooks/useHideViewedCandidates"
import { useCandidateFilters, type TableFilters, getDefaultTableFilters } from "@/hooks/use-candidate-filters"
import { useCandidateSelection } from "@/hooks/use-candidate-selection"
import { useTalentFunnel } from "@/hooks/use-talent-funnel"
import { useCandidatesSearchState } from "@/hooks/use-candidates-search-state"
import { useCandidatesViewState } from "@/hooks/use-candidates-view-state"

import { createCellRenderer } from "@/components/pages/candidates/CandidateTableCellRenderer"
import { useCandidatesArchetypes, type Archetype, type BackendArchetype, type AISuggestion } from "@/components/pages/candidates/hooks/useCandidatesArchetypes"
import { useCandidatesFilterSort } from "@/components/pages/candidates/hooks/useCandidatesFilterSort"
import { useRevealContact } from "@/components/pages/candidates/hooks/useRevealContact"
import { useCandidatesColumnConfig } from "@/components/pages/candidates/hooks/useCandidatesColumnConfig"
import { useCandidatesExecuteSearch } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"
import { useCandidatesCVHandlers } from "@/components/pages/candidates/hooks/useCandidatesCVHandlers"
import { useCandidatesSearch } from "@/components/pages/candidates/hooks/useCandidatesSearch"
import { useCandidatesLIAHandlers } from "@/components/pages/candidates/hooks/useCandidatesLIAHandlers"
import { useCandidatesActions } from "@/components/pages/candidates/hooks/useCandidatesActions"
import type { Candidate } from "@/components/pages/candidates/types"

// ── Candidates-core split (types, constants, data, filter helpers) ────────────
import {
  type CandidatesPageCoreProps,
  type SearchSource,
  type ChatMessage,
  type PearchSearchOptions,
  CANDIDATES_TABS,
  SEARCH_TEMPLATES,
  LIA_ASSISTANT_TIPS_DEFAULT,
  DEFAULT_PEARCH_OPTIONS,
  PREVIEW_WIDTH_DEFAULT,
  PREVIEW_WIDTH_MIN,
  PREVIEW_WIDTH_MAX,
  LIA_WIDTH_DEFAULT,
  useCandidatesData,
  getActiveTableFiltersCount,
  getActiveAdvancedFiltersCount,
  getActiveSearchFiltersCount,
  toggleTableFilterValue,
  type AdvancedFilters,
  DEFAULT_ADVANCED_FILTERS,
} from "./candidates-core"

export type { CandidatesPageCoreProps }

// SearchTab is intentionally local — other files in the feature define their own
// compatible union; exporting from a shared module would cause type-identity conflicts.
type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'

// Alias for backward compat — consumers receive `tabs` from the hook's return value
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
      .catch(() => ({ default: () => null as unknown })),
  {
    ssr: false,
    loading: () => (
      <div className="h-12 bg-gray-100 dark:bg-lia-bg-secondary rounded-lg animate-pulse motion-reduce:animate-none" />
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
  const searchParams = useSearchParams()
  const router = useRouter()
  const expandedSearchParam = searchParams.get('expandedSearch')
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const { user } = useJWTAuth()
  const { toast } = useToast()
  const { saveTalentFunnelState } = useNavigationPersistence()

  const hideViewedCandidates = useHideViewedCandidates({
    userId: user?.id,
    companyId: user?.company_id,
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

  // ── Core candidate state ──────────────────────────────────────────────────
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSearchActive, setIsSearchActive] = useState(false)

  // ── Search state (extracted to useCandidatesSearchState) ──────────────────
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

  // ── View state (extracted to useCandidatesViewState) ──────────────────────
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

  // ── Data fetching (extracted to useCandidatesData) ────────────────────────
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

  // Alias for backward compat
  const handleBulkActionComplete = refreshCandidates

  // ── Advanced filters state (declared early — referenced in effects below) ─
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedFilters>(DEFAULT_ADVANCED_FILTERS)

  // ── Navigation & URL effects ──────────────────────────────────────────────
  useEffect(() => {
    if (activeTab === 'search' || activeTab === 'favorites' || activeTab === 'lists') {
      saveTalentFunnelState(activeTab, lastSearchQuery)
    }
  }, [activeTab, lastSearchQuery, saveTalentFunnelState])

  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])

  useEffect(() => {
    if (expandedSearchParam === 'true') {
      setShowSearchResults(true)
      setDisplayedResultsCount(10)
      setActiveTab('search')
    }
  }, [expandedSearchParam])

  // ── Navigate to recent candidate (localStorage) ───────────────────────────
  useEffect(() => {
    if (!candidates.length) return
    const raw = localStorage.getItem('navigateToRecentCandidate')
    if (!raw) return
    localStorage.removeItem('navigateToRecentCandidate')
    try {
      const nav = JSON.parse(raw) as { candidateId?: string }
      const found = nav.candidateId && candidates.find(c => c.id === nav.candidateId)
      if (found) { setPreviewCandidate(found); setShowCandidatePreview(true) }
    } catch {}
  }, [candidates])

  // ── Open pending candidate passed via prop ────────────────────────────────
  useEffect(() => {
    if (pendingCandidateOpen && candidates.length > 0) {
      const found = candidates.find(c => c.id === pendingCandidateOpen.candidateId)
      if (found) { setPreviewCandidate(found); setShowCandidatePreview(true) }
      onCandidateOpened?.()
    }
  }, [pendingCandidateOpen, candidates, onCandidateOpened])

  // ── Auto-populate tableFilters from search entities ───────────────────────
  useEffect(() => {
    if (searchExecutionId > 0) {
      const e = lastSearchEntities
      const yearsExp = e?.years_experience
      const parsedYears = typeof yearsExp === 'string' ? parseInt(yearsExp, 10) : yearsExp
      setTableFilters(prev => ({
        ...prev,
        locations: e?.location ? [e.location] : [],
        jobTitles: e?.job_title ? [e.job_title] : [],
        skills: e?.skills?.length ? e.skills : [],
        industries: e?.industry ? [e.industry] : [],
        seniorityLevels: e?.seniority ? [e.seniority] : [],
        minExperience: parsedYears !== undefined && !isNaN(parsedYears) ? parsedYears : undefined,
        companies: e?.company ? [e.company] : [],
      }))
    }
  }, [searchExecutionId])

  // ── Reset page when filters change ───────────────────────────────────────
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { setCurrentPage(1) }, [searchTerm, quickFilters, advancedFilters, columnFilters, tableFilters])

  // ── Cross-tab filter from sessionStorage / URL ────────────────────────────
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tabParam = urlParams.get('tab')
    const filterParam = urlParams.get('filter')
    const companyParam = urlParams.get('name') || urlParams.get('companies')
    const filterData = sessionStorage.getItem('candidates-filter-data')

    if (filterData) {
      try {
        const data = JSON.parse(filterData)
        setCrossTabFilter(data)
        setShowCrossTabBanner(true)
        if (data.type === 'company' && data.company) {
          setSearchTerm(`empresa:"${data.company}"`)
          setQuickFilters(new Set(['company_filter']))
        }
        sessionStorage.removeItem('candidates-filter-data')
      } catch {}
    } else if (tabParam === 'candidates' && filterParam === 'company' && companyParam) {
      const companies = companyParam.split(',')
      setCrossTabFilter({ type: 'company', companies, source: 'url' })
      setShowCrossTabBanner(true)
      setSearchTerm(`empresas:${companies.join(',')}`)
    }
  }, [])

  // ── Talent funnel ─────────────────────────────────────────────────────────
  const talentFunnel = useTalentFunnel()
  const favorites = talentFunnel.getFavoriteIds()
  const pinnedCandidates = talentFunnel.getPinnedIds()
  const favoriteNotes = talentFunnel.getFavoriteNotes()

  // ── Local state ───────────────────────────────────────────────────────────
  const [itemsPerPage] = useState(50)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  const [liaPromptEntities, setLiaPromptEntities] = useState<ParsedEntities>({
    job_title: undefined, location: undefined, skills: [],
    years_experience: undefined, industry: undefined,
    seniority: undefined, company: undefined,
  })
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(true)
  const [showLiaAssistant, setShowLiaAssistant] = useState(false)
  const [liaIsParsingEntities, setLiaIsParsingEntities] = useState(false)
  const [liaSuggestions, setLiaSuggestions] = useState<string[]>([])
  const [liaAssistantTips, setLiaAssistantTips] = useState<string[]>(LIA_ASSISTANT_TIPS_DEFAULT)
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('ia-natural')
  const [liaWidth, setLiaWidth] = useState(LIA_WIDTH_DEFAULT)
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  const [isLiaSuperChat, setIsLiaSuperChat] = useState(false)
  const [pearchSearchOptions, setPearchSearchOptions] = useState<PearchSearchOptions>(DEFAULT_PEARCH_OPTIONS)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({
    ppiOptions: {}, general: {}, locations: {}, job: {}, company: {},
    skills: {}, education: {}, languages: {},
  })
  const [searchResults, setSearchResults] = useState<{
    local: Candidate[]; global: Candidate[]
    localCount: number; globalCount: number; query: string
    isLoading: boolean; showGlobalResults: boolean; globalDismissed: boolean
  }>({
    local: [], global: [], localCount: 0, globalCount: 0, query: '',
    isLoading: false, showGlobalResults: false, globalDismissed: false,
  })
  const [previewWidth, setPreviewWidth] = useState(PREVIEW_WIDTH_DEFAULT)
  const [selectedTemplate, setSelectedTemplate] = useState('')

  // Modal state
  const [showBatchApproval, setShowBatchApproval] = useState(false)
  const [showContactModal, setShowContactModal] = useState(false)
  const [contactModalAction, setContactModalAction] = useState<'general' | 'wsi_screening' | 'interview_invite'>('general')
  const [contactModalCandidate, setContactModalCandidate] = useState<Record<string, unknown> | null>(null)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [unifiedModalOpen, setUnifiedModalOpen] = useState(false)
  const [unifiedModalType, setUnifiedModalType] = useState<CommunicationType>('email')
  const [unifiedModalCandidate, setUnifiedModalCandidate] = useState<Candidate | null>(null)
  const [showQuickViewModal, setShowQuickViewModal] = useState(false)
  const [showComparisonModal, setShowComparisonModal] = useState(false)
  const [selectedCandidateForAction, setSelectedCandidateForAction] = useState<Candidate | null>(null)
  const [showAddCandidateModal, setShowAddCandidateModal] = useState(false)
  const [preSelectedListForModal, setPreSelectedListForModal] = useState<{ id: string; name: string } | null>(null)
  const [showWSITextModal, setShowWSITextModal] = useState(false)
  const [showWSIVoiceModal, setShowWSIVoiceModal] = useState(false)
  const [wsiCandidateForScreening, setWsiCandidateForScreening] = useState<Candidate | null>(null)
  const [showWSIInviteModal, setShowWSIInviteModal] = useState(false)
  const [wsiInviteCandidate, setWsiInviteCandidate] = useState<Candidate | null>(null)
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [rubricCandidate, setRubricCandidate] = useState<Candidate | null>(null)
  const [rubricEvaluationData, setRubricEvaluationData] = useState<Record<string, unknown> | null>(null)
  const [showSendEmailModal, setShowSendEmailModal] = useState(false)
  const [emailCandidateSelected, setEmailCandidateSelected] = useState<Candidate | null>(null)
  const [showCVPreviewModal, setShowCVPreviewModal] = useState(false)
  const [parsedCVData, setParsedCVData] = useState<ParsedCVResponse | null>(null)
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [addToListCandidateIds, setAddToListCandidateIds] = useState<string[]>([])
  const [addToListCandidateNames, setAddToListCandidateNames] = useState<string[]>([])
  const [showAddListToVacanciesModal, setShowAddListToVacanciesModal] = useState(false)
  const [selectedListForVacancies, setSelectedListForVacancies] = useState<{ id: string; name: string; candidateCount: number } | null>(null)
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  const [showShareSearchModal, setShowShareSearchModal] = useState(false)
  const [shareSearchCandidates, setShareSearchCandidates] = useState<Array<{ id: string; name: string; email?: string; avatar_url?: string; current_title?: string; linkedin_url?: string }>>([])
  const [shareSearchTitle, setShareSearchTitle] = useState('')
  const [showCreditConfirmation, setShowCreditConfirmation] = useState(false)
  const [pendingSearchRequest, setPendingSearchRequest] = useState<{
    query: string; entities?: ParsedEntities; mode?: SearchMode; metadata?: SearchMetadata
  } | null>(null)
  const [creditEstimate, setCreditEstimate] = useState<CreditEstimate | null>(null)
  const [searchThreadId, setSearchThreadId] = useState<string | undefined>(undefined)
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [showContactFilterModal, setShowContactFilterModal] = useState(false)
  const [pendingContactFilter, setPendingContactFilter] = useState<'email' | 'phone' | null>(null)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [isSavingToBase, setIsSavingToBase] = useState(false)
  const [isAddingToList, setIsAddingToList] = useState(false)
  const [showUnsavedWarningModal, setShowUnsavedWarningModal] = useState(false)
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [pendingTabChange, setPendingTabChange] = useState<string | null>(null)
  const [isLIAThinking, setIsLIAThinking] = useState(false)

  // ── Derived ───────────────────────────────────────────────────────────────
  const unsavedPearchCandidates = candidates.filter(c => c.source === 'pearch')
  const hasUnsavedPearchCandidates = unsavedPearchCandidates.length > 0 && showSearchResults
  const searchTemplates = SEARCH_TEMPLATES

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
    searchSource, pearchSearchOptions, toast,
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
    toast,
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
    setDisplayedResultsCount, setChatMessages, toast,
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
    toast, user,
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

  // ── Candidate interaction handlers ────────────────────────────────────────
  const handleCandidateClick = (candidate: Candidate) => {
    setPreviewCandidate(candidate)
    setShowCandidatePreview(true)
    markCandidateAsViewed(candidate.id, 'profile')
    onAddRecentItem?.({
      id: candidate.id, type: 'candidato', title: candidate.name,
      subtitle: candidate.currentRole || candidate.location,
      meta: { candidateId: candidate.id },
    })
  }

  const handleCloseCandidatePreview = () => { setShowCandidatePreview(false); setPreviewCandidate(null) }
  const handleTogglePreviewMaximize = () => { setIsPreviewMaximized(!isPreviewMaximized) }
  const handleCandidatePageOpen = (candidate: Candidate) => { router.push(`/funil-de-talentos/candidato/${candidate.id}`) }
  const handleCloseSidePreview = () => { setShowSidePreview(false); setSidePreviewCandidate(null) }
  const handleClosePreview = () => { setShowPreview(false); setSelectedCandidate(null); setIsPreviewMaximized(false) }
  const handleToggleMaximize = () => { setIsPreviewMaximized(!isPreviewMaximized) }
  const handleCloseCandidatePage = () => { setShowCandidatePage(false); setSelectedCandidate(null) }

  const handleCandidateSelection = (
    candidateId: string,
    _index: number,
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    event.stopPropagation()
    const newSelected = new Set(selectedCandidatesForBatch)
    if (event.target.checked) newSelected.add(candidateId)
    else newSelected.delete(candidateId)
    setSelectedCandidatesForBatch(newSelected)
  }
  const selectAllCandidates = () => { setSelectedCandidatesForBatch(new Set(sortedCandidates.map(c => c.id))) }
  const deselectAllCandidates = () => { setSelectedCandidatesForBatch(new Set()) }

  // ── Actions sub-hook ──────────────────────────────────────────────────────
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
    lastSearchQuery, deselectAllCandidates,
    toast, user,
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

  // ── WSI handlers ──────────────────────────────────────────────────────────
  const handleStartWSITextScreening = (candidate: Candidate) => { setWsiInviteCandidate(candidate); setShowWSIInviteModal(true) }
  const handleOpenWSIModal = (candidate: Candidate) => { setWsiCandidateForScreening(candidate); setShowWSITextModal(true) }
  const handleStartWSIVoiceScreening = (candidate: Candidate) => { setWsiCandidateForScreening(candidate); setShowWSIVoiceModal(true) }
  const handleWSIScreeningComplete = (_result: Record<string, unknown>) => {}

  // ── Preview resize ────────────────────────────────────────────────────────
  const handlePreviewResize = (e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = previewWidth
    const onMove = (ev: MouseEvent) => {
      setPreviewWidth(Math.min(Math.max(PREVIEW_WIDTH_MIN, startWidth + (startX - ev.clientX)), PREVIEW_WIDTH_MAX))
    }
    const onUp = () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  const handleLIAClick = (candidate: Candidate) => { setSelectedCandidateForLIA(candidate); setShowLIAPromptForCandidate(true) }

  // ── Sort helpers ──────────────────────────────────────────────────────────
  const handleSort = (field: string) => {
    if (sortBy === field) setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    else { setSortBy(field); setSortOrder('desc') }
  }
  const getSortIcon = (field: string) => {
    if (sortBy !== field) return <ArrowUpDown className="w-3 h-3 ml-1" />
    return sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
  }

  // ── Filter count / clear helpers (pure fns from useCandidatesFilters) ─────
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
    toast({ title: 'Busca salva', description: `${sortedCandidates.length} candidatos encontrados`, duration: 4000 })
  }
  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success border-status-success/30 dark:border-status-success/30'
    if (score >= 80) return 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-secondary border-lia-border-subtle dark:border-lia-border-subtle'
    if (score >= 70) return 'bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning border-status-warning/30 dark:border-status-warning/30'
    return 'bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error border-status-error/30 dark:border-status-error/30'
  }

  // ── LIA chat stubs (filled by ref after liaHandlers is wired) ─────────────
  const liaHandlersRef = React.useRef<ReturnType<typeof useCandidatesLIAHandlers> | null>(null)
  const handleLIAChatMessage = async (message: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleLIAChatMessage(message)
  }
  const handleAICommand = async (command: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleAICommand(command)
  }

  // ── Unified communication modal ───────────────────────────────────────────
  const openUnifiedModal = (candidate: Candidate, type: CommunicationType) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }

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
    toast, user, router,
  })
  liaHandlersRef.current = liaHandlers
  const handleQuickAction = liaHandlers.handleQuickAction
  const handleOrchestratedTalentMessage = liaHandlers.handleOrchestratedTalentMessage
  const handleTalentUIAction = liaHandlers.handleTalentUIAction
  const handleCalibrationLike = liaHandlers.handleCalibrationLike
  const handleCalibrationDislike = liaHandlers.handleCalibrationDislike

  // ── Quick-action modal handlers ───────────────────────────────────────────
  const handleSendEmail = (candidate: Candidate) => openUnifiedModal(candidate, 'email')
  const handleSendWhatsApp = (candidate: Candidate) => openUnifiedModal(candidate, 'whatsapp')
  const handleSendTriagem = (candidate: Candidate) => openUnifiedModal(candidate, 'triagem')
  const handleSendAgendamento = (candidate: Candidate) => openUnifiedModal(candidate, 'agendamento')
  const handleSendFeedback = (candidate: Candidate) => openUnifiedModal(candidate, 'feedback')

  const handleNavigateToFullProfile = (candidate: Candidate) => { setSelectedCandidate(candidate); setShowQuickViewModal(false); setShowComparisonModal(false); setShowCandidatePage(true) }
  const handleScheduleInterview = (candidate: Candidate) => { setSelectedCandidateForAction(candidate); setShowComparisonModal(false); setShowScheduleModal(true) }
  const handleContactCandidate = (candidate: Candidate) => { setSelectedCandidateForAction(candidate); setShowComparisonModal(false); setShowContactModal(true) }
  const handleSendMessage = (_data: Record<string, unknown>) => { setShowContactModal(false) }
  const handleScheduleComplete = (_data: Record<string, unknown>) => { setShowScheduleModal(false) }

  const handleBulkEmail = () => { const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id)); if (c) openUnifiedModal(c, 'email') }
  const handleBulkWSIScreening = () => { const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id)); if (c) openUnifiedModal(c, 'triagem') }
  const handleBulkScheduleInterview = () => { const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id)); if (c) openUnifiedModal(c, 'agendamento') }
  const handleBulkFeedback = () => { const c = sortedCandidates.find(c => selectedCandidatesForBatch.has(c.id)); if (c) openUnifiedModal(c, 'feedback') }

  const handleUnifiedModalClose = () => { setUnifiedModalOpen(false); setUnifiedModalCandidate(null) }
  const handleUnifiedModalSend = (data: Record<string, unknown>) => {
    const label = data.type === 'email' ? 'Email' : data.type === 'whatsapp' ? 'WhatsApp' : data.type === 'triagem' ? 'Convite de triagem' : data.type === 'agendamento' ? 'Convite de entrevista' : 'Feedback'
    toast({ title: 'Mensagem enviada!', description: `${label} enviado com sucesso.` })
    handleUnifiedModalClose()
  }
  const handleBatchApprovalComplete = (_data: Record<string, unknown>) => { setShowBatchApproval(false); setSelectedCandidatesForBatch(new Set()) }

  const handleAddCandidate = (newCandidate: Record<string, unknown>) => {
    const c = {
      ...newCandidate,
      candidateId: newCandidate.id,
      tags: (newCandidate.skills as string[]).slice(0, 3),
      status: 'active' as const,
      score: (newCandidate.liaAnalysis as Record<string, unknown>)?.score || 75,
      workModel: newCandidate.workModel as 'remoto' | 'híbrido' | 'presencial',
      contractType: newCandidate.contractType as 'CLT' | 'PJ' | 'Freelancer',
      linkedin: newCandidate.linkedin || '',
      skills: newCandidate.skills || [],
      experience: parseInt(newCandidate.experience as string) || 1,
      education: newCandidate.education || 'Superior Completo',
    }
    setCandidates([c as unknown as Candidate, ...candidates])
    setShowAddCandidateModal(false)
  }

  const getComparisonCandidates = () => sortedCandidates.filter(c => selectedCandidatesForBatch.has(c.id))

  const convertCandidatesForBatch = (cands: Candidate[]) =>
    cands.map(c => ({
      id: c.id, name: c.name, email: c.email, phone: c.phone, position: c.position,
      location: c.location, experience: c.experience.toString(), skills: c.skills,
      education: c.education, score: c.score, status: 'pending' as const,
      workModel: c.workModel, contractType: c.contractType,
      currentSalary: c.salary?.current?.toString() || '',
      expectedSalary: c.salary?.expected?.toString() || '',
      linkedin: c.linkedin, languages: c.languages || [], benefits: c.benefits || [],
      liaScore: c.liaAnalysis?.score || c.score, skillsMatch: c.skills.length,
      currentStage: 'Triagem',
      appliedDate: c.lastUpdated?.toISOString() || new Date().toISOString(),
      lastInteraction: c.lastUpdated?.toISOString() || new Date().toISOString(),
      notes: c.notes || '', github: '', portfolio: '', certifications: [],
      availability: 'Imediata', noticePeriod: '30 dias', priority: 'média' as const,
      source: 'linkedin', tags: c.tags || [], jobTitle: c.position, department: 'Tecnologia',
    }))

  // ── Contextual quick actions ──────────────────────────────────────────────
  const handleQuickSchedule = () => {
    if (selectedCandidatesForBatch.size > 0) { const id = Array.from(selectedCandidatesForBatch)[0]; const c = candidates.find(c => c.id === id); if (c) handleScheduleInterview(c) }
    else handleAICommand('agendar entrevista com candidatos')
  }
  const handleQuickEvaluate = () => {
    if (selectedCandidatesForBatch.size > 0) handleAICommand(`avaliar fit dos ${selectedCandidatesForBatch.size} candidatos selecionados`)
    else handleAICommand('avaliar fit técnico dos candidatos')
  }
  const handleQuickEmail = () => {
    if (selectedCandidatesForBatch.size > 0) { const id = Array.from(selectedCandidatesForBatch)[0]; const c = candidates.find(c => c.id === id); if (c) handleContactCandidate(c) }
    else handleAICommand('gerar email de follow-up para candidatos')
  }
  const handleQuickWhatsApp = () => { handleAICommand('enviar mensagem whatsapp para candidatos') }
  const handleQuickCompare = () => {
    if (selectedCandidatesForBatch.size >= 2) setShowComparisonModal(true)
    else handleAICommand('comparar perfis de candidatos')
  }
  const handleQuickTimeline = () => {
    if (selectedCandidatesForBatch.size > 0) { const id = Array.from(selectedCandidatesForBatch)[0]; const c = candidates.find(c => c.id === id); if (c) handleCandidatePageOpen(c) }
    else handleAICommand('mostrar timeline de interações com candidatos')
  }

  const getCandidateQuickActions = (): QuickAction[] => {
    const n = selectedCandidatesForBatch.size
    return [
      { id: 'schedule', label: n > 0 ? `Agendar (${n})` : 'Agendar', icon: Calendar, variant: 'default' as const, onClick: handleQuickSchedule },
      { id: 'evaluate', label: n > 0 ? `Avaliar Fit (${n})` : 'Avaliar Fit', icon: Target, variant: 'default' as const, onClick: handleQuickEvaluate },
      { id: 'compare', label: n >= 2 ? `Comparar (${n})` : 'Comparar', icon: ChevronsLeftRight, variant: 'default' as const, onClick: handleQuickCompare },
      { id: 'email', label: n > 0 ? `Email (${n})` : 'Email', icon: Mail, variant: 'success' as const, onClick: handleQuickEmail },
      { id: 'whatsapp', label: 'WhatsApp', icon: MessageSquare, variant: 'success' as const, onClick: handleQuickWhatsApp },
      { id: 'approve', label: n > 0 ? `Aprovar (${n})` : 'Aprovar', icon: CheckCircle, variant: 'success' as const, onClick: () => setShowBatchApproval(true) },
    ]
  }

  // ── CV legacy handlers ────────────────────────────────────────────────────
  const handleCVParsed = (data: ParsedCVResponse) => { setParsedCVData(data); setShowCVPreviewModal(true) }
  const handleCVConfirmed = (_candidateId: string) => { setShowCVPreviewModal(false); setParsedCVData(null); handleBulkActionComplete() }
  const mapCandidateToInternal = _mapCandidateToInternal

  // ── RETURN — same shape as original; do not rename anything ──────────────
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
    talentFunnel, toast, toggleTableFilter, unifiedModalCandidate, unifiedModalOpen, unifiedModalType,
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
