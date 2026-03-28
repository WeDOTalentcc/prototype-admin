"use client"

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import dynamic from "next/dynamic"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { TriagemDetailsModal } from "@/components/triagem-details-modal"
import { JobReportModal } from "@/components/job-report-modal"
import { SendEmailModal } from "@/components/email-templates/send-email-modal"
import { UnifiedCommunicationModal, type CommunicationType } from "@/components/modals/unified-communication-modal"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { WSITextScreeningModal } from "@/components/wsi/wsi-text-screening-modal"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { RubricEvaluationModal } from "@/components/rubric-evaluation-modal"
import { BigFiveModal } from "@/components/big-five-modal"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { ScoreBreakdownBadgeLazy } from "@/components/score/ScoreBreakdownBadge"
import { GeneralScoreModal } from "@/components/modals/general-score-modal"
import { TechnicalTestModal } from "@/components/modals/technical-test-modal"
import { EnglishTestModal } from "@/components/modals/english-test-modal"
import { CandidateDecisionFlowModal } from "@/components/candidate-decision-flow-modal"
import { TestPreviewModal } from "@/components/pages/job-kanban/TestPreviewModal"
import { LIASuggestionsPanel } from "@/components/pages/job-kanban/LIASuggestionsPanel"
import { TestLibraryModal } from "@/components/pages/job-kanban/TestLibraryModal"
import { TestHistoryModal } from "@/components/pages/job-kanban/TestHistoryModal"
import { LIAQuestionsPanel } from "@/components/pages/job-kanban/LIAQuestionsPanel"
import { CandidateCompareModal } from "@/components/modals/candidate-compare-modal"
import { UniversalTransitionModal, useUniversalTransition, type UniversalTransitionConfirmData, type KanbanCandidate } from "@/components/kanban"
import { useAuth } from "@/components/auth-context"
import { useToast } from "@/hooks/use-toast"
import { useShortList } from "@/hooks/use-short-list"
import { useProactiveInsights } from "@/hooks/use-proactive-insights"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
import { useTalentFunnel } from "@/hooks/use-talent-funnel"
import { useCandidateSuggestions, getSuggestionForCandidate } from "@/hooks/useCandidateSuggestions"
import { AISuggestionBadge } from "@/components/ai"
import { 
  UnifiedCandidateTable, 
  type TableColumn, 
  type TableSortConfig,
  getColumnDefinition,
  getDefaultTableColumns,
  COLUMN_PRESETS,
  InteractiveSubStatusCell,
  InteractiveStageCell
} from "@/components/tables"
import {
  ArrowLeft, ArrowRight, Layers3, FileText, TrendingUp, Briefcase, MapPin, ListChecks, ChevronRight, ChevronUp, ChevronDown, ChevronLeft,
  ClipboardList, MessageCircle, Clock, Brain, Send, Code, Globe, BrainCircuit, Flag, Linkedin, Languages,
  CheckCircle, AlertCircle, AlertTriangle, X, Download, Share2, Settings, User, Mic, Search, Filter,
  Plus, Users, Star, Heart, MoreVertical, MoreHorizontal, Eye, Calendar, CalendarCheck, Archive, Mail, Phone, Video,
  Trophy, XCircle, ThumbsUp, Target, MessageSquareText, MessageSquare, Building, BarChart3, DollarSign, Activity,
  ArrowUp, ArrowDown, TrendingDown, Award, Pin, Edit, Pencil, Trash2, RefreshCw, Wand2, Library, BookOpen, Folder,
  History, Gauge, UserCheck, Timer, RotateCcw, SortAsc, SortDesc, Columns, Table as TableIcon, Bell, Maximize2, ThumbsDown, ArrowUpDown, EyeOff, GripVertical, Lightbulb, Bookmark, Paperclip, ChevronsLeftRight, Copy, Fingerprint, Loader2, Save, Link2, PauseCircle, PlayCircle
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { textStyles, cardStyles, badgeStyles, buttonStyles, formatScorePercent } from "@/lib/design-tokens"
import {
  RECRUITMENT_STAGES,
  SUB_STATUSES,
  CANDIDATE_SOURCES,
  getStageByName,
  getSubStatusDisplayName,
  getCandidateSourceById,
  isApplicationSource,
  mapLegacyStage,
  getCompanyPipelineStages,
  type RecruitmentStage,
  type SubStatus,
  type CandidateSource
} from "@/lib/recruitment-stages"
import { 
  DataRequestIndicator, 
  type DataRequestStatus, 
  type RequestedField,
  getDataRequestStatusFromFields
} from "@/components/ui/data-request-indicator"
import { 
  StatusBadge, 
  ChannelBadge, 
  SourceBadge, 
  WarningBadge,
  DateTimeBadge,
  OriginBadge,
  AwaitingBadge,
  STAGE_PASTEL_COLORS as STATUS_BADGE_PASTEL_COLORS
} from "@/components/ui/status-badge"
import { OverrideApproveButton } from "@/components/kanban/components/OverrideApproveButton"
import { useBulkCandidateDataRequests, type BulkDataRequestInfo } from "@/hooks/use-candidate-data-requests"
import { DataRequestModal, type DataRequestSubmitData } from "@/components/modals/data-request-modal"
import { CloseVacancyModal } from "@/components/modals/close-vacancy-modal"
import { JobStatusModal } from "@/components/modals/job-status-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { type BulkActionType } from "@/components/ui/bulk-selection-bar"
import { Checkbox } from "@/components/ui/checkbox"
import { BulkActionModal } from "@/components/modals/bulk-action-modal"
import { UnifiedBulkActionsBar, type BulkActionId } from "@/components/ui/unified-bulk-actions-bar"
import { PipelineStagesCarousel } from "@/components/ui/pipeline-stages-carousel"
import { mockJobData, mockCandidates } from "@/components/kanban/mock/candidates"
import { 
  generateWorkHistory, 
  generateEducation, 
  seededRandom, 
  getSalaryByExperience,
  type CandidateForDataGeneration 
} from "@/components/kanban/mock/data-generators"
import { 
  getUrgencyLevel,
  getScoreColor,
  getScoreBgColor,
  getStageColor,
  calculateGeneralScore,
  type UrgencyLevel 
} from "@/components/kanban/utils/status-utils"
import { CandidateTableRow } from "@/components/kanban/components/CandidateTableRow"
import { ScreeningQuestionsPanel } from "@/components/job-creation"
import { JobEditTab } from "@/components/jobs/JobEditTab"
import { useCompanyDefaults } from "@/hooks/use-company-defaults"
import { usePipelineInheritance } from "@/hooks/use-pipeline-inheritance"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { enrichStagesWithSubStatuses, buildSubStatusMap } from "@/components/kanban/utils/stage-utils"
import { useReturnEvents } from '@/hooks/use-return-events'
import { ColumnContextMenu } from "@/components/kanban/components/ColumnContextMenu"
import { SaturationBadge } from "@/components/kanban/components/SaturationBadge"
import { KanbanFiltersPanel } from "@/components/pages/job-kanban/KanbanFiltersPanel"
import { KanbanColumnConfigPanel } from "@/components/pages/job-kanban/KanbanColumnConfigPanel"
import { KanbanTableView } from "@/components/pages/job-kanban/KanbanTableView"
import { KanbanLIASidebar } from "@/components/pages/job-kanban/KanbanLIASidebar"
import { KanbanColumnRenderer } from "@/components/pages/job-kanban/KanbanColumnRenderer"

import { AddColumnPopover } from "@/components/pages/job-kanban/AddColumnPopover"
import { useKanbanBulkActions } from "@/components/pages/job-kanban/hooks/useKanbanBulkActions"
import { useKanbanLIAHandlers } from "@/components/pages/job-kanban/hooks/useKanbanLIAHandlers"
import { useKanbanCandidateDecisions } from "@/components/pages/job-kanban/hooks/useKanbanCandidateDecisions"
import { useKanbanJobEditing } from "@/components/pages/job-kanban/hooks/useKanbanJobEditing"
import { useKanbanDragDrop } from "@/components/pages/job-kanban/hooks/useKanbanDragDrop"
import { mapInterviewStagesToKanban, organizeCandidatesByDynamicStages, createInitialCandidatesData, createStageSlug, inferActionBehavior, DYNAMIC_STAGE_COLORS, type InterviewStageFromJob, type DynamicStage } from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { calculateNotaLiaGeral, getLiaAlerts, getFilteredAndSortedCandidates as getFilteredAndSortedCandidatesUtil } from "@/components/pages/job-kanban/utils/kanbanHelpers"
const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false })


// Helper para criar slug a partir do nome da etapa
const createStageSlug = (stageName: string): string => {
  return stageName
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
}

// Cores para etapas dinâmicas (ciclo de cores monocromáticas)
const DYNAMIC_STAGE_COLORS = [
  'var(--gray-600)', // gray-700
  'var(--gray-600)', // gray-600
  'var(--gray-400)', // gray-500
  'var(--gray-400)', // gray-400
  'var(--gray-400)', // gray-500
  'var(--gray-600)', // gray-600
  'var(--gray-600)', // gray-700
]

const inferActionBehavior = (slug: string, stageType?: string): string => {
  const map: Record<string, string> = {
    'sourcing': 'intake', 'screening': 'screening',
    'long_list': 'passive', 'short_list': 'passive',
    'interview_hr': 'scheduling', 'entrevista_rh': 'scheduling',
    'interview_technical': 'scheduling', 'entrevista_tecnica': 'scheduling',
    'interview_manager': 'scheduling', 'entrevista_gestor': 'scheduling',
    'interview_manager2': 'scheduling', 'entrevista_gestor_2': 'scheduling',
    'interview_final': 'scheduling', 'entrevista_final': 'scheduling',
    'technical_test': 'evaluation', 'teste_tecnico': 'evaluation',
    'english_test': 'evaluation', 'teste_de_ingles': 'evaluation',
    'references': 'verification', 'referencias': 'verification',
    'offer': 'offer', 'proposta': 'offer',
    'hired': 'conclusion_hired', 'rejected': 'conclusion_rejected',
    'offer_declined': 'conclusion_declined',
  }
  if (map[slug]) return map[slug]
  if (slug.includes('entrevista') || slug.includes('interview')) return 'scheduling'
  if (slug.includes('teste') || slug.includes('test')) return 'evaluation'
  if (slug.includes('referencia') || slug.includes('reference')) return 'verification'
  if (slug.includes('proposta') || slug.includes('offer')) return 'offer'
  if (stageType === 'interview') return 'scheduling'
  if (stageType === 'test' || stageType === 'automated') return 'evaluation'
  return 'passive'
}

const mapInterviewStagesToKanban = (
  interviewStages?: InterviewStageFromJob[],
  fallbackStages: RecruitmentStage[] = RECRUITMENT_STAGES
): DynamicStage[] => {
  // Se as etapas já têm metadata completa do pipeline (stageCategory, isInitial, isFinal, etc.)
  if (interviewStages && interviewStages.length > 0 && (interviewStages[0] as any).stageCategory) {
    const enrichedStages = interviewStages as any[]
    const activeStages = enrichedStages.filter((s: any) => s.isActive !== false)
    let colorIndex = 0
    return activeStages
      .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
      .map((stage: any) => {
        const displayName = stage.stageName || stage.displayName || stage.name || 'Sem nome'
        const stageId = stage.name || createStageSlug(displayName)
        const isIntermediate = !stage.isInitial && !stage.isFinal && stage.stageType === 'active'
        const color = stage.color || (isIntermediate ? DYNAMIC_STAGE_COLORS[colorIndex++ % DYNAMIC_STAGE_COLORS.length] : 'var(--gray-600)')
        return {
          id: stageId,
          name: stageId,
          displayName,
          order: stage.order,
          color,
          stageType: stage.stageType || 'active',
          isInitial: stage.isInitial || false,
          isFinal: stage.isFinal || false,
          isHired: stage.isHired || false,
          isRejection: stage.isRejection || false,
          actionBehavior: stage.actionBehavior || inferActionBehavior(stageId),
        }
      })
  }

  // Se não há interview_stages ou são formato antigo sem metadata, usar fallback
  if (!interviewStages || interviewStages.length === 0) {
    return fallbackStages
      .filter(stage => stage.stageType !== 'standby')
      .map((stage) => ({
        id: stage.name,
        name: stage.name,
        displayName: stage.displayName,
        order: stage.stageOrder,
        color: stage.color,
        stageType: stage.stageType === 'standby' ? 'active' : stage.stageType,
        isInitial: stage.isInitial,
        isFinal: stage.isFinal,
        isHired: stage.isHired,
        isRejection: stage.isRejection,
        actionBehavior: inferActionBehavior(stage.name)
      }))
  }

  const systemInitialStages: DynamicStage[] = [
    { id: 'sourcing', name: 'sourcing', displayName: 'Funil', order: 0, stageType: 'active', isInitial: true, actionBehavior: 'intake' },
    { id: 'screening', name: 'screening', displayName: 'Triagem', order: 1, color: 'var(--gray-600)', stageType: 'active', isInitial: false, actionBehavior: 'screening' }
  ]
  const systemFinalStages: DynamicStage[] = [
    { id: 'hired', name: 'hired', displayName: 'Contratado', order: 900, stageType: 'final', isFinal: true, isHired: true, actionBehavior: 'conclusion_hired' },
    { id: 'rejected', name: 'rejected', displayName: 'Reprovado', order: 901, stageType: 'final', isFinal: true, isRejection: true, actionBehavior: 'conclusion_rejected' },
    { id: 'offer_declined', name: 'offer_declined', displayName: 'Proposta Recusada', order: 902, stageType: 'final', isFinal: true, actionBehavior: 'conclusion_declined' }
  ]
  const customStages: DynamicStage[] = interviewStages
    .filter(stage => {
      const slug = createStageSlug(stage.stageName)
      return !['sourcing', 'screening', 'triagem', 'hired', 'rejected', 'offer_declined'].includes(slug)
    })
    .sort((a, b) => a.order - b.order)
    .map((stage, index) => {
      const slug = createStageSlug(stage.stageName)
      return {
        id: slug,
        name: slug,
        displayName: stage.stageName,
        order: stage.order + 10,
        color: DYNAMIC_STAGE_COLORS[index % DYNAMIC_STAGE_COLORS.length],
        stageType: 'active' as const,
        isInitial: false,
        isFinal: false,
        actionBehavior: inferActionBehavior(slug, stage.type)
      }
    })
  return [...systemInitialStages, ...customStages, ...systemFinalStages].sort((a, b) => a.order - b.order)
}

// Função para organizar candidatos por etapas dinâmicas
const organizeCandidatesByDynamicStages = (
  candidates: any[],
  stages: DynamicStage[]
): Record<string, any[]> => {
  // Inicializar objeto com todas as etapas
  const organized: Record<string, any[]> = {}
  stages.forEach(stage => {
    organized[stage.id] = []
  })
  
  // Mapeamento de nomes legados para IDs de etapas
  const legacyMapping: Record<string, string> = {
    'funil': 'sourcing',
    'triagem': 'screening',
    'entrevista': 'interview_hr',
    'entrevista_rh': 'interview_hr',
    'entrevista_tecnica': 'interview_technical',
    'entrevista_gestor': 'interview_manager',
    'final': 'offer',
    'proposta': 'offer',
    'aprovados': 'hired',
    'contratado': 'hired',
    'reprovados': 'rejected',
    'reprovado': 'rejected',
    'proposta_recusada': 'offer_declined'
  }
  
  // Distribuir candidatos nas etapas
  candidates.forEach(candidate => {
    const rawStage = (candidate.stage || candidate.status || 'sourcing').toLowerCase().trim()
    let targetStageId = legacyMapping[rawStage] || rawStage
    
    // Se a etapa mapeada não existe nas etapas dinâmicas, tentar encontrar uma correspondente
    if (!organized[targetStageId]) {
      // Buscar etapa pelo displayName ou nome similar
      const matchingStage = stages.find(s => 
        s.displayName.toLowerCase() === rawStage ||
        s.name.toLowerCase() === rawStage ||
        createStageSlug(s.displayName) === createStageSlug(rawStage)
      )
      if (matchingStage) {
        targetStageId = matchingStage.id
      } else {
        // Se ainda não encontrou, colocar em sourcing (fallback)
        targetStageId = 'sourcing'
      }
    }
    
    // Garantir que a etapa existe no objeto
    if (!organized[targetStageId]) {
      organized[targetStageId] = []
    }
    
    organized[targetStageId].push({
      ...candidate,
      stage: targetStageId
    })
  })
  
  return organized
}

// Função para criar objeto candidatesData inicial baseado nas etapas dinâmicas
const createInitialCandidatesData = (stages: DynamicStage[]): Record<string, any[]> => {
  const data: Record<string, any[]> = {}
  stages.forEach(stage => {
    data[stage.id] = []
  })
  return data
}

// Mock data imported from @/components/kanban/mock/candidates
const jobData = mockJobData

export function JobKanbanPage({ job, onBack }: { job?: any, onBack?: () => void }) {
  const router = useRouter()
  const { toast } = useToast()
  const { saveJobsState } = useNavigationPersistence()
  const { user } = useAuth()
  const talentFunnel = useTalentFunnel()
  const _companyIdForSL = (user as any)?.company || 'demo'
  const _jobIdForSL = job?.id?.toString()
  const { shortLists, createShortList: _createSL, addCandidate: _addToSL, removeCandidate: _removeFromSL } = useShortList(_companyIdForSL, _jobIdForSL)
  const { insights: proactiveInsights, dismiss: dismissInsight } = useProactiveInsights(_jobIdForSL, _companyIdForSL)
  
  const { 
    suggestions: aiSuggestions, 
    approveSuggestion, 
    rejectSuggestion 
  } = useCandidateSuggestions(job?.id?.toString() || '')
  
  const pipelineInheritance = usePipelineInheritance(job?.id?.toString())

  const { events: returnEvents, getAlertForCandidate, computeAlerts, hasAlerts } = useReturnEvents({
    jobId: job?.id?.toString(),
    enabled: true,
    pollingIntervalMs: 30000,
  })

  useEffect(() => {
    if (job?.id) {
      pipelineInheritance.checkStatus()
    }
  }, [job?.id])

  const [viewMode, setViewMode] = useState<"kanban" | "table">("kanban")
  const [saturationData, setSaturationData] = useState<{ is_saturated: boolean; approved_count: number; saturation_threshold: number; saturation_percentage: number } | null>(null)

  const saturationJobId = job?.backendId || job?.id
  useEffect(() => {
    if (!saturationJobId) return
    fetch(`/api/backend-proxy/job-vacancies/${saturationJobId}/saturation-status/`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setSaturationData(data) })
      .catch(() => {})
  }, [saturationJobId])

  const [isCreationMode, setIsCreationMode] = useState(false)
  const [isPublishing, setIsPublishing] = useState(false)
  const [publicLink, setPublicLink] = useState<string | null>(null)
  const [showPublishSuccess, setShowPublishSuccess] = useState(false)

  const [activeTab, setActiveTab] = useState<"management" | "edit">("management")
  const [selectedCandidate, setSelectedCandidate] = useState<any>(null)
  const [selectedTriagemCandidate, setSelectedTriagemCandidate] = useState<any>(null)
  const [showExpandedMetrics, setShowExpandedMetrics] = useState(false)
  
  // Estado para controlar renderização apenas no cliente (evita erro de hidratação)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    if (!job?.backendId) return
    const creationJobId = localStorage.getItem("jobCreationMode")
    if (creationJobId && creationJobId === job.backendId) {
      setIsCreationMode(true)
      setActiveTab("edit")
      localStorage.removeItem("jobCreationMode")
    }
  }, [job?.backendId])

  const [jobEditForm, setJobEditForm] = useState<Record<string, any>>({})

  const handlePublishJob = useCallback(async () => {
    const vacancyId = job?.backendId
    if (!vacancyId) return

    setIsPublishing(true)
    try {
      // Auto-salva o formulário antes de publicar
      const fieldMapping: Record<string, string> = {
        title: 'title', department: 'department', location: 'location',
        workModel: 'work_model', type: 'employment_type', level: 'seniority_level',
        urgencyLevel: 'urgency_level', priority: 'priority',
        recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
        manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
        openDate: 'open_date', deadline: 'deadline',
        deadlineScreening: 'deadline_screening', deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing',
        benefits: 'benefits', description: 'description',
        targetAudience: 'target_audience', targetSector: 'target_sector',
        visibility: 'visibility', isConfidential: 'is_confidential',
        isAffirmative: 'is_affirmative', languages: 'languages',
      }
      const autoSavePayload: Record<string, any> = {}
      Object.entries(fieldMapping).forEach(([formKey, apiKey]) => {
        const val = jobEditForm[formKey]
        if (val !== undefined && val !== '' && val !== null) {
          autoSavePayload[apiKey] = val
        }
      })
      if (jobEditForm.salaryMin || jobEditForm.salaryMax) {
        autoSavePayload['salary_range'] = {
          min: jobEditForm.salaryMin ? Number(jobEditForm.salaryMin) : null,
          max: jobEditForm.salaryMax ? Number(jobEditForm.salaryMax) : null,
          currency: 'BRL',
        }
      }
      if (Object.keys(autoSavePayload).length > 0) {
        await liaApi.updateJobVacancy(vacancyId, autoSavePayload)
      }

      const linkResult = await liaApi.generatePublicLink(vacancyId)

      await liaApi.updateJobVacancy(vacancyId, { status: "Ativa" } as any)

      setPublicLink(linkResult.public_url)
      setShowPublishSuccess(true)
      setIsCreationMode(false)

      setJobEditForm((prev: any) => ({
        ...prev,
        status: "Ativa",
        public_url: linkResult.public_url,
      }))

      toast({
        title: "Vaga publicada!",
        description: "A vaga está ativa e o link de candidatura foi gerado.",
      })
    } catch (error: unknown) {
      const detail = error instanceof Error ? error.message : "Erro desconhecido"
      toast({
        title: "Erro ao publicar",
        description: `Não foi possível publicar a vaga: ${detail}`,
        variant: "destructive",
      })
    } finally {
      setIsPublishing(false)
    }
  }, [job?.backendId, jobEditForm, toast])

  // Persistência de navegação - salva estado quando muda
  useEffect(() => {
    if (job?.id) {
      saveJobsState(String(job.id), viewMode, activeTab)
    }
  }, [job?.id, viewMode, activeTab, saveJobsState])

  // Estados para etapas dinâmicas do Kanban
  const [dynamicStages, setDynamicStages] = useState<DynamicStage[]>(() =>
    mapInterviewStagesToKanban(job?.interviewStages)
  )

  // Enriquece as etapas com sub-statuses ativos do pipeline da empresa (fonte: DB)
  const { stages: companyPipelineStages } = useRecruitmentStages()
  useEffect(() => {
    if (!companyPipelineStages.length) return
    const subStatusMap = buildSubStatusMap(
      companyPipelineStages.map(s => ({
        name: s.name,
        sub_statuses: (s.sub_statuses || []).map(ss => ({
          name: ss.name,
          display_name: ss.display_name,
          is_default: ss.is_default,
          is_waiting: ss.is_waiting,
          waiting_for: ss.waiting_for,
        })),
      }))
    )
    setDynamicStages(prev => enrichStagesWithSubStatuses(prev, subStatusMap))
  }, [companyPipelineStages])

  const [showAddColumnPopover, setShowAddColumnPopover] = useState(false)
  const [newColumnName, setNewColumnName] = useState("")
  const [inferredBehavior, setInferredBehavior] = useState<{suggested_behavior: string, confidence: number} | null>(null)
  const [isAddingColumn, setIsAddingColumn] = useState(false)
  
  const { modalState: universalModalState, openTransition, closeTransition } = useUniversalTransition(dynamicStages)

  const handleTransitionRequired = useCallback((
    candidates: KanbanCandidate[],
    fromStage: string,
    toStage: string
  ) => {
    const isFromInterview = (fromStage || '').toLowerCase().includes('interview') || (fromStage || '').toLowerCase().includes('entrevista')
    const candidateWithInterview = candidates.find(c => c.agendada)

    if (isFromInterview && candidateWithInterview) {
      const c = candidateWithInterview
      const dateStr = c.interviewDate || new Date(c.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
      setTransitionInitialPrompt(
        `O recrutador está movendo ${c.name} da etapa de entrevista. Este candidato tem uma entrevista agendada para ${dateStr}. Isso significa cancelar a entrevista? Ou prefere alterar o horário e mantê-lo na entrevista? Pergunte e aguarde a resposta do recrutador.`
      )
      setTransitionAllowStageSelection(true)
      setTransitionInterviewAlert({ name: c.name, date: dateStr })
    }

    openTransition(candidates, fromStage, toStage)
  }, [openTransition])

  const handleUniversalTransitionConfirm = useCallback(async (data: UniversalTransitionConfirmData) => {
    try {
      const dispatchSummary: { sent: number; failed: number; channel?: string; mock?: boolean; aiPersonalized?: boolean } = { sent: 0, failed: 0 }

      for (const candidateId of data.candidateIds) {
        const candidateSubStatus = data.perCandidateSubStatus?.[candidateId] || data.subStatus

        const response = await fetch('/api/backend-proxy/transition/execute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vacancy_candidate_id: candidateId,
            to_stage: data.toStage,
            sub_status: candidateSubStatus,
            action: data.action,
            prompt: data.prompt,
            channel: data.channel || 'email',
            action_behavior: data.actionBehavior || universalModalState.actionBehavior,
            extracted_preferences: data.extracted_preferences || undefined,
          })
        })

        const result = await response.json()

        if (result.dispatch_results?.length) {
          for (const dr of result.dispatch_results) {
            if (dr.success) {
              dispatchSummary.sent++
              dispatchSummary.channel = dr.channel
              dispatchSummary.mock = dr.mock
              if (dr.ai_personalized) {
                dispatchSummary.aiPersonalized = true
              }
            } else {
              dispatchSummary.failed++
            }
          }
        }

        setCandidatesData(prev => {
          const newData = { ...prev }
          for (const key of Object.keys(newData)) {
            newData[key] = (newData[key] as any[]).filter((c: any) => c.id !== candidateId)
          }
          if (!newData[data.toStage]) {
            newData[data.toStage] = []
          }
          const existingCandidate = Object.values(prev).flat().find((c: any) => c.id === candidateId)
          const movedCandidate = {
            ...existingCandidate,
            id: candidateId,
            name: existingCandidate?.name || (data.candidateIds.length === 1 ? (universalModalState.candidates[0]?.name || '') : ''),
            stage: data.toStage,
            sub_status: data.perCandidateSubStatus?.[candidateId] || data.subStatus,
            stageId: data.toStage,
            actionBehavior: data.actionBehavior || universalModalState.actionBehavior,
            needsAction: data.action !== 'just_move',
          }
          newData[data.toStage] = [...newData[data.toStage], movedCandidate]
          return newData
        })
      }
      closeTransition()

      if (dispatchSummary.sent > 0) {
        const channelLabel = dispatchSummary.channel === 'whatsapp' ? 'WhatsApp' : 'e-mail'
        const mockNote = dispatchSummary.mock ? ' (modo simulação)' : ''
        const aiNote = dispatchSummary.aiPersonalized ? ' (personalizada por IA)' : ''
        toast({
          title: 'Transição realizada com envio automático',
          description: `${data.candidateIds.length} candidato(s) movido(s). ${dispatchSummary.sent} ${channelLabel}(s) enviado(s)${aiNote}${mockNote}.${dispatchSummary.failed > 0 ? ` ${dispatchSummary.failed} falha(s).` : ''}`,
        })
      } else {
        toast({
          title: 'Transição realizada',
          description: `${data.candidateIds.length} candidato(s) movido(s) com sucesso.`,
        })
      }
    } catch (error) {
      toast({
        title: 'Erro na transição',
        description: 'Não foi possível completar a transição.',
        variant: 'destructive'
      })
    }
  }, [closeTransition, toast, universalModalState.candidates])

  const handleOpenSpecializedModal = useCallback((modalType: string, context: any) => {
    switch (modalType) {
      case 'wsi-triagem-invite':
        if (context.candidates?.length > 0) {
          setWsiInviteCandidate(context.candidates[0])
          setShowWSIInviteModal(true)
        }
        break
      case 'scheduling':
        if (context.candidates?.length > 0) {
          setUnifiedModalCandidate(context.candidates[0])
          setUnifiedModalType('agendamento')
          setUnifiedModalSituation('agendamento')
          setUnifiedModalOpen(true)
        }
        break
      case 'data-request':
        if (context.candidates?.length > 0) {
          setDataRequestModalCandidate(context.candidates[0])
          setShowDataRequestModal(true)
        }
        break
      case 'decision-flow':
        if (context.candidates?.length > 0) {
          const candidate = context.candidates[0]
          setDecisionFlowCandidate(candidate)
          setDecisionFlowType(context.toStage === 'hired' ? 'confirm_hire' : 'reject_pre_triage')
          setShowDecisionFlowModal(true)
        }
        break
      case 'rejection-feedback':
        if (context.candidates?.length > 0) {
          setUnifiedModalCandidate(context.candidates[0])
          setUnifiedModalType('feedback')
          setUnifiedModalSituation('feedback_construtivo')
          setUnifiedModalOpen(true)
        }
        break
      case 'evaluation-send':
        if (context.candidates?.length > 0) {
          setUnifiedModalCandidate(context.candidates[0])
          setUnifiedModalType('email')
          setUnifiedModalSituation('avaliacao_tecnica')
          setUnifiedModalOpen(true)
        }
        break
      case 'offer-send':
        if (context.candidates?.length > 0) {
          setUnifiedModalCandidate(context.candidates[0])
          setUnifiedModalType('email')
          setUnifiedModalSituation('proposta')
          setUnifiedModalOpen(true)
        }
        break
      default:
    }
    closeTransition()
  }, [closeTransition])

  // Estados para drag and drop
  const [draggedCandidate, setDraggedCandidate] = useState<any>(null)
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)
  const [candidatesData, setCandidatesData] = useState<Record<string, any[]>>(() => 
    createInitialCandidatesData(mapInterviewStagesToKanban(job?.interviewStages))
  )
  const [isLoadingCandidates, setIsLoadingCandidates] = useState(true)
  const [hasMounted, setHasMounted] = useState(false)
  const pendingNavigationRef = useRef<{ nav: { candidateId?: string; candidateName?: string; jobId?: string; jobTitle?: string; currentStage?: string; action?: string; openTransitionModal?: boolean }; prompt: string | null } | null>(null)

  // Estado para DataRequestModal
  const [showDataRequestModal, setShowDataRequestModal] = useState(false)
  const [dataRequestModalCandidate, setDataRequestModalCandidate] = useState<any>(null)

  // Estado para seleção múltipla (moved before callbacks that use it)
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())

  // Todos os candidatos da tabela (moved before callbacks that use it)
  const allTableCandidates = useMemo(() => {
    return dynamicStages.reduce((acc: any[], stage) => {
      const stageCandidates = candidatesData[stage.id] || []
      return [...acc, ...stageCandidates]
    }, [])
  }, [dynamicStages, candidatesData])

  // Extract all candidate IDs for bulk data request fetching
  const allCandidateIds = useMemo(() => {
    return Object.values(candidatesData).flat().map((c: any) => c.id).filter(Boolean)
  }, [candidatesData])

  // Fetch data requests for all visible candidates
  const { 
    getDataRequestForCandidate,
    mutate: mutateDataRequests 
  } = useBulkCandidateDataRequests({
    candidateIds: allCandidateIds,
    vacancyId: job?.id?.toString(),
    enabled: allCandidateIds.length > 0,
  })

  // Handlers para DataRequestIndicator
  const handleDataRequestResend = useCallback((candidateId: string) => {
    const candidate = Object.values(candidatesData)
      .flat()
      .find((c: any) => c.id === candidateId)
    
    if (candidate) {
      setDataRequestModalCandidate(candidate)
      setShowDataRequestModal(true)
      toast({
        title: "Reenviar Solicitação",
        description: `Preparando reenvio de solicitação para ${candidate.name}`,
      })
    }
  }, [candidatesData, toast])

  const handleDataRequestViewDetails = useCallback((candidateId: string) => {
    const candidate = Object.values(candidatesData)
      .flat()
      .find((c: any) => c.id === candidateId)
    
    if (candidate) {
      setSelectedCandidate(candidate)
      toast({
        title: "Detalhes da Solicitação",
        description: `Visualizando detalhes de ${candidate.name}`,
      })
    }
  }, [candidatesData, toast])

  const handleDataRequestSubmit = useCallback(async (data: DataRequestSubmitData) => {
    toast({
      title: "Solicitação Enviada",
      description: `Solicitação de dados enviada para ${dataRequestModalCandidate?.name || 'candidato'}`,
    })
    setShowDataRequestModal(false)
    setDataRequestModalCandidate(null)
  }, [dataRequestModalCandidate, toast])

  // Marcar como cliente para evitar problemas de hidratação SSR
  useEffect(() => {
    setIsClient(true)
    setHasMounted(true)
  }, [])

  // Atualizar etapas dinâmicas quando job.interviewStages mudar
  useEffect(() => {
    const newStages = mapInterviewStagesToKanban(job?.interviewStages)
    setDynamicStages(newStages)
    
    // Atualizar candidatesData para incluir novas etapas
    setCandidatesData(prev => {
      const newData = createInitialCandidatesData(newStages)
      // Preservar candidatos existentes e redistribuir para etapas compatíveis
      Object.keys(prev).forEach(stageId => {
        const candidates = prev[stageId] || []
        if (newData[stageId]) {
          newData[stageId] = [...candidates]
        } else {
          // Se a etapa antiga não existe mais, mover para sourcing
          newData['sourcing'] = [...(newData['sourcing'] || []), ...candidates]
        }
      })
      return newData
    })
  }, [job?.interviewStages])

  // Carregar candidatos reais do backend
  useEffect(() => {
    setIsLoadingCandidates(true)
    liaApi.listCandidates(undefined, undefined, 0, 200)
      .then(response => {
        try {
          if (response.items && response.items.length > 0) {
            const mapCandidateToKanban = (c: CandidateLocal, index: number) => {
              try {
                const experience = c.years_of_experience || ((index % 12) + 1)
                const monthlySalary = c.current_salary || getSalaryByExperience(experience, index)
                const location = c.location_city && c.location_state 
                  ? `${c.location_city}, ${c.location_state}`
                  : c.location_city || 'Não especificado'
                
                let educationData: any[] = []
                let workHistoryData: any[] = []
                
                try {
                  educationData = generateEducation(c, experience)
                } catch (e) {
                  educationData = []
                }
                
                try {
                  workHistoryData = generateWorkHistory(c, experience)
                } catch (e) {
                  workHistoryData = []
                }
                
                const rawStatus = (c.status || 'novo').toLowerCase()
                let mappedStage = 'funil'
                if (rawStatus === 'reprovado' || rawStatus === 'rejected' || rawStatus === 'descartado' || rawStatus === 'reprovados') {
                  mappedStage = 'reprovados'
                } else if (rawStatus === 'aprovado' || rawStatus === 'hired' || rawStatus === 'contratado' || rawStatus === 'aprovados') {
                  mappedStage = 'aprovados'
                } else if (rawStatus === 'final' || rawStatus === 'proposta' || rawStatus === 'offer') {
                  mappedStage = 'final'
                } else if (rawStatus === 'entrevista' || rawStatus === 'interview' || rawStatus === 'entrevistando') {
                  mappedStage = 'entrevista'
                } else if (rawStatus === 'triagem' || rawStatus === 'screening' || rawStatus === 'em_triagem') {
                  mappedStage = 'triagem'
                }

                return {
                  id: c.id,
                  name: c.name || 'Sem nome',
                  role: c.current_title || 'Não especificado',
                  currentCompany: c.current_company || '',
                  location: location,
                  score: c.lia_score || null,
                  fitScore: c.skills_match_percentage || Math.floor(70 + seededRandom(c.id || String(index), 1) * 25),
                  warnings: 0,
                  avatar: c.avatar_url || '',
                  source: c.source || 'website',
                  appliedDate: c.created_at ? new Date(c.created_at).toLocaleDateString('pt-BR') : 'Hoje',
                  email: c.email || '',
                  phone: c.phone || '',
                  linkedin: c.linkedin_url || '',
                  experience: `${experience} anos`,
                  stage: mappedStage,
                  etapa: mappedStage,
                  education: educationData,
                  skills: c.technical_skills || [],
                  languages: Array.isArray(c.languages) 
                    ? c.languages.map((l: any) => typeof l === 'string' ? l : l.language)
                    : Object.keys(c.languages || {}),
                  expectedSalary: c.desired_salary_max 
                    ? `R$ ${c.desired_salary_max.toLocaleString('pt-BR')}`
                    : `R$ ${Math.floor(monthlySalary * 1.2).toLocaleString('pt-BR')}`,
                  currentSalary: `R$ ${monthlySalary.toLocaleString('pt-BR')}`,
                  contractType: c.contract_type_preference || 'CLT',
                  workModel: c.work_model_preference || 'híbrido',
                  availability: 'A confirmar',
                  portfolio: c.portfolio_url || '',
                  github: c.github_url || '',
                  workHistory: workHistoryData,
                  bigFive: {
                    openness: 70 + Math.floor(seededRandom(c.id || String(index), 10) * 20),
                    conscientiousness: 70 + Math.floor(seededRandom(c.id || String(index), 11) * 20),
                    extraversion: 60 + Math.floor(seededRandom(c.id || String(index), 12) * 25),
                    agreeableness: 70 + Math.floor(seededRandom(c.id || String(index), 13) * 20),
                    neuroticism: 25 + Math.floor(seededRandom(c.id || String(index), 14) * 25)
                  },
                  notes: c.notes || '',
                  liaAnalysis: {
                    score: c.lia_score || 75,
                    strengths: c.lia_insights?.strengths || ['Perfil técnico sólido'],
                    concerns: c.lia_insights?.concerns || [],
                    recommendation: c.lia_insights?.recommendation || 'Avaliar com atenção'
                  },
                  status: c.status || 'novo'
                }
              } catch (mapError) {
                return null
              }
            }

            const backendCandidates = response.items
              .map(mapCandidateToKanban)
              .filter((c): c is NonNullable<typeof c> => c !== null)
            
            
            // Usar etapas dinâmicas da vaga para organizar candidatos
            const currentDynamicStages = mapInterviewStagesToKanban(job?.interviewStages)
            const newOrganizedData: Record<string, any[]> = {}
            
            // Inicializar todas as etapas dinâmicas com arrays vazios
            currentDynamicStages.forEach(stage => {
              newOrganizedData[stage.id] = []
            })

            // Função para encontrar a melhor etapa para um candidato
            const findBestStageForCandidate = (rawStatus: string, mappedStage: string): string => {
              // Etapas sistema sempre existem
              if (mappedStage === 'rejected' || rawStatus === 'reprovado' || rawStatus === 'descartado') return 'rejected'
              if (mappedStage === 'offer_declined' || rawStatus === 'proposta_recusada') return 'offer_declined'
              if (mappedStage === 'hired' || rawStatus === 'aprovado' || rawStatus === 'contratado') return 'hired'
              
              // Buscar correspondência nas etapas dinâmicas
              const stageExists = (id: string) => currentDynamicStages.some(s => s.id === id)
              
              if ((mappedStage === 'offer' || rawStatus === 'final' || rawStatus === 'proposta') && stageExists('offer')) return 'offer'
              if ((rawStatus === 'interview_manager' || rawStatus === 'entrevista_gestor') && stageExists('interview_manager')) return 'interview_manager'
              if ((rawStatus === 'interview_technical' || rawStatus === 'entrevista_tecnica') && stageExists('interview_technical')) return 'interview_technical'
              if ((mappedStage === 'interview_hr' || rawStatus === 'entrevista' || rawStatus === 'interview' || rawStatus === 'entrevistando') && stageExists('interview_hr')) return 'interview_hr'
              if ((mappedStage === 'screening' || rawStatus === 'triagem' || rawStatus === 'em_triagem' || rawStatus === 'triado' || rawStatus === 'triado_aprovado') && stageExists('screening')) return 'screening'
              
              // Tentar encontrar etapa personalizada por nome similar
              const normalizedStatus = rawStatus.replace(/_/g, ' ').toLowerCase()
              const customStage = currentDynamicStages.find(s => 
                s.name.toLowerCase().includes(normalizedStatus) || 
                s.displayName.toLowerCase().includes(normalizedStatus) ||
                normalizedStatus.includes(s.name.toLowerCase())
              )
              if (customStage) return customStage.id
              
              // Fallback para sourcing
              return 'sourcing'
            }

            backendCandidates.forEach((candidate) => {
              const rawStatus = (candidate.status || 'novo').toLowerCase()
              const mappedStage = mapLegacyStage(rawStatus)
              const targetStage = findBestStageForCandidate(rawStatus, mappedStage)
              
              // Determinar se precisa de ação baseado na etapa
              const needsAction = ['sourcing', 'screening'].includes(targetStage)
              
              // Adicionar detalhes extras para etapas de entrevista
              let extraData = {}
              if (targetStage.startsWith('interview')) {
                const idx = (newOrganizedData[targetStage] || []).length
                const isScheduled = idx % 2 === 0
                extraData = {
                  agendada: isScheduled ? new Date(Date.now() + (idx + 1) * 24 * 60 * 60 * 1000).toISOString() : undefined,
                  interviewDate: isScheduled ? (idx === 0 ? 'Hoje às 14h' : `${idx + 1} dias às 10h`) : undefined,
                  typeOfInterview: isScheduled ? 'Teams' : undefined,
                  teamsLink: isScheduled ? 'https://teams.microsoft.com/l/meetup-join/19%3ameeting_demo123' : undefined,
                  interviewer: isScheduled ? 'Maria Silva - Head de P&C' : undefined
                }
              }
              
              if (newOrganizedData[targetStage]) {
                newOrganizedData[targetStage].push({ 
                  ...candidate, 
                  needsAction, 
                  stage: targetStage, 
                  sub_status: (candidate as any).sub_status || 'pending',
                  ...extraData
                })
              } else {
                // Fallback se a etapa não existe
                newOrganizedData['sourcing'] = newOrganizedData['sourcing'] || []
                newOrganizedData['sourcing'].push({ ...candidate, needsAction: true, stage: 'sourcing', sub_status: 'identified' })
              }
            })

            // Log com contagem dinâmica
            const stageCounts: Record<string, number> = {}
            currentDynamicStages.forEach(stage => {
              stageCounts[stage.displayName] = (newOrganizedData[stage.id] || []).length
            })
            setCandidatesData(newOrganizedData)
          } else {
          }
        } catch (processError) {
        } finally {
          setIsLoadingCandidates(false)
        }
      })
      .catch(error => {
        setIsLoadingCandidates(false)
      })
  }, [])

  // Estado para busca
  const [searchQuery, setSearchQuery] = useState("")

  // Estados para modais
  const [previewCandidate, setPreviewCandidate] = useState<any>(null)
  const [isPreviewOpen, setIsPreviewOpen] = useState(false)
  const [showCandidatePage, setShowCandidatePage] = useState(false)
  const [triagemCandidate, setTriagemCandidate] = useState<any>(null)
  const [showReport, setShowReport] = useState(false)
  const [isTriagemOpen, setIsTriagemOpen] = useState(false)
  const [showTestPreview, setShowTestPreview] = useState(false)
  const [editingQuestion, setEditingQuestion] = useState<number | null>(null)
  const [showLiaSuggestions, setShowLiaSuggestions] = useState(false)
  const [liaSuggestionsData, setLiaSuggestionsData] = useState<Array<{type: string; severity: string; candidate_id: string; candidate_name: string; message: string; suggested_action: string; stage: string}>>([])
  const [showLiaSuggestionsPanel, setShowLiaSuggestionsPanel] = useState(true)
  const [showExpandedLIA, setShowExpandedLIA] = useState(false) // Modal expandido da LIA
  const [transitionInitialPrompt, setTransitionInitialPrompt] = useState<string | undefined>(undefined)
  const [transitionAllowStageSelection, setTransitionAllowStageSelection] = useState(false)
  const [transitionInterviewAlert, setTransitionInterviewAlert] = useState<{ name: string; date: string } | null>(null)
  const [showSuperChat, setShowSuperChat] = useState(false) // Super chat expandido (ocupa mais espaço)
  const [liaPromptValue, setLiaPromptValue] = useState("") // Valor do prompt da LIA
  const [liaMessages, setLiaMessages] = useState<{id: string; type: 'user' | 'response'; content: string; timestamp: number; metadata?: Record<string, unknown>}[]>([]) // Mensagens do chat LIA
  const [isLiaLoading, setIsLiaLoading] = useState(false) // Estado de loading da LIA
  const [liaConversationId, setLiaConversationId] = useState<string | undefined>(undefined)
  const chatScrollRef = useRef<HTMLDivElement>(null) // Ref para auto-scroll do chat
  const [liaSearchQuery, setLiaSearchQuery] = useState("") // Busca de consultas LIA
  const [userCollapsedLIA, setUserCollapsedLIA] = useState(false) // Se usuário fechou manualmente
  const [liaExpandedWidth, setLiaExpandedWidth] = useState(400) // Largura do prompt expandido (mín: 280, máx: 520)
  const [isResizingLIA, setIsResizingLIA] = useState(false) // Controle de redimensionamento
  
  // Função para abrir o Super Chat expandido
  const openSuperChat = useCallback((initialMessage?: string) => {
    setShowExpandedLIA(false)
    setShowSuperChat(true)
    if (initialMessage) {
      setLiaPromptValue(initialMessage)
    }
  }, [])
  
  // Função para voltar ao prompt expandido lateral
  const returnToExpandedPrompt = useCallback(() => {
    setShowSuperChat(false)
    setShowExpandedLIA(true)
  }, [])
  const [showTestLibrary, setShowTestLibrary] = useState(false)
  const [showTestHistory, setShowTestHistory] = useState(false)
  const [selectedTestForHistory, setSelectedTestForHistory] = useState<any>(null)
  const [showConceptualPrompt, setShowConceptualPrompt] = useState(false)
  const [isEditModeTriagem, setIsEditModeTriagem] = useState(false)
  const [showConceptualPromptTriagem, setShowConceptualPromptTriagem] = useState(false)
  const [showApresentacaoPrompt, setShowApresentacaoPrompt] = useState(false)
  const [showFechamentoPrompt, setShowFechamentoPrompt] = useState(false)
  const [isEditMode, setIsEditMode] = useState(false) // Novo estado para modo de edição
  const [showTriagemSuggestions, setShowTriagemSuggestions] = useState(false) // Painel de sugestões para triagem
  const [selectedTriagemQuestion, setSelectedTriagemQuestion] = useState<string | null>(null) // Pergunta selecionada
  const [expandedCronograma, setExpandedCronograma] = useState(false) // Estado para expandir cronograma
  const [expandedTesteTecnico, setExpandedTesteTecnico] = useState(false) // Estado para expandir teste técnico
  const [expandedTesteIngles, setExpandedTesteIngles] = useState(false) // Estado para expandir teste de inglês
  const [expandedRoteiro, setExpandedRoteiro] = useState(false) // Estado para expandir roteiro de triagem
  
  // Estados para modal de email
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [emailCandidate, setEmailCandidate] = useState<any>(null)

  // Estado para modal Compartilhar com Gestor (H.3a)
  const [showShareGestorModal, setShowShareGestorModal] = useState(false)

  // Estados para Unified Communication Modal
  const [unifiedModalOpen, setUnifiedModalOpen] = useState(false)
  const [unifiedModalType, setUnifiedModalType] = useState<CommunicationType>('email')
  const [unifiedModalCandidate, setUnifiedModalCandidate] = useState<any>(null)
  const [unifiedModalSituation, setUnifiedModalSituation] = useState<string | undefined>(undefined)

  // Estados para WSI Text Screening Modal
  const [showWSIModal, setShowWSIModal] = useState(false)
  const [wsiCandidate, setWsiCandidate] = useState<any>(null)

  // Estados para WSI Triagem Invite Modal
  const [showWSIInviteModal, setShowWSIInviteModal] = useState(false)
  const [wsiInviteCandidate, setWsiInviteCandidate] = useState<any>(null)

  // Estados para Add to Vacancy Modal
  const [showAddToVacancyModal, setShowAddToVacancyModal] = useState(false)
  const [candidateForVacancy, setCandidateForVacancy] = useState<any>(null)

  // Estados para Rubric Evaluation Modal
  const [showRubricModal, setShowRubricModal] = useState(false)
  const [rubricCandidate, setRubricCandidate] = useState<any>(null)
  const [rubricEvaluationData, setRubricEvaluationData] = useState<any>(null)

  // Estados para modais de avaliação da tabela
  const [selectedCandidateForModal, setSelectedCandidateForModal] = useState<any>(null)
  const [activeModal, setActiveModal] = useState<'notaGeral' | 'triagem' | 'testeTecnico' | 'testeIngles' | null>(null)
  const [showBigFiveModal, setShowBigFiveModal] = useState(false)

  // Estados para modais de scores (dos cards do Kanban)
  const [showGeneralScoreModal, setShowGeneralScoreModal] = useState(false)
  const [showTechnicalTestModal, setShowTechnicalTestModal] = useState(false)
  const [showEnglishTestModal, setShowEnglishTestModal] = useState(false)
  const [scoreModalCandidate, setScoreModalCandidate] = useState<any>(null)

  // D9 — Estado para modal de comparação de candidatos
  const [showCompareModal, setShowCompareModal] = useState(false)
  const [compareCandidates, setCompareCandidates] = useState<{ id: string; name: string }[]>([])
  const [selectedForCompare, setSelectedForCompare] = useState<Set<string>>(new Set())

  // Estados para modal de fluxo de decisão (aprovar/reprovar)
  const [showDecisionFlowModal, setShowDecisionFlowModal] = useState(false)
  const [decisionFlowCandidate, setDecisionFlowCandidate] = useState<any>(null)
  const [decisionFlowType, setDecisionFlowType] = useState<'approve_to_triage' | 'approve_to_interview' | 'reject_pre_triage' | 'reject_post_triage' | 'request_urgency' | 'reschedule_interview' | 'confirm_hire'>('approve_to_triage')

  // Estados para modal de seleção de status (movimentação no Kanban)
  const [pendingMove, setPendingMove] = useState<{
    candidate: any;
    fromColumn: string;
    toColumn: string;
  } | null>(null)
  const [statusModalOpen, setStatusModalOpen] = useState(false)
  const [selectedSubStatus, setSelectedSubStatus] = useState<string>('')

  // Estados para JobStatusModal (pausar/reativar) e CloseVacancyModal (fechar vaga)
  const [showJobStatusModal, setShowJobStatusModal] = useState(false)
  const [jobStatusModalMode, setJobStatusModalMode] = useState<'pause' | 'activate'>('pause')
  const [showCloseVacancyModal, setShowCloseVacancyModal] = useState(false)


  // Estados para gerenciar perguntas e habilidades dinamicamente
  const [perguntasEliminatorias, setPerguntasEliminatorias] = useState([
    '1️⃣ Você está aberto(a) a novas oportunidades no momento? (opções: Sim / Não)',
    '2️⃣ Você tem disponibilidade para o modelo de trabalho [modelo da vaga]? (opções: Sim / Não)'
  ])
  const [perguntasInformativas, setPerguntasInformativas] = useState([
    '3️⃣ Qual sua disponibilidade para início, caso avance no processo? (opções: Imediata / Até 30 dias / Acima de 30 dias)',
    '4️⃣ Qual sua expectativa salarial para contratação CLT? (resposta aberta)'
  ])
  const [habilidadesTecnicas, setHabilidadesTecnicas] = useState([
    'Design System',
    'Prototipagem Figma',
    'User Research',
    'Testes de Usabilidade',
    'Metodologias Ágeis',
    'Métricas de UX'
  ])

  const [perguntasTecnicasAvaliacao, setPerguntasTecnicasAvaliacao] = useState([
    '1️⃣ De 1 a 5, como você avalia seu domínio em **[Skill 1]**? (1 = iniciante / 5 = especialista)',
    '2️⃣ Conte brevemente sobre um projeto em que aplicou **[Skill 2]**. (Pode responder em poucas frases; quero entender seu papel e resultados.)',
    '3️⃣ Como você costuma validar seus resultados ao trabalhar com **[Skill 3]**?',
    '4️⃣ Qual foi o principal desafio técnico que enfrentou em **[Skill 4]** e como resolveu?',
    '5️⃣ Quando você redesenha uma interface, quais **métricas** usa para avaliar se ela teve sucesso?'
  ])

  const [skillWeights, setSkillWeights] = useState([
    { skill: 'Design System', weight: 25, avgScore: 4.3, classification: 'Alto', validationType: 'Contexto real + microteste' },
    { skill: 'Prototipagem (Figma)', weight: 25, avgScore: 4.8, classification: 'Excelente', validationType: 'Microcase prático' },
    { skill: 'User Research', weight: 20, avgScore: 3.9, classification: 'Médio', validationType: 'Situação contextual' },
    { skill: 'Testes de Usabilidade', weight: 15, avgScore: 4.1, classification: 'Alto', validationType: 'Autodeclaração + microteste' },
    { skill: 'Métricas de UX', weight: 15, avgScore: 4.0, classification: 'Alto', validationType: 'Pergunta teórica' }
  ])

  // Valores originais definidos pela LIA (para restauração)
  const [originalSkillWeights] = useState([
    { skill: 'Design System', weight: 25, avgScore: 4.3, classification: 'Alto', validationType: 'Contexto real + microteste' },
    { skill: 'Prototipagem (Figma)', weight: 25, avgScore: 4.8, classification: 'Excelente', validationType: 'Microcase prático' },
    { skill: 'User Research', weight: 20, avgScore: 3.9, classification: 'Médio', validationType: 'Situação contextual' },
    { skill: 'Testes de Usabilidade', weight: 15, avgScore: 4.1, classification: 'Alto', validationType: 'Autodeclaração + microteste' },
    { skill: 'Métricas de UX', weight: 15, avgScore: 4.0, classification: 'Alto', validationType: 'Pergunta teórica' }
  ])

  // Estado para rastrear se os pesos foram modificados manualmente
  const [isSkillWeightsModified, setIsSkillWeightsModified] = useState(false)

  const [perguntasSituacionais, setPerguntasSituacionais] = useState([
    '1️⃣ Como você lida com **feedbacks críticos** sobre seu trabalho?',
    '2️⃣ Conte sobre uma situação em que precisou **defender uma decisão técnica ou de design**.',
    '3️⃣ Quando há **demandas conflitantes** entre diferentes áreas, como você prioriza?'
  ])

  // Estados para modais de ações em massa
  const [showAddToListModal, setShowAddToListModal] = useState(false)
  const [isAddingToList, setIsAddingToList] = useState(false)
  
  // Estados para bulk action modal
  const [showBulkActionModal, setShowBulkActionModal] = useState(false)
  const [bulkActionType, setBulkActionType] = useState<BulkActionType>('move_stage')

  const { handleBulkAction, handleBulkActionExecute } = useKanbanBulkActions({
    selectedCandidates,
    setSelectedCandidates,
    allTableCandidates,
    toast,
    setBulkActionType,
    setShowBulkActionModal,
    setDataRequestModalCandidate,
    setShowDataRequestModal,
    setUnifiedModalType,
    setUnifiedModalCandidate,
    setUnifiedModalOpen,
    setWsiInviteCandidate,
    setShowWSIInviteModal,
    setShowShareGestorModal,
    setCandidatesData,
  })

  // Preview Maximize State
  const [isPreviewMaximized, setIsPreviewMaximized] = useState(false)

  // Favorites State  
  const [favoriteCandidates, setFavoriteCandidates] = useState<Set<string>>(new Set())
  const [shortListedCandidateIds, setShortListedCandidateIds] = useState<Set<string>>(new Set())
  const [activeShortListId, setActiveShortListId] = useState<string | null>(null)

  // Viewed Candidates State
  const [viewedCandidateIds, setViewedCandidateIds] = useState<Set<string>>(new Set())

  // Sync favorites from useTalentFunnel hook
  useEffect(() => {
    const favoriteIds = talentFunnel.getFavoriteIds()
    setFavoriteCandidates(favoriteIds)
  }, [talentFunnel.favorites])

  // Load viewed candidates on mount
  useEffect(() => {
    const loadViewedCandidates = async () => {
      try {
        const response = await fetch('/api/backend-proxy/candidates/viewed')
        if (response.ok) {
          const data = await response.json()
          const viewedIds = new Set<string>(data.viewed_candidate_ids || data.viewedCandidateIds || [])
          setViewedCandidateIds(viewedIds)
        }
      } catch (error) {
      }
    }
    loadViewedCandidates()
  }, [])

  // Handler para redimensionar prompt expandido da LIA
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingLIA) return
      const newWidth = Math.max(280, Math.min(480, e.clientX - 16))
      setLiaExpandedWidth(newWidth)
    }
    const handleMouseUp = () => {
      setIsResizingLIA(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    if (isResizingLIA) {
      document.body.style.cursor = 'ew-resize'
      document.body.style.userSelect = 'none'
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizingLIA])

  // Detectar ação pendente de comunicação (despublicação com notificação)
  useEffect(() => {
    const pendingAction = localStorage.getItem('pendingCommunicationAction')
    if (pendingAction) {
      try {
        const action = JSON.parse(pendingAction) as {
          jobId: string
          template?: string
          candidateIds?: string[]
          channel?: 'email' | 'whatsapp'
        }
        if (action.jobId && String(action.jobId) === String(job?.id)) {
          localStorage.removeItem('pendingCommunicationAction')
          
          setTimeout(() => {
            const candidateCount = action.candidateIds?.length || 0
            const channelType = action.channel === 'whatsapp' ? 'whatsapp' : 'email'
            
            setUnifiedModalCandidate(null)
            setUnifiedModalType(channelType)
            setUnifiedModalOpen(true)
            
            if (candidateCount > 0) {
              toast({
                title: `Modal de comunicação aberto`,
                description: `${candidateCount} candidato(s) prontos para notificação via ${channelType === 'whatsapp' ? 'WhatsApp' : 'E-mail'}.`
              })
            }
          }, 500)
        }
      } catch (e) {
        localStorage.removeItem('pendingCommunicationAction')
      }
    }
  }, [job?.id, toast])

  const processPendingNavigation = useCallback(() => {
    if (!pendingNavigationRef.current) return false
    const allCands = Object.values(candidatesData).flat()
    if (allCands.length === 0) return false

    const { nav, prompt } = pendingNavigationRef.current
    pendingNavigationRef.current = null

    const matched = allCands.find(
      (c: any) =>
        (nav.candidateId && String(c.id) === String(nav.candidateId)) ||
        (nav.candidateName && c.name === nav.candidateName)
    )

    if (nav.openTransitionModal) {
      if (matched) {
        const candidateStage = Object.entries(candidatesData).find(
          ([, cands]) => (cands as any[]).some((c: any) => c.id === matched.id)
        )

        let fromStage = candidateStage?.[0] || nav.currentStage || ''
        let toStage = fromStage

        if (nav.action === 'reschedule' || nav.action === 'cancel') {
          const interviewSlugMap: Record<string, string> = {
            'technical': 'interview_hr',
            'behavioral': 'interview_hr',
            'cultural': 'interview_hr',
            'final': 'interview_final',
          }
          const interviewStageId = interviewSlugMap[(nav as any).interviewType] || 'interview_hr'
          const matchedStage = dynamicStages.find(s => s.id === interviewStageId || s.actionBehavior === 'scheduling')
          if (matchedStage) {
            fromStage = matchedStage.id
            toStage = matchedStage.id
          }
        }

        const kanbanCandidate: KanbanCandidate = {
          id: matched.id,
          name: matched.name,
          email: (matched as any).email,
          phone: (matched as any).phone,
          avatar: (matched as any).avatar,
          role: (matched as any).role || (matched as any).currentTitle,
          currentTitle: (matched as any).currentTitle,
          currentCompany: (matched as any).currentCompany || (matched as any).company,
          location: (matched as any).location,
          stage: fromStage,
          sub_status: (matched as any).sub_status,
          stageId: fromStage,
        }

        if (prompt) {
          setTransitionInitialPrompt(prompt)
        }
        if (nav.action === 'cancel' || nav.action === 'reschedule') {
          setTransitionAllowStageSelection(true)
        }
        openTransition([kanbanCandidate], fromStage, toStage)
      }
    } else {
      if (prompt) {
        setLiaPromptValue(prompt)
        setShowExpandedLIA(true)
      }
      if (matched) {
        setPreviewCandidate(matched)
        setIsPreviewOpen(true)
      }
    }
    return true
  }, [candidatesData, dynamicStages, openTransition, setTransitionInitialPrompt, setLiaPromptValue, setShowExpandedLIA, setPreviewCandidate, setIsPreviewOpen])

  useEffect(() => {
    const raw = localStorage.getItem('navigateToCandidate')
    if (!raw) return

    try {
      const nav = JSON.parse(raw) as {
        candidateId?: string
        candidateName?: string
        jobId?: string
        jobTitle?: string
        currentStage?: string
        interviewType?: string
        action?: string
        openTransitionModal?: boolean
      }
      localStorage.removeItem('navigateToCandidate')

      const prompt = localStorage.getItem('liaPrompt')
      if (prompt) {
        localStorage.removeItem('liaPrompt')
      }

      pendingNavigationRef.current = { nav, prompt }
      processPendingNavigation()
    } catch (e) {
      localStorage.removeItem('navigateToCandidate')
      localStorage.removeItem('liaPrompt')
    }
  }, [job?.id, processPendingNavigation])

  useEffect(() => {
    processPendingNavigation()
  }, [candidatesData, processPendingNavigation])

  // Estado para configuração de colunas
  const [showColumnConfig, setShowColumnConfig] = useState(false)
  const [tableColumns, setTableColumns] = useState<TableColumn[]>(() => getDefaultTableColumns())
  const [columnSearchTerm, setColumnSearchTerm] = useState('')
  
  // Estado para painel de filtros
  const [showTableFiltersPanel, setShowTableFiltersPanel] = useState(false)
  const [showKanbanFiltersPanel, setShowKanbanFiltersPanel] = useState(false)

  // Filtros específicos para Kanban
  const [kanbanScoreMin, setKanbanScoreMin] = useState(0)
  const [kanbanStatusFilter, setKanbanStatusFilter] = useState<string[]>([])
  const [kanbanWorkModelFilter, setKanbanWorkModelFilter] = useState<string[]>([])
  const [kanbanOriginFilter, setKanbanOriginFilter] = useState<string[]>([])

  // Table specific states - Nova tabela elegante
  const [tableSortColumn, setTableSortColumn] = useState<string>('notaLiaGeral')
  const [tableSortDirection, setTableSortDirection] = useState<'asc' | 'desc'>('desc')
  const [tableStageFilter, setTableStageFilter] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 50

  // Estados de redimensionamento de colunas da tabela
  const [tableColumnWidths, setTableColumnWidths] = useState({
    checkbox: 50,
    id: 70,
    notaLiaGeral: 100,
    scoreLiaTriagem: 100,
    scoreLiaCV: 100,
    testeTecnico: 90,
    testeIngles: 80,
    bigFive: 90,
    alertas: 50,
    candidato: 200,
    cargo: 150,
    empresa: 130,
    etapa: 110,
    status: 100,
    acoes: 100
  })
  
  // Callback estável para redimensionamento de colunas
  const handleTableColumnResize = useCallback((columnId: string, width: number) => {
    setTableColumnWidths(prev => ({
      ...prev,
      [columnId]: width
    }))
  }, [])

  // Estados para drag & drop de colunas da tabela
  const [draggedTableColumnId, setDraggedTableColumnId] = useState<string | null>(null)
  const [dragOverTableColumnId, setDragOverTableColumnId] = useState<string | null>(null)
  
  // Ordem das colunas da tabela (checkbox e acoes são fixos)
  const [tableColumnOrder, setTableColumnOrder] = useState<string[]>([
    'checkbox', 'id', 'notaLiaGeral', 'scoreLiaTriagem', 'scoreLiaCV', 'testeTecnico', 
    'testeIngles', 'bigFive', 'alertas', 'candidato', 'cargo', 'empresa', 'etapa', 'status', 'acoes'
  ])

  const [jobLocalOverrides, setJobLocalOverrides] = useState<Record<string, any>>({})
  const currentJob = job ? { ...job, ...jobLocalOverrides } : jobData

  const [showJobEditor, setShowJobEditor] = useState(false)
  const [editingSection, setEditingSection] = useState<string | null>(null)
  const [savingJobSection, setSavingJobSection] = useState<string | null>(null)
  const { defaults: companyDefaults } = useCompanyDefaults()

  useEffect(() => {
    if (currentJob) {
      setJobEditForm({
        title: currentJob.title || '',
        department: currentJob.department || '',
        location: currentJob.location || '',
        workModel: currentJob.workModel || '',
        type: currentJob.type || '',
        level: currentJob.level || '',
        status: currentJob.status || '',
        urgencyLevel: currentJob.urgencyLevel || 3,
        recruiter: currentJob.recruiter || '',
        recruiterEmail: currentJob.recruiterEmail || '',
        manager: currentJob.manager || currentJob.hiringManager || '',
        managerEmail: currentJob.managerEmail || currentJob.hiringManagerEmail || '',
        openDate: currentJob.openDate || '',
        deadline: currentJob.deadline || '',
        deadlineScreening: currentJob.deadlineScreening || '',
        deadlineShortlist: currentJob.deadlineShortlist || '',
        deadlineClosing: currentJob.deadlineClosing || '',
        salaryMin: currentJob.salaryRange?.min || currentJob.salaryMin || '',
        salaryMax: currentJob.salaryRange?.max || currentJob.salaryMax || '',
        bonusMin: currentJob.bonusRange?.min || currentJob.bonus_range?.min || '',
        bonusMax: currentJob.bonusRange?.max || currentJob.bonus_range?.max || '',
        benefits: currentJob.benefits || [],
        targetAudience: currentJob.targetAudience || '',
        targetSector: currentJob.targetSector || '',
        targetSegment: currentJob.targetSegment || '',
        languages: currentJob.languages || [],
        visibility: currentJob.visibility || 'internal',
        isConfidential: currentJob.isConfidential || false,
        maskedCompanyName: currentJob.maskedCompanyName || '',
        isAffirmative: currentJob.isAffirmative || false,
        affirmativeCriteriaPrimary: currentJob.affirmativeCriteriaPrimary || currentJob.affirmativeType || '',
        affirmativeCriteriaSecondary: currentJob.affirmativeCriteriaSecondary || '',
        affirmativeDescription: currentJob.affirmativeDescription || '',
        affirmativeDocumentRequired: currentJob.affirmativeDocumentRequired || false,
        affirmativeDocumentTypes: currentJob.affirmativeDocumentTypes || [],
        priority: currentJob.priority || 'média',
        description: currentJob.description || '',
        interviewStages: (currentJob.interviewStages && currentJob.interviewStages.length > 0 && currentJob.interviewStages[0]?.stageCategory)
          ? currentJob.interviewStages
          : (() => {
              const pipeline = getCompanyPipelineStages()
              return pipeline
                .filter(s => s.isActive)
                .map((s, i) => ({
                  stageName: s.displayName,
                  order: i + 1,
                  type: 'interview' as const,
                  name: s.name,
                  stageCategory: s.stageCategory,
                  isEditable: s.isEditable,
                  isRemovable: s.isRemovable,
                  isReorderable: s.isReorderable,
                  isInitial: s.isInitial,
                  isFinal: s.isFinal,
                  isHired: s.isHired,
                  isRejection: s.isRejection,
                  color: s.color,
                  stageType: s.stageType,
                  slaDays: s.defaultSlaDays,
                  defaultSlaDays: s.defaultSlaDays,
                  liaAssisted: s.liaAssisted,
                }))
            })(),
      })
    }
  }, [currentJob?.id])

  useEffect(() => {
    if (!companyDefaults?.defaultLanguages?.length) return
    if (jobEditForm.languages && jobEditForm.languages.length > 0) return

    const prefilled = companyDefaults.defaultLanguages.map((lang: string) => ({
      language: lang,
      level: 'Intermediário',
      required: false,
    }))
    setJobEditForm(prev => ({ ...prev, languages: prefilled }))
  }, [companyDefaults?.defaultLanguages, jobEditForm.languages])

  useEffect(() => {
    if (isLoadingCandidates) return
    const jobId = (currentJob?.backendId || currentJob?.id)?.toString()
    if (!jobId) return

    const hasAnyCandidates = Object.values(candidatesData).some(arr => arr.length > 0)
    if (!hasAnyCandidates) return

    liaApi.wsiGetCandidatesScores(jobId)
      .then(data => {
        if (!data?.candidates || Object.keys(data.candidates).length === 0) return

        setCandidatesData(prev => {
          const updated: Record<string, any[]> = {}
          for (const [stageId, candidates] of Object.entries(prev)) {
            updated[stageId] = candidates.map((c: any) => {
              const wsiData = data.candidates[c.id]
              if (!wsiData) return c
              return {
                ...c,
                liaScore: wsiData.overall_wsi,
                score: wsiData.overall_wsi,
                wsiScore: wsiData.overall_wsi,
                wsiTechnical: wsiData.technical_wsi,
                wsiBehavioral: wsiData.behavioral_wsi,
                wsiClassification: wsiData.classification,
                wsiPercentile: wsiData.percentile,
              }
            })
          }
          return updated
        })
      })
      .catch(err => {
      })
  }, [isLoadingCandidates, currentJob?.id])

  const findCandidateById = useCallback((id: string) => {
    return allTableCandidates.find((c: any) => String(c.id) === String(id))
  }, [allTableCandidates])

  const openUnifiedModal = useCallback((candidate: any, type: CommunicationType) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }, [])

  const { handleLiaUiAction, handleAICommand, handleOrchestratedMessage } = useKanbanLIAHandlers({
    liaMessages,
    setLiaMessages,
    setLiaPromptValue,
    setIsLiaLoading,
    setShowExpandedLIA,
    setShowSuperChat,
    setUserCollapsedLIA,
    liaConversationId,
    setLiaConversationId,
    currentJob,
    allTableCandidates,
    selectedCandidates,
    candidatesData,
    user,
    findCandidateById,
    openUnifiedModal,
    openTransition,
    setWsiCandidate,
    setShowWSIModal,
    setWsiInviteCandidate,
    setShowWSIInviteModal,
    setDataRequestModalCandidate,
    setShowDataRequestModal,
    setRubricCandidate,
    setShowRubricModal,
  })

  // Auto-scroll para o final do chat quando novas mensagens chegam
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [liaMessages, isLiaLoading])

  // Ciclo fechado: atualizar kanban quando LIA executar uma ação via chat principal
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.action_id === "move_candidate") {
        setTimeout(() => router.refresh(), 500)
      }
    }
    window.addEventListener("lia:action-executed", handler)
    return () => window.removeEventListener("lia:action-executed", handler)
  }, [router])

  const computedSuggestions = useMemo(() => {
    const suggestions: Array<{type: string; severity: string; candidate_id: string; candidate_name: string; message: string; suggested_action: string; stage: string}> = []
    const now = Date.now()
    dynamicStages.forEach(stage => {
      const stageCandidates = candidatesData[stage.id] || []
      stageCandidates.forEach((candidate: any) => {
        const addedDate = candidate.movedAt || candidate.addedAt
        const daysInStage = addedDate ? Math.floor((now - new Date(addedDate).getTime()) / (1000 * 60 * 60 * 24)) : 0
        if (daysInStage > 7) {
          suggestions.push({
            type: 'stale_candidate',
            severity: 'warning',
            candidate_id: candidate.id,
            candidate_name: candidate.name || 'Candidato',
            message: `${candidate.name || 'Candidato'} está parado em "${stage.displayName}" há ${daysInStage} dias`,
            suggested_action: 'Considere avançar ou dar retorno',
            stage: stage.id
          })
        }
        const score = candidate.lia_score || candidate.liaScore || 0
        if (score >= 80) {
          suggestions.push({
            type: 'high_score',
            severity: 'success',
            candidate_id: candidate.id,
            candidate_name: candidate.name || 'Candidato',
            message: `${candidate.name || 'Candidato'} tem score WSI alto (${Math.round(score)})`,
            suggested_action: 'Considere priorizar este candidato',
            stage: stage.id
          })
        }
        if (score > 0 && score < 40) {
          suggestions.push({
            type: 'low_score',
            severity: 'danger',
            candidate_id: candidate.id,
            candidate_name: candidate.name || 'Candidato',
            message: `${candidate.name || 'Candidato'} tem score WSI baixo (${Math.round(score)})`,
            suggested_action: 'Avaliar permanência no processo',
            stage: stage.id
          })
        }
      })
    })
    return suggestions
  }, [dynamicStages, candidatesData])

  const hasShownProactiveSuggestion = useRef(false)
  const lastBriefingJobId = useRef<string | null>(null)

  useEffect(() => {
    if (currentJob?.id && currentJob.id !== lastBriefingJobId.current) {
      hasShownProactiveSuggestion.current = false
      lastBriefingJobId.current = currentJob.id
    }
  }, [currentJob?.id])

  useEffect(() => {
    if (liaMessages.length > 0 || hasShownProactiveSuggestion.current || !currentJob?.id) return
    hasShownProactiveSuggestion.current = true

    const buildBriefing = async () => {
      const total = allTableCandidates.length
      const stageMap: Record<string, number> = {}
      allTableCandidates.forEach(c => {
        const s = c.stage || 'sourcing'
        stageMap[s] = (stageMap[s] || 0) + 1
      })
      const stageLabels: Record<string, string> = {
        sourcing: 'Sourcing', screening: 'Screening', interview_hr: 'Entrevista RH',
        interview_technical: 'Entrevista Técnica', interview_manager: 'Entrevista Gestor',
        offer: 'Proposta', hired: 'Contratado'
      }
      const pipelineLines = Object.entries(stageMap)
        .map(([k, v]) => `${stageLabels[k] || k}: ${v}`)
        .join(' | ')

      const staleCount = computedSuggestions.filter(s => s.type === 'stale_candidate').length
      const highScoreCount = computedSuggestions.filter(s => s.type === 'high_score').length
      const lowScoreCount = computedSuggestions.filter(s => s.type === 'low_score').length

      const atRiskCandidates = allTableCandidates.filter(c => (c.daysInStage || 0) > 14)
      const dropoutRiskCandidates = allTableCandidates.filter(c => {
        const days = c.daysInStage || 0
        const score = c.score || c.wsiScore || 0
        return days > 10 && score >= 70
      })

      let alertParts: string[] = []
      if (staleCount > 0) alertParts.push(`${staleCount} candidato${staleCount > 1 ? 's' : ''} parado${staleCount > 1 ? 's' : ''} ha mais de 7 dias`)
      if (atRiskCandidates.length > 0) alertParts.push(`${atRiskCandidates.length} candidato${atRiskCandidates.length > 1 ? 's' : ''} em risco (parado${atRiskCandidates.length > 1 ? 's' : ''} ha mais de 14 dias)`)
      if (dropoutRiskCandidates.length > 0) alertParts.push(`${dropoutRiskCandidates.length} candidato${dropoutRiskCandidates.length > 1 ? 's' : ''} com risco de desistencia (score alto + longo tempo de espera)`)
      if (highScoreCount > 0) alertParts.push(`${highScoreCount} candidato${highScoreCount > 1 ? 's' : ''} com score alto para priorizar`)
      if (lowScoreCount > 0) alertParts.push(`${lowScoreCount} candidato${lowScoreCount > 1 ? 's' : ''} com score baixo para revisar`)

      let mlSection = ''
      try {
        const companyId = _companyIdForSL
        const jobPayload = {
          title: currentJob.title,
          department: currentJob.department,
          seniority: currentJob.seniority,
          location: currentJob.location,
          work_model: currentJob.workModel,
          employment_type: currentJob.employmentType,
        }
        const [ttfRes, salRes] = await Promise.allSettled([
          fetch('/api/backend-proxy/ml/predict/time-to-fill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: companyId, job_data: jobPayload }),
          }).then(r => r.ok ? r.json() : null),
          fetch('/api/backend-proxy/ml/predict/salary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ company_id: companyId, job_data: jobPayload }),
          }).then(r => r.ok ? r.json() : null),
        ])

        const ttf = ttfRes.status === 'fulfilled' ? ttfRes.value : null
        const sal = salRes.status === 'fulfilled' ? salRes.value : null

        const mlParts: string[] = []
        if (ttf?.predicted_days) {
          mlParts.push(`Tempo estimado: **${ttf.predicted_days} dias** (${ttf.range_min}-${ttf.range_max}d)`)
        }
        if (sal?.suggested_min && sal?.suggested_max) {
          const fmt = (v: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL', maximumFractionDigits: 0 }).format(v)
          mlParts.push(`Faixa salarial sugerida: **${fmt(sal.suggested_min)} - ${fmt(sal.suggested_max)}** (percentil ${sal.market_percentile || '—'}%)`)
        }
        if (mlParts.length > 0) {
          mlSection = `\n\n**Previsoes IA:**\n• ${mlParts.join('\n• ')}`
        }
      } catch {
        // ML predictions unavailable — briefing still shows pipeline data
      }

      const sections: string[] = []
      sections.push(`**Pipeline:** ${total} candidato${total !== 1 ? 's' : ''} — ${pipelineLines}`)
      if (alertParts.length > 0) {
        sections.push(`**Alertas:**\n• ${alertParts.join('\n• ')}`)
      }
      if (mlSection) {
        sections.push(mlSection.trim())
      }
      if (dropoutRiskCandidates.length > 0) {
        const names = dropoutRiskCandidates.slice(0, 3).map(c => c.name).join(', ')
        sections.push(`**Acao sugerida:** Priorize contato com ${names}${dropoutRiskCandidates.length > 3 ? ` e mais ${dropoutRiskCandidates.length - 3}` : ''} para evitar perda de talentos qualificados.`)
      }
      sections.push('Posso ajudar com analises, comparacoes, previsoes de risco ou acoes. O que precisa?')

      const message = `Ola! Preparei o briefing desta vaga:\n\n${sections.join('\n\n')}`

      setLiaMessages(prev => {
        if (prev.length > 0) return prev
        return [{
          id: `proactive-${Date.now()}`,
          type: 'response',
          content: message,
          timestamp: Date.now()
        }]
      })
    }

    buildBriefing()
  }, [currentJob?.id, allTableCandidates.length, computedSuggestions, liaMessages.length])

  const { handleDragStart, handleDragEnd, handleDragOver, handleDragLeave, getSuggestedSubStatus, getAvailableSubStatuses, getSubStatusColor, stagesRequiringConfirmation, handleDrop, confirmMove, cancelMove } = useKanbanDragDrop({
    draggedCandidate,
    setDraggedCandidate,
    dragOverColumn,
    setDragOverColumn,
    dynamicStages,
    openTransition,
    pendingMove,
    setPendingMove,
    statusModalOpen,
    setStatusModalOpen,
    selectedSubStatus,
    setSelectedSubStatus,
    setCandidatesData,
    job,
  })

  // Helper para obter o nome de exibição de uma etapa
  const getStageDisplayName = (stageId: string): string => {
    const stage = dynamicStages.find(s => s.id === stageId)
    if (stage) return stage.displayName
    const recruitmentStage = RECRUITMENT_STAGES.find(s => s.name === stageId)
    return recruitmentStage?.displayName || stageId
  }

  // Função para filtrar candidatos baseado na busca
  const filterCandidates = (candidates: any[]) => {
    if (!searchQuery) return candidates

    const query = searchQuery.toLowerCase()
    return candidates.filter(candidate =>
      candidate.name.toLowerCase().includes(query) ||
      candidate.role?.toLowerCase().includes(query) ||
      candidate.company?.toLowerCase().includes(query) ||
      candidate.location?.toLowerCase().includes(query) ||
      candidate.currentCompany?.toLowerCase().includes(query)
    )
  }

  // Function to mark candidate as viewed
  const markCandidateAsViewed = async (candidateId: string) => {
    try {
      await fetch(`/api/backend-proxy/candidates/${candidateId}/viewed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: 'job-kanban' })
      })
      setViewedCandidateIds(prev => new Set([...prev, candidateId]))
    } catch (error) {
    }
  }

  // Função para abrir o preview do candidato
  const handleOpenPreview = (candidate: any) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(true)
    if (candidate?.id) {
      markCandidateAsViewed(candidate.id)
    }
  }

  // Função para fechar o preview
  const handleClosePreview = () => {
    setIsPreviewOpen(false)
    setPreviewCandidate(null)
  }

  // Função para abrir a página completa do candidato
  const handleCandidatePageOpen = (candidate: any) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(false) // Fecha o preview
    setShowCandidatePage(true) // Abre a página completa
  }

  // Função para fechar a página completa do candidato
  const handleCloseCandidatePage = () => {
    setShowCandidatePage(false)
  }

  const handleSendEmail = (candidate: any) => openUnifiedModal(candidate, 'email')
  const handleSendWhatsApp = (candidate: any) => openUnifiedModal(candidate, 'whatsapp')
  const handleSendTriagem = (candidate: any) => openUnifiedModal(candidate, 'triagem')
  const handleSendAgendamento = (candidate: any) => openUnifiedModal(candidate, 'agendamento')
  const handleSendFeedback = (candidate: any) => openUnifiedModal(candidate, 'feedback')

  const handleUnifiedModalClose = () => {
    setUnifiedModalOpen(false)
    setUnifiedModalCandidate(null)
    setUnifiedModalSituation(undefined)
  }

  // Handlers para WSI Text Screening e Add to Vacancy
  const handleStartWSITextScreening = (candidate: any) => {
    setWsiCandidate(candidate)
    setShowWSIModal(true)
  }

  const handleAddToVacancy = (candidate: any) => {
    setCandidateForVacancy(candidate)
    setShowAddToVacancyModal(true)
  }

  const handleTogglePreviewMaximize = () => {
    setIsPreviewMaximized(!isPreviewMaximized)
  }

  const handleToggleFavorite = (candidateId: string) => {
    talentFunnel.toggleFavoriteCandidate(candidateId)
    // Local state will be synced via the useEffect above
  }

  const handleToggleShortList = useCallback(async (candidateId: string) => {
    const isInList = shortListedCandidateIds.has(candidateId)
    let listId: string | null = activeShortListId || shortLists[0]?.id || null

    if (!listId) {
      const newList = await _createSL(_jobIdForSL || '', `Short List — ${job?.title || 'Vaga'}`)
      if (!newList) return
      listId = newList.id
      setActiveShortListId(newList.id)
    }

    if (isInList) {
      const ok = await _removeFromSL(listId, candidateId)
      if (ok) setShortListedCandidateIds(prev => { const next = new Set(prev); next.delete(candidateId); return next })
    } else {
      const ok = await _addToSL(listId, candidateId)
      if (ok) setShortListedCandidateIds(prev => new Set([...prev, candidateId]))
    }
  }, [shortListedCandidateIds, activeShortListId, shortLists, _createSL, _addToSL, _removeFromSL, _jobIdForSL, job?.title])

  // Handler for interactive sub-status change (from InteractiveSubStatusCell)
  const handleInteractiveStatusChange = async (
    candidateId: string, 
    newSubStatus: string, 
    stage: string, 
    jobVacancyId?: string
  ): Promise<boolean> => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/stage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          stage,
          sub_status: newSubStatus,
          job_vacancy_id: jobVacancyId || jobData?.id?.toString()
        })
      })

      if (!response.ok) {
        return false
      }

      // Optimistic update: update local state
      setCandidatesData((prevData: Record<string, any[]>) => {
        const newData = { ...prevData }
        for (const stageKey in newData) {
          newData[stageKey] = newData[stageKey].map((c: any) => 
            c.id === candidateId 
              ? { ...c, sub_status: newSubStatus }
              : c
          )
        }
        return newData
      })

      return true
    } catch (error) {
      return false
    }
  }

  // Handler for table transition request - delegates to UniversalTransitionModal (same as Kanban)
  const handleTableTransitionRequest = useCallback((
    candidate: {
      id: string
      name: string
      email?: string
      phone?: string
      avatar?: string
      currentTitle?: string
    },
    fromStage: string,
    toStage: string
  ) => {
    const kanbanCandidate: KanbanCandidate = {
      id: candidate.id,
      name: candidate.name,
      email: candidate.email,
      phone: candidate.phone,
      avatar: candidate.avatar,
      currentTitle: candidate.currentTitle,
      stageId: fromStage,
    }
    openTransition([kanbanCandidate], fromStage, toStage)
  }, [openTransition])

  const handleScheduleInterview = (candidate: any) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType('agendamento')
    setUnifiedModalOpen(true)
  }

  const handleNavigateCandidate = (index: number) => {
    const data = candidatesData as Record<string, any[]>
    const currentColumn = Object.keys(data).find(col => 
      data[col].some((c: any) => c.id === previewCandidate?.id)
    )
    if (currentColumn && data[currentColumn][index]) {
      setPreviewCandidate(data[currentColumn][index])
    }
  }

  const handleSendWSIInvite = (candidate: any) => {
    setWsiInviteCandidate(candidate)
    setShowWSIInviteModal(true)
  }

  // Handlers para Rubric Evaluation Modal
  // Funções para abrir modal de fluxo de decisão
  const { handleDecisionFlowConfirm, handleApproveCandidate, handleRejectCandidate, handleApproveFromScreening, handleRejectFromScreening, handleTriagemApprove, handleTriagemReject, handleOpenAnalysis, openDecisionFlowModal } = useKanbanCandidateDecisions({
    toast,
    job,
    dynamicStages,
    setCandidatesData,
    setShowDecisionFlowModal,
    setDecisionFlowCandidate,
    decisionFlowCandidate,
    openTransition,
    setTransitionInitialPrompt,
    onCloseTriagem: handleCloseTriagem,
    setRubricCandidate,
    setShowRubricModal,
    setRubricEvaluationData,
    setDecisionFlowType,
  })

  // Função para abrir modais de scores (dos cards do Kanban)
  const handleOpenScoreModal = (candidate: any, modalType: 'geral' | 'triagem' | 'cv' | 'tecnico' | 'ingles' | 'b5') => {
    setScoreModalCandidate(candidate)
    switch (modalType) {
      case 'geral':
        setShowGeneralScoreModal(true)
        break
      case 'triagem':
        handleOpenTriagem(candidate)
        break
      case 'cv':
        handleOpenAnalysis(candidate)
        break
      case 'tecnico':
        setShowTechnicalTestModal(true)
        break
      case 'ingles':
        setShowEnglishTestModal(true)
        break
      case 'b5':
        setShowBigFiveModal(true)
        break
    }
  }

  const { handleSaveJobSection, handleInlineRename, handleInlineToggleActive, handleInlineRemove, handleInlineMoveLeft, handleInlineMoveRight, handleInlineUpdateSLA } = useKanbanJobEditing({
    toast,
    currentJob,
    jobEditForm,
    setSavingJobSection,
    setEditingSection,
    setDynamicStages,
    setCandidatesData,
    mapInterviewStagesToKanban,
    createInitialCandidatesData,
  })

  // Funções para o relatório
  const handleShowReport = () => {
    setShowReport(true)
  }

  const handleCloseReport = () => {
    setShowReport(false)
  }

  // Helper functions for elegant table view
  // Flatten all candidates for table view - suporta etapas dinâmicas
  const getAllCandidates = useCallback(() => {
    const allCandidates: any[] = []
    
    // Criar mapeamento dinâmico baseado em dynamicStages
    const stageMapping: Record<string, { name: string; color: string }> = {}
    dynamicStages.forEach(stage => {
      let color = 'bg-gray-100 text-gray-800 dark:text-gray-200'
      if (stage.isHired) {
        color = 'bg-gray-900 text-white dark:bg-gray-50 dark:text-gray-900 font-bold'
      } else if (stage.isRejection || stage.id === 'offer_declined') {
        color = 'bg-gray-400 text-gray-950 dark:bg-gray-600 dark:text-gray-100 font-medium'
      } else if (stage.isInitial) {
        color = 'bg-gray-100 text-gray-800 dark:text-gray-200'
      } else if (stage.stageType === 'final') {
        color = 'bg-gray-300 text-gray-950 dark:bg-gray-600 dark:text-gray-50 font-bold'
      }
      stageMapping[stage.id] = { name: stage.displayName, color }
    })

    Object.entries(candidatesData).forEach(([stage, candidates]) => {
      if (candidates && Array.isArray(candidates)) {
        candidates.forEach(candidate => {
          allCandidates.push({
            ...candidate,
            stage: stageMapping[stage]?.name || stage,
            stageColor: stageMapping[stage]?.color || "bg-gray-100 text-gray-800 dark:text-gray-200"
          })
        })
      }
    })

    return allCandidates
  }, [dynamicStages, candidatesData])

  // Calculate Nota LIA Geral (0-100)
  const calculateNotaLiaGeral = (candidate: any) => {
    // COMPONENTES DA NOTA (cada um 0-100)

    // 1. Score LIA CV (análise curricular vs requisitos da vaga) - peso 25%
    const scoreLiaCV = candidate.skillsMatch || candidate.fitScore || 0

    // 2. Score LIA Triagem (pré-requisitos técnicos + comportamentais) - peso 30%
    const scoreLiaTriagem = (candidate.liaScore || candidate.score || 0)

    // 3. Score Teste Técnico (quando aplicável) - peso 25%
    const scoreTesteTecnico = candidate.technicalTestScore || 0

    // 4. Score Teste Inglês (quando aplicável) - peso 20%
    const scoreTesteIngles = candidate.englishTestScore || 0

    // CÁLCULO DA NOTA BASE (média ponderada 0-100)
    // Cada componente é convertido para escala 0-1 e multiplicado pelo peso em pontos
    const notaBase = (
      (scoreLiaCV / 100 * 25) +        // Máximo 25 pontos (25% do peso)
      (scoreLiaTriagem / 100 * 30) +   // Máximo 30 pontos (30% do peso)
      (scoreTesteTecnico / 100 * 25) + // Máximo 25 pontos (25% do peso)
      (scoreTesteIngles / 100 * 20)    // Máximo 20 pontos (20% do peso)
    )

    // BÔNUS DE URGÊNCIA (+10 pontos)
    let bonusUrgencia = 0
    if (candidate.approvalPending && candidate.liaStatus === 'aguardando_aprovacao_contato') {
      bonusUrgencia = 10
    } else if (candidate.approvalPending && candidate.liaStatus === 'triagem_completa') {
      bonusUrgencia = 8
    } else if (candidate.approvalPending || candidate.needsAction) {
      bonusUrgencia = 5
    }

    // BÔNUS POR ETAPA AVANÇADA (+5 pontos)
    let bonusEtapa = 0
    if (candidate.stage === 'Final') {
      bonusEtapa = 5
    } else if (candidate.stage === 'Entrevista') {
      bonusEtapa = 3
    }

    // BÔNUS POR TRIAGEM COMPLETA E APROVADA (+5 pontos)
    let bonusTriagem = 0
    if (candidate.triageComplete) {
      bonusTriagem = 5
    }

    // PENALIZAÇÃO POR TEMPO PARADO (-0.5 pontos por dia, máx -10)
    const daysStuck = 0 // Em produção, viria do backend
    const penalizacaoTempo = Math.min(daysStuck * 0.5, 10)

    // NOTA FINAL (0-100)
    let notaFinal = notaBase + bonusUrgencia + bonusEtapa + bonusTriagem - penalizacaoTempo

    // Garantir que fica entre 0 e 100
    notaFinal = Math.max(0, Math.min(100, notaFinal))

    return Math.round(notaFinal * 10) / 10 // arredonda para 1 casa decimal
  }


  // Table sorting function
  const handleTableSort = (column: string) => {
    if (tableSortColumn === column) {
      setTableSortDirection(tableSortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setTableSortColumn(column)
      setTableSortDirection('asc')
    }
  }

  // Handlers para redimensionamento de colunas da tabela
  const startTableColumnResize = (column: string, event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    const startX = event.clientX
    const startWidth = tableColumnWidths[column as keyof typeof tableColumnWidths] || 100

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(50, startWidth + (e.clientX - startX))
      setTableColumnWidths(prev => ({
        ...prev,
        [column]: newWidth
      }))
    }

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  }

  // Handlers para drag & drop de colunas da tabela
  const handleTableColumnDragStart = (columnId: string, e: React.DragEvent) => {
    if (columnId === 'checkbox' || columnId === 'acoes') return
    
    setDraggedTableColumnId(columnId)
    e.dataTransfer.effectAllowed = 'move'
    e.dataTransfer.setData('text/plain', columnId)
    
    const dragImage = document.createElement('div')
    dragImage.style.opacity = '0'
    document.body.appendChild(dragImage)
    e.dataTransfer.setDragImage(dragImage, 0, 0)
    setTimeout(() => document.body.removeChild(dragImage), 0)
  }

  const handleTableColumnDragOver = (columnId: string, e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (draggedTableColumnId && draggedTableColumnId !== columnId && columnId !== 'checkbox' && columnId !== 'acoes') {
      setDragOverTableColumnId(columnId)
    }
  }

  const handleTableColumnDragLeave = () => {
    setDragOverTableColumnId(null)
  }

  const handleTableColumnDrop = (targetColumnId: string, e: React.DragEvent) => {
    e.preventDefault()
    if (!draggedTableColumnId || draggedTableColumnId === targetColumnId) {
      setDraggedTableColumnId(null)
      setDragOverTableColumnId(null)
      return
    }

    if (targetColumnId === 'checkbox' || targetColumnId === 'acoes') {
      setDraggedTableColumnId(null)
      setDragOverTableColumnId(null)
      return
    }

    setTableColumnOrder(prev => {
      const newOrder = [...prev]
      const draggedIndex = newOrder.indexOf(draggedTableColumnId)
      const targetIndex = newOrder.indexOf(targetColumnId)
      
      if (draggedIndex === -1 || targetIndex === -1) return prev
      
      newOrder.splice(draggedIndex, 1)
      newOrder.splice(targetIndex, 0, draggedTableColumnId)
      
      localStorage.setItem('job-kanban-table-column-order', JSON.stringify(newOrder))
      
      return newOrder
    })

    setDraggedTableColumnId(null)
    setDragOverTableColumnId(null)
  }

  const handleTableColumnDragEnd = () => {
    setDraggedTableColumnId(null)
    setDragOverTableColumnId(null)
  }

  // Carregar ordem de colunas salva do localStorage
  useEffect(() => {
    const defaultOrder = [
      'checkbox', 'id', 'notaLiaGeral', 'scoreLiaTriagem', 'scoreLiaCV', 'testeTecnico', 
      'testeIngles', 'bigFive', 'alertas', 'candidato', 'cargo', 'empresa', 'etapa', 'status', 'acoes'
    ]
    const savedOrder = localStorage.getItem('job-kanban-table-column-order')
    
    if (savedOrder) {
      try {
        const parsed = JSON.parse(savedOrder) as string[]
        const validOrder = defaultOrder.filter(id => parsed.includes(id))
        
        if (validOrder.length === defaultOrder.length) {
          const orderedCols = parsed.filter((id: string) => defaultOrder.includes(id))
          const finalOrder = ['checkbox', ...orderedCols.filter((id: string) => id !== 'checkbox' && id !== 'acoes'), 'acoes']
          setTableColumnOrder(finalOrder)
        } else {
          setTableColumnOrder(defaultOrder)
        }
      } catch (e) {
        setTableColumnOrder(defaultOrder)
      }
    }
  }, [])

  // Fechar painéis laterais ao trocar de modo de visualização
  useEffect(() => {
    setShowTableFiltersPanel(false)
    setShowKanbanFiltersPanel(false)
    setShowColumnConfig(false)
  }, [viewMode])

  // Get LIA alerts for candidate
  const getLiaAlerts = (candidate: any) => {
    const alerts = []

    if (candidate.approvalPending || candidate.needsAction) {
      if (candidate.liaStatus === 'aguardando_aprovacao_contato') {
        alerts.push({
          type: 'urgent',
          icon: <Flag className="w-3.5 h-3.5" />,
          label: 'Aprovar Contato',
          color: 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600'
        })
      } else if (candidate.liaStatus === 'triagem_completa') {
        alerts.push({
          type: 'urgent',
          icon: <CheckCircle className="w-3 h-3" />,
          label: 'Aprovar Entrevista',
          color: 'bg-gray-900 text-white border-gray-900 dark:bg-gray-50 dark:text-gray-900 dark:border-gray-50'
        })
      } else if (candidate.needsAction) {
        alerts.push({
          type: 'urgent',
          icon: <AlertCircle className="w-3 h-3" />,
          label: 'Ação Necessária',
          color: 'bg-gray-400 text-gray-950 border-gray-400 dark:bg-gray-600 dark:text-gray-100 dark:border-gray-600'
        })
      }
    }

    if (candidate.status === 'reprovado' && candidate.feedbackStatus !== 'feedback_enviado') {
      alerts.push({
        type: 'action',
        icon: <Mail className="w-3 h-3" />,
        label: 'Enviar Feedback',
        color: 'bg-gray-200 text-gray-800 border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700'
      })
    }

    if (candidate.warnings && candidate.warnings > 0) {
      alerts.push({
        type: 'warning',
        icon: <Clock className="w-3 h-3" />,
        label: `${candidate.warnings} Alerta${candidate.warnings > 1 ? 's' : ''}`,
        color: 'bg-gray-300 text-gray-950 border-gray-400 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600'
      })
    }

    return alerts
  }

  // Get filtered and sorted candidates for table
  const getFilteredAndSortedCandidates = () => {
    let candidates = getAllCandidates()

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      candidates = candidates.filter(candidate =>
        candidate.name.toLowerCase().includes(query) ||
        candidate.role?.toLowerCase().includes(query) ||
        candidate.location?.toLowerCase().includes(query) ||
        candidate.currentCompany?.toLowerCase().includes(query)
      )
    }

    // Apply stage filter
    if (tableStageFilter.length > 0) {
      candidates = candidates.filter(c => tableStageFilter.includes(c.stage))
    }

    // Apply sorting
    candidates.sort((a, b) => {
      let aVal: any, bVal: any

      switch (tableSortColumn) {
        case 'name':
          aVal = a.name.toLowerCase()
          bVal = b.name.toLowerCase()
          break
        case 'scoreLiaTriagem':
          aVal = a.liaScore || a.score || 0
          bVal = b.liaScore || b.score || 0
          break
        case 'scoreLiaCV':
          aVal = a.skillsMatch || a.fitScore || 0
          bVal = b.skillsMatch || b.fitScore || 0
          break
        case 'testeTecnico':
          aVal = a.technicalTestScore || 0
          bVal = b.technicalTestScore || 0
          break
        case 'testeIngles':
          aVal = a.englishTestScore || 0
          bVal = b.englishTestScore || 0
          break
        case 'location':
          aVal = a.location.toLowerCase()
          bVal = b.location.toLowerCase()
          break
        case 'stage':
          aVal = a.stage.toLowerCase()
          bVal = b.stage.toLowerCase()
          break
        case 'notaLiaGeral':
          aVal = calculateNotaLiaGeral(a)
          bVal = calculateNotaLiaGeral(b)
          break
        default:
          aVal = calculateNotaLiaGeral(a)
          bVal = calculateNotaLiaGeral(b)
      }

      if (aVal < bVal) return tableSortDirection === 'asc' ? -1 : 1
      if (aVal > bVal) return tableSortDirection === 'asc' ? 1 : -1
      return 0
    })

    return candidates
  }

  // Paginate candidates
  const getPaginatedCandidates = () => {
    const filtered = getFilteredAndSortedCandidates()
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    return {
      candidates: filtered.slice(startIndex, endIndex),
      total: filtered.length,
      totalPages: Math.ceil(filtered.length / itemsPerPage)
    }
  }

  // Toggle stage filter
  const toggleStageFilter = (stageName: string) => {
    setTableStageFilter(prev => {
      if (prev.includes(stageName)) {
        return prev.filter(s => s !== stageName)
      } else {
        return [...prev, stageName]
      }
    })
    setCurrentPage(1) // Reset to first page when filter changes
  }

  // Clear all stage filters
  const clearStageFilters = () => {
    setTableStageFilter([])
    setCurrentPage(1)
  }

  // Get stage counts for filter badges
  const getStageCount = (stageName: string) => {
    return getAllCandidates().filter(c => c.stage === stageName).length
  }

  // Calculate conversion rate from previous stage
  const getConversionRate = (currentStage: string) => {
    const stageOrder = ['Funil', 'Triagem', 'Entrevista', 'Final', 'Aprovados', 'Reprovados']
    const currentIndex = stageOrder.indexOf(currentStage)
    
    if (currentIndex <= 0) return null // Funil não tem etapa anterior
    
    const previousStage = stageOrder[currentIndex - 1]
    const previousCount = getStageCount(previousStage)
    const currentCount = getStageCount(currentStage)
    
    if (previousCount === 0) return null
    
    const rate = Math.round((currentCount / previousCount) * 100)
    return {
      rate,
      previousStage,
      color: rate >= 70 ? 'text-gray-600 dark:text-gray-400' : 
             rate >= 50 ? 'text-gray-800 dark:text-gray-200' : 
             'text-gray-600 dark:text-gray-500'
    }
  }

  // Pipeline stages configuration for elegant table - derivado de dynamicStages
  const pipelineStages = useMemo(() => 
    dynamicStages.map(stage => ({
      id: stage.id,
      name: stage.displayName,
      color: stage.isHired 
        ? "bg-gray-100 text-gray-800 dark:text-gray-200 font-medium" 
        : "bg-gray-100 text-gray-800 dark:text-gray-200",
      count: candidatesData[stage.id]?.length || 0
    })), 
    [dynamicStages, candidatesData]
  )

  // Mock candidates data atualizado com URLs de avatar
  // Mock candidates data para o componente interno
  const candidatesMockData = {
    funil: [
      {
        id: 1,
        name: "Maria Santos",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "6 anos",
        days: "2 dias atrás",
        score: 8.7,
        fitScore: 92,
        skills: 4,
        needsAction: true,
        actionTime: "há 2 horas",
        badges: ["Aprovar Contato", "Não contratado", "LIA Database"],
        avatar: "https://i.pravatar.cc/150?img=49" // Avatar feminino
      },
      {
        id: 2,
        name: "João Silva",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "4 anos",
        days: "3 horas atrás",
        score: 7.2,
        fitScore: 78,
        skills: 65,
        badges: ["LIA sem Contato", "Tentando contato", "Website"],
        avatar: "https://i.pravatar.cc/150?img=11" // Avatar masculino
      },
      {
        id: 3,
        name: "Rafael Mendes",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "5 anos",
        days: "Ontem",
        score: 8.2,
        fitScore: 85,
        skills: 72,
        needsAction: true,
        actionTime: "há 4 horas",
        badges: [],
        avatar: "https://i.pravatar.cc/150?img=12" // Avatar masculino
      }
    ],
    triagem: [
      {
        id: 4,
        name: "Ana Costa",
        role: "UX Designer",
        company: "TechCorp",
        location: "Rio de Janeiro, RJ",
        experience: "7 anos",
        days: "3 horas atrás",
        score: 9.1,
        fitScore: 96,
        skills: 92,
        needsAction: true,
        actionTime: "há 30 min",
        badges: ["Triagem OK", "Confiável", "LIA Database"],
        warning: "Esse candidato está 10 dias parado. Posso movê-lo ou arquivá-lo?",
        warningDays: "Será arquivado em 4 dias se não houver ação",
        avatar: "https://i.pravatar.cc/150?img=44" // Avatar feminino
      },
      {
        id: 5,
        name: "Beatriz Oliveira",
        role: "UX Designer",
        company: "TechCorp",
        location: "Campinas, SP",
        experience: "6 anos",
        days: "Hoje",
        score: 8.4,
        fitScore: 87,
        skills: 80,
        badges: ["tentando contato", "Indeed"],
        avatar: "https://i.pravatar.cc/150?img=45" // Avatar feminino
      }
    ],
    entrevista: [
      {
        id: 6,
        name: "Carlos Oliveira",
        role: "UX Designer",
        company: "TechCorp",
        location: "Porto Alegre, RS",
        experience: "5 anos",
        interviewDate: "Entrevista agendada para hoje",
        score: 8.3,
        fitScore: 88,
        skills: 75,
        badges: ["em processo", "LinkedIn"],
        status: "Entrevista Entrevista agendada para hoje. Já enviei o lembrete!",
        avatar: "https://i.pravatar.cc/150?img=13" // Avatar masculino
      },
      {
        id: 7,
        name: "Daniela Santos",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "6 anos",
        interviewDate: "Entrevista amanhã",
        score: 8.6,
        fitScore: 90,
        skills: 86,
        badges: ["em processo", "Referral"],
        warning: "Esse candidato está 11 dias parado. Posso movê-lo ou arquivá-lo?",
        warningDays: "Será arquivado em 3 dias se não houver ação",
        avatar: "https://i.pravatar.cc/150?img=47" // Avatar feminino
      }
    ],
    final: [
      {
        id: 8,
        name: "Fernanda Lima",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "8 anos",
        feedback: "Feedback positivo recebido",
        score: 9.5,
        fitScore: 98,
        skills: null,
        badges: ["em processo", "Referral"],
        avatar: "https://i.pravatar.cc/150?img=48" // Avatar feminino
      },
      {
        id: 9,
        name: "Gabriel Rodrigues",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "7 anos",
        aguardando: "Aguardando aprovação",
        score: 8.8,
        fitScore: 93,
        skills: 90,
        badges: ["em processo", "Recrutador"],
        warning: "Esse candidato está 13 dias parado. Posso movê-lo ou arquivá-lo?",
        warningDays: "Será arquivado em 1 dias se não houver ação",
        avatar: "https://i.pravatar.cc/150?img=14" // Avatar masculino
      },
      {
        id: 10,
        name: "Juliana Martins",
        role: "UX Designer",
        company: "TechCorp",
        location: "Rio de Janeiro, RJ",
        experience: "8 anos",
        proposta: "Proposta em preparação",
        score: 9,
        fitScore: 95,
        skills: 93,
        avatar: "https://i.pravatar.cc/150?img=31" // Avatar feminino
      }
    ],
    aprovados: [
      {
        id: 11,
        name: "Patricia Souza",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "7 anos",
        proposta: "Proposta aceita",
        score: 9.3,
        fitScore: 96,
        skills: 95,
        badges: ["contratado", "Referral"],
        avatar: "https://i.pravatar.cc/150?img=32" // Avatar feminino
      }
    ],
    reprovados: [
      {
        id: 12,
        name: "Ricardo Alves",
        role: "UX Designer",
        company: "TechCorp",
        location: "São Paulo, SP",
        experience: "3 anos",
        feedback: "Feedback enviado há 2 dias",
        score: 6.5,
        fitScore: 68,
        skills: 42,
        badges: ["feedback enviado", "Website"],
        falha: "Falta de experiência em Design System",
        warning: "Esse candidato está 8 dias parado. Posso movê-lo ou arquivá-lo?",
        warningDays: "Será arquivado em 6 dias se não houver ação",
        avatar: "https://i.pravatar.cc/150?img=15" // Avatar masculino
      },
      {
        id: 13,
        name: "Mariana Costa",
        role: "UX Designer",
        company: "TechCorp",
        location: "Rio de Janeiro, RJ",
        experience: "4 anos",
        aguardando: "Aguardando feedback",
        score: 7,
        fitScore: 72,
        skills: 55,
        badges: ["pendente feedback", "LinkedIn"],
        expectativa: "Expectativa salarial acima do budget",
        warning: "Esse candidato está 12 dias parado. Posso movê-lo ou arquivá-lo?",
        warningDays: "Será arquivado em 2 dias se não houver ação",
        avatar: "https://i.pravatar.cc/150?img=35" // Avatar feminino
      }
    ]
  }

  // Kanban columns configuration - derivado de dynamicStages
  const kanbanColumns = useMemo(() => 
    dynamicStages.map(stage => ({
      id: stage.id,
      title: stage.displayName,
      count: candidatesData[stage.id]?.length || 0,
      color: "bg-gray-50 border-gray-200",
      stageColor: stage.color
    })),
    [dynamicStages, candidatesData]
  )

  // Backgrounds para colunas do Kanban - suporta etapas dinâmicas
  // Usa a cor da etapa dinâmica e fornece estilo padrão para etapas não conhecidas
  const getColumnStyle = (columnId: string) => {
    // Estilos fixos para etapas conhecidas
    const fixedStyles: Record<string, { bg: string; border: string; dot: string; header: string; accentColor: string }> = {
      sourcing: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: 'var(--gray-600)'
      },
      hired: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: 'var(--gray-600)'
      },
      rejected: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-300 dark:bg-gray-600',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: 'var(--gray-200)'
      },
      offer_declined: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-300 dark:bg-gray-600',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: 'var(--gray-200)'
      }
    }
    
    // Se há um estilo fixo, use-o
    if (fixedStyles[columnId]) {
      return fixedStyles[columnId]
    }
    
    // Para etapas dinâmicas, buscar a cor da etapa
    const dynamicStage = dynamicStages.find(s => s.id === columnId)
    const stageColor = dynamicStage?.color || 'var(--gray-400)'
    
    // Gerar estilo baseado na cor da etapa
    return {
      bg: 'bg-white dark:bg-gray-900',
      border: 'border-gray-200 dark:border-gray-700',
      dot: 'bg-gray-500 dark:bg-gray-400',
      header: 'text-gray-800 dark:text-gray-200',
      accentColor: stageColor
    }
  }

  // Helper para aplicar cores pastel em micro-detalhes (badges, chips, highlights)
  const getStageAccentStyle = (stage: string) => {
    const style = getColumnStyle(stage)
    return {
      backgroundColor: style.accentColor,
      borderColor: style.accentColor
    }
  }

  const getStageCategory = useCallback((stage: DynamicStage): 'system' | 'default' | 'custom' => {
    if (stage.isInitial || stage.isFinal || stage.isHired || stage.isRejection) return 'system'
    const systemIds = ['sourcing', 'screening', 'hired', 'rejected', 'offer_declined']
    if (systemIds.includes(stage.id)) return 'system'
    const defaultIds = ['long_list', 'short_list', 'interview_hr', 'technical_test', 'english_test',
      'interview_technical', 'interview_manager', 'interview_final', 'references', 'offer',
      'entrevista_rh', 'teste_tecnico', 'teste_de_ingles', 'entrevista_tecnica', 'entrevista_gestor',
      'entrevista_final', 'referencias', 'proposta']
    if (defaultIds.includes(stage.id)) return 'default'
    return 'custom'
  }, [])

  const STAGE_PASTEL_COLORS: Record<string, string> = {
    'sourcing': 'var(--gray-200)',      // Verde Menta - Funil
    'screening': 'var(--gray-200)',     // Rosa Antigo - Triagem
    'interview_hr': 'var(--gray-300)',  // Azul Acinzentado - Entrevista
    'interview_technical': 'var(--gray-300)',
    'interview_manager': 'var(--gray-300)',
    'offer': 'var(--gray-300)',         // Lilás Acinzentado - Final
    'hired': 'var(--gray-300)',
    'rejected': 'var(--gray-300)',
    'offer_declined': 'var(--gray-300)'
  }

  const renderKanbanColumn = (stageId: string, candidates: any[], colorClass: string, bgClass: string) => (
    <KanbanColumnRenderer
      stageId={stageId}
      candidates={candidates}
      colorClass={colorClass}
      bgClass={bgClass}
      dynamicStages={dynamicStages}
      searchQuery={searchQuery}
      draggedCandidate={draggedCandidate}
      dragOverColumn={dragOverColumn}
      selectedCandidates={selectedCandidates}
      selectedForCompare={selectedForCompare}
      viewedCandidateIds={viewedCandidateIds}
      favoriteCandidates={favoriteCandidates}
      shortListedCandidateIds={shortListedCandidateIds}
      aiSuggestions={aiSuggestions}
      kanbanScoreMin={kanbanScoreMin}
      kanbanStatusFilter={kanbanStatusFilter}
      kanbanWorkModelFilter={kanbanWorkModelFilter}
      kanbanOriginFilter={kanbanOriginFilter}
      currentJob={currentJob}
      _jobIdForSL={_jobIdForSL}
      getColumnStyle={getColumnStyle}
      getStageCategory={getStageCategory}
      calculateNotaLiaGeral={calculateNotaLiaGeral}
      getDataRequestForCandidate={getDataRequestForCandidate}
      setSelectedCandidates={setSelectedCandidates}
      setSelectedForCompare={setSelectedForCompare}
      setCandidatesData={setCandidatesData}
      setTransitionInitialPrompt={setTransitionInitialPrompt}
      setTransitionInterviewAlert={setTransitionInterviewAlert}
      setTransitionAllowStageSelection={setTransitionAllowStageSelection}
      setDecisionFlowCandidate={setDecisionFlowCandidate}
      setDecisionFlowType={setDecisionFlowType}
      setShowDecisionFlowModal={setShowDecisionFlowModal}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onDragLeave={handleDragLeave}
      onOpenPreview={handleOpenPreview}
      onSendEmail={handleSendEmail}
      onSendWhatsApp={handleSendWhatsApp}
      onScheduleInterview={handleScheduleInterview}
      onToggleFavorite={handleToggleFavorite}
      onToggleShortList={handleToggleShortList}
      onOpenAnalysis={handleOpenAnalysis}
      onOpenScoreModal={handleOpenScoreModal}
      onOpenDecisionFlowModal={openDecisionFlowModal}
      onSendWSIInvite={handleSendWSIInvite}
      onSendFeedback={handleSendFeedback}
      onApproveFromScreening={handleApproveFromScreening}
      onRejectFromScreening={handleRejectFromScreening}
      onInlineRename={handleInlineRename}
      onInlineToggleActive={handleInlineToggleActive}
      onInlineRemove={handleInlineRemove}
      onInlineMoveLeft={handleInlineMoveLeft}
      onInlineMoveRight={handleInlineMoveRight}
      onInlineUpdateSLA={handleInlineUpdateSLA}
      onOpenSettings={() => router.push('/configuracoes')}
      onDataRequestResend={handleDataRequestResend}
      onDataRequestViewDetails={handleDataRequestViewDetails}
      approveSuggestion={approveSuggestion}
      rejectSuggestion={rejectSuggestion}
      openTransition={openTransition}
    />
  )

  // Renderização apenas no cliente para evitar erros de hidratação SSR
  if (!isClient) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
          <span className="text-sm text-gray-500 font-['Open_Sans']">Carregando...</span>
        </div>
      </div>
    )
  }

  return (
    <>
      <style jsx>{`
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: scale(0.95);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }

        .dragging {
          opacity: 0.5;
          cursor: grabbing !important;
        }

        .drop-zone-active {
          background-color: var(--wedo-cyan-bg-05);
          border-color: 'var(--wedo-cyan)';
        }
      `}</style>

    <div className="h-screen bg-gray-50 dark:bg-gray-950 flex flex-col overflow-hidden">
      {/* Header Principal */}
      <div className="bg-gray-50 dark:bg-gray-950 border-b border-gray-200 dark:border-gray-700">
        <div className="w-full px-4">
          <div className="flex flex-col lg:flex-row items-start justify-between gap-4 mb-4">
            {/* Left: Título e Informações Principais */}
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <Button variant="ghost" size="sm" onClick={() => onBack ? onBack() : router.back()} className="gap-2 mt-1 flex-shrink-0">
                <ArrowLeft className="w-4 h-4" />
                Voltar
              </Button>
              <div className="h-8 w-px bg-gray-300 dark:bg-gray-600 mt-1 flex-shrink-0"></div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-semibold text-gray-950 dark:text-gray-50 whitespace-nowrap">
                    {currentJob.title}
                  </h1>
                  {currentJob.jobId && (
                    <span className="text-micro font-mono text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-1.5 py-0.5 rounded-md whitespace-nowrap">
                      {currentJob.jobId}
                    </span>
                  )}
                  <Popover>
                    <PopoverTrigger asChild>
                      <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:bg-gray-100 transition-colors select-none">
                        {jobEditForm.status || currentJob.status}
                      </Badge>
                    </PopoverTrigger>
                    <PopoverContent className="w-44 p-1" align="start">
                      {(() => { const st = jobEditForm.status || currentJob.status; return st === 'Ativa' || st === 'active' })() ? (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-100 transition-colors"
                            onClick={() => { setJobStatusModalMode('pause'); setShowJobStatusModal(true) }}
                          >
                            <PauseCircle className="w-3.5 h-3.5 text-status-warning" />
                            Pausar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            Fechar vaga
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors"
                            onClick={() => { setJobStatusModalMode('activate'); setShowJobStatusModal(true) }}
                          >
                            <PlayCircle className="w-3.5 h-3.5" />
                            Reativar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-error hover:bg-status-error/10 transition-colors"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            Fechar vaga
                          </button>
                        </>
                      )}
                    </PopoverContent>
                  </Popover>
                  {(() => {
                    const scrStatus = currentJob.screeningStatus || 'not_configured'
                    const scrLabels: Record<string, string> = {
                      not_configured: 'Triagem: N/C',
                      not_started: 'Triagem: Não Iniciada',
                      active: 'Triagem: Ativa',
                      paused: 'Triagem: Pausada',
                      completed: 'Triagem: Concluída',
                    }
                    const scrStyles: Record<string, string> = {
                      not_configured: 'bg-gray-100 text-gray-700 border border-gray-300',
                      not_started: 'bg-status-warning/10 text-status-warning border border-status-warning/30',
                      active: 'bg-status-success/10 text-status-success border border-status-success/30',
                      paused: 'bg-wedo-orange/10 text-wedo-orange border border-wedo-orange/30',
                      completed: 'bg-wedo-cyan/10 text-wedo-cyan border border-wedo-cyan/30',
                    }
                    const handleScreeningStatusChange = async (newStatus: string) => {
                      const jobId = currentJob.backendId || currentJob.jobId || currentJob.id
                      try {
                        await liaApi.updateJobVacancy(jobId, { screeningStatus: newStatus } as any)
                        setJobEditForm((prev: any) => ({ ...prev, screeningStatus: newStatus }))
                        toast({ title: `Triagem ${newStatus === 'active' ? 'ativada' : newStatus === 'paused' ? 'pausada' : 'atualizada'}` })
                      } catch {
                        toast({ title: 'Erro ao atualizar triagem', variant: 'destructive' })
                      }
                    }
                    const badge = (
                      <Badge className={`font-semibold whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:opacity-80 transition-opacity select-none ${scrStyles[scrStatus] || scrStyles.not_configured}`}>
                        {scrLabels[scrStatus] || 'Triagem: N/C'}
                      </Badge>
                    )
                    if (scrStatus === 'completed') return badge
                    return (
                      <Popover>
                        <PopoverTrigger asChild>{badge}</PopoverTrigger>
                        <PopoverContent className="w-48 p-1" align="start">
                          {scrStatus === 'not_configured' && (
                            <button
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-100 transition-colors"
                              onClick={() => setActiveTab('edit')}
                            >
                              <Settings className="w-3.5 h-3.5 text-gray-500" />
                              Configurar Triagem
                            </button>
                          )}
                          {scrStatus === 'not_started' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                Iniciar Triagem
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-100 transition-colors"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-gray-500" />
                                Configurar
                              </button>
                            </>
                          )}
                          {scrStatus === 'active' && (
                            <button
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-warning hover:bg-status-warning/10 transition-colors"
                              onClick={() => handleScreeningStatusChange('paused')}
                            >
                              <PauseCircle className="w-3.5 h-3.5" />
                              Pausar Triagem
                            </button>
                          )}
                          {scrStatus === 'paused' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-status-success hover:bg-status-success/10 transition-colors"
                                onClick={() => handleScreeningStatusChange('active')}
                              >
                                <PlayCircle className="w-3.5 h-3.5" />
                                Retomar Triagem
                              </button>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-gray-700 hover:bg-gray-100 transition-colors"
                                onClick={() => setActiveTab('edit')}
                              >
                                <Settings className="w-3.5 h-3.5 text-gray-500" />
                                Configurar
                              </button>
                            </>
                          )}
                        </PopoverContent>
                      </Popover>
                    )
                  })()}
                </div>
                <div className="flex items-center gap-1.5 flex-wrap mt-1">
                  {currentJob.status === 'Rascunho' && (
                    <Badge className="bg-status-warning/10 dark:bg-status-warning/20 border border-status-warning/30 dark:border-status-warning/30 text-status-warning dark:text-status-warning font-semibold whitespace-nowrap text-micro px-1.5 py-0">
                      Rascunho
                    </Badge>
                  )}
                  <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-semibold whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.level}
                  </Badge>
                  <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium capitalize whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.workModel || '—'}
                  </Badge>
                  <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.type || '—'}
                  </Badge>
                  <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.department}
                  </Badge>
                  <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                    {currentJob.location}
                  </Badge>
                  {currentJob.salary && currentJob.salary !== 'A combinar' && (
                    <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      {currentJob.salary}
                    </Badge>
                  )}
                  {currentJob.publishedLinkedIn && (
                    <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      Publicada
                    </Badge>
                  )}
                  <span className="text-micro text-gray-300 dark:text-gray-600 mx-0.5">|</span>
                  {currentJob.openDate && (
                    <span className="text-micro text-gray-700 dark:text-gray-300 whitespace-nowrap">
                      <Calendar className="w-3 h-3 inline mr-0.5 -mt-0.5" />
                      {new Date(currentJob.openDate).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  )}
                  {currentJob.openDate && (() => {
                    const days = Math.floor((Date.now() - new Date(currentJob.openDate).getTime()) / (1000 * 60 * 60 * 24))
                    if (days <= 0) return null
                    const isLate = days > 30
                    return (
                      <span className={`text-micro font-semibold whitespace-nowrap ${isLate ? 'text-status-error' : 'text-gray-700 dark:text-gray-300'}`}>
                        {days}d {isLate ? 'de atraso' : 'aberta'}
                      </span>
                    )
                  })()}
                  {currentJob.updatedAt && (
                    <span className="text-micro text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      Atualizada: {new Date(currentJob.updatedAt).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </span>
                  )}
                  {currentJob.deadlineScreening && (
                    <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo triagem: {new Date(currentJob.deadlineScreening).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {currentJob.deadlineShortlist && (
                    <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo short: {new Date(currentJob.deadlineShortlist).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {currentJob.deadlineClosing && (
                    <Badge className="bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-micro px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Encerramento: {new Date(currentJob.deadlineClosing).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {computedSuggestions.length > 0 && (
                    <Badge 
                      className="bg-wedo-cyan text-white border-0 font-semibold whitespace-nowrap text-micro px-1.5 py-0 cursor-pointer hover:bg-wedo-cyan-dark transition-colors"
                      onClick={() => {
                        setShowExpandedLIA(true)
                        setShowLiaSuggestionsPanel(true)
                      }}
                    >
                      <Lightbulb className="w-3 h-3 mr-1" />
                      {computedSuggestions.length} sugestão{computedSuggestions.length > 1 ? 'ões' : ''} da LIA
                    </Badge>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Action Buttons */}
            <div className="flex items-center gap-2 pt-1 flex-shrink-0">
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={() => {
                toast({
                  title: "Em breve",
                  description: "Em breve: Configuração de etapas do pipeline",
                })
              }}>
                <Settings className="w-3.5 h-3.5" />
                Configurar Etapas
              </Button>
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={handleShowReport}>
                <FileText className="w-3.5 h-3.5" />
                Relatório
              </Button>
              <Button variant="outline" size="sm" className="gap-2 h-8" onClick={() => {
                if (selectedCandidates.size > 0) {
                  setShowShareGestorModal(true)
                } else {
                  setSelectedCandidates(new Set(allTableCandidates.map(c => c.id)))
                  toast({
                    title: "Modo Compartilhamento",
                    description: "Todos os candidatos foram selecionados. Ajuste a seleção e clique em Compartilhar na barra de ações.",
                  })
                }
              }}>
                <Share2 className="w-3.5 h-3.5" />
                Compartilhar
              </Button>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="flex items-center gap-1 px-4 mt-2">
            <button
              onClick={() => { setActiveTab('management'); setShowJobEditor(false); }}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                activeTab === 'management'
                  ? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <Layers3 className="w-3.5 h-3.5" />
              Gestão da Vaga
              <Badge className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-micro px-1.5 py-0 ml-1">
                {allTableCandidates?.length || 0}
              </Badge>
            </button>
            <button
              onClick={() => { setActiveTab('edit'); setShowJobEditor(true); }}
              className={`flex items-center gap-2 px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
                activeTab === 'edit'
                  ? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              <Settings className="w-3.5 h-3.5" />
              Configurações
            </button>
            <div className="ml-auto flex items-center gap-2">
              {pipelineInheritance.isCustomized ? (
                <>
                  <span className="inline-flex items-center gap-1 text-micro text-status-warning dark:text-status-warning">
                    <Settings className="w-3 h-3" />
                    Pipeline personalizado
                  </span>
                  <button
                    onClick={async () => {
                      const success = await pipelineInheritance.resetToCompanyDefault()
                      if (success) {
                        toast({ title: 'Pipeline resetado', description: 'Pipeline restaurado para o padrão da empresa.' })
                        window.location.reload()
                      }
                    }}
                    disabled={pipelineInheritance.isLoading}
                    className="inline-flex items-center gap-1 px-2 py-1 text-micro font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
                   
                  >
                    <RotateCcw className="w-3 h-3" />
                    Resetar para padrão
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-1 text-micro text-gray-400 dark:text-gray-500">
                  <Link2 className="w-3 h-3" />
                  Herdado da empresa
                </span>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* D8 — Insights Proativos (dismiss por sessão via localStorage) */}
      {proactiveInsights.length > 0 && activeTab === 'management' && (
        <div className="px-4 py-2 space-y-1.5">
          {proactiveInsights.slice(0, 3).map(insight => (
            <div
              key={insight.id}
              className={`flex items-start gap-2 px-3 py-2 rounded-md border text-xs ${
                insight.urgency === 'urgent' ? 'bg-status-error/10 border-status-error/30 text-status-error' :
                insight.urgency === 'high' ? 'bg-status-warning/10 border-status-warning/30 text-status-warning' :
                'bg-gray-50 border-gray-200 text-gray-700'
              }`}
            >
              <span className="font-medium flex-shrink-0">{insight.title}</span>
              <span className="flex-1">{insight.message}</span>
              <button
                onClick={() => dismissInsight(insight.id)}
                className="flex-shrink-0 opacity-50 hover:opacity-100"
                aria-label="Dispensar"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'edit' ? (
        <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900">
          <div className="px-4 py-4 pb-12">
            <JobEditTab
              jobEditForm={jobEditForm}
              setJobEditForm={setJobEditForm}
              onSaveSection={handleSaveJobSection}
              savingSection={savingJobSection}
              companyDefaults={companyDefaults}
              job={currentJob}
              onJobUpdate={(updatedJob) => {
                setJobEditForm((prev: any) => ({ ...prev, ...updatedJob }))
                setJobLocalOverrides((prev) => ({ ...prev, ...updatedJob }))
              }}
              onFormUpdate={(updates) => {
                setJobEditForm((prev: any) => ({ ...prev, ...updates }))
              }}
              isCreationMode={isCreationMode}
              onPublish={handlePublishJob}
              isPublishing={isPublishing}
              publicLink={publicLink}
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-hidden bg-gray-100 dark:bg-gray-900 flex flex-col min-w-0">
          {/* Pipeline Flow - Cards do Funil (apenas no modo Tabela) */}
          {viewMode === "table" && (
            <div className="flex-shrink-0 bg-white dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
              <div className="w-full">
                <div className="flex items-center gap-2">
                  {tableStageFilter.length > 0 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={clearStageFilters}
                      className="h-6 text-micro gap-1 flex-shrink-0 px-2"
                    >
                      <X className="w-3 h-3" />
                      Limpar
                    </Button>
                  )}
                  <PipelineStagesCarousel
                    stages={pipelineStages.map(stage => ({
                      id: stage.id,
                      name: stage.id,
                      displayName: stage.name,
                      count: getStageCount(stage.name),
                    }))}
                    selectedStages={tableStageFilter}
                    onStageClick={(stageId) => {
                      const stage = pipelineStages.find(s => s.id === stageId)
                      if (stage) toggleStageFilter(stage.name)
                    }}
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Bulk Actions Banner - Componente Unificado */}
          {selectedCandidates.size > 0 && (
            <div className="flex-shrink-0 px-4 py-2">
              <UnifiedBulkActionsBar
                context="vacancy"
                selectedCount={selectedCandidates.size}
                totalCount={allTableCandidates.length}
                showSelectAll={true}
                isAllSelected={selectedCandidates.size === allTableCandidates.length && allTableCandidates.length > 0}
                onSelectAll={() => {
                  if (selectedCandidates.size === allTableCandidates.length) {
                    setSelectedCandidates(new Set())
                  } else {
                    setSelectedCandidates(new Set(allTableCandidates.map(c => c.id)))
                  }
                }}
                onDeselectAll={() => setSelectedCandidates(new Set())}
                onAction={(actionId) => handleBulkAction(actionId as BulkActionType | string)}
              />
            </div>
          )}

          {/* Controles de Visualização e Filtros */}
          <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-2">
            <div className="w-full px-4 flex items-center justify-between gap-2">
              {/* Lado Esquerdo: Prompt LIA - Oculto quando prompt expandido está aberto */}
              {!showExpandedLIA && (
                <div className="flex items-center gap-2">
                  {/* Prompt LIA Compacto - Estilo padronizado */}
                  <div className="flex-shrink-0 flex-1 max-w-panel-sm">
                    <div className="relative">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2 z-10 cursor-pointer" onClick={() => setShowExpandedLIA(!showExpandedLIA)}>
                        <Brain className="w-4 h-4 text-wedo-cyan" />
                      </div>
                      <input
                        type="text"
                        placeholder="Ex: Analisar candidatos com maior fit..."
                        value={liaPromptValue}
                        onChange={(e) => setLiaPromptValue(e.target.value)}
                        className="w-full h-10 pl-10 pr-20 text-base-ui rounded-md focus:outline-none placeholder:text-gray-600 transition-all border"
                        style={{backgroundColor: 'var(--gray-50)',
                          color: 'var(--gray-950)'}}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = 'var(--gray-800)'
                          e.currentTarget.style.boxShadow = '0 0 0 2px var(--gray-600-bg-12)'
                          setShowExpandedLIA(true)
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = 'var(--gray-200)'
                          e.currentTarget.style.boxShadow = 'none'
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && liaPromptValue.trim()) {
                            handleAICommand(liaPromptValue)
                          }
                        }}
                      />
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                        <button
                          className="p-1.5 rounded-md transition-colors hover:bg-gray-100"
                          onClick={() => setShowExpandedLIA(true)}
                          title="Expandir chat"
                          aria-label="Expandir chat da LIA"
                        >
                          <Maximize2 className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        </button>
                        <button
                          className="p-1.5 rounded-md transition-colors hover:bg-gray-100"
                          onClick={() => {
                            if (liaPromptValue.trim()) {
                              handleAICommand(liaPromptValue)
                            }
                          }}
                          aria-label="Enviar mensagem para a LIA"
                        >
                          <Send className="w-4 h-4 text-gray-700" aria-hidden="true" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Ações do lado direito */}
              <div className="flex items-center gap-2">
                {/* Barra de Busca - Primeiro elemento */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" />
                  <Input
                    type="text"
                    placeholder="Buscar..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 pr-3 py-1.5 text-sm w-48"
                    aria-label="Buscar candidatos"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded-md"
                      aria-label="Limpar busca"
                    >
                      <X className="w-3 h-3 text-gray-800 dark:text-gray-200" aria-hidden="true" />
                    </button>
                  )}
                </div>

                {/* Botões de Alternância de Visualização */}
                <div className="bg-gray-100 dark:bg-gray-700 rounded-md p-0.5 flex">
                  <button
                    onClick={() => setViewMode("kanban")}
                    className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      viewMode === "kanban"
                        ? "bg-white dark:bg-gray-600 text-gray-950 dark:text-gray-50 font-bold"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <Layers3 className="w-3.5 h-3.5" />
                      Kanban
                    </div>
                  </button>
                  <button
                    onClick={() => setViewMode("table")}
                    className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${
                      viewMode === "table"
                        ? "bg-white dark:bg-gray-600 text-gray-950 dark:text-gray-50 font-bold"
                        : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                    }`}
                  >
                    <div className="flex items-center gap-1.5">
                      <ListChecks className="w-3.5 h-3.5" />
                      Tabela
                    </div>
                  </button>
                </div>

                {/* Botão Selecionar Todos - Context-aware em ambos os modos */}
                <button
                  onClick={() => {
                    // Calcular candidatos visíveis baseado no modo atual
                    let visibleCandidates = allTableCandidates
                    
                    if (viewMode === "kanban") {
                      // No Kanban, aplicar TODOS os filtros (busca + filtros Kanban)
                      visibleCandidates = allTableCandidates.filter(candidate => {
                        // Filtro de busca
                        if (searchQuery) {
                          const query = searchQuery.toLowerCase()
                          const matchesSearch = 
                            candidate.name.toLowerCase().includes(query) ||
                            candidate.role?.toLowerCase().includes(query) ||
                            candidate.company?.toLowerCase().includes(query) ||
                            candidate.location?.toLowerCase().includes(query) ||
                            candidate.currentCompany?.toLowerCase().includes(query)
                          if (!matchesSearch) return false
                        }

                        // Filtro de Score LIA Mínimo
                        if (kanbanScoreMin > 0 && candidate.score && candidate.score < kanbanScoreMin) {
                          return false
                        }

                        // Filtro de Status
                        if (kanbanStatusFilter.length > 0 && candidate.status) {
                          const candidateStatus = candidate.status.toLowerCase().replace(/ /g, '_')
                          if (!kanbanStatusFilter.includes(candidateStatus)) return false
                        }

                        // Filtro de Modelo de Trabalho
                        if (kanbanWorkModelFilter.length > 0 && candidate.workModel) {
                          const workModel = candidate.workModel.toLowerCase()
                          if (!kanbanWorkModelFilter.includes(workModel)) return false
                        }

                        if (kanbanOriginFilter.length > 0) {
                          const candidateOrigin = (candidate.origin || '').toLowerCase()
                          if (!candidateOrigin || !kanbanOriginFilter.includes(candidateOrigin)) return false
                        }

                        return true
                      })
                    } else {
                      // No Table, aplicar filtros de etapa
                      if (tableStageFilter.length > 0) {
                        visibleCandidates = allTableCandidates.filter(c => {
                          // Determinar a etapa do candidato
                          const stage = 
                            candidatesData.sourcing?.includes(c) ? 'sourcing' :
                            candidatesData.screening?.includes(c) ? 'screening' :
                            candidatesData.interview_hr?.includes(c) ? 'interview_hr' :
                            candidatesData.interview_technical?.includes(c) ? 'interview_technical' :
                            candidatesData.interview_manager?.includes(c) ? 'interview_manager' :
                            candidatesData.offer?.includes(c) ? 'offer' :
                            candidatesData.hired?.includes(c) ? 'hired' :
                            candidatesData.rejected?.includes(c) ? 'rejected' :
                            candidatesData.offer_declined?.includes(c) ? 'offer_declined' : ''
                          return tableStageFilter.includes(stage)
                        })
                      }
                    }
                    
                    if (selectedCandidates.size === visibleCandidates.length && visibleCandidates.length > 0) {
                      // Se todos visíveis já estão selecionados, desmarcar todos
                      setSelectedCandidates(new Set())
                    } else {
                      // Selecionar todos os visíveis
                      const allIds = new Set(visibleCandidates.map(c => c.id))
                      setSelectedCandidates(allIds)
                    }
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium text-gray-800 dark:text-gray-200 bg-white border border-gray-200 rounded-full hover:bg-gray-50 transition-colors"
                 
                >
                  {/* Calcular candidatos visíveis para o texto do botão */}
                  {(() => {
                    let visibleCandidates = allTableCandidates
                    if (viewMode === "kanban") {
                      // Aplicar TODOS os filtros Kanban
                      visibleCandidates = allTableCandidates.filter(candidate => {
                        // Filtro de busca
                        if (searchQuery) {
                          const query = searchQuery.toLowerCase()
                          const matchesSearch = 
                            candidate.name.toLowerCase().includes(query) ||
                            candidate.role?.toLowerCase().includes(query) ||
                            candidate.company?.toLowerCase().includes(query) ||
                            candidate.location?.toLowerCase().includes(query) ||
                            candidate.currentCompany?.toLowerCase().includes(query)
                          if (!matchesSearch) return false
                        }

                        // Filtro de Score LIA Mínimo
                        if (kanbanScoreMin > 0 && candidate.score && candidate.score < kanbanScoreMin) {
                          return false
                        }

                        // Filtro de Status
                        if (kanbanStatusFilter.length > 0 && candidate.status) {
                          const candidateStatus = candidate.status.toLowerCase().replace(/ /g, '_')
                          if (!kanbanStatusFilter.includes(candidateStatus)) return false
                        }

                        // Filtro de Modelo de Trabalho
                        if (kanbanWorkModelFilter.length > 0 && candidate.workModel) {
                          const workModel = candidate.workModel.toLowerCase()
                          if (!kanbanWorkModelFilter.includes(workModel)) return false
                        }

                        if (kanbanOriginFilter.length > 0) {
                          const candidateOrigin = (candidate.origin || '').toLowerCase()
                          if (!candidateOrigin || !kanbanOriginFilter.includes(candidateOrigin)) return false
                        }

                        return true
                      })
                    } else if (tableStageFilter.length > 0) {
                      visibleCandidates = allTableCandidates.filter(c => {
                        const stage = 
                          candidatesData.sourcing?.includes(c) ? 'sourcing' :
                          candidatesData.screening?.includes(c) ? 'screening' :
                          candidatesData.interview_hr?.includes(c) ? 'interview_hr' :
                          candidatesData.interview_technical?.includes(c) ? 'interview_technical' :
                          candidatesData.interview_manager?.includes(c) ? 'interview_manager' :
                          candidatesData.offer?.includes(c) ? 'offer' :
                          candidatesData.hired?.includes(c) ? 'hired' :
                          candidatesData.rejected?.includes(c) ? 'rejected' :
                          candidatesData.offer_declined?.includes(c) ? 'offer_declined' : ''
                        return tableStageFilter.includes(stage)
                      })
                    }
                    
                    const allSelected = selectedCandidates.size === visibleCandidates.length && visibleCandidates.length > 0
                    
                    return allSelected ? (
                      <>
                        <XCircle className="w-4 h-4 text-gray-500" />
                        Desmarcar Todos
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 text-gray-500" />
                        Selecionar Todos ({visibleCandidates.length})
                      </>
                    )
                  })()}
                </button>

                {/* Botão Filtros - Disponível em ambos os modos */}
                <button
                  onClick={() => {
                    if (viewMode === "kanban") {
                      setShowKanbanFiltersPanel(!showKanbanFiltersPanel)
                    } else {
                      setShowTableFiltersPanel(!showTableFiltersPanel)
                    }
                  }}
                  className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
                    (viewMode === "kanban" ? showKanbanFiltersPanel : showTableFiltersPanel)
                      ? 'bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200' 
                      : 'text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                 
                >
                  <Target className="w-4 h-4" />
                  Filtros
                </button>

                {viewMode === "table" && (
                  <button
                    onClick={() => setShowColumnConfig(!showColumnConfig)}
                    title="Configurar colunas da tabela"
                    className={`inline-flex items-center gap-2 px-4 py-2 text-xs font-medium rounded-full transition-colors ${
                      showColumnConfig 
                        ? 'bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200' 
                        : 'text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                   
                  >
                    <ChevronsLeftRight className="w-4 h-4" />
                    Colunas
                    <span className={`text-xs font-medium ${showColumnConfig ? 'text-gray-300' : 'text-gray-500'}`}>
                      {tableColumns.filter(col => col.visible).length}
                    </span>
                  </button>
                )}

              </div>
            </div>
          </div>

          {/* Container Principal com LIA Sidebar Unificada */}
          <div className="flex-1 flex gap-2 overflow-hidden bg-gray-50 dark:bg-gray-900 min-w-0">
            {/* Super Chat Expandido - Ocupa a maior parte da tela, deixando apenas uma coluna visível */}
            {showSuperChat && (
              <>
              <div 
                className="flex-1 transition-all duration-300 pl-4 py-4 pr-0 min-w-0"
                style={{maxWidth: 'calc(100% - 48px)'}}
              >
                <div className="h-full flex flex-col">
                  <ExpandedChatModal
                    isOpen={true}
                    onClose={() => {
                      setShowSuperChat(false)
                      setUserCollapsedLIA(true)
                    }}
                    initialMessage={liaPromptValue}
                    initialMessages={liaMessages.map(msg => ({
                      id: msg.id,
                      role: msg.type === 'user' ? 'user' : 'assistant',
                      content: msg.content,
                      timestamp: new Date(msg.timestamp)
                    }))}
                    contextTitle="Análise de Candidatos"
                    inline={true}
                    mode="general"
                    onReturnToLateral={returnToExpandedPrompt}
                    hideModeButtons={true}
                    onOrchestratedMessage={handleOrchestratedMessage}
                  />
                </div>
              </div>

              {/* Barra Vertical de Navegação - Estilo colapsado com ícones */}
              <div className="flex-shrink-0 w-12 transition-all duration-300 py-4 pr-2">
                <div className="h-[calc(100vh-12rem)] flex flex-col items-center bg-white border border-gray-200 rounded-md py-3 gap-2">
                  {/* Botão Expandir */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowSuperChat(false)}
                    className="h-8 w-8 p-0 rounded-md hover:bg-gray-100"
                    title="Expandir visualização"
                  >
                    <ChevronRight className="w-4 h-4 text-gray-500" />
                  </Button>
                  
                  <div className="w-6 h-px bg-gray-200 my-1" />
                  
                  {/* Ícone HubSpot/Integração */}
                  <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-gray-50 rounded-md px-2 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-wedo-orange flex items-center justify-center">
                      <span className="text-white text-micro font-bold">H</span>
                    </div>
                  </div>
                  
                  {/* Ícone Ações/Automação */}
                  <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-gray-50 rounded-md px-2 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-status-warning flex items-center justify-center">
                      <Brain className="w-3.5 h-3.5 text-white" />
                    </div>
                  </div>
                  
                  <div className="flex-1" />
                  
                  {/* Candidatos - Texto Vertical */}
                  <div 
                    className="flex flex-col items-center gap-1 py-3 cursor-pointer hover:bg-gray-50 rounded-md px-1 transition-colors border-r-2 border-gray-900 dark:border-gray-50"
                    onClick={() => setShowSuperChat(false)}
                  >
                    <Users className="w-4 h-4 text-gray-600" />
                    <span 
                      className="text-micro font-medium text-gray-600 tracking-wide"
                      style={{writingMode: 'vertical-rl', textOrientation: 'mixed'}}
                    >
                      Candidatos ({Object.values(candidatesData).flat().length})
                    </span>
                  </div>
                </div>
              </div>
            </>
            )}

            {/* LIA Sidebar Unificada - Visível em ambos os modos (Kanban e Tabela) */}
            {showExpandedLIA && !showSuperChat && (
              <KanbanLIASidebar
                liaMessages={liaMessages}
                liaPromptValue={liaPromptValue}
                isLiaLoading={isLiaLoading}
                liaExpandedWidth={liaExpandedWidth}
                computedSuggestions={computedSuggestions}
                showLiaSuggestionsPanel={showLiaSuggestionsPanel}
                selectedCandidates={selectedCandidates}
                isResizingLIA={isResizingLIA}
                candidatesData={candidatesData}
                chatScrollRef={chatScrollRef}
                setLiaMessages={setLiaMessages}
                setLiaPromptValue={setLiaPromptValue}
                setLiaExpandedWidth={setLiaExpandedWidth}
                setShowExpandedLIA={setShowExpandedLIA}
                setUserCollapsedLIA={setUserCollapsedLIA}
                setShowLiaSuggestionsPanel={setShowLiaSuggestionsPanel}
                setSelectedCandidates={setSelectedCandidates}
                setIsResizingLIA={setIsResizingLIA}
                setSelectedCandidate={setSelectedCandidate}
                setShowCandidatePage={setShowCandidatePage}
                openSuperChat={openSuperChat}
                handleAICommand={handleAICommand}
                handleLiaUiAction={handleLiaUiAction}
              />
            )}

            {/* Visualização Kanban */}
            {viewMode === "kanban" && !showSuperChat && (
              <>
              {/* Painel de Filtros - KANBAN */}
              <KanbanFiltersPanel
                open={showKanbanFiltersPanel}
                onClose={() => setShowKanbanFiltersPanel(false)}
                scoreMin={kanbanScoreMin}
                onScoreMinChange={setKanbanScoreMin}
                statusFilter={kanbanStatusFilter}
                onStatusFilterChange={setKanbanStatusFilter}
                originFilter={kanbanOriginFilter}
                onOriginFilterChange={setKanbanOriginFilter}
                workModelFilter={kanbanWorkModelFilter}
                onWorkModelFilterChange={setKanbanWorkModelFilter}
              />

              <div className="flex-1 overflow-x-auto overflow-y-hidden" suppressHydrationWarning>
                <div className="p-4 h-full" suppressHydrationWarning>
                  {(!hasMounted || isLoadingCandidates) ? (
                    <div className="flex gap-3 h-full min-w-max" suppressHydrationWarning>
                      {dynamicStages.map((stage) => (
                        <div key={stage.id} className="flex flex-col flex-1 bg-white rounded-md min-w-[250px] max-w-[320px] border border-gray-200 h-[calc(100vh-16rem)]" suppressHydrationWarning>
                          <div className="flex-shrink-0 p-2.5 pb-1.5">
                            <div className="flex items-center gap-1.5">
                              <div className="w-2 h-2 rounded-full animate-pulse" style={{backgroundColor: stage.color}}></div>
                              <h3 className="font-medium text-xs text-gray-400">{stage.displayName}</h3>
                              <span className="text-micro text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full animate-pulse">...</span>
                            </div>
                          </div>
                          <div className="flex-1 flex items-center justify-center">
                            <div className="animate-pulse text-gray-400 text-xs" suppressHydrationWarning>Carregando...</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (() => {
                    const totalCandidates = Object.values(candidatesData).reduce(
                      (sum, arr) => sum + (arr?.length || 0), 0
                    )
                    if (totalCandidates === 0) {
                      return (
                        <EmptyState
                          icon={<Users />}
                          title="Nenhum candidato neste pipeline ainda"
                          description="Adicione candidatos ou busque no banco de talentos para iniciar o processo."
                          action={{
                            label: "Buscar candidatos",
                            onClick: () => setShowAddToVacancyModal(true),
                          }}
                          className="h-64"
                        />
                      )
                    }
                    return (
                    <div
                      className="flex gap-3 h-full min-w-max"
                      key={`kanban-${dynamicStages.map(s => candidatesData[s.id]?.length || 0).join('-')}`}
                      suppressHydrationWarning
                    >
                      {dynamicStages.map(stage => (
                        <React.Fragment key={stage.id}>
                          {renderKanbanColumn(stage.id, candidatesData[stage.id] || [], '', '')}
                        </React.Fragment>
                      ))}
                      <div className="flex-shrink-0 w-[280px]">
                        <div 
                          className="h-full min-h-[200px] rounded-md border-2 border-dashed border-gray-300 hover:border-gray-400 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all hover:bg-gray-50/50 group"
                          onClick={() => setShowAddColumnPopover(true)}
                        >
                          <div className="w-10 h-10 rounded-full bg-gray-100 group-hover:bg-gray-200 flex items-center justify-center transition-colors">
                            <Plus className="w-5 h-5 text-gray-400 group-hover:text-gray-600" />
                          </div>
                          <span className="text-xs text-gray-400 group-hover:text-gray-600 font-medium transition-colors">
                            Adicionar Coluna
                          </span>
                        </div>
                      </div>
                      <AddColumnPopover
                        isOpen={showAddColumnPopover}
                        onClose={() => setShowAddColumnPopover(false)}
                        dynamicStages={dynamicStages}
                        isAddingColumn={isAddingColumn}
                        onSetIsAddingColumn={setIsAddingColumn}
                        onAddStage={(stage) => {
                          setDynamicStages(prev => {
                            const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                            const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                            return [...activeStages, stage, ...finalStages]
                          })
                          setCandidatesData(prev => ({ ...prev, [stage.id]: [] }))
                        }}
                      />
                    </div>
                  )
                  })()}
                </div>
              </div>

              {/* Preview do Candidato - Painel Lateral Direito (KANBAN) */}
              {isPreviewOpen && previewCandidate && (
                <div className={`flex-shrink-0 transition-all duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-panel-lg'}`}>
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 h-[calc(100vh-6rem)] overflow-hidden">
                  <CandidatePreview
                    candidate={previewCandidate}
                    isOpen={isPreviewOpen}
                    onClose={handleClosePreview}
                    isMaximized={isPreviewMaximized}
                    onToggleMaximize={handleTogglePreviewMaximize}
                    candidates={(() => {
                      const data = candidatesData as Record<string, any[]>
                      const currentColumn = Object.keys(data).find(col => 
                        data[col].some((c: any) => c.id === previewCandidate?.id)
                      )
                      return currentColumn ? data[currentColumn] : []
                    })()}
                    currentIndex={(() => {
                      const data = candidatesData as Record<string, any[]>
                      const currentColumn = Object.keys(data).find(col => 
                        data[col].some((c: any) => c.id === previewCandidate?.id)
                      )
                      return currentColumn ? data[currentColumn].findIndex((c: any) => c.id === previewCandidate?.id) : 0
                    })()}
                    onNavigateCandidate={handleNavigateCandidate}
                    onOpenFullPage={handleCandidatePageOpen}
                    onScheduleInterview={handleScheduleInterview}
                    onAddToVacancy={handleAddToVacancy}
                    onToggleFavorite={handleToggleFavorite}
                    onWSIScreening={handleSendWSIInvite}
                    onOpenTriagemDetails={handleOpenTriagem}
                    isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id) : false}
                    onSendEmail={(candidate) => handleSendEmail(candidate)}
                    onSendWhatsApp={(candidate) => handleSendWhatsApp(candidate)}
                    onSendTriagem={(candidate) => handleSendTriagem(candidate)}
                    onSendAgendamento={(candidate) => handleSendAgendamento(candidate)}
                    onSendFeedback={(candidate) => handleSendFeedback(candidate)}
                    jobId={jobData.id?.toString()}
                  />
                  </div>
                </div>
              )}
              </>
            )}

            {/* Visualização em Tabela */}
            {viewMode === "table" && !showSuperChat && (
              <KanbanTableView
                showSuperChat={showSuperChat}
                showTableFiltersPanel={showTableFiltersPanel}
                onShowTableFiltersPanelChange={setShowTableFiltersPanel}
                dynamicStages={dynamicStages}
                tableStageFilter={tableStageFilter}
                onTableStageFilterChange={setTableStageFilter}
                tableSortColumn={tableSortColumn}
                tableSortDirection={tableSortDirection}
                onSortChange={(config) => {
                  setTableSortColumn(config.field)
                  setTableSortDirection(config.direction)
                }}
                currentPage={currentPage}
                onCurrentPageChange={setCurrentPage}
                getPaginatedCandidates={getPaginatedCandidates}
                showColumnConfig={showColumnConfig}
                onShowColumnConfigChange={setShowColumnConfig}
                tableColumns={tableColumns}
                onTableColumnsChange={setTableColumns}
                selectedCandidates={selectedCandidates}
                onSelectionChange={setSelectedCandidates}
                jobVacancyId={jobData?.id?.toString()}
                saturationData={saturationData}
                onColumnResize={handleTableColumnResize}
                onCandidateClick={handleOpenPreview}
                onStatusChange={handleInteractiveStatusChange}
                onTransitionRequest={handleTableTransitionRequest}
                onTransitionRequired={handleTransitionRequired}
                calculateNotaLiaGeral={calculateNotaLiaGeral}
                getLiaAlerts={getLiaAlerts}
                viewedCandidateIds={viewedCandidateIds}
                onOpenTriagem={handleOpenTriagem}
                onOpenAnalysis={handleOpenAnalysis}
                onSetSelectedCandidateForModal={setSelectedCandidateForModal}
                onSetActiveModal={setActiveModal}
                onSetShowBigFiveModal={setShowBigFiveModal}
                onSetScoreModalCandidate={setScoreModalCandidate}
                getDataRequestForCandidate={getDataRequestForCandidate}
                onDataRequestResend={handleDataRequestResend}
                onDataRequestViewDetails={handleDataRequestViewDetails}
                onApproveFromScreening={handleApproveFromScreening}
                onRejectFromScreening={handleRejectFromScreening}
                onApproveCandidate={handleApproveCandidate}
                onRejectCandidate={handleRejectCandidate}
                openDecisionFlowModal={openDecisionFlowModal}
                onSetTransitionInitialPrompt={setTransitionInitialPrompt}
                onSetTransitionAllowStageSelection={setTransitionAllowStageSelection}
                onSetTransitionInterviewAlert={setTransitionInterviewAlert}
                openTransition={openTransition}
                isPreviewOpen={isPreviewOpen}
                previewCandidate={previewCandidate}
                isPreviewMaximized={isPreviewMaximized}
                onClosePreview={handleClosePreview}
                onTogglePreviewMaximize={handleTogglePreviewMaximize}
                onNavigateCandidate={handleNavigateCandidate}
                onCandidatePageOpen={handleCandidatePageOpen}
                onScheduleInterview={handleScheduleInterview}
                onAddToVacancy={handleAddToVacancy}
                onToggleFavorite={handleToggleFavorite}
                favoriteCandidates={favoriteCandidates}
                onSendWSIInvite={handleSendWSIInvite}
                onSendEmail={handleSendEmail}
                onSendWhatsApp={handleSendWhatsApp}
                onSendTriagem={handleSendTriagem}
                onSendAgendamento={handleSendAgendamento}
                onSendFeedback={handleSendFeedback}
                candidatesData={candidatesData}
              />
            )}
          </div>
        </div>
      )}

      {/* Página Completa do Candidato */}
      {showCandidatePage && previewCandidate && (
        <CandidatePage
          candidate={previewCandidate}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={handleCloseCandidatePage}
        />
      )}

      {/* Modal de Detalhes da Triagem */}
      {isTriagemOpen && triagemCandidate && (
        <TriagemDetailsModal
          candidate={triagemCandidate}
          isOpen={isTriagemOpen}
          onClose={handleCloseTriagem}
          onApprove={handleTriagemApprove}
          onReject={handleTriagemReject}
        />
      )}

      {/* Modal da Biblioteca de Testes */}
      <TestLibraryModal
        open={showTestLibrary}
        onClose={() => setShowTestLibrary(false)}
        onTestPreview={() => setShowTestPreview(true)}
        onTestHistoryOpen={(testName) => { setSelectedTestForHistory(testName); setShowTestHistory(true) }}
      />

      {/* Modal de Histórico do Teste */}
      <TestHistoryModal
        open={showTestHistory}
        onClose={() => setShowTestHistory(false)}
        testName={selectedTestForHistory}
      />

      {/* Painel Lateral de Sugestões da LIA */}
      <LIAQuestionsPanel open={showLiaSuggestions} onClose={() => setShowLiaSuggestions(false)} />

      {/* Modal de Preview do Teste para Candidato */}
      <TestPreviewModal open={showTestPreview} onClose={() => setShowTestPreview(false)} />

      {/* Painel Lateral de Sugestões da LIA para Triagem */}
      <LIASuggestionsPanel open={showTriagemSuggestions} onClose={() => setShowTriagemSuggestions(false)} selectedTriagemQuestion={selectedTriagemQuestion} />

      {/* Modal de Relatório */}
      {showReport && currentJob && (
        <JobReportModal
          job={currentJob}
          isOpen={showReport}
          onClose={handleCloseReport}
        />
      )}

      {/* Modal de Email */}
      {emailCandidate && showEmailModal && (
        <SendEmailModal
          isOpen={showEmailModal}
          onClose={() => {
            setShowEmailModal(false)
            setEmailCandidate(null)
          }}
          candidate={{
            id: String(emailCandidate.id),
            name: emailCandidate.name || '',
            email: emailCandidate.email || `${(emailCandidate.name || 'candidato')?.toLowerCase().replace(/\s+/g, '.')}@email.com`,
            current_title: emailCandidate.role || emailCandidate.current_title || '',
            current_company: emailCandidate.currentCompany || emailCandidate.current_company || '',
            location_city: emailCandidate.location?.split(',')[0]?.trim() || emailCandidate.location_city || '',
            location_state: emailCandidate.location?.split(',')[1]?.trim() || emailCandidate.location_state || '',
          } as any}
          onSuccess={() => {
            setShowEmailModal(false)
            setEmailCandidate(null)
          }}
        />
      )}

      {/* Unified Communication Modal */}
      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? {
          id: unifiedModalCandidate.id,
          name: unifiedModalCandidate.name,
          role: unifiedModalCandidate.role || unifiedModalCandidate.current_title || '',
          email: unifiedModalCandidate.email,
          phone: unifiedModalCandidate.phone,
          location: unifiedModalCandidate.location,
          avatar: unifiedModalCandidate.avatar,
          score: unifiedModalCandidate.score || unifiedModalCandidate.fitScore,
          matchPercentage: unifiedModalCandidate.score || unifiedModalCandidate.fitScore,
          skills: unifiedModalCandidate.skills
        } : null}
        type={unifiedModalType}
        situation={unifiedModalSituation}
        companyId="demo"
        selectedCandidates={
          !unifiedModalCandidate && selectedCandidates.size > 0
            ? Array.from(selectedCandidates).map(id => {
                const allCandidates = [
                  ...(candidatesData.sourcing || []),
                  ...(candidatesData.screening || []),
                  ...(candidatesData.interview_hr || []),
                  ...(candidatesData.interview_technical || []),
                  ...(candidatesData.interview_manager || []),
                  ...(candidatesData.offer || []),
                  ...(candidatesData.hired || []),
                  ...(candidatesData.rejected || []),
                  ...(candidatesData.offer_declined || [])
                ]
                const candidate = allCandidates.find(c => c.id === id)
                return {
                  id,
                  name: candidate?.name || 'Candidato',
                  email: candidate?.email,
                  phone: candidate?.phone,
                  avatar: candidate?.avatar
                }
              })
            : []
        }
      />

      {/* Modal Adicionar à Lista */}
      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => setShowAddToListModal(false)}
        candidateIds={Array.from(selectedCandidates)}
        onSuccess={() => {
          setShowAddToListModal(false)
          setSelectedCandidates(new Set())
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à lista com sucesso!",
          })
        }}
      />

      {/* WSI Text Screening Modal */}
      {showWSIModal && wsiCandidate && (
        <WSITextScreeningModal
          isOpen={showWSIModal}
          onClose={() => {
            setShowWSIModal(false)
            setWsiCandidate(null)
          }}
          candidate={wsiCandidate}
          jobVacancyId={jobData.id?.toString()}
          jobTitle={jobData.title}
        />
      )}

      {/* WSI Triagem Invite Modal */}
      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate}
        jobTitle={currentJob.title}
        jobId={currentJob.id?.toString()}
        screeningQuestions={
          currentJob.screening_questions && currentJob.screening_questions.length > 0
            ? currentJob.screening_questions.map((q: any, idx: number) => ({
                id: q.id || `q-${idx}`,
                question: q.question || q.text || q,
                category: q.category || q.type || 'Triagem',
                bloomLevel: q.bloom_level || q.bloomLevel
              }))
            : [
                ...perguntasEliminatorias.map((q, idx) => ({
                  id: `elim-${idx}`,
                  question: q,
                  category: 'Eliminatória'
                })),
                ...perguntasInformativas.map((q, idx) => ({
                  id: `info-${idx}`,
                  question: q,
                  category: 'Informativa'
                })),
                ...perguntasTecnicasAvaliacao.map((q, idx) => ({
                  id: `tech-${idx}`,
                  question: q,
                  category: 'Técnica/Avaliação'
                }))
              ]
        }
      />

      {/* Add to Vacancy Modal */}
      <AddCandidatesToVacancyModal
        isOpen={showAddToVacancyModal}
        onClose={() => {
          setShowAddToVacancyModal(false)
          setCandidateForVacancy(null)
        }}
        candidateIds={candidateForVacancy ? [candidateForVacancy.id] : []}
        candidateNames={candidateForVacancy ? [candidateForVacancy.name] : []}
        currentRecruiterEmail={user?.email}
        onSuccess={() => {
          toast({
            title: "Candidato adicionado",
            description: "Candidato adicionado à vaga com sucesso"
          })
        }}
      />

      {/* Rubric Evaluation Modal */}
      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={handleRubricModalClose}
        evaluation={rubricEvaluationData}
        candidateId={rubricCandidate?.id || ''}
        candidateName={rubricCandidate?.name}
        jobId={jobData?.id?.toString() || ''}
        onApprove={async (candidateId: string, jobId: string) => {
          if (rubricCandidate) {
            await handleApproveCandidate(rubricCandidate)
            handleRubricModalClose()
          }
        }}
        onReject={async (candidateId: string, jobId: string) => {
          if (rubricCandidate) {
            await handleRejectCandidate(rubricCandidate)
            handleRubricModalClose()
          }
        }}
      />

      {/* Big Five Modal */}
      <BigFiveModal
        isOpen={showBigFiveModal}
        onClose={() => {
          setShowBigFiveModal(false)
          setSelectedCandidateForModal(null)
          setScoreModalCandidate(null)
        }}
        candidate={selectedCandidateForModal || scoreModalCandidate}
      />

      {decisionFlowCandidate && (
        <CandidateDecisionFlowModal
          isOpen={showDecisionFlowModal}
          onClose={() => {
            setShowDecisionFlowModal(false)
            setDecisionFlowCandidate(null)
          }}
          candidate={{
            id: decisionFlowCandidate.id,
            name: decisionFlowCandidate.name,
            role: decisionFlowCandidate.role || decisionFlowCandidate.cargo,
            currentCompany: decisionFlowCandidate.currentCompany || decisionFlowCandidate.empresa,
            avatar: decisionFlowCandidate.avatar,
            email: decisionFlowCandidate.email,
            phone: decisionFlowCandidate.phone || decisionFlowCandidate.telefone,
            hasWhatsApp: decisionFlowCandidate.hasWhatsApp !== false,
            stage: decisionFlowCandidate.stage || decisionFlowCandidate.etapa,
          }}
          flowType={decisionFlowType}
          onConfirm={handleDecisionFlowConfirm}
          onOpenFeedbackModal={(candidate) => {
            setUnifiedModalCandidate(decisionFlowCandidate)
            setUnifiedModalType('feedback')
            setUnifiedModalSituation('feedback_construtivo')
            setUnifiedModalOpen(true)
            handleRejectCandidate(decisionFlowCandidate)
          }}
        />
      )}

      {/* Modal de Seleção de Status (Movimentação no Kanban) */}
      {statusModalOpen && pendingMove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={cancelMove}
          />
          <div 
            className="relative bg-white dark:bg-gray-900 rounded-md w-full max-w-md mx-4 overflow-hidden border border-gray-200 dark:border-gray-700"
           
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                  <ArrowRight className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                    Confirmar Movimentação
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Selecione o status detalhado
                  </p>
                </div>
              </div>
              <button
                onClick={cancelMove}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-5">
              {/* Candidato Info */}
              <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={pendingMove.candidate.avatar} alt={pendingMove.candidate.name} />
                  <AvatarFallback>{pendingMove.candidate.name?.split(' ').map((n: string) => n[0]).join('') || 'C'}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-gray-950 dark:text-gray-50">{pendingMove.candidate.name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{pendingMove.candidate.role || pendingMove.candidate.cargo || 'Candidato'}</p>
                </div>
              </div>

              {/* Transição de Etapa */}
              <div className="flex items-center gap-3 justify-center">
                <div className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {getStageDisplayName(pendingMove.fromColumn)}
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
                <div className="px-3 py-2 bg-gray-900 rounded-md">
                  <span className="text-sm font-medium text-white">
                    {getStageDisplayName(pendingMove.toColumn)}
                  </span>
                </div>
              </div>

              {/* Status Sugerido pela LIA */}
              {getSuggestedSubStatus(pendingMove.toColumn) && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Status Sugerido pela LIA
                  </label>
                  <div 
                    className={`p-3 rounded-md border-2 cursor-pointer transition-all ${
                      selectedSubStatus === getSuggestedSubStatus(pendingMove.toColumn)
                        ? 'bg-gray-100 dark:bg-gray-800 border-gray-900 dark:border-gray-50'
 : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 hover:border-gray-300 dark:border-gray-600'
                    }`}
                    onClick={() => setSelectedSubStatus(getSuggestedSubStatus(pendingMove.toColumn))}
                  >
                    <Badge 
                      className="text-sm px-3 py-1 font-medium border-0 text-gray-950 bg-gray-900"
                    >
                      {getAvailableSubStatuses(pendingMove.toColumn).find(s => s.name === getSuggestedSubStatus(pendingMove.toColumn))?.displayName || getSuggestedSubStatus(pendingMove.toColumn)}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Seleção Manual de Status */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Selecionar outro status
                </label>
                <Select 
                  value={selectedSubStatus} 
                  onValueChange={setSelectedSubStatus}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Selecione um status" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {getAvailableSubStatuses(pendingMove.toColumn).map((status) => {
                      const colors = getSubStatusColor(status)
                      return (
                        <SelectItem 
                          key={status.name} 
                          value={status.name}
                          className="cursor-pointer"
                        >
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-sm font-medium ${colors.bg} ${colors.text}`}>
                            {status.displayName}
                          </span>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <Button
                variant="outline"
                onClick={cancelMove}
                className="px-4"
              >
                Cancelar
              </Button>
              <Button
                onClick={confirmMove}
                disabled={!selectedSubStatus}
                className="px-4 text-white bg-gray-900 hover:bg-gray-800"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Confirmar
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Avaliação (Nota Geral, Triagem, Testes) */}
      {activeModal && selectedCandidateForModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => {
              setActiveModal(null)
              setSelectedCandidateForModal(null)
            }}
          />
          <div 
            className="relative bg-white dark:bg-gray-900 rounded-md w-full max-w-2xl mx-4 max-h-[85vh] overflow-hidden border border-gray-200 dark:border-gray-700"
           
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-3">
                {activeModal === 'notaGeral' && <BrainCircuit className="w-5 h-5 text-gray-950 dark:text-gray-50" />}
                {activeModal === 'triagem' && <BrainCircuit className="w-5 h-5 text-wedo-cyan" />}
                {activeModal === 'testeTecnico' && <FileText className="w-5 h-5 text-gray-700" />}
                {activeModal === 'testeIngles' && <Languages className="w-5 h-5 text-gray-700" />}
                <div>
                  <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                    {activeModal === 'notaGeral' && 'Nota Geral'}
                    {activeModal === 'triagem' && 'Nota Triagem'}
                    {activeModal === 'testeTecnico' && 'Teste Técnico'}
                    {activeModal === 'testeIngles' && 'Teste Inglês'}
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedCandidateForModal.name}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)]">
              {/* Nota Geral */}
              {activeModal === 'notaGeral' && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
                      <span className="text-4xl font-bold text-gray-950 dark:text-gray-50">
                        {calculateNotaLiaGeral(selectedCandidateForModal)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Pontuação Geral do Candidato</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                      <p className="text-xs text-gray-500 mb-1">Nota Triagem</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {formatScorePercent(selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                      <p className="text-xs text-gray-500 mb-1">Nota CV</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {formatScorePercent(selectedCandidateForModal.skillsMatch || selectedCandidateForModal.fitScore || 0, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                      <p className="text-xs text-gray-500 mb-1">Teste Técnico</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {selectedCandidateForModal.technicalTestScore !== null && selectedCandidateForModal.technicalTestScore !== undefined 
                          ? formatScorePercent(selectedCandidateForModal.technicalTestScore, 0) 
                          : '—'}
                      </p>
                    </div>
                    <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                      <p className="text-xs text-gray-500 mb-1">Teste Inglês</p>
                      <p className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                        {selectedCandidateForModal.englishTestScore !== null && selectedCandidateForModal.englishTestScore !== undefined 
                          ? formatScorePercent(selectedCandidateForModal.englishTestScore, 0) 
                          : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Triagem */}
              {activeModal === 'triagem' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: 'var(--gray-100)'}}
                    >
                      <span className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                        {formatScorePercent(selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Score de Triagem LIA</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                    <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Análise da LIA</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      Candidato avaliado automaticamente pela LIA com base em critérios de experiência, 
                      competências e aderência ao perfil da vaga. A triagem considera fatores como 
                      histórico profissional, formação acadêmica e habilidades técnicas declaradas.
                    </p>
                  </div>
                </div>
              )}

              {/* Teste Técnico */}
              {activeModal === 'testeTecnico' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: selectedCandidateForModal.technicalTestScore >= 80 ? 'var(--status-success)' :
                                         selectedCandidateForModal.technicalTestScore >= 60 ? 'var(--status-warning)' :
                                         selectedCandidateForModal.technicalTestScore >= 40 ? 'var(--gray-400)' :
                                         'var(--gray-400)'}}
                    >
                      <span className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                        {formatScorePercent(selectedCandidateForModal.technicalTestScore, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Resultado do Teste Técnico</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                    <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Detalhes do Teste</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      Avaliação técnica realizada através de teste prático com foco nas competências 
                      técnicas requeridas para a posição. Inclui análise de código, resolução de 
                      problemas e conhecimento de ferramentas específicas.
                    </p>
                  </div>
                </div>
              )}

              {/* Teste Inglês */}
              {activeModal === 'testeIngles' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: selectedCandidateForModal.englishTestScore >= 80 ? 'var(--status-success)' :
                                         selectedCandidateForModal.englishTestScore >= 60 ? 'var(--gray-300)' :
                                         selectedCandidateForModal.englishTestScore >= 40 ? 'var(--gray-400)' :
                                         'var(--gray-400)'}}
                    >
                      <span className="text-3xl font-bold text-gray-950 dark:text-gray-50">
                        {formatScorePercent(selectedCandidateForModal.englishTestScore, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">Resultado do Teste de Inglês</p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-md">
                    <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Nível de Proficiência</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                      Avaliação de proficiência em inglês cobrindo compreensão escrita, 
                      expressão oral e vocabulário técnico relevante para a posição.
                    </p>
                  </div>
                </div>
              )}

            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="px-4 py-2 text-sm font-medium text-gray-800 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modais de Scores */}
      <GeneralScoreModal
        isOpen={showGeneralScoreModal}
        onClose={() => setShowGeneralScoreModal(false)}
        candidate={scoreModalCandidate}
      />
      <TechnicalTestModal
        isOpen={showTechnicalTestModal}
        onClose={() => setShowTechnicalTestModal(false)}
        candidate={scoreModalCandidate}
      />
      <EnglishTestModal
        isOpen={showEnglishTestModal}
        onClose={() => setShowEnglishTestModal(false)}
        candidate={scoreModalCandidate}
      />

      {/* D9 — Modal de Análise Comparativa */}
      <CandidateCompareModal
        open={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        candidates={compareCandidates}
        jobId={_jobIdForSL}
        companyId={_companyIdForSL}
      />

      {/* D9-G1 — Botão flutuante de comparação (aparece quando 2+ candidatos selecionados) */}
      {selectedForCompare.size >= 2 && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2">
          <button
            className="flex items-center gap-2 bg-gray-900 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-700 transition-colors shadow-lg"
            onClick={() => {
              const selectedIds = Array.from(selectedForCompare)
              const resolvedCandidates = allTableCandidates
                .filter(c => selectedIds.includes(c.id))
                .map(c => ({ id: c.id, name: c.name }))
              setCompareCandidates(resolvedCandidates)
              setShowCompareModal(true)
              setSelectedForCompare(new Set())
            }}
          >
            <span>Comparar ({selectedForCompare.size})</span>
          </button>
          <button
            className="bg-white border border-gray-200 text-gray-600 px-3 py-2 rounded-md text-sm hover:bg-gray-50 transition-colors shadow-lg"
            onClick={() => setSelectedForCompare(new Set())}
            aria-label="Limpar seleção de comparação"
          >
            ✕
          </button>
        </div>
      )}

      {/* UniversalTransitionModal - Modal universal para transições de etapa */}
      <UniversalTransitionModal
        isOpen={universalModalState.isOpen}
        onClose={() => { closeTransition(); setTransitionInitialPrompt(undefined); setTransitionAllowStageSelection(false); setTransitionInterviewAlert(null); }}
        candidates={universalModalState.candidates}
        fromStage={universalModalState.fromStage}
        toStage={universalModalState.toStage}
        toStageDisplayName={universalModalState.toStageDisplayName}
        actionBehavior={universalModalState.actionBehavior}
        subStatusOptions={universalModalState.subStatusOptions}
        onConfirm={handleUniversalTransitionConfirm}
        onOpenSpecializedModal={handleOpenSpecializedModal}
        companyId={user?.company}
        jobTitle={job?.title}
        initialPrompt={transitionInitialPrompt}
        availableStages={dynamicStages.map(s => ({ id: s.id, displayName: s.displayName, actionBehavior: s.actionBehavior }))}
        allowStageSelection={transitionAllowStageSelection}
        interviewAlert={transitionInterviewAlert ?? undefined}
      />

      {/* DataRequestModal - Modal para solicitar dados do candidato */}
      {showDataRequestModal && dataRequestModalCandidate && (
        <DataRequestModal
          isOpen={showDataRequestModal}
          onClose={() => {
            setShowDataRequestModal(false)
            setDataRequestModalCandidate(null)
          }}
          candidates={[{
            id: dataRequestModalCandidate.id,
            name: dataRequestModalCandidate.name,
            email: dataRequestModalCandidate.email,
            phone: dataRequestModalCandidate.phone,
            avatar: dataRequestModalCandidate.avatar
          }]}
          jobTitle={job?.title}
          onSubmit={handleDataRequestSubmit}
        />
      )}

      {/* BulkActionModal - Modal para ações em lote */}
      {showBulkActionModal && (
        <BulkActionModal
          isOpen={showBulkActionModal}
          onClose={() => setShowBulkActionModal(false)}
          actionType={bulkActionType}
          candidates={allTableCandidates
            .filter(c => selectedCandidates.has(c.id))
            .map(c => ({
              id: c.id,
              name: c.name || '',
              email: c.email,
              avatar: c.avatar || c.avatar_url,
              currentStage: c.stage
            }))}
          stages={dynamicStages.map(s => ({
            name: s.name,
            displayName: s.displayName,
            stageOrder: s.order,
            color: s.color,
            stageType: s.stageType,
            isInitial: s.isInitial,
            isFinal: s.isFinal,
            isHired: s.isHired,
            isRejection: s.isRejection,
            icon: (s as any).icon || '',
            stageCategory: (s as any).stageCategory || 'active',
            allowedTransitions: (s as any).allowedTransitions || []
          }))}
          jobTitle={job?.title}
          onExecute={handleBulkActionExecute}
        />
      )}

      {/* JobStatusModal — Pausar / Reativar Vaga (T5) */}
      {showJobStatusModal && (
        <JobStatusModal
          isOpen={showJobStatusModal}
          onClose={() => setShowJobStatusModal(false)}
          jobs={[{
            id: String(currentJob.backendId || currentJob.jobId || currentJob.id),
            title: currentJob.title || '',
            status: currentJob.status || '',
            candidates_count: Object.values(candidatesData).flat().length,
          }]}
          candidates={Object.entries(candidatesData)
            .filter(([stageId]) => !['hired', 'rejected', 'offer_declined'].includes(stageId))
            .flatMap(([stageId, cands]: [string, any[]]) =>
              (cands as any[]).map((c: any) => ({
                id: String(c.id),
                name: c.name || 'Candidato',
                email: c.email,
                phone: c.phone,
                stage: stageId,
                jobId: String(currentJob.backendId || currentJob.jobId || currentJob.id),
              }))
            )}
          mode={jobStatusModalMode}
          onStatusChange={(_jobIds, newStatus) => {
            setJobEditForm((prev: any) => ({ ...prev, status: newStatus }))
            toast({ title: newStatus === 'Paralisada' ? 'Vaga pausada com sucesso' : 'Vaga reativada com sucesso' })
            setShowJobStatusModal(false)
          }}
        />
      )}

      {/* CloseVacancyModal — Fechar Vaga com notificações (T4) */}
      {showCloseVacancyModal && (() => {
        const hiredList: any[] = candidatesData.hired || []
        const hiredCandidate = hiredList[0]
          ? { id: String(hiredList[0].id), name: hiredList[0].name || 'Candidato', email: hiredList[0].email, phone: hiredList[0].phone }
          : { id: '', name: '—', email: undefined as string | undefined, phone: undefined as string | undefined }
        const otherCandidates = Object.entries(candidatesData)
          .filter(([stageId]) => stageId !== 'hired')
          .flatMap(([stageId, cands]: [string, any[]]) =>
            (cands as any[]).map((c: any) => ({
              id: String(c.id),
              name: c.name || 'Candidato',
              email: c.email,
              phone: c.phone,
              stage: stageId,
            }))
          )
        return (
          <CloseVacancyModal
            isOpen={showCloseVacancyModal}
            onClose={() => setShowCloseVacancyModal(false)}
            vacancy={{
              id: String(currentJob.backendId || currentJob.jobId || currentJob.id),
              title: currentJob.title || '',
              department: currentJob.department,
            }}
            hiredCandidate={hiredCandidate}
            otherCandidates={otherCandidates}
            onConfirm={async () => {
              setJobEditForm((prev: any) => ({ ...prev, status: 'Encerrada' }))
              toast({ title: 'Vaga encerrada com sucesso' })
              setShowCloseVacancyModal(false)
            }}
          />
        )
      })()}

      {showPublishSuccess && publicLink && (
        <div className="fixed inset-0 bg-gray-900/50 dark:bg-gray-950/70 z-50 flex items-center justify-center" onClick={() => setShowPublishSuccess(false)}>
          <div className="bg-white dark:bg-gray-800 rounded-md shadow-xl w-full max-w-sm mx-4 animate-in fade-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 font-['Open_Sans',sans-serif]">
                Vaga Publicada!
              </h3>
            </div>
            <div className="px-6 py-4 space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400 font-['Open_Sans',sans-serif]">
                A vaga está ativa. Compartilhe o link abaixo com candidatos:
              </p>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={publicLink}
                  className="flex-1 px-3 py-2 text-xs text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md font-['Open_Sans',sans-serif] select-all"
                  onClick={e => (e.target as HTMLInputElement).select()}
                />
                <button
                  onClick={() => {
                    try {
                      navigator.clipboard.writeText(publicLink)
                      toast({
                        title: "Link copiado!",
                        description: "O link foi copiado para a área de transferência.",
                      })
                    } catch {
                      toast({
                        title: "Não foi possível copiar",
                        description: "Selecione o link manualmente e copie.",
                        variant: "destructive",
                      })
                    }
                  }}
                  className="p-2 rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-colors flex-shrink-0"
                  title="Copiar link"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setShowPublishSuccess(false)}
                className="px-4 py-2 text-sm font-medium rounded-md bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 transition-all font-['Open_Sans',sans-serif]"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Compartilhar com Gestor (H.3a) */}
      <ShareSearchModal
        open={showShareGestorModal}
        onClose={() => {
          setShowShareGestorModal(false)
        }}
        shareType="list"
        title={`Candidatos — ${currentJob?.title ?? "Vaga"}`}
        candidateIds={selectedCandidates.size > 0 ? Array.from(selectedCandidates) : allCandidateIds}
        candidateCount={selectedCandidates.size > 0 ? selectedCandidates.size : allCandidateIds.length}
        onSuccess={() => {
          setSelectedCandidates(new Set())
        }}
      />

    </div>
    </>
  )
}
