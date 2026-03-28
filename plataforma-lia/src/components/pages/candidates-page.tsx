// CandidatesPage — extracted hooks: useCandidatesCVHandlers, useCandidatesSearch, useCandidatesLIAHandlers, useCandidatesActions
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
  
  const { toast } = useToast()
  
  const { saveTalentFunnelState } = useNavigationPersistence()
  
  useEffect(() => {
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
  const [liaWidth, setLiaWidth] = useState(400) // Largura padrão 400px - ElevenLabs pattern
  const [isResizingLIA, setIsResizingLIA] = useState(false)
  const [isLiaSuperChat, setIsLiaSuperChat] = useState(false) // Modo superchat expandido
  
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
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-gray-100 dark:bg-gray-800 rounded">
                    📧 Email enviado há 2 dias
                  </div>
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-status-success/10 dark:bg-status-success/20 rounded">
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
                <Star className="w-3 h-3 text-status-warning" />
                4.8
              </div>
              <div className="text-gray-800">Avaliação</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded">
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
          <CandidateSearchResultsView
            lastSearchQuery={lastSearchQuery}
            lastSearchEntities={lastSearchEntities}
            onBack={() => setShowSearchResults(false)}
            onOpenEditQueryModal={(value) => {
              setEditQueryValue(value)
              setShowEditQueryModal(true)
            }}
            onOpenAdvancedSearch={() => setShowAdvancedSearch(true)}
            selectedCandidatesForBatch={selectedCandidatesForBatch}
            selectedPearchCount={selectedPearchCount}
            deselectAllCandidates={deselectAllCandidates}
            onAddToVacancy={() => setShowAddToVacancyModal(true)}
            onAddToList={handleAddToList}
            isAddingToList={isAddingToList}
            candidates={candidates}
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
            onBulkEmail={handleBulkEmail}
            onBulkWSIScreening={handleBulkWSIScreening}
            onToggleFavoriteBatch={() => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.toggleFavoriteCandidate(id))
              toast({
                title: "Favoritos atualizados",
                description: `${selectedCandidatesForBatch.size} candidato(s) adicionado(s) aos favoritos`
              })
            }}
            onHideBatch={() => {
              selectedCandidatesForBatch.forEach(id => talentFunnel.hideCandidate(id))
              toast({
                title: "Candidatos ocultos",
                description: `${selectedCandidatesForBatch.size} candidato(s) oculto(s) da pesquisa`
              })
              deselectAllCandidates()
            }}
            onSaveToLocalBase={handleSaveToLocalBase}
            isSavingToBase={isSavingToBase}
            showCrossTabBanner={showCrossTabBanner}
            crossTabFilter={crossTabFilter}
            clearCrossTabFilter={clearCrossTabFilter}
            viewingList={viewingList}
            setViewingList={setViewingList}

            setShowSearchResults={setShowSearchResults}
            setSearchTerm={setSearchTerm}
            setLastSearchQuery={setLastSearchQuery}
            setActiveTab={setActiveTab}
            showExpandedLIA={showExpandedLIA}
            isLIAThinking={isLIAThinking}
            liaPromptValue={liaPromptValue}
            setLiaPromptValue={setLiaPromptValue}
            setShowExpandedLIA={setShowExpandedLIA}
            onAICommand={handleAICommand}
            searchSortBy={searchSortBy}
            setSearchSortBy={setSearchSortBy}
            sortedCandidates={sortedCandidates}
            selectAllCandidates={selectAllCandidates}
            showTableFiltersPanel={showTableFiltersPanel}
            setShowTableFiltersPanel={setShowTableFiltersPanel}
            getActiveTableFiltersCount={getActiveTableFiltersCount}
            showColumnConfig={showColumnConfig}
            onToggleColumnConfig={handleToggleColumnConfig}
            tableColumns={tableColumns}
            quickFilters={quickFilters}
            searchTerm={searchTerm}
            getActiveAdvancedFiltersCount={getActiveAdvancedFiltersCount}
            isLiaSuperChat={isLiaSuperChat}
            setIsLiaSuperChat={setIsLiaSuperChat}
            liaWidth={liaWidth}
            setLiaWidth={setLiaWidth}
            isResizingLIA={isResizingLIA}
            setIsResizingLIA={setIsResizingLIA}
            activeSearchTab={activeSearchTab}
            setActiveSearchTab={setActiveSearchTab}
            chatMessages={chatMessages}
            setChatMessages={setChatMessages}
            searchResults={searchResults}
            setSearchResults={setSearchResults}
            currentSearchSource={currentSearchSource}
            searchSource={searchSource}
            pearchSearchOptions={pearchSearchOptions}
            activeSearchFilters={activeSearchFilters}
            setActiveSearchFilters={setActiveSearchFilters}
            isCreatingArchetype={isCreatingArchetype}
            setIsCreatingArchetype={setIsCreatingArchetype}
            archetypeCreationStep={archetypeCreationStep}
            setArchetypeCreationStep={setArchetypeCreationStep}
            setNewArchetypeData={setNewArchetypeData}
            setShowSaveAsArchetypeModal={setShowSaveAsArchetypeModal}
            setShowGlobalExpansionConfirm={setShowGlobalExpansionConfirm}
            setCandidates={setCandidates}
            setHasSearchResults={setHasSearchResults}
            setSearchResultsCount={setSearchResultsCount}
            setLocalResultsCount={setLocalResultsCount}
            setPearchResultsCount={setPearchResultsCount}
            setDisplayedResultsCount={setDisplayedResultsCount}
            onLIAChatMessage={handleLIAChatMessage}
            onQuickAction={handleQuickAction}
            onCalibrationLike={handleCalibrationLike}
            onCalibrationDislike={handleCalibrationDislike}
            setUserCollapsedLIA={setUserCollapsedLIA}
            tableFilters={tableFilters}
            setTableFilters={setTableFilters}
            newSoftSkillFilter={newSoftSkillFilter}
            setNewSoftSkillFilter={setNewSoftSkillFilter}
            newCertificationFilter={newCertificationFilter}
            setNewCertificationFilter={setNewCertificationFilter}
            toggleTableFilter={toggleTableFilter}
            clearAllTableFilters={clearAllTableFilters}
            isLoading={isLoading}
            visibleCandidates={visibleCandidates}
            visibleTableColumns={visibleTableColumns}
            columnWidths={columnWidths}
            setColumnWidths={setColumnWidths}
            setTableColumns={setTableColumns}
            pinnedCandidates={pinnedCandidates}
            favorites={favorites}
            sortBy={sortBy}
            sortOrder={sortOrder}
            setSortBy={setSortBy}
            setSortOrder={setSortOrder}
            setSelectedCandidatesForBatch={setSelectedCandidatesForBatch}
            onCandidateClick={handleCandidateClick}
            onTogglePin={handleTogglePin}
            onToggleFavorite={handleToggleFavorite}
            renderCellValue={renderCellValue}
            tableContainerRef={tableContainerRef}
            showSearchResults={showSearchResults}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            itemsPerPage={itemsPerPage}
            getPaginatedCandidates={getPaginatedCandidates}
            clearAllFilters={clearAllFilters}
            displayedResultsCount={displayedResultsCount}
            isLoadingMore={isLoadingMore}
            onLoadMore={handleLoadMore}
            columnSearchTerm={columnSearchTerm}
            setColumnSearchTerm={setColumnSearchTerm}
            setShowColumnConfig={setShowColumnConfig}
            showCandidatePreview={showCandidatePreview}
            previewCandidate={previewCandidate}
            previewWidth={previewWidth}
            onPreviewResize={handlePreviewResize}
            isPreviewMaximized={isPreviewMaximized}
            onCloseCandidatePreview={handleCloseCandidatePreview}
            onTogglePreviewMaximize={handleTogglePreviewMaximize}
            onCandidatePageOpen={handleCandidatePageOpen}
            setSelectedCandidateForAction={setSelectedCandidateForAction}
            setShowScheduleModal={setShowScheduleModal}
            onStartWSITextScreening={handleStartWSITextScreening}
            onSendEmail={handleSendEmail}
            onSendWhatsApp={handleSendWhatsApp}
            onSendTriagem={handleSendTriagem}
            onSendAgendamento={handleSendAgendamento}
            onSendFeedback={handleSendFeedback}
            setPreviewCandidate={setPreviewCandidate}
            setShareSearchCandidates={setShareSearchCandidates}
            setShareSearchTitle={setShareSearchTitle}
            setShowShareSearchModal={setShowShareSearchModal}
            toast={toast}
            talentFunnel={talentFunnel}
            setEditQueryValue={setEditQueryValue}
            setShowEditQueryModal={setShowEditQueryModal}
            setShowAddToVacancyModal={setShowAddToVacancyModal}
          />
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
      <CreditConfirmationModal
        open={showCreditConfirmation}
        onOpenChange={setShowCreditConfirmation}
        creditEstimate={creditEstimate}
        pearchSearchOptions={pearchSearchOptions}
        onSearchOptionsChange={setPearchSearchOptions}
        onCancel={() => {
          setShowCreditConfirmation(false)
          setPendingSearchRequest(null)
        }}
        onConfirm={handleConfirmPearchSearch}
      />

      {/* Modal de Confirmação para Expansão Global */}
      <GlobalExpansionConfirmModal
        open={showGlobalExpansionConfirm}
        onOpenChange={setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={lastSuccessfulQuery}
        lastSearchQuery={lastSearchQuery}
        localResultsCount={localResultsCount}
        isExpandingToGlobal={isExpandingToGlobal}
        onConfirm={handleExpandToGlobal}
      />

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <SourceChangeConfirmModal
        open={showSourceChangeModal}
        onOpenChange={setShowSourceChangeModal}
        pendingSourceChange={pendingSourceChange}
        onCancel={() => { setShowSourceChangeModal(false); setPendingSourceChange(null) }}
        onConfirm={confirmSourceChange}
      />

      {/* Modal de Confirmação para Filtro de Contato (Email/Telefone) */}
      <ContactFilterConfirmModal
        open={showContactFilterModal}
        onOpenChange={setShowContactFilterModal}
        pendingContactFilter={pendingContactFilter}
        onCancel={() => { setShowContactFilterModal(false); setPendingContactFilter(null) }}
        onConfirm={confirmContactFilterChange}
      />

      {/* Advanced Filters Modal */}
      {/* Modal de Filtros Avançados removido - agora usa painel lateral */}

      {/* Modal Salvar como Arquétipo */}
      <SaveAsArchetypeModal
        open={showSaveAsArchetypeModal}
        onOpenChange={setShowSaveAsArchetypeModal}
        currentQuery={lastSuccessfulQuery || searchResults.query || ''}
        isCreatingArchetype={isCreatingArchetype}
        newArchetypeData={newArchetypeData}
        onClose={() => {
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
        onSave={(archetype, message) => {
          setUserArchetypes(prev => [...prev, archetype])
          setShowSaveAsArchetypeModal(false)
          setChatMessages(prev => [...prev, message])
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
      />

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
      {/* Modal de Edição de Busca */}
      <EditQueryModal
        isOpen={showEditQueryModal}
        onClose={() => setShowEditQueryModal(false)}
        initialValue={editQueryValue}
        activeFiltersCount={getActiveSearchFiltersCount()}
        searchSource={searchSource}
        onSearchSourceChange={setSearchSource}
        pearchSearchOptions={pearchSearchOptions}
        onPearchOptionsChange={setPearchSearchOptions}
        onOpenFilters={() => setShowAdvancedSearch(true)}
        onSubmitNatural={async (query, entities, mode, metadata) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode(mode || 'natural')
          setLastSearchEntities(entities)
          setLastSearchMetadata(metadata)
          await executeSearch(query, entities, mode || 'natural', metadata, false)
        }}
        onSubmitAI={async (query) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode('ai-natural')
          setLastSearchEntities(null)
          await executeSearch(query, null, 'ai-natural', undefined, false)
        }}
      />

      {/* Modal de Preview de Sugestão IA */}
      <PreviewSuggestionModal
        previewSuggestion={previewSuggestion}
        previewingUserArchetype={previewingUserArchetype}
        onClose={() => {
          setPreviewSuggestion(null)
          setPreviewingUserArchetype(null)
        }}
        buildFiltersFromTags={buildFiltersFromTags}
        onUpdateArchetype={(id, updates) => {
          setUserArchetypes(prev => prev.map(a =>
            a.id === id ? { ...a, ...updates } : a
          ))
        }}
        onSaveArchetype={(newArchetype) => setUserArchetypes(prev => [...prev, newArchetype as any])}
        onExecuteSearch={async (query, filters, mode, metadata, usePearch) => {
          await executeSearch(query, filters as any, mode as any, metadata as any, usePearch)
        }}
        onSetLiaPromptValue={setLiaPromptValue}
        onSetActiveSearchTab={setActiveSearchTab}
      />

      {/* Modal de Confirmação de Exclusão de Arquétipo */}
      <DeleteArchetypeModal
        archetypeToDelete={archetypeToDelete}
        onClose={() => setArchetypeToDelete(null)}
        onDeleted={(id) => setUserArchetypes(prev => prev.filter(a => a.id !== id))}
      />

    </div>
  )
}
