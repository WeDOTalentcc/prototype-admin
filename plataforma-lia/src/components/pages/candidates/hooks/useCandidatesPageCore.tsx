"use client"

import { cn } from "@/lib/utils"
import React, { useState, useEffect, useRef } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { flushSync } from "react-dom"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { callOrchestratedTalentChat, OrchestratedTalentChatResponse } from "@/lib/api/kanban-assistant"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { LIAIcon } from "@/components/ui/lia-icon"
import {
  Users, Plus, Search, X, Eye, Star, Check,
  Pin, MapPin, Linkedin, CheckCircle, Filter, ArrowUpDown,
  ArrowUp, ArrowDown, ChevronsLeftRight, Target, User,
  Bookmark, Play, Edit, BarChart3, PieChart, Zap, Brain,
  Calendar, Clock, TrendingUp, Building, AlertCircle, DollarSign,
  Briefcase, ArrowLeft, Mail, Phone, MessageSquare, Github, Code, Layers, FileText, Globe, Home, Send, Lightbulb, Mic, Paperclip, Download, FileUp, GripVertical,
  Settings, GraduationCap, HelpCircle, Loader2, Crown, Rocket, Copy, List, Scale, ChevronRight,
  Maximize2, Minimize2, PanelLeftClose, PanelLeft, ChevronDown
} from "lucide-react"

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"
import { ContextualActionsBanner } from "@/components/contextual-actions-banner"
import { BatchApprovalModal } from "@/components/batch-approval-modal"
import { RubricEvaluationModal } from "@/components/rubric-evaluation-modal"
import { NewCandidateUnifiedModal } from "@/components/modals/new-candidate-unified-modal"
import { ContextPill } from "@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from "@/components/ui/quick-action-chips"
import { LiaSearchQueriesGuide } from "@/components/ui/lia-search-queries-guide"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { ActionResultCard } from "@/components/chat/action-result-card"

import { ContactModal, ScheduleModal } from "@/components/quick-actions-modals"
import { GlobalExpansionConfirmModal } from "@/components/pages/candidates/GlobalExpansionConfirmModal"
import { SourceChangeConfirmModal } from "@/components/pages/candidates/SourceChangeConfirmModal"
import { ContactFilterConfirmModal } from "@/components/pages/candidates/ContactFilterConfirmModal"
import { DeleteArchetypeModal } from "@/components/pages/candidates/DeleteArchetypeModal"
import { LIASearchSidebar } from "@/components/pages/candidates/LIASearchSidebar"
import { QuickViewModal } from "@/components/quick-view-modal"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { CandidateComparison } from "@/components/candidate-comparison"

import { FavoritesTab } from "@/components/talent-funnel-tabs/favorites-tab"
import { HistoryTab } from "@/components/talent-funnel-tabs/history-tab"
import { SavedSearchesTab } from "@/components/talent-funnel-tabs/saved-searches-tab"
import { ListsTab } from "@/components/talent-funnel-tabs/lists-tab"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { useJWTAuth } from "@/contexts/auth-context"
import { AddListToVacanciesModal } from "@/components/modals/add-list-to-vacancies-modal"
import { UnsavedPearchWarningModal } from "@/components/modals/unsaved-pearch-warning-modal"
import { useTalentFunnel, type SearchHistoryItem, type SavedSearch } from "@/hooks/use-talent-funnel"

import { type ParsedEntities, type SearchMode, type SearchMetadata } from "@/components/search/smart-search-input"

import { type SearchFilters } from "@/components/search/advanced-filters-modal"
import { FilterAutocomplete } from "@/components/search/filter-autocomplete"

import { WSITextScreeningModal, WSIVoiceScreeningStatus, WSIScorecard } from "@/components/wsi"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
import { SendEmailModal } from "@/components/email-templates"
import { CVPreview, type ParsedCVResponse } from "@/components/cv"
import { LIAFeedbackWidget } from "@/components/calibration"
import { ProactiveInsightCard, type SearchAnalytics } from "@/components/proactive-insight-card"
import { UnifiedCandidateTable } from "@/components/tables"
import type { TableColumn, TableSortConfig } from "@/components/tables/types"
import { SearchLoadingAnimation } from "@/components/ui/search-loading-animation"
import { CalibrationCard, type CalibrationCandidate } from "@/components/calibration-card"
import { CandidateReviewModal, type ReviewCandidate, type Criterion } from "@/components/pages/candidate-review-modal"
import { JobVacancy, EmailTemplate } from "@/services/lia-api"

import { CreditConfirmationDialog } from "@/components/search/credit-confirmation-dialog"

import { RevealCreditsModal } from "@/components/reveal-credits-modal"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

import {
  searchCandidates as searchCandidatesHybrid,
  searchLocalCandidates,
  estimateCredits,
  calculateCreditsLocally,
  type SearchRequest,
  type SearchResponse,
  type CreditEstimate
} from "@/lib/api/candidate-search"

import { getSourceDetails, isGlobalSource, isLocalSource } from "@/lib/utils/source-detection"
import { useToast } from "@/hooks/use-toast"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
import { useHideViewedCandidates } from "@/hooks/useHideViewedCandidates"
import { useCandidateFilters, type TableFilters, getDefaultTableFilters } from "@/hooks/use-candidate-filters"
import { useCandidateSelection } from "@/hooks/use-candidate-selection"
import { useBulkCandidateDataRequests } from "@/hooks/use-candidate-data-requests"
import { useCandidatesListMapped } from "@/hooks/use-candidates-list-mapped"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

import { textStyles, cardStyles, badgeStyles, formatScore, formatScorePercent } from "@/lib/design-tokens"
import { CandidateTabs } from "@/components/pages/candidates/CandidateTabs"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"
import { SearchResultsHeader } from "@/components/pages/candidates/SearchResultsHeader"
import { CandidatesFilterPanel } from "@/components/pages/candidates/CandidatesFilterPanel"
import { CandidateSearchResultsView } from "@/components/pages/candidates/CandidateSearchResultsView"
import type { Candidate } from "@/components/pages/candidates/types"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { CreditConfirmationModal } from "@/components/pages/candidates/CreditConfirmationModal"
import { SaveAsArchetypeModal } from "@/components/pages/candidates/SaveAsArchetypeModal"
import { EditQueryModal } from "@/components/pages/candidates/EditQueryModal"
import { PreviewSuggestionModal } from "@/components/pages/candidates/PreviewSuggestionModal"
import { useCandidatesCVHandlers } from "@/components/pages/candidates/hooks/useCandidatesCVHandlers"
import { useCandidatesSearch } from "@/components/pages/candidates/hooks/useCandidatesSearch"
import { useCandidatesLIAHandlers } from "@/components/pages/candidates/hooks/useCandidatesLIAHandlers"
import { useCandidatesActions } from "@/components/pages/candidates/hooks/useCandidatesActions"
import { createCellRenderer } from "@/components/pages/candidates/CandidateTableCellRenderer"
import { useCandidatesSearchState } from "@/hooks/use-candidates-search-state"
import { useCandidatesViewState } from "@/hooks/use-candidates-view-state"
import { useCandidatesArchetypes, type Archetype, type BackendArchetype, type AISuggestion } from "@/components/pages/candidates/hooks/useCandidatesArchetypes"
import { useCandidatesTableConfig } from "@/components/pages/candidates/hooks/useCandidatesTableConfig"
import { useCandidatesFilterSort } from "@/components/pages/candidates/hooks/useCandidatesFilterSort"
import { useRevealContact } from "@/components/pages/candidates/hooks/useRevealContact"
import { useCandidatesColumnConfig } from "@/components/pages/candidates/hooks/useCandidatesColumnConfig"
import { useCandidatesExecuteSearch, mapCandidateToInternal as _mapCandidateToInternal } from "@/components/pages/candidates/hooks/useCandidatesExecuteSearch"

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const SmartSearchInput = dynamic(
  () => import("@/components/search/smart-search-input").then(m => ({ default: m.SmartSearchInput })).catch(() => {
    return { default: () => null as unknown }
  }),
  { ssr: false, loading: () => <div className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" /> }
)
const AdvancedFiltersModal = dynamic(() => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })), { ssr: false })
// Tipo para controle de origem de busca (local, global ou híbrido)
type SearchSource = 'local' | 'global' | 'hybrid'

// Configurações das abas - Simplificado (Busca mostra resultados inline, como Google/LinkedIn)
const tabs = [
  { id: 'search', label: 'Busca' },
  { id: 'favorites', label: 'Favoritos' },
  { id: 'lists', label: 'Listas' },
  { id: 'saved-searches', label: 'Buscas Salvas' },
  { id: 'history', label: 'Histórico' }
]

export interface CandidatesPageCoreProps {
  onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void
  pendingCandidateOpen?: { candidateId: string; candidateName: string } | null
  onCandidateOpened?: () => void
}

export function useCandidatesPageCore({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened }: CandidatesPageCoreProps = {}) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const expandedSearchParam = searchParams.get('expandedSearch')
  const { settings: globalSettings, loading: globalSettingsLoading } = useGlobalSearchSettings()
  const { user } = useJWTAuth()
  
  // Hook for hiding viewed candidates
  const hideViewedCandidates = useHideViewedCandidates({
    userId: user?.id,
    companyId: user?.company_id,
    userEmail: user?.email
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

  // Only show global/hybrid options after settings are loaded AND global search is enabled
  const showGlobalSearchOptions = !globalSettingsLoading && globalSettings.globalSearchEnabled

  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isSearchActive, setIsSearchActive] = useState(false)

  // F3: hook de candidatos — fonte de verdade para carga inicial do backend
  const candidatesListHook = useCandidatesListMapped()

  // Data requests em bulk para os candidatos visíveis — Sprint E F3 (aditivo, não conflita)
  const {
    dataRequestsMap,
    getDataRequestForCandidate,
  } = useBulkCandidateDataRequests({
    candidateIds: candidates.map(c => c.id),
    enabled: candidates.length > 0,
  })

  // F3: sync hook data → local state (base view candidates + loading)
  // Search handlers override candidates via setCandidates when results arrive;
  // hook is the source of truth for the base/local candidates view.
  useEffect(() => {
    setCandidates(candidatesListHook.candidates)
    setIsLoading(candidatesListHook.loading)
  }, [candidatesListHook.candidates, candidatesListHook.loading])

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

  useEffect(() => {
    if (pendingCandidateOpen && candidates.length > 0) {
      const found = candidates.find(c => c.id === pendingCandidateOpen.candidateId)
      if (found) {
        setPreviewCandidate(found)
        setShowCandidatePreview(true)
      }
      onCandidateOpened?.()
    }
  }, [pendingCandidateOpen, candidates, onCandidateOpened])

  // ========== SEARCH STATE (Sprint 4.11 — extracted to useCandidatesSearchState) ==========
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

  const { toast } = useToast()

  const { saveTalentFunnelState } = useNavigationPersistence()

  // ========== VIEW STATE (Sprint 4.11 — extracted to useCandidatesViewState) ==========
  // Declared here (before effects) so setters are in scope for all effect closures below
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

  useEffect(() => {
    if (activeTab === 'search' || activeTab === 'favorites' || activeTab === 'lists') {
      saveTalentFunnelState(activeTab, lastSearchQuery)
    }
  }, [activeTab, lastSearchQuery, saveTalentFunnelState])

  // Reset search source to local if global search is disabled
  useEffect(() => {
    if (!showGlobalSearchOptions && (searchSource === 'hybrid' || searchSource === 'global')) {
      setSearchSource('local')
    }
  }, [showGlobalSearchOptions, searchSource])

  // Handle expandedSearch URL parameter - open results view with expanded prompt
  useEffect(() => {
    if (expandedSearchParam === 'true') {
      setShowSearchResults(true)
      setDisplayedResultsCount(10)
      setActiveTab('search')
    }
  }, [expandedSearchParam])

  // ========== CANDIDATE LISTS STATE (for unified modal) ==========
  const [candidateListsForModal, setCandidateListsForModal] = useState<Array<{ id: string; name: string; color?: string }>>([])

  // Load candidate lists + viewed candidates on mount
  useEffect(() => {
    liaApi.getCandidateLists({ limit: 50 })
      .then(r => r?.items && setCandidateListsForModal(r.items.map((l: { id: string; name: string; color?: string }) => ({ id: l.id, name: l.name, color: l.color }))))
      .catch(() => setCandidateListsForModal([]))
    fetch('/api/backend-proxy/candidates/viewed')
      .then(r => r.ok ? r.json() : null)
      .then(data => data?.candidate_ids && setViewedCandidateIds(new Set(data.candidate_ids)))
      .catch(() => {})
  }, [])
  
  // Auto-populate tableFilters from search entities when a new search is executed
  useEffect(() => {
    if (searchExecutionId > 0) {
      const e = lastSearchEntities
      const yearsExp = e?.years_experience
      const parsedYears = typeof yearsExp === 'string' ? parseInt(yearsExp, 10) : yearsExp
      setTableFilters(prev => ({ ...prev,
        locations: e?.location ? [e.location] : [],
        jobTitles: e?.job_title ? [e.job_title] : [],
        skills: e?.skills?.length ? e.skills : [],
        industries: e?.industry ? [e.industry] : [],
        seniorityLevels: e?.seniority ? [e.seniority] : [],
        minExperience: (parsedYears !== undefined && !isNaN(parsedYears)) ? parsedYears : undefined,
        companies: e?.company ? [e.company] : []
      }))
    }
  }, [searchExecutionId])

  // Mark candidate as viewed when clicked
  const markCandidateAsViewed = async (candidateId: string, source: string = 'profile') => {
    try {
      await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ source }) })
      setViewedCandidateIds(prev => new Set([...prev, candidateId]))
    } catch {}
  }
  
  const talentFunnel = useTalentFunnel()
  
  // Estados derivados do hook para compatibilidade com componentes existentes
  const favorites = talentFunnel.getFavoriteIds()
  const pinnedCandidates = talentFunnel.getPinnedIds()
  const favoriteNotes = talentFunnel.getFavoriteNotes()
  
  const [itemsPerPage] = useState(50)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  // Estados para critérios de busca, sugestões e assistente no modal expandido da LIA
  const [liaPromptEntities, setLiaPromptEntities] = useState<ParsedEntities>({
    job_title: undefined,
    location: undefined,
    skills: [],
    years_experience: undefined,
    industry: undefined,
    seniority: undefined,
    company: undefined
  })
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(true)
  const [showLiaAssistant, setShowLiaAssistant] = useState(false)
  const [liaIsParsingEntities, setLiaIsParsingEntities] = useState(false)
  const [liaSuggestions, setLiaSuggestions] = useState<string[]>([])
  const [liaAssistantTips, setLiaAssistantTips] = useState<string[]>([
    "Seja específico sobre habilidades técnicas necessárias",
    "Indique a senioridade desejada (júnior, pleno, sênior)",
    "Mencione localização se for relevante para a vaga",
    "Inclua soft skills importantes para o time"
  ])
  
  // Auto-expandir LIA sidebar + mensagem no chat quando candidatos são selecionados
  const prevSelectedCountRef = useRef(0)
  useEffect(() => {
    const currentCount = selectedCandidatesForBatch.size
    const prevCount = prevSelectedCountRef.current
    if (currentCount > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
      if (currentCount !== prevCount) {
        const names = candidates.filter(c => selectedCandidatesForBatch.has(c.id)).slice(0, 3).map(c => c.name)
        const preview = names.join(', ') + (currentCount > 3 ? ` e mais ${currentCount - 3}` : '')
        const plural = currentCount > 1
        setChatMessages(prev => [...prev, {
          id: `lia-selection-${Date.now()}`, type: 'lia' as const,
          content: `Você selecionou **${currentCount} candidato${plural ? 's' : ''}**: ${preview}.\n\nPosso analisar ${plural ? 'estes candidatos' : 'este candidato'} para você:\n\n• **Analisar potencial de crescimento**\n• **Definir tipo de perfil** (executor, estratégico, etc)\n• **Resumo executivo do perfil**`,
          timestamp: new Date()
        }])
      }
    }
    prevSelectedCountRef.current = currentCount
  }, [selectedCandidatesForBatch.size, userCollapsedLIA, candidates, selectedCandidatesForBatch])
  
  // Parsing de entidades do liaPromptValue com debounce
  useEffect(() => {
    const emptyEntities = { job_title: undefined, location: undefined, skills: [], years_experience: undefined, industry: undefined, seniority: undefined, company: undefined }
    if (!liaPromptValue.trim()) { setLiaPromptEntities(emptyEntities); setLiaSuggestions([]); return }
    const timer = setTimeout(async () => {
      setLiaIsParsingEntities(true)
      try {
        const res = await fetch('/api/backend-proxy/search/parse-query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: liaPromptValue }) })
        if (res.ok) {
          const data = await res.json()
          const e = data.entities || data
          setLiaPromptEntities({ job_title: e.job_title || undefined, location: e.location || undefined, skills: e.skills || [], years_experience: e.years_experience || undefined, industry: e.industry || undefined, seniority: e.seniority || undefined, company: e.company || undefined })
          setLiaSuggestions(Array.isArray(data.suggestions) ? data.suggestions : [])
        }
      } catch {} finally { setLiaIsParsingEntities(false) }
    }, 500)
    return () => clearTimeout(timer)
  }, [liaPromptValue])
  
  // Estados para o novo sistema de pesquisa avançada da LIA - 6 abas
  type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('ia-natural')
  const [liaWidth, setLiaWidth] = useState(400) // Largura padrão 400px - ElevenLabs pattern
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  const [isLiaSuperChat, setIsLiaSuperChat] = useState(false) // Modo superchat expandido
  
  // Estado para modal de filtros avançados removido - agora usa painel lateral
  
  const [pearchSearchOptions, setPearchSearchOptions] = useState({
    searchType: 'fast' as 'fast' | 'pro',
    limit: 50,
    showEmails: false,
    showPhoneNumbers: false,
    highFreshness: false,
    requireEmails: false,
    requirePhoneNumbers: false
  })

  type ChatMessage = {
    id: string
    type: 'user' | 'lia' | 'proactive_insight' | 'calibration'
    content: string
    timestamp: Date
    searchResults?: {
      localCount: number
      globalCount: number
      query: string
    }
    analytics?: SearchAnalytics
    candidates?: CalibrationCandidate[]
    metadata?: {
      action_executed?: boolean
      action_result?: Record<string, unknown>
      action_type?: string
      needs_confirmation?: boolean
      needs_params?: boolean
      pending_action_id?: string
      conversation_id?: string
    }
  }
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])

  const archetypesHook = useCandidatesArchetypes({
    searchSource, pearchSearchOptions, toast,
    setCandidates, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount,
    setLastSearchQuery, setLastSearchMode, setActiveSearchTab: (_v: string) => setActiveSearchTab(v),
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
  const [activeSearchFilters, setActiveSearchFilters] = useState<SearchFilters>({
    ppiOptions: {},
    general: {},
    locations: {},
    job: {},
    company: {},
    skills: {},
    education: {},
    languages: {}
  })
  
  // Estados para resultado de busca com separação local/global
  const [searchResults, setSearchResults] = useState<{
    local: Candidate[]
    global: Candidate[]
    localCount: number
    globalCount: number
    query: string
    isLoading: boolean
    showGlobalResults: boolean
    globalDismissed: boolean
  }>({
    local: [],
    global: [],
    localCount: 0,
    globalCount: 0,
    query: "",
    isLoading: false,
    showGlobalResults: false,
    globalDismissed: false
  })
  
  // CV Dropzone handlers — extracted to useCandidatesCVHandlers
  const cvHandlers = useCandidatesCVHandlers({
    setCandidates, setIsDroppingCV, setCvUploadLoading,
    setHasSearchResults, setSearchResultsCount, setShowSearchResults,
    setDisplayedResultsCount, setChatMessages, toast,
  })
  const handleCVDrop = cvHandlers.handleCVDrop
  const handleCVDragOver = cvHandlers.handleCVDragOver
  const handleCVDragLeave = cvHandlers.handleCVDragLeave
  
  // Abrir o painel LIA automaticamente ao carregar a página
  useEffect(() => {
    setShowExpandedLIA(true)
  }, [])

  const [previewWidth, setPreviewWidth] = useState(420) // 420px padrão - aumentado para acomodar informações

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
          const companyName = data.company
          setSearchTerm(`empresa:"${companyName}"`)
          setQuickFilters(new Set(['company_filter']))
        }

        sessionStorage.removeItem('candidates-filter-data')
      } catch (error) {
      }
    } else if (tabParam === 'candidates' && filterParam === 'company' && companyParam) {
      const companies = companyParam.split(',')
      setCrossTabFilter({
        type: 'company',
        companies: companies,
        source: 'url'
      })
      setShowCrossTabBanner(true)
      setSearchTerm(`empresas:${companies.join(',')}`)
    }
  }, [])

  const clearCrossTabFilter = () => { setCrossTabFilter(null); setShowCrossTabBanner(false); setSearchTerm(""); setQuickFilters(new Set()); window.history.replaceState({}, '', window.location.pathname) }

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
  const [bulkJobVacancies, setBulkJobVacancies] = useState<JobVacancy[]>([])
  const [bulkEmailTemplates, setBulkEmailTemplates] = useState<EmailTemplate[]>([])
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
    query: string
    entities?: ParsedEntities
    mode?: SearchMode
    metadata?: SearchMetadata
  } | null>(null)
  const [creditEstimate, setCreditEstimate] = useState<CreditEstimate | null>(null)
  const [searchThreadId, setSearchThreadId] = useState<string | undefined>(undefined)
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [showContactFilterModal, setShowContactFilterModal] = useState(false)
  const [pendingContactFilter, setPendingContactFilter] = useState<'email' | 'phone' | null>(null)

  const revealContactHook = useRevealContact({ setCreditsRemaining: (fn) => setCreditsRemaining(typeof fn === 'function' ? fn(creditsRemaining) : fn), toast })
  const { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing } = revealContactHook.state
  const { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact } = revealContactHook.actions
  
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [isSavingToBase, setIsSavingToBase] = useState(false)
  const [isAddingToList, setIsAddingToList] = useState(false)
  const [showUnsavedWarningModal, setShowUnsavedWarningModal] = useState(false)
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)
  const [pendingTabChange, setPendingTabChange] = useState<string | null>(null)
  
  // Calcular candidatos Pearch não salvos nos resultados atuais
  const unsavedPearchCandidates = candidates.filter(c => c.source === 'pearch')
  const hasUnsavedPearchCandidates = unsavedPearchCandidates.length > 0 && showSearchResults

  // Load job vacancies and email templates for bulk actions
  useEffect(() => {
    liaApi.listJobVacancies().then(r => r.items && setBulkJobVacancies(r.items.filter((j: JobVacancy) => j.status === 'open' || j.status === 'draft'))).catch(() => {})
    liaApi.listEmailTemplates(undefined, true).then(r => r.items && setBulkEmailTemplates(r.items)).catch(() => {})
  }, [])

  // Callback for refreshing candidates after bulk actions
  const handleBulkActionComplete = () => {
    setIsLoading(true)
    liaApi.listCandidates(undefined, undefined, 0, 100)
      .then(response => {
        if (response.items?.length > 0) {
          setCandidates(response.items.map((c: CandidateLocal) => mapCandidateToInternal(c as unknown as Record<string, unknown>)))
        }
        setIsLoading(false)
      })
      .catch(() => setIsLoading(false))
  }

  // CV Parser handlers (legado - mantido para compatibilidade)
  const handleCVParsed = (data: ParsedCVResponse) => {
    setParsedCVData(data)
    setShowCVPreviewModal(true)
  }

  const handleCVConfirmed = (candidateId: string) => {
    setShowCVPreviewModal(false)
    setParsedCVData(null)
    handleBulkActionComplete()
  }

  // Helper para mapear candidato do backend para formato interno
  const mapCandidateToInternal = _mapCandidateToInternal

  // ── Função principal de busca — extraída para useCandidatesExecuteSearch ──
  const { executeSearch } = useCandidatesExecuteSearch({
    searchSource, pearchSearchOptions, searchThreadId, setSearchThreadId,
    hideViewedCandidatesFilter: hideViewedCandidates.filterCandidates,
    talentFunnel,
    setCandidates, setSearchResults, setHasSearchResults, setSearchResultsCount,
    setLocalResultsCount, setPearchResultsCount, setCreditsUsedInSearch,
    setCreditsRemaining: (fn) => setCreditsRemaining(typeof fn === 'function' ? fn(creditsRemaining ?? 0) : fn),
    setShowSearchResults, setDisplayedResultsCount, setCurrentSearchSource,
    setHasSearched, setLastSearchEntities, setLastSearchMetadata, setLastSearchUsedPearch,
    setSearchExecutionId, setShowExpandGlobalOption, setShowExpandedLIA, setUserCollapsedLIA,
    setLastSuccessfulQuery, setChatMessages, setIsLoading, setIsSearchActive,
  })



  const [selectedTemplate, setSelectedTemplate] = useState("")
  // Search handlers — extracted to useCandidatesSearch
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

  // Estados para LIA micro-interação
  const [isLIAThinking, setIsLIAThinking] = useState(false)

  // ── Column config — extraído para useCandidatesColumnConfig ──
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
  // Helper para renderizar valor de célula genérica — extraído para CandidateTableCellRenderer
  const renderCellValue = createCellRenderer({
    searchFeedbacks,
    revealedContacts,
    searchQuery: searchResults.query,
    viewedCandidateIds,
    expandedRows,
    onSearchFeedbackChange: handleSearchFeedbackChange,
    onRevealContact: openRevealModal,
    onToggleExpandedRow: (candidateId) =>
      setExpandedRows((prev) => {
        const newSet = new Set(prev)
        if (newSet.has(candidateId)) {
          newSet.delete(candidateId)
        } else {
          newSet.add(candidateId)
        }
        return newSet
      }),
  })

  // Estados para templates de busca (cobrindo: Location, Job Title, Experience, Industry, Skills)
  const searchTemplates = [
    "Backend Sênior em São Paulo, 5+ anos em fintechs, Node.js e Python",
    "Frontend Pleno remoto, 3+ anos em startups, React e TypeScript",
    "Product Manager Sênior em Campinas, experiência em B2B SaaS, metodologias ágeis",
    "Data Scientist Pleno híbrido, 4+ anos em e-commerce, Python e machine learning",
    "Tech Lead em São Paulo, 7+ anos em healthtech, liderança de times ágeis"
  ]

  // Funções utilitárias
  const getScoreColor = (score: number) => {
    if (score >= 90) return "bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success border-status-success/30 dark:border-status-success/30"
    if (score >= 80) return "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700"
    if (score >= 70) return "bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning border-status-warning/30 dark:border-status-warning/30"
    return "bg-status-error/15 dark:bg-status-error/30 text-status-error dark:text-status-error border-status-error/30 dark:border-status-error/30"
  }

  const saveCurrentSearch = () => {
    const searchData = {
      name: `Busca ${new Date().toLocaleDateString()}`,
      searchTerm,
      quickFilters: Array.from(quickFilters),
      timestamp: new Date().toISOString()
    }
    sessionStorage.setItem('current-search-data', JSON.stringify(searchData))
    setActiveTab('saved-searches')
    toast({ title: "Busca salva", description: `${sortedCandidates.length} candidatos encontrados`, duration: 4000 })
  }

  const [advancedFilters, setAdvancedFilters] = useState<Record<string, string[]>>({
    work_models: [],
    skills: [],
    companies: [],
    locations: [],
    job_titles: [],
  })

  // ── Filtros e ordenação — extraídos para useCandidatesFilterSort ──
  const {
    filteredCandidates,
    sortedCandidates,
    paginatedCandidates,
    searchDisplayCandidates,
    visibleCandidates,
    getPaginatedCandidates,
  } = useCandidatesFilterSort({
    candidates,
    searchTerm,
    hasSearchResults,
    quickFilters,
    columnFilters,
    advancedFilters,
    tableFilters,
    sortBy,
    sortOrder,
    searchSortBy,
    searchFeedbacks,
    displayedResultsCount,
    showSearchResults,
    currentPage,
    itemsPerPage,
    showOnlyNew,
    viewedCandidateIds,
  })

  // 🔄 Resetar página quando filtros mudarem
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, quickFilters, advancedFilters, columnFilters, tableFilters])

  // Handlers para ações
  const handleCandidateClick = (candidate: Candidate) => {
    setPreviewCandidate(candidate)
    setShowCandidatePreview(true)
    markCandidateAsViewed(candidate.id, 'profile')
    onAddRecentItem?.({
      id: candidate.id,
      type: 'candidato',
      title: candidate.name,
      subtitle: candidate.currentRole || candidate.location,
      meta: { candidateId: candidate.id }
    })
  }

  const handleCloseCandidatePreview = () => {
    setShowCandidatePreview(false)
    setPreviewCandidate(null)
  }

  const handleTogglePreviewMaximize = () => {
    setIsPreviewMaximized(!isPreviewMaximized)
  }

  const handleCandidatePageOpen = (candidate: Candidate) => {
    // Navigate to the dedicated full-page candidate view
    router.push(`/funil-de-talentos/candidato/${candidate.id}`)
  }

  const handleCloseSidePreview = () => {
    setShowSidePreview(false)
    setSidePreviewCandidate(null)
  }

  // CandidatePreviewPanel — extraído para CandidatePreviewPanel.tsx
  // import { CandidatePreviewPanel } from "@/components/pages/candidates/CandidatePreviewPanel"



  const handleClosePreview = () => {
    setShowPreview(false)
    setSelectedCandidate(null)
    setIsPreviewMaximized(false)
  }

  const handleToggleMaximize = () => {
    setIsPreviewMaximized(!isPreviewMaximized)
  }

  const handleCloseCandidatePage = () => {
    setShowCandidatePage(false)
    setSelectedCandidate(null)
  }

  const handleCandidateSelection = (candidateId: string, index: number, event: React.ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation()

    const newSelected = new Set(selectedCandidatesForBatch)

    if (event.target.checked) {
      newSelected.add(candidateId)
    } else {
      newSelected.delete(candidateId)
    }

    setSelectedCandidatesForBatch(newSelected)
  }

  const selectAllCandidates = () => {
    const allIds = new Set(sortedCandidates.map(c => c.id))
    setSelectedCandidatesForBatch(allIds)
  }

  const deselectAllCandidates = () => {
    setSelectedCandidatesForBatch(new Set())
  }

  // Actions handlers — extracted to useCandidatesActions
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
    lastSearchQuery,
    deselectAllCandidates,
    toast, user,
  })
  const handleSaveToLocalBase = candidatesActions.handleSaveToLocalBase
  const handleAddToList = candidatesActions.handleAddToList
  const handleTabChangeWithWarning = candidatesActions.handleTabChangeWithWarning
  const handleSaveAllAndExit = candidatesActions.handleSaveAllAndExit
  const handleExitWithoutSaving = candidatesActions.handleExitWithoutSaving

  // Contar candidatos Pearch selecionados
  const selectedPearchCount = candidates.filter(
    c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
  ).length

  const handleToggleFavorite = (candidateId: string, note?: string) => {
    talentFunnel.toggleFavoriteCandidate(candidateId, note)
  }

  const handleUpdateFavoriteNote = (candidateId: string, note: string) => {
    talentFunnel.updateFavoriteNote(candidateId, note)
  }

  const handleTogglePin = (candidateId: string) => {
    talentFunnel.togglePinnedCandidate(candidateId)
  }
  
  // WSI Screening Handlers
  const handleStartWSITextScreening = (candidate: Candidate) => {
    // Abrir modal de convite de triagem WSI
    setWsiInviteCandidate(candidate)
    setShowWSIInviteModal(true)
  }
  
  // Handler para abrir o modal WSI diretamente (quando precisa preencher manualmente)
  const handleOpenWSIModal = (candidate: Candidate) => {
    setWsiCandidateForScreening(candidate)
    setShowWSITextModal(true)
  }

  const handleStartWSIVoiceScreening = (candidate: Candidate) => {
    setWsiCandidateForScreening(candidate)
    setShowWSIVoiceModal(true)
  }

  const handleWSIScreeningComplete = (result: Record<string, unknown>) => {
  }

  // Handler para resize do preview
  const handlePreviewResize = (e: React.MouseEvent) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = previewWidth

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = startX - moveEvent.clientX
      const newWidth = Math.min(Math.max(280, startWidth + deltaX), 600) // Min: 280px, Max: 600px
      setPreviewWidth(newWidth)
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = 'default'
      document.body.style.userSelect = 'auto'
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }

  const handleLIAClick = (candidate: Candidate) => {
    setSelectedCandidateForLIA(candidate)
    setShowLIAPromptForCandidate(true)
  }

  // Funções de ordenação
  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
  }

  const getSortIcon = (field: string) => {
    if (sortBy !== field) return <ArrowUpDown className="w-3 h-3 ml-1" />
    return sortOrder === 'asc' ? <ArrowUp className="w-3 h-3 ml-1" /> : <ArrowDown className="w-3 h-3 ml-1" />
  }

  // Funções para filtros da tabela de resultados (tableFilters - separado dos filtros de busca)
  const getActiveTableFiltersCount = (): number => {
    let count = 0
    count += tableFilters.statuses.length
    count += tableFilters.tags.length
    count += tableFilters.seniorityLevels.length
    count += tableFilters.workModels.length
    count += tableFilters.contractTypes.length
    count += tableFilters.locations.length
    count += tableFilters.sources.length
    if (tableFilters.minExperience !== undefined) count++
    if (tableFilters.maxExperience !== undefined) count++
    if (tableFilters.minScore !== undefined) count++
    if (tableFilters.maxScore !== undefined) count++
    if (tableFilters.minSalary !== undefined) count++
    if (tableFilters.maxSalary !== undefined) count++
    if (tableFilters.remoteOnly) count++
    if (tableFilters.hasEmail) count++
    if (tableFilters.hasPhone) count++
    if (tableFilters.hasLinkedin) count++
    if (tableFilters.hasGithub) count++
    if (tableFilters.hasPortfolio) count++
    count += tableFilters.softSkills.length
    count += tableFilters.certifications.length
    if (tableFilters.willingToRelocate !== null) count++
    if (tableFilters.mobility !== null) count++
    if (tableFilters.updatedAtFrom) count++
    if (tableFilters.updatedAtTo) count++
    if (tableFilters.lastContactedFrom) count++
    if (tableFilters.lastContactedTo) count++
    if (tableFilters.availabilityWindow) count++
    if (tableFilters.shortlistedDateFrom) count++
    if (tableFilters.shortlistedDateTo) count++
    if (tableFilters.shortlistedVacancyOrigin) count++
    if (tableFilters.placementDateFrom) count++
    if (tableFilters.placementDateTo) count++
    if (tableFilters.placementVacancyDestination) count++
    if (tableFilters.placementClientCompany) count++
    if (tableFilters.specificVacancyId) count++
    if (tableFilters.registrationDateFrom) count++
    if (tableFilters.registrationDateTo) count++
    return count
  }

  const getActiveAdvancedFiltersCount = (): number => {
    return Object.values(advancedFilters).reduce((sum, arr) => sum + arr.length, 0)
  }

  const getActiveSearchFiltersCount = (): number => {
    let count = quickFilters.size
    count += getActiveAdvancedFiltersCount()
    return count
  }

  const toggleTableFilter = (category: keyof TableFilters, value: string) => {
    setTableFilters(prev => {
      const current = prev[category]
      if (Array.isArray(current)) return { ...prev, [category]: current.includes(value) ? current.filter(v => v !== value) : [...current, value] }
      return prev
    })
  }
  const clearAllTableFilters = () => setTableFilters(getDefaultTableFilters())
  const clearAllFilters = () => {
    setSearchTerm(""); setQuickFilters(new Set()); setSelectedTemplate("")
    setColumnFilters({ position: [], company: [], location: [], scoreRange: [], bigFive: { openness: '', conscientiousness: '', extraversion: '', agreeableness: '', neuroticism: '' } })
    clearAllTableFilters()
  }

  // handleLIAChatMessage, handleAICommand — delegates to liaHandlers (wired after openUnifiedModal)
  const liaHandlersRef = React.useRef<ReturnType<typeof useCandidatesLIAHandlers> | null>(null)
  const handleLIAChatMessage = async (message: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleLIAChatMessage(message)
  }
  const handleAICommand = async (command: string) => {
    if (liaHandlersRef.current) return liaHandlersRef.current.handleAICommand(command)
  }

  // AI-First Quick Action Handlers
  const handleQuickSchedule = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const firstSelectedId = Array.from(selectedCandidatesForBatch)[0]
      const candidate = candidates.find((c: Candidate) => c.id === firstSelectedId)
      if (candidate) {
        handleScheduleInterview(candidate)
      }
    } else {
      handleAICommand("agendar entrevista com candidatos")
    }
  }

  const handleQuickEvaluate = () => {
    if (selectedCandidatesForBatch.size > 0) {
      handleAICommand(`avaliar fit dos ${selectedCandidatesForBatch.size} candidatos selecionados`)
    } else {
      handleAICommand("avaliar fit técnico dos candidatos")
    }
  }

  const handleQuickEmail = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const firstSelectedId = Array.from(selectedCandidatesForBatch)[0]
      const candidate = candidates.find((c: Candidate) => c.id === firstSelectedId)
      if (candidate) {
        handleContactCandidate(candidate)
      }
    } else {
      handleAICommand("gerar email de follow-up para candidatos")
    }
  }

  const handleQuickWhatsApp = () => {
    handleAICommand("enviar mensagem whatsapp para candidatos")
  }

  const handleQuickCompare = () => {
    if (selectedCandidatesForBatch.size >= 2) {
      setShowComparisonModal(true)
    } else {
      handleAICommand("comparar perfis de candidatos")
    }
  }

  const handleQuickTimeline = () => {
    if (selectedCandidatesForBatch.size > 0) {
      const firstSelectedId = Array.from(selectedCandidatesForBatch)[0]
      const candidate = candidates.find((c: Candidate) => c.id === firstSelectedId)
      if (candidate) {
        handleCandidatePageOpen(candidate)
      }
    } else {
      handleAICommand("mostrar timeline de interações com candidatos")
    }
  }

  // Get contextual quick actions based on selection
  const getCandidateQuickActions = (): QuickAction[] => {
    const selectedCount = selectedCandidatesForBatch.size
    
    return [
      {
        id: 'schedule',
        label: selectedCount > 0 ? `Agendar (${selectedCount})` : 'Agendar',
        icon: Calendar,
        variant: 'default' as const,
        onClick: handleQuickSchedule
      },
      {
        id: 'evaluate',
        label: selectedCount > 0 ? `Avaliar Fit (${selectedCount})` : 'Avaliar Fit',
        icon: Target,
        variant: 'default' as const,
        onClick: handleQuickEvaluate
      },
      {
        id: 'compare',
        label: selectedCount >= 2 ? `Comparar (${selectedCount})` : 'Comparar',
        icon: ChevronsLeftRight,
        variant: 'default' as const,
        onClick: handleQuickCompare
      },
      {
        id: 'email',
        label: selectedCount > 0 ? `Email (${selectedCount})` : 'Email',
        icon: Mail,
        variant: 'success' as const,
        onClick: handleQuickEmail
      },
      {
        id: 'whatsapp',
        label: 'WhatsApp',
        icon: MessageSquare,
        variant: 'success' as const,
        onClick: handleQuickWhatsApp
      },
      {
        id: 'approve',
        label: selectedCount > 0 ? `Aprovar (${selectedCount})` : 'Aprovar',
        icon: CheckCircle,
        variant: 'success' as const,
        onClick: () => setShowBatchApproval(true)
      }
    ]
  }

  // Handlers para ações dos modais
  const handleSendMessage = (data: Record<string, unknown>) => {
    setShowContactModal(false)
  }

  const handleScheduleComplete = (data: Record<string, unknown>) => {
    setShowScheduleModal(false)
  }

  const handleNavigateToFullProfile = (candidate: Candidate) => {
    setSelectedCandidate(candidate)
    setShowQuickViewModal(false)
    setShowComparisonModal(false)
    setShowCandidatePage(true)
  }

  const handleScheduleInterview = (candidate: Candidate) => {
    setSelectedCandidateForAction(candidate)
    setShowComparisonModal(false)
    setShowScheduleModal(true)
  }

  const handleContactCandidate = (candidate: Candidate) => {
    setSelectedCandidateForAction(candidate)
    setShowComparisonModal(false)
    setShowContactModal(true)
  }

  // Handler for opening the Unified Communication Modal with specific type
  const openUnifiedModal = (candidate: Candidate, type: CommunicationType) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }

  // Wire LIA handlers hook now that all dependencies are available
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
    executeSearch,
    talentFunnel,
    toast, user, router,
  })
  // Bind late ref so stubs work
  liaHandlersRef.current = liaHandlers
  // Export quick action helpers from the hook for JSX consumption
  const handleQuickAction = liaHandlers.handleQuickAction
  const handleOrchestratedTalentMessage = liaHandlers.handleOrchestratedTalentMessage
  const handleTalentUIAction = liaHandlers.handleTalentUIAction
  const handleCalibrationLike = liaHandlers.handleCalibrationLike
  const handleCalibrationDislike = liaHandlers.handleCalibrationDislike

  // Handlers for specific unified modal types
  const handleSendEmail = (candidate: Candidate) => openUnifiedModal(candidate, 'email')
  const handleSendWhatsApp = (candidate: Candidate) => openUnifiedModal(candidate, 'whatsapp')
  const handleSendTriagem = (candidate: Candidate) => openUnifiedModal(candidate, 'triagem')
  const handleSendAgendamento = (candidate: Candidate) => openUnifiedModal(candidate, 'agendamento')
  const handleSendFeedback = (candidate: Candidate) => openUnifiedModal(candidate, 'feedback')

  // Bulk action handlers for ContextualActionsBanner - uses UnifiedCommunicationModal
  const handleBulkEmail = () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const firstCandidate = sortedCandidates.find(c => selectedIds.includes(c.id))
    if (firstCandidate) {
      openUnifiedModal(firstCandidate, 'email')
    }
  }

  const handleBulkWSIScreening = () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const firstCandidate = sortedCandidates.find(c => selectedIds.includes(c.id))
    if (firstCandidate) {
      openUnifiedModal(firstCandidate, 'triagem')
    }
  }

  const handleBulkScheduleInterview = () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const firstCandidate = sortedCandidates.find(c => selectedIds.includes(c.id))
    if (firstCandidate) {
      openUnifiedModal(firstCandidate, 'agendamento')
    }
  }

  const handleBulkFeedback = () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const firstCandidate = sortedCandidates.find(c => selectedIds.includes(c.id))
    if (firstCandidate) {
      openUnifiedModal(firstCandidate, 'feedback')
    }
  }

  const handleUnifiedModalClose = () => {
    setUnifiedModalOpen(false)
    setUnifiedModalCandidate(null)
  }

  const handleUnifiedModalSend = (data: Record<string, unknown>) => {
    toast({
      title: "Mensagem enviada!",
      description: `${data.type === 'email' ? 'Email' : data.type === 'whatsapp' ? 'WhatsApp' : data.type === 'triagem' ? 'Convite de triagem' : data.type === 'agendamento' ? 'Convite de entrevista' : 'Feedback'} enviado com sucesso.`,
    })
    handleUnifiedModalClose()
  }

  const handleBatchApprovalComplete = (data: Record<string, unknown>) => {
    setShowBatchApproval(false)
    setSelectedCandidatesForBatch(new Set())
  }

  const handleAddCandidate = (newCandidate: Record<string, unknown>) => {
    const candidateWithDefaults = {
      ...newCandidate,
      candidateId: newCandidate.id,
      tags: newCandidate.skills.slice(0, 3),
      status: 'active' as const,
      score: newCandidate.liaAnalysis?.score || 75,
      workModel: newCandidate.workModel as 'remoto' | 'híbrido' | 'presencial',
      contractType: newCandidate.contractType as 'CLT' | 'PJ' | 'Freelancer',
      linkedin: newCandidate.linkedin || '',
      skills: newCandidate.skills || [],
      experience: parseInt(newCandidate.experience) || 1,
      education: newCandidate.education || 'Superior Completo'
    }

    setCandidates([candidateWithDefaults, ...candidates])
    setShowAddCandidateModal(false)
  }

  const getComparisonCandidates = () => {
    return sortedCandidates.filter(candidate => selectedCandidatesForBatch.has(candidate.id))
  }

  const convertCandidatesForBatch = (candidates: Candidate[]) => {
    return candidates.map(candidate => ({
      id: candidate.id,
      name: candidate.name,
      email: candidate.email,
      phone: candidate.phone,
      position: candidate.position,
      location: candidate.location,
      experience: candidate.experience.toString(),
      skills: candidate.skills,
      education: candidate.education,
      score: candidate.score,
      status: 'pending' as const,
      workModel: candidate.workModel,
      contractType: candidate.contractType,
      currentSalary: candidate.salary?.current?.toString() || '',
      expectedSalary: candidate.salary?.expected?.toString() || '',
      linkedin: candidate.linkedin,
      languages: candidate.languages || [],
      benefits: candidate.benefits || [],
      // Campos adicionais requeridos pelo BatchApprovalCandidate
      liaScore: candidate.liaAnalysis?.score || candidate.score,
      skillsMatch: candidate.skills.length,
      currentStage: 'Triagem',
      appliedDate: candidate.lastUpdated?.toISOString() || new Date().toISOString(),
      lastInteraction: candidate.lastUpdated?.toISOString() || new Date().toISOString(),
      notes: candidate.notes || '',
      github: '',
      portfolio: '',
      certifications: [],
      availability: 'Imediata',
      noticePeriod: '30 dias',
      priority: 'média' as const,
      source: 'linkedin',
      tags: candidate.tags || [],
      jobTitle: candidate.position,
      department: 'Tecnologia'
    }))
  }

  // handleToggleColumnConfig, handleSaveColumns, handleSaveColumnView, handleLoadColumnView, handleDeleteColumnView, startResize,
  // handleColumnDragStart/Over/Leave/Drop/End, and the localStorage column order effect
  // are now provided by useCandidatesColumnConfig above.

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
