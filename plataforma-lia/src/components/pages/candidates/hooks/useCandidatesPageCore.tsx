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
      const nav = JSON.parse(raw) as { candidateId?: string; candidateName?: string }
      if (nav.candidateId) {
        const found = candidates.find(c => c.id === nav.candidateId)
        if (found) {
          setPreviewCandidate(found)
          setShowCandidatePreview(true)
        }
      }
    } catch {
    }
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

  // Load candidate lists for modal
  useEffect(() => {
    const loadCandidateLists = async () => {
      try {
        const response = await liaApi.getCandidateLists({ limit: 50 })
        if (response?.items) {
          setCandidateListsForModal(response.items.map(list => ({
            id: list.id,
            name: list.name,
            color: list.color
          })))
        }
      } catch {
        setCandidateListsForModal([])
      }
    }
    loadCandidateLists()
  }, [])

  // Load viewed candidates on mount
  useEffect(() => {
    const loadViewedCandidates = async () => {
      try {
        const response = await fetch('/api/backend-proxy/candidates/viewed')
        if (response.ok) {
          const data = await response.json()
          if (data.candidate_ids) {
            setViewedCandidateIds(new Set(data.candidate_ids))
          }
        }
      } catch (error) {
      }
    }
    loadViewedCandidates()
  }, [])
  
  // Auto-populate tableFilters from search entities when a search is performed
  // Uses searchExecutionId to trigger on each new search execution
  // Clears fields explicitly when not present in the new search to always reflect current search criteria
  useEffect(() => {
    if (searchExecutionId > 0) {
      if (lastSearchEntities) {
        const yearsExp = lastSearchEntities.years_experience
        const parsedYears = typeof yearsExp === 'string' ? parseInt(yearsExp, 10) : yearsExp
        setTableFilters(prev => ({
          ...prev,
          locations: lastSearchEntities.location ? [lastSearchEntities.location] : [],
          jobTitles: lastSearchEntities.job_title ? [lastSearchEntities.job_title] : [],
          skills: lastSearchEntities.skills?.length ? lastSearchEntities.skills : [],
          industries: lastSearchEntities.industry ? [lastSearchEntities.industry] : [],
          seniorityLevels: lastSearchEntities.seniority ? [lastSearchEntities.seniority] : [],
          minExperience: (parsedYears !== undefined && !isNaN(parsedYears)) ? parsedYears : undefined,
          companies: lastSearchEntities.company ? [lastSearchEntities.company] : []
        }))
      } else {
        // No entities parsed - clear all auto-populated fields
        setTableFilters(prev => ({
          ...prev,
          locations: [],
          jobTitles: [],
          skills: [],
          industries: [],
          seniorityLevels: [],
          minExperience: undefined,
          companies: []
        }))
      }
    }
  }, [searchExecutionId])
  
  // Mark candidate as viewed when clicked
  const markCandidateAsViewed = async (candidateId: string, source: string = 'profile') => {
    try {
      await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source })
      })
      setViewedCandidateIds(prev => new Set([...prev, candidateId]))
    } catch (error) {
    }
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
  
  // 🎯 Auto-expandir LIA sidebar quando há candidatos selecionados
  // Respeita intent manual do usuário (userCollapsedLIA)
  // IMPORTANTE: Não fecha o LIA automaticamente - usuário controla manualmente
  // Também adiciona mensagem ao chat quando candidatos são selecionados
  const prevSelectedCountRef = useRef(0)
  useEffect(() => {
    const currentCount = selectedCandidatesForBatch.size
    const prevCount = prevSelectedCountRef.current
    
    if (currentCount > 0 && !userCollapsedLIA) {
      setShowExpandedLIA(true)
      // REMOVIDO: setShowAdvancedSearch(true) - modal só abre via botão Filtro ou prompt expandido
      
      // Adicionar mensagem ao chat quando seleção muda
      if (currentCount !== prevCount && currentCount > 0) {
        const selectedCandidateNames = candidates
          .filter(c => selectedCandidatesForBatch.has(c.id))
          .slice(0, 3)
          .map(c => c.name)
        
        const namesPreview = selectedCandidateNames.join(', ') + (currentCount > 3 ? ` e mais ${currentCount - 3}` : '')
        
        const liaMessage: ChatMessage = {
          id: `lia-selection-${Date.now()}`,
          type: 'lia',
          content: `Você selecionou **${currentCount} candidato${currentCount > 1 ? 's' : ''}**: ${namesPreview}.\n\nPosso analisar ${currentCount > 1 ? 'estes candidatos' : 'este candidato'} para você:\n\n• **Analisar potencial de crescimento**\n• **Definir tipo de perfil** (executor, estratégico, etc)\n• **Resumo executivo do perfil**\n• **Pontos a serem desenvolvidos**\n• **Tipos de vagas ideais para ${currentCount > 1 ? 'estes perfis' : 'este perfil'}**`,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, liaMessage])
      }
    }
    // REMOVIDO: Não fecha mais o LIA automaticamente quando currentCount === 0
    // O LIA permanece aberto após busca - usuário fecha manualmente se quiser
    
    prevSelectedCountRef.current = currentCount
  }, [selectedCandidatesForBatch.size, userCollapsedLIA, candidates, selectedCandidatesForBatch])
  
  // Parsing de entidades do liaPromptValue com debounce
  useEffect(() => {
    if (!liaPromptValue.trim()) {
      setLiaPromptEntities({
        job_title: undefined,
        location: undefined,
        skills: [],
        years_experience: undefined,
        industry: undefined,
        seniority: undefined,
        company: undefined
      })
      setLiaSuggestions([])
      return
    }
    
    const debounceTimer = setTimeout(async () => {
      setLiaIsParsingEntities(true)
      try {
        const response = await fetch('/api/backend-proxy/search/parse-query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: liaPromptValue })
        })
        if (response.ok) {
          const data = await response.json()
          const entities = data.entities || data
          setLiaPromptEntities({
            job_title: entities.job_title || undefined,
            location: entities.location || undefined,
            skills: entities.skills || [],
            years_experience: entities.years_experience || undefined,
            industry: entities.industry || undefined,
            seniority: entities.seniority || undefined,
            company: entities.company || undefined
          })
          // Store suggestions from backend response
          if (data.suggestions && Array.isArray(data.suggestions)) {
            setLiaSuggestions(data.suggestions)
          } else {
            setLiaSuggestions([])
          }
        }
      } catch (error) {
      } finally {
        setLiaIsParsingEntities(false)
      }
    }, 500)
    
    return () => clearTimeout(debounceTimer)
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

  // ✨ Função para limpar filtro cross-tab
  const clearCrossTabFilter = () => {
    setCrossTabFilter(null)
    setShowCrossTabBanner(false)
    setSearchTerm("")
    setQuickFilters(new Set())
    // Limpar URL params
    window.history.replaceState({}, '', window.location.pathname)
  }

  // Estados dos modais
  const [showBatchApproval, setShowBatchApproval] = useState(false)
  const [showContactModal, setShowContactModal] = useState(false)
  const [contactModalAction, setContactModalAction] = useState<'general' | 'wsi_screening' | 'interview_invite'>('general')
  const [contactModalCandidate, setContactModalCandidate] = useState<Record<string, unknown> | null>(null)
  const [showScheduleModal, setShowScheduleModal] = useState(false)
  
  // Unified Communication Modal State
  const [unifiedModalOpen, setUnifiedModalOpen] = useState(false)
  const [unifiedModalType, setUnifiedModalType] = useState<CommunicationType>('email')
  const [unifiedModalCandidate, setUnifiedModalCandidate] = useState<Candidate | null>(null)
  const [showQuickViewModal, setShowQuickViewModal] = useState(false)
  const [showComparisonModal, setShowComparisonModal] = useState(false)
  const [selectedCandidateForAction, setSelectedCandidateForAction] = useState<Candidate | null>(null)
  const [showAddCandidateModal, setShowAddCandidateModal] = useState(false)
  const [preSelectedListForModal, setPreSelectedListForModal] = useState<{ id: string; name: string } | null>(null)
  // WSI Screening States
  const [showWSITextModal, setShowWSITextModal] = useState(false)
  const [showWSIVoiceModal, setShowWSIVoiceModal] = useState(false)
  const [wsiCandidateForScreening, setWsiCandidateForScreening] = useState<Candidate | null>(null)
  
  // WSI Triagem Invite Modal State
  const [showWSIInviteModal, setShowWSIInviteModal] = useState(false)
  const [wsiInviteCandidate, setWsiInviteCandidate] = useState<Candidate | null>(null)
  
  // Rubric Evaluation Modal State (LIA Analysis)
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [rubricCandidate, setRubricCandidate] = useState<Candidate | null>(null)
  const [rubricEvaluationData, setRubricEvaluationData] = useState<Record<string, unknown> | null>(null)

  // Email Modal States
  const [showSendEmailModal, setShowSendEmailModal] = useState(false)
  const [emailCandidateSelected, setEmailCandidateSelected] = useState<Candidate | null>(null)

  // CV Parser Modal States (mantido para CVPreview legado)
  const [showCVPreviewModal, setShowCVPreviewModal] = useState(false)
  const [parsedCVData, setParsedCVData] = useState<ParsedCVResponse | null>(null)

  // Bulk Actions States
  const [bulkJobVacancies, setBulkJobVacancies] = useState<JobVacancy[]>([])
  const [bulkEmailTemplates, setBulkEmailTemplates] = useState<EmailTemplate[]>([])

  // Candidate Lists Modal States
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [addToListCandidateIds, setAddToListCandidateIds] = useState<string[]>([])
  const [addToListCandidateNames, setAddToListCandidateNames] = useState<string[]>([])
  const [showAddListToVacanciesModal, setShowAddListToVacanciesModal] = useState(false)
  const [selectedListForVacancies, setSelectedListForVacancies] = useState<{ id: string; name: string; candidateCount: number } | null>(null)
  
  // Add to Vacancy Modal State
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  
  // Share Search Modal State
  const [showShareSearchModal, setShowShareSearchModal] = useState(false)
  const [shareSearchCandidates, setShareSearchCandidates] = useState<Array<{ id: string; name: string; email?: string; avatar_url?: string; current_title?: string; linkedin_url?: string }>>([])
  const [shareSearchTitle, setShareSearchTitle] = useState('')

  // Pearch AI Credit System States
  const [showCreditConfirmation, setShowCreditConfirmation] = useState(false)
  const [pendingSearchRequest, setPendingSearchRequest] = useState<{
    query: string
    entities?: ParsedEntities
    mode?: SearchMode
    metadata?: SearchMetadata
  } | null>(null)
  const [creditEstimate, setCreditEstimate] = useState<CreditEstimate | null>(null)
  const [searchThreadId, setSearchThreadId] = useState<string | undefined>(undefined)
  
  // Source Change & Contact Filter Credit Confirmation Modals
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [showContactFilterModal, setShowContactFilterModal] = useState(false)
  const [pendingContactFilter, setPendingContactFilter] = useState<'email' | 'phone' | null>(null)

  // ── Reveal Contact — extraído para useRevealContact ──
  const revealContactHook = useRevealContact({ setCreditsRemaining: (fn) => setCreditsRemaining(typeof fn === 'function' ? fn(creditsRemaining) : fn), toast })
  const { showRevealModal, revealCandidate, revealType, revealedContacts, isRevealing } = revealContactHook.state
  const { setShowRevealModal, setRevealCandidate, setRevealType, setRevealedContacts, openRevealModal, handleRevealContact } = revealContactHook.actions
  
  // Estado para linhas expandidas (quebra de linha do cargo)
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  
  // Estado para salvar candidatos Pearch na base local
  const [isSavingToBase, setIsSavingToBase] = useState(false)
  
  // Estado para importar candidatos Pearch ao adicionar à lista
  const [isAddingToList, setIsAddingToList] = useState(false)
  
  // Estado para modal de aviso de candidatos Pearch não salvos
  const [showUnsavedWarningModal, setShowUnsavedWarningModal] = useState(false)
  const [pendingTabChange, setPendingTabChange] = useState<string | null>(null)
  
  // Calcular candidatos Pearch não salvos nos resultados atuais
  const unsavedPearchCandidates = candidates.filter(c => c.source === 'pearch')
  const hasUnsavedPearchCandidates = unsavedPearchCandidates.length > 0 && showSearchResults

  // Load job vacancies and email templates for bulk actions
  useEffect(() => {
    liaApi.listJobVacancies()
      .then(response => {
        if (response.items) {
          setBulkJobVacancies(response.items.filter((j: JobVacancy) => j.status === 'open' || j.status === 'draft'))
        }
      })
      .catch(() => {})

    liaApi.listEmailTemplates(undefined, true)
      .then(response => {
        if (response.items) {
          setBulkEmailTemplates(response.items)
        }
      })
      .catch(() => {})
  }, [])

  // openRevealModal and handleRevealContact are now provided by useRevealContact above

  // Callback for refreshing candidates after bulk actions
  const handleBulkActionComplete = () => {
    setIsLoading(true)
    liaApi.listCandidates(undefined, undefined, 0, 100)
      .then(response => {
        if (response.items && response.items.length > 0) {
          const backendCandidates: Candidate[] = response.items.map((c: CandidateLocal) => ({
            id: c.id,
            candidateId: c.id.substring(0, 5).toUpperCase(),
            name: c.name || 'Sem nome',
            email: c.email || '',
            phone: c.phone || '',
            position: c.current_title || 'Não informado',
            location: [c.location_city, c.location_state].filter(Boolean).join(', ') || 'Não informado',
            workModel: (c.work_model_preference || 'remoto') as 'remoto' | 'híbrido' | 'presencial',
            score: c.lia_score || 75,
            status: (c.status || 'active') as 'active' | 'prospect' | 'interview' | 'hired',
            currentSalary: c.desired_salary_min ? `R$ ${c.desired_salary_min.toLocaleString('pt-BR')}` : undefined,
            expectedSalary: c.desired_salary_max ? `R$ ${c.desired_salary_max.toLocaleString('pt-BR')}` : undefined,
            contractType: (c.contract_type_preference?.toUpperCase() || 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
            tags: c.tags || [],
            linkedin: c.linkedin_url || '',
            skills: c.technical_skills || [],
            experience: c.years_of_experience || 0,
            education: c.education || c.educations || [],
            notes: c.notes,
            avatar: c.avatar_url || (c as Record<string, unknown>).picture_url,
            liaAnalysis: {
              score: c.lia_score || 75,
              strengths: c.lia_insights?.strengths || ['Perfil técnico sólido'],
              concerns: c.lia_insights?.concerns || [],
              recommendation: c.lia_insights?.recommendation || 'Avaliar com atenção'
            },
            source: 'local',
            has_email: true,
            has_phone: true
          }))
          setCandidates(backendCandidates)
        }
        setIsLoading(false)
      })
      .catch(error => {
        setIsLoading(false)
      })
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

  // Função principal de busca - Integra Local + Pearch AI
  const executeSearch = async (
    query: string,
    entities?: ParsedEntities,
    mode?: SearchMode,
    metadata?: SearchMetadata,
    usePearch: boolean = false
  ) => {
    setIsLoading(true)
    setIsSearchActive(true)
    
    // Reset searchResults com estado de carregamento
    setSearchResults(prev => ({ 
      ...prev, 
      isLoading: true, 
      query: query 
    }))
    
    try {
      let mappedCandidates: Candidate[] = []
      let totalCount = 0
      let creditsUsed: number | undefined
      
      const shouldUsePearch = usePearch || searchSource === 'global'
      const shouldUseHybrid = searchSource === 'hybrid'
      
      let localCount = 0
      let pearchCount = 0
      
      // ============== MODO SIMILAR - Busca por perfil similar ==============
      if (mode === 'similar' && metadata) {
        const similarUrl = metadata.similarProfileUrl || (metadata.similarProfileUrls?.[0])
        
        if (similarUrl) {
          const response = await fetch('/api/backend-proxy/search/candidates/similar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              linkedin_url: similarUrl,
              limit: 20,
              search_pearch: shouldUsePearch || shouldUseHybrid,
              pearch_type: pearchSearchOptions.searchType
            })
          })
          
          if (response.ok) {
            const data = await response.json()
            totalCount = data.total_count || 0
            localCount = data.local_count || 0
            pearchCount = data.pearch_count || 0
            creditsUsed = data.credits_used
            
            if (data.credits_remaining !== undefined) {
              setCreditsRemaining(data.credits_remaining)
            }
            
            if (data.candidates && data.candidates.length > 0) {
              mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
            }
          } else {
          }
        }
      }
      // ============== MODO JD - Busca por Job Description ==============
      else if (mode === 'jd' && metadata?.jobDescription) {
        const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            job_description: metadata.jobDescription,
            limit: 20,
            search_pearch: shouldUsePearch || shouldUseHybrid,
            pearch_type: pearchSearchOptions.searchType
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          
          if (data.credits_remaining !== undefined) {
            setCreditsRemaining(data.credits_remaining)
          }
          
          if (data.candidates && data.candidates.length > 0) {
            mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
          }
        } else {
        }
      }
      // ============== MODO ARCHETYPES - Busca por arquétipo ==============
      else if (mode === 'archetypes' && metadata?.archetypeVacancyId) {
        const archetypeId = metadata.archetypeVacancyId
        const response = await fetch(`/api/backend-proxy/search/archetypes/${archetypeId}/search`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            limit: 20,
            search_pearch: shouldUsePearch || shouldUseHybrid,
            pearch_type: pearchSearchOptions.searchType
          })
        })
        
        if (response.ok) {
          const data = await response.json()
          totalCount = data.total_count || 0
          localCount = data.local_count || 0
          pearchCount = data.pearch_count || 0
          creditsUsed = data.credits_used
          
          if (data.credits_remaining !== undefined) {
            setCreditsRemaining(data.credits_remaining)
          }
          
          if (data.candidates && data.candidates.length > 0) {
            mappedCandidates = data.candidates.map((c: Record<string, unknown>) => mapCandidateToInternal(c))
          }
        } else {
        }
      }
      // ============== MODO NATURAL/BOOLEAN/FILTROS - Busca padrão ==============
      else if (shouldUsePearch || shouldUseHybrid) {
        // Converter entities para SearchSpec para filtros avançados da Pearch
        const searchSpec = entities ? {
          location: entities.location,
          job_title: entities.job_title,
          seniority: entities.seniority,
          years_experience: entities.years_experience,
          skills: entities.skills || [],
          industry: entities.industry,
          company: entities.company
        } : undefined
        
        // Busca via Pearch AI (apenas Pearch ou híbrida)
        const searchResponse = await searchCandidatesHybrid({
          query,
          thread_id: searchThreadId,
          search_spec: searchSpec,
          search_local: shouldUseHybrid,
          search_pearch: true,
          pearch_type: pearchSearchOptions.searchType,
          local_limit: shouldUseHybrid ? 20 : 1,
          pearch_limit: pearchSearchOptions.limit,
          show_emails: pearchSearchOptions.showEmails,
          show_phone_numbers: pearchSearchOptions.showPhoneNumbers,
          high_freshness: pearchSearchOptions.highFreshness,
          require_emails: pearchSearchOptions.requireEmails,
          require_phone_numbers: pearchSearchOptions.requirePhoneNumbers
        })
        
        // Salvar thread_id para refinamentos futuros
        if (searchResponse.thread_id) {
          setSearchThreadId(searchResponse.thread_id)
        }
        
        creditsUsed = searchResponse.credits_used
        totalCount = searchResponse.total_count || 0
        localCount = searchResponse.local_count || 0
        pearchCount = searchResponse.pearch_count || 0
        
        // Atualiza saldo de créditos se retornado na resposta
        if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
          setCreditsRemaining(searchResponse.credits_remaining)
        }
        
        // Mapear candidatos do formato Pearch/SearchResponse para formato interno
        // A API já define source='local' ou source='pearch' em CandidateSearchResultDTO
        if (searchResponse.candidates && searchResponse.candidates.length > 0) {
          mappedCandidates = searchResponse.candidates.map((c) => {
            // A API define source corretamente como 'local' ou 'pearch'
            // Usamos o source da API diretamente, com fallback para 'pearch' se indefinido
            const candidateSource = c.source || 'pearch'
            
            return {
              id: c.id || `pearch-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              candidateId: c.id?.substring(0, 8).toUpperCase() || 'PEARCH',
              name: c.name || 'Nome não disponível',
              email: c.email || '',
              phone: c.phone || '',
              mobile_phone: c.phone,
              current_title: c.headline || c.current_title || '',
              current_company: c.current_company || '',
              current_salary: undefined,
              desired_salary_min: undefined,
              desired_salary_max: undefined,
              location: c.location || '',
              location_city: c.location?.split(',')[0]?.trim(),
              location_state: c.location?.split(',')[1]?.trim(),
              linkedin_url: c.linkedin_url,
              avatar_url: c.avatar_url || c.picture_url,
              technical_skills: c.skills || [],
              skills: c.skills || [],
              seniority_level: c.seniority_level,
              years_of_experience: c.years_experience || c.total_experience_years,
              experience: c.years_experience || c.total_experience_years || 0,
              position: c.headline || c.current_title || '',
              monthlySalary: 0,
              workModel: 'remoto' as const,
              score: c.match_score ? Math.round(c.match_score * 25) : 75,
              contractType: 'CLT' as const,
              linkedin: c.linkedin_url || '',
              avatar: c.avatar_url,
              // Mapeamento de experiências profissionais da Pearch
              experiences: c.experiences || c.work_history || [],
              workHistory: (c.experiences || c.work_history || []).map((exp: Record<string, unknown>) => ({
                company: exp.company_info?.name || exp.company || '',
                title: exp.company_roles?.[0]?.title || exp.title || '',
                startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                duration: exp.duration || '',
                location: exp.company_info?.location || exp.location || '',
                description: exp.company_roles?.[0]?.description || exp.description || ''
              })),
              // Mapeamento de formação acadêmica da Pearch
              education: (c.education || c.educations || []).map((edu: Record<string, unknown>) => ({
                school: edu.school || '',
                degree: edu.degree || '',
                field_of_study: edu.field_of_study || '',
                fieldOfStudy: edu.field_of_study || '',
                startDate: edu.start_date || '',
                endDate: edu.end_date || ''
              })),
              liaAnalysis: {
                score: c.match_score ? Math.round(c.match_score * 25) : 75,
                strengths: c.match_reasoning ? [c.match_reasoning] : [],
                concerns: [],
                recommendation: c.match_reasoning || ''
              },
              source: candidateSource,
              pearch_profile_id: c.pearch_profile_id,
              has_email: c.has_email ?? true,
              has_phone: c.has_phone ?? true,
              is_opentowork: c.is_opentowork,
              is_decision_maker: c.is_decision_maker,
              is_top_universities: c.is_top_universities,
              is_startup: c.is_startup || c.company_info?.is_startup,
              expertise: c.expertise,
              outreach_message: c.outreach_message
            }
          })
        }
      } else {
        // Busca apenas local via liaApi (gratuita)
        const response = await liaApi.listCandidates(query, undefined, 0, 50)
        
        if (response.items && response.items.length > 0) {
          // Filtrar baseado na query para busca local
          const searchLower = query.toLowerCase()
          const filtered = response.items.filter((c: CandidateLocal) => {
            return (
              c.name?.toLowerCase().includes(searchLower) ||
              c.current_title?.toLowerCase().includes(searchLower) ||
              c.current_company?.toLowerCase().includes(searchLower) ||
              c.location_city?.toLowerCase().includes(searchLower) ||
              c.location_state?.toLowerCase().includes(searchLower) ||
              c.technical_skills?.some((s: string) => s.toLowerCase().includes(searchLower))
            )
          })
          
          totalCount = filtered.length
          localCount = filtered.length
          pearchCount = 0
          
          // Mapear candidatos locais para formato interno
          mappedCandidates = filtered.map((c: CandidateLocal) => ({
            id: c.id,
            candidateId: c.id.substring(0, 8).toUpperCase(),
            name: c.name || 'Sem nome',
            email: c.email || '',
            phone: c.phone || '',
            mobile_phone: c.mobile_phone,
            current_title: c.current_title || '',
            current_company: c.current_company || '',
            current_salary: c.current_salary,
            desired_salary_min: c.desired_salary_min,
            desired_salary_max: c.desired_salary_max,
            location: [c.location_city, c.location_state].filter(Boolean).join(', '),
            location_city: c.location_city,
            location_state: c.location_state,
            linkedin_url: c.linkedin_url,
            avatar_url: c.avatar_url || c.picture_url,
            technical_skills: c.technical_skills || [],
            skills: c.technical_skills || [],
            seniority_level: c.seniority_level,
            years_of_experience: c.years_of_experience,
            experience: c.years_of_experience || 0,
            position: c.current_title || '',
            monthlySalary: c.current_salary || 0,
            workModel: (c.work_model_preference || 'remoto') as 'remoto' | 'híbrido' | 'presencial',
            score: c.lia_score || 75,
            contractType: (c.contract_type_preference?.toUpperCase() || 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
            linkedin: c.linkedin_url || '',
            education: c.education || c.educations || [],
            avatar: c.avatar_url || (c as Record<string, unknown>).picture_url,
            liaAnalysis: {
              score: c.lia_score || 75,
              strengths: c.lia_insights?.strengths || [],
              concerns: c.lia_insights?.concerns || [],
              recommendation: c.lia_insights?.recommendation || ''
            },
            source: 'local',
            tags: c.tags || [],
            notes: c.notes,
            has_email: true,
            has_phone: true,
            is_opentowork: c.is_opentowork,
            is_decision_maker: c.is_decision_maker,
            is_top_universities: c.is_top_universities,
            is_startup: c.is_startup || c.company_info?.is_startup,
            expertise: c.expertise,
            outreach_message: c.outreach_message
          }))
        }
      }
      
      // Marcar que a busca foi realizada
      setHasSearched(true)
      
      // Salvar entities, metadata e usePearch para uso na expansão global e re-execução de busca
      // Sempre incrementa searchExecutionId para resetar filtros, mesmo quando entities é null
      setLastSearchEntities(entities || null)
      setLastSearchMetadata(metadata)
      setLastSearchUsedPearch(usePearch || searchSource === 'global' || searchSource === 'hybrid')
      setSearchExecutionId(prev => prev + 1)
      
      // Determinar e atualizar a fonte de busca atual
      const shouldUsePearchForSource = usePearch || searchSource === 'global'
      const shouldUseHybridForSource = searchSource === 'hybrid'
      if (shouldUsePearchForSource) {
        setCurrentSearchSource('global')
      } else if (shouldUseHybridForSource) {
        setCurrentSearchSource('hybrid')
      } else {
        setCurrentSearchSource('local')
      }
      
      // Salvar no histórico
      talentFunnel.addToHistory({
        query,
        mode: (mode || 'natural') as string,
        source: searchSource,
        entities,
        metadata,
        resultsCount: mappedCandidates.length
      })
      
      // Separar candidatos locais e globais
      const localCandidates = mappedCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return !isGlobalSource(c.source, hasPearchId)
      })
      const globalCandidates = mappedCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return isGlobalSource(c.source, hasPearchId)
      })
      
      // Determinar se devemos mostrar candidatos globais automaticamente
      // Quando busca é global ou híbrida, mostrar automaticamente
      // Quando busca é local, manter pendente para usuário ativar
      const shouldAutoShowGlobal = shouldUsePearch || shouldUseHybrid
      
      // IMPORTANTE: Se busca é global/híbrida, todos os candidatos vão para a tabela
      // Se busca é apenas local, só os locais vão automaticamente
      const candidatesBeforeFilter = shouldAutoShowGlobal 
        ? mappedCandidates // Todos (locais + globais)
        : localCandidates  // Apenas locais
      
      // Apply hide viewed candidates filter if enabled
      const candidatesForTable = hideViewedCandidates.filterCandidates(candidatesBeforeFilter)
      
      // Calculate how many were hidden from LOCAL vs GLOBAL sources separately
      const hiddenCandidates = candidatesBeforeFilter.filter(c => !candidatesForTable.some(visible => visible.id === c.id))
      const hiddenLocalCount = hiddenCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return !isGlobalSource(c.source, hasPearchId)
      }).length
      const hiddenGlobalCount = hiddenCandidates.filter(c => {
        const hasPearchId = Boolean(c.pearch_profile_id)
        return isGlobalSource(c.source, hasPearchId)
      }).length
      const totalHiddenCount = hiddenLocalCount + hiddenGlobalCount
      
      setCandidates(candidatesForTable)
      setHasSearchResults(true)
      // Adjust counts to reflect filtered results - subtract hidden from correct source
      const baseLocalCount = localCount > 0 ? localCount : localCandidates.length
      const baseGlobalCount = pearchCount > 0 ? pearchCount : globalCandidates.length
      setSearchResultsCount((totalCount || mappedCandidates.length) - totalHiddenCount)
      setLocalResultsCount(Math.max(0, baseLocalCount - hiddenLocalCount))
      setPearchResultsCount(Math.max(0, baseGlobalCount - hiddenGlobalCount))
      setCreditsUsedInSearch(creditsUsed || 0)
      setShowSearchResults(true)
      setDisplayedResultsCount(10)
      
      // Popular o searchResults para exibir resumo no painel LIA
      // IMPORTANTE: Preservar globalDismissed entre buscas
      setSearchResults(prev => ({
        local: localCandidates,
        global: globalCandidates,
        localCount: localCount > 0 ? localCount : localCandidates.length,
        globalCount: pearchCount > 0 ? pearchCount : globalCandidates.length,
        query: query,
        isLoading: false,
        showGlobalResults: shouldAutoShowGlobal, // Auto-mostrar quando busca global/híbrida
        globalDismissed: prev.globalDismissed // Preservar estado de dismiss entre buscas
      }))
      
      // IMPORTANTE: Expandir prompt LIA automaticamente após busca concluída
      setShowExpandedLIA(true)
      setUserCollapsedLIA(false) // Reset para permitir auto-expansão
      
      // Detectar candidatos internacionais e sugerir filtro de localização
      // APENAS se: busca foi puramente local (não híbrida nem Pearch) e há resultados globais pendentes
      // Não mostrar se o usuário optou por busca global ou híbrida
      const shouldShowLocationTip = !usePearch && !shouldUsePearch && !shouldUseHybrid && globalCandidates.length > 0
      
      if (shouldShowLocationTip) {
        // Verificar se a busca não especificou localização brasileira
        const hasLocationInQuery = /brasil|brazil|são paulo|sp\b|rio|rj\b|minas|mg\b|curitiba|porto alegre|belo horizonte|recife|salvador|fortaleza|brasília/i.test(query)
        
        // Detectar se há candidatos claramente internacionais (países fora do Brasil)
        const internationalCountries = [
          'india', 'united states', 'usa', 'uk', 'united kingdom', 'canada', 'germany',
          'france', 'spain', 'portugal', 'australia', 'netherlands', 'italy', 'mexico',
          'argentina', 'colombia', 'chile', 'peru', 'philippines', 'pakistan', 'nigeria'
        ]
        
        const internationalCandidates = globalCandidates.filter(c => {
          const location = (c.location || c.location_city || '').toLowerCase()
          return internationalCountries.some(country => location.includes(country))
        })
        
        // Só mostrar dica se há candidatos claramente internacionais e query não especificou Brasil
        if (internationalCandidates.length >= 3 && !hasLocationInQuery) {
          const liaMessage: ChatMessage = {
            id: `lia-location-tip-${Date.now()}`,
            type: 'lia',
            content: `💡 **Dica de Localização**\n\nEncontrei candidatos de outros países nos resultados globais.\n\nSe você busca apenas profissionais no **Brasil**, pode refinar a busca adicionando a localização, por exemplo:\n\n• "*${query} em São Paulo*"\n• "*${query} Brasil*"\n\nOu use os **filtros de localização** no painel de busca avançada.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, liaMessage])
        }
      }
      
      // Salvar a query bem-sucedida para uso no modal de arquétipo
      setLastSuccessfulQuery(query)
      
      // Mostrar opção de expandir busca global se só buscou local
      if (!shouldUsePearch && !shouldUseHybrid) {
        setShowExpandGlobalOption(true)
      } else {
        setShowExpandGlobalOption(false)
      }
      
      // Log de créditos se usou Pearch
      if (creditsUsed) {
      }
      
      // 🎯 Chamar análise proativa após busca com resultados
      if (mappedCandidates.length > 0) {
        try {
          const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query,
              candidates: mappedCandidates.slice(0, 50).map(c => ({
                id: c.id,
                name: c.name,
                current_title: c.current_title || c.position,
                current_company: c.current_company,
                location: c.location || c.location_city,
                skills: c.skills || c.technical_skills,
                years_experience: c.experience || c.years_of_experience,
                lia_score: c.liaAnalysis?.score || c.score,
                seniority_level: c.seniority_level,
                work_model: c.workModel || c.work_model_preference,
                email: c.email,
                phone: c.phone || c.mobile_phone,
                linkedin_url: c.linkedin_url,
                source: c.source
              })),
              local_count: localCount,
              global_count: pearchCount
            })
          })
          
          if (analyzeResponse.ok) {
            const analyticsData: SearchAnalytics = await analyzeResponse.json()
            
            // Inserir card de insights proativos no chat
            const insightMessage: ChatMessage = {
              id: `proactive-insight-${Date.now()}`,
              type: 'proactive_insight',
              content: '',
              timestamp: new Date(),
              analytics: analyticsData
            }
            setChatMessages(prev => [...prev, insightMessage])
          }
        } catch (analyzeError) {
        }
      }
    } catch (error) {
      // IMPORTANTE: Reset searchResults.isLoading em caso de erro
      setSearchResults(prev => ({
        ...prev,
        isLoading: false,
        query: '' // Limpar query para não mostrar o card de loading sem resultado
      }))
    } finally {
      setIsLoading(false)
      setIsSearchActive(false)
    }
  }

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
      advancedFilters,
      timestamp: new Date().toISOString()
    }

    // Armazenar busca
    sessionStorage.setItem('current-search-data', JSON.stringify(searchData))

    // Navegar para aba saved-searches
    setActiveTab('saved-searches')

    toast({
      title: "Busca salva",
      description: `${sortedCandidates.length} candidatos encontrados`,
      duration: 4000
    })
  }

  // Filtros e ordenação
  const filteredCandidates = candidates.filter(candidate => {
    // ✨ Filtro cross-tab (empresa específica)
    if (crossTabFilter?.type === 'company') {
      const targetCompany = crossTabFilter.company || crossTabFilter.companies?.[0]
      if (targetCompany) {
        const candidateCompany = candidate.workHistory?.[0]?.company || ''
        if (!candidateCompany.toLowerCase().includes(targetCompany.toLowerCase())) {
          return false
        }
      }
    }

    // Filtro de busca textual - NÃO aplica se já temos resultados de busca IA
    // (os candidatos já foram filtrados pelo backend)
    if (searchTerm && !hasSearchResults && !searchTerm.startsWith('empresa:') && !searchTerm.startsWith('empresas:')) {
      const search = searchTerm.toLowerCase()
      const matches =
        candidate.name.toLowerCase().includes(search) ||
        candidate.position.toLowerCase().includes(search) ||
        (candidate.candidateId && candidate.candidateId.toLowerCase().includes(search)) ||
        candidate.skills.some(skill => skill.toLowerCase().includes(search))
      if (!matches) return false
    }

    // Filtro de busca por empresa (formato: empresa:"Nome")
    if (searchTerm.startsWith('empresa:"') || searchTerm.startsWith('empresas:')) {
      const companyMatch = searchTerm.match(/empresa:"([^"]+)"/) || searchTerm.match(/empresas:(.+)/)
      if (companyMatch) {
        const searchCompanies = companyMatch[1].split(',').map(c => c.trim())
        const candidateCompany = candidate.workHistory?.[0]?.company || ''
        if (!searchCompanies.some(company =>
          candidateCompany.toLowerCase().includes(company.toLowerCase())
        )) {
          return false
        }
      }
    }

    if (quickFilters.size > 0) {
      const hasQuickFilter = Array.from(quickFilters).some(filter => {
        switch (filter) {
          case 'frontend':
            return candidate.skills.some(skill => ['React', 'Vue', 'Angular', 'JavaScript'].includes(skill))
          case 'backend':
            return candidate.skills.some(skill => ['Node.js', 'Python', 'Java', 'PHP'].includes(skill))
          case 'design':
            return candidate.skills.some(skill => ['Figma', 'Sketch', 'Adobe', 'Design'].includes(skill))
          case 'senior':
            return candidate.experience >= 5
          case 'remoto':
            return candidate.location.includes('Remoto') || candidate.location.includes('Remote')
          default:
            return true
        }
      })
      if (!hasQuickFilter) return false
    }

    // Filtros de coluna
    if (columnFilters.position.length > 0 && !columnFilters.position.includes(candidate.position)) {
      return false
    }

    if (columnFilters.company.length > 0) {
      const company = candidate.workHistory?.[0]?.company || ''
      if (!columnFilters.company.includes(company)) {
        return false
      }
    }

    if (columnFilters.location.length > 0 && !columnFilters.location.includes(candidate.location)) {
      return false
    }

    if (columnFilters.scoreRange.length > 0) {
      const score = candidate.liaAnalysis?.score || candidate.score
      let scoreRange: string
      if (score >= 90) scoreRange = '90-100%'
      else if (score >= 80) scoreRange = '80-89%'
      else if (score >= 70) scoreRange = '70-79%'
      else scoreRange = '60-69%'

      if (!columnFilters.scoreRange.includes(scoreRange)) {
        return false
      }
    }

    // Filtros de Big Five - só aplica se houver filtros ativos
    if (columnFilters.bigFive) {
      const hasActiveBigFiveFilters = Object.values(columnFilters.bigFive).some(v => v && v !== '')
      
      if (hasActiveBigFiveFilters) {
        const bigFive = candidate.bigFive
        if (!bigFive) return false // Se não tem dados de Big Five e há filtro ativo, não passa
        
        // Função para classificar score em nível
        const getLevel = (score: number) => {
          if (score >= 80) return 'alto'
          if (score >= 60) return 'medio'
          return 'baixo'
        }

        // Verificar cada dimensão filtrada
        for (const [dimension, filterLevel] of Object.entries(columnFilters.bigFive)) {
          if (filterLevel && filterLevel !== '') {
            const score = bigFive[dimension as keyof typeof bigFive]
            if (!score || getLevel(score) !== filterLevel) {
              return false
            }
          }
        }
      }
    }

    // Filtros avançados

    // Filtro por modelo de trabalho
    if (advancedFilters.work_models.length > 0) {
      const workModelFilters = advancedFilters.work_models.filter(filter =>
        ['remoto', 'híbrido', 'presencial'].includes(filter)
      )
      if (workModelFilters.length > 0 && !workModelFilters.includes(candidate.workModel)) {
        return false
      }
    }

    // Filtro por skills
    if (advancedFilters.skills.length > 0) {
      const hasSkill = advancedFilters.skills.some(skill =>
        candidate.skills.some(candidateSkill =>
          candidateSkill.toLowerCase().includes(skill.toLowerCase())
        )
      )
      if (!hasSkill) return false
    }

    // Filtro por empresa
    if (advancedFilters.companies.length > 0) {
      const candidateCompany = candidate.workHistory?.[0]?.company || ''
      const hasCompany = advancedFilters.companies.some(company =>
        candidateCompany.toLowerCase().includes(company.toLowerCase())
      )
      if (!hasCompany) return false
    }

    // Filtro por localização
    if (advancedFilters.locations.length > 0) {
      const hasLocation = advancedFilters.locations.some(location =>
        candidate.location.toLowerCase().includes(location.toLowerCase())
      )
      if (!hasLocation) return false
    }

    // Filtro por cargos
    if (advancedFilters.job_titles.length > 0) {
      const hasJobTitle = advancedFilters.job_titles.some(title =>
        candidate.position.toLowerCase().includes(title.toLowerCase())
      )
      if (!hasJobTitle) return false
    }

    // 🎯 Filtros da Tabela de Resultados (tableFilters) - Separado dos filtros de busca
    // Filtro por contato - Email
    if (tableFilters.hasEmail) {
      const hasEmail = !!(candidate.email || candidate.has_email)
      if (!hasEmail) return false
    }

    // Filtro por contato - Telefone
    if (tableFilters.hasPhone) {
      const hasPhone = !!(candidate.phone || candidate.mobile_phone || candidate.has_phone)
      if (!hasPhone) return false
    }

    // Filtro por contato - LinkedIn
    if (tableFilters.hasLinkedin) {
      const hasLinkedin = !!(candidate.linkedin_url || candidate.linkedin)
      if (!hasLinkedin) return false
    }

    // Filtro por modelo remoto
    if (tableFilters.remoteOnly) {
      const isRemote = candidate.workModel === 'remoto' || 
                       candidate.is_remote || 
                       candidate.location?.toLowerCase().includes('remoto')
      if (!isRemote) return false
    }

    // Filtro por experiência mínima
    if (tableFilters.minExperience !== undefined) {
      const experience = candidate.experience || candidate.years_of_experience || 0
      if (experience < tableFilters.minExperience) return false
    }

    // Filtro por experiência máxima
    if (tableFilters.maxExperience !== undefined) {
      const experience = candidate.experience || candidate.years_of_experience || 0
      if (experience > tableFilters.maxExperience) return false
    }

    // Filtro por score mínimo
    if (tableFilters.minScore !== undefined) {
      const score = candidate.liaAnalysis?.score || candidate.score || candidate.lia_score || 0
      if (score < tableFilters.minScore) return false
    }

    // Filtro por score máximo
    if (tableFilters.maxScore !== undefined) {
      const score = candidate.liaAnalysis?.score || candidate.score || candidate.lia_score || 0
      if (score > tableFilters.maxScore) return false
    }

    // Filtro por senioridade
    if (tableFilters.seniorityLevels.length > 0) {
      const level = candidate.seniority_level || ''
      const position = candidate.position || ''
      const matchesSeniority = tableFilters.seniorityLevels.some(filterLevel => 
        level.toLowerCase().includes(filterLevel.toLowerCase()) ||
        position.toLowerCase().includes(filterLevel.toLowerCase())
      )
      if (!matchesSeniority) return false
    }

    // Filtro por modelo de trabalho (tableFilters)
    if (tableFilters.workModels.length > 0) {
      if (!tableFilters.workModels.includes(candidate.workModel)) return false
    }

    // Filtro por tipo de contrato
    if (tableFilters.contractTypes.length > 0) {
      if (!tableFilters.contractTypes.includes(candidate.contractType)) return false
    }

    // Filtro por fonte
    if (tableFilters.sources.length > 0) {
      const source = candidate.source || ''
      const matchesSource = tableFilters.sources.some(filterSource =>
        source.toLowerCase().includes(filterSource.toLowerCase())
      )
      if (!matchesSource) return false
    }

    // Filtro por Github
    if (tableFilters.hasGithub) {
      const hasGithub = !!(candidate.github_url)
      if (!hasGithub) return false
    }

    // Filtro por Portfólio
    if (tableFilters.hasPortfolio) {
      const hasPortfolio = !!(candidate.portfolio_url)
      if (!hasPortfolio) return false
    }

    // Filtro por Soft Skills
    if (tableFilters.softSkills.length > 0) {
      const candidateSoftSkills = candidate.soft_skills || []
      const hasMatchingSoftSkill = tableFilters.softSkills.some(skill =>
        candidateSoftSkills.some(cs => cs.toLowerCase().includes(skill.toLowerCase()))
      )
      if (!hasMatchingSoftSkill) return false
    }

    // Filtro por Certificações
    if (tableFilters.certifications.length > 0) {
      const candidateCertifications = candidate.certifications || []
      const hasMatchingCertification = tableFilters.certifications.some(cert =>
        candidateCertifications.some(cc => cc.toLowerCase().includes(cert.toLowerCase()))
      )
      if (!hasMatchingCertification) return false
    }

    // Filtro por Aberto a mudar (willing_to_relocate)
    if (tableFilters.willingToRelocate !== null) {
      if (candidate.willing_to_relocate !== tableFilters.willingToRelocate) return false
    }

    // Filtro por Mobilidade
    if (tableFilters.mobility !== null) {
      if (candidate.mobility !== tableFilters.mobility) return false
    }

    // Filtro por Última Atualização (de)
    if (tableFilters.updatedAtFrom) {
      const updatedAt = candidate.updated_at ? new Date(candidate.updated_at) : null
      const fromDate = new Date(tableFilters.updatedAtFrom)
      if (!updatedAt || updatedAt < fromDate) return false
    }

    // Filtro por Última Atualização (até)
    if (tableFilters.updatedAtTo) {
      const updatedAt = candidate.updated_at ? new Date(candidate.updated_at) : null
      const toDate = new Date(tableFilters.updatedAtTo)
      if (!updatedAt || updatedAt > toDate) return false
    }

    // Filtro por Último Contato (de)
    if (tableFilters.lastContactedFrom) {
      const lastContacted = candidate.last_contacted_at ? new Date(candidate.last_contacted_at) : null
      const fromDate = new Date(tableFilters.lastContactedFrom)
      if (!lastContacted || lastContacted < fromDate) return false
    }

    // Filtro por Último Contato (até)
    if (tableFilters.lastContactedTo) {
      const lastContacted = candidate.last_contacted_at ? new Date(candidate.last_contacted_at) : null
      const toDate = new Date(tableFilters.lastContactedTo)
      if (!lastContacted || lastContacted > toDate) return false
    }

    return true
  })

  const sortedCandidates = [...filteredCandidates].sort((a, b) => {
    let aValue: unknown = a[sortBy as keyof Candidate]
    let bValue: unknown = b[sortBy as keyof Candidate]

    if (sortBy === 'score_lia') {
      aValue = a.liaAnalysis?.score || a.score
      bValue = b.liaAnalysis?.score || b.score
    }

    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase()
      bValue = bValue.toLowerCase()
    }

    if (sortOrder === 'asc') {
      return aValue > bValue ? 1 : -1
    } else {
      return aValue < bValue ? 1 : -1
    }
  })

  // 🚀 Função para paginação (como Gestão de Vagas)
  const getPaginatedCandidates = () => {
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return {
      candidates: sortedCandidates.slice(startIndex, endIndex),
      total: sortedCandidates.length,
      totalPages: Math.ceil(sortedCandidates.length / itemsPerPage)
    }
  }

  // Candidatos paginados para exibição
  const paginatedCandidates = getPaginatedCandidates().candidates

  const searchDisplayCandidates = React.useMemo(() => {
    let sorted = [...sortedCandidates]
    
    switch (searchSortBy) {
      case 'score_desc':
        sorted.sort((a, b) => (b.lia_score || b.score || 0) - (a.lia_score || a.score || 0))
        break
      case 'score_asc':
        sorted.sort((a, b) => (a.lia_score || a.score || 0) - (b.lia_score || b.score || 0))
        break
      case 'name_asc':
        sorted.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        break
      case 'name_desc':
        sorted.sort((a, b) => (b.name || '').localeCompare(a.name || ''))
        break
      case 'experience_desc':
        sorted.sort((a, b) => (b.experience || b.years_of_experience || 0) - (a.experience || a.years_of_experience || 0))
        break
      default:
        break
    }
    
    const feedbackKeys = Object.keys(searchFeedbacks)
    if (feedbackKeys.length > 0) {
      sorted.sort((a, b) => {
        const fbA = searchFeedbacks[a.id]
        const fbB = searchFeedbacks[b.id]
        const priorityA = fbA === 'like' ? 0 : fbA === 'dislike' ? 2 : 1
        const priorityB = fbB === 'like' ? 0 : fbB === 'dislike' ? 2 : 1
        return priorityA - priorityB
      })
    }
    
    return sorted.slice(0, displayedResultsCount)
  }, [sortedCandidates, searchSortBy, displayedResultsCount, searchFeedbacks])

  const visibleCandidates = showSearchResults ? searchDisplayCandidates : paginatedCandidates

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

  // Componente de Preview Lateral do Candidato
  const CandidatePreviewPanel = ({ candidate, onClose }: { candidate: Candidate; onClose: () => void }) => {
    const [activeTab, setActiveTab] = useState('overview')

    const tabs = [
      { id: 'overview', label: 'Visão Geral', icon: User },
      { id: 'experience', label: 'Experiência', icon: Briefcase },
      { id: 'skills', label: 'Habilidades', icon: Star },
      { id: 'contact', label: 'Contato', icon: MessageSquare }
    ]

    const renderTabContent = () => {
      switch (activeTab) {
        case 'overview':
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Informações Básicas</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Cargo:</span>
                    <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{candidate.position}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Localização:</span>
                    <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{candidate.location}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Status:</span>
                    <Badge className={`${
                      candidate.status === 'active' ? badgeStyles.success :
                      candidate.status === 'prospect' ? badgeStyles.info :
                      candidate.status === 'interview' ? badgeStyles.warning :
                      badgeStyles.default
                    } px-2 py-0.5`}>
                      {candidate.status === 'active' ? 'Ativo' :
                       candidate.status === 'prospect' ? 'Prospect' :
                       candidate.status === 'interview' ? 'Entrevista' : 'Contratado'}
                    </Badge>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Score LIA</h4>
                <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`${textStyles.label} dark:text-gray-200`}>Compatibilidade</span>
                    <span className="text-base font-bold text-gray-900 dark:text-gray-50">{formatScorePercent(candidate.score)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full"
                      style={{width: `${formatScore(candidate.score)}%`}}
                    ></div>
                  </div>
                  <div className={`${textStyles.description} mt-1 dark:text-gray-400`}>
                    Score baseado em habilidades, experiência e fit cultural
                  </div>
                  <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <LIAFeedbackWidget
                      candidateId={candidate.id}
                      liaScore={candidate.score}
                      liaRecommendation={candidate.liaAnalysis?.recommendation}
                      compact={false}
                      showLabel={true}
                    />
                  </div>
                </div>
              </div>
            </div>
          )

        case 'experience':
          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Experiência Profissional</h4>
                <div className="space-y-3">
                  <div className="border-l-4 border-wedo-green pl-3 py-2 bg-wedo-green/10 dark:bg-wedo-green/20 rounded-r-lg">
                    <div className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>
                      Senior Developer
                    </div>
                    <div className={`${textStyles.bodySmall} text-wedo-green dark:text-wedo-green`}>
                      Tech Corp • 2021 - Atual
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1 dark:text-gray-400`}>
                      Desenvolvimento de aplicações web com React, Node.js e PostgreSQL
                    </div>
                  </div>
                  <div className="border-l-4 border-gray-300 pl-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-r-lg">
                    <div className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>
                      Full Stack Developer
                    </div>
                    <div className={`${textStyles.bodySmall} dark:text-gray-500`}>
                      Startup XYZ • 2019 - 2021
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1 dark:text-gray-400`}>
                      Desenvolvimento fullstack e arquitetura de sistemas
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )

        case 'skills':
          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Habilidades Técnicas</h4>
                <div className="space-y-3">
                  <div>
                    <h5 className={`${textStyles.label} dark:text-gray-200 mb-1`}>Frontend</h5>
                    <div className="flex flex-wrap gap-1">
                      {['React', 'TypeScript', 'Next.js', 'Tailwind CSS'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Backend</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Node.js', 'Python', 'PostgreSQL', 'MongoDB'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-status-success/15 text-status-success border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Soft Skills</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Liderança', 'Comunicação', 'Trabalho em equipe', 'Resolução de problemas'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-wedo-purple/15 text-wedo-purple border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )

        case 'contact':
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Informações de Contato</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Mail className="w-4 h-4 text-gray-800" />
                    <div>
                      <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{candidate.email}</div>
                      <div className="text-xs text-gray-800">Email principal</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Phone className="w-4 h-4 text-gray-800" />
                    <div>
                      <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{candidate.phone}</div>
                      <div className="text-xs text-gray-800">Telefone/WhatsApp</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Linkedin className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">Ver perfil LinkedIn</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">Perfil profissional</div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Histórico de Interações</h4>
                <div className="space-y-2">
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                    📧 Email enviado há 2 dias
                  </div>
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                    📞 Ligação agendada para amanhã às 14h
                  </div>
                </div>
              </div>
            </div>
          )

        default:
          return null
      }
    }

    return (
      <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage
                  src={candidate.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(candidate.name)}&background=60BED1&color=fff&size=150`}
                  alt={candidate.name}
                />
                <AvatarFallback className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold">
                  {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-gray-950 dark:text-gray-50">{candidate.name}</h3>
                <p className="text-sm text-gray-800 dark:text-gray-500">{candidate.position}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="font-semibold text-gray-950 dark:text-gray-50">{formatScorePercent(candidate.score)}</div>
              <div className="text-gray-800">Score LIA</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="font-semibold text-gray-950 dark:text-gray-50 flex items-center justify-center gap-1">
                <Star className="w-3 h-3 text-status-warning" />
                4.8
              </div>
              <div className="text-gray-800">Avaliação</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <Badge className={`text-xs ${
                candidate.status === 'active' ? 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success' :
                candidate.status === 'prospect' ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' :
                candidate.status === 'interview' ? 'bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning' :
                'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
              }`}>
                {candidate.status === 'active' ? 'Ativo' :
                 candidate.status === 'prospect' ? 'Prospect' :
                 candidate.status === 'interview' ? 'Entrevista' : 'Contratado'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-0" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => handleTabChangeWithWarning(tab.id)}
                className={`flex-1 py-2 px-3 text-xs font-medium text-center border-b-2 ${
                  activeTab === tab.id
                    ? 'border-gray-950 text-gray-950 dark:border-gray-50 dark:text-gray-50'
                    : 'border-transparent text-gray-800 hover:text-gray-950 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <tab.icon className="w-3 h-3 mx-auto mb-1" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {renderTabContent()}
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
          <Button
            className="w-full gap-2 bg-gray-900 hover:bg-gray-800"
            onClick={() => {}}
          >
            <Calendar className="w-4 h-4" />
            Agendar Entrevista
          </Button>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <Mail className="w-4 h-4" />
              Email
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <LIAIcon size="sm" />
              LIA
            </Button>
          </div>
        </div>
      </div>
    )
  }

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

  // Handlers para filtros avançados
  const toggleAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }))
  }

  const removeAdvancedFilter = (category: string, value: string) => {
    setAdvancedFilters(prev => ({
      ...prev,
      [category]: prev[category].filter(v => v !== value)
    }))
  }

  const getActiveAdvancedFiltersCount = () => {
    return Object.values(advancedFilters).reduce((sum, filters) => sum + filters.length, 0)
  }

  const getActiveSearchFiltersCount = () => {
    let count = 0
    Object.values(activeSearchFilters).forEach(category => {
      if (category) {
        Object.values(category).forEach(value => {
          if (value !== undefined && value !== null && value !== "" && value !== false &&
              !(Array.isArray(value) && value.length === 0)) {
            count++
          }
        })
      }
    })
    return count
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

  const toggleTableFilter = (category: keyof TableFilters, value: string) => {
    setTableFilters(prev => {
      const current = prev[category]
      if (Array.isArray(current)) {
        return {
          ...prev,
          [category]: current.includes(value)
            ? current.filter(v => v !== value)
            : [...current, value]
        }
      }
      return prev
    })
  }

  const clearAllTableFilters = () => {
    setTableFilters(getDefaultTableFilters())
  }

  const clearAllFilters = () => {
    setSearchTerm("")
    setQuickFilters(new Set())
    setBooleanSearch("")
    setSelectedTemplate("")
    setAdvancedFilters({
      first_names: [],
      job_titles: [],
      years_experience: [],
      degrees: [],
      schools: [],
      companies: [],
      industries: [],
      skills: [],
      spoken_languages: [],
      locations: [],
      salary_ranges: [],
      contract_types: [],
      work_models: [],
      availability: [],
      certifications: [],
      soft_skills: []
    })
    setColumnFilters({
      position: [],
      company: [],
      location: [],
      scoreRange: [],
      bigFive: {
        openness: '',
        conscientiousness: '',
        extraversion: '',
        agreeableness: '',
        neuroticism: ''
      }
    })
  }

  const saveSearch = () => {
    if (searchTerm || booleanSearch) {
      const searchQuery = `${searchTerm} ${booleanSearch}`.trim()
      setSearchHistory(prev => [searchQuery, ...prev.slice(0, 9)])
    }
  }

  const saveSearchAsTemplate = () => {
    const searchQuery = `${searchTerm} ${booleanSearch}`.trim()
    if (searchQuery) {
      const searchData = {
        name: selectedTemplate || `Busca ${new Date().toLocaleDateString()}`,
        query: searchQuery,
        filters: { ...advancedFilters, booleanSearch },
        timestamp: new Date().toISOString()
      }
      setSavedSearches(prev => [searchData, ...prev])
      toast({
        title: "Busca salva",
        description: "Sua busca foi salva como template",
        duration: 4000
      })
    }
  }

  const applySavedSearch = (search: Record<string, unknown>) => {
    setSearchTerm(search.query.replace(search.filters.booleanSearch || '', '').trim())
    setBooleanSearch(search.filters.booleanSearch || '')
    setAdvancedFilters(search.filters)
  }

  const deleteSavedSearch = (index: number) => {
    setSavedSearches(prev => prev.filter((_, i) => i !== index))
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
    revealType, rubricCandidate, rubricEvaluationData, saveCurrentSearch, savedSearches, searchResults,
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
