/**
 * CandidatesPage — Sprint E god object extraction (phase 1 complete)
 *
 * This file has 12375 lines and is being broken down incrementally.
 * Extracted hooks (ready for import in phase 2):
 *   @see hooks/use-candidate-filters.ts   — TableFilters state + getDefaultTableFilters
 *   @see hooks/use-candidate-selection.ts — multi-select + bulk action state
 *
 * Sprint F3 (done): useCandidatesListMapped wired; manual initial useEffect removed.
 *   candidatesListHook syncs candidates + isLoading; search handlers still override via setCandidates.
 * Sprint F5 (done): CandidateTabs + CandidateSearchBar extracted + used in JSX.
 * TODO phase 3 remaining: Extract CandidateTableSection component.
 */
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

// Quick Actions Modals
import { ContactModal, ScheduleModal } from "@/components/quick-actions-modals"
import { QuickViewModal } from "@/components/quick-view-modal"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { CandidateComparison } from "@/components/candidate-comparison"

// Imports das abas do talent funnel
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

// Smart Search AI-First
import { type ParsedEntities, type SearchMode, type SearchMetadata } from "@/components/search/smart-search-input"

// Advanced Filters Modal
import { type SearchFilters } from "@/components/search/advanced-filters-modal"
import { FilterAutocomplete } from "@/components/search/filter-autocomplete"

// WSI Components
import { WSITextScreeningModal, WSIVoiceScreeningStatus, WSIScorecard } from "@/components/wsi"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
// Email Templates
import { SendEmailModal } from "@/components/email-templates"
// CV Parser
import { CVPreview, type ParsedCVResponse } from "@/components/cv"
// Calibration
import { LIAFeedbackWidget } from "@/components/calibration"
// Proactive Insights
import { ProactiveInsightCard, type SearchAnalytics } from "@/components/proactive-insight-card"
// Unified Table
import { UnifiedCandidateTable } from "@/components/tables"
import type { TableColumn, TableSortConfig } from "@/components/tables/types"
// Search Loading Animation
import { SearchLoadingAnimation } from "@/components/ui/search-loading-animation"
import { CalibrationCard, type CalibrationCandidate } from "@/components/calibration-card"
// Candidate Review Modal
import { CandidateReviewModal, type ReviewCandidate, type Criterion } from "@/components/pages/candidate-review-modal"
// Bulk Actions
// BulkActionsBar removido - ações agora aparecem no chat da LIA
import { JobVacancy, EmailTemplate } from "@/services/lia-api"

// Credit Confirmation Dialog for Global Search
import { CreditConfirmationDialog } from "@/components/search/credit-confirmation-dialog"

// Reveal Credits Modal
import { RevealCreditsModal } from "@/components/reveal-credits-modal"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

// Pearch AI Search Integration
import {
  searchCandidates as searchCandidatesHybrid,
  searchLocalCandidates,
  estimateCredits,
  calculateCreditsLocally,
  type SearchRequest,
  type SearchResponse,
  type CreditEstimate
} from "@/lib/api/candidate-search"

// Source Detection Utility
import { getSourceDetails, isGlobalSource, isLocalSource } from "@/lib/utils/source-detection"
// Toast notifications
import { useToast } from "@/hooks/use-toast"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
// Global Search Settings
import { useGlobalSearchSettings } from "@/hooks/useGlobalSearchSettings"
// Hide Viewed Candidates Hook
import { useHideViewedCandidates } from "@/hooks/useHideViewedCandidates"
import { useCandidateFilters, type TableFilters, getDefaultTableFilters } from "@/hooks/use-candidate-filters"
import { useCandidateSelection } from "@/hooks/use-candidate-selection"
import { useBulkCandidateDataRequests } from "@/hooks/use-candidate-data-requests"
// Sprint G4: useCandidatesListMapped wraps useCandidatesList + transform CandidateLocal→Candidate
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

// Design Tokens
import { textStyles, cardStyles, badgeStyles, formatScore, formatScorePercent } from "@/lib/design-tokens"
import { CandidateTabs } from "@/components/pages/candidates/CandidateTabs"
import { CandidateSearchBar } from "@/components/pages/candidates/CandidateSearchBar"
import { SearchResultsHeader } from "@/components/pages/candidates/SearchResultsHeader"
import { CandidatesFilterPanel } from "@/components/pages/candidates/CandidatesFilterPanel"
import type { Candidate } from "@/components/pages/candidates/types"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const SmartSearchInput = dynamic(
  () => import("@/components/search/smart-search-input").then(m => ({ default: m.SmartSearchInput })).catch(() => {
    return { default: () => null as any }
  }),
  { ssr: false, loading: () => <div className="h-12 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse" /> }
)
const AdvancedFiltersModal = dynamic(() => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })), { ssr: false })

const SALARY_RANGES = {
  junior: { min: 4000, max: 7000 },
  pleno: { min: 8000, max: 14000 },
  senior: { min: 15000, max: 25000 },
  specialist: { min: 20000, max: 35000 },
  lead: { min: 25000, max: 40000 }
}

const getSalaryByExperience = (experience: number, index: number): number => {
  let range = SALARY_RANGES.junior
  if (experience >= 10) range = SALARY_RANGES.lead
  else if (experience >= 7) range = SALARY_RANGES.specialist
  else if (experience >= 4) range = SALARY_RANGES.senior
  else if (experience >= 2) range = SALARY_RANGES.pleno
  
  const variation = (index * 1234) % (range.max - range.min + 1)
  return range.min + variation
}

const generateWorkHistory = (candidate: CandidateLocal, experience: number): Array<{
  company: string
  title: string
  position: string
  period: string
  startDate: string
  endDate?: string
  description: string
}> => {
  const workHistory: Array<{
    company: string
    title: string
    position: string
    period: string
    startDate: string
    endDate?: string
    description: string
  }> = []
  
  const currentYear = new Date().getFullYear()
  const title = candidate.current_title || 'Profissional'
  const company = candidate.current_company || ''
  const seniority = candidate.seniority_level?.toLowerCase() || ''
  
  const techCompanies = ['TechCorp Brasil', 'Nubank', 'iFood', 'Mercado Livre', 'Stone', 'PicPay', 'Itaú Digital', 'Bradesco Next', 'Movile', 'VTEX', 'Creditas', 'Loft', 'QuintoAndar', 'Wildlife Studios', 'Loggi']
  const startups = ['Startup XYZ', 'InnovaTech', 'FinTech Solutions', 'DataDriven Co', 'CloudFirst', 'AgileHub', 'ScaleTech', 'GrowthLabs']
  const consultancies = ['Accenture', 'McKinsey Digital', 'BCG Gamma', 'KPMG Tech', 'Deloitte Digital', 'EY Brasil']
  
  const getDescriptionByTitle = (t: string): string => {
    const lower = t.toLowerCase()
    if (lower.includes('cto') || lower.includes('chief')) return 'Liderança técnica e estratégica, definição de arquitetura e roadmap tecnológico'
    if (lower.includes('head') || lower.includes('diretor')) return 'Gestão de equipes multidisciplinares e entrega de projetos estratégicos'
    if (lower.includes('gerente') || lower.includes('manager')) return 'Coordenação de times, gestão de projetos e processos ágeis'
    if (lower.includes('tech lead') || lower.includes('líder')) return 'Liderança técnica de squad, code reviews e mentoria de desenvolvedores'
    if (lower.includes('senior') || lower.includes('sênior')) return 'Desenvolvimento de soluções complexas e mentoria de desenvolvedores juniores'
    if (lower.includes('arquiteto') || lower.includes('architect')) return 'Definição de arquitetura de sistemas e padrões técnicos'
    if (lower.includes('full stack') || lower.includes('fullstack')) return 'Desenvolvimento end-to-end de aplicações web e APIs'
    if (lower.includes('frontend') || lower.includes('front-end')) return 'Desenvolvimento de interfaces responsivas e experiência do usuário'
    if (lower.includes('backend') || lower.includes('back-end')) return 'Desenvolvimento de APIs RESTful e microsserviços'
    if (lower.includes('devops') || lower.includes('sre')) return 'Automação de infraestrutura, CI/CD e monitoramento'
    if (lower.includes('data') || lower.includes('dados')) return 'Análise de dados, machine learning e pipelines de dados'
    if (lower.includes('product') || lower.includes('produto')) return 'Definição de roadmap, discovery e entrega de valor ao usuário'
    if (lower.includes('design') || lower.includes('ux')) return 'Pesquisa de usuário, prototipagem e design de interfaces'
    return 'Desenvolvimento de software e entrega de soluções técnicas'
  }
  
  if (company) {
    const startYear = currentYear - Math.min(experience, 3)
    workHistory.push({
      company: company,
      title: title,
      position: title,
      period: `${startYear} - Atual`,
      startDate: `${startYear}-01-01`,
      description: getDescriptionByTitle(title)
    })
  }
  
  if (experience >= 3) {
    const prevCompanies = seniority.includes('senior') || seniority.includes('lead') || seniority.includes('specialist') ? techCompanies : startups
    const prevCompany = prevCompanies[Math.floor(Math.random() * prevCompanies.length)]
    const prevTitle = title.replace(/Senior|Sênior|Lead|Principal|Staff/gi, '').trim() || 'Desenvolvedor'
    const endYear = company ? currentYear - Math.min(experience, 3) : currentYear - 1
    const startYear = endYear - Math.min(2, Math.floor(experience / 2))
    
    workHistory.push({
      company: prevCompany,
      title: prevTitle,
      position: prevTitle,
      period: `${startYear} - ${endYear}`,
      startDate: `${startYear}-01-01`,
      endDate: `${endYear}-12-01`,
      description: getDescriptionByTitle(prevTitle)
    })
  }
  
  if (experience >= 6) {
    const earlyCompany = consultancies[Math.floor(Math.random() * consultancies.length)]
    const earlyTitle = 'Analista de Sistemas'
    const endYear = currentYear - Math.floor(experience / 2) - 1
    const startYear = endYear - 2
    
    workHistory.push({
      company: earlyCompany,
      title: earlyTitle,
      position: earlyTitle,
      period: `${startYear} - ${endYear}`,
      startDate: `${startYear}-01-01`,
      endDate: `${endYear}-12-01`,
      description: 'Desenvolvimento de software e suporte técnico a clientes enterprise'
    })
  }
  
  if (workHistory.length === 0) {
    workHistory.push({
      company: 'Empresa Atual',
      title: title,
      position: title,
      period: `${currentYear - 1} - Atual`,
      startDate: `${currentYear - 1}-01-01`,
      description: getDescriptionByTitle(title)
    })
  }
  
  return workHistory
}

const generateEducation = (candidate: CandidateLocal, experience: number): Array<{
  school: string
  institution: string
  degree: string
  field_of_study: string
  fieldOfStudy: string
  startDate: string
  endDate: string
}> => {
  const education: Array<{
    school: string
    institution: string
    degree: string
    field_of_study: string
    fieldOfStudy: string
    startDate: string
    endDate: string
  }> = []
  
  const currentYear = new Date().getFullYear()
  const title = (candidate.current_title || '').toLowerCase()
  const seniority = (candidate.seniority_level || '').toLowerCase()
  
  const topUniversities = ['USP', 'UNICAMP', 'UFRJ', 'UFMG', 'UFRGS', 'PUC-Rio', 'PUC-SP', 'Insper', 'FGV', 'ITA', 'IME']
  const otherUniversities = ['Mackenzie', 'FIAP', 'FATEC', 'Unisinos', 'PUCRS', 'UFSCar', 'UFSC', 'UFPR', 'UnB', 'UFBA']
  const mbaSchools = ['Insper', 'FGV', 'USP/FIA', 'Fundação Dom Cabral', 'IBMEC', 'BSP', 'Saint Paul']
  
  const getFieldByTitle = (t: string): string => {
    if (t.includes('data') || t.includes('dados') || t.includes('machine learning') || t.includes('ai')) return 'Ciência de Dados'
    if (t.includes('frontend') || t.includes('front-end') || t.includes('design') || t.includes('ux')) return 'Design Digital'
    if (t.includes('devops') || t.includes('sre') || t.includes('infra')) return 'Engenharia de Computação'
    if (t.includes('product') || t.includes('produto')) return 'Administração de Empresas'
    if (t.includes('security') || t.includes('segurança')) return 'Segurança da Informação'
    return 'Ciência da Computação'
  }
  
  const isLeadership = seniority.includes('lead') || seniority.includes('head') || seniority.includes('director') || 
                       title.includes('cto') || title.includes('gerente') || title.includes('manager') ||
                       title.includes('head') || title.includes('diretor') || experience >= 10
  
  if (isLeadership && experience >= 8) {
    const mbaSchool = mbaSchools[Math.floor(Math.random() * mbaSchools.length)]
    const endYear = currentYear - Math.floor(experience / 3)
    const startYear = endYear - 2
    
    education.push({
      school: mbaSchool,
      institution: mbaSchool,
      degree: 'MBA',
      field_of_study: 'Gestão de Tecnologia e Inovação',
      fieldOfStudy: 'Gestão de Tecnologia e Inovação',
      startDate: `${startYear}-02-01`,
      endDate: `${endYear}-12-01`
    })
  }
  
  const isSenior = seniority.includes('senior') || seniority.includes('specialist') || seniority.includes('lead') || experience >= 5
  const universities = isSenior ? topUniversities : otherUniversities
  const university = universities[Math.floor(Math.random() * universities.length)]
  const field = getFieldByTitle(title)
  const gradEndYear = currentYear - experience - 1
  const gradStartYear = gradEndYear - 4
  
  education.push({
    school: university,
    institution: university,
    degree: 'Bacharelado',
    field_of_study: field,
    fieldOfStudy: field,
    startDate: `${gradStartYear}-02-01`,
    endDate: `${gradEndYear}-12-01`
  })
  
  if (isSenior && !isLeadership && experience >= 5) {
    const pgSchool = topUniversities[Math.floor(Math.random() * topUniversities.length)]
    const pgEndYear = currentYear - Math.floor(experience / 2)
    const pgStartYear = pgEndYear - 2
    
    education.push({
      school: pgSchool,
      institution: pgSchool,
      degree: 'Pós-Graduação',
      field_of_study: 'Engenharia de Software',
      fieldOfStudy: 'Engenharia de Software',
      startDate: `${pgStartYear}-02-01`,
      endDate: `${pgEndYear}-12-01`
    })
  }
  
  return education
}

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

export function CandidatesPage({ onAddRecentItem, pendingCandidateOpen, onCandidateOpened }: { onAddRecentItem?: (item: { id: string; type: 'vaga' | 'chat' | 'candidato'; title: string; subtitle?: string; meta?: Record<string, string | undefined> }) => void; pendingCandidateOpen?: { candidateId: string; candidateName: string } | null; onCandidateOpened?: () => void } = {}) {
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
  
  // Sprint E — extracted hooks
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

  // Estados simples usando useState
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
      // ignore
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

  const [searchTerm, setSearchTerm] = useState("")
  const [quickFilters, setQuickFilters] = useState<Set<string>>(new Set())

  const [activeTab, setActiveTab] = useState<'search' | 'favorites' | 'lists' | 'history' | 'saved-searches' | 'agents'>('search')
  const [lastSearchQuery, setLastSearchQuery] = useState<string>("")
  const [lastSearchEntities, setLastSearchEntities] = useState<ParsedEntities | null>(null)
  const [lastSearchMode, setLastSearchMode] = useState<string>("")
  const [lastSearchMetadata, setLastSearchMetadata] = useState<SearchMetadata | undefined>(undefined)
  const [lastSearchUsedPearch, setLastSearchUsedPearch] = useState<boolean>(false)
  const [hasSearchResults, setHasSearchResults] = useState(false)
  const [searchResultsCount, setSearchResultsCount] = useState<number>(0)
  const [localResultsCount, setLocalResultsCount] = useState<number>(0)
  const [pearchResultsCount, setPearchResultsCount] = useState<number>(0)
  const [creditsUsedInSearch, setCreditsUsedInSearch] = useState<number>(0)
  const [creditsRemaining, setCreditsRemaining] = useState<number | null>(null) // Saldo atual de créditos Pearch
  const [showExpandGlobalOption, setShowExpandGlobalOption] = useState(false)
  
  // Estados para modais de crédito floatantes na busca inteligente
  const [openCreditModals, setOpenCreditModals] = useState({
    hybrid: false,
    global: false,
    email: false,
    phone: false
  })
  
  // Estados para modal de edição de query
  const [showEditQueryModal, setShowEditQueryModal] = useState(false)
  const [editQueryValue, setEditQueryValue] = useState("")
  
  // Toast notifications
  const { toast } = useToast()
  
  // Persistência de navegação
  const { saveTalentFunnelState } = useNavigationPersistence()
  
  // Salvar estado quando aba ou busca mudam
  useEffect(() => {
    // Só salva se a aba for uma das 3 principais
    if (activeTab === 'search' || activeTab === 'favorites' || activeTab === 'lists') {
      saveTalentFunnelState(activeTab, lastSearchQuery)
    }
  }, [activeTab, lastSearchQuery, saveTalentFunnelState])
  const [showSearchResults, setShowSearchResults] = useState(false) // Controla se mostra resultados inline na tab Busca
  const [searchSource, setSearchSource] = useState<'local' | 'global' | 'hybrid'>('hybrid') // Toggle local vs Global
  
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
  
  // ========== SEARCH SOURCE CONTROLS ==========
  const [currentSearchSource, setCurrentSearchSource] = useState<SearchSource>('local') // Fonte atual da busca exibida
  const [showGlobalExpansionConfirm, setShowGlobalExpansionConfirm] = useState(false) // Modal de confirmação de créditos para expansão global
  const [hasSearched, setHasSearched] = useState(false) // Flag para saber se já executou uma busca
  const [isExpandingToGlobal, setIsExpandingToGlobal] = useState(false) // Loading state para expansão global
  
  
  // ========== VIEWED CANDIDATES STATE ==========
  const [viewedCandidateIds, setViewedCandidateIds] = useState<Set<string>>(new Set())
  const [showOnlyNew, setShowOnlyNew] = useState(false)
  const [isDroppingCV, setIsDroppingCV] = useState(false)
  const [cvUploadLoading, setCvUploadLoading] = useState(false)
  
  // Counter to track each unique search execution
  const [searchExecutionId, setSearchExecutionId] = useState<number>(0)
  
  // ========== FASE 1 FUNIL DE TALENTOS STATE ==========
  const [searchSortBy, setSearchSortBy] = useState<string>('relevance')
  const [searchFeedbacks, setSearchFeedbacks] = useState<Record<string, 'like' | 'dislike'>>({})
  const [displayedResultsCount, setDisplayedResultsCount] = useState(10)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  
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
        console.error('Error loading viewed candidates:', error)
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
      console.error('Error marking candidate as viewed:', error)
    }
  }
  
  // CV Dropzone handlers
  const handleCVDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(false)
    
    const files = e.dataTransfer.files
    if (files.length === 0) return
    
    const file = files[0]
    const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    
    if (!validTypes.includes(file.type) && !file.name.match(/\.(pdf|doc|docx|txt)$/i)) {
      toast({
        title: "Formato inválido",
        description: "Por favor, envie um arquivo PDF, DOC, DOCX ou TXT",
        variant: "destructive"
      })
      return
    }
    
    setCvUploadLoading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/backend-proxy/search/candidates/from-cv?limit=20&search_pearch=false', {
        method: 'POST',
        body: formData
      })
      
      if (!response.ok) {
        throw new Error('Erro ao processar CV')
      }
      
      const data = await response.json()
      
      // Add LIA message with results (only show local results - user can opt-in to global)
      const liaMessage: ChatMessage = {
        id: `lia-cv-${Date.now()}`,
        type: 'lia',
        content: `📄 Analisei o CV **${file.name}** e encontrei:\n\n` +
          `**Perfil extraído:**\n` +
          `• Título: ${data.extracted_title || 'Não identificado'}\n` +
          `• Skills: ${data.extracted_skills?.slice(0, 5).join(', ') || 'Não identificadas'}\n\n` +
          `**Busca na base local:**\n` +
          `• Query gerada: "${data.query_generated}"\n` +
          `• ${data.local_count || data.total_count} candidato${(data.local_count || data.total_count) > 1 ? 's' : ''} encontrado${(data.local_count || data.total_count) > 1 ? 's' : ''}`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, liaMessage])
      
      // Update candidates with results if available
      if (data.candidates && data.candidates.length > 0) {
        const mappedCandidates: Candidate[] = data.candidates.map((c: any) => ({
          id: c.id || `cv-${Date.now()}-${Math.random()}`,
          candidateId: c.id || '',
          name: c.name || `${c.first_name || ''} ${c.last_name || ''}`.trim(),
          email: '',
          phone: '',
          current_title: c.current_title || c.headline,
          current_company: c.current_company,
          linkedin_url: c.linkedin_url,
          technical_skills: c.skills || [],
          location_city: c.location?.split(',')[0]?.trim(),
          avatar_url: c.picture_url,
          years_of_experience: c.total_experience_years,
          status: 'new',
          source: c.source || 'local',
          position: c.current_title || 'Não especificado',
          location: c.location || 'Não especificado',
          workModel: 'remoto' as 'remoto' | 'híbrido' | 'presencial',
          score: c.score || 75,
          skills: c.skills || [],
          experience: c.total_experience_years || 0,
          education: 'Não informado',
          contractType: 'CLT' as 'CLT' | 'PJ' | 'Freelancer',
          linkedin: c.linkedin_url || '',
          monthlySalary: 0,
          avatar: c.picture_url
        }))
        
        setCandidates(mappedCandidates)
        setHasSearchResults(true)
        setSearchResultsCount(mappedCandidates.length)
        setShowSearchResults(true)
        setDisplayedResultsCount(10)
        
        toast({
          title: "CV analisado",
          description: `Encontrados ${mappedCandidates.length} candidatos similares`,
        })
      }
    } catch (error) {
      console.error('CV upload error:', error)
      toast({
        title: "Erro ao processar CV",
        description: error instanceof Error ? error.message : 'Erro desconhecido',
        variant: "destructive"
      })
    } finally {
      setCvUploadLoading(false)
    }
  }
  
  const handleCVDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(true)
  }
  
  const handleCVDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDroppingCV(false)
  }
  
  // Hook centralizado para gerenciar favoritos, histórico e buscas salvas
  const talentFunnel = useTalentFunnel()
  
  // Estados derivados do hook para compatibilidade com componentes existentes
  const favorites = talentFunnel.getFavoriteIds()
  const pinnedCandidates = talentFunnel.getPinnedIds()
  const favoriteNotes = talentFunnel.getFavoriteNotes()
  

  // Estados para paginação tradicional (como Gestão de Vagas)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(50)
  const tableContainerRef = useRef<HTMLDivElement>(null)

  // ✨ Estados para integração cross-tab
  const [crossTabFilter, setCrossTabFilter] = useState<any>(null)
  const [showCrossTabBanner, setShowCrossTabBanner] = useState(false)
  
  // ✨ Estado para visualização de lista
  const [viewingList, setViewingList] = useState<{ id: string; name: string; color?: string } | null>(null)

  // Estados existentes...
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [showPreview, setShowPreview] = useState(false)
  const [isPreviewMaximized, setIsPreviewMaximized] = useState(false)
  const [showCandidatePage, setShowCandidatePage] = useState(false)
  const [showCandidatePreview, setShowCandidatePreview] = useState(false)
  const [previewCandidate, setPreviewCandidate] = useState<Candidate | null>(null)
  const [sortBy, setSortBy] = useState<string>('score')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showSidePreview, setShowSidePreview] = useState(false)
  const [sidePreviewCandidate, setSidePreviewCandidate] = useState<Candidate | null>(null)
  const [selectedCandidateForLIA, setSelectedCandidateForLIA] = useState<Candidate | null>(null)
  const [showLIAPromptForCandidate, setShowLIAPromptForCandidate] = useState(false)
  const [showExpandedLIA, setShowExpandedLIA] = useState(false)
  const [liaPromptValue, setLiaPromptValue] = useState("")
  const [userCollapsedLIA, setUserCollapsedLIA] = useState(false)
  const [talentConversationId, setTalentConversationId] = useState<string | undefined>(undefined)
  
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
        console.error('Error parsing entities:', error)
      } finally {
        setLiaIsParsingEntities(false)
      }
    }, 500)
    
    return () => clearTimeout(debounceTimer)
  }, [liaPromptValue])
  
  // Estados para o novo sistema de pesquisa avançada da LIA - 6 abas
  type SearchTab = 'ia-natural' | 'similar' | 'job-description' | 'boolean' | 'arquetipos' | 'filtros'
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>('ia-natural')
  const [jobDescriptionText, setJobDescriptionText] = useState("")
  const [liaWidth, setLiaWidth] = useState(400) // Largura padrão 400px - ElevenLabs pattern
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  const [isLiaSuperChat, setIsLiaSuperChat] = useState(false) // Modo superchat expandido
  const [superChatWidth, setSuperChatWidth] = useState(600) // Largura do superchat
  
  // Estados adicionais para as novas abas
  const [similarProfileUrl, setSimilarProfileUrl] = useState("")
  const [booleanSearchValue, setBooleanSearchValue] = useState("")
  const [filterLocation, setFilterLocation] = useState("")
  const [filterExperience, setFilterExperience] = useState("any")
  const [filterSeniority, setFilterSeniority] = useState("any")
  const [filterWorkModel, setFilterWorkModel] = useState("any")
  
  // Estados para busca Similar e Job Description
  const [isSearchingSimilar, setIsSearchingSimilar] = useState(false)
  const [isSearchingJD, setIsSearchingJD] = useState(false)
  const [extractedJDCriteria, setExtractedJDCriteria] = useState<{
    job_title?: string
    seniority?: string
    skills: string[]
    experience_years?: number
    location?: string
    languages: string[]
  } | null>(null)
  
  // Estado para modal de filtros avançados removido - agora usa painel lateral
  
  // 🏷️ Estados para sistema de Arquétipos
  type Archetype = {
    id: string
    name: string
    description: string
    emoji: string
    query: string
    filters: {
      job_title?: string
      seniority?: string
      skills?: string[]
      location?: string
      experience_years?: number
    }
    tags?: string[]
    industry?: string
    createdAt: Date
    isDefault?: boolean
    usage_count?: number
  }
  
  // Backend archetypes loaded from API
  type BackendArchetype = {
    id: string
    name: string
    description?: string
    emoji: string
    query: string
    filters: Record<string, any>
    tags: string[]
    industry?: string
    seniority?: string
    is_default: boolean
    is_active: boolean
    usage_count: number
    created_at?: string
  }
  const [backendArchetypes, setBackendArchetypes] = useState<BackendArchetype[]>([])
  const [isLoadingArchetypes, setIsLoadingArchetypes] = useState(false)
  const [archetypesLoadError, setArchetypesLoadError] = useState<string | null>(null)
  const [isSearchingByArchetype, setIsSearchingByArchetype] = useState(false)
  
  const [userArchetypes, setUserArchetypes] = useState<Archetype[]>([])
  const [isCreatingArchetype, setIsCreatingArchetype] = useState(false)
  const [archetypeCreationStep, setArchetypeCreationStep] = useState<'initial' | 'input' | 'extracting' | 'review' | 'saving'>('initial')
  const [newArchetypeData, setNewArchetypeData] = useState<Partial<Archetype>>({})
  const [archetypeJobDescription, setArchetypeJobDescription] = useState("")
  const [archetypeLibraryTab, setArchetypeLibraryTab] = useState<'meus' | 'sugestoes' | 'templates'>('meus')
  const [showSaveAsArchetypeModal, setShowSaveAsArchetypeModal] = useState(false)
  const [archetypeNameInput, setArchetypeNameInput] = useState("")
  const [archetypeEmojiInput, setArchetypeEmojiInput] = useState("🎯")
  const [lastSuccessfulQuery, setLastSuccessfulQuery] = useState("") // Armazena a última query bem-sucedida para o modal de arquétipo
  
  // Estado para preview de sugestão IA
  type AISuggestion = {
    name: string
    description: string
    query: string
    filters: {
      job_title?: string
      seniority?: string
      skills?: string[]
      location?: string
    }
  }
  const [previewSuggestion, setPreviewSuggestion] = useState<AISuggestion | null>(null)
  const [previewTags, setPreviewTags] = useState<string[]>([])
  const [newPreviewTag, setNewPreviewTag] = useState("")
  const [isSavingPreviewArchetype, setIsSavingPreviewArchetype] = useState(false)
  
  // Estado para preview de arquétipo do usuário (Meus Arquétipos)
  const [previewingUserArchetype, setPreviewingUserArchetype] = useState<Archetype | null>(null)
  
  // Estado para exclusão de arquétipo com confirmação
  const [archetypeToDelete, setArchetypeToDelete] = useState<Archetype | null>(null)
  const [isDeletingArchetype, setIsDeletingArchetype] = useState(false)
  
  const buildFiltersFromTags = (tags: string[]): Record<string, string[]> => {
    const seniorityKeywords = ['júnior', 'junior', 'pleno', 'sênior', 'senior', 'especialista', 'lead', 'principal', 'staff', 'estagiário', 'trainee']
    const locationKeywords = ['são paulo', 'rio de janeiro', 'belo horizonte', 'curitiba', 'porto alegre', 'brasília', 'salvador', 'fortaleza', 'recife', 'remoto', 'híbrido', 'presencial']
    
    const skills: string[] = []
    const locations: string[] = []
    const seniority: string[] = []
    
    tags.forEach(tag => {
      const lowerTag = tag.toLowerCase().trim()
      
      if (seniorityKeywords.some(kw => lowerTag.includes(kw))) {
        seniority.push(tag)
      } else if (locationKeywords.some(kw => lowerTag.includes(kw))) {
        locations.push(tag)
      } else {
        skills.push(tag)
      }
    })
    
    return {
      skills,
      locations,
      seniority,
      keywords: tags
    }
  }
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
  
  // Estado para histórico de chat da LIA
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
  const chatScrollRef = useRef<HTMLDivElement>(null)
  
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
        console.error('Erro ao processar filtro cross-tab:', error)
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
  
  // 🎯 Load archetypes from backend
  const loadArchetypesFromBackend = async () => {
    setIsLoadingArchetypes(true)
    setArchetypesLoadError(null)
    try {
      const response = await fetch('/api/backend-proxy/search/archetypes')
      if (!response.ok) {
        throw new Error(`Erro ao carregar arquétipos: ${response.status}`)
      }
      const data = await response.json()
      setBackendArchetypes(data.archetypes || [])
    } catch (error) {
      console.error('Erro ao carregar arquétipos:', error)
      setArchetypesLoadError(error instanceof Error ? error.message : 'Erro ao carregar arquétipos')
    } finally {
      setIsLoadingArchetypes(false)
    }
  }
  
  
  // Function to execute search by archetype
  const executeArchetypeSearch = async (archetype: BackendArchetype) => {
    setIsSearchingByArchetype(true)
    try {
      const response = await fetch(`/api/backend-proxy/search/archetypes/${archetype.id}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          search_local: true,
          search_pearch: searchSource === 'global' || searchSource === 'hybrid',
          pearch_type: pearchSearchOptions.searchType,
          local_limit: 50,
          pearch_limit: pearchSearchOptions.limit,
          calculate_lia_score: true
        })
      })
      
      if (!response.ok) {
        throw new Error(`Erro na busca: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Update UI with search results
      setLiaPromptValue(archetype.query)
      setActiveSearchTab('ia-natural')
      
      // Map candidates to expected format
      if (data.candidates && data.candidates.length > 0) {
        const mappedCandidates: Candidate[] = data.candidates.map((c: any) => ({
          id: c.id || `arch-${Date.now()}-${Math.random()}`,
          candidateId: c.id || '',
          name: c.name || `${c.first_name || ''} ${c.last_name || ''}`.trim(),
          email: '',
          phone: '',
          current_title: c.current_title || c.headline,
          current_company: c.current_company,
          linkedin_url: c.linkedin_url,
          seniority_level: archetype.seniority,
          technical_skills: c.skills || [],
          location_city: c.location?.split(',')[0]?.trim(),
          location_state: c.location?.split(',')[1]?.trim(),
          avatar_url: c.picture_url,
          years_of_experience: c.total_experience_years,
          status: 'new',
          source: c.source || 'pearch',
          matching_score: c.lia_score || c.score || 0,
          match_summary: c.lia_reasoning || c.match_summary,
          is_opentowork: c.is_open_to_work,
          lia_score: c.lia_score,
          lia_breakdown: c.lia_breakdown,
          lia_strengths: c.lia_strengths || [],
          lia_concerns: c.lia_concerns || []
        }))
        
        setCandidates(mappedCandidates)
        setHasSearchResults(true)
        setSearchResultsCount(mappedCandidates.length)
        setLocalResultsCount(data.local_count || 0)
        setPearchResultsCount(data.pearch_count || 0)
        setLastSearchQuery(archetype.query)
        setLastSearchMode('archetype')
        
        // Add chat message for LIA (only show local count - user can opt-in to global)
        const localCount = data.local_count || mappedCandidates.length
        const liaMessage: ChatMessage = {
          id: `lia-arch-${Date.now()}`,
          type: 'lia',
          content: `🎯 Busca por arquétipo "${archetype.name}" concluída!\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''}** na sua base local.${data.credits_remaining !== undefined ? `\n\n💳 Créditos restantes: ${data.credits_remaining}` : ''}`,
          timestamp: new Date(),
          searchResults: {
            localCount: localCount,
            globalCount: 0,
            query: archetype.query
          }
        }
        setChatMessages(prev => [...prev, liaMessage])
        
        toast({
          title: "Busca por arquétipo concluída",
          description: `${mappedCandidates.length} candidato(s) encontrado(s) para "${archetype.name}"`,
        })
      } else {
        toast({
          title: "Nenhum candidato encontrado",
          description: `A busca por "${archetype.name}" não retornou resultados`,
          variant: "destructive"
        })
      }
    } catch (error) {
      console.error('Erro na busca por arquétipo:', error)
      toast({
        title: "Erro na busca",
        description: error instanceof Error ? error.message : 'Erro ao buscar por arquétipo',
        variant: "destructive"
      })
    } finally {
      setIsSearchingByArchetype(false)
    }
  }

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
  const [contactModalCandidate, setContactModalCandidate] = useState<any>(null)
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
  const [rubricEvaluationData, setRubricEvaluationData] = useState<any>(null)

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
  const [pearchSearchOptions, setPearchSearchOptions] = useState({
    searchType: 'fast' as 'fast' | 'pro',
    limit: 50, // Aumentado de 15 para 50 - limite máximo é 100
    showEmails: false,
    showPhoneNumbers: false,
    highFreshness: false,
    requireEmails: false, // Filtrar apenas candidatos com email disponível (+1 crédito)
    requirePhoneNumbers: false // Filtrar apenas candidatos com telefone disponível (+1 crédito)
  })
  
  // Source Change & Contact Filter Credit Confirmation Modals
  const [showSourceChangeModal, setShowSourceChangeModal] = useState(false)
  const [pendingSourceChange, setPendingSourceChange] = useState<'hybrid' | 'global' | null>(null)
  const [showContactFilterModal, setShowContactFilterModal] = useState(false)
  const [pendingContactFilter, setPendingContactFilter] = useState<'email' | 'phone' | null>(null)

  // Reveal Contact System States
  const [showRevealModal, setShowRevealModal] = useState(false)
  const [revealCandidate, setRevealCandidate] = useState<Candidate | null>(null)
  const [revealType, setRevealType] = useState<"email" | "phone">("email")
  const [revealedContacts, setRevealedContacts] = useState<Record<string, { email?: string; phone?: string }>>({})
  const [isRevealing, setIsRevealing] = useState(false)
  
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
      .catch(error => console.error('Error loading job vacancies:', error))

    liaApi.listEmailTemplates(undefined, true)
      .then(response => {
        if (response.items) {
          setBulkEmailTemplates(response.items)
        }
      })
      .catch(error => console.error('Error loading email templates:', error))
  }, [])

  // Handler para abrir modal de reveal
  const openRevealModal = (candidate: Candidate, type: "email" | "phone") => {
    setRevealCandidate(candidate)
    setRevealType(type)
    setShowRevealModal(true)
  }

  // Handler para executar reveal de contato
  const handleRevealContact = async () => {
    if (!revealCandidate) return

    setIsRevealing(true)
    try {
      const response = await fetch('/api/backend-proxy/search/reveal/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: revealCandidate.id,
          candidate_name: revealCandidate.name,
          reveal_type: revealType,
          linkedin_slug: revealCandidate.linkedin_url?.split('/in/')?.[1]?.replace('/', '') || null
        })
      })

      const data = await response.json()

      if (data.success) {
        setRevealedContacts(prev => ({
          ...prev,
          [revealCandidate.id]: {
            ...prev[revealCandidate.id],
            [revealType]: revealType === 'email' ? data.email : data.phone
          }
        }))
        setShowRevealModal(false)
        
        // Atualiza o saldo de créditos se retornado pelo backend
        if (data.credits_remaining !== undefined && data.credits_remaining !== null) {
          setCreditsRemaining(data.credits_remaining)
        }
        
        // Toast de sucesso com info sobre persistência
        const revealedValue = revealType === 'email' ? data.email : data.phone
        toast({
          title: revealType === 'email' ? "Email revelado" : "Telefone revelado",
          description: (
            <div className="flex flex-col gap-1">
              <span className="font-medium">{revealedValue}</span>
              {data.credits_used > 0 && (
                <span className="text-xs text-muted-foreground">
                  -{data.credits_used} créditos
                  {data.credits_remaining !== undefined && ` (saldo: ${data.credits_remaining})`}
                </span>
              )}
            </div>
          ),
          duration: 5000
        })
        
        // Persistir dados revelados no banco automaticamente (candidato Pearch)
        if (revealCandidate.source === 'pearch') {
          try {
            // Usar pearch_profile_id se disponível, senão usar id como fallback
            const pearchId = revealCandidate.pearch_profile_id || revealCandidate.id
            
            const persistResponse = await fetch('/api/backend-proxy/search/candidates/persist-revealed', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                pearch_id: pearchId,
                candidate_name: revealCandidate.name,
                email: revealType === 'email' ? data.email : null,
                phone: revealType === 'phone' ? data.phone : null,
                linkedin_url: revealCandidate.linkedin_url || null,
                current_title: revealCandidate.current_title || null,
                current_company: revealCandidate.current_company || null,
                avatar_url: revealCandidate.avatar_url || null
              })
            })
            
            const persistData = await persistResponse.json()
            
            if (persistData.success) {
              // Toast sutil informando que LIA salvou o dado
              toast({
                title: "LIA salvou o contato",
                description: persistData.is_new 
                  ? "Candidato adicionado à sua base local" 
                  : "Dados atualizados no cadastro existente",
                duration: 3000
              })
            } else {
              // Toast de aviso se não conseguiu persistir
              toast({
                title: "Aviso",
                description: "Contato revelado mas não foi salvo na base. Use 'Salvar na Base' para persistir.",
                duration: 4000
              })
            }
          } catch (persistError) {
            console.error('Error persisting revealed contact:', persistError)
            // Toast de aviso sobre falha na persistência
            toast({
              title: "Aviso",
              description: "Contato revelado mas não foi salvo automaticamente. Use 'Salvar na Base' para persistir.",
              duration: 4000
            })
          }
        }
      } else {
        // Toast de erro quando não encontra contato
        toast({
          variant: "destructive",
          title: "Contato não disponível",
          description: data.message || 'Não foi possível revelar o contato',
          duration: 5000
        })
      }
    } catch (error) {
      console.error('Error revealing contact:', error)
      // Toast de erro genérico
      toast({
        variant: "destructive",
        title: "Erro ao revelar contato",
        description: "Ocorreu um erro. Tente novamente.",
        duration: 5000
      })
    } finally {
      setIsRevealing(false)
    }
  }

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
            avatar: c.avatar_url || (c as any).picture_url,
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
        console.error('Error refreshing candidates:', error)
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
  const mapCandidateToInternal = (c: any): Candidate => {
    const candidateSource = c.source || 'pearch'
    return {
      id: c.id || `search-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      candidateId: c.id?.substring(0, 8).toUpperCase() || 'CAND',
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
      score: c.match_score ? Math.round(c.match_score * 25) : (c.score || 75),
      contractType: 'CLT' as const,
      linkedin: c.linkedin_url || '',
      avatar: c.avatar_url || c.picture_url,
      experiences: c.experiences || c.work_history || [],
      workHistory: (c.experiences || c.work_history || []).map((exp: any) => ({
        company: exp.company_info?.name || exp.company || '',
        title: exp.company_roles?.[0]?.title || exp.title || '',
        startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
        endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
        duration: exp.duration || '',
        location: exp.company_info?.location || exp.location || '',
        description: exp.company_roles?.[0]?.description || exp.description || ''
      })),
      education: (c.education || c.educations || []).map((edu: any) => ({
        school: edu.school || '',
        degree: edu.degree || '',
        field_of_study: edu.field_of_study || '',
        fieldOfStudy: edu.field_of_study || '',
        startDate: edu.start_date || '',
        endDate: edu.end_date || ''
      })),
      liaAnalysis: {
        score: c.match_score ? Math.round(c.match_score * 25) : (c.score || 75),
        strengths: c.match_reasoning ? [c.match_reasoning] : [],
        concerns: [],
        recommendation: c.match_reasoning || c.match_summary || ''
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
  }

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
              mappedCandidates = data.candidates.map((c: any) => mapCandidateToInternal(c))
            }
          } else {
            console.error('Erro na busca similar:', await response.text())
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
            mappedCandidates = data.candidates.map((c: any) => mapCandidateToInternal(c))
          }
        } else {
          console.error('Erro na busca por JD:', await response.text())
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
            mappedCandidates = data.candidates.map((c: any) => mapCandidateToInternal(c))
          }
        } else {
          console.error('Erro na busca por arquétipo:', await response.text())
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
              workHistory: (c.experiences || c.work_history || []).map((exp: any) => ({
                company: exp.company_info?.name || exp.company || '',
                title: exp.company_roles?.[0]?.title || exp.title || '',
                startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                duration: exp.duration || '',
                location: exp.company_info?.location || exp.location || '',
                description: exp.company_roles?.[0]?.description || exp.description || ''
              })),
              // Mapeamento de formação acadêmica da Pearch
              education: (c.education || c.educations || []).map((edu: any) => ({
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
            avatar: c.avatar_url || (c as any).picture_url,
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
        mode: (mode || 'natural') as any,
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
        console.log(`Créditos utilizados: ${creditsUsed}`)
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
          console.warn('Erro ao analisar resultados:', analyzeError)
        }
      }
    } catch (error) {
      console.error('Erro na busca:', error)
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

  // Handler para confirmar busca com Pearch (após modal de créditos)
  const handleConfirmPearchSearch = async () => {
    setShowCreditConfirmation(false)
    
    if (pendingSearchRequest) {
      await executeSearch(
        pendingSearchRequest.query,
        pendingSearchRequest.entities,
        pendingSearchRequest.mode,
        pendingSearchRequest.metadata,
        true // usePearch = true
      )
      setPendingSearchRequest(null)
    }
  }
  
  // Handler para mudança de fonte de busca com confirmação de créditos
  const handleSourceChange = (newSource: 'local' | 'hybrid' | 'global') => {
    if (newSource === 'local') {
      // Local é gratuito - muda direto
      setSearchSource('local')
    } else {
      // Híbrido ou Global consome créditos - mostrar modal de confirmação
      setPendingSourceChange(newSource)
      setShowSourceChangeModal(true)
    }
  }
  
  // Confirmar mudança de fonte após aceitar modal
  const confirmSourceChange = () => {
    if (pendingSourceChange) {
      const newSource = pendingSourceChange
      
      // Use flushSync to ensure state is committed before executing search
      flushSync(() => {
        setSearchSource(newSource)
        setPendingSourceChange(null)
        setShowSourceChangeModal(false)
      })
      
      // Now execute search with updated state
      if (lastSearchQuery && hasSearched) {
        // Use the new source to determine Pearch usage, but also respect previous search context
        const shouldUsePearch = newSource === 'global' || newSource === 'hybrid' || lastSearchUsedPearch
        executeSearch(
          lastSearchQuery,
          lastSearchEntities,
          lastSearchMode as SearchMode,
          lastSearchMetadata,
          shouldUsePearch
        )
      }
      
      toast({
        title: newSource === 'hybrid' ? 'Busca Híbrida ativada' : 'Busca Global ativada',
        description: 'Atualizando resultados com a nova configuração...',
      })
    } else {
      setShowSourceChangeModal(false)
    }
  }
  
  // Handler para mudança de filtro de contato com confirmação de créditos
  const handleContactFilterChange = (filterType: 'email' | 'phone') => {
    const isCurrentlyActive = filterType === 'email' 
      ? pearchSearchOptions.requireEmails 
      : pearchSearchOptions.requirePhoneNumbers
    
    if (isCurrentlyActive) {
      // Desativar filtro - não precisa confirmação
      if (filterType === 'email') {
        setPearchSearchOptions(prev => ({ ...prev, requireEmails: false }))
      } else {
        setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: false }))
      }
    } else {
      // Ativar filtro - mostrar modal de confirmação (consome créditos extras)
      setPendingContactFilter(filterType)
      setShowContactFilterModal(true)
    }
  }
  
  // Confirmar ativação de filtro de contato após aceitar modal
  const confirmContactFilterChange = () => {
    const filterType = pendingContactFilter
    
    // Use flushSync to ensure state is committed before executing search
    flushSync(() => {
      if (filterType === 'email') {
        setPearchSearchOptions(prev => ({ ...prev, requireEmails: true }))
      } else if (filterType === 'phone') {
        setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: true }))
      }
      setPendingContactFilter(null)
      setShowContactFilterModal(false)
    })
    
    // Now execute search with updated state - respect previous Pearch usage
    if (lastSearchQuery && hasSearched) {
      const shouldUsePearch = searchSource === 'global' || searchSource === 'hybrid' || lastSearchUsedPearch
      executeSearch(
        lastSearchQuery,
        lastSearchEntities,
        lastSearchMode as SearchMode,
        lastSearchMetadata,
        shouldUsePearch
      )
    }
    
    toast({
      title: filterType === 'email' ? 'Filtro de Email ativado' : 'Filtro de Telefone ativado',
      description: 'Atualizando resultados com o novo filtro...',
    })
  }

  const handleSearchFeedbackChange = (candidateId: string, feedback: 'like' | 'dislike' | null) => {
    setSearchFeedbacks(prev => {
      const updated = { ...prev }
      if (feedback === null) {
        delete updated[candidateId]
      } else {
        updated[candidateId] = feedback
      }
      return updated
    })
  }

  const handleLoadMore = async () => {
    setIsLoadingMore(true)
    await new Promise(resolve => setTimeout(resolve, 300))
    setDisplayedResultsCount(prev => prev + 10)
    setIsLoadingMore(false)
  }

  // Handler para expandir busca para global (Pearch AI)
  const handleExpandToGlobal = async () => {
    setShowGlobalExpansionConfirm(false)
    setIsExpandingToGlobal(true)
    
    try {
      // Reusar a última query bem-sucedida
      const queryToUse = lastSuccessfulQuery || lastSearchQuery
      
      if (!queryToUse) {
        toast({
          title: "Nenhuma busca ativa",
          description: "Execute uma busca local primeiro para poder expandir para busca global.",
          variant: "destructive"
        })
        return
      }
      
      // Construir SearchSpec a partir das entities salvas
      const searchSpec = lastSearchEntities ? {
        location: lastSearchEntities.location,
        job_title: lastSearchEntities.job_title,
        seniority: lastSearchEntities.seniority,
        years_experience: lastSearchEntities.years_experience,
        skills: lastSearchEntities.skills || [],
        industry: lastSearchEntities.industry,
        company: lastSearchEntities.company
      } : undefined
      
      // Executar busca global (Pearch AI)
      const searchResponse = await searchCandidatesHybrid({
        query: queryToUse,
        thread_id: searchThreadId,
        search_spec: searchSpec,
        search_local: true, // Manter local para híbrido
        search_pearch: true, // Adicionar busca global
        pearch_type: pearchSearchOptions.searchType,
        local_limit: 20,
        pearch_limit: pearchSearchOptions.limit,
        show_emails: pearchSearchOptions.showEmails,
        show_phone_numbers: pearchSearchOptions.showPhoneNumbers,
        high_freshness: pearchSearchOptions.highFreshness,
        require_emails: pearchSearchOptions.requireEmails,
        require_phone_numbers: pearchSearchOptions.requirePhoneNumbers
      })
      
      // Atualizar thread_id
      if (searchResponse.thread_id) {
        setSearchThreadId(searchResponse.thread_id)
      }
      
      // Atualizar saldo de créditos
      if (searchResponse.credits_remaining !== undefined && searchResponse.credits_remaining !== null) {
        setCreditsRemaining(searchResponse.credits_remaining)
      }
      
      // Mapear candidatos do Pearch para formato interno
      if (searchResponse.candidates && searchResponse.candidates.length > 0) {
        const mappedCandidates = searchResponse.candidates.map((c) => {
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
            avatar: c.avatar_url || c.picture_url,
            // Mapeamento de experiências profissionais da Pearch
            experiences: c.experiences || [],
            workHistory: (c.experiences || []).map((exp: any) => ({
              company: exp.company_info?.name || exp.company || '',
              title: exp.company_roles?.[0]?.title || exp.title || '',
              startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
              endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
              duration: exp.duration || '',
              location: exp.company_info?.location || exp.location || '',
              description: exp.company_roles?.[0]?.description || exp.description || ''
            })),
            // Mapeamento de formação acadêmica da Pearch
            education: (c.education || []).map((edu: any) => ({
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
        
        // Separar candidatos locais e globais
        const localCandidates = mappedCandidates.filter(c => !isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
        const globalCandidates = mappedCandidates.filter(c => isGlobalSource(c.source, Boolean(c.pearch_profile_id)))
        
        // Atualizar estados
        setCandidates(mappedCandidates)
        setCurrentSearchSource('hybrid')
        setSearchResultsCount(searchResponse.total_count || mappedCandidates.length)
        setLocalResultsCount(searchResponse.local_count || localCandidates.length)
        setPearchResultsCount(searchResponse.pearch_count || globalCandidates.length)
        setCreditsUsedInSearch(searchResponse.credits_used || 0)
        
        // Atualizar searchResults para exibição no painel LIA
        setSearchResults(prev => ({
          ...prev,
          local: localCandidates,
          global: globalCandidates,
          localCount: searchResponse.local_count || localCandidates.length,
          globalCount: searchResponse.pearch_count || globalCandidates.length,
          showGlobalResults: true
        }))
        
        // Notificar usuário
        toast({
          title: "Busca expandida com sucesso!",
          description: `Encontrados ${globalCandidates.length} candidatos adicionais na base global.`
        })
        
        // Adicionar mensagem no chat
        const liaMessage: ChatMessage = {
          id: `lia-expand-global-${Date.now()}`,
          type: 'lia',
          content: `🌐 **Busca expandida para base global**\n\nEncontrei mais **${globalCandidates.length} candidatos** na Busca Global!\n\nAgora você tem acesso a um pool ampliado de talentos para sua vaga.`,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, liaMessage])
        
        // 🎯 Chamar análise proativa após expansão para busca global
        if (mappedCandidates.length > 0) {
          try {
            const analyzeResponse = await fetch('/api/backend-proxy/search/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                query: queryToUse,
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
                  work_model: c.workModel || 'remoto',
                  email: c.email,
                  phone: c.phone || c.mobile_phone,
                  linkedin_url: c.linkedin_url,
                  source: c.source
                })),
                local_count: localCandidates.length,
                global_count: globalCandidates.length
              })
            })
            
            if (analyzeResponse.ok) {
              const analyticsData: SearchAnalytics = await analyzeResponse.json()
              
              // Inserir card de insights proativos no chat
              const insightMessage: ChatMessage = {
                id: `proactive-insight-global-${Date.now()}`,
                type: 'proactive_insight',
                content: '',
                timestamp: new Date(),
                analytics: analyticsData
              }
              setChatMessages(prev => [...prev, insightMessage])
            }
          } catch (analyzeError) {
            console.warn('Erro ao analisar resultados da busca global:', analyzeError)
          }
        }
      }
      
      setShowExpandGlobalOption(false)
      
    } catch (error) {
      console.error('Erro ao expandir busca para global:', error)
      toast({
        title: "Erro ao expandir busca",
        description: "Não foi possível expandir para busca global. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsExpandingToGlobal(false)
    }
  }

  // Estados para LIA micro-interação
  const [isLIAThinking, setIsLIAThinking] = useState(false)

  // 🎯 Handler para quick actions do ProactiveInsightCard
  const handleQuickAction = async (actionId: string, actionType: string) => {
    const liaMessage: ChatMessage = {
      id: `lia-action-${Date.now()}`,
      type: 'lia',
      content: '',
      timestamp: new Date()
    }
    
    switch (actionType) {
      case 'screening':
        liaMessage.content = '🎯 **Iniciando triagem em lote**\n\nPreparando triagem WSI para os candidatos selecionados...'
        setChatMessages(prev => [...prev, liaMessage])
        toast({
          title: "Triagem WSI",
          description: "Funcionalidade de triagem em lote será implementada em breve."
        })
        break
        
      case 'assign':
        liaMessage.content = '📋 **Atribuir candidatos a vaga**\n\nSelecione os candidatos e escolha a vaga para atribuição.'
        setChatMessages(prev => [...prev, liaMessage])
        if (candidates.length > 0) {
          setSelectedCandidatesForBatch(new Set(candidates.slice(0, 10).map(c => c.id)))
        }
        break
        
      case 'favorite':
        const candidateIds = candidates.slice(0, 10).map(c => c.id)
        candidateIds.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
        liaMessage.content = `⭐ **${candidateIds.length} candidatos adicionados aos favoritos**\n\nVocê pode acessá-los na aba "Favoritos".`
        setChatMessages(prev => [...prev, liaMessage])
        toast({
          title: "Favoritos atualizados",
          description: `${candidateIds.length} candidatos adicionados aos favoritos`,
        })
        break
        
      case 'whatsapp':
        liaMessage.content = '📱 **Contato via WhatsApp**\n\nPreparando mensagens personalizadas para contato...'
        setChatMessages(prev => [...prev, liaMessage])
        break
        
      case 'schedule':
        liaMessage.content = '📅 **Agendamento de entrevistas**\n\nAbrindo modal de agendamento em lote...'
        setChatMessages(prev => [...prev, liaMessage])
        setShowScheduleModal(true)
        break
        
      case 'refine':
        liaMessage.content = '🔍 **Refinar busca**\n\nDigite novos critérios para refinar sua busca.'
        setChatMessages(prev => [...prev, liaMessage])
        setLiaPromptValue('')
        break
        
      case 'export':
        liaMessage.content = '📊 **Exportando candidatos**\n\nPreparando arquivo para download...'
        setChatMessages(prev => [...prev, liaMessage])
        try {
          const exportData = candidates.map(c => ({
            nome: c.name,
            cargo: c.current_title || c.position,
            empresa: c.current_company,
            email: c.email,
            telefone: c.phone || c.mobile_phone,
            linkedin: c.linkedin_url,
            cidade: c.location_city || c.location,
            score: c.liaAnalysis?.score || c.score
          }))
          const csvContent = [
            Object.keys(exportData[0]).join(','),
            ...exportData.map(row => Object.values(row).map(v => `"${v || ''}"`).join(','))
          ].join('\n')
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `candidatos_${new Date().toISOString().split('T')[0]}.csv`
          link.click()
          
          const successMessage: ChatMessage = {
            id: `lia-export-success-${Date.now()}`,
            type: 'lia',
            content: `✅ **Exportação concluída!**\n\n${exportData.length} candidatos exportados para CSV.`,
            timestamp: new Date()
          }
          setChatMessages(prev => [...prev, successMessage])
        } catch (error) {
          console.error('Erro ao exportar:', error)
        }
        break
        
      default:
        liaMessage.content = `Ação "${actionId}" será implementada em breve.`
        setChatMessages(prev => [...prev, liaMessage])
    }
  }

  // 🎯 Handler para mensagens orquestradas do chat de talentos
  const handleOrchestratedTalentMessage = async (message: string): Promise<OrchestratedTalentChatResponse> => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    
    const candidatesForContext = candidates.slice(0, 50).map(c => ({
      id: c.id,
      name: c.name,
      current_title: c.current_title || c.position,
      current_company: c.current_company,
      location: c.location_city || c.location,
      skills: c.skills || [],
      experience_years: c.experience_years,
      lia_score: c.liaAnalysis?.score || c.score,
      wsi_score: c.wsi_score,
      source: c.source,
      // Campos adicionais para análises completas
      work_model: c.work_model_preference || c.workModel,
      is_remote: c.is_remote,
      willing_to_relocate: c.willing_to_relocate,
      salary_expectation_clt: c.salary_expectation_clt || c.desired_salary_min,
      salary_expectation_pj: c.salary_expectation_pj,
      languages: c.languages,
      seniority_level: c.seniority_level,
      gender: c.gender,
      status: c.status,
      is_active: c.is_active,
      technical_skills: c.technical_skills,
      soft_skills: c.soft_skills,
    }))
    
    const searchContextData = {
      query: searchResults.query || liaPromptValue,
      mode: activeSearchTab,
      total_results: searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0),
      local_results: searchResults.localCount,
      global_results: searchResults.globalCount,
      active_filters: activeSearchFilters
    }
    
    try {
      const response = await callOrchestratedTalentChat({
        message,
        candidates: candidatesForContext,
        selected_candidate_ids: selectedIds.length > 0 ? selectedIds : undefined,
        search_context: searchContextData,
        target_job: undefined,
        conversation_id: talentConversationId,
        company_id: user?.company || 'default',
      })
      if (response.conversation_id) {
        setTalentConversationId(response.conversation_id)
      }
      
      if (response.ui_action) {
        handleTalentUIAction(response.ui_action, response.ui_action_params)
      }
      
      if (response.action_executed && response.action_result) {
        toast({
          title: "Ação executada",
          description: response.action_type ? `${response.action_type} concluída com sucesso` : "Ação concluída com sucesso"
        })
      }
      
      return response
    } catch (error) {
      console.error('Orchestrated talent chat error:', error)
      return {
        success: false,
        content: 'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.',
        agent_used: 'Fallback',
        agents_consulted: [],
        intent_detected: 'error',
        confidence: 0,
        suggested_prompts: [],
        actions: [],
        ui_action: null
      }
    }
  }
  
  // 🎯 Handler para UI actions retornadas pelo orquestrador
  const handleTalentUIAction = (action: string, params?: Record<string, unknown>) => {
    switch (action) {
      case 'start_job_wizard':
        toast({
          title: "Criar Nova Vaga",
          description: "Abrindo wizard de criação de vaga..."
        })
        break
      case 'switch_search_mode':
        if (params?.mode && typeof params.mode === 'string') {
          setActiveSearchTab(params.mode as SearchTab)
        }
        break
      case 'open_communication_modal':
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0]
          const candidate = candidates.find(c => c.id === firstId)
          if (candidate) {
            setUnifiedModalCandidate(candidate)
            setUnifiedModalType('email')
            setUnifiedModalOpen(true)
          }
        }
        break
      case 'open_schedule_modal':
        setShowScheduleModal(true)
        break
      case 'open_screening_modal':
        if (selectedCandidatesForBatch.size > 0) {
          const firstId = Array.from(selectedCandidatesForBatch)[0]
          const candidate = candidates.find(c => c.id === firstId)
          if (candidate) {
            setUnifiedModalCandidate(candidate)
            setUnifiedModalType('triagem')
            setUnifiedModalOpen(true)
          }
        }
        break
      case 'trigger_export':
        handleQuickAction('export', 'export')
        break
      case 'open_add_to_list_modal':
        if (selectedCandidatesForBatch.size > 0) {
          setShowAddToListModal(true)
        }
        break
    }
  }

  // 🎯 Handlers para CalibrationCard
  const handleCalibrationLike = async (candidateId: string) => {
    try {
      await fetch('/api/backend-proxy/search/calibration/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: 'like',
          context: { source: 'chat_calibration' }
        })
      })
      
      toast({
        title: "Feedback registrado",
        description: "Candidato marcado como interessante",
      })
    } catch (error) {
      console.error('Erro ao enviar feedback:', error)
    }
  }

  const handleCalibrationDislike = async (candidateId: string, reason?: string) => {
    try {
      await fetch('/api/backend-proxy/search/calibration/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_id: candidateId,
          feedback: 'dislike',
          reason,
          context: { source: 'chat_calibration' }
        })
      })
      
      toast({
        title: "Feedback registrado",
        description: "Preferência salva para calibração",
      })
    } catch (error) {
      console.error('Erro ao enviar feedback:', error)
    }
  }

  // Estados para configuração de colunas
  const [showColumnConfig, setShowColumnConfig] = useState(false)
  const [tableColumns, setTableColumns] = useState([
    // ============================================
    // CAMPOS VISÍVEIS POR PADRÃO (11 colunas)
    // Match Score visível durante buscas para mostrar aderência
    // ============================================
    { id: 'feedback', label: '', visible: true, order: -2, width: 70, minWidth: 70, category: 'basico', sortable: false },
    { id: 'source', label: 'Fonte', visible: true, order: -1, category: 'basico' },
    { id: 'match_score', label: 'Match', visible: true, order: -0.5, category: 'ia' },
    { id: 'name', label: 'Candidato', visible: true, order: 0, category: 'basico' },
    { id: 'current_title', label: 'Cargo atual', visible: true, order: 1, category: 'profissional' },
    { id: 'current_company', label: 'Empresa atual', visible: true, order: 2, category: 'profissional' },
    { id: 'current_salary', label: 'Salário atual', visible: true, order: 3, category: 'salario' },
    { id: 'desired_salary_max', label: 'Expectativa salarial', visible: true, order: 4, category: 'salario' },
    { id: 'mobile_phone', label: 'Celular', visible: true, order: 5, category: 'contato' },
    { id: 'email', label: 'E-mail', visible: true, order: 6, category: 'contato' },
    { id: 'location_city', label: 'Cidade', visible: true, order: 7, category: 'localizacao' },
    { id: 'linkedin_url', label: 'LinkedIn', visible: true, order: 8, category: 'contato' },

    // ============================================
    // IDENTIFICAÇÃO E CONTATO (campos do banco)
    // ============================================
    { id: 'id', label: 'ID do candidato', visible: false, order: 9, category: 'basico' },
    { id: 'secondary_email', label: 'E-mail secundário', visible: false, order: 10, category: 'contato' },
    { id: 'phone', label: 'Telefone fixo', visible: false, order: 11, category: 'contato' },
    { id: 'secondary_phone', label: 'Telefone adicional', visible: false, order: 12, category: 'contato' },
    { id: 'github_url', label: 'GitHub', visible: false, order: 13, category: 'contato' },
    { id: 'portfolio_url', label: 'Portfólio', visible: false, order: 14, category: 'contato' },

    // ============================================
    // INFORMAÇÕES PESSOAIS (campos do banco)
    // ============================================
    { id: 'date_of_birth', label: 'Data de nascimento', visible: false, order: 15, category: 'pessoal' },
    { id: 'gender', label: 'Gênero', visible: false, order: 17, category: 'pessoal' },
    { id: 'nationality', label: 'Nacionalidade', visible: false, order: 18, category: 'pessoal' },
    { id: 'marital_status', label: 'Estado civil', visible: false, order: 19, category: 'pessoal' },
    { id: 'cpf', label: 'CPF', visible: false, order: 20, category: 'pessoal' },

    // ============================================
    // PERFIL PROFISSIONAL (campos do banco)
    // ============================================
    { id: 'seniority_level', label: 'Nível de senioridade', visible: false, order: 21, category: 'profissional' },
    { id: 'years_of_experience', label: 'Anos de experiência', visible: false, order: 22, category: 'profissional' },
    { id: 'self_introduction', label: 'Autoapresentação', visible: false, order: 23, category: 'profissional' },

    // ============================================
    // COMPETÊNCIAS E HABILIDADES (campos do banco)
    // ============================================
    { id: 'technical_skills', label: 'Habilidades técnicas', visible: false, order: 24, category: 'competencias' },
    { id: 'soft_skills', label: 'Soft skills', visible: false, order: 25, category: 'competencias' },
    { id: 'languages', label: 'Idiomas', visible: false, order: 26, category: 'competencias' },
    { id: 'certifications', label: 'Certificações', visible: false, order: 27, category: 'competencias' },
    { id: 'interests', label: 'Interesses', visible: false, order: 28, category: 'competencias' },
    { id: 'education', label: 'Formação acadêmica', visible: false, order: 28.5, category: 'competencias' },

    // ============================================
    // LOCALIZAÇÃO - CIDADE/ESTADO/PAÍS (campos do banco)
    // ============================================
    { id: 'location_state', label: 'Estado', visible: false, order: 29, category: 'localizacao' },
    { id: 'location_country', label: 'País', visible: false, order: 30, category: 'localizacao' },

    // ============================================
    // ENDEREÇO COMPLETO (campos do banco)
    // ============================================
    { id: 'address_street', label: 'Endereço – Rua', visible: false, order: 31, category: 'endereco' },
    { id: 'address_number', label: 'Endereço – Número', visible: false, order: 32, category: 'endereco' },
    { id: 'address_district', label: 'Endereço – Bairro', visible: false, order: 33, category: 'endereco' },
    { id: 'address_zip', label: 'Endereço – CEP', visible: false, order: 34, category: 'endereco' },
    { id: 'address_complement', label: 'Endereço – Complemento', visible: false, order: 35, category: 'endereco' },

    // ============================================
    // PREFERÊNCIAS DE TRABALHO (campos do banco)
    // ============================================
    { id: 'is_remote', label: 'Aceita remoto', visible: false, order: 36, category: 'preferencias' },
    { id: 'willing_to_relocate', label: 'Aceita mudança', visible: false, order: 37, category: 'preferencias' },
    { id: 'mobility', label: 'Disponibilidade para viagens', visible: false, order: 38, category: 'preferencias' },
    { id: 'work_model_preference', label: 'Modelo de trabalho preferido', visible: false, order: 39, category: 'preferencias' },
    { id: 'contract_type_preference', label: 'Tipo de contrato preferido', visible: false, order: 40, category: 'preferencias' },

    // ============================================
    // SALÁRIO E EXPECTATIVAS (campos do banco)
    // ============================================
    { id: 'salary_currency', label: 'Moeda do salário', visible: false, order: 41, category: 'salario' },
    { id: 'desired_salary_min', label: 'Salário mínimo desejado', visible: false, order: 42, category: 'salario' },
    // desired_salary_max já definido acima na order: 4 como 'Expectativa salarial'
    { id: 'salary_expectation_clt', label: 'Expectativa salarial CLT', visible: false, order: 43, category: 'salario' },
    { id: 'salary_expectation_pj', label: 'Expectativa salarial PJ', visible: false, order: 45, category: 'salario' },
    { id: 'salary_expectation_freelance', label: 'Expectativa salarial Freelance', visible: false, order: 46, category: 'salario' },

    // ============================================
    // CURRÍCULO E DOCUMENTOS (campos do banco)
    // ============================================
    { id: 'resume_url', label: 'Currículo (URL)', visible: false, order: 47, category: 'documentos' },
    { id: 'resume_text', label: 'Currículo (texto)', visible: false, order: 48, category: 'documentos' },
    { id: 'cover_letter', label: 'Carta de apresentação', visible: false, order: 49, category: 'documentos' },

    // ============================================
    // ORIGEM E INTEGRAÇÃO (campos do banco)
    // ============================================
    { id: 'source', label: 'Fonte de cadastro', visible: false, order: 50, category: 'origem' },
    { id: 'ats_source_name', label: 'Nome do ATS', visible: false, order: 51, category: 'origem' },
    { id: 'ats_candidate_id', label: 'ID no ATS', visible: false, order: 52, category: 'origem' },
    { id: 'pearch_profile_id', label: 'ID na Base Global', visible: false, order: 53, category: 'origem' },

    // ============================================
    // BUSCA GLOBAL / PEARCH (campos exclusivos da busca global)
    // ============================================
    { id: 'is_open_to_work', label: 'Open to Work', visible: false, order: 54, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_decision_maker', label: 'Decision Maker', visible: false, order: 55, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_top_universities', label: 'Top Universities', visible: false, order: 56, category: 'busca_global', isGlobalSearch: true },
    { id: 'is_hiring', label: 'Está contratando', visible: false, order: 57, category: 'busca_global', isGlobalSearch: true },
    { id: 'headline', label: 'Headline LinkedIn', visible: false, order: 58, category: 'busca_global', isGlobalSearch: true },
    { id: 'expertise', label: 'Expertise', visible: false, order: 59, category: 'busca_global', isGlobalSearch: true },
    { id: 'linkedin_followers_count', label: 'Seguidores LinkedIn', visible: false, order: 60, category: 'busca_global', isGlobalSearch: true },
    { id: 'linkedin_connections_count', label: 'Conexões LinkedIn', visible: false, order: 61, category: 'busca_global', isGlobalSearch: true },
    { id: 'outreach_message', label: 'Mensagem de Abordagem', visible: false, order: 62, category: 'busca_global', isGlobalSearch: true },
    { id: 'best_personal_email', label: 'Melhor Email Pessoal', visible: false, order: 63, category: 'busca_global', isGlobalSearch: true },
    { id: 'phone_types', label: 'Tipos de Telefone', visible: false, order: 64, category: 'busca_global', isGlobalSearch: true },
    { id: 'estimated_age', label: 'Idade Estimada', visible: false, order: 65, category: 'busca_global', isGlobalSearch: true },
    { id: 'match_reasoning', label: 'Justificativa do Match', visible: false, order: 66, category: 'busca_global', isGlobalSearch: true },
    { id: 'overall_summary', label: 'Resumo Geral', visible: false, order: 67, category: 'busca_global', isGlobalSearch: true },
    { id: 'query_insights', label: 'Insights por Requisito', visible: false, order: 68, category: 'busca_global', isGlobalSearch: true },
    { id: 'pearch_insights', label: 'Insights Pearch', visible: false, order: 69, category: 'busca_global', isGlobalSearch: true },
    { id: 'middle_name', label: 'Nome do Meio', visible: false, order: 70, category: 'busca_global', isGlobalSearch: true },
    { id: 'best_business_email', label: 'Email Corporativo', visible: false, order: 71, category: 'busca_global', isGlobalSearch: true },
    { id: 'personal_emails', label: 'Emails Pessoais', visible: false, order: 72, category: 'busca_global', isGlobalSearch: true },
    { id: 'business_emails', label: 'Emails Corporativos', visible: false, order: 73, category: 'busca_global', isGlobalSearch: true },
    { id: 'company_followers_count', label: 'Seguidores da Empresa', visible: false, order: 74, category: 'busca_global', isGlobalSearch: true },
    { id: 'company_keywords', label: 'Palavras-chave da Empresa', visible: false, order: 75, category: 'busca_global', isGlobalSearch: true },

    // ============================================
    // INSIGHTS LIA / IA (campos do banco)
    // Score LIA só aparece para candidatos que participaram de processo
    // ============================================
    { id: 'lia_score', label: 'Score LIA', visible: false, order: 64, category: 'ia' },
    { id: 'lia_insights', label: 'Insights LIA', visible: false, order: 65, category: 'ia' },
    { id: 'skills_match_percentage', label: '% Match de habilidades', visible: false, order: 66, category: 'ia' },

    // ============================================
    // STATUS E WORKFLOW (campos do banco)
    // ============================================
    { id: 'status', label: 'Status no pipeline', visible: false, order: 56, category: 'status' },
    { id: 'is_active', label: 'Ativo no sistema', visible: false, order: 57, category: 'status' },
    { id: 'is_blacklisted', label: 'LCNU', visible: false, order: 58, category: 'status' },
    { id: 'blacklist_reason', label: 'Motivo LCNU', visible: false, order: 59, category: 'status' },

    // ============================================
    // COMUNICAÇÃO (campos do banco)
    // ============================================
    { id: 'preferred_contact_method', label: 'Método de contato preferido', visible: false, order: 60, category: 'comunicacao' },
    { id: 'best_time_to_contact', label: 'Melhor horário para contato', visible: false, order: 61, category: 'comunicacao' },
    { id: 'communication_consent', label: 'Consentimento LGPD', visible: false, order: 62, category: 'comunicacao' },

    // ============================================
    // STATUS DE CADASTRO (campos do banco)
    // ============================================
    { id: 'completed_register', label: 'Cadastro completo', visible: false, order: 63, category: 'cadastro' },
    { id: 'accept_terms', label: 'Aceite dos termos', visible: false, order: 64, category: 'cadastro' },

    // ============================================
    // INFORMAÇÕES ADICIONAIS (campos do banco)
    // ============================================
    { id: 'tags', label: 'Tags', visible: false, order: 65, category: 'adicional' },
    { id: 'notes', label: 'Notas internas', visible: false, order: 66, category: 'adicional' },
    { id: 'additional_data', label: 'Dados adicionais', visible: false, order: 67, category: 'adicional' },

    // ============================================
    // TIMESTAMPS (campos do banco)
    // ============================================
    { id: 'created_at', label: 'Data de cadastro', visible: false, order: 68, category: 'datas' },
    { id: 'updated_at', label: 'Última atualização', visible: false, order: 69, category: 'datas' },
    { id: 'last_contacted_at', label: 'Último contato', visible: false, order: 70, category: 'datas' },
    { id: 'last_activity_at', label: 'Última atividade', visible: false, order: 71, category: 'datas' },

    { id: 'acoes', label: 'Ações', visible: true, order: 0.5, category: 'basico' }
  ])
  const [savedColumnViews, setSavedColumnViews] = useState([
    {
      id: '1',
      name: 'Visualização Padrão',
      columns: [
        { id: 'name', label: 'Nome completo', visible: true, order: 0 },
        { id: 'score_lia', label: 'Score LIA', visible: true, order: 1 },
        { id: 'role_name', label: 'Cargo atual', visible: true, order: 2 },
        { id: 'current_company', label: 'Empresa atual', visible: true, order: 3 },
        { id: 'city', label: 'Cidade', visible: true, order: 4 },
      ],
      createdAt: '2025-01-01T00:00:00.000Z'
    }
  ])

  // Estados de busca avançada
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false) // Modal de filtros na busca inicial
  // showTableFiltersPanel, tableFilters, newSoftSkillFilter, newCertificationFilter → useCandidateFilters()
  const [booleanSearch, setBooleanSearch] = useState("")
  const [selectedTemplate, setSelectedTemplate] = useState("")
  const [showSearchHistory, setShowSearchHistory] = useState(false)
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [savedSearches, setSavedSearches] = useState<any[]>([])
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['tech_positions']))
  const [columnSearchTerm, setColumnSearchTerm] = useState("")

  // Estados de filtros avançados
  const [advancedFilters, setAdvancedFilters] = useState<{[key: string]: string[]}>({
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

  // columnFilters, openFilterDropdown → useCandidateFilters()

  // Estados de redimensionamento de colunas - todas as 72 colunas
  const [columnWidths, setColumnWidths] = useState<Record<string, number>>({
    // Colunas fixas
    checkbox: 50,
    acoes: 120,
    
    // Básico
    source: 60,
    name: 220,
    id: 100,
    
    // Contato
    email: 200,
    secondary_email: 200,
    phone: 130,
    mobile_phone: 130,
    secondary_phone: 130,
    linkedin_url: 60,
    github_url: 150,
    portfolio_url: 150,
    
    // Pessoal
    date_of_birth: 120,
    gender: 100,
    nationality: 130,
    marital_status: 120,
    cpf: 130,
    
    // Match / Aderência
    match_score: 50,
    
    // Profissional
    current_title: 250,
    current_company: 150,
    seniority_level: 130,
    years_of_experience: 100,
    self_introduction: 200,
    
    // IA
    lia_score: 100,
    lia_insights: 200,
    skills_match_percentage: 100,
    
    // Competências
    technical_skills: 200,
    soft_skills: 180,
    languages: 150,
    certifications: 180,
    interests: 150,
    education: 200,
    
    // Localização
    location_city: 120,
    location_state: 100,
    location_country: 100,
    
    // Endereço
    address_street: 180,
    address_number: 80,
    address_district: 120,
    address_zip: 100,
    address_complement: 150,
    
    // Preferências
    is_remote: 100,
    willing_to_relocate: 100,
    mobility: 100,
    work_model_preference: 130,
    contract_type_preference: 130,
    
    // Salário
    current_salary: 130,
    salary_currency: 80,
    desired_salary_min: 130,
    desired_salary_max: 130,
    salary_expectation_clt: 130,
    salary_expectation_pj: 130,
    salary_expectation_freelance: 130,
    
    // Documentos
    resume_url: 150,
    resume_text: 200,
    cover_letter: 200,
    
    // Origem
    source: 120,
    ats_source_name: 120,
    ats_candidate_id: 120,
    pearch_profile_id: 120,
    
    // Busca Global / Pearch
    is_open_to_work: 100,
    is_decision_maker: 120,
    is_top_universities: 130,
    is_hiring: 100,
    headline: 250,
    expertise: 200,
    linkedin_followers_count: 120,
    linkedin_connections_count: 120,
    outreach_message: 300,
    best_personal_email: 180,
    phone_types: 150,
    estimated_age: 100,
    match_reasoning: 300,
    overall_summary: 300,
    query_insights: 350,
    pearch_insights: 200,
    middle_name: 120,
    best_business_email: 200,
    personal_emails: 180,
    business_emails: 180,
    company_followers_count: 130,
    company_keywords: 200,
    
    // Status
    status: 120,
    is_active: 80,
    is_blacklisted: 100,
    blacklist_reason: 150,
    
    // Comunicação
    preferred_contact_method: 130,
    best_time_to_contact: 130,
    communication_consent: 100,
    
    // Cadastro
    completed_register: 100,
    accept_terms: 100,
    
    // Adicional
    tags: 150,
    notes: 200,
    additional_data: 150,
    
    // Datas
    created_at: 130,
    updated_at: 130,
    last_contacted_at: 130,
    last_activity_at: 130
  })

  // Estados para drag & drop de colunas
  const [draggedColumnId, setDraggedColumnId] = useState<string | null>(null)
  const [dragOverColumnId, setDragOverColumnId] = useState<string | null>(null)
  
  // Ordem das colunas da tabela
  const [columnOrder, setColumnOrder] = useState<string[]>([
    'checkbox', 'id', 'candidato', 'cargo', 'empresa', 'salario_mensal', 'localizacao', 'modelo_trabalho', 'acoes'
  ])

  // Helper para verificar se uma coluna está visível
  const isColumnVisible = (columnId: string) => {
    const column = tableColumns.find(col => col.id === columnId)
    return column ? column.visible : false
  }

  // Derivar colunas visíveis ordenadas
  const visibleTableColumns = tableColumns
    .filter(col => col.visible)
    .sort((a, b) => a.order - b.order)

  // Helper para renderizar valor de célula genérica
  const renderCellValue = (candidate: Candidate, columnId: string) => {
    const formatDate = (date: string | undefined) => {
      if (!date) return 'N/A'
      return new Date(date).toLocaleDateString('pt-BR')
    }
    
    const formatCurrency = (value: number | undefined, currency?: string) => {
      if (!value) return 'N/A'
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: currency || 'BRL'
      }).format(value)
    }

    const formatBoolean = (value: boolean | undefined) => {
      if (value === undefined) return 'N/A'
      return value ? 'Sim' : 'Não'
    }

    const formatArray = (arr: string[] | undefined) => {
      if (!arr || arr.length === 0) return 'N/A'
      return arr.slice(0, 3).join(', ') + (arr.length > 3 ? ` (+${arr.length - 3})` : '')
    }

    const formatLanguages = (langs: Record<string, string> | undefined) => {
      if (!langs) return 'N/A'
      const entries = Object.entries(langs)
      if (entries.length === 0) return 'N/A'
      return entries.slice(0, 2).map(([lang, level]) => `${lang}: ${level}`).join(', ')
    }

    switch (columnId) {
      case 'checkbox':
      case 'acoes':
      case 'actions':
        return null

      case 'feedback':
        const hasFeedback = !!searchFeedbacks[candidate.id]
        return (
          <div className={cn(
            "flex items-center justify-center transition-opacity duration-200",
            hasFeedback ? "opacity-100" : "opacity-0 group-hover:opacity-100"
          )}>
            <SearchFeedbackButtons
              candidateId={candidate.id}
              candidateName={candidate.name}
              candidateScore={candidate.match_score || candidate.lia_score || candidate.score}
              initialFeedback={searchFeedbacks[candidate.id] || null}
              onFeedbackChange={handleSearchFeedbackChange}
              size="sm"
              alwaysVisible={hasFeedback}
            />
          </div>
        )
      
      // Fonte (Local vs Global) - Com tooltips dinâmicos usando utilitário centralizado
      case 'source':
        const hasPearchId = !!candidate.pearch_profile_id
        const sourceInfo = getSourceDetails(candidate.source, hasPearchId)
        const isLocal = sourceInfo.isLocal
        
        return (
          <div className="relative group flex items-center justify-center cursor-help">
            {isLocal ? (
              <div className="w-6 h-6 rounded-full flex items-center justify-center transition-all hover:scale-110" style={{ backgroundColor: 'rgba(180, 160, 140, 0.2)' }}>
                <Home className="w-3.5 h-3.5" style={{ color: '#A08060' }} />
              </div>
            ) : (
              <div className="w-6 h-6 rounded-full flex items-center justify-center transition-all hover:scale-110 bg-gray-100 dark:bg-gray-700">
                <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-300" />
              </div>
            )}
            {/* Tooltip dinâmico com informações de créditos */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 pointer-events-none">
              <div className="px-3 py-2 rounded-md text-xs min-w-[180px] text-white bg-gray-900">
                <div className="font-semibold mb-1 flex items-center gap-1.5">
                  {isLocal ? (
                    <Home className="w-3.5 h-3.5" style={{ color: '#E8946C' }} />
                  ) : (
                    <Globe className="w-3.5 h-3.5 text-gray-300" />
                  )}
                  {sourceInfo.label}
                </div>
                <div className="text-xs text-gray-500 mb-1">
                  {sourceInfo.subtext}
                </div>
                {isLocal ? (
                  <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700 text-wedo-green-light">
                    <CheckCircle className="w-3 h-3" />
                    Sem consumo de créditos
                  </div>
                ) : (
                  <div className="text-xs font-medium flex items-center gap-1 mt-1.5 pt-1.5 border-t border-gray-700" style={{ color: 'var(--status-warning)' }}>
                    <DollarSign className="w-3 h-3" />
                    {sourceInfo.credits || '5-7 créditos/candidato'}
                  </div>
                )}
                <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
              </div>
            </div>
          </div>
        )
      
      // Match Score - Aderência à busca (Ring Progress)
      case 'match_score':
        const matchScore = candidate.score || 0
        const hasActiveSearch = searchResults.query && searchResults.query.length > 0
        
        // Se não há busca ativa, não mostrar score
        if (!hasActiveSearch || matchScore === 0) {
          return (
            <div className="flex items-center justify-center">
              <span className={textStyles.label}>—</span>
            </div>
          )
        }
        
        // Cores baseadas no score (paleta harmonizada)
        const getMatchRingColor = (score: number) => {
          if (score >= 85) return 'var(--gray-600)' // teal - excelente
          if (score >= 70) return 'var(--wedo-green-light)' // verde claro - bom
          if (score >= 50) return '#E8A07C' // coral - moderado
          return 'var(--gray-400)' // gray-400 - baixo
        }
        
        const ringColor = getMatchRingColor(matchScore)
        const ringSize = 32
        const strokeWidth = 3
        const radius = (ringSize - strokeWidth) / 2
        const circumference = radius * 2 * Math.PI
        const strokeDashoffset = circumference - (matchScore / 100) * circumference
        
        return (
          <div className="flex items-center justify-center">
            <div className="relative" style={{ width: ringSize, height: ringSize }}>
              {/* Background ring */}
              <svg className="absolute" width={ringSize} height={ringSize}>
                <circle
                  cx={ringSize / 2}
                  cy={ringSize / 2}
                  r={radius}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={strokeWidth}
                  className="text-gray-500 dark:text-gray-500"
                />
              </svg>
              {/* Progress ring */}
              <svg 
                className="absolute -rotate-90" 
                width={ringSize} 
                height={ringSize}
              >
                <circle
                  cx={ringSize / 2}
                  cy={ringSize / 2}
                  r={radius}
                  fill="none"
                  stroke={ringColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                  className="transition-all duration-300"
                />
              </svg>
              {/* Percentage text */}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`${textStyles.label} font-bold dark:text-gray-200`}>
                  {matchScore}
                </span>
              </div>
            </div>
          </div>
        )
        
      // Básico
      case 'name':
        const hasPearchBadges = candidate.is_opentowork || candidate.is_decision_maker || candidate.is_top_universities || candidate.is_startup
        const isCandidateViewed = viewedCandidateIds.has(candidate.id)
        return (
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <Avatar className="w-9 h-9">
                <AvatarImage
                  src={candidate.avatar_url || candidate.avatar || candidate.photo_url || candidate.picture_url || candidate.photoUrl || candidate.profile_picture}
                  alt={candidate.name}
                />
                <AvatarFallback className="text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                  {candidate.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              {isCandidateViewed && (
                <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                  <Eye className="w-2.5 h-2.5 text-white" />
                </div>
              )}
            </div>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-gray-950 dark:text-gray-200 truncate text-xs">{candidate.name}</span>
              </div>
            </div>
          </div>
        )
      case 'id':
        return <span className="font-mono text-xs text-gray-800">{candidate.candidateId || candidate.id}</span>
      // IA
      case 'lia_score':
        const score = candidate.lia_score || 0
        const hasBeenEvaluated = candidate.lia_score && candidate.lia_score > 0

        if (!hasBeenEvaluated) {
          return (
            <div className="relative group cursor-help">
              <span className="text-xs text-gray-800">—</span>
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50">
                <div className="bg-gray-900 dark:bg-gray-700 text-white px-3 py-2 rounded-md text-xs min-w-[180px]">
                  <div className="font-semibold mb-1.5 flex items-center gap-1.5">
                    <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                    Sem avaliação
                  </div>
                  <div className="text-xs text-gray-500">
                    Este candidato ainda não participou de nenhum processo seletivo.
                  </div>
                  <div className="text-xs text-gray-800 mt-1.5">
                    O Score LIA é calculado quando o candidato é avaliado para uma vaga específica.
                  </div>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></div>
                </div>
              </div>
            </div>
          )
        }
        
        return (
          <ScoreBreakdownBadgeLazy
            score={score}
            candidateId={candidate.id}
            jobId={(candidate.additional_data?.job_id as string) ?? ""}
            size="sm"
          />
        )
      case 'lia_insights':
        const insights = candidate.lia_insights
        return <span className="text-xs text-gray-800 truncate">{insights?.overall_summary?.slice(0, 50) || ''}{insights?.overall_summary && insights.overall_summary.length > 50 ? '...' : ''}</span>
      case 'skills_match_percentage':
        return <span className="text-xs">{candidate.skills_match_percentage ? `${candidate.skills_match_percentage}%` : ''}</span>

      // Contato - Com sistema de reveal para candidatos Pearch
      case 'email':
        const candidateEmail = revealedContacts[candidate.id]?.email || candidate.email
        // IMPORTANTE: Usar isGlobalSource para determinar se é candidato Pearch elegível para reveal
        const canRevealEmail = isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) && candidate.has_email !== false
        
        if (candidateEmail) {
          return <span className="text-xs text-gray-800 truncate">{candidateEmail}</span>
        }
        
        if (canRevealEmail) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                openRevealModal(candidate, 'email')
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
              title="Clique para revelar email (2 créditos)"
            >
              <Mail className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(2 cr)</span>
            </button>
          )
        }
        
        return <span className="text-xs text-gray-800">-</span>
      case 'secondary_email':
        return <span className="text-xs text-gray-800 truncate">{candidate.secondary_email || ''}</span>
      case 'phone':
        const candidatePhone = revealedContacts[candidate.id]?.phone || candidate.phone
        // IMPORTANTE: Usar isGlobalSource para determinar se é candidato Pearch elegível para reveal
        const canRevealPhone = isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) && candidate.has_phone !== false
        
        if (candidatePhone) {
          return <span className="text-xs text-gray-800">{candidatePhone}</span>
        }
        
        if (canRevealPhone) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                openRevealModal(candidate, 'phone')
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
              title="Clique para revelar telefone (14 créditos)"
            >
              <Phone className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(14 cr)</span>
            </button>
          )
        }
        
        return <span className="text-xs text-gray-800">-</span>
      case 'mobile_phone':
        const candidateMobile = revealedContacts[candidate.id]?.phone || candidate.mobile_phone || candidate.phone
        // IMPORTANTE: Usar isGlobalSource para determinar se é candidato Pearch elegível para reveal
        const canRevealMobile = isGlobalSource(candidate.source, Boolean(candidate.pearch_profile_id)) && candidate.has_phone !== false
        
        if (candidateMobile) {
          return <span className="text-xs text-gray-800">{candidateMobile}</span>
        }
        
        if (canRevealMobile) {
          return (
            <button
              onClick={(e) => {
                e.stopPropagation()
                openRevealModal(candidate, 'phone')
              }}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-medium rounded-full bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
              title="Clique para revelar celular (14 créditos)"
            >
              <Phone className="w-3 h-3" />
              <span>Revelar</span>
              <span className="opacity-60">(14 cr)</span>
            </button>
          )
        }
        
        return <span className="text-xs text-gray-800">-</span>
      case 'secondary_phone':
        return <span className="text-xs text-gray-800">{candidate.secondary_phone || ''}</span>
      case 'linkedin_url':
        return candidate.linkedin_url ? (
          <a 
            href={candidate.linkedin_url} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="inline-flex items-center justify-center w-6 h-6 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Ver perfil no LinkedIn"
          >
            <Linkedin className="w-4 h-4 text-[#0A66C2]" />
          </a>
        ) : (
          <span className="inline-flex items-center justify-center w-6 h-6" title="LinkedIn não informado">
            <Linkedin className="w-4 h-4 text-gray-500 dark:text-gray-500" />
          </span>
        )
      case 'github_url':
        return candidate.github_url ? (
          <a href={candidate.github_url} target="_blank" rel="noopener" className="text-gray-800 hover:underline text-xs flex items-center gap-1">
            <Github className="w-3 h-3" /> GitHub
          </a>
        ) : <span className="text-xs text-gray-800">N/A</span>
      case 'portfolio_url':
        return candidate.portfolio_url ? (
          <a href={candidate.portfolio_url} target="_blank" rel="noopener" className="text-purple-600 hover:underline text-xs flex items-center gap-1">
            <Globe className="w-3 h-3" /> Portfólio
          </a>
        ) : <span className="text-xs text-gray-800">N/A</span>

      // Pessoal
      case 'date_of_birth':
        return <span className="text-xs text-gray-800">{formatDate(candidate.date_of_birth)}</span>
      case 'gender':
        return <span className="text-xs text-gray-800">{candidate.gender || ''}</span>
      case 'nationality':
        return <span className="text-xs text-gray-800">{candidate.nationality || ''}</span>
      case 'marital_status':
        return <span className="text-xs text-gray-800">{candidate.marital_status || ''}</span>
      case 'cpf':
        return <span className="text-xs text-gray-800 font-mono">{candidate.cpf || ''}</span>

      // Profissional
      case 'current_title':
        const titleText = candidate.current_title || candidate.position || ''
        const isRowExpanded = expandedRows.has(candidate.id)
        const titleNeedsTruncation = titleText.length > 40
        
        return (
          <div className="flex items-start gap-1 max-w-[250px]">
            <span 
              className={`text-xs text-gray-800 font-medium ${isRowExpanded ? 'whitespace-normal break-words' : 'truncate'}`}
              title={titleText}
            >
              {titleText}
            </span>
            {titleNeedsTruncation && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setExpandedRows(prev => {
                    const newSet = new Set(prev)
                    if (newSet.has(candidate.id)) {
                      newSet.delete(candidate.id)
                    } else {
                      newSet.add(candidate.id)
                    }
                    return newSet
                  })
                }}
                className="flex-shrink-0 p-0.5 rounded hover:bg-gray-100 transition-colors"
                title={isRowExpanded ? "Recolher texto" : "Expandir texto"}
              >
                <ChevronsLeftRight className={`w-3 h-3 text-gray-800 hover:text-gray-800 transition-transform ${isRowExpanded ? 'rotate-90' : ''}`} />
              </button>
            )}
          </div>
        )
      case 'current_company':
        return <span className="text-xs text-gray-800 truncate">{candidate.current_company || candidate.workHistory?.[0]?.company || ''}</span>
      case 'seniority_level':
        return <Badge variant="outline" className="text-xs">{candidate.seniority_level || ''}</Badge>
      case 'years_of_experience':
        return <span className="text-xs text-gray-800">{candidate.years_of_experience !== undefined ? `${candidate.years_of_experience} anos` : ''}</span>
      case 'self_introduction':
        return <span className="text-xs text-gray-800 truncate">{candidate.self_introduction?.slice(0, 50) || ''}{candidate.self_introduction && candidate.self_introduction.length > 50 ? '...' : ''}</span>

      // Competências
      case 'technical_skills':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.technical_skills || candidate.skills)}</span>
      case 'soft_skills':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.soft_skills)}</span>
      case 'languages':
        return <span className="text-xs text-gray-800 truncate">{formatLanguages(candidate.languages)}</span>
      case 'certifications':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.certifications)}</span>
      case 'interests':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.interests)}</span>
      case 'education':
        const educationData = candidate.education || candidate.educations
        if (Array.isArray(educationData) && educationData.length > 0) {
          const firstEdu = educationData[0]
          return <span className="text-xs text-gray-800 truncate">{firstEdu.degree || firstEdu.course || ''}{firstEdu.institution ? ` - ${firstEdu.institution}` : ''}</span>
        }
        return <span className="text-xs text-gray-800">—</span>

      // Localização
      case 'location_city':
        return (
          <div className="flex items-center gap-1">
            <MapPin className="w-3 h-3 text-gray-800" />
            <span className="text-xs text-gray-800 truncate">{candidate.location_city || candidate.location?.split(',')[0] || ''}</span>
          </div>
        )
      case 'location_state':
        return <span className="text-xs text-gray-800">{candidate.location_state || ''}</span>
      case 'location_country':
        return <span className="text-xs text-gray-800">{candidate.location_country || ''}</span>

      // Endereço
      case 'address_street':
        return <span className="text-xs text-gray-800 truncate">{candidate.address_street || ''}</span>
      case 'address_number':
        return <span className="text-xs text-gray-800">{candidate.address_number || ''}</span>
      case 'address_district':
        return <span className="text-xs text-gray-800 truncate">{candidate.address_district || ''}</span>
      case 'address_zip':
        return <span className="text-xs text-gray-800 font-mono">{candidate.address_zip || ''}</span>
      case 'address_complement':
        return <span className="text-xs text-gray-800 truncate">{candidate.address_complement || ''}</span>

      // Preferências
      case 'is_remote':
        return (
          <Badge variant="outline" className={`text-xs ${candidate.is_remote ? 'bg-green-50 text-green-700 border-green-200' : ''}`}>
            {formatBoolean(candidate.is_remote)}
          </Badge>
        )
      case 'willing_to_relocate':
        return <span className="text-xs text-gray-800">{formatBoolean(candidate.willing_to_relocate)}</span>
      case 'mobility':
        return <span className="text-xs text-gray-800">{formatBoolean(candidate.mobility)}</span>
      case 'work_model_preference':
        const workModel = candidate.work_model_preference || candidate.workModel
        return (
          <Badge
            className="text-xs"
            style={{
              backgroundColor: workModel === 'remoto' ? 'var(--gray-200)' : workModel === 'híbrido' ? 'var(--gray-200)' : 'var(--gray-200)',
              color: workModel === 'remoto' ? 'var(--gray-600)' : workModel === 'híbrido' ? 'var(--gray-600)' : 'var(--gray-600)'
            }}
          >
            {workModel === 'remoto' ? '🏠 Remoto' : workModel === 'híbrido' ? '🔄 Híbrido' : workModel === 'presencial' ? '🏢 Presencial' : workModel || ''}
          </Badge>
        )
      case 'contract_type_preference':
        return <span className="text-xs text-gray-800">{candidate.contract_type_preference || ''}</span>

      // Salário
      case 'current_salary':
        return <span className="text-xs text-gray-800 font-medium">{formatCurrency(candidate.current_salary || candidate.monthlySalary, candidate.salary_currency)}</span>
      case 'salary_currency':
        return <span className="text-xs text-gray-800">{candidate.salary_currency || 'BRL'}</span>
      case 'desired_salary_min':
        return <span className="text-xs text-gray-800">{formatCurrency(candidate.desired_salary_min, candidate.salary_currency)}</span>
      case 'desired_salary_max':
        return <span className="text-xs text-gray-800">{formatCurrency(candidate.desired_salary_max, candidate.salary_currency)}</span>
      case 'salary_expectation_clt':
        return <span className="text-xs text-gray-800">{formatCurrency(candidate.salary_expectation_clt)}</span>
      case 'salary_expectation_pj':
        return <span className="text-xs text-gray-800">{formatCurrency(candidate.salary_expectation_pj)}</span>
      case 'salary_expectation_freelance':
        return <span className="text-xs text-gray-800">{formatCurrency(candidate.salary_expectation_freelance)}</span>

      // Documentos
      case 'resume_url':
        return candidate.resume_url ? (
          <a href={candidate.resume_url} target="_blank" rel="noopener" className="text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:underline text-xs flex items-center gap-1">
            <FileText className="w-3 h-3" /> Currículo
          </a>
        ) : <span className="text-xs text-gray-800">N/A</span>
      case 'resume_text':
        return <span className="text-xs text-gray-800 truncate">{candidate.resume_text?.slice(0, 40) || ''}{candidate.resume_text && candidate.resume_text.length > 40 ? '...' : ''}</span>
      case 'cover_letter':
        return <span className="text-xs text-gray-800 truncate">{candidate.cover_letter?.slice(0, 40) || ''}{candidate.cover_letter && candidate.cover_letter.length > 40 ? '...' : ''}</span>

      // Match Score - fallback simples
      case 'match_score':
        const matchScoreFallback = candidate.score || 0
        if (matchScoreFallback === 0) {
          return <span className="text-xs text-gray-800">—</span>
        }
        return <span className="text-xs text-gray-800 font-medium">{matchScoreFallback}%</span>
        
      // Origem
      case 'source':
        return <Badge variant="outline" className="text-xs">{candidate.source || ''}</Badge>
      case 'ats_source_name':
        return <span className="text-xs text-gray-800">{candidate.ats_source_name || ''}</span>
      case 'ats_candidate_id':
        return <span className="text-xs text-gray-800 font-mono">{candidate.ats_candidate_id || ''}</span>
      case 'pearch_profile_id':
        return <span className="text-xs text-gray-800 font-mono">{candidate.pearch_profile_id || ''}</span>

      // Busca Global / Pearch
      case 'is_open_to_work':
        const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
        return isOpenToWork ? (
          <Badge className="text-xs bg-green-100 text-green-800">Open to Work</Badge>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'is_decision_maker':
        return candidate.is_decision_maker ? (
          <Badge className="text-xs bg-purple-100 text-purple-800">Decision Maker</Badge>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'is_top_universities':
        return candidate.is_top_universities ? (
          <Badge className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">Top University</Badge>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'is_hiring':
        return candidate.is_hiring ? (
          <Badge className="text-xs bg-orange-100 text-orange-800">Contratando</Badge>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'headline':
        return <span className="text-xs text-gray-800 truncate">{candidate.headline || ''}</span>
      case 'expertise':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.expertise)}</span>
      case 'linkedin_followers_count':
        return candidate.linkedin_followers_count ? (
          <span className="text-xs text-gray-800">{candidate.linkedin_followers_count.toLocaleString('pt-BR')}</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'linkedin_connections_count':
        return candidate.linkedin_connections_count ? (
          <span className="text-xs text-gray-800">{candidate.linkedin_connections_count.toLocaleString('pt-BR')}</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'outreach_message':
        return candidate.outreach_message ? (
          <div className="flex items-center gap-1">
            <span className="text-xs text-gray-800 truncate max-w-[200px]">{candidate.outreach_message.slice(0, 50)}...</span>
            <button
              onClick={(e) => {
                e.stopPropagation()
                navigator.clipboard.writeText(candidate.outreach_message!)
              }}
              className="p-0.5 hover:bg-gray-100 rounded"
              title="Copiar mensagem"
            >
              <Copy className="w-3 h-3 text-gray-500" />
            </button>
          </div>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'pearch_insights':
        return candidate.pearch_insights?.overall_summary ? (
          <span className="text-xs text-gray-800 truncate">{candidate.pearch_insights.overall_summary.slice(0, 50)}...</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'best_personal_email':
        return candidate.best_personal_email ? (
          <a href={`mailto:${candidate.best_personal_email}`} className="text-xs text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:underline truncate">
            {candidate.best_personal_email}
          </a>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'phone_types':
        if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        const activeTypes = Object.entries(candidate.phone_types)
          .filter(([_, active]) => active)
          .map(([type]) => type)
        return <span className="text-xs text-gray-800">{activeTypes.join(', ') || '—'}</span>
      case 'estimated_age':
        return candidate.estimated_age ? (
          <span className="text-xs text-gray-800">{candidate.estimated_age} anos</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'match_reasoning':
        return candidate.pearch_insights?.match_reasoning ? (
          <span className="text-xs text-gray-800 truncate" title={candidate.pearch_insights.match_reasoning}>
            {candidate.pearch_insights.match_reasoning.slice(0, 60)}...
          </span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'overall_summary':
        return candidate.pearch_insights?.overall_summary ? (
          <span className="text-xs text-gray-800 truncate" title={candidate.pearch_insights.overall_summary}>
            {candidate.pearch_insights.overall_summary.slice(0, 60)}...
          </span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'query_insights':
        const queryInsights = candidate.pearch_insights?.query_insights
        if (!queryInsights || queryInsights.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <div className="flex flex-col gap-0.5">
            {queryInsights.slice(0, 2).map((insight, idx) => (
              <div key={idx} className="flex items-center gap-1">
                <Badge className={`text-micro px-1 py-0 ${
                  insight.match_level === 'Exceeds' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
                  insight.match_level === 'Meets' ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' :
                  insight.match_level === 'Partial' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                  'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
                }`}>
                  {insight.match_level}
                </Badge>
                <span className={`${textStyles.caption} truncate max-w-[150px]`} title={insight.subquery}>
                  {insight.subquery?.slice(0, 25)}...
                </span>
              </div>
            ))}
            {queryInsights.length > 2 && (
              <span className={textStyles.caption}>+{queryInsights.length - 2} mais</span>
            )}
          </div>
        )
      case 'middle_name':
        return candidate.middle_name ? (
          <span className="text-xs text-gray-800 truncate">{candidate.middle_name}</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'best_business_email':
        return candidate.best_business_email ? (
          <a href={`mailto:${candidate.best_business_email}`} className="text-xs text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:underline truncate">
            {candidate.best_business_email}
          </a>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'personal_emails':
        const personalEmailsArr = candidate.personal_emails
        if (!personalEmailsArr || personalEmailsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <span className="text-xs text-gray-800 truncate" title={personalEmailsArr.join(', ')}>
            {personalEmailsArr.length === 1 ? personalEmailsArr[0] : `${personalEmailsArr[0]} (+${personalEmailsArr.length - 1})`}
          </span>
        )
      case 'business_emails':
        const businessEmailsArr = candidate.business_emails
        if (!businessEmailsArr || businessEmailsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <span className="text-xs text-gray-800 truncate" title={businessEmailsArr.join(', ')}>
            {businessEmailsArr.length === 1 ? businessEmailsArr[0] : `${businessEmailsArr[0]} (+${businessEmailsArr.length - 1})`}
          </span>
        )
      case 'company_followers_count':
        return candidate.company_followers_count != null ? (
          <span className="text-xs text-gray-800">{candidate.company_followers_count.toLocaleString('pt-BR')}</span>
        ) : <span className="text-xs text-gray-500">—</span>
      case 'company_keywords':
        const companyKeywordsArr = candidate.company_keywords
        if (!companyKeywordsArr || companyKeywordsArr.length === 0) {
          return <span className="text-xs text-gray-500">—</span>
        }
        return (
          <div className="flex flex-wrap gap-1">
            {companyKeywordsArr.slice(0, 3).map((keyword, idx) => (
              <Badge key={idx} variant="outline" className={`${badgeStyles.default} px-1 py-0`}>
                {keyword}
              </Badge>
            ))}
            {companyKeywordsArr.length > 3 && (
              <span className={textStyles.caption}>+{companyKeywordsArr.length - 3}</span>
            )}
          </div>
        )

      // Status
      case 'status':
        const statusColors: Record<string, string> = {
          'novo': 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300',
          'triagem': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
          'entrevista': 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300',
          'aprovado': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
          'reprovado': 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
        }
        return <Badge className={`text-xs ${statusColors[candidate.status || ''] || 'bg-gray-100 text-gray-800'}`}>{candidate.status || ''}</Badge>
      case 'is_active':
        return (
          <Badge variant="outline" className={`text-xs ${candidate.is_active ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {formatBoolean(candidate.is_active)}
          </Badge>
        )
      case 'is_blacklisted':
        return candidate.is_blacklisted ? (
          <Badge className="text-xs bg-red-100 text-red-800">Sim</Badge>
        ) : <span className="text-xs text-gray-800">Não</span>
      case 'blacklist_reason':
        return <span className="text-xs text-gray-800 truncate">{candidate.blacklist_reason || ''}</span>

      // Comunicação
      case 'preferred_contact_method':
        return <span className="text-xs text-gray-800">{candidate.preferred_contact_method || ''}</span>
      case 'best_time_to_contact':
        return <span className="text-xs text-gray-800">{candidate.best_time_to_contact || ''}</span>
      case 'communication_consent':
        return <Badge variant="outline" className={`text-xs ${candidate.communication_consent ? 'bg-green-50 text-green-700' : ''}`}>{formatBoolean(candidate.communication_consent)}</Badge>

      // Cadastro
      case 'completed_register':
        return <span className="text-xs text-gray-800">{formatBoolean(candidate.completed_register)}</span>
      case 'accept_terms':
        return <span className="text-xs text-gray-800">{formatBoolean(candidate.accept_terms)}</span>

      // Adicional
      case 'tags':
        return <span className="text-xs text-gray-800 truncate">{formatArray(candidate.tags)}</span>
      case 'notes':
        return <span className="text-xs text-gray-800 truncate">{candidate.notes?.slice(0, 40) || ''}{candidate.notes && candidate.notes.length > 40 ? '...' : ''}</span>
      case 'additional_data':
        return <span className="text-xs text-gray-800">JSON</span>

      // Datas
      case 'created_at':
        return <span className="text-xs text-gray-800">{formatDate(candidate.created_at)}</span>
      case 'updated_at':
        return <span className="text-xs text-gray-800">{formatDate(candidate.updated_at)}</span>
      case 'last_contacted_at':
        return <span className="text-xs text-gray-800">{formatDate(candidate.last_contacted_at)}</span>
      case 'last_activity_at':
        return <span className="text-xs text-gray-800">{formatDate(candidate.last_activity_at)}</span>

      default:
        return <span className="text-xs text-gray-800">N/A</span>
    }
  }

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
    if (score >= 90) return "bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 border-green-200 dark:border-green-800"
    if (score >= 80) return "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-200 dark:border-gray-700"
    if (score >= 70) return "bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800"
    return "bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border-red-200 dark:border-red-800"
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
    let aValue: any = a[sortBy as keyof Candidate]
    let bValue: any = b[sortBy as keyof Candidate]

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
                      style={{ width: `${formatScore(candidate.score)}%` }}
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
                        <Badge key={index} className="text-xs bg-green-100 text-green-700 border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Soft Skills</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Liderança', 'Comunicação', 'Trabalho em equipe', 'Resolução de problemas'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-purple-100 text-purple-700 border-0">
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
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-gray-100 dark:bg-gray-800 rounded">
                    📧 Email enviado há 2 dias
                  </div>
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-green-50 dark:bg-green-900/20 rounded">
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
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="font-semibold text-gray-950 dark:text-gray-50">{formatScorePercent(candidate.score)}</div>
              <div className="text-gray-800">Score LIA</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <div className="font-semibold text-gray-950 dark:text-gray-50 flex items-center justify-center gap-1">
                <Star className="w-3 h-3 text-yellow-500" />
                4.8
              </div>
              <div className="text-gray-800">Avaliação</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
              <Badge className={`text-xs ${
                candidate.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
                candidate.status === 'prospect' ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' :
                candidate.status === 'interview' ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300' :
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
            onClick={() => console.log('Agendar entrevista')}
          >
            <Calendar className="w-4 h-4" />
            Agendar Entrevista
          </Button>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => console.log('Enviar email')}
            >
              <Mail className="w-4 h-4" />
              Email
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => console.log('Perguntar à LIA')}
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

  // Salvar candidatos Pearch selecionados na base local
  const handleSaveToLocalBase = async () => {
    const selectedPearchCandidates = candidates.filter(
      c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
    )
    
    if (selectedPearchCandidates.length === 0) {
      toast({
        title: "Nenhum candidato Pearch selecionado",
        description: "Selecione candidatos de busca global para salvar na base.",
        variant: "destructive"
      })
      return
    }
    
    setIsSavingToBase(true)
    
    try {
      const importPayload = {
        candidates: selectedPearchCandidates.map(c => ({
          pearch_id: c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }
      
      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })
      
      if (!response.ok) {
        throw new Error('Falha ao importar candidatos')
      }
      
      const result = await response.json()
      
      toast({
        title: "Candidatos salvos na base!",
        description: result.message,
      })
      
      // Limpar seleção após salvar
      deselectAllCandidates()
      
    } catch (error) {
      console.error('Error saving candidates to local base:', error)
      toast({
        title: "Erro ao salvar candidatos",
        description: "Tente novamente em alguns instantes.",
        variant: "destructive"
      })
    } finally {
      setIsSavingToBase(false)
    }
  }

  // Handler para adicionar candidatos à lista (importando Pearch candidates primeiro)
  const handleAddToList = async () => {
    const selectedIds = Array.from(selectedCandidatesForBatch)
    const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
    const selectedNames = selectedCandidates.map(c => c.name)
    
    // Separar candidatos locais e Pearch
    const localCandidates = selectedCandidates.filter(c => c.source !== 'pearch')
    const pearchCandidates = selectedCandidates.filter(c => c.source === 'pearch')
    
    // Se não há candidatos Pearch, abrir modal diretamente
    if (pearchCandidates.length === 0) {
      setAddToListCandidateIds(selectedIds)
      setAddToListCandidateNames(selectedNames)
      setShowAddToListModal(true)
      return
    }
    
    // Importar candidatos Pearch primeiro
    setIsAddingToList(true)
    
    try {
      const importPayload = {
        candidates: pearchCandidates.map(c => ({
          pearch_id: c.pearch_profile_id || c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }
      
      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })
      
      if (!response.ok) {
        throw new Error('Falha ao importar candidatos Pearch')
      }
      
      const result = await response.json()
      
      // Criar mapeamento de pearch_id → local_id
      const idMapping = new Map<string, string>()
      if (result.mapping && Array.isArray(result.mapping)) {
        result.mapping.forEach((m: { pearch_id: string; local_id: string }) => {
          idMapping.set(m.pearch_id, m.local_id)
        })
      }
      
      // Substituir IDs Pearch pelos IDs locais
      const localIds: string[] = []
      
      // Adicionar IDs dos candidatos locais
      localCandidates.forEach(c => {
        localIds.push(c.id)
      })
      
      // Adicionar IDs mapeados dos candidatos Pearch
      pearchCandidates.forEach(c => {
        const pearchId = c.pearch_profile_id || c.id
        const localId = idMapping.get(pearchId)
        if (localId) {
          localIds.push(localId)
        } else {
          // Fallback: usar ID original se não encontrar mapeamento
          console.warn(`No mapping found for Pearch candidate: ${pearchId}`)
          localIds.push(c.id)
        }
      })
      
      // Abrir modal com IDs locais
      setAddToListCandidateIds(localIds)
      setAddToListCandidateNames(selectedNames)
      setShowAddToListModal(true)
      
      // Mostrar toast informativo
      if (result.imported_count > 0 || result.updated_count > 0) {
        toast({
          title: "Candidatos importados",
          description: `${result.imported_count || 0} novo(s), ${result.updated_count || 0} atualizado(s)`,
        })
      }
      
    } catch (error) {
      console.error('Error importing Pearch candidates:', error)
      toast({
        title: "Erro ao importar candidatos",
        description: "Não foi possível salvar candidatos Pearch na base. Tente novamente.",
        variant: "destructive"
      })
    } finally {
      setIsAddingToList(false)
    }
  }
  
  // Contar candidatos Pearch selecionados
  const selectedPearchCount = candidates.filter(
    c => selectedCandidatesForBatch.has(c.id) && c.source === 'pearch'
  ).length

  // Handler para mudança de aba com verificação de candidatos não salvos
  const handleTabChangeWithWarning = (newTab: string) => {
    // Se está na aba de busca com resultados Pearch e quer mudar para outra aba
    if (activeTab === 'search' && hasUnsavedPearchCandidates && newTab !== 'search') {
      setPendingTabChange(newTab)
      setShowUnsavedWarningModal(true)
    } else {
      setActiveTab(newTab as any)
    }
  }

  // Handler para salvar todos os candidatos Pearch e sair
  const handleSaveAllAndExit = async () => {
    setIsSavingToBase(true)
    
    try {
      const importPayload = {
        candidates: unsavedPearchCandidates.map(c => ({
          pearch_id: c.pearch_profile_id || c.id,
          name: c.name,
          first_name: c.name?.split(' ')[0] || null,
          last_name: c.name?.split(' ').slice(1).join(' ') || null,
          middle_name: c.middle_name || null,
          email: c.email || null,
          phone: c.phone || null,
          linkedin_url: c.linkedin_url || null,
          avatar_url: c.avatar_url || null,
          current_title: c.current_title || null,
          current_company: c.current_company || null,
          headline: c.headline || null,
          summary: c.summary || null,
          location: c.location || null,
          years_of_experience: c.years_of_experience || null,
          skills: c.skills || [],
          expertise: c.expertise || [],
          languages: c.languages || [],
          education: c.education || [],
          experiences: (c.experiences || []).map((exp: any) => ({
            company_name: exp.company || exp.company_name || 'Empresa não informada',
            company_linkedin_url: exp.company_linkedin_url || null,
            company_domain: exp.company_domain || null,
            title: exp.title || null,
            start_date: exp.start_date || null,
            end_date: exp.end_date || null,
            duration_years: exp.duration_years || null,
            is_current: exp.current || false,
            description: exp.description || null,
            location: exp.location || null,
            industries: exp.industries || [],
            company_size: exp.company_size || null,
            company_size_range: exp.company_size_range || null,
            technologies: exp.technologies || [],
            is_startup: exp.is_startup || null,
            company_founded_year: null,
            company_annual_revenue: null,
            company_followers_count: exp.company_followers_count || exp.company_info?.followers_count || null,
            company_keywords: exp.company_keywords || exp.company_info?.keywords || []
          })),
          is_open_to_work: c.is_open_to_work || null,
          is_decision_maker: c.is_decision_maker || null,
          is_top_universities: c.is_top_universities || null,
          is_hiring: c.is_hiring || null,
          best_personal_email: c.best_personal_email || null,
          best_business_email: c.best_business_email || null,
          personal_emails: c.personal_emails || [],
          business_emails: c.business_emails || [],
          phone_types: c.phone_types || null,
          estimated_age: c.estimated_age || null,
          linkedin_followers_count: c.linkedin_followers_count || c.followers_count || null,
          linkedin_connections_count: c.linkedin_connections_count || c.connections_count || null,
          insights: c.pearch_insights || c.insights || null,
          outreach_message: c.outreach_message || null
        })),
        source_search_query: lastSearchQuery || undefined
      }
      
      const response = await fetch('/api/backend-proxy/search/candidates/import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(importPayload)
      })
      
      if (!response.ok) {
        throw new Error('Falha ao importar candidatos')
      }
      
      const result = await response.json()
      
      toast({
        title: "Candidatos salvos!",
        description: result.message,
      })
      
      // Limpar resultados de busca e mudar para a aba pendente
      setCandidates([])
      setShowSearchResults(false)
      setShowUnsavedWarningModal(false)
      if (pendingTabChange) {
        setActiveTab(pendingTabChange as any)
        setPendingTabChange(null)
      }
      
    } catch (error: any) {
      console.error('Error saving candidates:', error)
      const errorMessage = error?.message || 'Erro desconhecido ao salvar candidatos'
      toast({
        title: "Erro ao salvar",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setIsSavingToBase(false)
    }
  }

  // Handler para sair sem salvar
  const handleExitWithoutSaving = () => {
    setCandidates([])
    setShowSearchResults(false)
    setShowUnsavedWarningModal(false)
    if (pendingTabChange) {
      setActiveTab(pendingTabChange as any)
      setPendingTabChange(null)
    }
  }

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

  const handleWSIScreeningComplete = (result: any) => {
    console.log('WSI Screening completed:', result)
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

  // Handler para aplicar filtros avançados (agora usado pelo painel lateral)
  const handleApplyAdvancedFilters = (filters: SearchFilters) => {
    setActiveSearchFilters(filters)
    
    // Aplicar filtros na busca
    const query = buildQueryFromFilters(filters)
    if (query) {
      executeSearch(query, {}, 'natural', undefined, false)
    }
  }

  // Função auxiliar para construir query a partir de filtros
  const buildQueryFromFilters = (filters: SearchFilters): string => {
    const parts: string[] = []
    
    if (filters.skills?.skills && filters.skills.skills.length > 0) {
      parts.push(`skills: ${filters.skills.skills.join(', ')}`)
    }
    if (filters.locations?.locations && filters.locations.locations.length > 0) {
      parts.push(`localização: ${filters.locations.locations.join(', ')}`)
    }
    if (filters.general?.minExperience || filters.general?.maxExperience) {
      const min = filters.general.minExperience || 0
      const max = filters.general.maxExperience || 10
      parts.push(`experiência: ${min}-${max} anos`)
    }
    if (filters.job?.levels && filters.job.levels.length > 0) {
      parts.push(`senioridade: ${filters.job.levels.join(', ')}`)
    }
    if (filters.job?.titles && filters.job.titles.length > 0) {
      parts.push(`cargo: ${filters.job.titles.join(', ')}`)
    }
    if (filters.languages?.languages && filters.languages.languages.length > 0) {
      parts.push(`idiomas: ${filters.languages.languages.join(', ')}`)
    }
    if (filters.company?.industries && filters.company.industries.length > 0) {
      parts.push(`indústrias: ${filters.company.industries.join(', ')}`)
    }
    if (filters.education?.degrees && filters.education.degrees.length > 0) {
      parts.push(`formação: ${filters.education.degrees.join(', ')}`)
    }
    
    return parts.join(', ')
  }

  // Funções para filtros de coluna
  const getColumnStats = (column: string) => {
    const stats: {[key: string]: number} = {}

    candidates.forEach(candidate => {
      let value: string

      switch (column) {
        case 'position':
          value = candidate.position
          break
        case 'company':
          value = candidate.workHistory?.[0]?.company || ''
          break
        case 'location':
          value = candidate.location
          break
        case 'scoreRange':
          const score = candidate.liaAnalysis?.score || candidate.score
          if (score >= 90) value = '90-100%'
          else if (score >= 80) value = '80-89%'
          else if (score >= 70) value = '70-79%'
          else value = '60-69%'
          break
        default:
          value = 'N/A'
      }

      stats[value] = (stats[value] || 0) + 1
    })

    return Object.entries(stats)
      .sort(([,a], [,b]) => b - a) // Ordenar por quantidade (desc)
      .map(([value, count]) => ({ value, count }))
  }

  const toggleColumnFilter = (column: string, value: string) => {
    setColumnFilters(prev => ({
      ...prev,
      [column]: prev[column].includes(value)
        ? prev[column].filter((v: string) => v !== value)
        : [...prev[column], value]
    }))
  }

  const getActiveColumnFiltersCount = () => {
    let count = 0

    // Contar filtros regulares (arrays)
    Object.entries(columnFilters).forEach(([key, value]) => {
      if (key !== 'bigFive' && Array.isArray(value)) {
        count += value.length
      }
    })

    // Contar filtros de Big Five (valores não vazios)
    if (columnFilters.bigFive) {
      count += Object.values(columnFilters.bigFive).filter(v => v !== '').length
    }

    return count
  }

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newExpanded = new Set(prev)
      if (newExpanded.has(sectionId)) {
        newExpanded.delete(sectionId)
      } else {
        newExpanded.add(sectionId)
      }
      return newExpanded
    })
  }

  // Handlers para templates e busca
  const handleTemplateSelection = (template: string) => {
    setSelectedTemplate(template)
    // Implementar lógica de aplicação do template
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

  const applySavedSearch = (search: any) => {
    setSearchTerm(search.query.replace(search.filters.booleanSearch || '', '').trim())
    setBooleanSearch(search.filters.booleanSearch || '')
    setAdvancedFilters(search.filters)
  }

  const deleteSavedSearch = (index: number) => {
    setSavedSearches(prev => prev.filter((_, i) => i !== index))
  }

  // Detecta se o texto é uma pergunta genérica (não uma busca de candidatos)
  const isConversationalMessage = (text: string): boolean => {
    const normalizedText = text.toLowerCase().trim()

    const greetings = [
      /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite|tudo bem|tudo certo|beleza)[\s!.,?]*$/,
      /^(oi|olá|ola|hey|hi|hello|e aí|eai|fala|bom dia|boa tarde|boa noite)\s+(lia|tudo|como)/,
      /^(obrigad[oa]|valeu|thanks|vlw|brigad[oa])[\s!.,?]*$/,
      /^(tchau|até mais|ate mais|bye|flw|falou)[\s!.,?]*$/,
    ]

    return greetings.some(pattern => pattern.test(normalizedText))
  }

  const isGenericQuestion = (text: string): boolean => {
    const normalizedText = text.toLowerCase().trim()
    
    const questionPatterns = [
      /^(o que|que tipo|qual|quais|como|por que|quando|onde|quem|quanto|quantos)\s/,
      /^(me explica|explique|pode explicar|poderia explicar)/,
      /^(me ajuda|ajuda|help|pode ajudar|poderia ajudar)/,
      /^(o que você|voce pode|você consegue|vc pode)/,
      /\?$/,
    ]
    
    const searchKeywords = [
      'desenvolvedor', 'developer', 'programador', 'engenheiro', 'analista',
      'gerente', 'manager', 'coordenador', 'diretor', 'especialista',
      'junior', 'pleno', 'sênior', 'senior', 'trainee', 'estagiário',
      'python', 'java', 'javascript', 'react', 'node', 'angular', 'vue',
      'backend', 'frontend', 'fullstack', 'devops', 'data', 'machine learning',
      'são paulo', 'rio de janeiro', 'belo horizonte', 'remoto', 'híbrido',
      'anos de experiência', 'experiência em', 'conhecimento em',
      'product manager', 'product owner', 'scrum master', 'ux', 'ui',
      'designer', 'marketing', 'vendas', 'sales', 'rh', 'recursos humanos',
      'b2b', 'saas', 'fintech', 'startup'
    ]
    
    const hasSearchKeywords = searchKeywords.some(keyword => 
      normalizedText.includes(keyword.toLowerCase())
    )
    
    const isQuestion = questionPatterns.some(pattern => pattern.test(normalizedText))
    
    return isQuestion && !hasSearchKeywords
  }

  // Handler para mensagens no chat da LIA (perguntas ou buscas)
  // Loading State Ownership:
  // - Comandos de análise: handleAICommand gerencia isLIAThinking
  // - Perguntas genéricas: orquestrador gerencia isLIAThinking (try/finally aqui)
  // - Buscas: executeSearch gerencia setIsLoading (indicador visual diferente)
  const handleLIAChatMessage = async (message: string) => {
    const trimmedMessage = message.trim()
    const normalizedMessage = trimmedMessage.toLowerCase()
    
    // Comandos de análise redirecionados para handleAICommand (gerencia seu próprio loading)
    const analysisCommands = [
      'analisar potencial', 'potencial de crescimento', 'analise potencial',
      'definir tipo', 'tipo de perfil',
      'resumo executivo', 'resumir busca', 'resumir resultado',
      'pontos a desenvolver', 'pontos a serem desenvolvidos',
      'vagas ideais', 'tipos de vagas',
      'top 5', 'top5', 'melhores candidatos',
      'comparar', 'comparação'
    ]
    
    // Verificar se é um comando de análise - se for, usar handleAICommand
    const isAnalysisCommand = analysisCommands.some(cmd => normalizedMessage.includes(cmd))
    
    if (isAnalysisCommand) {
      handleAICommand(trimmedMessage)
      setLiaPromptValue('')
      return
    }
    
    // Adicionar mensagem do usuário ao chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: trimmedMessage,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])
    setLiaPromptValue('')
    
    // Se é saudação/conversacional ou pergunta genérica, usar o orquestrador (não buscar candidatos)
    if (isConversationalMessage(trimmedMessage) || isGenericQuestion(trimmedMessage)) {
      setIsLIAThinking(true)
      
      try {
        const response = await handleOrchestratedTalentMessage(trimmedMessage)
        
        if (response.success) {
          const agentInfo = response.agents_consulted?.length > 1 
            ? `_Agentes: ${response.agents_consulted.join(', ')}_\n\n`
            : ''
          
          const liaResponse: ChatMessage = {
            id: `lia-response-${Date.now()}`,
            type: 'lia',
            content: agentInfo + response.content,
            timestamp: new Date(),
            metadata: {
              action_executed: response.action_executed,
              action_result: response.action_result as Record<string, unknown> | undefined,
              action_type: response.action_type,
              needs_confirmation: response.needs_confirmation,
              needs_params: response.needs_params,
              pending_action_id: response.pending_action_id,
              conversation_id: response.conversation_id
            }
          }
          setChatMessages(prev => [...prev, liaResponse])
          
          if (response.suggested_prompts && response.suggested_prompts.length > 0) {
            const suggestionsMessage: ChatMessage = {
              id: `lia-suggestions-${Date.now()}`,
              type: 'lia',
              content: `💡 **Sugestões:**\n${response.suggested_prompts.slice(0, 3).map(p => `• ${p}`).join('\n')}`,
              timestamp: new Date()
            }
            setTimeout(() => {
              setChatMessages(prev => [...prev, suggestionsMessage])
            }, 500)
          }
        } else {
          throw new Error('Orchestrator returned unsuccessful response')
        }
      } catch (error) {
        console.error('Orchestrator error, using fallback:', error)
        
        const fallbackContent = isConversationalMessage(trimmedMessage)
          ? `Olá! Sou a LIA, sua assistente de recrutamento. Aqui no Funil de Talentos posso ajudá-lo a:\n\n🔍 **Buscar candidatos** — descreva o perfil desejado\n📊 **Analisar candidatos** — selecione e peça análise\n⚖️ **Comparar perfis** — selecione candidatos e peça comparação\n\nComo posso ajudar?`
          : `Entendi sua pergunta! Posso ajudá-lo a:\n\n🔍 **Buscar candidatos** - descreva o perfil desejado\n📊 **Analisar candidatos** - selecione e peça análise\n📋 **Criar vagas** - diga "criar nova vaga"\n⚖️ **Comparar perfis** - selecione candidatos e peça comparação\n\nComo posso ajudar?`

        const fallbackResponse: ChatMessage = {
          id: `lia-response-${Date.now()}`,
          type: 'lia',
          content: fallbackContent,
          timestamp: new Date()
        }
        setChatMessages(prev => [...prev, fallbackResponse])
      } finally {
        setIsLIAThinking(false)
      }
      return
    }
    
    // Se é uma busca de candidatos, executar normalmente (executeSearch já gerencia seu próprio loading)
    executeSearch(trimmedMessage)
  }

  // Handlers para modais
  const handleQuickView = (candidate: Candidate) => {
    setSidePreviewCandidate(candidate)
    setShowSidePreview(true)
  }

  const handleAICommand = async (command: string) => {
    console.log('AI Command:', command)
    const trimmedCommand = command.trim().toLowerCase()

    // Adicionar mensagem do usuário ao chat
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: command,
      timestamp: new Date()
    }
    setChatMessages(prev => [...prev, userMessage])

    // Ativar estado de "pensando"
    setIsLIAThinking(true)

    try {
      // Determinar tipo de comando e processar
      let liaResponse: ChatMessage

      // Comandos de resumo de busca
      if (trimmedCommand.includes('resumir') && (trimmedCommand.includes('busca') || trimmedCommand.includes('resultado'))) {
        const totalCandidates = candidates.length
        
        if (totalCandidates === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📊 **Resumo da Busca**\n\nNenhum candidato encontrado ainda.\n\n💡 *Faça uma busca digitando o perfil desejado acima, como "Desenvolvedor Python Sênior".*`,
            timestamp: new Date()
          }
        } else {
          const localCount = candidates.filter(c => c.source === 'local' || !c.source).length
          const avgScore = Math.round(candidates.reduce((acc, c) => acc + (c.score || 0), 0) / totalCandidates)
          const topSkills = candidates.flatMap(c => c.skills || c.technical_skills || []).reduce((acc, skill) => {
            if (skill && typeof skill === 'string') {
              acc[skill] = (acc[skill] || 0) + 1
            }
            return acc
          }, {} as Record<string, number>)
          const sortedSkills = Object.entries(topSkills).sort((a, b) => b[1] - a[1]).slice(0, 5)
          const locations = [...new Set(candidates.map(c => c.location || c.location_city).filter(Boolean))]
          
          const skillsText = sortedSkills.length > 0 
            ? sortedSkills.map(([skill, count]) => `• ${skill} (${count})`).join('\n')
            : '• Nenhuma skill identificada nos perfis'
          const locationsText = locations.length > 0 
            ? `${locations.slice(0, 3).join(', ')}${locations.length > 3 ? ` e mais ${locations.length - 3}` : ''}`
            : 'Não especificadas'

          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📊 **Resumo da Busca**\n\nEncontrei **${totalCandidates} candidato${totalCandidates !== 1 ? 's' : ''}** (${localCount} da base local).\n\n**Score médio de compatibilidade:** ${formatScorePercent(avgScore)}\n\n**Top skills mais comuns:**\n${skillsText}\n\n**Localizações:** ${locationsText}\n\n💡 *Posso analisar candidatos específicos ou comparar os selecionados.*`,
            timestamp: new Date()
          }
        }
      }
      // Comando Top 5 candidatos
      else if (trimmedCommand.includes('top 5') || trimmedCommand.includes('top5') || trimmedCommand.includes('melhores candidatos')) {
        if (candidates.length === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🏆 **Top Candidatos**\n\nNenhum candidato disponível ainda.\n\n💡 *Faça uma busca para encontrar candidatos.*`,
            timestamp: new Date()
          }
        } else {
          const topCandidates = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5)
          const topCount = topCandidates.length
          const topList = topCandidates.map((c, i) => {
            const candidateSkills = c.skills || c.technical_skills || []
            const skillsPreview = candidateSkills.length > 0 
              ? ` | Skills: ${candidateSkills.slice(0, 3).join(', ')}${candidateSkills.length > 3 ? '...' : ''}`
              : ''
            return `${i + 1}. **${c.name}** - ${c.position || c.current_title || 'N/A'} @ ${c.current_company || 'N/A'} (Score: ${formatScorePercent(c.score || 0)})${skillsPreview}`
          }).join('\n')

          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🏆 **Top ${topCount} Candidatos**\n\n${topList}\n\n💡 *Selecione candidatos para análise mais detalhada ou comparação.*`,
            timestamp: new Date()
          }
        }
      }
      // Comando Comparar selecionados
      else if (trimmedCommand.includes('comparar') && (trimmedCommand.includes('selecionado') || selectedCandidatesForBatch.size >= 2)) {
        if (selectedCandidatesForBatch.size < 2) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `⚠️ **Selecione pelo menos 2 candidatos** para fazer a comparação.\n\nClique na checkbox ao lado de cada candidato na tabela.`,
            timestamp: new Date()
          }
        } else {
          const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          if (selectedCandidates.length === 0) {
            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`,
              timestamp: new Date()
            }
          } else {
            const comparison = selectedCandidates.map(c => {
              const candidateSkills = c.skills || c.technical_skills || []
              const skillsText = candidateSkills.length > 0 
                ? candidateSkills.slice(0, 5).join(', ')
                : 'Não informadas'
              const expYears = c.experience ?? c.years_of_experience
              const experienceText = typeof expYears === 'number'
                ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}`
                : 'Não informado'
              return `**${c.name}**\n• Cargo: ${c.position || c.current_title || 'Não informado'}\n• Empresa: ${c.current_company || 'Não informada'}\n• Experiência: ${experienceText}\n• Score: ${formatScorePercent(c.score || 0)}\n• Skills: ${skillsText}`
            }).join('\n\n')

            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚖️ **Comparação de ${selectedCandidates.length} Candidatos**\n\n${comparison}\n\n💡 *Clique no score CV de cada candidato na tabela para ver a análise detalhada.*`,
              timestamp: new Date()
            }
          }
        }
      }
      // Comandos de análise de candidato específico
      else if (
        trimmedCommand.includes('analisar potencial') ||
        trimmedCommand.includes('potencial de crescimento') ||
        trimmedCommand.includes('definir tipo') ||
        trimmedCommand.includes('tipo de perfil') ||
        trimmedCommand.includes('resumo executivo') ||
        trimmedCommand.includes('pontos a desenvolver') ||
        trimmedCommand.includes('vagas ideais')
      ) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `⚠️ **Nenhum candidato selecionado**\n\nSelecione um ou mais candidatos na tabela para que eu possa analisar.\n\n💡 Clique na checkbox ao lado do nome do candidato.`,
            timestamp: new Date()
          }
        } else {
          const selectedCandidates = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          
          if (selectedCandidates.length === 0) {
            liaResponse = {
              id: `lia-${Date.now()}`,
              type: 'lia',
              content: `⚠️ **Candidatos não encontrados**\n\nOs candidatos selecionados não foram localizados. Tente fazer uma nova busca.`,
              timestamp: new Date()
            }
          } else {
            // Chamar API de análise
            try {
              const candidatesForApi = selectedCandidates.map(c => ({
                id: c.id,
                name: c.name,
                position: c.position || c.current_title || 'Profissional',
                location: c.location || c.location_city || 'Não especificada',
                company: c.current_company || 'Não especificada',
                skills: c.skills || c.technical_skills || [],
                experience_years: c.experience || c.years_of_experience || 0,
                seniority_level: c.seniority_level || 'pleno',
                cv_text: c.resume_text || c.self_introduction || ''
              }))

              // Determinar job_title com fallbacks - garantir que nunca é vazio
              let jobTitleForApi = 'Análise de perfil profissional'
              const queryText = searchResults?.query?.trim()
              const firstPosition = selectedCandidates[0]?.position?.trim() || selectedCandidates[0]?.current_title?.trim()
              if (queryText && queryText.length > 0) {
                jobTitleForApi = queryText
              } else if (firstPosition && firstPosition.length > 0) {
                jobTitleForApi = firstPosition
              }

              const response = await fetch('/api/lia/api/v1/analysis/candidates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  candidates: candidatesForApi,
                  analysis_type: 'general',
                  job_title: jobTitleForApi
                })
              })

              if (!response.ok) {
                const errorText = await response.text().catch(() => 'Erro desconhecido')
                console.error('API Error:', response.status, errorText)
                
                // Mostrar erro específico ao usuário antes do fallback
                let userErrorMessage = ''
                if (response.status === 422) {
                  userErrorMessage = 'Dados do candidato inválidos ou incompletos.'
                } else if (response.status === 401 || response.status === 403) {
                  userErrorMessage = 'Não autorizado. Verifique suas credenciais.'
                } else if (response.status >= 500) {
                  userErrorMessage = 'Serviço de análise temporariamente indisponível.'
                } else {
                  userErrorMessage = `Erro ${response.status}: ${errorText.substring(0, 80)}`
                }
                
                throw new Error(userErrorMessage)
              }
              
              const data = await response.json()
              const results = data.results || []
              
              if (results.length === 0) {
                liaResponse = {
                  id: `lia-${Date.now()}`,
                  type: 'lia',
                  content: `🧠 **Análise LIA**\n\nNenhum resultado de análise gerado para os candidatos selecionados.\n\n**Possíveis causas:**\n• Perfis com informações insuficientes\n• Erro temporário no serviço de análise\n\n💡 *Tente selecionar candidatos com perfis mais completos.*`,
                  timestamp: new Date()
                }
              } else {
                let analysisContent = `🧠 **Análise LIA**\n\n`
                
                for (const result of results) {
                  analysisContent += `**${result.candidate_name || 'Candidato'}**\n`
                  analysisContent += `• **Arquétipo:** ${result.archetype || 'Executor Confiável'}\n`
                  analysisContent += `• **Score LIA:** ${formatScorePercent(result.lia_score || 0)}\n`
                  analysisContent += `• **Fit de Personalidade:** ${formatScorePercent(result.fit_score || 0)}\n`
                  
                  if (result.strengths?.length > 0) {
                    analysisContent += `• **Pontos fortes:** ${result.strengths.slice(0, 3).join(', ')}\n`
                  }
                  if (result.gaps?.length > 0) {
                    analysisContent += `• **Pontos a desenvolver:** ${result.gaps.slice(0, 2).join(', ')}\n`
                  }
                  if (result.recommendation) {
                    analysisContent += `• **Recomendação:** ${result.recommendation}\n`
                  }
                  if (result.potential_roles?.length > 0) {
                    analysisContent += `• **Vagas ideais:** ${result.potential_roles.slice(0, 3).join(', ')}\n`
                  }
                  analysisContent += `\n`
                }
                
                liaResponse = {
                  id: `lia-${Date.now()}`,
                  type: 'lia',
                  content: analysisContent,
                  timestamp: new Date()
                }
              }
            } catch (apiError) {
              console.error('API Error:', apiError)
              // Extrair mensagem de erro legível
              const errorMessage = apiError instanceof Error ? apiError.message : 'Erro desconhecido'
              
              // Fallback com análise local simplificada
              const selectedCandidate = selectedCandidates[0]
              const candidateSkills = selectedCandidate.skills || selectedCandidate.technical_skills || []
              const skillsText = candidateSkills.length > 0 
                ? candidateSkills.slice(0, 5).join(', ')
                : 'Não informadas'
              const expYears = selectedCandidate.experience ?? selectedCandidate.years_of_experience
              const experienceText = typeof expYears === 'number'
                ? `${expYears} ${expYears === 1 ? 'ano' : 'anos'}`
                : 'Não informada'
              
              liaResponse = {
                id: `lia-${Date.now()}`,
                type: 'lia',
                content: `🧠 **Análise de ${selectedCandidate.name}** (modo offline)\n\n**⚠️ Motivo:** ${errorMessage}\n\n**Perfil:** ${selectedCandidate.position || selectedCandidate.current_title || 'Profissional'}\n**Empresa:** ${selectedCandidate.current_company || 'Não informada'}\n**Experiência:** ${experienceText}\n**Skills:** ${skillsText}\n\n**Arquétipo sugerido:** Executor Confiável\n**Potencial:** Alto para funções técnicas\n\n💡 *Esta é uma análise simplificada. Tente novamente mais tarde para análise completa com IA.*`,
                timestamp: new Date()
              }
            }
          }
        }
      }
      // Análises de busca - perguntas sobre os resultados
      else if (trimmedCommand.includes('quantos candidatos') || trimmedCommand.includes('quantos encontrei')) {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: candidates.length === 0 
            ? `📊 **Nenhum candidato encontrado** ainda.\n\n💡 *Faça uma busca para ver resultados.*`
            : `📊 **Total de candidatos:** ${candidates.length}\n\n• Base local: ${candidates.filter(c => c.source === 'local' || !c.source).length}\n• Base global: ${candidates.filter(c => c.source === 'global' || c.source === 'pearch').length}\n\n💡 *Selecione candidatos para análise detalhada.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('score') && (trimmedCommand.includes('médio') || trimmedCommand.includes('media') || trimmedCommand.includes('lia'))) {
        const avgScore = candidates.length > 0 ? Math.round(candidates.reduce((acc, c) => acc + (c.score || c.lia_score || 0), 0) / candidates.length) : 0
        const highScoreCount = candidates.filter(c => (c.score || c.lia_score || 0) >= 70).length
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: candidates.length === 0 
            ? `📊 **Nenhum candidato** para calcular score médio.\n\n💡 *Faça uma busca primeiro.*`
            : `📊 **Score LIA médio:** ${formatScorePercent(avgScore)}\n\n• Candidatos com score ≥70%: **${highScoreCount}** (${Math.round(highScoreCount/candidates.length*100)}%)\n• Score máximo: ${formatScorePercent(Math.max(...candidates.map(c => c.score || c.lia_score || 0)))}\n• Score mínimo: ${formatScorePercent(Math.min(...candidates.map(c => c.score || c.lia_score || 0)))}\n\n💡 *Os candidatos de maior score geralmente têm melhor fit com a vaga.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('skills') && (trimmedCommand.includes('comuns') || trimmedCommand.includes('mais'))) {
        const allSkills = candidates.flatMap(c => c.skills || c.technical_skills || [])
        const skillCounts = allSkills.reduce((acc, skill) => {
          if (skill && typeof skill === 'string') acc[skill] = (acc[skill] || 0) + 1
          return acc
        }, {} as Record<string, number>)
        const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 10)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: topSkills.length === 0 
            ? `📊 **Nenhuma skill identificada** nos perfis.\n\n💡 *Os candidatos podem não ter skills cadastradas.*`
            : `📊 **Top Skills mais comuns:**\n\n${topSkills.map(([skill, count], i) => `${i+1}. **${skill}** - ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *Use essas skills como filtro para refinar sua busca.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('experiência') && trimmedCommand.includes('média')) {
        const withExp = candidates.filter(c => typeof (c.experience ?? c.years_of_experience) === 'number')
        const avgExp = withExp.length > 0 ? (withExp.reduce((acc, c) => acc + (c.experience ?? c.years_of_experience ?? 0), 0) / withExp.length).toFixed(1) : 0
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: withExp.length === 0 
            ? `📊 **Experiência não informada** nos perfis.\n\n💡 *Os candidatos podem não ter anos de experiência cadastrados.*`
            : `📊 **Experiência média:** ${avgExp} anos\n\n• Candidatos com experiência informada: ${withExp.length}/${candidates.length}\n• Mais experiente: ${Math.max(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n• Menos experiente: ${Math.min(...withExp.map(c => c.experience ?? c.years_of_experience ?? 0))} anos\n\n💡 *Filtrar por experiência pode refinar seus resultados.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('onde estão') || trimmedCommand.includes('localizados') || trimmedCommand.includes('localização')) {
        const locations = candidates.map(c => c.location || c.location_city || c.location_state).filter(Boolean)
        const locationCounts = locations.reduce((acc, loc) => {
          acc[loc as string] = (acc[loc as string] || 0) + 1
          return acc
        }, {} as Record<string, number>)
        const topLocations = Object.entries(locationCounts).sort((a, b) => b[1] - a[1]).slice(0, 8)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: topLocations.length === 0 
            ? `📍 **Localização não informada** nos perfis.\n\n💡 *Os candidatos podem não ter localização cadastrada.*`
            : `📍 **Distribuição por localização:**\n\n${topLocations.map(([loc, count]) => `• **${loc}**: ${count} candidato${count > 1 ? 's' : ''}`).join('\n')}\n\n💡 *${candidates.filter(c => c.is_remote).length} candidatos aceitam trabalho remoto.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('nota') && trimmedCommand.includes('acima')) {
        const threshold = 70
        const aboveCount = candidates.filter(c => (c.score || c.lia_score || 0) >= threshold).length
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `📊 **Candidatos com nota LIA ≥${threshold}%:** ${aboveCount}\n\n• Total de candidatos: ${candidates.length}\n• Porcentagem qualificados: ${candidates.length > 0 ? Math.round(aboveCount/candidates.length*100) : 0}%\n\n💡 *Candidatos acima de 70% geralmente são bons matches.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('pontos fortes') && trimmedCommand.includes('comum')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para analisar pontos fortes em comum.`, timestamp: new Date() }
        } else {
          const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          const allSkills = selected.flatMap(c => c.skills || c.technical_skills || [])
          const skillCounts = allSkills.reduce((acc, s) => { if (s) acc[s] = (acc[s] || 0) + 1; return acc }, {} as Record<string, number>)
          const commonSkills = Object.entries(skillCounts).filter(([_, count]) => count >= Math.ceil(selected.length * 0.5)).map(([skill]) => skill)
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: commonSkills.length === 0 
              ? `📊 **Nenhuma skill em comum** encontrada entre os ${selected.length} candidatos selecionados.`
              : `📊 **Pontos fortes em comum** (${selected.length} candidatos):\n\n${commonSkills.slice(0, 8).map(s => `• **${s}**`).join('\n')}\n\n💡 *Essas são as skills compartilhadas pela maioria.*`,
            timestamp: new Date()
          }
        }
      }
      else if (trimmedCommand.includes('gaps') || trimmedCommand.includes('competência')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para identificar gaps de competência.`, timestamp: new Date() }
        } else {
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `🔍 **Análise de Gaps**\n\nPara identificar gaps precisos, preciso conhecer os requisitos da vaga.\n\n💡 **Sugestão:** Selecione uma vaga no seletor acima para comparar candidatos com os requisitos específicos.`,
            timestamp: new Date()
          }
        }
      }
      else if (trimmedCommand.includes('prioridade') || trimmedCommand.includes('organize')) {
        const sorted = [...candidates].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10)
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: sorted.length === 0 
            ? `📊 **Nenhum candidato** para organizar.\n\n💡 *Faça uma busca primeiro.*`
            : `📊 **Candidatos por prioridade:**\n\n${sorted.map((c, i) => `${i+1}. **${c.name}** - Score: ${formatScorePercent(c.score || 0)} | ${c.position || c.current_title || 'N/A'}`).join('\n')}\n\n💡 *Ordenados por score de compatibilidade.*`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('melhorar') && trimmedCommand.includes('busca')) {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `💡 **Dicas para melhorar sua busca:**\n\n• Adicione **skills específicas** (ex: "Python, AWS")\n• Defina **nível de senioridade** (júnior, pleno, sênior)\n• Especifique **localização** (cidade ou "remoto")\n• Use **palavras-chave** do cargo desejado\n• Tente **termos alternativos** para a mesma função\n\n**Exemplo:** "Desenvolvedor Backend Python sênior São Paulo remoto"`,
          timestamp: new Date()
        }
      }
      else if (trimmedCommand.includes('resuma') && trimmedCommand.includes('perfil') && trimmedCommand.includes('selecionado')) {
        if (selectedCandidatesForBatch.size === 0) {
          liaResponse = { id: `lia-${Date.now()}`, type: 'lia', content: `⚠️ **Selecione candidatos** para resumir seus perfis.`, timestamp: new Date() }
        } else {
          const selected = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
          const summary = selected.map(c => `**${c.name}**\n${c.position || c.current_title || 'Profissional'} @ ${c.current_company || 'N/A'}`).join('\n\n')
          liaResponse = {
            id: `lia-${Date.now()}`,
            type: 'lia',
            content: `📋 **Resumo dos perfis selecionados:**\n\n${summary}\n\n💡 *Para análise detalhada, use "Analisar potencial de crescimento".*`,
            timestamp: new Date()
          }
        }
      }
      // Comando não reconhecido - resposta amigável com orientação
      else {
        liaResponse = {
          id: `lia-${Date.now()}`,
          type: 'lia',
          content: `🤔 Entendi sua solicitação, mas **ainda não consigo responder a esse tipo de pergunta**.\n\nEstou em constante evolução e **em breve serei capaz** de atender você em diversas situações e demandas do seu dia a dia como recrutador!\n\n**Por enquanto, posso ajudar você com:**\n\n📊 **Análises de busca:**\n• Resumir esta busca\n• Top 5 candidatos\n• Skills mais comuns\n• Score médio dos candidatos\n\n👥 **Análise de candidatos selecionados:**\n• Analisar potencial de crescimento\n• Comparar candidatos\n• Pontos fortes em comum\n• Definir tipo de perfil\n\n💡 *Clique em "Mais ideias" para ver todas as opções disponíveis!*`,
          timestamp: new Date()
        }
      }

      setChatMessages(prev => [...prev, liaResponse])
    } catch (error) {
      console.error('handleAICommand error:', error)
      const errorMessage: ChatMessage = {
        id: `lia-error-${Date.now()}`,
        type: 'lia',
        content: `❌ Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.`,
        timestamp: new Date()
      }
      setChatMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLIAThinking(false)
    }
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
  const handleSendMessage = (data: any) => {
    console.log('Send message:', data)
    setShowContactModal(false)
  }

  const handleScheduleComplete = (data: any) => {
    console.log('Schedule complete:', data)
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

  const handleUnifiedModalSend = (data: any) => {
    console.log('Unified modal send:', data)
    toast({
      title: "Mensagem enviada!",
      description: `${data.type === 'email' ? 'Email' : data.type === 'whatsapp' ? 'WhatsApp' : data.type === 'triagem' ? 'Convite de triagem' : data.type === 'agendamento' ? 'Convite de entrevista' : 'Feedback'} enviado com sucesso.`,
    })
    handleUnifiedModalClose()
  }

  const handleBatchApprovalComplete = (data: any) => {
    console.log('Batch approval complete:', data)
    setShowBatchApproval(false)
    setSelectedCandidatesForBatch(new Set())
  }

  const handleAddCandidate = (newCandidate: any) => {
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

  // Handlers para configuração de colunas
  const handleToggleColumnConfig = () => {
    setShowColumnConfig(!showColumnConfig)
  }

  const handleSaveColumns = () => {
    // Salvar no localStorage
    localStorage.setItem('candidate-table-columns', JSON.stringify(tableColumns))
    console.log('Columns saved:', tableColumns)
    setShowColumnConfig(false)
  }

  const handleSaveColumnView = (view: any) => {
    const newView = {
      ...view,
      id: Date.now().toString(),
      createdAt: new Date().toISOString()
    }
    const updatedViews = [...savedColumnViews, newView]
    setSavedColumnViews(updatedViews)
    localStorage.setItem('candidate-column-views', JSON.stringify(updatedViews))
  }

  const handleLoadColumnView = (view: any) => {
    setTableColumns(view.columns)
  }

  const handleDeleteColumnView = (viewId: string) => {
    const updatedViews = savedColumnViews.filter(view => view.id !== viewId)
    setSavedColumnViews(updatedViews)
    localStorage.setItem('candidate-column-views', JSON.stringify(updatedViews))
  }

  // REMOVIDO: função renderExpandedRow para simplificação da tabela

  // Handlers para redimensionamento de colunas
  const startResize = (column: string, event: React.MouseEvent) => {
    event.preventDefault()

    const startX = event.clientX
    const startWidth = columnWidths[column as keyof typeof columnWidths]

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(80, startWidth + (e.clientX - startX))
      setColumnWidths(prev => ({
        ...prev,
        [column]: newWidth
      }))
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // Handlers para drag & drop de colunas
  const handleColumnDragStart = (columnId: string, e: React.DragEvent) => {
    setDraggedColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', columnId)
    
    // Criar imagem de drag invisível
    const dragImage = document.createElement('div')
    dragImage.style.opacity = '0'
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 0, 0)
    setTimeout(() => document.body.removeChild(dragImage), 0)
  }

  const handleColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedColumnId && draggedColumnId !== columnId && columnId !== 'checkbox' && columnId !== 'acoes') {
      setDragOverColumnId(columnId)
    }
  }

  const handleColumnDragLeave = () => {
    setDragOverColumnId(null)
  }

  const handleColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedColumnId || draggedColumnId === targetColumnId) {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }

    // Não permitir mover para checkbox ou ações
    if (targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedColumnId(null)
      setDragOverColumnId(null)
      return
    }

    setColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      
      if (draggedIndex === -1 || targetIndex === -1) return prev
      
      // Remove da posição atual e insere na nova posição
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedColumnId)
      
      // Salvar no localStorage
      localStorage.setItem('candidate-table-column-order', JSON.stringify(newOrder))
      
      return newOrder
    })

    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }

  const handleColumnDragEnd = () => {
    setDraggedColumnId(null)
    setDragOverColumnId(null)
  }

  // Carregar ordem salva ao inicializar com validação
  useEffect(() => {
    const defaultOrder = ['checkbox', 'id', 'candidato', 'cargo', 'empresa', 'salario_mensal', 'localizacao', 'modelo_trabalho', 'acoes']
    const savedOrder = localStorage.getItem('candidate-table-column-order')
    
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        
        // Validar e mesclar com a ordem padrão para evitar inconsistências
        const validOrder = defaultOrder.filter(id => parsed.includes(id))
        const newIds = defaultOrder.filter(id => !parsed.includes(id))
        
        // Se a ordem salva está válida e contém todas as colunas
        if (validOrder.length === defaultOrder.length) {
          // Manter colunas fixas (checkbox e acoes) nas posições corretas
          const orderedCols = parsed.filter((id: string) => defaultOrder.includes(id))
          const finalOrder = ['checkbox', ...orderedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes'), 'acoes']
          setColumnOrder(finalOrder)
        } else {
          // Ordem corrompida, usar padrão
          setColumnOrder(defaultOrder)
        }
      } catch (e) {
        console.error('Erro ao carregar ordem das colunas:', e)
        setColumnOrder(defaultOrder)
      }
    }
  }, [])


  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-950 overflow-hidden">
      {/* Header Fixo - Título e Tabs */}
      <div className="flex-shrink-0 px-4 pt-3 pb-0 bg-gray-50 dark:bg-gray-950">
        {/* Header Principal - Padrão Gestão de Vagas */}
        <div className="flex items-center justify-between mb-0.5">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black flex items-center gap-2">
                <Users className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                Funil de Talentos
              </h1>
            </div>
          </div>
          <div className="flex gap-2">
            {/* Botão Novo Candidato - visível em todas as abas */}
            <Button
              className="gap-2 h-8 px-3 font-medium"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
              onClick={() => setShowAddCandidateModal(true)}
            >
              <Plus className="w-4 h-4" />
              Novo Candidato
            </Button>

            {/* Botões específicos por aba */}
            {activeTab === 'search' && showSearchResults && (
              <>
                <Button
                  variant="outline"
                  className="gap-2 h-8 px-3"
                  onClick={() => {
                    setShowSearchResults(false)
                    setSearchTerm('')
                    setLastSearchQuery('')
                  }}
                >
                  <Search className="w-4 h-4" />
                  Nova Busca
                </Button>

                {/* Botão para salvar busca atual */}
                {(searchTerm || quickFilters.size > 0 || getActiveAdvancedFiltersCount() > 0) && (
                  <Button
                    variant="outline"
                    className="gap-2 h-8 px-3"
                    onClick={saveCurrentSearch}
                    title="Salvar esta busca para reutilizar"
                  >
                    <Bookmark className="w-4 h-4" />
                    Salvar Busca
                  </Button>
                )}
              </>
            )}

            {activeTab === 'favorites' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}

            {activeTab === 'history' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}

            {activeTab === 'saved-searches' && (
              <Button
                variant="outline"
                className="gap-2 h-8 px-3"
                onClick={() => setActiveTab('search')}
              >
                <Search className="w-4 h-4" />
                Nova Busca
              </Button>
            )}
          </div>
        </div>

        {/* Sistema de Abas - extraído para CandidateTabs (Sprint F5) */}
        <CandidateTabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={handleTabChangeWithWarning}
        />
      </div>

      {/* Área de Conteúdo Scrollável */}
      <div className="flex-1 flex flex-col overflow-hidden px-4 pt-2 pb-2">
        {/* Conteúdo das Abas */}
        
        {/* ========== TAB BUSCA (AI-First) — extraído para CandidateSearchBar (Sprint F5) ========== */}
        {activeTab === 'search' && !showSearchResults && (
          <CandidateSearchBar
            isSearchActive={isSearchActive}
            isDroppingCV={isDroppingCV}
            cvUploadLoading={cvUploadLoading}
            searchTerm={searchTerm}
            isLoading={isLoading}
            activeFiltersCount={getActiveSearchFiltersCount()}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            onSearchTermChange={setSearchTerm}
            onSubmit={async (query, entities, mode, metadata) => {
              setLastSearchQuery(query)
              setLastSearchMode(mode || 'natural')
              await executeSearch(query, entities, mode, metadata, false)
            }}
            onDrop={handleCVDrop}
            onDragOver={handleCVDragOver}
            onDragLeave={handleCVDragLeave}
            onOpenFilters={() => setShowAdvancedSearch(true)}
            onGoToResults={() => setShowSearchResults(true)}
            onSearchSourceChange={setSearchSource}
            onRequireEmailsChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requireEmails: value }))}
            onRequirePhoneNumbersChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: value }))}
          />
        )}

        {/* ========== TAB BUSCA - RESULTADOS INLINE ========== */}
        {activeTab === 'search' && showSearchResults && (
          <div className="flex flex-col h-[calc(100vh-9rem)] gap-2">
            {/* Header com query da busca e opções de edição — extraído para SearchResultsHeader (Sprint G3) */}
            <SearchResultsHeader
              lastSearchQuery={lastSearchQuery}
              lastSearchEntities={lastSearchEntities}
              onBack={() => setShowSearchResults(false)}
              onOpenEditQueryModal={(value) => {
                setEditQueryValue(value)
                setShowEditQueryModal(true)
              }}
              onOpenAdvancedSearch={() => setShowAdvancedSearch(true)}
            />

            {/* Contextual Actions Banner - Ações para candidatos selecionados */}
            <ContextualActionsBanner
              selectedCount={selectedCandidatesForBatch.size}
              pearchCount={selectedPearchCount}
              onDeselectAll={deselectAllCandidates}
              onAddToVacancy={() => setShowAddToVacancyModal(true)}
              onAddToList={handleAddToList}
              isAddingToList={isAddingToList}
              onShareSearch={() => {
                const selectedList = candidates.filter(c => selectedCandidatesForBatch.has(c.id))
                const searchTitle = lastSearchQuery || `Busca - ${new Date().toLocaleDateString('pt-BR')}`
                setShareSearchCandidates(selectedList.map(c => ({
                  id: c.id,
                  name: c.name,
                  email: c.email,
                  avatar_url: c.avatar,
                  current_title: c.position,
                  linkedin_url: c.linkedin
                })))
                setShareSearchTitle(searchTitle)
                setShowShareSearchModal(true)
              }}
              onSendMessage={handleBulkEmail}
              onWSIScreening={handleBulkWSIScreening}
              onToggleFavorite={() => {
                selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
                toast({
                  title: "Favoritos atualizados",
                  description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos`
                })
              }}
              onHide={() => {
                selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
                toast({
                  title: "Candidatos ocultos",
                  description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa`
                })
                deselectAllCandidates()
              }}
              onSaveToLocalBase={handleSaveToLocalBase}
              isSavingToBase={isSavingToBase}
            />

            {/* ✨ Banner Cross-Tab Filter */}
            {showCrossTabBanner && crossTabFilter && (
              <Card className="bg-gray-50 dark:bg-gray-800">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-900 dark:bg-gray-100 rounded-md flex items-center justify-center">
                      {crossTabFilter.type === 'company' ? (
                        <Building className="w-5 h-5 text-white dark:text-gray-900" />
                      ) : (
                        <Target className="w-5 h-5 text-white dark:text-gray-900" />
                      )}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                        🎯 Filtro Aplicado: {crossTabFilter.type === 'company' ? 'Empresa' : 'Inteligência Competitiva'}
                      </h3>
                      <p className="text-sm text-gray-800 dark:text-gray-400 mb-3">
                        {crossTabFilter.type === 'company' && crossTabFilter.company && (
                          `Mostrando candidatos da empresa "${crossTabFilter.company}" mapeada`
                        )}
                        {crossTabFilter.type === 'company' && crossTabFilter.companies && (
                          `Mostrando candidatos das empresas: ${crossTabFilter.companies.join(', ')}`
                        )}
                        {crossTabFilter.filter === 'discontented_talents' && (
                          `Talentos com indicações de descontentamento detectadas pela LIA`
                        )}
                      </p>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={clearCrossTabFilter}
                        >
                          <X className="w-3 h-3 mr-1" />
                          Limpar Filtro
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* ✨ Banner Visualizando Lista */}
            {viewingList && (
              <Card className="bg-gray-50 dark:bg-gray-800 border-l-4" style={{ borderLeftColor: viewingList.color || 'var(--gray-600)' }}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-10 h-10 rounded-md flex items-center justify-center"
                      style={{ backgroundColor: viewingList.color || 'var(--gray-600)' }}
                    >
                      <List className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                        📋 Visualizando Lista: {viewingList.name}
                      </h3>
                      <p className="text-sm text-gray-800 dark:text-gray-400">
                        {candidates.length} {candidates.length === 1 ? 'candidato' : 'candidatos'} nesta lista
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setViewingList(null)
                          setShowSearchResults(false)
                          setSearchTerm('')
                          setLastSearchQuery('')
                        }}
                      >
                        <X className="w-3 h-3 mr-1" />
                        Fechar Lista
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveTab('lists')}
                      >
                        <ArrowLeft className="w-3 h-3 mr-1" />
                        Voltar às Listas
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}


            {/* Toolbar Compacto - Prompt LIA + Controles */}
            {/* Esconde o prompt compacto quando o expandido estiver aberto */}
            {!showExpandedLIA && (
              <div className="flex items-center justify-between gap-4 mb-1 mt-1">
                {/* Prompt LIA - Compacto (max 300px) - Design Specs v3.1 */}
                <div className="flex-1 max-w-[300px]">
                  <div 
                    className={`relative flex items-center h-10 rounded-md bg-white transition-all ${
                      isLIAThinking ? 'cursor-wait' : ''
                    } border border-gray-200`} style={{ paddingLeft: '16px', paddingRight: '80px' }}
                  >
                    <input
                      type="text"
                      placeholder={isLIAThinking ? "LIA está pensando..." : "Ex: Analisar candidatos com..."}
                      value={liaPromptValue}
                      onChange={(e) => setLiaPromptValue(e.target.value)}
                      disabled={isLIAThinking}
                      className="flex-1 h-full text-base-ui bg-transparent focus:outline-none text-gray-950 placeholder:text-gray-600"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                      onFocus={(e) => {
                        // Focus state: borda cyan + shadow
                        const container = e.target.parentElement
                        if (container) {
                          container.style.borderColor = 'var(--gray-200)'
                          container.style.boxShadow = '0 0 0 2px rgba(96, 190, 209, 0.12)'
                        }
                        // Expandir LIA sidebar ao focar
                        if (!isLIAThinking) {
                          setShowExpandedLIA(true)
                        }
                      }}
                      onBlur={(e) => {
                        const container = e.target.parentElement
                        if (container) {
                          container.style.borderColor = 'var(--gray-200)'
                          container.style.boxShadow = 'none'
                        }
                      }}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' && liaPromptValue.trim() && !isLIAThinking) {
                          handleAICommand(liaPromptValue)
                          setLiaPromptValue('')
                        }
                      }}
                    />
                    {/* Botões: Maximize + Send */}
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                      <button
                        className="p-1.5 rounded-full hover:bg-gray-100 transition-colors"
                        onClick={() => setShowExpandedLIA(true)}
                        title="Expandir"
                        aria-label="Expandir chat da LIA"
                      >
                        <Maximize2 className="w-4 h-4 text-gray-700" aria-hidden="true" />
                      </button>
                      <button
                        className={`p-1.5 rounded-full transition-colors ${
                          isLIAThinking ? 'cursor-wait opacity-50' : 'hover:bg-gray-100'
                        }`}
                        onClick={() => {
                          if (liaPromptValue.trim() && !isLIAThinking) {
                            handleAICommand(liaPromptValue)
                            setLiaPromptValue('')
                          }
                        }}
                        disabled={isLIAThinking}
                        title="Enviar"
                        aria-label="Enviar mensagem para a LIA"
                      >
                        {isLIAThinking ? (
                          <div className="w-4 h-4 border-2 border-gray-900 dark:border-gray-50 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                        ) : (
                          <Send className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Indicador de Thinking - Aparece quando LIA está processando */}
                  {isLIAThinking && (
                    <div className="mt-2 flex items-center gap-2 text-xs px-3 py-1.5 rounded-md animate-fade-in" style={{ backgroundColor: 'rgba(229, 231, 235, 0.3)', border: '1px solid rgba(96, 190, 209, 0.2)' }}>
                      <Brain className="w-3 h-3 animate-pulse text-wedo-cyan" />
                      <span className="font-medium text-gray-800">LIA está pensando</span>
                      <div className="flex gap-0.5">
                        <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                        <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                        <span className="w-1 h-1 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                      </div>
                    </div>
                  )}
              </div>

              {/* Controles e Info - Sempre visíveis à direita */}
              <div className="flex items-center gap-3">
                {/* Badge de seleção */}
                {selectedCandidatesForBatch.size > 0 && (
                  <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0 text-xs font-medium">
                    🎯 {selectedCandidatesForBatch.size}
                  </Badge>
                )}

                {/* Sort indicator - mostra ordenação ativa (configuração dentro dos filtros) */}
                {searchSortBy !== 'relevance' && (
                  <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0 text-xs font-medium gap-1">
                    <ArrowUpDown className="w-3 h-3" />
                    {searchSortBy === 'score_desc' ? 'Maior Score' :
                     searchSortBy === 'score_asc' ? 'Menor Score' :
                     searchSortBy === 'name_asc' ? 'Nome A-Z' :
                     searchSortBy === 'name_desc' ? 'Nome Z-A' :
                     searchSortBy === 'experience_desc' ? 'Maior Experiência' : 'Relevância'}
                  </Badge>
                )}

                {/* Botão Selecionar Todos - Padronizado conforme design */}
                {selectedCandidatesForBatch.size === 0 && sortedCandidates.length > 0 && (
                  <button
                    onClick={selectAllCandidates}
                    className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-gray-800 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-colors"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                  >
                    <CheckCircle className="w-4 h-4 text-gray-500" />
                    Selecionar Todos
                  </button>
                )}

                {/* Botões de controle - Filtros da Tabela (tableFilters) - Padronizado */}
                <button
                  onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
                  className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
                    showTableFiltersPanel 
                      ? 'bg-gray-900 text-white hover:bg-gray-800' 
                      : 'text-gray-800 bg-white border border-gray-200 hover:bg-gray-50'
                  }`}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                >
                  <Target className="w-4 h-4" />
                  Filtros
                  {getActiveTableFiltersCount() > 0 && (
                    <span className={`text-xs font-medium ${showTableFiltersPanel ? 'text-gray-300' : 'text-gray-500'}`}>
                      {getActiveTableFiltersCount()}
                    </span>
                  )}
                </button>

                <button
                  onClick={handleToggleColumnConfig}
                  title="Configurar colunas da tabela"
                  className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
                    showColumnConfig 
                      ? 'bg-gray-900 text-white hover:bg-gray-800' 
                      : 'text-gray-800 bg-white border border-gray-200 hover:bg-gray-50'
                  }`}
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                >
                  <ChevronsLeftRight className="w-4 h-4" />
                  Colunas
                  <span className={`text-xs font-medium ${showColumnConfig ? 'text-gray-300' : 'text-gray-500'}`}>
                    {tableColumns.filter(col => col.visible && col.id !== 'acoes').length}
                  </span>
                </button>
              </div>
            </div>
            )}

            {/* Badge de Filtros Ativos - Simplificado */}
            {(quickFilters.size > 0 || searchTerm || getActiveAdvancedFiltersCount() > 0) && (
              <div className="mb-1.5 flex items-center gap-2">
                <Badge className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0">
                  filtros ativos
                </Badge>
                {selectedCandidatesForBatch.size > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={deselectAllCandidates}
                    className="h-6 px-2 text-xs text-gray-800 hover:text-gray-900"
                  >
                    <X className="w-3 h-3 mr-1" />
                    Limpar seleção
                  </Button>
                )}
              </div>
            )}


            {/* Results Layout with Sidebars - Layout flex responsivo */}
            {/* ORDEM: LIA à esquerda, Filtros à direita, Tabela ao centro */}
            <div className="flex gap-4 overflow-hidden transition-all duration-300 flex-1 min-h-0 w-full">
              {/* LIA Sidebar Expandida - Sistema de Pesquisa Avançada */}
              {showExpandedLIA && (
                <div 
                  className={`transition-all duration-300 relative group ${isLiaSuperChat ? 'flex-1 z-10' : 'flex-shrink-0'}`}
                  style={{ 
                    width: isLiaSuperChat ? 'auto' : `${liaWidth}px`,
                    maxWidth: isLiaSuperChat ? 'none' : `${liaWidth}px`
                  }}
                >
                  <Card className="h-[calc(100vh-9rem)] flex flex-col overflow-hidden border border-gray-300" style={{ backgroundColor: 'var(--gray-50)' }}>
                    {/* Header do Prompt Expandido - Design Specs v3.1 */}
                    <div className="flex-shrink-0 px-4 py-3" style={{ backgroundColor: 'var(--gray-50)' }}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div 
                            className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0"
                            style={{ backgroundColor: 'var(--gray-50)' }}
                          >
                            <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="text-sm font-semibold leading-tight truncate text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              Olá! Sou a Lia.
                            </h3>
                            <p className="text-xs leading-tight truncate mt-0.5 text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              Posso criar vagas, buscar candidatos, analisar métricas e muito mais!
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {/* Botão Expandir/Retrair Superchat */}
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => {
                                    if (isLiaSuperChat) {
                                      setIsLiaSuperChat(false)
                                    } else {
                                      setIsLiaSuperChat(true)
                                      setSuperChatWidth(Math.max(superChatWidth, 600))
                                    }
                                  }}
                                  className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                                >
                                  {isLiaSuperChat ? (
                                    <PanelLeftClose className="w-4 h-4 text-gray-700" />
                                  ) : (
                                    <Maximize2 className="w-4 h-4 text-gray-500" />
                                  )}
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p className="text-xs">{isLiaSuperChat ? 'Retrair chat' : 'Expandir para Superchat'}</p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                          {/* Botão Fechar */}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setShowExpandedLIA(false)
                              setUserCollapsedLIA(true)
                              setIsLiaSuperChat(false)
                            }}
                            className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                          >
                            <X className="w-4 h-4 text-gray-500" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Ações movidas para banner acima da tabela */}

                    {/* Conteúdo das Abas */}
                    <div className="flex-1 overflow-y-auto p-4 mx-3 mb-3 rounded-md" style={{ backgroundColor: 'var(--gray-50)' }}>
                      
                      {/* ABA 1: IA NATURAL - Chat Format */}
                      {activeSearchTab === 'ia-natural' && (
                        <div className="flex flex-col h-full" style={{ minHeight: '400px' }}>
                          {/* Área de Chat - Histórico de Mensagens */}
                          <div 
                            ref={chatScrollRef}
                            className="flex-1 overflow-y-auto space-y-3 mb-4"
                            style={{ maxHeight: 'calc(100% - 80px)' }}
                          >
                            {/* Resultado da Busca (como resposta da LIA) - PRIMEIRO cronologicamente */}
                            {searchResults.query && (
                              <div className="space-y-3">
                                {/* Mensagem do usuário */}
                                <div className="flex justify-end">
                                  <div className="max-w-[85%] p-3 rounded-md bg-gray-900 dark:bg-gray-50 text-white">
                                    <p className="text-xs" style={{ fontFamily: 'Open Sans, sans-serif' }}>{searchResults.query}</p>
                                  </div>
                                </div>
                                
                                {/* Resposta da LIA */}
                                <div className="flex items-start gap-2">
                                  <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                                    <LIAIcon size="xs" />
                                  </div>
                                  <div className="flex-1 space-y-3">
                                    {/* Resumo dos resultados */}
                                    <div className="p-3 rounded-md bg-white dark:bg-gray-800">
                                      <p className="text-xs font-medium text-gray-950 dark:text-gray-50 mb-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                        Encontrei <span className="text-gray-600 dark:text-gray-400">{searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0)} candidato{(searchResults.localCount + (searchResults.showGlobalResults ? searchResults.globalCount : 0)) > 1 ? 's' : ''}</span> para sua busca:
                                      </p>
                                      <div className="flex items-center gap-3 text-xs mb-2">
                                        {searchResults.localCount > 0 && (
                                          <div className="flex items-center gap-1 text-emerald-600">
                                            <Home className="w-3 h-3" />
                                            <span className="font-medium">{searchResults.localCount} base local</span>
                                          </div>
                                        )}
                                        {searchResults.showGlobalResults && searchResults.globalCount > 0 && (
                                          <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
                                            <Globe className="w-3 h-3" />
                                            <span className="font-medium">{searchResults.globalCount} busca global</span>
                                          </div>
                                        )}
                                      </div>
                                      <div className="flex items-center justify-between mt-2">
                                        <p className="text-xs text-gray-800 dark:text-gray-400 flex items-center gap-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                          <TrendingUp className="w-3 h-3" />
                                          Ordenados por aderência ao perfil
                                        </p>
                                        <button
                                          onClick={() => {
                                            setShowSaveAsArchetypeModal(true)
                                            setArchetypeNameInput('')
                                            setArchetypeEmojiInput('🎯')
                                          }}
                                          className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full border border-gray-900 dark:border-gray-50 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:bg-gray-800 transition-all"
                                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                                        >
                                          <Bookmark className="w-3 h-3" />
                                          Salvar Arquétipo
                                        </button>
                                      </div>
                                    </div>
                                    
                                    {/* Candidatos locais na tabela */}
                                    {searchResults.localCount > 0 && (
                                      <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                                        <div className="flex items-center gap-2">
                                          <Home className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                                          <p className="text-xs text-gray-800 dark:text-gray-300" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                            <span className="font-semibold">{searchResults.localCount} candidatos</span> da base local exibidos na tabela
                                          </p>
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Botão para expandir busca para global - OPT-IN: só mostra após busca local */}
                                    {currentSearchSource === 'local' && !searchResults.showGlobalResults && !searchResults.globalDismissed && searchResults.query && (
 <div className="p-3 rounded-md border border-gray-900 dark:border-gray-200 bg-gray-50 dark:bg-gray-800">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-2">
                                            <Globe className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                            <div>
                                              <p className="text-xs font-medium text-blue-900 dark:text-blue-300">
                                                Expandir para Busca Global?
                                              </p>
                                              <p className="text-xs text-gray-600 dark:text-gray-400">
                                                Acesse +800M de perfis (1 crédito/candidato)
                                              </p>
                                            </div>
                                          </div>
                                          <div className="flex items-center gap-2">
                                            <Button
                                              size="sm"
                                              variant="ghost"
                                              className="!text-xs !px-2.5 !py-1.5 text-gray-800 hover:text-gray-950 hover:bg-gray-100 dark:hover:bg-gray-800"
                                              style={{ fontFamily: 'Open Sans, sans-serif' }}
                                              onClick={() => {
                                                setSearchResults(prev => ({ ...prev, globalDismissed: true }))
                                              }}
                                            >
                                              <X className="w-3 h-3 mr-1" />
                                              Manter local
                                            </Button>
                                            <Button
                                              size="sm"
                                              className="!text-xs !px-3 !py-1.5 bg-gray-900" style={{ color: 'var(--gray-50)', fontFamily: 'Open Sans, sans-serif' }}
                                              onClick={() => setShowGlobalExpansionConfirm(true)}
                                            >
                                              <Globe className="w-3 h-3 mr-1" />
                                              Expandir Busca
                                            </Button>
                                          </div>
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Mensagem quando usuário descartou busca global */}
                                    {currentSearchSource === 'local' && searchResults.globalDismissed && !searchResults.showGlobalResults && searchResults.query && (
                                      <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-800/50">
                                        <div className="flex items-center justify-between">
                                          <div className="flex items-center gap-2">
                                            <Globe className="w-3.5 h-3.5 text-gray-800" />
                                            <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                              Busca global disponível
                                            </p>
                                          </div>
                                          <button
                                            onClick={() => setSearchResults(prev => ({ ...prev, globalDismissed: false }))}
                                            className="text-xs text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark hover:underline"
                                            style={{ fontFamily: 'Open Sans, sans-serif' }}
                                          >
                                            Expandir busca
                                          </button>
                                        </div>
                                      </div>
                                    )}
                                    
                                    {/* Confirmação de candidatos globais adicionados */}
                                    {searchResults.showGlobalResults && searchResults.globalCount > 0 && (
 <div className="p-2.5 rounded-md bg-gray-50 dark:bg-gray-800 border border-gray-900 dark:border-gray-200">
                                        <div className="flex items-center gap-2">
                                          <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
 <p className="text-xs text-wedo-cyan-dark dark:text-gray-300" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                            <span className="font-semibold">{searchResults.globalCount} candidatos</span> globais adicionados à tabela
                                          </p>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* Loading - LIA Buscando */}
                            {searchResults.isLoading && (
                              <div className="space-y-3">
                                {/* Mensagem do usuário (query atual) */}
                                {searchResults.query && (
                                  <div className="flex justify-end">
                                    <div className="max-w-[85%] p-3 rounded-md bg-gray-900 dark:bg-gray-50 text-white">
                                      <p className="text-xs" style={{ fontFamily: 'Open Sans, sans-serif' }}>{searchResults.query}</p>
                                    </div>
                                  </div>
                                )}
                                
                                {/* LIA Pensando */}
                                <div className="flex items-start gap-2">
                                  <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse" style={{ backgroundColor: 'rgba(96, 190, 209, 0.2)' }}>
                                    <LIAIcon size="xs" />
                                  </div>
                                  <div className="flex-1 space-y-2">
                                    {/* Card de status */}
                                    <div className="p-4 rounded-md bg-gray-50 dark:bg-gray-800/50">
                                      <div className="flex items-center gap-3 mb-3">
                                        <div className="relative">
                                          <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                                            <Search className="w-4 h-4 text-gray-600 dark:text-gray-400 animate-pulse" />
                                          </div>
                                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-gray-900 dark:bg-gray-50 rounded-full animate-ping" />
                                        </div>
                                        <div>
                                          <p className="text-xs font-medium text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                            LIA está buscando...
                                          </p>
                                          <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                            Analisando perfis compatíveis
                                          </p>
                                        </div>
                                      </div>
                                      
                                      {/* Progress steps */}
                                      <div className="space-y-2">
                                        <div className="flex items-center gap-2 text-xs text-gray-800 dark:text-gray-500">
                                          <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                                            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                            </svg>
                                          </div>
                                          <span style={{ fontFamily: 'Open Sans, sans-serif' }}>Interpretando critérios</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-gray-800 dark:text-gray-500">
                                          <div className="w-4 h-4 rounded-full bg-gray-900 dark:bg-gray-50 flex items-center justify-center animate-spin">
                                            <div className="w-2 h-2 border border-white border-t-transparent rounded-full" />
                                          </div>
                                          <span style={{ fontFamily: 'Open Sans, sans-serif' }}>Buscando na base de candidatos</span>
                                        </div>
                                        <div className="flex items-center gap-2 text-xs text-gray-800">
                                          <div className="w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-700" />
                                          <span style={{ fontFamily: 'Open Sans, sans-serif' }}>Rankeando por compatibilidade</span>
                                        </div>
                                      </div>
                                    </div>
                                    
                                    {/* Typing indicator */}
                                    <div className="flex items-center gap-1.5 px-3 py-2">
                                      <div className="flex gap-1">
                                        <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <div className="w-2 h-2 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* Mensagens do Chat - DEPOIS dos resultados da busca (ordem cronológica) */}
                            {chatMessages.map((msg) => (
                              <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.type === 'user' ? (
                                  /* User Message - Alinhado à direita, balão cinza claro com avatar */
                                  <div className="flex items-start gap-2 max-w-[70%]">
                                    <img 
                                      src="https://randomuser.me/api/portraits/men/32.jpg" 
                                      alt="Você"
                                      className="w-7 h-7 rounded-full object-cover flex-shrink-0"
                                    />
                                    <div 
                                      className="px-2.5 py-2 rounded-2xl bg-gray-100"
                                      style={{ fontFamily: '"Open Sans", sans-serif' }}
                                    >
                                      <div className="flex items-center gap-1.5 mb-0.5">
                                        <span className="text-micro font-bold text-gray-800">Você</span>
                                        <span className="text-micro text-gray-500">agora</span>
                                      </div>
                                      <p className="text-xs text-gray-800 leading-relaxed">{msg.content}</p>
                                    </div>
                                  </div>
                                ) : msg.type === 'proactive_insight' && msg.analytics ? (
                                  <div className="w-full">
                                    <ProactiveInsightCard
                                      analytics={msg.analytics}
                                      onAction={handleQuickAction}
                                      isExpanded={false}
                                    />
                                  </div>
                                ) : msg.type === 'calibration' && msg.candidates ? (
                                  <div className="w-full space-y-3">
                                    <div className="flex items-start gap-2">
                                      <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                                        <LIAIcon size="xs" />
                                      </div>
                                      <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                        Vou mostrar alguns candidatos para entender melhor o perfil que você busca:
                                      </p>
                                    </div>
                                    <div className="space-y-2 pl-8">
                                      {msg.candidates.map(candidate => (
                                        <CalibrationCard
                                          key={candidate.id}
                                          candidate={candidate}
                                          onLike={handleCalibrationLike}
                                          onDislike={handleCalibrationDislike}
                                        />
                                      ))}
                                    </div>
                                  </div>
                                ) : (
                                  <div className="max-w-[90%]">
                                    <div className="flex items-start gap-2">
                                      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                                        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                                      </div>
                                      <div className="flex-1">
                                        <span className="text-micro font-bold text-gray-800" style={{ fontFamily: 'Inter, sans-serif' }}>LIA</span>
                                        <p className="text-xs text-gray-800 leading-relaxed whitespace-pre-wrap mt-0.5">
                                          {msg.content.split(/(\*\*[^*]+\*\*)/).map((part, i) => 
                                            part.startsWith('**') && part.endsWith('**') 
                                              ? <strong key={i}>{part.slice(2, -2)}</strong>
                                              : part
                                          )}
                                        </p>
                                        {msg.metadata?.action_executed && msg.metadata?.action_result && (
                                          <ActionResultCard
                                            actionType={msg.metadata.action_type || 'analyze_profile'}
                                            result={msg.metadata.action_result}
                                          />
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                          
                          {/* Input de Chat - Fixo na parte inferior - Layout Inline Padronizado */}
                          <div className="mt-auto p-3 bg-white rounded-md">
                            {/* Banner de criação de arquétipo */}
                            {isCreatingArchetype && (
                              <div className="mb-2 p-2 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Target className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                    Criando novo arquétipo...
                                  </span>
                                </div>
                                <button
                                  onClick={() => {
                                    setIsCreatingArchetype(false)
                                    setArchetypeCreationStep('initial')
                                  }}
                                  className="p-1 hover:bg-gray-100 dark:bg-gray-800 rounded"
                                  aria-label="Cancelar criação de arquétipo"
                                >
                                  <X className="w-3 h-3 text-gray-600 dark:text-gray-400" aria-hidden="true" />
                                </button>
                              </div>
                            )}
                            {/* Input Inline Padronizado - Design Specs v3.1 */}
                            <div className="flex items-center gap-2 p-2 rounded-md bg-white border border-gray-100">
                              <div 
                                className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center"
                              >
                                <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                              </div>
                              <input
                                type="text"
                                placeholder={isCreatingArchetype
                                  ? "Cole a descrição da vaga ou descreva o perfil ideal..."
                                  : "Envie mensagem para a LIA..."
                                }
                                aria-label={isCreatingArchetype ? "Descrição do perfil ideal para arquétipo" : "Mensagem para a LIA"}
                                value={liaPromptValue}
                                onChange={(e) => setLiaPromptValue(e.target.value)}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && liaPromptValue.trim()) {
                                    if (isCreatingArchetype) {
                                      const userMessage: ChatMessage = {
                                        id: `user-${Date.now()}`,
                                        type: 'user',
                                        content: liaPromptValue.trim(),
                                        timestamp: new Date()
                                      }
                                      setChatMessages(prev => [...prev, userMessage])
                                      
                                      setTimeout(() => {
                                        const extractedName = liaPromptValue.length > 50 
                                          ? liaPromptValue.substring(0, 50).split(' ').slice(0, 5).join(' ')
                                          : liaPromptValue.trim()
                                        
                                        const liaResponse: ChatMessage = {
                                          id: `lia-extraction-${Date.now()}`,
                                          type: 'lia',
                                          content: `✅ Analisei sua descrição e identifiquei os critérios principais.\n\n**Arquétipo sugerido:** ${extractedName}\n\nClique em "Salvar Arquétipo" abaixo para confirmar, ou continue descrevendo para refinar.`,
                                          timestamp: new Date()
                                        }
                                        setChatMessages(prev => [...prev, liaResponse])
                                        
                                        setNewArchetypeData({
                                          name: extractedName,
                                          description: liaPromptValue.trim(),
                                          query: liaPromptValue.trim(),
                                          emoji: '🎯'
                                        })
                                        setArchetypeCreationStep('review')
                                        setShowSaveAsArchetypeModal(true)
                                        setArchetypeNameInput(extractedName)
                                      }, 1000)
                                      
                                      setLiaPromptValue('')
                                    } else {
                                      handleLIAChatMessage(liaPromptValue.trim())
                                    }
                                  }
                                }}
                                className="flex-1 text-xs bg-transparent focus:outline-none text-gray-950 dark:text-gray-50"
                                style={{ fontFamily: 'Open Sans, sans-serif' }}
                              />
                              <AudioRecordButton
                                onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
                                className="p-1.5"
                                iconClassName="w-4 h-4"
                              />
                              <button
                                type="button"
                                onClick={() => {
                                  if (liaPromptValue.trim()) {
                                    if (isCreatingArchetype) {
                                      const userMessage: ChatMessage = {
                                        id: `user-${Date.now()}`,
                                        type: 'user',
                                        content: liaPromptValue.trim(),
                                        timestamp: new Date()
                                      }
                                      setChatMessages(prev => [...prev, userMessage])
                                      
                                      setTimeout(() => {
                                        const extractedName = liaPromptValue.length > 50 
                                          ? liaPromptValue.substring(0, 50).split(' ').slice(0, 5).join(' ')
                                          : liaPromptValue.trim()
                                        
                                        const liaResponse: ChatMessage = {
                                          id: `lia-extraction-${Date.now()}`,
                                          type: 'lia',
                                          content: `✅ Analisei sua descrição e identifiquei os critérios principais.\n\n**Arquétipo sugerido:** ${extractedName}\n\nClique em "Salvar Arquétipo" abaixo para confirmar, ou continue descrevendo para refinar.`,
                                          timestamp: new Date()
                                        }
                                        setChatMessages(prev => [...prev, liaResponse])
                                        
                                        setNewArchetypeData({
                                          name: extractedName,
                                          description: liaPromptValue.trim(),
                                          query: liaPromptValue.trim(),
                                          emoji: '🎯'
                                        })
                                        setArchetypeCreationStep('review')
                                        setShowSaveAsArchetypeModal(true)
                                        setArchetypeNameInput(extractedName)
                                      }, 1000)
                                      
                                      setLiaPromptValue('')
                                    } else {
                                      handleLIAChatMessage(liaPromptValue.trim())
                                    }
                                  }
                                }}
                                disabled={!liaPromptValue.trim() || searchResults.isLoading}
                                className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors disabled:opacity-50 bg-gray-900"
                              >
                                <Send className="w-3.5 h-3.5 text-white" />
                              </button>
                            </div>
                            
                            {/* Sugestões - abaixo do input conforme design specs */}
                            <div className="flex items-center gap-1.5 mt-1.5">
                              <span className="text-micro font-medium text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>Sugestões:</span>
                              <button
                                onClick={() => handleAICommand('Top 5 candidatos')}
                                className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium rounded-full transition-all"
                                style={{ fontFamily: 'Open Sans, sans-serif' }}
                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--gray-200)'}
                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--gray-50)'}
                              >
                                <Star className="w-2.5 h-2.5 text-gray-500" />
                                Top 5
                              </button>
                              <button
                                onClick={() => handleAICommand('Resumir esta busca')}
                                className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium rounded-full transition-all"
                                style={{ fontFamily: 'Open Sans, sans-serif' }}
                                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--gray-200)'}
                                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--gray-50)'}
                              >
                                <FileText className="w-2.5 h-2.5 text-gray-500" />
                                Resumir busca
                              </button>
                              <LiaSearchQueriesGuide
                                onSelectQuery={(query) => handleAICommand(query)}
                                selectedCount={selectedCandidatesForBatch.size}
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Abas removidas: JOB DESCRIPTION, SIMILAR, BOOLEAN - funcionalidades movidas para página principal */}
                      {activeSearchTab === 'job-description' && (
                        <div className="space-y-4">
                          {/* Descrição */}
                          <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                            Cole sua descrição de vaga e a IA extrairá os critérios automaticamente
                          </p>

                          {/* Textarea Grande */}
                          <div className="relative">
                            <textarea
                              placeholder="Cole aqui a descrição da vaga completa..."
                              value={jobDescriptionText}
                              onChange={(e) => setJobDescriptionText(e.target.value)}
                              className="w-full h-48 p-4 pb-12 text-xs rounded-md border focus:outline-none transition-all resize-none bg-white dark:bg-gray-800 text-gray-950 dark:text-gray-50 border border-gray-100" style={{ fontFamily: 'Open Sans, sans-serif' }}
                              onFocus={(e) => e.target.style.borderColor = 'var(--gray-200)'}
                              onBlur={(e) => e.target.style.borderColor = 'var(--gray-50)'}
                            />
                            {/* Botões de Anexo e Áudio */}
                            <div className="absolute bottom-3 right-3 flex gap-2">
                              <button
                                type="button"
                                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                                title="Anexar documento"
                                onClick={() => {
                                  // TODO: Implementar upload de arquivo
                                  console.log('Anexar documento')
                                }}
                              >
                                <Paperclip className="w-4 h-4 text-gray-800" />
                              </button>
                              <button
                                type="button"
                                className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                                title="Gravar áudio"
                                onClick={() => {
                                  // TODO: Implementar gravação de áudio
                                  console.log('Gravar áudio')
                                }}
                              >
                                <Mic className="w-4 h-4 text-gray-800" />
                              </button>
                            </div>
                          </div>

                          {/* Critérios Extraídos */}
                          {extractedJDCriteria && (
                            <div className="p-3 rounded-md border" style={{ backgroundColor: 'rgba(96, 190, 209, 0.06)', borderColor: 'rgba(96, 190, 209, 0.3)' }}>
                              <div className="flex items-center gap-2 mb-2">
                                <Brain className="w-4 h-4 text-wedo-cyan" />
                                <span className="text-xs font-medium text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                  Critérios Extraídos
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {extractedJDCriteria.job_title && (
                                  <span className="px-2 py-1 text-xs rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark">
                                    {extractedJDCriteria.job_title}
                                  </span>
                                )}
                                {extractedJDCriteria.seniority && (
                                  <span className="px-2 py-1 text-xs rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark">
                                    {extractedJDCriteria.seniority}
                                  </span>
                                )}
                                {extractedJDCriteria.skills.map((skill, idx) => (
                                  <span key={idx} className="px-2 py-1 text-xs rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark">
                                    {skill}
                                  </span>
                                ))}
                                {extractedJDCriteria.experience_years && (
                                  <span className="px-2 py-1 text-xs rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark">
                                    {extractedJDCriteria.experience_years}+ anos
                                  </span>
                                )}
                                {extractedJDCriteria.location && (
                                  <span className="px-2 py-1 text-xs rounded-full bg-wedo-cyan/20 text-wedo-cyan-dark">
                                    {extractedJDCriteria.location}
                                  </span>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Botão Extrair e Buscar */}
                          <Button
                            className="w-full h-11 !text-sm font-semibold gap-2"
                            style={{
                              backgroundColor: isSearchingJD ? 'var(--gray-400)' : 'var(--gray-950)',
                              color: 'var(--gray-50)',
                              fontFamily: 'Open Sans, sans-serif'
                            }}
                            onClick={async () => {
                              if (jobDescriptionText.trim() && !isSearchingJD) {
                                setIsSearchingJD(true)
                                setExtractedJDCriteria(null)
                                
                                const userMessage: ChatMessage = {
                                  id: `user-jd-${Date.now()}`,
                                  type: 'user',
                                  content: `Buscar candidatos pela descrição da vaga:\n\n"${jobDescriptionText.substring(0, 200)}${jobDescriptionText.length > 200 ? '...' : ''}"`,
                                  timestamp: new Date()
                                }
                                setChatMessages(prev => [...prev, userMessage])
                                
                                try {
                                  const response = await fetch('/api/backend-proxy/search/candidates/by-job-description', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      job_description: jobDescriptionText.trim(),
                                      limit: 20,
                                      search_pearch: searchSource !== 'local',
                                      pearch_type: pearchSearchOptions.searchType
                                    })
                                  })
                                  
                                  if (!response.ok) throw new Error('Erro na busca')
                                  
                                  const data = await response.json()
                                  
                                  if (data.extracted_criteria) {
                                    setExtractedJDCriteria({
                                      job_title: data.extracted_criteria.job_title,
                                      seniority: data.extracted_criteria.seniority,
                                      skills: data.extracted_criteria.skills || [],
                                      experience_years: data.extracted_criteria.experience_years,
                                      location: data.extracted_criteria.location,
                                      languages: data.extracted_criteria.languages || []
                                    })
                                  }
                                  
                                  if (data.candidates && data.candidates.length > 0) {
                                    const mappedCandidates = data.candidates.map((c: any) => ({
                                      id: c.id || `jd-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                                      candidateId: c.id?.substring(0, 8).toUpperCase() || 'JD',
                                      name: c.name || 'Nome não disponível',
                                      email: c.email || '',
                                      phone: c.phone || '',
                                      current_title: c.headline || c.current_title || '',
                                      current_company: c.current_company || '',
                                      location: c.location || '',
                                      linkedin_url: c.linkedin_url,
                                      avatar_url: c.avatar_url || c.picture_url,
                                      avatar: c.avatar_url,
                                      technical_skills: c.skills || [],
                                      skills: c.skills || [],
                                      seniority_level: c.seniority_level,
                                      years_of_experience: c.years_experience || c.total_experience_years,
                                      experience: c.years_experience || c.total_experience_years || 0,
                                      score: c.match_score ? Math.round(c.match_score * 25) : 75,
                                      source: c.source || 'pearch',
                                      has_email: c.has_email ?? true,
                                      has_phone: c.has_phone ?? true,
                                      is_opentowork: c.is_opentowork,
                                      is_decision_maker: c.is_decision_maker,
                                      is_top_universities: c.is_top_universities,
                                      is_startup: c.is_startup || c.company_info?.is_startup,
                                      expertise: c.expertise,
                                      outreach_message: c.outreach_message,
                                      experiences: c.experiences || [],
                                      workHistory: (c.experiences || []).map((exp: any) => ({
                                        company: exp.company_info?.name || exp.company || '',
                                        title: exp.company_roles?.[0]?.title || exp.title || '',
                                        startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                                        endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                                        duration: exp.duration || '',
                                        location: exp.company_info?.location || exp.location || '',
                                        description: exp.company_roles?.[0]?.description || exp.description || ''
                                      })),
                                      education: (c.education || []).map((edu: any) => ({
                                        school: edu.school || '',
                                        degree: edu.degree || '',
                                        field_of_study: edu.field_of_study || '',
                                        fieldOfStudy: edu.field_of_study || '',
                                        startDate: edu.start_date || '',
                                        endDate: edu.end_date || ''
                                      }))
                                    }))
                                    
                                    const localCandidates = mappedCandidates.filter((c: any) => c.source === 'local')
                                    const globalCandidates = mappedCandidates.filter((c: any) => c.source === 'pearch')
                                    
                                    // Respeitar searchSource selecionado pelo usuário
                                    const shouldAutoShowGlobal = searchSource === 'global' || searchSource === 'hybrid'
                                    const candidatesForTable = shouldAutoShowGlobal ? mappedCandidates : localCandidates
                                    
                                    setCandidates(candidatesForTable)
                                    setHasSearchResults(true)
                                    setSearchResultsCount(data.total_count || mappedCandidates.length)
                                    setLocalResultsCount(data.local_count || localCandidates.length)
                                    setPearchResultsCount(data.pearch_count || globalCandidates.length)
                                    setShowSearchResults(true)
                                    setDisplayedResultsCount(10)
                                    
                                    setSearchResults(prev => ({
                                      local: localCandidates,
                                      global: globalCandidates,
                                      localCount: data.local_count || localCandidates.length,
                                      globalCount: data.pearch_count || globalCandidates.length,
                                      query: data.query_generated || jobDescriptionText.substring(0, 50),
                                      isLoading: false,
                                      showGlobalResults: shouldAutoShowGlobal,
                                      globalDismissed: prev.globalDismissed
                                    }))
                                    
                                    const localCount = data.local_count || localCandidates.length
                                    const liaMessage: ChatMessage = {
                                      id: `lia-jd-result-${Date.now()}`,
                                      type: 'lia',
                                      content: `**Busca por Job Description concluída!**\n\nQuery gerada: "${data.query_generated}"\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''}** na sua base local.`,
                                      timestamp: new Date(),
                                      searchResults: {
                                        localCount: localCount,
                                        globalCount: 0,
                                        query: data.query_generated || ''
                                      }
                                    }
                                    setChatMessages(prev => [...prev, liaMessage])
                                  } else {
                                    const liaMessage: ChatMessage = {
                                      id: `lia-jd-noresult-${Date.now()}`,
                                      type: 'lia',
                                      content: `Não encontrei candidatos com os critérios extraídos da descrição da vaga.\n\nTente ajustar a descrição ou usar a busca por IA Natural com termos mais específicos.`,
                                      timestamp: new Date()
                                    }
                                    setChatMessages(prev => [...prev, liaMessage])
                                  }
                                } catch (error) {
                                  console.error('Erro na busca por JD:', error)
                                  const liaMessage: ChatMessage = {
                                    id: `lia-jd-error-${Date.now()}`,
                                    type: 'lia',
                                    content: `Erro ao buscar candidatos pela descrição da vaga. Por favor, tente novamente.`,
                                    timestamp: new Date()
                                  }
                                  setChatMessages(prev => [...prev, liaMessage])
                                } finally {
                                  setIsSearchingJD(false)
                                }
                              }
                            }}
                            disabled={!jobDescriptionText.trim() || jobDescriptionText.length < 50 || isSearchingJD}
                          >
                            {isSearchingJD ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Analisando...
                              </>
                            ) : (
                              <>
                                <span 
                                  className="flex items-center justify-center w-5 h-5 rounded bg-gray-900"
                                >
                                  <Brain className="w-3 h-3 text-white" />
                                </span>
                                Extrair e Buscar
                              </>
                            )}
                          </Button>
                          
                          {jobDescriptionText.length > 0 && jobDescriptionText.length < 50 && (
                            <p className="text-xs text-amber-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              A descrição precisa ter pelo menos 50 caracteres para análise adequada.
                            </p>
                          )}
                        </div>
                      )}

                      {/* ABA 4: SIMILAR */}
                      {activeSearchTab === 'similar' && (
                        <div className="space-y-4">
                          <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                            Encontre candidatos similares a um perfil específico
                          </p>
                          
                          <div className="relative">
                            <input
                              type="text"
                              value={similarProfileUrl}
                              onChange={(e) => setSimilarProfileUrl(e.target.value)}
                              placeholder="Cole o link do LinkedIn ou nome do candidato..."
                              className="w-full p-3 text-xs rounded-md border focus:outline-none transition-all bg-white dark:bg-gray-800 text-gray-950 dark:text-gray-50 border border-gray-100" style={{ fontFamily: 'Open Sans, sans-serif' }}
                            />
                          </div>
                          
                          <div className="p-3 rounded-md" style={{ backgroundColor: 'rgba(96, 190, 209, 0.06)' }}>
                            <div className="flex items-start gap-2">
                              <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700" />
                              <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                <strong>Dica:</strong> Cole o link do LinkedIn de um candidato que você considera ideal para encontrar perfis similares.
                              </p>
                            </div>
                          </div>

                          <Button
                            className={`w-full h-11 !text-sm font-semibold text-white font-open-sans ${isSearchingSimilar ? 'bg-gray-400' : 'bg-wedo-cyan-dark'}`}
                            onClick={async () => {
                              if (similarProfileUrl.trim() && !isSearchingSimilar) {
                                setIsSearchingSimilar(true)
                                
                                const isLinkedInUrl = similarProfileUrl.includes('linkedin.com/in/')
                                
                                const userMessage: ChatMessage = {
                                  id: `user-similar-${Date.now()}`,
                                  type: 'user',
                                  content: isLinkedInUrl 
                                    ? `Buscar candidatos similares ao perfil: ${similarProfileUrl}` 
                                    : `Buscar candidatos similares: ${similarProfileUrl}`,
                                  timestamp: new Date()
                                }
                                setChatMessages(prev => [...prev, userMessage])
                                
                                try {
                                  const requestBody: { linkedin_url?: string; candidate_id?: string; limit: number; search_pearch: boolean; pearch_type: string } = {
                                    limit: 20,
                                    search_pearch: searchSource !== 'local',
                                    pearch_type: pearchSearchOptions.searchType
                                  }
                                  
                                  if (isLinkedInUrl) {
                                    requestBody.linkedin_url = similarProfileUrl.trim()
                                  } else {
                                    requestBody.candidate_id = similarProfileUrl.trim()
                                  }
                                  
                                  const response = await fetch('/api/backend-proxy/search/candidates/similar', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify(requestBody)
                                  })
                                  
                                  if (!response.ok) {
                                    const errorData = await response.json().catch(() => ({}))
                                    throw new Error(errorData.detail || 'Erro na busca')
                                  }
                                  
                                  const data = await response.json()
                                  
                                  if (data.candidates && data.candidates.length > 0) {
                                    const mappedCandidates = data.candidates.map((c: any) => ({
                                      id: c.id || `similar-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                                      candidateId: c.id?.substring(0, 8).toUpperCase() || 'SIM',
                                      name: c.name || 'Nome não disponível',
                                      email: c.email || '',
                                      phone: c.phone || '',
                                      current_title: c.headline || c.current_title || '',
                                      current_company: c.current_company || '',
                                      location: c.location || '',
                                      linkedin_url: c.linkedin_url,
                                      avatar_url: c.avatar_url || c.picture_url,
                                      avatar: c.avatar_url,
                                      technical_skills: c.skills || [],
                                      skills: c.skills || [],
                                      seniority_level: c.seniority_level,
                                      years_of_experience: c.years_experience || c.total_experience_years,
                                      experience: c.years_experience || c.total_experience_years || 0,
                                      score: c.match_score ? Math.round(c.match_score * 25) : 75,
                                      source: c.source || 'pearch',
                                      has_email: c.has_email ?? true,
                                      has_phone: c.has_phone ?? true,
                                      is_opentowork: c.is_opentowork,
                                      is_decision_maker: c.is_decision_maker,
                                      is_top_universities: c.is_top_universities,
                                      is_startup: c.is_startup || c.company_info?.is_startup,
                                      expertise: c.expertise,
                                      outreach_message: c.outreach_message,
                                      experiences: c.experiences || [],
                                      workHistory: (c.experiences || []).map((exp: any) => ({
                                        company: exp.company_info?.name || exp.company || '',
                                        title: exp.company_roles?.[0]?.title || exp.title || '',
                                        startDate: exp.company_roles?.[0]?.start_date || exp.start_date || '',
                                        endDate: exp.company_roles?.[0]?.end_date || exp.end_date || '',
                                        duration: exp.duration || '',
                                        location: exp.company_info?.location || exp.location || '',
                                        description: exp.company_roles?.[0]?.description || exp.description || ''
                                      })),
                                      education: (c.education || []).map((edu: any) => ({
                                        school: edu.school || '',
                                        degree: edu.degree || '',
                                        field_of_study: edu.field_of_study || '',
                                        fieldOfStudy: edu.field_of_study || '',
                                        startDate: edu.start_date || '',
                                        endDate: edu.end_date || ''
                                      }))
                                    }))
                                    
                                    const localCandidates = mappedCandidates.filter((c: any) => c.source === 'local')
                                    const globalCandidates = mappedCandidates.filter((c: any) => c.source === 'pearch')
                                    
                                    // Respeitar searchSource selecionado pelo usuário
                                    const shouldAutoShowGlobal = searchSource === 'global' || searchSource === 'hybrid'
                                    const candidatesForTable = shouldAutoShowGlobal ? mappedCandidates : localCandidates
                                    
                                    setCandidates(candidatesForTable)
                                    setHasSearchResults(true)
                                    setSearchResultsCount(data.total_count || mappedCandidates.length)
                                    setLocalResultsCount(data.local_count || localCandidates.length)
                                    setPearchResultsCount(data.pearch_count || globalCandidates.length)
                                    setShowSearchResults(true)
                                    setDisplayedResultsCount(10)
                                    
                                    setSearchResults(prev => ({
                                      local: localCandidates,
                                      global: globalCandidates,
                                      localCount: data.local_count || localCandidates.length,
                                      globalCount: data.pearch_count || globalCandidates.length,
                                      query: data.query_generated || 'Similar Search',
                                      isLoading: false,
                                      showGlobalResults: shouldAutoShowGlobal,
                                      globalDismissed: prev.globalDismissed
                                    }))
                                    
                                    const refProfileInfo = data.reference_profile 
                                      ? `\n\n**Perfil de referência:** ${data.reference_profile.name || data.reference_profile.linkedin_url || 'ID: ' + data.reference_profile.id}`
                                      : ''
                                    
                                    const localCount = data.local_count || localCandidates.length
                                    const liaMessage: ChatMessage = {
                                      id: `lia-similar-result-${Date.now()}`,
                                      type: 'lia',
                                      content: `**Busca de perfis similares concluída!**${refProfileInfo}\n\nQuery gerada: "${data.query_generated}"\n\nEncontrei **${localCount} candidato${localCount > 1 ? 's' : ''} similar${localCount > 1 ? 'es' : ''}** na sua base local.`,
                                      timestamp: new Date(),
                                      searchResults: {
                                        localCount: localCount,
                                        globalCount: 0,
                                        query: data.query_generated || ''
                                      }
                                    }
                                    setChatMessages(prev => [...prev, liaMessage])
                                  } else {
                                    const liaMessage: ChatMessage = {
                                      id: `lia-similar-noresult-${Date.now()}`,
                                      type: 'lia',
                                      content: `Não encontrei candidatos similares ao perfil informado.\n\nVerifique se o link do LinkedIn está correto ou tente com outro perfil de referência.`,
                                      timestamp: new Date()
                                    }
                                    setChatMessages(prev => [...prev, liaMessage])
                                  }
                                } catch (error: any) {
                                  console.error('Erro na busca similar:', error)
                                  const liaMessage: ChatMessage = {
                                    id: `lia-similar-error-${Date.now()}`,
                                    type: 'lia',
                                    content: `Erro ao buscar candidatos similares: ${error.message || 'Por favor, tente novamente.'}`,
                                    timestamp: new Date()
                                  }
                                  setChatMessages(prev => [...prev, liaMessage])
                                } finally {
                                  setIsSearchingSimilar(false)
                                }
                              }
                            }}
                            disabled={!similarProfileUrl.trim() || isSearchingSimilar}
                          >
                            {isSearchingSimilar ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Buscando...
                              </>
                            ) : (
                              <>
                                <Users className="w-4 h-4 mr-2" />
                                Encontrar Similares
                              </>
                            )}
                          </Button>
                        </div>
                      )}

                      {/* ABA 5: BOOLEAN */}
                      {activeSearchTab === 'boolean' && (
                        <div className="space-y-4">
                          <p className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                            Use operadores booleanos para buscas avançadas
                          </p>
                          
                          <div className="flex flex-wrap gap-1 mb-2">
                            {['AND', 'OR', 'NOT', '"..."', '(...)'].map((op) => (
                              <button
                                key={op}
                                onClick={() => setBooleanSearchValue(prev => prev + ' ' + op)}
                                className="px-2 py-1 text-xs rounded-full bg-gray-100 hover:bg-gray-200 text-gray-800 font-mono transition-colors"
                              >
                                {op}
                              </button>
                            ))}
                          </div>
                          
                          <textarea
                            value={booleanSearchValue}
                            onChange={(e) => setBooleanSearchValue(e.target.value)}
                            placeholder='Ex: ("Node.js" OR "Python") AND "sênior" NOT "júnior"'
                            className="w-full h-32 p-3 text-xs rounded-md border focus:outline-none transition-all resize-none bg-white dark:bg-gray-800 text-gray-950 dark:text-gray-50 font-mono border border-gray-100" style={{ fontFamily: 'monospace' }}
                          />
                          
                          <div className="p-3 rounded-md" style={{ backgroundColor: 'rgba(96, 190, 209, 0.06)' }}>
                            <div className="flex items-start gap-2">
                              <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700" />
                              <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                <strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições.
                              </p>
                            </div>
                          </div>

                          <Button
                            className="w-full h-11 !text-sm font-semibold bg-wedo-cyan-dark text-white font-open-sans"
                            onClick={() => {
                              if (booleanSearchValue.trim()) {
                                console.log('Buscar boolean:', booleanSearchValue)
                              }
                            }}
                            disabled={!booleanSearchValue.trim()}
                          >
                            <Code className="w-4 h-4 mr-2" />
                            Buscar com Boolean
                          </Button>
                        </div>
                      )}

                      {/* ABA 6: FILTROS - Padronizado com Modal */}
                      {activeSearchTab === 'filtros' && (
                        <div className="space-y-4">
                          {/* Dica contextual */}
                          <div className="p-3 rounded-md" style={{ backgroundColor: 'rgba(96, 190, 209, 0.06)' }}>
                            <div className="flex items-start gap-2">
                              <Lightbulb className="w-4 h-4 mt-0.5 flex-shrink-0 text-gray-700" />
                              <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                <strong>Dica:</strong> Use os filtros avançados para refinar sua busca por localização, experiência, skills, idiomas e muito mais.
                              </p>
                            </div>
                          </div>

                          {/* Resumo dos filtros ativos */}
                          {Object.values(activeSearchFilters).some(category => 
                            Object.values(category as Record<string, any>).some(v => v === true || (typeof v === 'string' && v.length > 0))
                          ) && (
                            <div className="p-3 rounded-md border" style={{ backgroundColor: 'rgba(16, 185, 129, 0.05)', borderColor: 'rgba(16, 185, 129, 0.3)' }}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <Check className="w-4 h-4 text-emerald-500" />
                                  <span className="text-xs font-medium text-emerald-700" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                    Filtros ativos
                                  </span>
                                </div>
                                <button
                                  onClick={() => setActiveSearchFilters({
                                    ppiOptions: {},
                                    general: {},
                                    locations: {},
                                    job: {},
                                    company: {},
                                    skills: {},
                                    education: {},
                                    languages: {}
                                  })}
                                  className="text-xs text-gray-800 hover:text-red-500 transition-colors"
                                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                                >
                                  Limpar todos
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Botão para abrir painel lateral de filtros da tabela */}
                          <Button
                            className="w-full h-12 !text-sm font-semibold"
                            style={{
                              backgroundColor: showTableFiltersPanel ? 'var(--gray-800)' : 'var(--gray-600)',
                              color: 'var(--gray-50)',
                              fontFamily: 'Open Sans, sans-serif'
                            }}
                            onClick={() => setShowTableFiltersPanel(!showTableFiltersPanel)}
                          >
                            <Filter className="w-4 h-4 mr-2" />
                            {showTableFiltersPanel ? 'Fechar Filtros' : 'Abrir Filtros Avançados'}
                          </Button>

                          {/* Info sobre filtros laterais */}
                          {!showTableFiltersPanel && (
                            <p className="text-xs text-gray-800 text-center mt-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              Os filtros aparecerão ao lado da tabela de candidatos
                            </p>
                          )}
                        </div>
                      )}

                    </div>
                  </Card>

                  {/* Resize Handle - Sempre visível */}
                  <div
                    className={`absolute -right-1.5 top-1/2 -translate-y-1/2 w-3 cursor-ew-resize hover:scale-125 transition-all z-10 flex items-center justify-center ${isLiaSuperChat ? 'h-full' : 'h-12'}`}
                    title="Arraste para ajustar a largura"
                    onMouseDown={(e) => {
                      e.preventDefault()
                      setIsResizingLIA(true)
                      const startX = e.clientX
                      const startWidth = isLiaSuperChat ? superChatWidth : liaWidth

                      const handleMouseMove = (e: MouseEvent) => {
                        const deltaX = e.clientX - startX
                        if (isLiaSuperChat) {
                          // Em modo superchat, permite largura maior (até 80% da tela)
                          const maxWidth = Math.floor(window.innerWidth * 0.8)
                          const newWidth = Math.max(500, Math.min(maxWidth, startWidth + deltaX))
                          setSuperChatWidth(newWidth)
                        } else {
                          const newWidth = Math.max(400, Math.min(800, startWidth + deltaX))
                          setLiaWidth(newWidth)
                        }
                      }

                      const handleMouseUp = () => {
                        setIsResizingLIA(false)
                        document.removeEventListener('mousemove', handleMouseMove)
                        document.removeEventListener('mouseup', handleMouseUp)
                      }

                      document.addEventListener('mousemove', handleMouseMove)
                      document.addEventListener('mouseup', handleMouseUp)
                    }}
                  >
 <div className={`w-1 rounded-full transition-colors ${isLiaSuperChat ? 'h-24 bg-gray-900' : 'h-8 dark:bg-gray-600 hover:dark:hover:bg-gray-800'}`} />
                  </div>
                </div>
              )}

              {/* Filtros da Tabela de Resultados - Coluna inline entre LIA e tabela */}
              {/* SEPARADO dos filtros de busca (activeSearchFilters) - usa tableFilters para filtrar resultados localmente */}
              {showTableFiltersPanel && (
                <CandidatesFilterPanel
                  tableFilters={tableFilters}
                  setTableFilters={setTableFilters}
                  searchSortBy={searchSortBy}
                  onSortChange={setSearchSortBy}
                  newSoftSkillFilter={newSoftSkillFilter}
                  setNewSoftSkillFilter={setNewSoftSkillFilter}
                  newCertificationFilter={newCertificationFilter}
                  setNewCertificationFilter={setNewCertificationFilter}
                  activeFiltersCount={getActiveTableFiltersCount()}
                  onToggleFilter={toggleTableFilter}
                  onClearAll={clearAllTableFilters}
                  onClose={() => setShowTableFiltersPanel(false)}
                />
              )}


              {/* Main Content Area - Candidatos Table with Superchat collapse support */}
              <div className={`bg-white dark:bg-gray-800 rounded-md transition-all duration-300 ${
                isLiaSuperChat 
                  ? 'w-14 flex-shrink-0' 
                  : 'flex-1 min-w-0 h-full'
              }`}>
                {isLiaSuperChat ? (
                  /* Versão Contraída - Apenas ícone para expandir */
                  <div className="h-full flex flex-col items-center py-4 gap-3">
                    {/* Botão para expandir tabela */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsLiaSuperChat(false)}
                      className="h-10 w-10 p-0 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
                      title="Expandir tabela de candidatos"
                    >
                      <ChevronRight className="w-5 h-5 text-gray-800 dark:text-gray-400" />
                    </Button>
                    
                    {/* Ícone da tabela */}
                    <div className="flex flex-col items-center gap-2 text-gray-800">
                      <Users className="w-5 h-5" />
                      <span className="text-xs font-medium" style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}>
                        Candidatos ({sortedCandidates.length})
                      </span>
                    </div>
                    
                    {/* Indicador de candidatos selecionados */}
                    {selectedCandidatesForBatch.size > 0 && (
                      <Badge className="bg-gray-900 dark:bg-gray-50 text-white text-xs px-1.5 py-0.5">
                        {selectedCandidatesForBatch.size}
                      </Badge>
                    )}
                  </div>
                ) : (
                  /* Versão Expandida - Tabela completa */
                  <div className="h-full flex flex-col overflow-hidden">
                {/* Table Container - Scrollável */}
                <div 
                  ref={tableContainerRef}
                  className="flex-1 relative overflow-auto"
                >
                  {/* Loading Overlay */}
                  {isLoading && (
                    <div className="flex items-center justify-center h-full absolute inset-0 z-20 bg-white dark:bg-gray-900">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
                        <p className="text-gray-800 text-sm">Carregando candidatos...</p>
                      </div>
                    </div>
                  )}

                  {/* Unified Candidate Table */}
                  {!isLoading && sortedCandidates.length > 0 && (
                    <UnifiedCandidateTable
                      candidates={visibleCandidates as any}
                      columns={visibleTableColumns.map((col) => ({
                        id: col.id,
                        label: col.label,
                        visible: col.visible,
                        sortable: true,
                        width: columnWidths[col.id] || 120,
                        minWidth: 80,
                        align: col.id === 'name' ? 'left' as const : 'center' as const,
                        order: col.order,
                        isGlobalSearch: col.isGlobalSearch
                      }))}
                      selectedIds={selectedCandidatesForBatch}
                      pinnedIds={pinnedCandidates}
                      favoriteIds={favorites}
                      sortConfig={sortBy ? { field: sortBy, direction: sortOrder } : undefined}
                      isLoading={false}
                      emptyMessage="Nenhum candidato encontrado"
                      showCheckboxes={true}
                      showPagination={false}
                      enableColumnResize={true}
                      enableColumnReorder={true}
                      onColumnResize={(columnId, newWidth) => {
                        setColumnWidths(prev => ({
                          ...prev,
                          [columnId]: newWidth
                        }))
                      }}
                      onColumnReorder={(reorderedColumns) => {
                        setTableColumns(prev => prev.map(col => {
                          const reordered = reorderedColumns.find(r => r.id === col.id)
                          return reordered ? { ...col, order: reordered.order } : col
                        }))
                      }}
                      onCandidateClick={(candidate) => handleCandidateClick(candidate as any)}
                      onSelectionChange={(ids) => setSelectedCandidatesForBatch(ids)}
                      onSortChange={(config) => {
                        setSortBy(config.field)
                        setSortOrder(config.direction)
                      }}
                      onTogglePin={(candidateId) => handleTogglePin(candidateId)}
                      onToggleFavorite={(candidateId) => handleToggleFavorite(candidateId)}
                      renderCustomCell={(candidate, columnId) => renderCellValue(candidate as any, columnId)}
                    />
                  )}
                  {/* Paginação (como Gestão de Vagas) - oculta quando usando Load More em resultados de busca */}
                  {!isLoading && !showSearchResults && getPaginatedCandidates().totalPages > 1 && (
                    <div className="bg-white dark:bg-gray-900 rounded-md p-3 mt-2">
                      <div className="flex items-center justify-between">
                        <div className="text-sm text-gray-800 dark:text-gray-400">
                          Mostrando {((currentPage - 1) * itemsPerPage) + 1} - {Math.min(currentPage * itemsPerPage, getPaginatedCandidates().total)} de {getPaginatedCandidates().total} candidatos
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(1)}
                            disabled={currentPage === 1}
                            className="h-8"
                          >
                            Primeira
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                            disabled={currentPage === 1}
                            className="h-8"
                          >
                            Anterior
                          </Button>

                          {/* Page numbers */}
                          <div className="flex items-center gap-1">
                            {Array.from({ length: getPaginatedCandidates().totalPages }, (_, i) => i + 1)
                              .filter(page => {
                                return page === 1 ||
                                       page === getPaginatedCandidates().totalPages ||
                                       (page >= currentPage - 1 && page <= currentPage + 1)
                              })
                              .map((page, index, array) => (
                                <React.Fragment key={page}>
                                  {index > 0 && page - array[index - 1] > 1 && (
                                    <span className="px-2 text-gray-800">...</span>
                                  )}
                                  <Button
                                    variant={currentPage === page ? 'default' : 'outline'}
                                    size="sm"
                                    onClick={() => setCurrentPage(page)}
                                    className="h-8 w-8 p-0"
                                  >
                                    {page}
                                  </Button>
                                </React.Fragment>
                              ))
                            }
                          </div>

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(prev => Math.min(getPaginatedCandidates().totalPages, prev + 1))}
                            disabled={currentPage === getPaginatedCandidates().totalPages}
                            className="h-8"
                          >
                            Próxima
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setCurrentPage(getPaginatedCandidates().totalPages)}
                            disabled={currentPage === getPaginatedCandidates().totalPages}
                            className="h-8"
                          >
                            Última
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Empty State */}
                  {!isLoading && sortedCandidates.length === 0 && (
                    <div className="bg-white dark:bg-gray-900 rounded-md p-8 text-center">
                      <Users className="w-12 h-12 text-gray-800 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-950 dark:text-gray-50 mb-2">
                        Nenhum candidato encontrado
                      </h3>
                      <p className="text-gray-800 dark:text-gray-400 mb-4">
                        Tente ajustar os filtros ou termos de busca
                      </p>
                      <Button
                        variant="outline"
                        onClick={clearAllFilters}
                      >
                        Limpar filtros
                      </Button>
                    </div>
                  )}
                </div>
                {/* Load More - Fase 1 Funil de Talentos (FORA do scroll container, sempre visível) */}
                {showSearchResults && displayedResultsCount < sortedCandidates.length && (
                  <div className="flex-shrink-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 py-3 px-4">
                    <div className="flex flex-col items-center gap-1.5">
                      <Button
                        variant="outline"
                        className="w-full max-w-md h-10 gap-2 text-sm font-medium"
                        onClick={handleLoadMore}
                        disabled={isLoadingMore}
                      >
                        {isLoadingMore ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                        {isLoadingMore ? 'Carregando...' : 'Carregar mais 10 candidatos'}
                      </Button>
                      <span className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                        {Math.min(displayedResultsCount, sortedCandidates.length)} de {sortedCandidates.length} candidatos
                      </span>
                    </div>
                  </div>
                )}
                {showSearchResults && displayedResultsCount >= sortedCandidates.length && sortedCandidates.length > 10 && (
                  <p className="flex-shrink-0 text-center text-sm text-gray-500 py-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    Todos os {sortedCandidates.length} candidatos carregados
                  </p>
                )}
              </div>
              )}
            </div>

              {/* Column Configuration Sidebar - Right - WeDOTalent Light Design */}
              {showColumnConfig && (
                <div className="flex-shrink-0 w-80 transition-all duration-300">
                  <div className="bg-white rounded-md h-[calc(100vh-6rem)] overflow-hidden">
                    {/* Header */}
                    <div className="p-4 flex items-center justify-between border-b border-gray-100">
                      <div>
                        <h3 
                          className="text-sm font-semibold text-gray-950 dark:text-gray-50"
                         
                        >
                          Configurar Colunas
                        </h3>
                        <p 
                          className="text-xs mt-0.5 text-gray-800"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          {tableColumns.filter(c => c.visible && c.id !== 'acoes').length} de {tableColumns.filter(c => c.id !== 'acoes').length} colunas ativas
                        </p>
                      </div>
                      <button
                        onClick={() => setShowColumnConfig(false)}
                        className="h-8 w-8 rounded-md flex items-center justify-center transition-all text-gray-800 hover:text-gray-950 hover:bg-gray-100"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    
                    {/* Search and Actions */}
                    <div className="p-3 space-y-3 border-b border-gray-100">
                      <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-800" />
                        <input
                          type="text"
                          placeholder="Buscar coluna..."
                          value={columnSearchTerm}
                          onChange={(e) => setColumnSearchTerm(e.target.value)}
                          className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-gray-50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 text-gray-950 dark:text-gray-50"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        />
                      </div>
                      <div className="flex gap-2">
                        <button
                          className="flex-1 text-xs h-8 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}
                          onClick={() => {
                            setTableColumns(prev => prev.map((col, idx) => ({
                              ...col,
                              visible: col.id === 'acoes' || idx < 7,
                              order: col.id === 'acoes' ? 0.5 : idx
                            })))
                          }}
                        >
                          Restaurar Padrão
                        </button>
                        <button
                          className="text-xs h-8 px-4 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}
                          onClick={() => {
                            setTableColumns(prev => prev.map(col => ({ ...col, visible: true })))
                          }}
                        >
                          Todas
                        </button>
                      </div>
                    </div>

                    {/* Column List */}
                    <div className="overflow-y-auto h-[calc(100%-160px)] p-3">
                      {(() => {
                        const categoryLabels: Record<string, string> = {
                          basico: 'Identificação Básica',
                          contato: 'Contato',
                          pessoal: 'Informações Pessoais',
                          profissional: 'Perfil Profissional',
                          competencias: 'Competências',
                          localizacao: 'Localização',
                          endereco: 'Endereço Completo',
                          preferencias: 'Preferências de Trabalho',
                          salario: 'Salário e Expectativas',
                          documentos: 'Currículo e Documentos',
                          origem: 'Origem e Integração',
                          busca_global: 'Busca Global',
                          ia: 'Insights LIA / IA',
                          status: 'Status e Workflow',
                          comunicacao: 'Comunicação',
                          cadastro: 'Status de Cadastro',
                          adicional: 'Informações Adicionais',
                          datas: 'Datas e Timestamps'
                        }
                        
                        const filteredColumns = tableColumns.filter(col => 
                          col.id !== 'acoes' && col.id !== 'feedback' && (
                          col.label.toLowerCase().includes(columnSearchTerm.toLowerCase()) ||
                          col.id.toLowerCase().includes(columnSearchTerm.toLowerCase()))
                        )
                        
                        const groupedColumns = filteredColumns.reduce((acc, col) => {
                          const category = col.category || 'adicional'
                          if (!acc[category]) acc[category] = []
                          acc[category].push(col)
                          return acc
                        }, {} as Record<string, typeof tableColumns>)
                        
                        const categoryOrder = ['basico', 'contato', 'pessoal', 'profissional', 'competencias', 'localizacao', 'endereco', 'preferencias', 'salario', 'documentos', 'origem', 'busca_global', 'ia', 'status', 'comunicacao', 'cadastro', 'adicional', 'datas']
                        
                        return categoryOrder.map(category => {
                          const columns = groupedColumns[category]
                          if (!columns || columns.length === 0) return null
                          
                          const visibleCount = columns.filter(c => c.visible).length
                          
                          return (
                            <div key={category} className="mb-5">
                              <div className="flex items-center justify-between mb-2 px-1">
                                <h4 
                                  className="text-xs font-semibold uppercase tracking-wider text-gray-800"
                                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                                >
                                  {categoryLabels[category] || category}
                                </h4>
                                <span 
                                  className="text-xs px-2 py-0.5 rounded-full"
                                  style={{ 
                                    backgroundColor: visibleCount > 0 ? '#f3f4f6' : '#f3f4f6',
                                    color: visibleCount > 0 ? 'var(--gray-600)' : 'var(--gray-400)',
                                    fontFamily: 'Open Sans, sans-serif'
                                  }}
                                >
                                  {visibleCount}/{columns.length}
                                </span>
                              </div>
                              <div className="space-y-1">
                                {columns.map((col) => (
                                  <div
                                    key={col.id}
                                    onClick={() => {
                                      setTableColumns(prev => prev.map(c => 
                                        c.id === col.id ? { ...c, visible: !c.visible } : c
                                      ))
                                    }}
                                    className="flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-all hover:bg-gray-100"
                                    style={{ 
                                      backgroundColor: col.visible ? '#f9fafb' : '#fafafa',
                                      border: col.visible ? '1px solid #d1d5db' : '1px solid #e5e7eb'
                                    }}
                                  >
                                    {/* Custom Checkbox - Monocromático */}
                                    <div 
                                      className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all"
                                      style={{ 
                                        backgroundColor: col.visible ? 'var(--gray-600)' : 'transparent',
                                        border: col.visible ? 'none' : '2px solid #d1d5db'
                                      }}
                                    >
                                      {col.visible && (
                                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                      )}
                                    </div>
                                    <span 
                                      className="text-xs flex-1 flex items-center gap-1.5"
                                      style={{ 
                                        color: col.visible ? 'var(--gray-800)' : '#6b7280',
                                        fontFamily: 'Open Sans, sans-serif',
                                        fontWeight: col.visible ? 500 : 400
                                      }}
                                    >
                                      {col.isGlobalSearch && (
                                        <Globe className="w-3 h-3 text-gray-600 dark:text-gray-400" />
                                      )}
                                      {col.label}
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )
                        })
                      })()}
                    </div>
                  </div>
                </div>
              )}

              {/* Candidate Preview - Painel lateral direito */}
              {showCandidatePreview && previewCandidate && (
                <div className="flex-shrink-0 relative" style={{ width: `${previewWidth}px` }}>
                  {/* Resize Handle */}
                  <div
                    className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors z-10 group"
                    onMouseDown={handlePreviewResize}
                    title="Arraste para redimensionar"
                  >
                    <div className="absolute inset-0 -left-1 -right-1"></div>
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-gray-600 group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors"></div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 h-[calc(100vh-6rem)] overflow-hidden">
                    <CandidatePreview
                      candidate={previewCandidate}
                      isOpen={showCandidatePreview}
                      onClose={handleCloseCandidatePreview}
                      isMaximized={isPreviewMaximized}
                      onToggleMaximize={handleTogglePreviewMaximize}
                      candidates={sortedCandidates}
                      currentIndex={sortedCandidates.findIndex(c => c.id === previewCandidate.id)}
                      onNavigateCandidate={(index) => {
                        if (sortedCandidates[index]) {
                          setPreviewCandidate(sortedCandidates[index])
                        }
                      }}
                      onOpenFullPage={handleCandidatePageOpen}
                      onScheduleInterview={(candidate) => {
                        setSelectedCandidateForAction(candidate)
                        setShowScheduleModal(true)
                      }}
                      onAddToVacancy={(candidate) => {
                        setSelectedCandidatesForBatch(new Set([candidate.id]))
                        setShowAddToVacancyModal(true)
                      }}
                      onToggleFavorite={(candidateId) => handleToggleFavorite(candidateId)}
                      onWSIScreening={(candidate) => handleStartWSITextScreening(candidate)}
                      isFavorite={favorites.has(previewCandidate.id)}
                      onSendEmail={(candidate) => handleSendEmail(candidate)}
                      onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
                      onSendTriagem={(candidate) => handleSendTriagem(candidate)}
                      onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
                      onSendFeedback={(candidate) => handleSendFeedback(candidate)}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Aba Favoritos */}
        {activeTab === 'favorites' && (
          <div className="flex gap-6">
            <div className={`${showCandidatePreview && previewCandidate ? 'flex-1' : 'w-full'} transition-all duration-300`}>
              <FavoritesTab
                candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))}
                pinnedCandidates={pinnedCandidates}
                favoriteCandidates={favorites}
                favoriteNotes={favoriteNotes}
                onTogglePin={handleTogglePin}
                onToggleFavorite={handleToggleFavorite}
                onCandidateClick={handleCandidateClick}
                onLIAClick={handleLIAClick}
                onUpdateFavoriteNote={handleUpdateFavoriteNote}
              />
            </div>
            
            {/* Candidate Preview - Painel lateral direito */}
            {showCandidatePreview && previewCandidate && (
              <div className="flex-shrink-0 relative" style={{ width: `${previewWidth}px` }}>
                <div
                  className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors z-10 group"
                  onMouseDown={handlePreviewResize}
                  title="Arraste para redimensionar"
                >
                  <div className="absolute inset-0 -left-1 -right-1"></div>
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-gray-600 group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors"></div>
                </div>
                <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 h-[calc(100vh-6rem)] overflow-hidden">
                  <CandidatePreview
                    candidate={previewCandidate}
                    isOpen={showCandidatePreview}
                    onClose={handleCloseCandidatePreview}
                    isMaximized={isPreviewMaximized}
                    onToggleMaximize={handleTogglePreviewMaximize}
                    candidates={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))}
                    currentIndex={candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id)).findIndex(c => c.id === previewCandidate.id)}
                    onNavigateCandidate={(index) => {
                      const favoriteCandidates = candidates.filter(c => pinnedCandidates.has(c.id) || favorites.has(c.id))
                      if (favoriteCandidates[index]) {
                        setPreviewCandidate(favoriteCandidates[index])
                      }
                    }}
                    onOpenFullPage={handleCandidatePageOpen}
                    onScheduleInterview={(candidate) => {
                      setSelectedCandidateForAction(candidate)
                      setShowScheduleModal(true)
                    }}
                    onAddToVacancy={(candidate) => {
                      setSelectedCandidatesForBatch(new Set([candidate.id]))
                      setShowAddToVacancyModal(true)
                    }}
                    onToggleFavorite={(candidateId) => handleToggleFavorite(candidateId)}
                    onWSIScreening={(candidate) => handleStartWSITextScreening(candidate)}
                    isFavorite={favorites.has(previewCandidate.id)}
                    onSendEmail={(candidate) => handleSendEmail(candidate)}
                    onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
                    onSendTriagem={(candidate) => handleSendTriagem(candidate)}
                    onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
                    onSendFeedback={(candidate) => handleSendFeedback(candidate)}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Aba Listas */}
        {activeTab === 'lists' && (
          <ListsTab
            onListSelect={async (listId) => {
              try {
                setIsLoading(true)
                const listDetails = await liaApi.getCandidateList(listId, { limit: 100 })
                
                const mappedCandidates: Candidate[] = listDetails.candidates.items.map((member) => {
                  const c = member.candidate
                  const location = [c.location_city, c.location_state, c.location_country].filter(Boolean).join(', ') || 'Não informado'
                  const workModel = c.work_model_preference === 'remote' ? 'remoto' : 
                                   c.work_model_preference === 'hybrid' ? 'híbrido' : 'presencial'
                  
                  return {
                    id: c.id,
                    candidateId: c.id,
                    name: c.name || 'Sem nome',
                    email: c.email || '',
                    phone: c.phone || c.mobile_phone || '',
                    linkedin_url: c.linkedin_url,
                    github_url: c.github_url,
                    portfolio_url: c.portfolio_url,
                    avatar_url: c.avatar_url,
                    current_title: c.current_title,
                    current_company: c.current_company,
                    seniority_level: c.seniority_level,
                    years_of_experience: c.years_of_experience,
                    technical_skills: c.technical_skills || [],
                    soft_skills: c.soft_skills || [],
                    languages: c.languages || {},
                    certifications: c.certifications || [],
                    location_city: c.location_city,
                    location_state: c.location_state,
                    location_country: c.location_country,
                    is_remote: c.is_remote,
                    willing_to_relocate: c.willing_to_relocate,
                    work_model_preference: c.work_model_preference,
                    contract_type_preference: c.contract_type_preference,
                    current_salary: c.current_salary,
                    desired_salary_min: c.desired_salary_min,
                    desired_salary_max: c.desired_salary_max,
                    resume_url: c.resume_url,
                    source: c.source || 'local',
                    lia_score: c.lia_score,
                    lia_insights: c.lia_insights,
                    status: c.status,
                    tags: c.tags || [],
                    created_at: c.created_at,
                    updated_at: c.updated_at,
                    position: c.current_title || 'Profissional',
                    monthlySalary: c.current_salary || 0,
                    location: location,
                    workModel: workModel as 'remoto' | 'híbrido' | 'presencial',
                    score: c.lia_score || 0,
                    contractType: (c.contract_type_preference === 'PJ' ? 'PJ' : 
                                   c.contract_type_preference === 'Freelancer' ? 'Freelancer' : 'CLT') as 'CLT' | 'PJ' | 'Freelancer',
                    linkedin: c.linkedin_url || '',
                    skills: c.technical_skills || [],
                    experience: c.years_of_experience || 0,
                    education: '',
                    workHistory: [],
                  }
                })
                
                setCandidates(mappedCandidates)
                setViewingList({ 
                  id: listDetails.id, 
                  name: listDetails.name, 
                  color: listDetails.color 
                })
                setActiveTab('search')
                setShowSearchResults(true)
                setDisplayedResultsCount(10)
                setLastSearchQuery(`Lista: ${listDetails.name}`)
                
                toast({
                  title: "Lista carregada",
                  description: `Exibindo ${mappedCandidates.length} candidatos da lista "${listDetails.name}"`,
                })
              } catch (error) {
                console.error('Failed to load list:', error)
                toast({
                  title: "Erro ao carregar lista",
                  description: error instanceof Error ? error.message : "Não foi possível carregar os candidatos da lista.",
                  variant: "destructive"
                })
              } finally {
                setIsLoading(false)
              }
            }}
            onAddToJobs={(listId) => {
              liaApi.getCandidateList(listId).then(list => {
                setSelectedListForVacancies({
                  id: listId,
                  name: list.name,
                  candidateCount: list.candidate_count
                })
                setShowAddListToVacanciesModal(true)
              }).catch(err => {
                toast({
                  title: "Erro ao carregar lista",
                  description: err.message,
                  variant: "destructive"
                })
              })
            }}
            onAddCandidateToList={(listId, listName) => {
              setPreSelectedListForModal({ id: listId, name: listName })
              setShowAddCandidateModal(true)
            }}
          />
        )}

        {/* Aba Histórico */}
        {activeTab === 'history' && (
          <HistoryTab
            history={talentFunnel.history}
            onReExecuteSearch={(historyItem) => {
              // Re-executar a busca do histórico
              setSearchTerm(historyItem.query)
              setLastSearchQuery(historyItem.query)
              setLastSearchMode(historyItem.mode || 'natural')
              if (historyItem.source) {
                setSearchSource(historyItem.source)
              }
              setActiveTab('search')
              // Trigger busca automática após um pequeno delay
              setTimeout(() => {
                setShowSearchResults(false) // Reset para mostrar a tela de busca
              }, 100)
            }}
            onSaveAsSearch={(historyItem, name, description) => {
              // Salvar busca usando o hook centralizado
              talentFunnel.saveHistoryAsSearch(historyItem, name, description)
            }}
            onDeleteItem={(id) => {
              talentFunnel.removeFromHistory(id)
            }}
            onClearAll={() => {
              talentFunnel.clearHistory()
            }}
          />
        )}

        {/* Aba Buscas Salvas */}
        {activeTab === 'saved-searches' && (
          <SavedSearchesTab
            savedSearches={talentFunnel.savedSearches}
            onExecuteSearch={(search) => {
              // Executar busca salva
              setSearchTerm(search.query)
              setLastSearchQuery(search.query)
              setLastSearchMode(search.mode)
              setSearchSource(search.source)
              setActiveTab('search')
              talentFunnel.incrementSavedSearchUsage(search.id)
              setTimeout(() => {
                setShowSearchResults(false)
              }, 100)
            }}
            onAddSearch={(search) => {
              talentFunnel.addSavedSearch(search)
            }}
            onUpdateSearch={(id, updates) => {
              talentFunnel.updateSavedSearch(id, updates)
            }}
            onDeleteSearch={(id) => {
              talentFunnel.removeSavedSearch(id)
            }}
            onToggleFavorite={(id) => {
              talentFunnel.toggleSavedSearchFavorite(id)
            }}
            onNavigateToSearch={() => {
              setActiveTab('search')
              setShowSearchResults(false)
            }}
          />
        )}

      </div>

      {/* Modals */}
      
      {/* Contact Modal */}
      {(selectedCandidateForAction || contactModalCandidate) && (
        <ContactModal
          isOpen={showContactModal}
          onClose={() => {
            setShowContactModal(false)
            setSelectedCandidateForAction(null)
            setContactModalCandidate(null)
            setContactModalAction('general')
          }}
          candidate={(() => {
            const c = contactModalCandidate || selectedCandidateForAction
            if (!c) return null
            return {
              id: c.id,
              name: c.name,
              role: c.position || c.role,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score || 0,
              status: c.status || 'Novo',
              matchPercentage: c.liaAnalysis?.score || c.matchPercentage || c.score || 0,
              riskLevel: 'low',
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience || ''),
              seniority: c.seniority || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected?.toString() || '',
              preferredLocation: c.location,
              linkedin: c.linkedin,
              skills: c.skills || [],
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }
          })()}
          onSend={handleSendMessage}
          initialAction={contactModalAction}
        />
      )}

      {/* Schedule Modal */}
      {selectedCandidateForAction && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => {
            setShowScheduleModal(false)
            setSelectedCandidateForAction(null)
          }}
          candidate={{
            id: selectedCandidateForAction.id,
            name: selectedCandidateForAction.name,
            role: selectedCandidateForAction.position,
            email: selectedCandidateForAction.email,
            phone: selectedCandidateForAction.phone,
            location: selectedCandidateForAction.location,
            avatar: selectedCandidateForAction.avatar,
            score: selectedCandidateForAction.score,
            status: selectedCandidateForAction.status,
            matchPercentage: selectedCandidateForAction.liaAnalysis?.score || selectedCandidateForAction.score,
            riskLevel: 'low',
            culturalFit: 85,
            technicalMatch: 90,
            experience: String(selectedCandidateForAction.experience),
            seniority: selectedCandidateForAction.seniority || 'Pleno',
            availability: 'Imediata',
            expectedSalary: selectedCandidateForAction.salary?.expected?.toString() || '',
            preferredLocation: selectedCandidateForAction.location,
            linkedin: selectedCandidateForAction.linkedin,
            skills: selectedCandidateForAction.skills,
            lastActivity: new Date().toISOString(),
            source: 'internal'
          }}
          onSchedule={handleScheduleComplete}
        />
      )}

      {/* Unified Communication Modal - New standardized modal for all communication types */}
      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? {
          id: unifiedModalCandidate.id,
          name: unifiedModalCandidate.name,
          role: unifiedModalCandidate.position || unifiedModalCandidate.current_title || '',
          email: unifiedModalCandidate.email,
          phone: unifiedModalCandidate.phone,
          location: unifiedModalCandidate.location,
          avatar: unifiedModalCandidate.avatar,
          score: unifiedModalCandidate.score,
          matchPercentage: unifiedModalCandidate.liaAnalysis?.score || unifiedModalCandidate.score,
          skills: unifiedModalCandidate.skills
        } : null}
        type={unifiedModalType}
        jobTitle={lastSearchQuery || undefined}
        onSend={handleUnifiedModalSend}
        // TODO: Replace 'demo' with actual company_id from auth context when authentication is implemented.
        // This is required for proper multi-tenancy support.
        companyId="demo"
      />

      {/* Candidate Comparison Modal */}
      {showComparisonModal && selectedCandidatesForBatch.size >= 2 && (
        <CandidateComparison
          isOpen={showComparisonModal}
          onClose={() => setShowComparisonModal(false)}
          candidates={sortedCandidates
            .filter(c => selectedCandidatesForBatch.has(c.id))
            .map(c => ({
              id: c.id,
              name: c.name,
              role: c.position,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score,
              status: c.status,
              matchPercentage: c.liaAnalysis?.score || c.score,
              riskLevel: 'low',
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience),
              seniority: c.seniority || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected?.toString() || '',
              skills: c.skills,
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }))}
          onSelectCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleNavigateToFullProfile(candidate)
          }}
          onScheduleInterview={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleScheduleInterview(candidate)
          }}
          onContactCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleContactCandidate(candidate)
          }}
        />
      )}

      {/* Candidate Page Modal */}
      {showCandidatePage && selectedCandidate && (
        <CandidatePage
          candidate={selectedCandidate}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={() => {}}
        />
      )}

      {/* New Candidate Unified Modal - AI-first experience */}
      <NewCandidateUnifiedModal
        key={`modal-${preSelectedListForModal?.id || 'default'}`}
        isOpen={showAddCandidateModal}
        onClose={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onCandidateAdded={(candidate) => {
          handleAddCandidate(candidate)
          // Reload lists if a list was pre-selected
          if (preSelectedListForModal) {
            liaApi.getCandidateLists({ limit: 50 }).then(response => {
              if (response.items) {
                setCandidateListsForModal(response.items.map(list => ({
                  id: list.id,
                  name: list.name,
                  color: list.color
                })))
              }
            }).catch(() => {})
          }
        }}
        jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title, department: j.department, location: j.location }))}
        candidateLists={candidateListsForModal}
        preSelectedListId={preSelectedListForModal?.id}
        preSelectedListName={preSelectedListForModal?.name}
        onGoToSearch={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
          setActiveTab('search')
        }}
        onOpenFullProfile={(candidateId) => {
          const candidate = candidates.find(c => c.id === candidateId)
          if (candidate) {
            handleCandidatePageOpen(candidate)
          }
        }}
      />

      {/* Batch Approval Modal */}
      {showBatchApproval && (
        <BatchApprovalModal
          candidates={convertCandidatesForBatch(candidates.filter(c => selectedCandidatesForBatch.has(c.id)))}
          isOpen={showBatchApproval}
          onClose={() => setShowBatchApproval(false)}
          onApprovalComplete={handleBatchApprovalComplete}
        />
      )}

      {/* WSI Text Screening Modal */}
      {wsiCandidateForScreening && (
        <WSITextScreeningModal
          isOpen={showWSITextModal}
          onClose={() => {
            setShowWSITextModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            avatar: wsiCandidateForScreening.avatar,
            position: wsiCandidateForScreening.position
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
        />
      )}

      {/* WSI Voice Screening Modal */}
      {wsiCandidateForScreening && (
        <WSIVoiceScreeningStatus
          isOpen={showWSIVoiceModal}
          onClose={() => {
            setShowWSIVoiceModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            phone: wsiCandidateForScreening.phone
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
          autoStart={true}
        />
      )}

      {/* WSI Triagem Invite Modal */}
      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate ? {
          id: wsiInviteCandidate.id,
          name: wsiInviteCandidate.name,
          role: wsiInviteCandidate.position,
          email: wsiInviteCandidate.email,
          phone: wsiInviteCandidate.phone,
          location: wsiInviteCandidate.location,
          avatar: wsiInviteCandidate.avatar
        } : null}
        jobTitle={wsiInviteCandidate?.position || 'Vaga'}
        onSend={async (data) => {
          try {
            if (data.channel === 'email' && wsiInviteCandidate?.email) {
              await liaApi.sendEmail('wsi-triagem-invite', {
                recipient_email: wsiInviteCandidate.email,
                recipient_name: wsiInviteCandidate.name,
                candidate_id: wsiInviteCandidate.id,
                subject_override: data.subject || `Convite para Triagem - ${wsiInviteCandidate.position || 'Vaga'}`,
                body_override: data.message,
                variables: {
                  candidate_name: wsiInviteCandidate.name,
                  job_title: wsiInviteCandidate.position || 'Vaga'
                }
              })
            }
            
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          } catch (error) {
            console.error('Error sending WSI invite:', error)
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          }
        }}
      />

      {/* Rubric Evaluation Modal - Análise LIA */}
      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={() => {
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        evaluation={rubricEvaluationData}
        candidateId={rubricCandidate?.id || ''}
        candidateName={rubricCandidate?.name}
        jobId=""
        onApprove={async () => {
          toast({
            title: "Candidato aprovado",
            description: `${rubricCandidate?.name} foi aprovado com sucesso`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        onReject={async () => {
          toast({
            title: "Candidato reprovado",
            description: `${rubricCandidate?.name} foi reprovado`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
      />

      {/* Send Email Modal */}
      <SendEmailModal
        isOpen={showSendEmailModal}
        onClose={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
        candidate={emailCandidateSelected ? {
          id: emailCandidateSelected.id,
          name: emailCandidateSelected.name,
          email: emailCandidateSelected.email,
          phone: emailCandidateSelected.phone,
          current_title: emailCandidateSelected.position,
          technical_skills: emailCandidateSelected.skills,
          source: 'internal',
          is_active: true,
          is_remote: emailCandidateSelected.workModel === 'remoto',
          willing_to_relocate: false,
          tags: emailCandidateSelected.tags,
          status: emailCandidateSelected.status,
          lia_insights: {},
          soft_skills: [],
          languages: {},
          certifications: []
        } : null}
        onSuccess={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
      />

      {/* Reveal Contact Modal */}
      {revealCandidate && (
        <RevealCreditsModal
          isOpen={showRevealModal}
          onClose={() => {
            setShowRevealModal(false)
            setRevealCandidate(null)
          }}
          onConfirm={handleRevealContact}
          revealType={revealType}
          candidateName={revealCandidate.name}
          creditsRequired={revealType === 'email' ? 2 : 14}
        />
      )}

      {/* CV Preview Modal (legado - mantido para compatibilidade) */}
      {parsedCVData && (
        <CVPreview
          isOpen={showCVPreviewModal}
          onClose={() => {
            setShowCVPreviewModal(false)
            setParsedCVData(null)
          }}
          parsedData={parsedCVData}
          onConfirm={handleCVConfirmed}
          jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title }))}
        />
      )}

      {/* Bulk Actions Bar removido - ações agora aparecem no chat da LIA */}

      {/* Modal de Confirmação de Créditos Base Global */}
      <AlertDialog open={showCreditConfirmation} onOpenChange={setShowCreditConfirmation}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                <Zap className="w-4 h-4 text-gray-700" />
              </div>
              Confirmar Busca na Base Global
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-500">
                Esta busca utilizará créditos da sua conta.
              </p>
              
              {creditEstimate && (
                <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4 space-y-3">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-800">Tipo de busca:</span>
                    <span className="font-medium capitalize">{pearchSearchOptions.searchType}</span>
                  </div>
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-800">Limite de resultados:</span>
                    <span className="font-medium">{pearchSearchOptions.limit}</span>
                  </div>
                  
                  {/* Filtros de Otimização de Créditos */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-3 space-y-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Filtros de Contato</span>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        <span className="text-sm text-gray-800">Apenas com Email</span>
                        <span className="text-xs text-gray-500">(+1 cr)</span>
                      </div>
                      <Switch
                        checked={pearchSearchOptions.requireEmails}
                        onCheckedChange={(checked) => setPearchSearchOptions(prev => ({ ...prev, requireEmails: checked }))}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-gray-800">Apenas com Telefone</span>
                        <span className="text-xs text-gray-500">(+1 cr)</span>
                      </div>
                      <Switch
                        checked={pearchSearchOptions.requirePhoneNumbers}
                        onCheckedChange={(checked) => setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: checked }))}
                      />
                    </div>
                    {(pearchSearchOptions.requireEmails || pearchSearchOptions.requirePhoneNumbers) && (
                      <p className="text-xs text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-2 rounded">
                        Filtrando candidatos com contato disponível - você não gastará créditos com perfis sem dados de contato.
                      </p>
                    )}
                  </div>
                  
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-800">Custo base:</span>
                    <span className="font-medium">{creditEstimate.breakdown.base} créditos</span>
                  </div>
                  {creditEstimate.breakdown.emails > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-800">E-mails (+):</span>
                      <span className="font-medium">{creditEstimate.breakdown.emails} créditos</span>
                    </div>
                  )}
                  {creditEstimate.breakdown.phone_numbers > 0 && (
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-gray-800">Telefones (+):</span>
                      <span className="font-medium">{creditEstimate.breakdown.phone_numbers} créditos</span>
                    </div>
                  )}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">Total estimado:</span>
                      <span className="font-bold text-lg text-gray-700">
                        {creditEstimate.total_estimated} créditos
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-2 rounded-md">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>O custo final pode variar dependendo dos resultados encontrados.</span>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setShowCreditConfirmation(false)
              setPendingSearchRequest(null)
            }}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleConfirmPearchSearch}
              className="text-white bg-gray-900"
            >
              Confirmar Busca
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Expansão Global */}
      <AlertDialog open={showGlobalExpansionConfirm} onOpenChange={setShowGlobalExpansionConfirm}>
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)' }}>
                <Globe className="w-4 h-4 text-gray-700" />
              </div>
              Expandir para Busca Global
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p className="text-sm text-gray-800 dark:text-gray-500">
                A Busca Global encontra candidatos além da sua base local em um pool de mais de 800 milhões de perfis profissionais.
              </p>
              
              <div className="bg-gray-50 dark:bg-gray-800/50 rounded-md p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-800">Busca atual:</span>
                  <span className="font-medium text-xs max-w-[200px] truncate">{lastSuccessfulQuery || lastSearchQuery || 'N/A'}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-800">Resultados locais:</span>
                  <span className="font-medium">{localResultsCount} candidatos</span>
                </div>
                <div className="border-t border-gray-200 dark:border-gray-700 pt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Custo por candidato:</span>
                    <span className="font-bold text-lg text-gray-700">
                      1 crédito
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 p-2 rounded-md">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Você será cobrado apenas pelos candidatos que visualizar/revelar contatos.</span>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setShowGlobalExpansionConfirm(false)}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleExpandToGlobal}
              disabled={isExpandingToGlobal}
              className="text-white gap-2 bg-gray-900"
            >
              {isExpandingToGlobal ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Expandindo...
                </>
              ) : (
                <>
                  <Globe className="w-4 h-4" />
                  Expandir Busca
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent className="sm:max-w-[320px] w-[85vw] p-4 border border-gray-100" style={{ borderRadius: '10px', fontFamily: '"Open Sans", sans-serif' }}>
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ backgroundColor: pendingSourceChange === 'hybrid' ? 'rgba(96, 190, 209, 0.15)' : 'rgba(217, 119, 6, 0.15)' }}>
                {pendingSourceChange === 'hybrid' ? (
                  <Zap className="w-4 h-4 text-gray-700" />
                ) : (
                  <Globe className="w-4 h-4" style={{ color: 'var(--status-warning)' }} />
                )}
              </div>
              <div>
                <h3 className={textStyles.title}>
                  {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
                </h3>
                <p className={textStyles.caption}>
                  {pendingSourceChange === 'hybrid' 
                    ? 'Combina base local + global (800M+ perfis).'
                    : 'Acessa 800M+ perfis profissionais.'}
                </p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-md p-3 space-y-2 border border-gray-100">
              <div className="flex justify-between items-center text-xs">
                <span className={textStyles.bodySmall}>Tipo de busca:</span>
                <span className={`${textStyles.label} text-gray-800`}>{pendingSourceChange === 'hybrid' ? 'Híbrido' : 'Global'}</span>
              </div>
              <div className="border-t border-gray-200 pt-2">
                <div className="flex justify-between items-center text-xs">
                  <span className={`${textStyles.label} text-gray-800`}>Custo por candidato:</span>
                  <span className="font-semibold text-gray-700">
                    1 crédito
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-1.5 text-micro text-amber-600 bg-amber-50 p-2 rounded-md">
              <AlertCircle className="w-3 h-3 flex-shrink-0" />
              <span>Cada candidato da base global consumirá 1 crédito.</span>
            </div>
          </div>
          
          <div className="flex gap-2.5 pt-3">
            <button
              onClick={() => {
                setShowSourceChangeModal(false)
                setPendingSourceChange(null)
              }}
              className="flex-1 h-8 text-xs px-3 rounded-md bg-white border border-gray-200 text-gray-800 hover:bg-gray-50 font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={confirmSourceChange}
              className="flex-1 h-8 text-xs px-3 rounded-md text-white flex items-center justify-center gap-1.5 font-medium transition-colors hover:opacity-90 bg-gray-900"
            >
              {pendingSourceChange === 'hybrid' ? (
                <>
                  <Zap className="w-3.5 h-3.5" />
                  Ativar
                </>
              ) : (
                <>
                  <Globe className="w-3.5 h-3.5" />
                  Ativar
                </>
              )}
            </button>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Filtro de Contato (Email/Telefone) */}
      <AlertDialog open={showContactFilterModal} onOpenChange={setShowContactFilterModal}>
        <AlertDialogContent className="max-w-md border border-gray-100">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'rgba(93, 164, 122, 0.15)' }}>
                {pendingContactFilter === 'email' ? (
                  <Mail className="w-4 h-4 text-wedo-green" />
                ) : (
                  <Phone className="w-4 h-4 text-wedo-green" />
                )}
              </div>
              {pendingContactFilter === 'email' ? 'Filtrar por Email' : 'Filtrar por Telefone'}
            </AlertDialogTitle>
            <AlertDialogDescription className="space-y-4">
              <p className="text-sm text-gray-800">
                {pendingContactFilter === 'email'
                  ? 'Ao ativar este filtro, a busca retornará apenas candidatos com email disponível.'
                  : 'Ao ativar este filtro, a busca retornará apenas candidatos com telefone disponível.'}
              </p>
              
              <div className="bg-gray-50 rounded-md p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-800">Filtro:</span>
                  <span className="font-medium">{pendingContactFilter === 'email' ? 'Apenas com Email' : 'Apenas com Telefone'}</span>
                </div>
                <div className="border-t border-gray-200 pt-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">Custo adicional:</span>
                    <span className="font-bold text-lg text-wedo-green">
                      +1 crédito/cand
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 p-2 rounded-md">
                <CheckCircle className="w-4 h-4 flex-shrink-0" />
                <span>Você não gastará créditos com perfis sem dados de contato disponíveis.</span>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => {
              setShowContactFilterModal(false)
              setPendingContactFilter(null)
            }}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={confirmContactFilterChange}
              className="text-white gap-2 bg-wedo-green"
            >
              {pendingContactFilter === 'email' ? (
                <>
                  <Mail className="w-4 h-4" />
                  Ativar Filtro Email
                </>
              ) : (
                <>
                  <Phone className="w-4 h-4" />
                  Ativar Filtro Telefone
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Advanced Filters Modal */}
      {/* Modal de Filtros Avançados removido - agora usa painel lateral */}

      {/* Modal Salvar como Arquétipo */}
      <AlertDialog 
        open={showSaveAsArchetypeModal} 
        onOpenChange={(open) => {
          setShowSaveAsArchetypeModal(open)
          // Se fechando, resetar modo de criação
          if (!open && isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
      >
        <AlertDialogContent className="max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-base" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              <Bookmark className="w-5 h-5 text-gray-700" />
              Salvar como Arquétipo
            </AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-4 pt-2">
                <p className="text-xs text-gray-800 dark:text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                  Transforme esta busca em um arquétipo reutilizável para encontrar candidatos similares rapidamente.
                </p>
                
                {/* Query atual */}
                <div className="p-3 rounded-md bg-gray-50 dark:bg-gray-800">
                  <p className="text-xs font-medium text-gray-800 mb-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    {isCreatingArchetype ? 'Descrição do perfil:' : 'Busca atual:'}
                  </p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 line-clamp-3" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                    {isCreatingArchetype && newArchetypeData.query 
                      ? newArchetypeData.query 
                      : (lastSuccessfulQuery || searchResults.query || 'Nenhuma busca realizada')}
                  </p>
                </div>
                
                {/* Seletor de Emoji */}
                <div>
                  <label className="text-xs font-medium mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Ícone</label>
                  <div className="flex gap-2 flex-wrap">
                    {['🎯', '🚀', '⚛️', '🛠️', '📱', '☁️', '👨‍💼', '💼', '🔧', '📊', '🧠', '🔐'].map((emoji) => (
                      <button
                        key={emoji}
                        onClick={() => setArchetypeEmojiInput(emoji)}
                        className={`w-10 h-10 rounded-md text-xl flex items-center justify-center transition-all ${
                          archetypeEmojiInput === emoji 
                            ? 'bg-gray-100 dark:bg-gray-800 border-2 border-gray-900 dark:border-gray-50' 
                            : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                        }`}
                      >
                        {emoji}
                      </button>
                    ))}
                  </div>
                </div>
                
                {/* Nome do Arquétipo */}
                <div>
                  <label className="text-xs font-medium mb-1.5 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Nome do Arquétipo</label>
                  <Input
                    value={archetypeNameInput}
                    onChange={(e) => setArchetypeNameInput(e.target.value)}
                    placeholder="Ex: DevOps Sênior Cloud"
                    className="text-sm"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                  />
                </div>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel onClick={() => {
              setShowSaveAsArchetypeModal(false)
              // Resetar modo de criação ao cancelar
              if (isCreatingArchetype) {
                setIsCreatingArchetype(false)
                setArchetypeCreationStep('initial')
                setNewArchetypeData({})
              }
            }}>
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => {
                const queryToSave = isCreatingArchetype && newArchetypeData.query 
                  ? newArchetypeData.query 
                  : (lastSuccessfulQuery || searchResults.query)
                
                if (archetypeNameInput.trim() && queryToSave) {
                  const newArchetype: Archetype = {
                    id: `archetype-${Date.now()}`,
                    name: archetypeNameInput.trim(),
                    description: queryToSave,
                    emoji: archetypeEmojiInput,
                    query: queryToSave,
                    filters: {},
                    createdAt: new Date(),
                    isDefault: false
                  }
                  setUserArchetypes(prev => [...prev, newArchetype])
                  setShowSaveAsArchetypeModal(false)
                  setArchetypeNameInput('')
                  
                  // Resetar modo de criação
                  setIsCreatingArchetype(false)
                  setArchetypeCreationStep('initial')
                  setNewArchetypeData({})
                  
                  // Feedback via chat
                  const liaMessage: ChatMessage = {
                    id: `lia-archetype-saved-${Date.now()}`,
                    type: 'lia',
                    content: `✅ Arquétipo "${archetypeNameInput.trim()}" salvo com sucesso! Você pode encontrá-lo na aba Arquétipos.`,
                    timestamp: new Date()
                  }
                  setChatMessages(prev => [...prev, liaMessage])
                }
              }}
              disabled={!archetypeNameInput.trim()}
              className="text-white bg-gray-900"
            >
              <Bookmark className="w-4 h-4 mr-1" />
              Salvar Arquétipo
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onApply={(filters) => {
          setActiveSearchFilters(filters)
          setShowAdvancedSearch(false)
          
          // Sync hide viewed candidates filter to the hook
          const hideScope = filters.general?.hideViewedScope || "dont_hide"
          const hidePeriod = filters.general?.hideViewedPeriod || "all_time"
          hideViewedCandidates.setScope(hideScope)
          hideViewedCandidates.setPeriod(hidePeriod)
          
          // Fetch viewed candidates if filter is enabled
          if (hideScope !== "dont_hide") {
            hideViewedCandidates.fetchViewedCandidates()
          }
        }}
        initialFilters={activeSearchFilters}
        estimatedMatches={1000000}
      />

      {/* Add to List Modal */}
      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => {
          setShowAddToListModal(false)
          setAddToListCandidateIds([])
          setAddToListCandidateNames([])
        }}
        candidateIds={addToListCandidateIds}
        candidateNames={addToListCandidateNames}
        onSuccess={() => {
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à lista"
          })
        }}
      />

      {/* Share Search Modal */}
      <ShareSearchModal
        open={showShareSearchModal}
        onClose={() => {
          setShowShareSearchModal(false)
          setShareSearchCandidates([])
          setShareSearchTitle('')
        }}
        shareType="search"
        title={shareSearchTitle}
        candidateIds={shareSearchCandidates.map(c => c.id)}
        candidateCount={shareSearchCandidates.length}
        sourceQuery={lastSearchQuery || undefined}
      />

      {/* Add List to Vacancies Modal */}
      {selectedListForVacancies && (
        <AddListToVacanciesModal
          isOpen={showAddListToVacanciesModal}
          onClose={() => {
            setShowAddListToVacanciesModal(false)
            setSelectedListForVacancies(null)
          }}
          listId={selectedListForVacancies.id}
          listName={selectedListForVacancies.name}
          candidateCount={selectedListForVacancies.candidateCount}
          onSuccess={() => {
            toast({
              title: "Sucesso",
              description: "Candidatos adicionados às vagas selecionadas"
            })
          }}
        />
      )}

      {/* Add Candidates to Vacancy Modal */}
      <AddCandidatesToVacancyModal
        isOpen={showAddToVacancyModal}
        onClose={() => setShowAddToVacancyModal(false)}
        candidateIds={Array.from(selectedCandidatesForBatch)}
        candidateNames={candidates.filter(c => selectedCandidatesForBatch.has(c.id)).map(c => c.name)}
        currentRecruiterEmail={user?.email}
        onSuccess={() => {
          setSelectedCandidatesForBatch(new Set())
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à vaga"
          })
        }}
      />

      {/* Modal de aviso de candidatos Pearch não salvos */}
      <UnsavedPearchWarningModal
        isOpen={showUnsavedWarningModal}
        onClose={() => {
          setShowUnsavedWarningModal(false)
          setPendingTabChange(null)
        }}
        onSaveAndExit={handleSaveAllAndExit}
        onExitWithoutSaving={handleExitWithoutSaving}
        unsavedCount={unsavedPearchCandidates.length}
        unsavedCandidates={unsavedPearchCandidates}
        isSaving={isSavingToBase}
      />

      {/* Modal de Edição de Query - Centralizado na tela */}
      {showEditQueryModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)', backdropFilter: 'blur(1px)' }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setShowEditQueryModal(false)
          }}
        >
          <div 
            className="bg-white rounded-md border border-gray-100 w-full max-w-[900px] max-h-[90vh] overflow-hidden flex flex-col mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex-shrink-0 p-6 pb-4">
              <h2 className="text-sm font-semibold text-gray-800 flex items-center gap-2" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                <Search className="w-4 h-4 text-gray-700" />
                Editar sua busca
              </h2>
              <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                Refine sua busca com linguagem natural. A LIA irá analisar e sugerir melhorias.
              </p>
            </div>
            
            {/* Content */}
            <div className="flex-1 px-6 pb-4 overflow-auto">
              <SmartSearchInput
                value={editQueryValue}
                onChange={setEditQueryValue}
                onSubmit={async (query, entities, mode, metadata) => {
                  if (query.trim()) {
                    setShowEditQueryModal(false)
                    const trimmedQuery = query.trim()
                    setSearchTerm(trimmedQuery)
                    setLastSearchQuery(trimmedQuery)
                    setLastSearchMode(mode || 'natural')
                    setLastSearchEntities(entities)
                    setLastSearchMetadata(metadata)
                    await executeSearch(trimmedQuery, entities, mode || 'natural', metadata, false)
                  }
                }}
                onCancel={() => setShowEditQueryModal(false)}
                onOpenFilters={() => {
                  setShowEditQueryModal(false)
                  setShowAdvancedSearch(true)
                }}
                placeholder="Ex: desenvolvedor python com 5 anos de experiência em machine learning"
                activeFiltersCount={getActiveSearchFiltersCount()}
                searchSource={searchSource}
                onSearchSourceChange={setSearchSource}
                requireEmails={pearchSearchOptions.requireEmails}
                onRequireEmailsChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requireEmails: value }))}
                requirePhoneNumbers={pearchSearchOptions.requirePhoneNumbers}
                onRequirePhoneNumbersChange={(value) => setPearchSearchOptions(prev => ({ ...prev, requirePhoneNumbers: value }))}
              />
            </div>
            
            {/* Footer */}
            <div className="flex-shrink-0 border-t border-gray-100 p-6 pt-4 flex justify-end gap-3">
              <button
                onClick={() => setShowEditQueryModal(false)}
                className="px-4 py-2 text-sm text-gray-800 hover:bg-gray-100 rounded-md transition-colors border border-gray-200"
                style={{ fontFamily: 'Open Sans, sans-serif' }}
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  if (editQueryValue.trim()) {
                    const newQuery = editQueryValue.trim()
                    setShowEditQueryModal(false)
                    setSearchTerm(newQuery)
                    setLastSearchQuery(newQuery)
                    setLastSearchMode('ai-natural')
                    setLastSearchEntities(null)
                    await executeSearch(newQuery, null, 'ai-natural', undefined, false)
                  }
                }}
                className="px-4 py-2 text-sm text-white rounded-md transition-colors bg-gray-900 hover:bg-gray-800"
                style={{ fontFamily: 'Open Sans, sans-serif' }}
              >
                Salvar e Buscar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Preview de Sugestão IA */}
      <Dialog open={!!previewSuggestion} onOpenChange={(open) => {
        if (!open) {
          setPreviewSuggestion(null)
          setPreviewingUserArchetype(null)
        }
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              <Brain className="w-5 h-5 text-wedo-cyan" />
              {previewSuggestion?.name}
            </DialogTitle>
            <DialogDescription className="text-xs text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              {previewSuggestion?.description}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-2">
            <div>
              <label className="text-xs font-medium mb-2 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                Critérios de busca
              </label>
              <div className="flex flex-wrap gap-2">
                {previewTags.map((tag, index) => (
                  <Badge 
                    key={index}
                    className="!text-xs !px-2 !py-1 flex items-center gap-1.5"
                    style={{ backgroundColor: 'rgba(96, 190, 209, 0.15)', border: '1px solid rgba(96, 190, 209, 0.3)' }}
                  >
                    {tag}
                    <button
                      onClick={() => setPreviewTags(prev => prev.filter((_, i) => i !== index))}
                      className="ml-0.5 hover:bg-wedo-cyan/20 rounded-full p-0.5 transition-colors"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
            
            <div>
              <label className="text-xs font-medium mb-2 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                Adicionar critério
              </label>
              <div className="flex gap-2">
                <Input
                  value={newPreviewTag}
                  onChange={(e) => setNewPreviewTag(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && newPreviewTag.trim()) {
                      e.preventDefault()
                      setPreviewTags(prev => [...prev, newPreviewTag.trim()])
                      setNewPreviewTag("")
                    }
                  }}
                  placeholder="Digite e pressione Enter..."
                  className="text-sm"
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                />
                <Button
                  type="button"
                  size="sm"
                  onClick={() => {
                    if (newPreviewTag.trim()) {
                      setPreviewTags(prev => [...prev, newPreviewTag.trim()])
                      setNewPreviewTag("")
                    }
                  }}
                  className="bg-gray-900"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
          
          <DialogFooter className="flex-col sm:flex-row gap-2 sm:gap-3 pt-2">
            <Button
              variant="outline"
              onClick={() => {
                setPreviewSuggestion(null)
                setPreviewingUserArchetype(null)
              }}
              className="w-full sm:w-auto order-3 sm:order-1"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              Cancelar
            </Button>
            <Button
              variant="outline"
              onClick={async () => {
                if (!previewSuggestion) return
                if (previewTags.length === 0) {
                  toast({
                    title: "Nenhum critério",
                    description: "Adicione pelo menos um critério de busca para salvar o arquétipo.",
                    variant: "destructive"
                  })
                  return
                }
                setIsSavingPreviewArchetype(true)
                try {
                  const editedFilters = buildFiltersFromTags(previewTags)
                  const queryFromTags = previewTags.join(' ')
                  
                  if (previewingUserArchetype) {
                    const response = await fetch(`/api/backend-proxy/search/archetypes/${previewingUserArchetype.id}`, {
                      method: 'PATCH',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        name: previewSuggestion.name,
                        description: previewSuggestion.description,
                        query: queryFromTags,
                        criteria: {
                          keywords: editedFilters.keywords,
                          skills: editedFilters.skills,
                          locations: editedFilters.locations,
                          seniority: editedFilters.seniority
                        },
                      }),
                    })
                    
                    if (!response.ok && response.status !== 404) {
                      throw new Error(`Failed to update archetype: ${response.status}`)
                    }
                    
                    setUserArchetypes(prev => prev.map(a => 
                      a.id === previewingUserArchetype.id 
                        ? {
                            ...a,
                            name: previewSuggestion.name,
                            description: previewSuggestion.description,
                            query: queryFromTags,
                            filters: editedFilters,
                            tags: previewTags
                          }
                        : a
                    ))
                    toast({
                      title: "Arquétipo atualizado",
                      description: `"${previewSuggestion.name}" foi atualizado com sucesso.`,
                    })
                  } else {
                    const response = await fetch('/api/backend-proxy/search/archetypes/', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        name: previewSuggestion.name,
                        description: previewSuggestion.description,
                        query: queryFromTags,
                        criteria: {
                          keywords: editedFilters.keywords,
                          skills: editedFilters.skills,
                          locations: editedFilters.locations,
                          seniority: editedFilters.seniority
                        },
                        emoji: '✨',
                      }),
                    })
                    
                    if (!response.ok) {
                      throw new Error(`Failed to save archetype: ${response.status}`)
                    }
                    
                    const savedArchetype = await response.json()
                    
                    const newArchetype: Archetype = {
                      id: savedArchetype.id || `arch-${Date.now()}`,
                      name: previewSuggestion.name,
                      description: previewSuggestion.description,
                      emoji: '✨',
                      query: queryFromTags,
                      filters: editedFilters,
                      tags: previewTags,
                      createdAt: new Date()
                    }
                    setUserArchetypes(prev => [...prev, newArchetype])
                    toast({
                      title: "Arquétipo salvo",
                      description: `"${previewSuggestion.name}" foi adicionado aos seus arquétipos.`,
                    })
                  }
                  setPreviewSuggestion(null)
                  setPreviewingUserArchetype(null)
                } catch (error) {
                  console.error('Error saving archetype:', error)
                  toast({
                    title: "Erro ao salvar",
                    description: "Não foi possível salvar o arquétipo. Tente novamente.",
                    variant: "destructive"
                  })
                } finally {
                  setIsSavingPreviewArchetype(false)
                }
              }}
              disabled={isSavingPreviewArchetype || previewTags.length === 0}
              className="w-full sm:w-auto order-2"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              {isSavingPreviewArchetype ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  {previewingUserArchetype ? 'Atualizando...' : 'Salvando...'}
                </>
              ) : previewingUserArchetype ? (
                <>
                  <Edit className="w-4 h-4 mr-2" />
                  Atualizar Arquétipo
                </>
              ) : (
                <>
                  <Bookmark className="w-4 h-4 mr-2" />
                  Salvar como Meu Arquétipo
                </>
              )}
            </Button>
            <Button
              onClick={async () => {
                if (!previewSuggestion) return
                if (previewTags.length === 0) {
                  toast({
                    title: "Nenhum critério",
                    description: "Adicione pelo menos um critério de busca para executar.",
                    variant: "destructive"
                  })
                  return
                }
                const editedFilters = buildFiltersFromTags(previewTags)
                const queryFromTags = previewTags.join(' ')
                setLiaPromptValue(queryFromTags)
                setActiveSearchTab('ia-natural')
                setPreviewSuggestion(null)
                setPreviewingUserArchetype(null)
                await executeSearch(queryFromTags, editedFilters, 'natural', { mode: 'natural' as any }, false)
              }}
              disabled={previewTags.length === 0}
              className="w-full sm:w-auto order-1 sm:order-3 bg-gray-900" style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              <Search className="w-4 h-4 mr-2" />
              Usar Busca
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Modal de Confirmação de Exclusão de Arquétipo */}
      <AlertDialog open={!!archetypeToDelete} onOpenChange={(open) => !open && setArchetypeToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2 text-base" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              <AlertCircle className="w-5 h-5 text-red-500" />
              Excluir Arquétipo
            </AlertDialogTitle>
            <AlertDialogDescription className="text-base-ui text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              Tem certeza que deseja excluir o arquétipo <strong>"{archetypeToDelete?.name}"</strong>? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel 
              onClick={() => setArchetypeToDelete(null)}
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                if (!archetypeToDelete) return
                setIsDeletingArchetype(true)
                try {
                  const response = await fetch(`/api/backend-proxy/search/archetypes/${archetypeToDelete.id}`, {
                    method: 'DELETE'
                  })
                  
                  if (!response.ok && response.status !== 404) {
                    throw new Error(`Failed to delete archetype: ${response.status}`)
                  }
                  
                  setUserArchetypes(prev => prev.filter(a => a.id !== archetypeToDelete.id))
                  toast({
                    title: "Arquétipo excluído",
                    description: `"${archetypeToDelete.name}" foi removido dos seus arquétipos.`,
                  })
                } catch (error) {
                  console.error('Error deleting archetype:', error)
                  setUserArchetypes(prev => prev.filter(a => a.id !== archetypeToDelete.id))
                  toast({
                    title: "Arquétipo excluído",
                    description: `"${archetypeToDelete.name}" foi removido dos seus arquétipos.`,
                  })
                } finally {
                  setIsDeletingArchetype(false)
                  setArchetypeToDelete(null)
                }
              }}
              className="bg-red-500 hover:bg-red-600"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
              disabled={isDeletingArchetype}
            >
              {isDeletingArchetype ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Excluindo...
                </>
              ) : (
                'Excluir'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>


    </div>
  )
}
