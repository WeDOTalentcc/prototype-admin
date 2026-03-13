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
import { ContextualActionsBanner } from "@/components/contextual-actions-banner"
import { AddToListModal } from "@/components/modals/add-to-list-modal"
import { WSITextScreeningModal } from "@/components/wsi/wsi-text-screening-modal"
import { WSITriagemInviteModal } from "@/components/wsi/wsi-triagem-invite-modal"
import { AddCandidatesToVacancyModal } from "@/components/modals/add-candidates-to-vacancy-modal"
import { RubricEvaluationModal } from "@/components/rubric-evaluation-modal"
import { BigFiveModal } from "@/components/big-five-modal"
import { ScoreIconButton } from "@/components/ui/score-icon-button"
import { GeneralScoreModal } from "@/components/modals/general-score-modal"
import { TechnicalTestModal } from "@/components/modals/technical-test-modal"
import { EnglishTestModal } from "@/components/modals/english-test-modal"
import { CandidateDecisionFlowModal } from "@/components/candidate-decision-flow-modal"
import { UniversalTransitionModal, useUniversalTransition, type UniversalTransitionConfirmData, type KanbanCandidate } from "@/components/kanban"
import { useAuth } from "@/components/auth-context"
import { useToast } from "@/hooks/use-toast"
import { useShortList } from "@/hooks/use-short-list"
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
import { callKanbanAssistant, callOrchestratedJobChat } from "@/lib/api/kanban-assistant"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { liaApi, CandidateLocal } from "@/services/lia-api"
import { textStyles, cardStyles, badgeStyles, buttonStyles, formatScorePercent } from "@/lib/design-tokens"
import { isClearChatCommand } from "@/lib/chat-commands"
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
import { BulkActionModal, type BulkActionCandidate, type BulkActionResult, type BulkActionExecuteData } from "@/components/modals/bulk-action-modal"
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

const CandidatePreview = dynamic(() => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })), { ssr: false })
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const ExpandedChatModal = dynamic(() => import("@/components/expanded-chat-modal").then(m => ({ default: m.ExpandedChatModal })), { ssr: false })

// Interface para etapas dinâmicas do Kanban
interface InterviewStageFromJob {
  stageName: string
  order: number
  sla?: number
  type: 'automated' | 'manual' | 'hybrid' | 'system' | 'interview' | 'test' | 'custom'
}

interface DynamicStage {
  id: string
  name: string
  displayName: string
  order: number
  color: string
  stageType: 'active' | 'final'
  isInitial?: boolean
  isFinal?: boolean
  isHired?: boolean
  isRejection?: boolean
  isActive?: boolean
  actionBehavior?: string
}

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
  '#374151', // gray-700
  '#4B5563', // gray-600
  '#6B7280', // gray-500
  '#9CA3AF', // gray-400
  '#6B7280', // gray-500
  '#4B5563', // gray-600
  '#374151', // gray-700
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
        const color = stage.color || (isIntermediate ? DYNAMIC_STAGE_COLORS[colorIndex++ % DYNAMIC_STAGE_COLORS.length] : '#374151')
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
    { id: 'screening', name: 'screening', displayName: 'Triagem', order: 1, color: '#4B5563', stageType: 'active', isInitial: false, actionBehavior: 'screening' }
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
    } catch (error: any) {
      console.error("[JobKanbanPage] Failed to publish job:", error)
      const detail = error?.message || "Erro desconhecido"
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
      console.error('Transition error:', error)
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
        console.log('Opening specialized modal:', modalType, context)
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
    console.log('Submitting data request:', data)
    toast({
      title: "Solicitação Enviada",
      description: `Solicitação de dados enviada para ${dataRequestModalCandidate?.name || 'candidato'}`,
    })
    setShowDataRequestModal(false)
    setDataRequestModalCandidate(null)
  }, [dataRequestModalCandidate, toast])

  // Handler para ações em lote
  const handleBulkAction = useCallback((actionId: BulkActionType | string) => {
    if (selectedCandidates.size === 0) return
    
    switch (actionId) {
      case 'move_stage':
      case 'reject':
        setBulkActionType(actionId as BulkActionType)
        setShowBulkActionModal(true)
        break
      case 'request_data':
        const selectedForDataRequest = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        if (selectedForDataRequest.length > 0) {
          setDataRequestModalCandidate(selectedForDataRequest[0])
          setShowDataRequestModal(true)
        }
        break
      case 'send_message':
        setUnifiedModalType('email')
        setUnifiedModalCandidate(null)
        setUnifiedModalOpen(true)
        break
      case 'wsi_screening':
        const selectedForWSI = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        if (selectedForWSI.length > 0) {
          setWsiInviteCandidate(selectedForWSI[0])
          setShowWSIInviteModal(true)
        }
        break
      case 'lia_analysis':
        const selectedForAnalysis = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        if (selectedForAnalysis.length > 0) {
          handleOpenAnalysis(selectedForAnalysis[0])
        }
        break
      case 'share_search':
        setShowShareGestorModal(true)
        break
      default:
        toast({
          title: "Ação em Lote",
          description: `Ação "${actionId}" para ${selectedCandidates.size} candidato(s)`,
        })
    }
  }, [selectedCandidates, allTableCandidates, toast])

  // Handler para executar ação em lote
  const handleBulkActionExecute = useCallback(async (data: BulkActionExecuteData): Promise<BulkActionResult[]> => {
    const results: BulkActionResult[] = []
    
    try {
      // Call backend API first for persistence
      if (data.actionType === 'move_stage' && data.targetStage) {
        // Use full stage name for backend - the API endpoint supports both status and stage
        // Backend will handle the mapping and preserve full stage information in additional_data
        const apiResult = await liaApi.bulkUpdateStatus({
          candidate_ids: data.candidateIds,
          new_status: data.targetStage
        })
        
        // Build result maps from API response
        const failedMap = new Map(apiResult.errors?.map(e => [e.id, e.error]) || [])
        const successfulIds = data.candidateIds.filter(id => !failedMap.has(id))
        
        // Update local state in a single batch for all successful candidates
        if (successfulIds.length > 0) {
          setCandidatesData(prev => {
            const newData = { ...prev }
            const movedCandidates: any[] = []
            
            // Remove candidates from their current stages
            for (const candidateId of successfulIds) {
              for (const [stageId, candidates] of Object.entries(newData)) {
                const candidateIndex = candidates.findIndex((c: any) => c.id === candidateId)
                if (candidateIndex !== -1) {
                  const candidate = { ...candidates[candidateIndex], stage: data.targetStage }
                  movedCandidates.push(candidate)
                  newData[stageId] = candidates.filter((_: any, i: number) => i !== candidateIndex)
                  break
                }
              }
            }
            
            // Add all candidates to target stage in one operation
            if (movedCandidates.length > 0 && data.targetStage) {
              if (!newData[data.targetStage]) {
                newData[data.targetStage] = []
              }
              newData[data.targetStage] = [...newData[data.targetStage], ...movedCandidates]
            }
            
            return newData
          })
        }
        
        // Build results array
        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }
        
      } else if (data.actionType === 'reject') {
        // Call backend API with rejected status
        const apiResult = await liaApi.bulkUpdateStatus({
          candidate_ids: data.candidateIds,
          new_status: 'rejected'
        })
        
        // Build result maps from API response
        const failedMap = new Map(apiResult.errors?.map(e => [e.id, e.error]) || [])
        const successfulIds = data.candidateIds.filter(id => !failedMap.has(id))
        
        // Update local state in a single batch for all successful candidates
        if (successfulIds.length > 0) {
          setCandidatesData(prev => {
            const newData = { ...prev }
            const movedCandidates: any[] = []
            
            // Remove candidates from their current stages
            for (const candidateId of successfulIds) {
              for (const [stageId, candidates] of Object.entries(newData)) {
                const candidateIndex = candidates.findIndex((c: any) => c.id === candidateId)
                if (candidateIndex !== -1) {
                  const candidate = { ...candidates[candidateIndex], stage: 'rejected', rejectionReason: data.rejectionReason }
                  movedCandidates.push(candidate)
                  newData[stageId] = candidates.filter((_: any, i: number) => i !== candidateIndex)
                  break
                }
              }
            }
            
            // Add all candidates to rejected stage in one operation
            if (movedCandidates.length > 0) {
              if (!newData['rejected']) {
                newData['rejected'] = []
              }
              newData['rejected'] = [...newData['rejected'], ...movedCandidates]
            }
            
            return newData
          })
        }
        
        // Build results array
        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }
        
      } else if (data.actionType === 'send_message') {
        // Call backend API for sending emails
        // Note: template_id should be passed via data.message or a dedicated field
        const templateId = data.message || 'default-template'
        const apiResult = await liaApi.bulkSendEmail({
          candidate_ids: data.candidateIds,
          template_id: templateId
        })
        
        const failedMap = new Map(apiResult.errors?.map(e => [e.id, e.error]) || [])
        
        for (const candidateId of data.candidateIds) {
          if (failedMap.has(candidateId)) {
            results.push({ candidateId, success: false, error: failedMap.get(candidateId) })
          } else {
            results.push({ candidateId, success: true })
          }
        }
        
      } else if (data.actionType === 'request_data') {
        // For request_data, we process each candidate individually
        // since there's no bulk endpoint for data requests
        for (const candidateId of data.candidateIds) {
          try {
            // Data request is handled via the modal flow (handleDataRequestSubmit)
            // Mark as success for now - actual request is sent via the modal
            results.push({ candidateId, success: true })
          } catch (error) {
            results.push({ candidateId, success: false, error: 'Erro ao solicitar dados' })
          }
        }
        
      } else {
        // Fallback for other action types - just mark as processed
        for (const candidateId of data.candidateIds) {
          results.push({ candidateId, success: true })
        }
      }
      
    } catch (error) {
      // API call failed - mark all candidates as failed
      const errorMessage = error instanceof Error ? error.message : 'Erro ao processar ação em lote'
      toast({
        title: "Erro",
        description: errorMessage,
        variant: "destructive"
      })
      
      for (const candidateId of data.candidateIds) {
        results.push({ candidateId, success: false, error: errorMessage })
      }
    }
    
    setSelectedCandidates(new Set())
    
    const successCount = results.filter(r => r.success).length
    const failCount = results.filter(r => !r.success).length
    
    if (successCount > 0) {
      toast({
        title: "Ação Concluída",
        description: failCount > 0 
          ? `${successCount} de ${results.length} candidatos processados com sucesso. ${failCount} falharam.`
          : `${successCount} candidato(s) processados com sucesso`,
      })
    }
    
    return results
  }, [toast])

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
    console.log('🔄 JobKanbanPage: Iniciando fetch de candidatos...')
    setIsLoadingCandidates(true)
    liaApi.listCandidates(undefined, undefined, 0, 200)
      .then(response => {
        console.log('✅ JobKanbanPage: Resposta recebida:', response?.items?.length, 'candidatos')
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
                  console.warn('⚠️ Erro ao gerar educação para', c.name, e)
                  educationData = []
                }
                
                try {
                  workHistoryData = generateWorkHistory(c, experience)
                } catch (e) {
                  console.warn('⚠️ Erro ao gerar histórico para', c.name, e)
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
                console.error('❌ Erro ao mapear candidato:', c.name, mapError)
                return null
              }
            }

            const backendCandidates = response.items
              .map(mapCandidateToKanban)
              .filter((c): c is NonNullable<typeof c> => c !== null)
            
            console.log('📊 JobKanbanPage: Candidatos mapeados:', backendCandidates.length)
            
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
            console.log('📊 JobKanbanPage: Candidatos organizados por etapas dinâmicas:', stageCounts)
            console.log('✅ JobKanbanPage: Atualizando candidatesData com dados do backend')
            setCandidatesData(newOrganizedData)
          } else {
            console.log('⚠️ JobKanbanPage: Nenhum candidato retornado do backend')
          }
        } catch (processError) {
          console.error('❌ JobKanbanPage: Erro ao processar candidatos:', processError)
        } finally {
          console.log('🏁 JobKanbanPage: Finalizando loading (finally block)')
          setIsLoadingCandidates(false)
        }
      })
      .catch(error => {
        console.error('❌ JobKanbanPage: Erro ao carregar candidatos:', error)
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
        console.error('Error loading viewed candidates:', error)
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
        console.error('Erro ao processar ação pendente:', e)
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
      console.error('Erro ao processar navigateToCandidate no Kanban:', e)
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

  const currentJob = job || jobData

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
        console.warn('WSI scores enrichment skipped:', err.message)
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

  const handleLiaUiAction = useCallback((action: string, params: Record<string, any>) => {
    if (action === 'start_job_wizard') return

    const candidateIds: string[] = params.candidate_ids || []
    const matchedCandidates = candidateIds.map(id => findCandidateById(id)).filter(Boolean)
    const firstCandidate = matchedCandidates.length > 0 ? matchedCandidates[0] : null

    if (!firstCandidate) {
      console.warn(`[LIA UI Action] No candidate found for action "${action}", ids:`, candidateIds)
      return
    }

    setTimeout(() => {
      switch (action) {
        case 'move_candidate':
        case 'approve_candidate':
          {
            const fromStage = firstCandidate.stage || ''
            const toStage = params.target_stage as string || params.to_stage as string || ''
            const kanbanCandidate: KanbanCandidate = {
              id: String(firstCandidate.id),
              name: firstCandidate.name || '',
              role: firstCandidate.role || '',
              score: firstCandidate.score || 0,
              email: firstCandidate.email,
              phone: firstCandidate.phone,
            }
            openTransition([kanbanCandidate], fromStage, toStage)
          }
          break

        case 'send_email':
          openUnifiedModal(firstCandidate, 'email')
          break

        case 'start_screening':
          if (params.screening_type === 'wsi_text') {
            setWsiCandidate(firstCandidate)
            setShowWSIModal(true)
          } else {
            setWsiInviteCandidate(firstCandidate)
            setShowWSIInviteModal(true)
          }
          break

        case 'schedule_interview':
          openUnifiedModal(firstCandidate, 'agendamento')
          break

        case 'request_data':
          setDataRequestModalCandidate(firstCandidate)
          setShowDataRequestModal(true)
          break

        case 'analyze_profile':
          setRubricCandidate(firstCandidate)
          setShowRubricModal(true)
          break

        default:
          console.warn(`[LIA UI Action] Unknown action: "${action}"`)
          break
      }
    }, 600)
  }, [findCandidateById, openUnifiedModal, openTransition])

  // Handler inteligente para comandos da LIA no contexto do Kanban - usando Orquestrador Multi-Agente
  const handleAICommand = async (command: string) => {
    if (isClearChatCommand(command)) {
      setLiaMessages([])
      setLiaPromptValue('')
      return
    }

    const timestamp = Date.now()
    const userMessage = { id: `user-${timestamp}`, type: 'user' as const, content: command, timestamp }
    
    setLiaMessages(prev => [...prev, userMessage])
    setLiaPromptValue('')
    setShowExpandedLIA(true)
    setIsLiaLoading(true)

    try {
      const jobContext = {
        id: currentJob.id,
        title: currentJob.title,
        department: currentJob.department,
        level: currentJob.level,
        requirements: currentJob.requirements,
        skills: currentJob.requirements,
        location: currentJob.location,
        salary: currentJob.salary,
        workModel: currentJob.workModel,
        deadline: currentJob.deadline
      }

      const candidatesForApi = allTableCandidates.map(c => ({
        id: c.id,
        name: c.name,
        role: c.role,
        currentCompany: c.currentCompany,
        location: c.location,
        score: c.score,
        wsiScore: c.wsiScore || c.score,
        wsiTechnical: c.wsiTechnical,
        wsiBehavioral: c.wsiBehavioral,
        fitScore: c.fitScore,
        skills: c.skills,
        experience: c.experience,
        stage: c.stage,
        subStatus: c.subStatus,
        daysInStage: c.daysInStage,
        warnings: c.warnings,
        email: c.email,
        phone: c.phone,
        bigFive: c.bigFive,
        hasCV: !!c.cvUrl
      }))

      const selectedIds = selectedCandidates.size > 0 
        ? Array.from(selectedCandidates) 
        : undefined

      const response = await callOrchestratedJobChat({
        message: command,
        job_context: jobContext,
        candidates: candidatesForApi,
        selected_candidate_ids: selectedIds,
        conversation_id: liaConversationId,
        company_id: user?.company || 'default',
      })

      if (response.success) {
        if (response.conversation_id) {
          setLiaConversationId(response.conversation_id)
        }
        
        const agentInfo = response.agents_consulted?.length > 1 
          ? `_Agentes: ${response.agents_consulted.join(', ')}_\n\n`
          : ''
        
        const responseMessage = { 
          id: `response-${timestamp}`, 
          type: 'response' as const, 
          content: agentInfo + response.content, 
          timestamp: timestamp + 1,
          metadata: {
            intent: response.intent_detected,
            confidence: response.confidence,
            agent: response.agent_used,
            suggested_prompts: response.suggested_prompts,
            actions: response.actions,
            action_executed: response.action_executed,
            action_result: response.action_result,
            action_type: response.action_type,
            needs_confirmation: response.needs_confirmation,
            needs_params: response.needs_params,
            pending_action_id: response.pending_action_id,
          }
        }
        setLiaMessages(prev => [...prev, responseMessage])
        
        if (response.action_executed && response.action_result) {
          setTimeout(() => {
            fetchCandidates()
          }, 500)
        }

        if (!response.action_executed && response.action_type && response.ui_action) {
          const fallbackMsg = {
            id: `fallback-${timestamp}`,
            type: 'response' as const,
            content: '⚠️ Não consegui executar automaticamente. Deseja tentar manualmente?',
            timestamp: timestamp + 2,
            metadata: {
              is_fallback: true,
              action_type: response.action_type,
              ui_action: response.ui_action,
              ui_action_params: response.ui_action_params,
            }
          }
          setLiaMessages(prev => [...prev, fallbackMsg])
        }
        
        if (response.ui_action === 'start_job_wizard') {
          setTimeout(() => {
            setShowSuperChat(true)
            setUserCollapsedLIA(false)
          }, 500)
        }
        
        if (!response.action_executed && response.ui_action && response.ui_action !== 'start_job_wizard') {
          const enrichedParams = { ...(response.ui_action_params || {}) }
          if (!enrichedParams.candidate_ids && response.actions?.length > 0) {
            const actionWithIds = response.actions.find((a: any) => a.candidate_ids?.length > 0)
            if (actionWithIds) {
              enrichedParams.candidate_ids = actionWithIds.candidate_ids
            }
          }
          handleLiaUiAction(response.ui_action, enrichedParams)
        }
      } else if (response.error === 'auth_error') {
        const authMsg = {
          id: `auth-error-${timestamp}`,
          type: 'response' as const,
          content: response.content || 'Sessao expirada. Recarregue a pagina para continuar.',
          timestamp: timestamp + 1,
        }
        setLiaMessages(prev => [...prev, authMsg])
      } else {
        throw new Error('API returned unsuccessful response')
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('[LIA] Orchestrator indisponivel, usando fallback:', (error as Error)?.message || error)
      }
      try {
        const jobContext = {
          title: currentJob.title,
          department: currentJob.department,
          level: currentJob.level,
          requirements: currentJob.requirements,
          skills: currentJob.requirements,
          location: currentJob.location,
          salary: currentJob.salary,
          workModel: currentJob.workModel,
          deadline: currentJob.deadline
        }
        const candidatesForApi = allTableCandidates.map(c => ({
          id: c.id,
          name: c.name,
          role: c.role,
          currentCompany: c.currentCompany,
          location: c.location,
          score: c.score,
          fitScore: c.fitScore,
          skills: c.skills,
          experience: c.experience,
          stage: c.stage,
          warnings: c.warnings,
          email: c.email,
          phone: c.phone,
          bigFive: c.bigFive
        }))
        const selectedIds = selectedCandidates.size > 0 ? Array.from(selectedCandidates) : undefined
        const fallbackResponse = await callKanbanAssistant({
          command,
          job_context: jobContext,
          candidates: candidatesForApi,
          selected_candidate_ids: selectedIds
        })
        if (fallbackResponse.success) {
          const responseMessage = { 
            id: `response-${timestamp}`, 
            type: 'response' as const, 
            content: fallbackResponse.content, 
            timestamp: timestamp + 1 
          }
          setLiaMessages(prev => [...prev, responseMessage])
          
          if (fallbackResponse.ui_action) {
            handleLiaUiAction(fallbackResponse.ui_action, fallbackResponse.ui_action_params || {})
          }
        } else {
          throw new Error('Fallback also failed')
        }
      } catch (fallbackError) {
        const fallbackContent = getFallbackResponse(command)
        const responseMessage = { 
          id: `response-${timestamp}`, 
          type: 'response' as const, 
          content: fallbackContent, 
          timestamp: timestamp + 1 
        }
        setLiaMessages(prev => [...prev, responseMessage])
      }
    } finally {
      setIsLiaLoading(false)
    }
  }

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

  // Wrapper function for orchestrated messages to pass to ExpandedChatModal
  const handleOrchestratedMessage = async (message: string): Promise<{
    content: string
    ui_action?: string | null
    ui_action_params?: Record<string, unknown>
  }> => {
    const jobContext = {
      id: currentJob.id,
      title: currentJob.title,
      department: currentJob.department,
      level: currentJob.level,
      requirements: currentJob.requirements,
      skills: currentJob.requirements,
      location: currentJob.location,
      salary: currentJob.salary,
      workModel: currentJob.workModel,
      deadline: currentJob.deadline
    }

    const candidatesForApi = allTableCandidates.map(c => ({
      id: c.id,
      name: c.name,
      role: c.role,
      currentCompany: c.currentCompany,
      location: c.location,
      score: c.score,
      wsiScore: c.wsiScore || c.score,
      wsiTechnical: c.wsiTechnical,
      wsiBehavioral: c.wsiBehavioral,
      fitScore: c.fitScore,
      skills: c.skills,
      experience: c.experience,
      stage: c.stage,
      subStatus: c.subStatus,
      daysInStage: c.daysInStage,
      warnings: c.warnings,
      email: c.email,
      phone: c.phone,
      bigFive: c.bigFive,
      hasCV: !!c.cvUrl
    }))

    const selectedIds = selectedCandidates.size > 0 
      ? Array.from(selectedCandidates) 
      : undefined

    try {
      const response = await callOrchestratedJobChat({
        message,
        job_context: jobContext,
        candidates: candidatesForApi,
        selected_candidate_ids: selectedIds,
        conversation_id: liaConversationId,
        company_id: user?.company || 'default',
      })

      if (response.error === 'auth_error') {
        return {
          content: response.content || 'Sessao expirada. Recarregue a pagina para continuar.',
          ui_action: null
        }
      }

      if (response.conversation_id) {
        setLiaConversationId(response.conversation_id)
      }

      return {
        content: response.content,
        ui_action: response.ui_action,
        ui_action_params: response.ui_action_params
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Orchestrated message error:', error)
      }
      return {
        content: getFallbackResponse(message),
        ui_action: null
      }
    }
  }

  // Fallback local para quando a API não está disponível
  const getFallbackResponse = (command: string): string => {
    const cmd = command.toLowerCase().trim()
    
    if (cmd.includes('quantos candidatos') || cmd.includes('total de candidatos') || cmd.includes('quantos no funil')) {
      const total = allTableCandidates.length
      const stages = {
        sourcing: candidatesData.sourcing?.length || 0,
        screening: candidatesData.screening?.length || 0,
        interview_hr: candidatesData.interview_hr?.length || 0,
        interview_technical: candidatesData.interview_technical?.length || 0,
        interview_manager: candidatesData.interview_manager?.length || 0,
        offer: candidatesData.offer?.length || 0,
        hired: candidatesData.hired?.length || 0,
        rejected: candidatesData.rejected?.length || 0
      }
      return `📊 **Total no Kanban: ${total} candidatos**\n\n` +
        `• Funil: ${stages.sourcing}\n` +
        `• Triagem: ${stages.screening}\n` +
        `• Entrevista RH: ${stages.interview_hr}\n` +
        `• Entrevista Técnica: ${stages.interview_technical}\n` +
        `• Entrevista Gestor: ${stages.interview_manager}\n` +
        `• Proposta: ${stages.offer}\n` +
        `• Contratado: ${stages.hired}\n` +
        `• Reprovado: ${stages.rejected}`
    }
    
    if (cmd.includes('candidatos por etapa') || cmd.includes('distribuição') || cmd.includes('distribuicao')) {
      const stages = {
        'Funil': candidatesData.sourcing?.length || 0,
        'Triagem': candidatesData.screening?.length || 0,
        'Entrevista RH': candidatesData.interview_hr?.length || 0,
        'Entrevista Técnica': candidatesData.interview_technical?.length || 0,
        'Entrevista Gestor': candidatesData.interview_manager?.length || 0,
        'Proposta': candidatesData.offer?.length || 0,
        'Contratado': candidatesData.hired?.length || 0,
        'Reprovado': candidatesData.rejected?.length || 0
      }
      const total = Object.values(stages).reduce((a, b) => a + b, 0)
      return `📈 **Distribuição por Etapa**\n\n` +
        Object.entries(stages).map(([stage, count]) => {
          const percent = total > 0 ? Math.round((count / total) * 100) : 0
          return `• ${stage}: ${count} (${percent}%)`
        }).join('\n')
    }
    
    if (cmd.includes('top 5') || cmd.includes('top5') || cmd.includes('melhores candidatos') || cmd.includes('top candidatos')) {
      const sorted = [...allTableCandidates]
        .sort((a, b) => {
          const scoreA = a.score || a.fitScore || 0
          const scoreB = b.score || b.fitScore || 0
          return scoreB - scoreA
        })
        .slice(0, 5)
      
      return `🏆 **Top 5 Candidatos**\n\n` +
        sorted.map((c, i) => {
          const score = c.score ? `Score LIA: ${c.score}` : `FitScore: ${c.fitScore || 'N/A'}%`
          return `${i + 1}. **${c.name}**\n   ${c.role || 'N/A'} | ${c.currentCompany || ''}\n   ${score}`
        }).join('\n\n')
    }
    
    if (cmd.includes('comparar') || cmd.includes('comparação') || cmd.includes('comparacao')) {
      if (selectedCandidates.size === 0) {
        return `⚖️ **Comparar Candidatos**\n\nSelecione 2 ou mais candidatos no Kanban para compará-los.\n\n💡 Dica: Clique no checkbox de cada candidato que deseja comparar.`
      } else if (selectedCandidates.size === 1) {
        return `⚖️ **Comparar Candidatos**\n\nVocê selecionou apenas 1 candidato. Selecione mais candidatos para fazer uma comparação.`
      } else {
        const selectedList = allTableCandidates.filter(c => selectedCandidates.has(c.id))
        return `⚖️ **Comparação - ${selectedList.length} Candidatos**\n\n` +
          selectedList.map(c => {
            const score = c.score ? `Score: ${c.score}` : `Fit: ${c.fitScore || 'N/A'}%`
            return `**${c.name}**\n` +
              `• ${c.role || 'N/A'} @ ${c.currentCompany || 'N/A'}\n` +
              `• ${score} | Warnings: ${c.warnings || 0}\n` +
              `• Skills: ${(c.skills || []).slice(0, 3).join(', ') || 'N/A'}`
          }).join('\n\n')
      }
    }
    
    if (cmd.includes('gargalo') || cmd.includes('bottleneck') || cmd.includes('acumulados')) {
      const stages = [
        { name: 'Funil', count: candidatesData.sourcing?.length || 0 },
        { name: 'Triagem', count: candidatesData.screening?.length || 0 },
        { name: 'Entrevista RH', count: candidatesData.interview_hr?.length || 0 },
        { name: 'Entrevista Técnica', count: candidatesData.interview_technical?.length || 0 },
        { name: 'Entrevista Gestor', count: candidatesData.interview_manager?.length || 0 },
        { name: 'Proposta', count: candidatesData.offer?.length || 0 }
      ].sort((a, b) => b.count - a.count)
      
      const maxCount = stages[0].count
      const gargalos = stages.filter(s => s.count === maxCount)
      
      return `🚧 **Análise de Gargalos**\n\n` +
        `**Maior acúmulo:** ${gargalos.map(g => g.name).join(', ')} (${maxCount} candidatos)\n\n` +
        `**Ranking por volume:**\n` +
        stages.map((s, i) => `${i + 1}. ${s.name}: ${s.count} candidatos`).join('\n') +
        `\n\n💡 **Sugestão:** Priorize ações na etapa com maior acúmulo para melhorar o fluxo do processo.`
    }
    
    // Mensagem amigável para perguntas fora do contexto
    const recruiterName = currentJob.recruiter?.split(' ')[0] || 'Recrutador'
    return `💬 **Olá, ${recruiterName}!**\n\nEu ainda estou evoluindo e em breve estarei pronta para atender a todas as suas solicitações e esclarecer todas as suas dúvidas. 🚀\n\nPeço desculpas por não conseguir te ajudar com essa pergunta específica agora.\n\nNeste momento, posso te ajudar com **análises e informações do pipeline de recrutamento**, como:\n\n• "Quantos candidatos temos no processo?"\n• "Quem são os top 5 candidatos?"\n• "Como está a distribuição por etapa?"\n• "Comparar candidatos selecionados"\n• "Identificar gargalos no processo"\n\n✨ Vamos conversar muito em breve! Use as sugestões acima ou me pergunte sobre seus candidatos.`
  }

  // Handlers para drag and drop
  const handleDragStart = (e: React.DragEvent, candidate: any, fromColumn: string) => {
    setDraggedCandidate({ ...candidate, fromColumn })
    e.dataTransfer.effectAllowed = 'move'
    // Adiciona classe de dragging
    e.currentTarget.classList.add('opacity-50')
  }

  const handleDragEnd = (e: React.DragEvent) => {
    e.currentTarget.classList.remove('opacity-50')
    setDraggedCandidate(null)
    setDragOverColumn(null)
  }

  const handleDragOver = (e: React.DragEvent, column: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverColumn(column)
  }

  const handleDragLeave = () => {
    setDragOverColumn(null)
  }

  // Função para obter o sub-status sugerido pela LIA baseado na etapa destino
  const getSuggestedSubStatus = (toColumn: string): string => {
    const suggestions: Record<string, string> = {
      hired: 'onboarding_scheduled',
      rejected: 'another_candidate_selected',
      offer_declined: 'accepted_other_offer',
      screening: 'cv_received',
      long_list: 'added_to_long_list',
      short_list: 'added_to_short_list',
      interview_hr: 'awaiting_hr_schedule',
      interview_technical: 'awaiting_technical_schedule',
      interview_manager: 'awaiting_manager1_schedule',
      interview_final: 'awaiting_final_schedule',
      offer: 'preparing_offer',
      references: 'references_requested',
    }
    return suggestions[toColumn] || ''
  }

  // Função para obter os sub-statuses disponíveis para uma etapa
  // Prefere sub-statuses configurados no DB (via DynamicStage enriquecida); fallback para lista estática
  const getAvailableSubStatuses = (toColumn: string): SubStatus[] => {
    const stage = dynamicStages.find(s => s.id === toColumn)
    if (stage?.subStatuses?.length) {
      return stage.subStatuses.map(ss => ({
        name: ss.name,
        displayName: ss.display_name,
        isDefault: ss.is_default,
        isWaiting: ss.is_waiting,
      }))
    }
    return SUB_STATUSES[toColumn] || []
  }
  
  // Helper para determinar a cor de um sub-status
  const getSubStatusColor = (status: SubStatus): { bg: string; text: string } => {
    if (status.isApproval) return { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300' }
    if (status.isRejection) return { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' }
    if (status.isWaiting) return { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-700 dark:text-amber-300' }
    return { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-700 dark:text-gray-300' }
  }

  // Etapas que requerem confirmação via modal
  const stagesRequiringConfirmation = ['hired', 'rejected', 'offer_declined']

  const handleDrop = async (e: React.DragEvent, toColumn: string) => {
    e.preventDefault()

    if (!draggedCandidate) return

    const fromColumn = draggedCandidate.fromColumn
    if (fromColumn === toColumn) {
      setDragOverColumn(null)
      return
    }

    const targetStageExists = dynamicStages.some(stage => stage.id === toColumn)
    const validTargetColumn = targetStageExists ? toColumn : 'sourcing'

    const kanbanCandidate: KanbanCandidate = {
      id: draggedCandidate.id,
      name: draggedCandidate.name,
      email: draggedCandidate.email,
      phone: draggedCandidate.phone,
      avatar: draggedCandidate.avatar,
      stage: fromColumn,
      score: draggedCandidate.score,
      role: draggedCandidate.role,
      company: draggedCandidate.currentCompany || draggedCandidate.company,
      appliedDate: draggedCandidate.appliedDate,
      source: draggedCandidate.source,
      sub_status: draggedCandidate.sub_status,
    }

    openTransition([kanbanCandidate], fromColumn, validTargetColumn)
    setDragOverColumn(null)
    setDraggedCandidate(null)
  }

  // Função para confirmar a movimentação após seleção de sub-status
  const confirmMove = async () => {
    if (!pendingMove) return

    const { candidate, fromColumn, toColumn } = pendingMove
    const candidateId = candidate.id

    // Atualiza o estado movendo o candidato entre colunas (optimistic update)
    setCandidatesData(prev => {
      const newData = { ...prev }

      // Remove da coluna origem
      const fromKey = fromColumn as keyof typeof newData
      if (newData[fromKey]) {
        ;(newData[fromKey] as any[]) = (newData[fromKey] as any[]).filter((c: any) => c.id !== candidateId)
      }

      // Adiciona na coluna destino
      const toKey = toColumn as keyof typeof newData
      const candidateToMove = { ...candidate }
      delete candidateToMove.fromColumn

      candidateToMove.stage = toColumn
      candidateToMove.sub_status = selectedSubStatus
      
      // Definir needsAction baseado no tipo de etapa (replica lógica do handleDrop)
      if (toColumn === 'sourcing') candidateToMove.needsAction = true
      else if (toColumn === 'screening') candidateToMove.needsAction = false
      else if (toColumn.startsWith('interview') || toColumn.includes('entrevista')) candidateToMove.needsAction = false
      else if (toColumn === 'hired' || toColumn === 'rejected' || toColumn === 'offer_declined') candidateToMove.needsAction = false
      
      // Atualizar status para etapas finais
      if (toColumn === 'hired') candidateToMove.status = 'contratado'
      else if (toColumn === 'rejected') candidateToMove.status = 'reprovado'
      else if (toColumn === 'offer_declined') candidateToMove.status = 'proposta_recusada'
      else if (toColumn === 'offer') candidateToMove.status = 'proposta'

      // Garantir que o bucket destino existe
      if (!newData[toKey]) {
        newData[toKey] = []
      }
      newData[toKey] = [...newData[toKey], candidateToMove]

      return newData
    })

    // Fechar modal e limpar estado
    setStatusModalOpen(false)
    setPendingMove(null)
    setSelectedSubStatus('')
    
    // Persistir no backend
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidateId}/stage`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          stage: toColumn,
          sub_status: selectedSubStatus,
          job_vacancy_id: job?.id?.toString()
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('❌ Erro ao atualizar etapa do candidato:', errorData)
      } else {
        const result = await response.json()
        console.log('✅ Etapa do candidato atualizada no backend com sub-status:', result)
      }
    } catch (error) {
      console.error('❌ Erro de rede ao atualizar etapa:', error)
    }
  }

  // Função para cancelar a movimentação
  const cancelMove = () => {
    setStatusModalOpen(false)
    setPendingMove(null)
    setSelectedSubStatus('')
  }


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
      console.error('Error marking candidate as viewed:', error)
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
        console.error('Failed to update candidate status:', response.statusText)
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
      console.error('Error updating candidate status:', error)
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
  const handleOpenAnalysis = async (candidate: any) => {
    setRubricCandidate(candidate)
    setShowRubricModal(true)
    
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/rubric-evaluation`)
      if (response.ok) {
        const data = await response.json()
        setRubricEvaluationData(data)
      } else {
        const mockEvaluation = {
          overall_score: candidate.fitScore || candidate.score || 75,
          recommendation: candidate.fitScore >= 70 ? 'approve' : candidate.fitScore >= 50 ? 'review' : 'reject',
          summary: `Análise do candidato ${candidate.name} para a vaga. Avaliação baseada no currículo e requisitos da posição.`,
          criteria: [
            { name: 'Experiência Técnica', score: Math.round((candidate.technicalTestScore || candidate.fitScore || 70) * 0.8 + 20), weight: 30, details: 'Avaliação da experiência técnica do candidato' },
            { name: 'Formação Acadêmica', score: Math.round(60 + Math.random() * 30), weight: 20, details: 'Compatibilidade da formação com a vaga' },
            { name: 'Habilidades Interpessoais', score: Math.round(65 + Math.random() * 25), weight: 20, details: 'Competências comportamentais identificadas' },
            { name: 'Fit Cultural', score: Math.round(70 + Math.random() * 20), weight: 15, details: 'Alinhamento com os valores da empresa' },
            { name: 'Disponibilidade', score: Math.round(75 + Math.random() * 20), weight: 15, details: 'Adequação ao modelo de trabalho e início' }
          ]
        }
        setRubricEvaluationData(mockEvaluation)
      }
    } catch (error) {
      console.error('Error fetching rubric evaluation:', error)
      const mockEvaluation = {
        overall_score: candidate.fitScore || candidate.score || 75,
        recommendation: 'review',
        summary: `Análise do candidato ${candidate.name} para a vaga.`,
        criteria: [
          { name: 'Experiência Técnica', score: 75, weight: 30, details: 'Avaliação da experiência técnica' },
          { name: 'Formação Acadêmica', score: 70, weight: 20, details: 'Compatibilidade da formação' },
          { name: 'Habilidades Interpessoais', score: 72, weight: 20, details: 'Competências comportamentais' },
          { name: 'Fit Cultural', score: 78, weight: 15, details: 'Alinhamento cultural' },
          { name: 'Disponibilidade', score: 85, weight: 15, details: 'Disponibilidade para início' }
        ]
      }
      setRubricEvaluationData(mockEvaluation)
    }
  }

  // Funções para abrir modal de fluxo de decisão
  const openDecisionFlowModal = (candidate: any, action: 'approve' | 'reject') => {
    const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
    const isTriagemCompleted = stage === 'triagem' || candidate.triagemHistory || candidate.screeningHistory
    
    setDecisionFlowCandidate(candidate)
    
    if (action === 'approve') {
      if (isTriagemCompleted) {
        setDecisionFlowType('approve_to_interview')
      } else {
        setDecisionFlowType('approve_to_triage')
      }
    } else {
      if (isTriagemCompleted) {
        setDecisionFlowType('reject_post_triage')
      } else {
        setDecisionFlowType('reject_pre_triage')
      }
    }
    
    setShowDecisionFlowModal(true)
  }

  const handleDecisionFlowConfirm = async (action: string, feedbackMessage?: string, channel?: string) => {
    if (!decisionFlowCandidate) return
    
    const candidate = decisionFlowCandidate
    
    if (action === 'approve_to_triage' || action === 'approve_to_interview') {
      await handleApproveCandidate(candidate)
    } else if (action.startsWith('reject')) {
      await handleRejectCandidate(candidate)
      if (action === 'reject_with_feedback' && feedbackMessage) {
        toast({
          title: 'Feedback enviado',
          description: `Mensagem de feedback enviada para ${candidate.name} via ${channel === 'whatsapp' ? 'WhatsApp' : 'Email'}.`,
        })
      }
    }
    
    setShowDecisionFlowModal(false)
    setDecisionFlowCandidate(null)
  }

  const handleApproveCandidate = async (candidate: any) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_id: job?.id?.toString() || null,
          decision: 'approved'
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        const targetStage = data.new_stage || 'Triagem'
        
        const stageMapping: Record<string, string> = {
          'Triagem': 'screening',
          'Entrevista': 'interview_hr',
          'Entrevista RH': 'interview_hr',
          'Long List': 'long_list',
          'Short List': 'short_list',
        }
        const targetStageId = stageMapping[targetStage] || 'screening'
        
        setCandidatesData(prev => {
          const currentStage = Object.keys(prev).find(stage => 
            (prev as any)[stage]?.some((c: any) => c.id === candidate.id)
          )
          if (!currentStage) return prev
          
          const newData = { ...prev } as any
          newData[currentStage] = newData[currentStage].filter((c: any) => c.id !== candidate.id)
          const updatedCandidate = { ...candidate, stage: targetStageId, status: 'approved_screening' }
          newData[targetStageId] = [...(newData[targetStageId] || []), updatedCandidate]
          return newData
        })
        
        toast({
          title: 'Candidato aprovado',
          description: `${candidate.name} foi movido para ${targetStage}.`,
          variant: 'default'
        })
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.error('Error approving candidate:', errorData)
        
        if (errorData.detail?.error === 'missing_contact_info') {
          toast({
            title: 'Dados de contato incompletos',
            description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.`,
            variant: 'destructive'
          })
        } else {
          toast({
            title: 'Erro ao aprovar',
            description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.',
            variant: 'destructive'
          })
        }
      }
    } catch (error) {
      console.error('Error approving candidate:', error)
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
    }
  }

  const handleRejectCandidate = async (candidate: any) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_id: job?.id?.toString() || null,
          decision: 'rejected',
          reason: 'Reprovado via análise'
        })
      })
      
      const moveToRejected = () => {
        setCandidatesData(prev => {
          const currentStage = Object.keys(prev).find(stage => 
            (prev as any)[stage]?.some((c: any) => c.id === candidate.id)
          )
          if (!currentStage) return prev
          
          const newData = { ...prev } as any
          newData[currentStage] = newData[currentStage].filter((c: any) => c.id !== candidate.id)
          const updatedCandidate = { ...candidate, stage: 'rejected', status: 'rejected_screening' }
          newData['rejected'] = [...(newData['rejected'] || []), updatedCandidate]
          return newData
        })
      }
      
      if (response.ok) {
        const data = await response.json()
        toast({
          title: 'Candidato reprovado',
          description: `${candidate.name} foi movido para ${data.new_stage || 'Reprovados'}.`,
          variant: 'destructive'
        })
        moveToRejected()
      } else {
        const errorData = await response.json().catch(() => ({}))
        console.error('Error rejecting candidate:', errorData)
        toast({
          title: 'Erro ao reprovar',
          description: errorData.error || 'Não foi possível reprovar o candidato.',
          variant: 'destructive'
        })
      }
    } catch (error) {
      console.error('Error rejecting candidate:', error)
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
    }
  }

  const handleRubricModalClose = () => {
    setShowRubricModal(false)
    setRubricCandidate(null)
    setRubricEvaluationData(null)
  }

  // Função para abrir detalhes da triagem
  const handleOpenTriagem = (candidate: any) => {
    setTriagemCandidate(candidate)
    setIsTriagemOpen(true)
  }

  const handleCloseTriagem = () => {
    setIsTriagemOpen(false)
    setTriagemCandidate(null)
  }

  const handleApproveFromScreening = async (candidate: any) => {
    const interviewStage = dynamicStages.find(s => 
      s.id.startsWith('interview') || s.id.includes('entrevista')
    )
    const targetStage = interviewStage?.id || 'interview_hr'
    const targetDisplayName = interviewStage?.displayName || 'Entrevista RH'

    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_id: job?.id?.toString() || null,
          decision: 'approved'
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        if (errorData.detail?.error === 'missing_contact_info') {
          toast({
            title: 'Dados de contato incompletos',
            description: `${candidate.name} não possui email ou telefone válido. Adicione um contato antes de aprovar.`,
            variant: 'destructive'
          })
        } else {
          toast({
            title: 'Erro ao aprovar',
            description: errorData.detail?.message || errorData.error || 'Não foi possível aprovar o candidato.',
            variant: 'destructive'
          })
        }
        return
      }
    } catch (error) {
      console.error('Erro ao registrar aprovação:', error)
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
      return
    }

    const scoreInfo = candidate.liaScore || candidate.score
    const promptParts = [
      `${candidate.name} foi aprovado na triagem`,
      scoreInfo ? ` com score de ${scoreInfo}%` : '',
      ` e avança para "${targetDisplayName}".`,
      scoreInfo && Number(scoreInfo) >= 85 ? ` Excelente aproveitamento — um dos melhores candidatos desta triagem.` : '',
      ` Vou entrar em contato com o candidato pelo canal configurado (email/WhatsApp) e agendar a entrevista conforme sua agenda disponível.`,
      ` Se quiser sugerir um horário ou data específica, escreva aqui que vou priorizar. Caso contrário, é só confirmar que eu cuido de tudo.`,
    ]
    setTransitionInitialPrompt(promptParts.join(''))

    const kanbanCandidate: KanbanCandidate = {
      id: candidate.id,
      name: candidate.name,
      role: candidate.role || candidate.cargo,
      avatar: candidate.avatar,
      score: candidate.liaScore || candidate.score,
      email: candidate.email,
      phone: candidate.phone || candidate.telefone,
    }

    openTransition([kanbanCandidate], 'screening', targetStage)
  }

  const handleRejectFromScreening = async (candidate: any) => {
    try {
      const response = await fetch(`/api/backend-proxy/candidates/${candidate.id}/screening-decision/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          job_id: job?.id?.toString() || null,
          decision: 'rejected',
          reason: 'Reprovado via análise de triagem'
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        toast({
          title: 'Erro ao reprovar',
          description: errorData.detail?.message || errorData.error || 'Não foi possível registrar a reprovação.',
          variant: 'destructive'
        })
        return
      }
    } catch (error) {
      console.error('Erro ao registrar reprovação:', error)
      toast({
        title: 'Erro de conexão',
        description: 'Não foi possível conectar ao servidor.',
        variant: 'destructive'
      })
      return
    }

    const scoreInfo = candidate.liaScore || candidate.score
    const promptParts = [
      `O recrutador decidiu reprovar ${candidate.name} após a triagem`,
      scoreInfo ? ` (score: ${scoreInfo}%)` : '',
      `. Este candidato será movido para "Reprovados".`,
      ` Sugira um motivo de reprovação (ex: perfil desalinhado, experiência insuficiente, competências técnicas abaixo do esperado).`,
      ` Pergunte se o recrutador deseja enviar feedback construtivo ao candidato e por qual canal (email ou WhatsApp).`,
    ]
    setTransitionInitialPrompt(promptParts.join(''))

    const kanbanCandidate: KanbanCandidate = {
      id: candidate.id,
      name: candidate.name,
      role: candidate.role || candidate.cargo,
      avatar: candidate.avatar,
      score: candidate.liaScore || candidate.score,
      email: candidate.email,
      phone: candidate.phone || candidate.telefone,
    }

    openTransition([kanbanCandidate], 'screening', 'rejected')
  }

  const handleTriagemApprove = async (candidate: any) => {
    handleCloseTriagem()
    await handleApproveFromScreening(candidate)
  }

  const handleTriagemReject = async (candidate: any) => {
    handleCloseTriagem()
    await handleRejectFromScreening(candidate)
  }

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

  const handleSaveJobSection = async (sectionId: string, fields: string[]) => {
    if (!currentJob) return
    setSavingJobSection(sectionId)
    try {
      const fieldMapping: Record<string, string> = {
        title: 'title', department: 'department', location: 'location',
        workModel: 'work_model', type: 'employment_type', level: 'seniority_level',
        status: 'status', urgencyLevel: 'urgency_level',
        recruiter: 'recruiter', recruiterEmail: 'recruiter_email',
        manager: 'hiring_manager', managerEmail: 'hiring_manager_email',
        openDate: 'open_date', deadline: 'deadline',
        deadlineScreening: 'deadline_screening', deadlineShortlist: 'deadline_shortlist',
        deadlineClosing: 'deadline_closing',
        benefits: 'benefits', targetAudience: 'target_audience',
        targetSector: 'target_sector', targetSegment: 'target_segment',
        languages: 'languages', visibility: 'visibility',
        publishedLinkedIn: 'published_linkedin', publishedWebsite: 'published_website',
        publishedIndeed: 'published_indeed',
        isConfidential: 'is_confidential', maskedCompanyName: 'masked_company_name',
        isAffirmative: 'is_affirmative',
        affirmativeCriteriaPrimary: 'affirmative_criteria_primary',
        affirmativeCriteriaSecondary: 'affirmative_criteria_secondary',
        affirmativeDescription: 'affirmative_description',
        affirmativeDocumentRequired: 'affirmative_document_required',
        affirmativeDocumentTypes: 'affirmative_document_types',
        priority: 'priority',
        description: 'description',
        interviewStages: 'interview_stages',
      }
      const updates: Record<string, any> = {}
      fields.forEach(f => {
        if (f === 'salaryMin' || f === 'salaryMax') {
          if (!updates['salary_range']) {
            updates['salary_range'] = {
              min: jobEditForm.salaryMin ? Number(jobEditForm.salaryMin) : null,
              max: jobEditForm.salaryMax ? Number(jobEditForm.salaryMax) : null,
              currency: 'BRL'
            }
          }
          return
        }
        if (f === 'bonusMin' || f === 'bonusMax') {
          if (!updates['bonus_range']) {
            updates['bonus_range'] = {
              min: jobEditForm.bonusMin ? Number(jobEditForm.bonusMin) : null,
              max: jobEditForm.bonusMax ? Number(jobEditForm.bonusMax) : null,
              currency: 'BRL'
            }
          }
          return
        }
        updates[fieldMapping[f] || f] = jobEditForm[f]
      })
      const jobId = currentJob.backendId || currentJob.jobId || currentJob.id
      await liaApi.updateJobVacancy(jobId, updates)
      if (fields.includes('interviewStages') && jobEditForm.interviewStages) {
        const newStages = mapInterviewStagesToKanban(jobEditForm.interviewStages)
        setDynamicStages(newStages)
        setCandidatesData(prev => {
          const newData = createInitialCandidatesData(newStages)
          Object.keys(prev).forEach(stageId => {
            const candidates = prev[stageId] || []
            if (newData[stageId]) {
              newData[stageId] = [...candidates]
            } else {
              newData['sourcing'] = [...(newData['sourcing'] || []), ...candidates]
            }
          })
          return newData
        })
      }
      toast({ title: 'Seção salva com sucesso!' })
      setEditingSection(null)
    } catch (error) {
      console.error('Erro ao salvar:', error)
      toast({ title: 'Erro ao salvar. Tente novamente.', variant: 'destructive' })
    } finally {
      setSavingJobSection(null)
    }
  }

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
        console.error('Erro ao carregar ordem das colunas:', e)
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
        accentColor: '#374151'
      },
      hired: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: '#374151'
      },
      rejected: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-300 dark:bg-gray-600',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: '#D1D5DB'
      },
      offer_declined: {
        bg: 'bg-white dark:bg-gray-900',
        border: 'border-gray-200 dark:border-gray-700',
        dot: 'bg-gray-300 dark:bg-gray-600',
        header: 'text-gray-800 dark:text-gray-200',
        accentColor: '#D1D5DB'
      }
    }
    
    // Se há um estilo fixo, use-o
    if (fixedStyles[columnId]) {
      return fixedStyles[columnId]
    }
    
    // Para etapas dinâmicas, buscar a cor da etapa
    const dynamicStage = dynamicStages.find(s => s.id === columnId)
    const stageColor = dynamicStage?.color || '#6B7280'
    
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

  const handleInlineRename = useCallback(async (stageId: string, newName: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ display_name: newName }),
      })
      setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, displayName: newName } : s))
      toast({ title: 'Etapa renomeada', description: `Nome atualizado para "${newName}".` })
    } catch {
      toast({ title: 'Erro ao renomear', description: 'Nao foi possivel renomear a etapa.', variant: 'destructive' })
    }
  }, [toast])

  const handleInlineToggleActive = useCallback(async (stageId: string, isActive: boolean) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: isActive }),
      })
      if (!isActive) {
        setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      } else {
        setDynamicStages(prev => prev.map(s => s.id === stageId ? { ...s, isActive } : s))
      }
      toast({ title: isActive ? 'Etapa ativada' : 'Etapa desativada' })
    } catch {
      toast({ title: 'Erro', description: 'Nao foi possivel alterar o status da etapa.', variant: 'destructive' })
    }
  }, [toast])

  const handleInlineRemove = useCallback(async (stageId: string) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/remove`, {
        method: 'DELETE',
      })
      setDynamicStages(prev => prev.filter(s => s.id !== stageId))
      toast({ title: 'Coluna removida' })
    } catch {
      toast({ title: 'Erro ao remover', description: 'Nao foi possivel remover a coluna.', variant: 'destructive' })
    }
  }, [toast])

  const handleInlineMoveLeft = useCallback(async (stageId: string) => {
    setDynamicStages(prev => {
      const idx = prev.findIndex(s => s.id === stageId)
      if (idx <= 0) return prev
      const newStages = [...prev]
      const temp = newStages[idx]
      newStages[idx] = newStages[idx - 1]
      newStages[idx - 1] = temp
      const reordered = newStages.map((s, i) => ({ ...s, order: i }))
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      fetch(`${baseUrl}/api/v1/recruitment-stages/stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: reordered.map(s => ({ stage_id: s.id, new_order: s.order })) }),
      }).catch(() => {})
      return reordered
    })
  }, [])

  const handleInlineMoveRight = useCallback(async (stageId: string) => {
    setDynamicStages(prev => {
      const idx = prev.findIndex(s => s.id === stageId)
      if (idx < 0 || idx >= prev.length - 1) return prev
      const newStages = [...prev]
      const temp = newStages[idx]
      newStages[idx] = newStages[idx + 1]
      newStages[idx + 1] = temp
      const reordered = newStages.map((s, i) => ({ ...s, order: i }))
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      fetch(`${baseUrl}/api/v1/recruitment-stages/stages/reorder`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stages: reordered.map(s => ({ stage_id: s.id, new_order: s.order })) }),
      }).catch(() => {})
      return reordered
    })
  }, [])

  const handleInlineUpdateSLA = useCallback(async (stageId: string, slaHours: number) => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || ''
      await fetch(`${baseUrl}/api/v1/recruitment-stages/stages/${stageId}/inline-edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sla_hours: slaHours }),
      })
      toast({ title: 'SLA atualizado', description: `SLA definido para ${slaHours} horas.` })
    } catch {
      toast({ title: 'Erro ao atualizar SLA', variant: 'destructive' })
    }
  }, [toast])

  const STAGE_PASTEL_COLORS: Record<string, string> = {
    'sourcing': '#DCE4DB',      // Verde Menta - Funil
    'screening': '#E3DADC',     // Rosa Antigo - Triagem
    'interview_hr': '#DDE1E9',  // Azul Acinzentado - Entrevista
    'interview_technical': '#DDE1E9',
    'interview_manager': '#DDE1E9',
    'offer': '#E5E0E2',         // Lilás Acinzentado - Final
    'hired': '#E5E0E2',
    'rejected': '#E5E0E2',
    'offer_declined': '#E5E0E2'
  }

  const renderKanbanColumn = (stageId: string, candidates: any[], colorClass: string, bgClass: string) => {
    // Primeiro, buscar nome de exibição de dynamicStages, depois fallback para RECRUITMENT_STAGES
    const dynamicStage = dynamicStages.find(s => s.id === stageId)
    const stageInfo = getStageByName(stageId)
    const displayTitle = dynamicStage?.displayName || stageInfo?.displayName || stageId
    
    // Ordenar candidatos da coluna Triagem
    let sortedCandidates = [...candidates]
    if (stageId === 'screening') {
      sortedCandidates = candidates.sort((a, b) => {
        if (a.needsAction && !b.needsAction) return -1
        if (!a.needsAction && b.needsAction) return 1
        return b.score - a.score
      })
    }

    // Aplicar filtro de busca E filtros Kanban
    const filteredCandidates = sortedCandidates.filter(candidate => {
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

      if (kanbanScoreMin > 0 && candidate.score && candidate.score < kanbanScoreMin) {
        return false
      }

      if (kanbanStatusFilter.length > 0 && candidate.status) {
        const candidateStatus = candidate.status.toLowerCase().replace(/ /g, '_')
        if (!kanbanStatusFilter.includes(candidateStatus)) return false
      }

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

    const columnStyle = getColumnStyle(stageId)
    const isDropping = dragOverColumn === stageId

    return (
      <div
        className={`flex flex-col flex-1 bg-white rounded-md min-w-[275px] max-w-[368px] border border-gray-200 transition-all duration-300 ${
          isDropping ? 'ring-2 ring-gray-400 bg-gray-50/20' : ''
        } h-[calc(100vh-16rem)]`}
        onDragOver={(e) => handleDragOver(e, stageId)}
        onDragLeave={handleDragLeave}
        onDrop={(e) => handleDrop(e, stageId)}
      >
        {/* Header da Coluna - Fixo */}
        <div className="flex-shrink-0 p-2.5 pb-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 group">
              <div className={`w-2 h-2 rounded-full ${columnStyle.dot} transition-transform duration-300 ${
                isDropping ? 'scale-150' : ''
              }`}></div>
              <h3 className={`font-medium text-xs ${columnStyle.header}`}>{displayTitle}</h3>
              <span className="text-[10px] text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded-full">
                {filteredCandidates.length}
              </span>
              {stageId === 'screening' && (currentJob.backendId || currentJob.id) && (
                <SaturationBadge jobId={(currentJob.backendId || currentJob.id).toString()} />
              )}
              {dynamicStage && (
                <ColumnContextMenu
                  stage={dynamicStage}
                  stageCategory={getStageCategory(dynamicStage)}
                  onRename={handleInlineRename}
                  onToggleActive={handleInlineToggleActive}
                  onRemove={handleInlineRemove}
                  onMoveLeft={handleInlineMoveLeft}
                  onMoveRight={handleInlineMoveRight}
                  onUpdateSLA={handleInlineUpdateSLA}
                  onOpenSettings={() => router.push('/configuracoes')}
                  canMoveLeft={dynamicStages.indexOf(dynamicStage) > 0 && !dynamicStages[dynamicStages.indexOf(dynamicStage) - 1]?.isInitial}
                  canMoveRight={dynamicStages.indexOf(dynamicStage) < dynamicStages.length - 1 && !dynamicStages[dynamicStages.indexOf(dynamicStage) + 1]?.isFinal}
                />
              )}
            </div>
            {filteredCandidates.length > 0 && (
              <Checkbox
                checked={filteredCandidates.every(c => selectedCandidates.has(c.id))}
                onCheckedChange={(checked) => {
                  if (checked) {
                    const newSelected = new Set(selectedCandidates)
                    filteredCandidates.forEach(c => newSelected.add(c.id))
                    setSelectedCandidates(newSelected)
                  } else {
                    const newSelected = new Set(selectedCandidates)
                    filteredCandidates.forEach(c => newSelected.delete(c.id))
                    setSelectedCandidates(newSelected)
                  }
                }}
                className="w-3.5 h-3.5 data-[state=checked]:bg-gray-900 data-[state=checked]:border-gray-900"
                title={`Selecionar todos da etapa ${displayTitle}`}
              />
            )}
          </div>
        </div>

        {/* Cards - Com scroll vertical */}
        <div className="flex-1 overflow-y-auto px-1.5 pb-1 space-y-1">
          {filteredCandidates.map((candidate, index) => (
            <div
              key={candidate.id}
              draggable
              onDragStart={(e) => handleDragStart(e, candidate, stageId)}
              onDragEnd={handleDragEnd}
              className={`bg-white dark:bg-gray-800 rounded-md border relative overflow-hidden ${
                candidate.needsAction ? 'border-l-4 border-l-[#1F2937] border-gray-200 dark:border-gray-700' : 
                (candidate.status === 'triado_aprovado' || candidate.status === 'triado') && stageId === 'screening' ? 'border-l-4 border-l-green-500 border-gray-200 dark:border-gray-700 bg-green-50/30 dark:bg-green-900/20' : 
                'border-gray-200 dark:border-gray-700'
              } hover:transition-all duration-300 cursor-move group`}
              style={{
                animationDelay: `${index * 50}ms`,
                minHeight: '110px',
                transition: 'all 0.3s ease',
                animation: isDropping ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : undefined
              }}
              onMouseEnter={(e) => {
                if (!draggedCandidate) {
                  e.currentTarget.style.transform = 'translateY(-1px)'
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)'
                }
              }}
              onMouseLeave={(e) => {
                if (!draggedCandidate) {
                  e.currentTarget.style.transform = 'translateY(0)'
                  e.currentTarget.style.boxShadow = ''
                }
              }}
              onClick={() => !draggedCandidate && handleOpenPreview(candidate)}
            >
              {/* Tarja de Ação Necessária - Cinza puro */}
              {candidate.needsAction && (
                <div 
                  className="px-2 py-0.5 border-b bg-gray-100"
                >
                  <div className="flex items-center gap-1">
                    <Flag className="w-3 h-3 text-amber-500" />
                    <span className="text-[10px] font-bold text-gray-500" style={{ fontFamily: "'Open Sans', sans-serif" }}>Ação Necessária</span>
                  </div>
                </div>
              )}

              <div className="p-2 relative">
                {/* Ações rápidas - Posicionadas no canto direito */}
                <div className="absolute right-2 top-8 flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  {/* Menu de opções - Primeiro */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        className="p-1 hover:bg-gray-100 rounded transition-opacity bg-white/80"
                        onClick={(e) => e.stopPropagation()}
                        title="Mais opções"
                      >
                        <MoreVertical className="w-3 h-3 text-gray-600" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent side="right" align="start" sideOffset={8} className="w-48">
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleSendEmail(candidate); }} 
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer" 
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <Mail className="w-3.5 h-3.5 mr-2 text-gray-500" />
                        Enviar Email
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleSendWhatsApp(candidate); }} 
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer" 
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <MessageCircle className="w-3.5 h-3.5 mr-2 text-gray-500" />
                        Enviar WhatsApp
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleScheduleInterview(candidate); }} 
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer" 
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <Calendar className="w-3.5 h-3.5 mr-2 text-gray-500" />
                        Agendar Entrevista
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleSendWSIInvite(candidate); }} 
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer" 
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <ClipboardList className="w-3.5 h-3.5 mr-2 text-gray-500" />
                        Triagem WSI
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={(e) => { e.stopPropagation(); handleSendFeedback(candidate); }} 
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer" 
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <MessageSquareText className="w-3.5 h-3.5 mr-2 text-gray-500" />
                        Enviar Feedback
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={(e) => { e.stopPropagation(); handleToggleShortList(candidate.id); }}
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <Bookmark className={`w-3.5 h-3.5 mr-2 ${shortListedCandidateIds.has(candidate.id) ? 'fill-gray-900 text-gray-900 dark:fill-gray-50 dark:text-gray-50' : 'text-gray-500'}`} />
                        {shortListedCandidateIds.has(candidate.id) ? 'Remover da Short List' : 'Adicionar à Short List'}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => { e.stopPropagation(); handleToggleFavorite(candidate.id); }}
                        className="text-xs text-gray-800 dark:text-gray-200 hover:bg-gray-50 cursor-pointer"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        <Heart className={`w-3.5 h-3.5 mr-2 ${favoriteCandidates.has(candidate.id) ? 'fill-red-500 text-red-500' : 'text-gray-500'}`} />
                        {favoriteCandidates.has(candidate.id) ? 'Remover dos Favoritos' : 'Adicionar a Favoritos'}
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>

                  {/* Botão de Preview */}
                  <button
                    className="p-1 hover:bg-gray-100 rounded transition-colors bg-white/80"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleOpenPreview(candidate)
                    }}
                    title="Ver detalhes do candidato"
                  >
                    <Eye className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                  </button>
                </div>

                {/* Header do Card - Checkbox, Avatar, Nome */}
                <div className="flex items-center gap-1.5 mb-2 pr-6">
                  {/* Checkbox pequeno */}
                  <input
                    type="checkbox"
                    checked={selectedCandidates.has(candidate.id)}
                    className="w-3 h-3 rounded cursor-pointer flex-shrink-0 border border-gray-200"
                    onClick={(e) => {
                      e.stopPropagation()
                      const newSelected = new Set(selectedCandidates)
                      if (newSelected.has(candidate.id)) {
                        newSelected.delete(candidate.id)
                      } else {
                        newSelected.add(candidate.id)
                      }
                      setSelectedCandidates(newSelected)
                    }}
                    onChange={() => {}}
                  />

                  {/* Avatar pequeno com foto */}
                  <div className="relative flex-shrink-0">
                    {(() => {
                      const getKanbanAvatarUrl = (id: string, name: string): string => {
                        let hash = 0
                        const str = id + name
                        for (let i = 0; i < str.length; i++) {
                          const char = str.charCodeAt(i)
                          hash = ((hash << 5) - hash) + char
                          hash = hash & hash
                        }
                        const avatarIndex = Math.abs(hash % 70) + 1
                        const gender = Math.abs(hash % 2) === 0 ? 'men' : 'women'
                        return `https://randomuser.me/api/portraits/thumb/${gender}/${avatarIndex}.jpg`
                      }
                      const kanbanAvatarUrl = candidate.avatar?.startsWith('http') ? candidate.avatar : getKanbanAvatarUrl(candidate.id || '', candidate.name || '')
                      return (
                        <Avatar className="w-7 h-7">
                          <AvatarImage src={kanbanAvatarUrl} alt={candidate.name} />
                          <AvatarFallback className="text-[10px] font-medium text-gray-600">
                            {candidate.name.split(' ').map((n: string) => n[0]).join('').substring(0, 2)}
                          </AvatarFallback>
                        </Avatar>
                      )
                    })()}
                    {viewedCandidateIds.has(candidate.id) && (
                      <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                        <Eye className="w-2 h-2 text-white" />
                      </div>
                    )}
                  </div>

                  {/* Nome do candidato + Data Request Indicator */}
                  <div className="flex items-center gap-1 flex-1 min-w-0">
                    <h4 className="font-medium text-xs truncate text-gray-950 dark:text-gray-50" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                      {candidate.name}
                    </h4>
                    {/* DataRequestIndicator - Real data from API */}
                    {(() => {
                      const dataRequest = getDataRequestForCandidate(candidate.id)
                      if (!dataRequest) return null
                      return (
                        <DataRequestIndicator
                          candidateId={candidate.id}
                          status={dataRequest.status}
                          fieldsRequested={dataRequest.fieldsRequested}
                          fieldsCompleted={dataRequest.fieldsCompleted}
                          expiresAt={dataRequest.expiresAt}
                          onResend={handleDataRequestResend}
                          onViewDetails={handleDataRequestViewDetails}
                          size="sm"
                        />
                      )
                    })()}
                  </div>
                </div>

                {/* Scores - Todos os 6 indicadores (Geral, Triagem, CV, Técnico, Inglês, B5) */}
                {(() => {
                  const geralScore = calculateNotaLiaGeral(candidate)
                  const triagemScore = candidate.liaScore ?? candidate.score
                  const cvScore = candidate.skillsMatch || candidate.fitScore
                  const tecnicoScore = candidate.technicalTestScore
                  const inglesScore = candidate.englishTestScore
                  const b5Data = candidate.bigFive || candidate.bigFiveScores
                  const b5Score = b5Data ? Math.round(Object.values(b5Data).reduce((a: number, b: any) => a + (typeof b === 'number' ? b : 0), 0) / Object.values(b5Data).length) : null

                  const scores = [
                    { id: 'geral', icon: Gauge, value: geralScore, label: 'Geral', alwaysClickable: false },
                    { id: 'triagem', icon: BrainCircuit, value: triagemScore, label: 'Triagem', alwaysClickable: true },
                    { id: 'cv', icon: Target, value: cvScore, label: 'CV', alwaysClickable: true },
                    { id: 'tecnico', icon: Code, value: tecnicoScore, label: 'Técnico', alwaysClickable: false },
                    { id: 'ingles', icon: Globe, value: inglesScore, label: 'Inglês', alwaysClickable: false },
                    { id: 'b5', icon: Fingerprint, value: b5Score, label: 'B5', alwaysClickable: false }
                  ]

                  return (
                    <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
                      {scores.map(({ id, icon: Icon, value, label, alwaysClickable }) => (
                        <ScoreIconButton
                          key={id}
                          id={id}
                          icon={Icon}
                          value={value}
                          formattedValue={value ? formatScorePercent(value, 0) : undefined}
                          label={label}
                          alwaysClickable={alwaysClickable}
                          onClick={() => handleOpenScoreModal(candidate, id as 'geral' | 'triagem' | 'cv' | 'tecnico' | 'ingles' | 'b5')}
                        />
                      ))}
                    </div>
                  )
                })()}

                {/* Informações do candidato - Alinhadas à esquerda */}
                <div className="space-y-0 mb-1.5">
                  <div className="flex items-center gap-1 text-[11px]" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <Briefcase className="w-2.5 h-2.5 flex-shrink-0" />
                    <span className="truncate">{candidate.role}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px]" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <Building className="w-2.5 h-2.5 flex-shrink-0" />
                    <span className="truncate">{candidate.currentCompany || 'Não informado'}</span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px]" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                    <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                    <span className="truncate">{candidate.location}</span>
                  </div>
                </div>

                {/* Tags de Status Compactas */}
                <div className="mt-2 flex flex-wrap gap-1">
                  {/* AI Suggestion Badge - Show if candidate has pending AI suggestion */}
                  {(() => {
                    const suggestion = getSuggestionForCandidate(aiSuggestions, candidate.id)
                    if (suggestion) {
                      return (
                        <div onClick={(e) => e.stopPropagation()}>
                          <AISuggestionBadge
                            suggestion={suggestion}
                            onApprove={approveSuggestion}
                            onReject={rejectSuggestion}
                            compact
                          />
                        </div>
                      )
                    }
                    return null
                  })()}
                  
                  {/* FUNIL - Candidatos sem triagem ainda */}
                  {stageId === 'sourcing' && (
                    <>
                      {/* Status de entrada */}
                      <StatusBadge
                        stageId={stageId}
                        variant="standard"
                        icon={User}
                        label={
                          candidate.source === 'linkedin' ? 'Aplicou via LinkedIn' :
                          candidate.source === 'website' ? 'Aplicou no site' :
                          candidate.source === 'lia_database' ? 'Mapeado pela LIA' :
                          'Adicionado manual'
                        }
                      />
                      {/* Status da triagem automática - accent com pulse */}
                      <StatusBadge
                        stageId={stageId}
                        variant="accent"
                        icon={BrainCircuit}
                        label="LIA iniciará triagem"
                        pulse
                      />
                    </>
                  )}

                  {/* TRIAGEM - Candidatos em contato com LIA */}
                  {stageId === 'screening' && (
                    <>
                      {(candidate.needsAction || candidate.status === 'triado_aprovado') ? (
                        // Triagem concluída, aguardando decisão
                        <>
                          <StatusBadge
                            stageId={stageId}
                            variant="dark"
                            icon={CheckCircle}
                            label="Triagem concluída"
                          />
                          <StatusBadge
                            stageId={stageId}
                            variant="accent"
                            icon={Target}
                            label="Decisão pendente"
                            pulse
                            onClick={() => handleOpenAnalysis(candidate)}
                            title="Clique para ver análise completa"
                          />
                        </>
                      ) : (
                        // Em processo de triagem
                        <StatusBadge
                          stageId={stageId}
                          variant="outlined"
                          icon={MessageCircle}
                          label={candidate.liatriagem === 'respondendo' ? 'Respondendo agora' : 'Conversa em andamento'}
                        />
                      )}

                      {/* Canal de comunicação */}
                      <ChannelBadge channel={candidate.contactChannelId || 'whatsapp'} />
                    </>
                  )}

                  {/* ENTREVISTA - Candidatos aprovados na triagem */}
                  {(stageId === 'interview_hr' || stageId === 'interview_technical' || stageId === 'interview_manager') && (
                    <>
                      {candidate.agendada ? (
                        <>
                          <StatusBadge
                            stageId={stageId}
                            variant="scheduled"
                            icon={CalendarCheck}
                            label="Entrevista confirmada"
                          />
                          {candidate.interviewDate && (
                            <DateTimeBadge date={candidate.interviewDate} />
                          )}
                          <ChannelBadge channel={candidate.typeOfInterview || 'teams'} />
                        </>
                      ) : (
                        <StatusBadge
                          stageId={stageId}
                          variant="accent"
                          icon={Clock}
                          label="Aguardando agendamento"
                          pulse
                        />
                      )}
                      {/* Feedback pendente após entrevista realizada */}
                      {candidate.interviewCompleted && !candidate.interviewFeedback && (
                        <StatusBadge
                          stageId={stageId}
                          variant="accent"
                          icon={Clock}
                          label="Feedback pendente"
                          pulse
                        />
                      )}
                    </>
                  )}

                  {/* FINAL - Candidatos em estágio final */}
                  {stageId === 'offer' && (
                    <>
                      <StatusBadge
                        stageId={stageId}
                        variant="standard"
                        icon={Star}
                        label="Finalista"
                      />
                      {candidate.proposal ? (
                        <>
                          <StatusBadge
                            stageId={stageId}
                            variant="dark"
                            icon={FileText}
                            label="Proposta enviada"
                          />
                          {!candidate.proposalResponse && (
                            <StatusBadge
                              stageId={stageId}
                              variant="accent"
                              icon={Clock}
                              label="Aguardando resposta"
                              pulse
                            />
                          )}
                        </>
                      ) : (
                        <StatusBadge
                          stageId={stageId}
                          variant="accent"
                          icon={Clock}
                          label="Aguardando aprovação"
                          pulse
                        />
                      )}
                      {candidate.negotiating && (
                        <StatusBadge
                          stageId={stageId}
                          variant="outlined"
                          icon={MessageCircle}
                          label="Em negociação"
                        />
                      )}
                    </>
                  )}

                  {/* CONTRATADOS - Candidatos contratados */}
                  {stageId === 'hired' && (
                    <>
                      <StatusBadge
                        stageId={stageId}
                        variant="hired"
                        icon={Trophy}
                        label="Contratado"
                      />
                      {candidate.startDate && (
                        <StatusBadge
                          stageId={stageId}
                          variant="standard"
                          icon={Calendar}
                          label={`Início: ${new Date(candidate.startDate).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}`}
                        />
                      )}
                      {candidate.sub_status && (
                        <StatusBadge
                          stageId={stageId}
                          subStatus={candidate.sub_status}
                        />
                      )}
                    </>
                  )}

                  {/* REPROVADOS - Candidatos rejeitados */}
                  {stageId === 'rejected' && (
                    <>
                      <StatusBadge
                        stageId={stageId}
                        variant="rejected"
                        icon={XCircle}
                        label={
                          candidate.rejectionReason === 'withdrew' ? 'Desistiu' :
                          candidate.rejectionStage === 'screening' ? 'Reprovado triagem' :
                          candidate.rejectionStage === 'interview' ? 'Reprovado entrevista' :
                          'Reprovado'
                        }
                      />
                      {candidate.feedbackSent && (
                        <StatusBadge
                          stageId={stageId}
                          variant="dark"
                          icon={CheckCircle}
                          label="Feedback enviado"
                        />
                      )}
                    </>
                  )}

                  {/* PROPOSTA RECUSADA */}
                  {stageId === 'offer_declined' && (
                    <>
                      <StatusBadge
                        stageId={stageId}
                        variant="rejected"
                        icon={XCircle}
                        label="Proposta recusada"
                      />
                      {candidate.feedbackSent && (
                        <StatusBadge
                          stageId={stageId}
                          variant="dark"
                          icon={CheckCircle}
                          label="Feedback enviado"
                        />
                      )}
                    </>
                  )}

                  {/* Badge de Warning - Dias parado */}
                  {(candidate.warning || candidate.warningDays) && (
                    <WarningBadge 
                      days={candidate.daysPaused} 
                      message={candidate.warningDays} 
                    />
                  )}

                  {/* Badge de expectativa salarial */}
                  {candidate.expectativa && (
                    <StatusBadge
                      stageId={stageId}
                      variant={
                        candidate.expectativa === 'no budget' ? 'dark' :
                        candidate.expectativa === 'acima do budget' ? 'outlined' :
                        'standard'
                      }
                      icon={DollarSign}
                      label={candidate.expectativa}
                    />
                  )}

                  {/* Badge de Origem (canal de entrada) */}
                  {candidate.origin && (
                    <OriginBadge origin={candidate.origin} />
                  )}

                  {/* Badge Aguardando (fila de saturação) + Override */}
                  {(candidate.status === 'awaiting_screening' || candidate.sub_status === 'awaiting_screening' || candidate.subStatus === 'awaiting_screening') && (
                    <>
                      <AwaitingBadge />
                      {(currentJob?.backendId || currentJob?.id) && (
                        <OverrideApproveButton
                          candidateId={candidate.id}
                          candidateName={candidate.name}
                          vacancyId={(currentJob.backendId || currentJob.id).toString()}
                          onApproved={(cId) => {
                            setCandidatesData(prev => {
                              const updated = { ...prev }
                              Object.keys(updated).forEach(key => {
                                updated[key] = updated[key].map(c => 
                                  c.id === cId 
                                    ? { ...c, status: 'triado_aprovado', sub_status: undefined, subStatus: undefined }
                                    : c
                                )
                              })
                              return updated
                            })
                          }}
                        />
                      )}
                    </>
                  )}

                  {/* Tag de Origem - usando componente SourceBadge */}
                  <SourceBadge 
                    source={candidate.source || 'website'} 
                    isApplication={isApplicationSource(candidate.source || 'website')}
                  />

                  {/* Sub-Status Badge - usando StatusBadge com derivação automática */}
                  {candidate.sub_status && !['hired', 'rejected', 'offer_declined'].includes(stageId) && (
                    <StatusBadge
                      stageId={stageId}
                      subStatus={candidate.sub_status}
                    />
                  )}
                </div>

              </div>

              {/* Container de Ações - Expandem abaixo do conteúdo no hover */}
              {(stageId === 'sourcing' || stageId === 'screening' || stageId.startsWith('interview_') || stageId === 'offer') && (
                <div 
                  className="border-t border-gray-100 p-2 max-h-0 overflow-hidden opacity-0 group-hover:max-h-20 group-hover:opacity-100 transition-all duration-200 ease-out relative z-20 bg-gray-50"
                >
                  {/* Botões para FUNIL - Aprovar/Reprovar para iniciar triagem */}
                  {stageId === 'sourcing' && (
                    <div className="flex gap-1">
                      <button
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-[10px] font-medium transition-colors"
                        style={{ fontFamily: "'Open Sans', sans-serif" }}
                        onClick={(e) => {
                          e.stopPropagation()
                          openDecisionFlowModal(candidate, 'approve')
                        }}
                      >
                        <ThumbsUp className="w-3 h-3" />
                        <span>Aprovar</span>
                      </button>
                      <button
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-full text-[10px] font-medium transition-colors"
                        style={{ fontFamily: "'Open Sans', sans-serif" }}
                        onClick={(e) => {
                          e.stopPropagation()
                          openDecisionFlowModal(candidate, 'reject')
                        }}
                      >
                        <XCircle className="w-3 h-3" />
                        <span>Reprovar</span>
                      </button>
                    </div>
                  )}

                  {/* Botões para TRIAGEM - Aprovar abre UniversalTransitionModal com agendamento LIA */}
                  {stageId === 'screening' && (
                    <div className="flex gap-1">
                      <button
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-[10px] font-medium transition-colors"
                        style={{ fontFamily: "'Open Sans', sans-serif" }}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleApproveFromScreening(candidate)
                        }}
                      >
                        <ThumbsUp className="w-3 h-3" />
                        <span>Aprovar</span>
                      </button>
                      <button
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-full text-[10px] font-medium transition-colors"
                        style={{ fontFamily: "'Open Sans', sans-serif" }}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleRejectFromScreening(candidate)
                        }}
                      >
                        <XCircle className="w-3 h-3" />
                        <span>Reprovar</span>
                      </button>
                    </div>
                  )}

                  {/* Coluna Funil não precisa de botões pois a triagem é automática */}
                  
                  {/* Botões para ENTREVISTA - Ações de agendamento LIA */}
                  {(stageId === 'interview_hr' || stageId === 'interview_technical' || stageId === 'interview_manager') && (
                    <div className="flex gap-1">
                      {candidate.agendada ? (
                        <>
                          {/* Botão Entrevista Agendada - Abre Teams diretamente */}
                          <button
                            className="flex-1 flex items-center justify-center gap-1.5 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-[10px] font-medium transition-colors"
                            style={{ fontFamily: "'Open Sans', sans-serif" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              const teamsUrl = candidate.teamsLink || 'https://teams.microsoft.com/l/meetup-join/...'
                              window.open(teamsUrl, '_blank')
                            }}
                            title={`Entrar na reunião - ${candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR')}`}
                          >
                            <Video className="w-3 h-3 text-gray-600" />
                            <span>{candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                          </button>
                          {/* Botão Alterar Horário - Abre UniversalTransitionModal com LIA */}
                          <button
                            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-full text-[10px] font-medium transition-colors"
                            style={{ fontFamily: "'Open Sans', sans-serif" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              const dateStr = candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
                              setTransitionInitialPrompt(`O recrutador quer alterar o horário da entrevista de ${candidate.name} agendada para ${dateStr}. Peça a nova data e horário preferido e confirme o reagendamento com o candidato.`)
                              setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                              openTransition([candidate], stageId, stageId)
                            }}
                            title="Alterar horário da entrevista"
                          >
                            <Calendar className="w-3 h-3" />
                            <span>Alterar</span>
                          </button>
                          {/* Botão Cancelar Entrevista */}
                          <button
                            className="flex-shrink-0 flex items-center justify-center gap-1 px-2 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 rounded-full text-[10px] font-medium transition-colors"
                            style={{ fontFamily: "'Open Sans', sans-serif" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              const dateStr = candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
                              setTransitionInitialPrompt(`O recrutador quer cancelar a entrevista de ${candidate.name} agendada para ${dateStr}. Pergunte para qual etapa ele quer mover o candidato (ou se mantém na mesma) e confirme o cancelamento.`)
                              setTransitionAllowStageSelection(true)
                              setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                              openTransition([candidate], stageId, stageId)
                            }}
                            title="Cancelar entrevista"
                          >
                            <XCircle className="w-3 h-3" />
                            <span>Cancelar</span>
                          </button>
                        </>
                      ) : (
                        <>
                          {/* Botão Solicitar Urgência - Abre modal de confirmação */}
                          <button
                            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-full text-[10px] font-medium transition-colors"
                            style={{ fontFamily: "'Open Sans', sans-serif" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              setDecisionFlowCandidate(candidate)
                              setDecisionFlowType('request_urgency')
                              setShowDecisionFlowModal(true)
                            }}
                          >
                            <AlertCircle className="w-3 h-3" />
                            <span>Urgência</span>
                          </button>
                          {/* Botão Alterar Horário - Abre modal de confirmação */}
                          <button
                            className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-[10px] font-medium transition-colors"
                            style={{ fontFamily: "'Open Sans', sans-serif" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              setDecisionFlowCandidate(candidate)
                              setDecisionFlowType('reschedule_interview')
                              setShowDecisionFlowModal(true)
                            }}
                          >
                            <Calendar className="w-3 h-3" />
                            <span>Alterar Horário</span>
                          </button>
                        </>
                      )}
                    </div>
                  )}

                  {stageId === 'offer' && (
                    <button
                      className="w-full flex items-center justify-center gap-1 px-2 py-1.5 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:hover:bg-gray-200 dark:text-gray-900 rounded-full text-[10px] transition-colors"
                      style={{ fontFamily: "'Open Sans', sans-serif" }}
                      onClick={(e) => {
                        e.stopPropagation()
                        console.log('Gerenciar proposta:', candidate.name)
                      }}
                    >
                      <FileText className="w-3 h-3" />
                      <span>Gerenciar Proposta</span>
                    </button>
                  )}
                </div>
                )}
            </div>
          ))}
        </div>
      </div>
    )
  }

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
          background-color: rgba(96, 190, 209, 0.05);
          border-color: rgb(96, 190, 209);
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
                    <span className="text-[10px] font-mono text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 px-1.5 py-0.5 rounded whitespace-nowrap">
                      {currentJob.jobId}
                    </span>
                  )}
                  <Popover>
                    <PopoverTrigger asChild>
                      <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-xs px-2 py-0.5 cursor-pointer hover:bg-[#c9d6c8] transition-colors select-none">
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
                            <PauseCircle className="w-3.5 h-3.5 text-amber-500" />
                            Pausar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 transition-colors"
                            onClick={() => setShowCloseVacancyModal(true)}
                          >
                            <Archive className="w-3.5 h-3.5" />
                            Fechar vaga
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-emerald-700 hover:bg-emerald-50 transition-colors"
                            onClick={() => { setJobStatusModalMode('activate'); setShowJobStatusModal(true) }}
                          >
                            <PlayCircle className="w-3.5 h-3.5" />
                            Reativar vaga
                          </button>
                          <button
                            className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-red-600 hover:bg-red-50 transition-colors"
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
                      not_started: 'bg-amber-50 text-amber-800 border border-amber-300',
                      active: 'bg-emerald-50 text-emerald-800 border border-emerald-300',
                      paused: 'bg-orange-50 text-orange-800 border border-orange-300',
                      completed: 'bg-sky-50 text-sky-800 border border-sky-300',
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
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-emerald-700 hover:bg-emerald-50 transition-colors"
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
                              className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-amber-700 hover:bg-amber-50 transition-colors"
                              onClick={() => handleScreeningStatusChange('paused')}
                            >
                              <PauseCircle className="w-3.5 h-3.5" />
                              Pausar Triagem
                            </button>
                          )}
                          {scrStatus === 'paused' && (
                            <>
                              <button
                                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs text-emerald-700 hover:bg-emerald-50 transition-colors"
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
                    <Badge className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 font-semibold whitespace-nowrap text-[10px] px-1.5 py-0">
                      Rascunho
                    </Badge>
                  )}
                  <Badge className="bg-[#E3DADC] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-semibold whitespace-nowrap text-[10px] px-1.5 py-0">
                    {currentJob.level}
                  </Badge>
                  <Badge className="bg-[#DDE1E9] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium capitalize whitespace-nowrap text-[10px] px-1.5 py-0">
                    {currentJob.workModel || '—'}
                  </Badge>
                  <Badge className="bg-[#E3DADC] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                    {currentJob.type || '—'}
                  </Badge>
                  <Badge className="bg-[#DDE1E9] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                    {currentJob.department}
                  </Badge>
                  <Badge className="bg-[#E3DADC] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                    {currentJob.location}
                  </Badge>
                  {currentJob.salary && currentJob.salary !== 'A combinar' && (
                    <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                      {currentJob.salary}
                    </Badge>
                  )}
                  {currentJob.publishedLinkedIn && (
                    <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                      Publicada
                    </Badge>
                  )}
                  <span className="text-[10px] text-gray-300 dark:text-gray-600 mx-0.5">|</span>
                  {currentJob.openDate && (
                    <span className="text-[10px] text-gray-700 dark:text-gray-300 whitespace-nowrap">
                      <Calendar className="w-3 h-3 inline mr-0.5 -mt-0.5" />
                      {new Date(currentJob.openDate).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </span>
                  )}
                  {currentJob.openDate && (() => {
                    const days = Math.floor((Date.now() - new Date(currentJob.openDate).getTime()) / (1000 * 60 * 60 * 24))
                    if (days <= 0) return null
                    const isLate = days > 30
                    return (
                      <span className={`text-[10px] font-semibold whitespace-nowrap ${isLate ? 'text-red-600' : 'text-gray-700 dark:text-gray-300'}`}>
                        {days}d {isLate ? 'de atraso' : 'aberta'}
                      </span>
                    )
                  })()}
                  {currentJob.updatedAt && (
                    <span className="text-[10px] text-gray-600 dark:text-gray-400 whitespace-nowrap">
                      Atualizada: {new Date(currentJob.updatedAt).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </span>
                  )}
                  {currentJob.deadlineScreening && (
                    <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo triagem: {new Date(currentJob.deadlineScreening).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {currentJob.deadlineShortlist && (
                    <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Prazo short: {new Date(currentJob.deadlineShortlist).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {currentJob.deadlineClosing && (
                    <Badge className="bg-[#DCE4DB] dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200 font-medium whitespace-nowrap text-[10px] px-1.5 py-0">
                      <Calendar className="w-3 h-3 mr-0.5" />
                      Encerramento: {new Date(currentJob.deadlineClosing).toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })}
                    </Badge>
                  )}
                  {computedSuggestions.length > 0 && (
                    <Badge 
                      className="bg-wedo-cyan text-white border-0 font-semibold whitespace-nowrap text-[10px] px-1.5 py-0 cursor-pointer hover:bg-wedo-cyan-dark transition-colors"
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
              <Badge className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-[10px] px-1.5 py-0 ml-1">
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
                  <span className="inline-flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400" style={{ fontFamily: "'Open Sans', sans-serif" }}>
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
                    className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-md transition-colors"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    <RotateCcw className="w-3 h-3" />
                    Resetar para padrão
                  </button>
                </>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] text-gray-400 dark:text-gray-500" style={{ fontFamily: "'Open Sans', sans-serif" }}>
                  <Link2 className="w-3 h-3" />
                  Herdado da empresa
                </span>
              )}
            </div>
          </div>

        </div>
      </div>

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
                      className="h-6 text-[10px] gap-1 flex-shrink-0 px-2"
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
                  <div className="flex-shrink-0 flex-1 max-w-[300px]">
                    <div className="relative">
                      <div className="absolute left-3 top-1/2 -translate-y-1/2 z-10 cursor-pointer" onClick={() => setShowExpandedLIA(!showExpandedLIA)}>
                        <Brain className="w-4 h-4 text-wedo-cyan" />
                      </div>
                      <input
                        type="text"
                        placeholder="Ex: Analisar candidatos com maior fit..."
                        value={liaPromptValue}
                        onChange={(e) => setLiaPromptValue(e.target.value)}
                        className="w-full h-10 pl-10 pr-20 text-[13px] rounded-md focus:outline-none placeholder:text-gray-600 transition-all border"
                        style={{ 
                          backgroundColor: '#FFFFFF',
                          color: '#1a1a1a',
                          fontFamily: '"Open Sans", sans-serif'
                        }}
                        onFocus={(e) => {
                          e.currentTarget.style.borderColor = '#1f2937'
                          e.currentTarget.style.boxShadow = '0 0 0 2px rgba(31, 41, 55, 0.12)'
                          setShowExpandedLIA(true)
                        }}
                        onBlur={(e) => {
                          e.currentTarget.style.borderColor = '#E5E7EB'
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
                        >
                          <Maximize2 className="w-4 h-4 text-gray-700" />
                        </button>
                        <button
                          className="p-1.5 rounded-md transition-colors hover:bg-gray-100"
                          onClick={() => {
                            if (liaPromptValue.trim()) {
                              handleAICommand(liaPromptValue)
                            }
                          }}
                        >
                          <Send className="w-4 h-4 text-gray-700" />
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
                  />
                  {searchQuery && (
                    <button
                      onClick={() => setSearchQuery("")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 rounded"
                    >
                      <X className="w-3 h-3 text-gray-800 dark:text-gray-200" />
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
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                style={{ maxWidth: 'calc(100% - 48px)' }}
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
              <div className="flex-shrink-0 w-[48px] transition-all duration-300 py-4 pr-2">
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
                    <div className="w-6 h-6 rounded-full bg-orange-500 flex items-center justify-center">
                      <span className="text-white text-[10px] font-bold">H</span>
                    </div>
                  </div>
                  
                  {/* Ícone Ações/Automação */}
                  <div className="flex flex-col items-center gap-1 py-2 cursor-pointer hover:bg-gray-50 rounded-md px-2 transition-colors">
                    <div className="w-6 h-6 rounded-full bg-yellow-400 flex items-center justify-center">
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
                      className="text-[9px] font-medium text-gray-600 tracking-wide"
                      style={{ writingMode: 'vertical-rl', textOrientation: 'mixed' }}
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
                <div 
                  className="flex-shrink-0 transition-all duration-300 pl-4 py-4 pr-0 relative"
                  style={{ width: `${liaExpandedWidth}px` }}
                >
                  <Card className="h-[calc(100vh-16rem)] flex flex-col overflow-hidden border border-gray-300" style={{ backgroundColor: '#FFFFFF', maxHeight: 'calc(100vh - 16rem)' }}>
                    {/* Mensagem de Apresentação da LIA */}
                    <div className="flex-shrink-0 px-4 py-3" style={{ backgroundColor: '#FFFFFF' }}>
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div 
                            className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0"
                            style={{ backgroundColor: '#FFFFFF' }}
                          >
                            <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="text-[14px] font-semibold leading-tight truncate text-gray-950 dark:text-gray-50" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              Olá! Sou a Lia.
                            </h3>
                            <p className="text-[11px] leading-tight truncate mt-0.5 text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                              Como posso te ajudar hoje?
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          {liaMessages.length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setLiaMessages([])}
                              title="Nova conversa"
                              className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                            >
                              <RotateCcw className="w-3.5 h-3.5 text-gray-400" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openSuperChat()}
                            title="Expandir chat"
                            className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                          >
                            <Maximize2 className="w-4 h-4 text-gray-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setShowExpandedLIA(false)
                              setUserCollapsedLIA(true)
                            }}
                            className="h-7 w-7 p-0 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                          >
                            <X className="w-4 h-4 text-gray-500" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {/* Indicador de candidatos selecionados - Estilo padronizado */}
                    {selectedCandidates.size > 0 && (
                      <div className="flex-shrink-0 px-4 py-2">
                        <div className="px-3 py-2 bg-gray-100 rounded-md border border-gray-200 flex items-center gap-2">
                          <Users className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
                          <span className="text-xs text-gray-700 font-medium">
                            {selectedCandidates.size} candidato{selectedCandidates.size > 1 ? 's' : ''} selecionado{selectedCandidates.size > 1 ? 's' : ''}
                          </span>
                          <button 
                            onClick={() => setSelectedCandidates(new Set())}
                            className="ml-auto p-1 rounded hover:bg-gray-200"
                          >
                            <X className="w-3 h-3 text-gray-500" />
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Sugestões Proativas da LIA */}
                    {computedSuggestions.length > 0 && (
                      <div className="flex-shrink-0 px-4 py-2">
                        <button
                          onClick={() => setShowLiaSuggestionsPanel(prev => !prev)}
                          className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Lightbulb className="w-3.5 h-3.5 text-wedo-cyan" />
                            <span className="text-xs font-semibold text-gray-700" style={{ fontFamily: 'Open Sans, sans-serif' }}>Sugestões da LIA</span>
                            <Badge className="bg-wedo-cyan text-white border-0 text-[10px] px-1.5 py-0 h-4 min-w-[18px] flex items-center justify-center">
                              {computedSuggestions.length}
                            </Badge>
                          </div>
                          {showLiaSuggestionsPanel ? (
                            <ChevronUp className="w-3.5 h-3.5 text-gray-500" />
                          ) : (
                            <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                          )}
                        </button>
                        {showLiaSuggestionsPanel && (
                          <div className="space-y-1.5 mt-2 max-h-[200px] overflow-y-auto">
                            {computedSuggestions.map((suggestion, idx) => {
                              const borderColor = suggestion.type === 'stale_candidate' ? 'border-l-amber-400' : suggestion.type === 'high_score' ? 'border-l-emerald-400' : 'border-l-red-400'
                              const IconComponent = suggestion.type === 'stale_candidate' ? Clock : suggestion.type === 'high_score' ? TrendingUp : AlertTriangle
                              const iconColor = suggestion.type === 'stale_candidate' ? 'text-amber-500' : suggestion.type === 'high_score' ? 'text-emerald-500' : 'text-red-500'
                              return (
                                <div key={`suggestion-${idx}`} className={`border-l-2 ${borderColor} bg-white rounded-r-lg px-2.5 py-2 border border-gray-100`}>
                                  <div className="flex items-start gap-2">
                                    <IconComponent className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${iconColor}`} />
                                    <div className="flex-1 min-w-0">
                                      <p className="text-[11px] text-gray-700 leading-tight" style={{ fontFamily: 'Open Sans, sans-serif' }}>{suggestion.message}</p>
                                      <p className="text-[10px] text-gray-500 mt-0.5" style={{ fontFamily: 'Open Sans, sans-serif' }}>{suggestion.suggested_action}</p>
                                    </div>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        const candidate = Object.values(candidatesData).flat().find((c: any) => c.id === suggestion.candidate_id)
                                        if (candidate) {
                                          setSelectedCandidate(candidate)
                                          setShowCandidatePage(true)
                                        }
                                      }}
                                      className="text-[10px] font-medium px-2 py-0.5 rounded-full hover:bg-gray-100 transition-colors flex-shrink-0"
                                      className="text-wedo-cyan"
                                    >
                                      Ver
                                    </button>
                                  </div>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Área de Mensagens do Chat - Só aparece quando há mensagens */}
                    {liaMessages.length > 0 ? (
                      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
                        {liaMessages.map((msg) => (
                          <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {msg.type === 'user' ? (
                              <div className="flex items-start gap-2 max-w-[90%]">
                                <img 
                                  src="https://randomuser.me/api/portraits/men/32.jpg" 
                                  alt="Você"
                                  className="w-6 h-6 rounded-full object-cover flex-shrink-0"
                                />
                                <div 
                                  className="px-2.5 py-2 rounded-md bg-gray-100"
                                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                                >
                                  <p className="text-[11px] text-gray-800 leading-relaxed">{msg.content}</p>
                                </div>
                              </div>
                            ) : (
                              <div 
                                className="max-w-[90%] group"
                                style={{ fontFamily: 'Open Sans, sans-serif' }}
                              >
                                <div className="flex items-start gap-2">
                                  <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                                    <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                                  </div>
                                  <div className="pt-0.5 flex-1">
                                    <div className="flex items-center gap-1 mb-0.5">
                                      <span className="text-[10px] font-bold text-gray-800" style={{ fontFamily: 'Inter, sans-serif' }}>LIA</span>
                                    </div>
                                    <div className="text-[11px] text-gray-800 space-y-1 leading-relaxed">
                                      {msg.content.split('\n').map((line, i) => {
                                        if (line.startsWith('•')) {
                                          return <p key={i} className="pl-2">{line}</p>
                                        }
                                        if (line.match(/^\d+\./)) {
                                          return <p key={i} className="pl-2">{line}</p>
                                        }
                                        if (line.includes('**')) {
                                          const parts = line.split(/\*\*(.*?)\*\*/g)
                                          return (
                                            <p key={i}>
                                              {parts.map((part, j) => 
                                                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                                              )}
                                            </p>
                                          )
                                        }
                                        return line ? <p key={i}>{line}</p> : null
                                      })}
                                    </div>
                                    {(msg as any).metadata?.action_executed && (msg as any).metadata?.action_result && (
                                      <ActionResultCard
                                        actionType={(msg as any).metadata.action_type || 'move_candidate'}
                                        result={(msg as any).metadata.action_result}
                                      />
                                    )}
                                    {(msg as any).metadata?.is_fallback && (
                                      <button
                                        onClick={() => handleLiaUiAction(
                                          (msg as any).metadata.ui_action,
                                          (msg as any).metadata.ui_action_params || {}
                                        )}
                                        className="mt-2 px-3 py-1.5 text-xs font-medium text-white bg-gray-900 hover:bg-gray-800 rounded transition-colors"
                                        style={{ fontFamily: 'Inter, sans-serif' }}
                                      >
                                        Abrir manualmente
                                      </button>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                        
                        {isLiaLoading && (
                          <div className="flex justify-start">
                            <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-gray-100 dark:bg-gray-800">
                              <div className="w-5 h-5 rounded-md bg-white flex items-center justify-center">
                                <Loader2 className="w-3 h-3 animate-spin text-gray-600 dark:text-gray-400" />
                              </div>
                              <span className="text-[10px] text-gray-500">Pensando...</span>
                            </div>
                          </div>
                        )}
                        
                        <div ref={chatScrollRef} />
                      </div>
                    ) : (
                      /* Espaço flexível vazio quando não há mensagens - empurra conteúdo para baixo */
                      <div className="flex-1" />
                    )}

                    {/* Input Area - Fixo na parte inferior */}
                    <div className="flex-shrink-0 px-4 pb-4 pt-2">
                      {/* Campo de Input */}
                      <div className="flex items-center gap-2 p-2 rounded-md border bg-white border-gray-100">
                        <input
                          type="text"
                          placeholder="Envie mensagem para a LIA..."
                          value={liaPromptValue}
                          onChange={(e) => setLiaPromptValue(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && liaPromptValue.trim() && !isLiaLoading) {
                              handleAICommand(liaPromptValue);
                              setLiaPromptValue('');
                            }
                          }}
                          disabled={isLiaLoading}
                          className="flex-1 text-xs bg-transparent focus:outline-none text-gray-950 dark:text-gray-50 disabled:opacity-50"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        />
                        <AudioRecordButton
                          onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
                          className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-gray-100 transition-colors"
                        />
                        <button
                          type="button"
                          onClick={() => {
                            if (liaPromptValue.trim() && !isLiaLoading) {
                              handleAICommand(liaPromptValue);
                              setLiaPromptValue('');
                            }
                          }}
                          disabled={!liaPromptValue.trim() || isLiaLoading}
                          className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors disabled:opacity-50 bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:hover:bg-gray-200"
                        >
                          <Send className="w-3.5 h-3.5 text-white dark:text-gray-900" />
                        </button>
                      </div>
                      
                      {/* Sugestões de Análises - Abaixo do input */}
                      <div className="flex items-center gap-1.5 mt-2">
                        <span className="text-[9px] font-medium text-gray-500" style={{ fontFamily: 'Open Sans, sans-serif' }}>Sugestões:</span>
                        <button
                          onClick={() => setLiaPromptValue('Rankear candidatos desta vaga')}
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-medium text-gray-700 bg-[#F3F4F6] rounded-full hover:bg-gray-200 transition-all"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          <Star className="w-2.5 h-2.5 text-gray-500" />
                          Rankear
                        </button>
                        <button
                          onClick={() => setLiaPromptValue('Comparar os melhores candidatos')}
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-medium text-gray-700 bg-[#F3F4F6] rounded-full hover:bg-gray-200 transition-all"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          <Users className="w-2.5 h-2.5 text-gray-500" />
                          Comparar
                        </button>
                        <CandidateQueriesGuide 
                          onSelectQuery={(query) => setLiaPromptValue(query)}
                          className="!px-2 !py-0.5 !text-[9px] !bg-[#F3F4F6] !border-0 hover:!bg-gray-200"
                        />
                      </div>
                    </div>
                  </Card>
                  {/* Barra de redimensionamento */}
                  <div
                    className="absolute right-0 top-0 w-2 h-full cursor-ew-resize group flex items-center justify-center z-10"
                    onMouseDown={(e) => {
                      e.preventDefault()
                      setIsResizingLIA(true)
                    }}
                  >
                    <div className="w-0.5 h-12 bg-gray-300 group-hover:bg-gray-600 rounded-full transition-colors" />
                  </div>
                </div>
            )}

            {/* Visualização Kanban */}
            {viewMode === "kanban" && !showSuperChat && (
              <>
                {/* Painel de Filtros - KANBAN */}
              {showKanbanFiltersPanel && (
                <div className="flex-shrink-0 w-72 transition-all duration-300">
                  <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700 rounded-md">
                    {/* Header do Painel */}
                    <div className="flex-shrink-0 p-4 border-b border-gray-100">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Filter className="w-4 h-4 text-gray-600" />
                          <h3 className={textStyles.title}>
                            Filtros Avançados
                          </h3>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowKanbanFiltersPanel(false)}
                          className="h-7 w-7 p-0 hover:bg-gray-100"
                        >
                          <X className="w-4 h-4 text-gray-600" />
                        </Button>
                      </div>
                      <p className={`${textStyles.description} mt-1`}>
                        Refine os candidatos exibidos
                      </p>
                    </div>

                    {/* Conteúdo dos Filtros - Scrollable */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                      {/* Filtro por Score LIA */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Score LIA Mínimo
                        </label>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={kanbanScoreMin}
                            onChange={(e) => setKanbanScoreMin(Number(e.target.value))}
                            className="flex-1 h-1.5 bg-gray-200 rounded-md appearance-none cursor-pointer accent-gray-900"
                          />
                          <span className="text-xs text-gray-600 w-12 text-right">{kanbanScoreMin}%</span>
                        </div>
                      </div>

                      {/* Filtro por Status */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Status
                        </label>
                        <div className="space-y-1.5">
                          {['novo', 'em_analise', 'aguardando_aprovacao', 'triado_aprovado', 'negociacao'].map((status) => (
                            <label key={status} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={kanbanStatusFilter.includes(status)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setKanbanStatusFilter([...kanbanStatusFilter, status])
                                  } else {
                                    setKanbanStatusFilter(kanbanStatusFilter.filter(s => s !== status))
                                  }
                                }}
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {status === 'novo' ? 'Novo' :
                                 status === 'em_analise' ? 'Em análise' :
                                 status === 'aguardando_aprovacao' ? 'Aguardando aprovação' :
                                 status === 'triado_aprovado' ? 'Triado aprovado' :
                                 'Negociação'}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Filtro por Origem */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Origem
                        </label>
                        <div className="space-y-1.5">
                          {[
                            { value: 'web', label: 'Web' },
                            { value: 'whatsapp', label: 'WhatsApp' },
                            { value: 'sourcing', label: 'Busca Ativa' },
                            { value: 'ats', label: 'ATS' },
                          ].map(({ value, label }) => (
                            <label key={value} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={kanbanOriginFilter.includes(value)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setKanbanOriginFilter([...kanbanOriginFilter, value])
                                  } else {
                                    setKanbanOriginFilter(kanbanOriginFilter.filter(o => o !== value))
                                  }
                                }}
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {label}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Filtro por Modelo de Trabalho */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Modelo de Trabalho
                        </label>
                        <div className="space-y-1.5">
                          {['remoto', 'hibrido', 'presencial'].map((modelo) => (
                            <label key={modelo} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={kanbanWorkModelFilter.includes(modelo)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setKanbanWorkModelFilter([...kanbanWorkModelFilter, modelo])
                                  } else {
                                    setKanbanWorkModelFilter(kanbanWorkModelFilter.filter(m => m !== modelo))
                                  }
                                }}
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {modelo === 'remoto' ? 'Remoto' : modelo === 'hibrido' ? 'Híbrido' : 'Presencial'}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Footer com Ações */}
                    <div className="flex-shrink-0 p-4 border-t border-gray-100 bg-gray-50">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setKanbanScoreMin(0)
                            setKanbanStatusFilter([])
                            setKanbanWorkModelFilter([])
                            setKanbanOriginFilter([])
                          }}
                          className="flex-1 px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          Limpar
                        </button>
                        <button
                          onClick={() => setShowKanbanFiltersPanel(false)}
                          className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors bg-gray-800" style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          Aplicar
                        </button>
                      </div>
                    </div>
                  </Card>
                </div>
              )}

              <div className="flex-1 overflow-x-auto overflow-y-hidden" suppressHydrationWarning>
                <div className="p-4 h-full" suppressHydrationWarning>
                  {(!hasMounted || isLoadingCandidates) ? (
                    <div className="flex gap-3 h-full min-w-max" suppressHydrationWarning>
                      {dynamicStages.map((stage) => (
                        <div key={stage.id} className="flex flex-col flex-1 bg-white rounded-md min-w-[250px] max-w-[320px] border border-gray-200 h-[calc(100vh-16rem)]" suppressHydrationWarning>
                          <div className="flex-shrink-0 p-2.5 pb-1.5">
                            <div className="flex items-center gap-1.5">
                              <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: stage.color }}></div>
                              <h3 className="font-medium text-xs text-gray-400">{stage.displayName}</h3>
                              <span className="text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded-full animate-pulse">...</span>
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
                          <span className="text-xs text-gray-400 group-hover:text-gray-600 font-medium transition-colors" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                            Adicionar Coluna
                          </span>
                        </div>
                      </div>
                      {showAddColumnPopover && (
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowAddColumnPopover(false)}>
                          <div className="bg-white rounded-md w-[420px] max-h-[600px] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
                            <div className="flex items-center justify-between mb-4">
                              <h3 className="text-sm font-semibold text-neutral-800" style={{ fontFamily: 'Open Sans, sans-serif' }}>Adicionar Coluna ao Pipeline</h3>
                              <button onClick={() => setShowAddColumnPopover(false)} className="p-1 rounded hover:bg-neutral-100"><X className="w-4 h-4 text-neutral-400" /></button>
                            </div>
                            
                            <div className="space-y-3 mb-4">
                              <label className="text-xs font-medium text-neutral-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>Nome da Etapa</label>
                              <input
                                type="text"
                                value={newColumnName}
                                onChange={(e) => {
                                  setNewColumnName(e.target.value)
                                  setInferredBehavior(null)
                                }}
                                placeholder="Ex: Teste de Lógica, Entrevista Cultural..."
                                className="w-full px-3 py-2.5 text-sm border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-neutral-400 focus:border-neutral-400 transition-all"
                                style={{ fontFamily: 'Open Sans, sans-serif' }}
                              />
                              {newColumnName.length >= 3 && !inferredBehavior && (
                                <button
                                  onClick={async () => {
                                    try {
                                      const res = await fetch('/api/backend-proxy/recruitment-stages/stages/infer-behavior', {
                                        method: 'POST',
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({ stage_name: newColumnName })
                                      })
                                      if (res.ok) {
                                        const data = await res.json()
                                        setInferredBehavior(data)
                                      }
                                    } catch {}
                                  }}
                                  className="text-xs px-3 py-1.5 rounded border border-neutral-200 hover:bg-neutral-50 text-neutral-600 transition-all"
                                >
                                  Sugerir tipo de ação
                                </button>
                              )}
                              {inferredBehavior && (
                                <div className="flex items-center gap-2 p-2 rounded bg-neutral-50 border border-neutral-200">
                                  <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-wedo-cyan/15 text-wedo-cyan">
                                    {inferredBehavior.suggested_behavior}
                                  </span>
                                  <span className="text-[10px] text-neutral-400">
                                    {Math.round(inferredBehavior.confidence * 100)}% confiança
                                  </span>
                                </div>
                              )}
                            </div>
                            
                            <button
                              disabled={newColumnName.length < 2 || isAddingColumn}
                              onClick={async () => {
                                setIsAddingColumn(true)
                                const maxOrder = dynamicStages.filter(s => !s.isFinal && !s.isHired && !s.isRejection).reduce((max, s) => Math.max(max, s.order), 0)
                                const stageName = newColumnName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')
                                try {
                                  const response = await fetch('/api/backend-proxy/recruitment-stages/stages', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                      name: stageName,
                                      display_name: newColumnName,
                                      stage_order: maxOrder + 1,
                                      action_behavior: inferredBehavior?.suggested_behavior || 'passive',
                                      color: '#94A3B8',
                                      is_system: false,
                                    })
                                  })
                                  const result = await response.json()
                                  const backendId = result?.id || `custom_${Date.now()}`
                                  const newStage: DynamicStage = {
                                    id: backendId,
                                    name: stageName,
                                    displayName: newColumnName,
                                    order: maxOrder + 1,
                                    color: '#94A3B8',
                                    stageType: 'active',
                                    isHired: false,
                                    isRejection: false,
                                    isFinal: false,
                                  }
                                  setDynamicStages(prev => {
                                    const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                                    const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                                    return [...activeStages, newStage, ...finalStages]
                                  })
                                  setCandidatesData(prev => ({ ...prev, [newStage.id]: [] }))
                                  setShowAddColumnPopover(false)
                                  setNewColumnName("")
                                  setInferredBehavior(null)
                                  console.log('[Pipeline] Column persisted to backend:', newStage.displayName, backendId)
                                } catch (err) {
                                  console.error('[Pipeline] Failed to persist column, adding locally:', err)
                                  const newStage: DynamicStage = {
                                    id: `custom_${Date.now()}`,
                                    name: stageName,
                                    displayName: newColumnName,
                                    order: maxOrder + 1,
                                    color: '#94A3B8',
                                    stageType: 'active',
                                    isHired: false,
                                    isRejection: false,
                                    isFinal: false,
                                  }
                                  setDynamicStages(prev => {
                                    const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                                    const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                                    return [...activeStages, newStage, ...finalStages]
                                  })
                                  setCandidatesData(prev => ({ ...prev, [newStage.id]: [] }))
                                  setShowAddColumnPopover(false)
                                  setNewColumnName("")
                                  setInferredBehavior(null)
                                } finally {
                                  setIsAddingColumn(false)
                                }
                              }}
                              className="w-full py-2.5 rounded text-sm font-medium text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                              style={{ backgroundColor: newColumnName.length >= 2 && !isAddingColumn ? '#171717' : '#a3a3a3', fontFamily: 'Open Sans, sans-serif' }}
                            >
                              {isAddingColumn ? 'Adicionando...' : 'Adicionar Coluna'}
                            </button>
                            
                            <div className="mt-4 pt-4 border-t border-neutral-100">
                              <label className="text-xs font-medium text-neutral-500 mb-2 block" style={{ fontFamily: 'Open Sans, sans-serif' }}>Ou escolha do catálogo:</label>
                              <div className="grid grid-cols-2 gap-2">
                                {[
                                  { name: 'Teste Técnico', behavior: 'evaluation', color: '#E8B8B8' },
                                  { name: 'Teste de Inglês', behavior: 'evaluation', color: '#E5C5C5' },
                                  { name: 'Entrevista Técnica', behavior: 'scheduling', color: '#F59E0B' },
                                  { name: 'Entrevista Gestor', behavior: 'scheduling', color: '#10B981' },
                                  { name: 'Entrevista Final', behavior: 'scheduling', color: '#D5BFA8' },
                                  { name: 'Dinâmica de Grupo', behavior: 'scheduling', color: '#A78BFA' },
                                  { name: 'Referências', behavior: 'verification', color: '#E8E4E0' },
                                  { name: 'Case / Estudo', behavior: 'evaluation', color: '#D4A8A8' },
                                ].filter(cat => !dynamicStages.some(ds => ds.displayName === cat.name)).map(cat => (
                                  <button
                                    key={cat.name}
                                    disabled={isAddingColumn}
                                    onClick={async () => {
                                      setIsAddingColumn(true)
                                      const maxOrder = dynamicStages.filter(s => !s.isFinal && !s.isHired && !s.isRejection).reduce((max, s) => Math.max(max, s.order), 0)
                                      const stageName = cat.name.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_/]/g, '')
                                      try {
                                        const response = await fetch('/api/backend-proxy/recruitment-stages/stages', {
                                          method: 'POST',
                                          headers: { 'Content-Type': 'application/json' },
                                          body: JSON.stringify({
                                            name: stageName,
                                            display_name: cat.name,
                                            stage_order: maxOrder + 1,
                                            action_behavior: cat.behavior || 'passive',
                                            color: cat.color,
                                            is_system: false,
                                          })
                                        })
                                        const result = await response.json()
                                        const backendId = result?.id || `catalog_${Date.now()}_${stageName}`
                                        const newStage: DynamicStage = {
                                          id: backendId,
                                          name: stageName,
                                          displayName: cat.name,
                                          order: maxOrder + 1,
                                          color: cat.color,
                                          stageType: 'active',
                                          isHired: false,
                                          isRejection: false,
                                          isFinal: false,
                                        }
                                        setDynamicStages(prev => {
                                          const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                                          const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                                          return [...activeStages, newStage, ...finalStages]
                                        })
                                        setCandidatesData(prev => ({ ...prev, [newStage.id]: [] }))
                                        setShowAddColumnPopover(false)
                                        setNewColumnName("")
                                        setInferredBehavior(null)
                                        console.log('[Pipeline] Catalog column persisted to backend:', cat.name, backendId)
                                      } catch (err) {
                                        console.error('[Pipeline] Failed to persist catalog column, adding locally:', err)
                                        const newStage: DynamicStage = {
                                          id: `catalog_${Date.now()}_${stageName}`,
                                          name: stageName,
                                          displayName: cat.name,
                                          order: maxOrder + 1,
                                          color: cat.color,
                                          stageType: 'active',
                                          isHired: false,
                                          isRejection: false,
                                          isFinal: false,
                                        }
                                        setDynamicStages(prev => {
                                          const finalStages = prev.filter(s => s.isFinal || s.isHired || s.isRejection)
                                          const activeStages = prev.filter(s => !s.isFinal && !s.isHired && !s.isRejection)
                                          return [...activeStages, newStage, ...finalStages]
                                        })
                                        setCandidatesData(prev => ({ ...prev, [newStage.id]: [] }))
                                        setShowAddColumnPopover(false)
                                        setNewColumnName("")
                                        setInferredBehavior(null)
                                      } finally {
                                        setIsAddingColumn(false)
                                      }
                                    }}
                                    className="flex items-center gap-2 p-2 rounded-sm border border-neutral-200 hover:border-neutral-400 hover:bg-neutral-50 transition-all text-left disabled:opacity-50 disabled:cursor-not-allowed"
                                  >
                                    <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: cat.color }} />
                                    <span className="text-[11px] text-neutral-700 font-medium" style={{ fontFamily: 'Open Sans, sans-serif' }}>{cat.name}</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )
                  })()}
                </div>
              </div>

              {/* Preview do Candidato - Painel Lateral Direito (KANBAN) */}
              {isPreviewOpen && previewCandidate && (
                <div className={`flex-shrink-0 transition-all duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-[400px]'}`}>
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
              <>
              {/* Painel de Filtros - TABLE */}
              {showTableFiltersPanel && (
                <div className="flex-shrink-0 w-72 transition-all duration-300">
                  <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700 rounded-md">
                    {/* Header do Painel de Filtros */}
                    <div className="flex-shrink-0 p-4 border-b border-gray-100">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Filter className="w-4 h-4 text-gray-600" />
                          <h3 className={textStyles.title}>
                            Filtros Avançados
                          </h3>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowTableFiltersPanel(false)}
                          className="h-7 w-7 p-0 hover:bg-gray-100"
                        >
                          <X className="w-4 h-4 text-gray-600" />
                        </Button>
                      </div>
                      <p className={`${textStyles.description} mt-1`}>
                        Refine os candidatos exibidos
                      </p>
                    </div>

                    {/* Conteúdo dos Filtros - Scrollable */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                      {/* Filtro por Etapa */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Etapa do Pipeline
                        </label>
                        <div className="space-y-1.5">
                          {dynamicStages.map((stage) => (
                            <label key={stage.id} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={tableStageFilter.includes(stage.id)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setTableStageFilter([...tableStageFilter, stage.id])
                                  } else {
                                    setTableStageFilter(tableStageFilter.filter(s => s !== stage.id))
                                  }
                                }}
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {stage.displayName}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Filtro por Score LIA */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Score LIA Mínimo
                        </label>
                        <div className="flex items-center gap-2">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            defaultValue="0"
                            className="flex-1 h-1.5 bg-gray-200 rounded-md appearance-none cursor-pointer accent-gray-900"
                          />
                          <span className="text-xs text-gray-600 w-8 text-right">0%</span>
                        </div>
                      </div>

                      {/* Filtro por Status */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Status
                        </label>
                        <div className="space-y-1.5">
                          {['Novo', 'Em análise', 'Aguardando aprovação', 'Triado aprovado', 'Negociação'].map((status) => (
                            <label key={status} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {status}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>

                      {/* Filtro por Modelo de Trabalho */}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                          Modelo de Trabalho
                        </label>
                        <div className="space-y-1.5">
                          {['Remoto', 'Híbrido', 'Presencial'].map((modelo) => (
                            <label key={modelo} className="flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-900/20"
                              />
                              <span className="text-xs text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
                                {modelo}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Footer com Ações */}
                    <div className="flex-shrink-0 p-4 border-t border-gray-100 bg-gray-50">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setTableStageFilter([])
                          }}
                          className="flex-1 px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          Limpar
                        </button>
                        <button
                          onClick={() => setShowTableFiltersPanel(false)}
                          className="flex-1 px-3 py-2 text-xs font-medium text-white rounded-md transition-colors bg-gray-800" style={{ fontFamily: 'Open Sans, sans-serif' }}
                        >
                          Aplicar
                        </button>
                      </div>
                    </div>
                  </Card>
                </div>
              )}

              {/* Conteúdo da Tabela */}
              <div className="flex-1 overflow-hidden bg-gray-50 dark:bg-gray-950 flex flex-col min-w-0">
                <div className="flex-1 overflow-auto px-4 py-2">
                {/* Tabela Elegante - Unified Component */}
                {(() => {
                  const nameCol = getColumnDefinition('candidate')
                  const titleCol = getColumnDefinition('role')
                  const companyCol = getColumnDefinition('currentCompany')

                  const unifiedColumns: TableColumn[] = [
                    { id: 'quickActions', label: 'Aprovação', visible: true, sortable: false, align: 'center', width: 120 },
                    { id: 'id', label: 'ID', visible: true, sortable: false, width: 55 },
                    { id: 'score', label: 'Geral', visible: true, sortable: true, width: 70 },
                    { id: 'liaScore', label: 'Triagem', visible: true, sortable: true, width: 80 },
                    { id: 'fitScore', label: 'CV', visible: true, sortable: true, width: 60 },
                    { id: 'technicalTestScore', label: 'Técnico', visible: true, sortable: true, width: 75 },
                    { id: 'englishTestScore', label: 'Inglês', visible: true, sortable: true, width: 70 },
                    { id: 'bigFive', label: 'B5', visible: true, sortable: false, width: 55 },
                    { id: 'name', label: nameCol?.label || 'Candidato', visible: true, sortable: nameCol?.sortable ?? true, width: 280 },
                    { id: 'role', label: titleCol?.label || 'Cargo', visible: true, sortable: titleCol?.sortable ?? false, width: 150 },
                    { id: 'currentCompany', label: companyCol?.label || 'Empresa', visible: true, sortable: companyCol?.sortable ?? false, width: companyCol?.width || 130 },
                    { id: 'stage', label: 'Etapa', visible: true, sortable: true, width: 85 },
                    { id: 'status', label: 'Status', visible: true, sortable: false, width: 85 }
                  ]

                  return (
                    <UnifiedCandidateTable
                      candidates={getPaginatedCandidates().candidates}
                      columns={unifiedColumns}
                      selectedIds={selectedCandidates}
                      sortConfig={tableSortColumn ? { 
                        field: tableSortColumn, 
                        direction: tableSortDirection 
                      } : undefined}
                      showCheckboxes={true}
                      emptyMessage="Nenhum candidato nesta etapa"
                      enableColumnResize={true}
                      isInteractive={true}
                      jobVacancyId={jobData?.id?.toString()}
                      onColumnResize={handleTableColumnResize}
                      onCandidateClick={handleOpenPreview}
                      onSelectionChange={(newSelection) => setSelectedCandidates(newSelection)}
                      onSortChange={(config) => {
                        setTableSortColumn(config.field)
                        setTableSortDirection(config.direction)
                      }}
                      onStatusChange={handleInteractiveStatusChange}
                      onTransitionRequest={handleTableTransitionRequest}
                      renderCustomHeader={(columnId: string, defaultLabel: string) => {
                        if (columnId === 'quickActions') {
                          const isSat = saturationData?.is_saturated || (saturationData?.saturation_percentage ?? 0) >= 90
                          return (
                            <span className="flex items-center gap-1 whitespace-nowrap">
                              {defaultLabel}
                              {isSat && saturationData && (
                                <span
                                  className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[9px] font-medium font-['Open_Sans'] ${
                                    saturationData.is_saturated
                                      ? 'text-red-600 bg-red-50 border border-red-200'
                                      : 'text-amber-600 bg-amber-50 border border-amber-200'
                                  }`}
                                  title={`Pipeline ${saturationData.is_saturated ? 'Saturado' : 'Quase saturado'} (${saturationData.approved_count}/${saturationData.saturation_threshold})`}
                                >
                                  <AlertTriangle className="w-2.5 h-2.5" />
                                  {saturationData.approved_count}/{saturationData.saturation_threshold}
                                </span>
                              )}
                            </span>
                          )
                        }
                        return null
                      }}
                      renderCustomCell={(candidate: any, columnId: string) => {
                        const ranking = calculateNotaLiaGeral(candidate)
                        const alerts = getLiaAlerts(candidate)
                        const urgency = getUrgencyLevel(ranking)

                        switch (columnId) {
                          case 'id':
                            return (
                              <div className="text-xs font-mono text-gray-600 dark:text-gray-400">
                                {candidate.candidateCode || candidate.id?.substring(0, 6).toUpperCase()}
                              </div>
                            )

                          case 'score':
                            const hasNotaGeral = ranking !== null && ranking !== undefined && ranking > 0
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasNotaGeral ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasNotaGeral) {
                                    setSelectedCandidateForModal(candidate)
                                    setActiveModal('notaGeral')
                                  }
                                }}
                                title={hasNotaGeral ? 'Clique para ver detalhes' : 'Não avaliado'}
                              >
                                <Gauge className="w-3.5 h-3.5" style={{ color: hasNotaGeral ? '#111827' : '#9CA3AF' }} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasNotaGeral ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                                  {hasNotaGeral ? ranking : '—'}
                                </span>
                              </div>
                            )

                          case 'liaScore':
                            const hasTriagem = (candidate.liaScore !== null && candidate.liaScore !== undefined) || (candidate.score !== null && candidate.score !== undefined)
                            const triagemValue = candidate.liaScore ?? candidate.score
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTriagem ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasTriagem) {
                                    handleOpenTriagem(candidate)
                                  }
                                }}
                                title={hasTriagem ? 'Clique para ver Triagem LIA' : 'Não avaliado'}
                              >
                                <Brain className={`w-3.5 h-3.5 ${hasTriagem ? 'text-wedo-cyan' : 'text-gray-400'}`} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasTriagem ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                                  {hasTriagem ? formatScorePercent(triagemValue, 0) : '—'}
                                </span>
                              </div>
                            )

                          case 'fitScore':
                            const hasFitScore = (candidate.skillsMatch !== null && candidate.skillsMatch !== undefined && candidate.skillsMatch > 0) || (candidate.fitScore !== null && candidate.fitScore !== undefined && candidate.fitScore > 0)
                            const fitValue = candidate.skillsMatch || candidate.fitScore || 0
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasFitScore ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasFitScore) {
                                    handleOpenAnalysis(candidate)
                                  }
                                }}
                                title={hasFitScore ? 'Clique para ver Análise CV vs Vaga' : 'Não avaliado'}
                              >
                                <Target className="w-3.5 h-3.5" style={{ color: hasFitScore ? '#111827' : '#9CA3AF' }} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasFitScore ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                                  {hasFitScore ? formatScorePercent(fitValue, 0) : '—'}
                                </span>
                              </div>
                            )

                          case 'technicalTestScore':
                            const hasTechnical = candidate.technicalTestScore !== null && candidate.technicalTestScore !== undefined
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasTechnical ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasTechnical) {
                                    setSelectedCandidateForModal(candidate)
                                    setActiveModal('testeTecnico')
                                  }
                                }}
                                title={hasTechnical ? 'Clique para ver detalhes' : 'Não realizado'}
                              >
                                <Code className="w-3.5 h-3.5" style={{ color: hasTechnical ? '#374151' : '#9CA3AF' }} strokeWidth={2} />
                                {hasTechnical && (
                                  <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                                    {formatScorePercent(candidate.technicalTestScore, 0)}
                                  </span>
                                )}
                              </div>
                            )

                          case 'englishTestScore':
                            const hasEnglish = candidate.englishTestScore !== null && candidate.englishTestScore !== undefined
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasEnglish ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasEnglish) {
                                    setSelectedCandidateForModal(candidate)
                                    setActiveModal('testeIngles')
                                  }
                                }}
                                title={hasEnglish ? 'Clique para ver detalhes' : 'Não realizado'}
                              >
                                <Globe className="w-3.5 h-3.5" style={{ color: hasEnglish ? '#374151' : '#9CA3AF' }} strokeWidth={2} />
                                {hasEnglish && (
                                  <span className="text-xs font-semibold text-gray-950 dark:text-gray-50">
                                    {formatScorePercent(candidate.englishTestScore, 0)}
                                  </span>
                                )}
                              </div>
                            )

                          case 'bigFive':
                            const hasBigFive = candidate.bigFive || candidate.bigFiveScores
                            const bigFiveData = candidate.bigFive || candidate.bigFiveScores || {}
                            const bigFiveValues = Object.values(bigFiveData).filter((v): v is number => typeof v === 'number')
                            const bigFiveAvg = bigFiveValues.length > 0 ? Math.round(bigFiveValues.reduce((a, b) => a + b, 0) / bigFiveValues.length) : null
                            return (
                              <div 
                                className={`flex items-center gap-1 justify-center cursor-pointer group ${hasBigFive ? '' : 'opacity-40'}`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  if (hasBigFive) {
                                    setSelectedCandidateForModal(candidate)
                                    setShowBigFiveModal(true)
                                  }
                                }}
                                title={hasBigFive ? 'Clique para ver relatório Big Five completo' : 'Não realizado'}
                              >
                                <Fingerprint className="w-3.5 h-3.5" style={{ color: hasBigFive ? '#374151' : '#9CA3AF' }} strokeWidth={2} />
 <span className={`text-xs font-semibold ${hasBigFive ? 'text-gray-950' : 'text-gray-400 dark:text-gray-600'}`}>
                                  {hasBigFive && bigFiveAvg !== null ? bigFiveAvg : '—'}
                                </span>
                              </div>
                            )

                          case 'quickActions':
                            const quickActionStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                            const isAlreadyDecided = quickActionStage === 'aprovados' || quickActionStage === 'reprovados'
                            const showNeedsAction = candidate.needsAction === true
                            
                            if (isAlreadyDecided) {
                              return null
                            }
                            
                            return (
                              <div className="relative flex items-center justify-center">
                                {/* Indicador "Ação Necessária" - aparece quando não está em hover */}
                                {showNeedsAction && (
                                  <div className="flex items-center gap-1 group-hover:hidden transition-opacity">
                                    <Flag className="w-3.5 h-3.5 text-amber-500" strokeWidth={2} />
                                  </div>
                                )}
                                {/* Botões de ação - aparecem no hover */}
                                <div className="hidden group-hover:flex items-center justify-center gap-1.5">
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      if (quickActionStage === 'screening' || quickActionStage === 'triagem') {
                                        handleApproveFromScreening(candidate)
                                      } else {
                                        openDecisionFlowModal(candidate, 'approve')
                                      }
                                    }}
                                    className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity bg-gray-800"
                                    title="Aprovar candidato"
                                  >
                                    <ThumbsUp className="w-3.5 h-3.5 text-white" strokeWidth={2} />
                                  </button>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      if (quickActionStage === 'screening' || quickActionStage === 'triagem') {
                                        handleRejectFromScreening(candidate)
                                      } else {
                                        openDecisionFlowModal(candidate, 'reject')
                                      }
                                    }}
                                    className="w-7 h-7 rounded-full flex items-center justify-center hover:opacity-80 transition-opacity bg-wedo-coral"
                                    title="Reprovar candidato"
                                  >
                                    <XCircle className="w-3.5 h-3.5 text-white" strokeWidth={2} />
                                  </button>
                                </div>
                              </div>
                            )

                          case 'name':
                            const getAvatarUrl = (id: string, name: string): string => {
                              let hash = 0
                              const str = id + name
                              for (let i = 0; i < str.length; i++) {
                                const char = str.charCodeAt(i)
                                hash = ((hash << 5) - hash) + char
                                hash = hash & hash
                              }
                              const avatarIndex = Math.abs(hash % 70) + 1
                              const gender = Math.abs(hash % 2) === 0 ? 'men' : 'women'
                              return `https://randomuser.me/api/portraits/${gender}/${avatarIndex}.jpg`
                            }
                            const avatarUrl = candidate.avatar?.startsWith('http') ? candidate.avatar : getAvatarUrl(candidate.id || '', candidate.name || '')
                            const isDemo = !candidate.avatar?.startsWith('http') || candidate.isDemo
                            return (
                              <div className="flex items-center gap-2">
                                <div className="relative">
                                  <Avatar className="w-8 h-8">
                                    <AvatarImage src={avatarUrl} alt={candidate.name} />
                                    <AvatarFallback>{candidate.name.split(' ').map((n: string) => n[0]).join('')}</AvatarFallback>
                                  </Avatar>
                                  {viewedCandidateIds.has(candidate.id) && (
                                    <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-gray-300 rounded-full flex items-center justify-center border border-white" title="Perfil visualizado">
                                      <Eye className="w-2.5 h-2.5 text-white" />
                                    </div>
                                  )}
                                </div>
                                <div className="flex items-center gap-1.5">
                                  {isDemo && (
                                    <span className="text-[10px] font-medium text-gray-400 dark:text-gray-500">[D]</span>
                                  )}
                                  <span className="font-medium text-sm text-gray-950 dark:text-gray-50">
                                    {candidate.name}
                                  </span>
                                  {(() => {
                                    const dataRequest = getDataRequestForCandidate(candidate.id)
                                    if (!dataRequest) return null
                                    return (
                                      <DataRequestIndicator
                                        candidateId={candidate.id}
                                        status={dataRequest.status}
                                        fieldsRequested={dataRequest.fieldsRequested}
                                        fieldsCompleted={dataRequest.fieldsCompleted}
                                        expiresAt={dataRequest.expiresAt || undefined}
                                        size="sm"
                                        onResend={handleDataRequestResend}
                                        onViewDetails={handleDataRequestViewDetails}
                                      />
                                    )
                                  })()}
                                </div>
                              </div>
                            )

                          case 'role':
                            return (
                              <div className="text-xs text-gray-950 dark:text-gray-50">
                                {candidate.role || candidate.position || 'UX Designer'}
                              </div>
                            )

                          case 'currentCompany':
                            return (
                              <div className="text-xs text-gray-950 dark:text-gray-50">
                                {candidate.currentCompany || (candidate.source === 'LinkedIn' ? 'TechCorp' : 'Digital Agency')}
                              </div>
                            )

                          case 'stage': {
                            const stageDropdownStages = dynamicStages.map(s => ({ id: s.id, name: s.name, displayName: s.displayName, color: s.color }))
                            const currentStageObj = stageDropdownStages.find(s => s.id === (candidate.stageId || candidate.stage))
                            return (
                              <Popover>
                                <PopoverTrigger asChild>
                                  <button className="inline-flex items-center gap-1 group/stage" onClick={(e) => e.stopPropagation()}>
                                    <Badge
                                      className="text-xs font-semibold border-0 whitespace-nowrap text-gray-950 dark:text-gray-50 cursor-pointer"
                                      style={{ backgroundColor: currentStageObj?.color || '#E5E7EB' }}
                                    >
                                      {currentStageObj?.displayName || candidate.stage}
                                    </Badge>
                                    <ChevronDown className="w-3 h-3 text-gray-400 group-hover/stage:text-gray-600 transition-colors" />
                                  </button>
                                </PopoverTrigger>
                                <PopoverContent className="w-44 p-1.5" align="start" sideOffset={4}>
                                  <div className="space-y-0.5">
                                    {stageDropdownStages.map((stage) => {
                                      const isCurrent = stage.id === (candidate.stageId || candidate.stage)
                                      return (
                                        <button
                                          key={stage.id}
                                          className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs transition-colors ${
                                            isCurrent
                                              ? 'bg-gray-100 dark:bg-gray-800 font-bold'
                                              : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'
                                          }`}
                                          style={{ fontFamily: 'Open Sans, sans-serif' }}
                                          onClick={() => {
                                            if (!isCurrent) {
                                              handleTransitionRequired([candidate], candidate.stageId || candidate.stage, stage.id)
                                            }
                                          }}
                                        >
                                          <div
                                            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                                            style={{ backgroundColor: stage.color }}
                                          />
                                          <span className="flex-1 text-left text-gray-800 dark:text-gray-200 truncate">
                                            {stage.displayName}
                                          </span>
                                          {isCurrent && <CheckCircle className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0" />}
                                        </button>
                                      )
                                    })}
                                  </div>
                                </PopoverContent>
                              </Popover>
                            )
                          }

                          case 'status': {
                            const hasScheduledInterview = !!candidate.agendada
                            return (
                              <div className="flex items-center gap-1.5">
                                <InteractiveSubStatusCell
                                  candidateId={candidate.id}
                                  candidateName={candidate.name}
                                  stage={candidate.stage}
                                  subStatus={candidate.sub_status || candidate.status}
                                  jobVacancyId={jobData?.id?.toString()}
                                  onStatusChange={handleInteractiveStatusChange}
                                />
                                {hasScheduledInterview && (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation()
                                      const stage = candidate.stageId || candidate.stage || 'interview_hr'
                                      const dateStr = candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })
                                      setTransitionInitialPrompt(`O recrutador quer gerenciar a entrevista de ${candidate.name} agendada para ${dateStr}. Pergunte se quer alterar o horário (peça nova data/hora) ou cancelar. Se cancelar, pergunte para qual etapa quer mover o candidato.`)
                                      setTransitionAllowStageSelection(true)
                                      setTransitionInterviewAlert({ name: candidate.name, date: dateStr })
                                      openTransition([candidate], stage, stage)
                                    }}
                                    className="w-5 h-5 rounded flex items-center justify-center text-cyan-600 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 transition-colors flex-shrink-0"
                                    title={`Gerenciar entrevista — ${candidate.interviewDate || new Date(candidate.agendada).toLocaleDateString('pt-BR')}`}
                                  >
                                    <Video className="w-3 h-3" />
                                  </button>
                                )}
                              </div>
                            )
                          }

                          // Busca Global / Pearch columns
                          case 'is_open_to_work':
                            const isOpenToWork = candidate.is_opentowork || candidate.is_open_to_work
                            return isOpenToWork ? (
                              <Badge className="text-xs bg-green-100 text-green-800">Open to Work</Badge>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'is_decision_maker':
                            return candidate.is_decision_maker ? (
                              <Badge className="text-xs bg-purple-100 text-purple-800">Decision Maker</Badge>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'is_top_universities':
                            return candidate.is_top_universities ? (
                              <Badge className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">Top University</Badge>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'is_hiring':
                            return candidate.is_hiring ? (
                              <Badge className="text-xs bg-orange-100 text-orange-800">Contratando</Badge>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'headline':
                            return <span className="text-xs text-gray-800 dark:text-gray-200 truncate">{candidate.headline || ''}</span>
                          
                          case 'expertise':
                            const expertiseArray = candidate.expertise
                            return <span className="text-xs text-gray-800 dark:text-gray-200 truncate">{Array.isArray(expertiseArray) ? expertiseArray.join(', ') : (expertiseArray || '')}</span>
                          
                          case 'linkedin_followers_count':
                            return candidate.linkedin_followers_count ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200">{candidate.linkedin_followers_count.toLocaleString('pt-BR')}</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'linkedin_connections_count':
                            return candidate.linkedin_connections_count ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200">{candidate.linkedin_connections_count.toLocaleString('pt-BR')}</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'outreach_message':
                            return candidate.outreach_message ? (
                              <div className="flex items-center gap-1">
                                <span className="text-xs text-gray-800 dark:text-gray-200 truncate max-w-[200px]">{candidate.outreach_message.slice(0, 50)}...</span>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    navigator.clipboard.writeText(candidate.outreach_message!)
                                  }}
                                  className="p-0.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
                                  title="Copiar mensagem"
                                >
                                  <Copy className="w-3 h-3 text-gray-500" />
                                </button>
                              </div>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'best_personal_email':
                            return candidate.best_personal_email ? (
                              <a href={`mailto:${candidate.best_personal_email}`} className="text-xs text-gray-700 hover:text-gray-900 hover:underline truncate dark:text-gray-300 dark:hover:text-gray-100">
                                {candidate.best_personal_email}
                              </a>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'phone_types':
                            if (!candidate.phone_types || Object.keys(candidate.phone_types).length === 0) {
                              return <span className="text-xs text-gray-400">—</span>
                            }
                            const activePhoneTypes = Object.entries(candidate.phone_types)
                              .filter(([_, active]) => active)
                              .map(([type]) => type)
                            return <span className="text-xs text-gray-800 dark:text-gray-200">{activePhoneTypes.join(', ') || '—'}</span>
                          
                          case 'estimated_age':
                            return candidate.estimated_age ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200">{candidate.estimated_age} anos</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'match_reasoning':
                            return candidate.pearch_insights?.match_reasoning ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate" title={candidate.pearch_insights.match_reasoning}>
                                {candidate.pearch_insights.match_reasoning.slice(0, 60)}...
                              </span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'overall_summary':
                            return candidate.pearch_insights?.overall_summary ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate" title={candidate.pearch_insights.overall_summary}>
                                {candidate.pearch_insights.overall_summary.slice(0, 60)}...
                              </span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'query_insights':
                            const queryInsightsData = candidate.pearch_insights?.query_insights
                            if (!queryInsightsData || queryInsightsData.length === 0) {
                              return <span className="text-xs text-gray-400">—</span>
                            }
                            return (
                              <div className="flex flex-col gap-0.5">
                                {queryInsightsData.slice(0, 2).map((insight: any, idx: number) => (
                                  <div key={idx} className="flex items-center gap-1">
                                    <Badge className={`${textStyles.caption} !text-[10px] px-1 py-0 ${
                                      insight.match_level === 'Exceeds' ? badgeStyles.success :
                                      insight.match_level === 'Meets' ? badgeStyles.info :
                                      insight.match_level === 'Partial' ? badgeStyles.warning :
                                      badgeStyles.default
                                    }`}>
                                      {insight.match_level}
                                    </Badge>
                                    <span className={`${textStyles.caption} dark:!text-gray-400 truncate max-w-[150px]`} title={insight.subquery}>
                                      {insight.subquery?.slice(0, 25)}...
                                    </span>
                                  </div>
                                ))}
                                {queryInsightsData.length > 2 && (
                                  <span className={textStyles.caption}>+{queryInsightsData.length - 2} mais</span>
                                )}
                              </div>
                            )
                          
                          case 'pearch_insights':
                            return candidate.pearch_insights?.overall_summary ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate">{candidate.pearch_insights.overall_summary.slice(0, 50)}...</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'middle_name':
                            return candidate.middle_name ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate">{candidate.middle_name}</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'best_business_email':
                            return candidate.best_business_email ? (
                              <a href={`mailto:${candidate.best_business_email}`} className="text-xs text-gray-700 hover:text-gray-900 hover:underline truncate dark:text-gray-300 dark:hover:text-gray-100">
                                {candidate.best_business_email}
                              </a>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'personal_emails':
                            const personalEmails = candidate.personal_emails
                            if (!personalEmails || personalEmails.length === 0) {
                              return <span className="text-xs text-gray-400">—</span>
                            }
                            return (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate" title={personalEmails.join(', ')}>
                                {personalEmails.length === 1 ? personalEmails[0] : `${personalEmails[0]} (+${personalEmails.length - 1})`}
                              </span>
                            )
                          
                          case 'business_emails':
                            const businessEmails = candidate.business_emails
                            if (!businessEmails || businessEmails.length === 0) {
                              return <span className="text-xs text-gray-400">—</span>
                            }
                            return (
                              <span className="text-xs text-gray-800 dark:text-gray-200 truncate" title={businessEmails.join(', ')}>
                                {businessEmails.length === 1 ? businessEmails[0] : `${businessEmails[0]} (+${businessEmails.length - 1})`}
                              </span>
                            )
                          
                          case 'company_followers_count':
                            return candidate.company_followers_count != null ? (
                              <span className="text-xs text-gray-800 dark:text-gray-200">{candidate.company_followers_count.toLocaleString('pt-BR')}</span>
                            ) : <span className="text-xs text-gray-400">—</span>
                          
                          case 'company_keywords':
                            const companyKeywords = candidate.company_keywords
                            if (!companyKeywords || companyKeywords.length === 0) {
                              return <span className="text-xs text-gray-400">—</span>
                            }
                            return (
                              <div className="flex flex-wrap gap-1">
                                {companyKeywords.slice(0, 3).map((keyword: string, idx: number) => (
                                  <Badge key={idx} variant="outline" className="text-[10px] px-1 py-0 bg-gray-50 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                                    {keyword}
                                  </Badge>
                                ))}
                                {companyKeywords.length > 3 && (
                                  <span className={textStyles.caption}>+{companyKeywords.length - 3}</span>
                                )}
                              </div>
                            )

                          case 'analise':
                            const candidateStage = candidate.stage || candidate.etapa || 'funil'
                            const hasAnalysisData = candidate.liaAnalysis || candidate.cvAnalysis || candidate.score
                            const hasTriagemData = candidate.triagemHistory || candidate.screeningHistory || candidateStage.toLowerCase() !== 'funil'
                            return (
                              <div className="flex items-center justify-center gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 ${hasAnalysisData ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100' : 'text-gray-400 cursor-not-allowed'}`}
                                  title={hasAnalysisData ? "Ver Análise CV vs Vaga" : "Análise pendente"}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (hasAnalysisData) handleOpenAnalysis(candidate)
                                  }}
                                  disabled={!hasAnalysisData}
                                >
                                  <Target className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className={`h-7 w-7 p-0 ${hasTriagemData ? 'text-gray-700 hover:text-gray-900 hover:bg-gray-100' : 'text-gray-400 cursor-not-allowed'}`}
                                  title={hasTriagemData ? "Ver Detalhes da Triagem" : "Triagem pendente"}
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (hasTriagemData) handleOpenTriagem(candidate)
                                  }}
                                  disabled={!hasTriagemData}
                                >
                                  <BrainCircuit className="w-4 h-4" />
                                </Button>
                              </div>
                            )

                          case 'acoes':
                          case 'actions':
                            return (
                              <div className="flex items-center justify-center">
                                <Popover>
                                  <PopoverTrigger asChild>
                                    <button
                                      onClick={(e) => e.stopPropagation()}
                                      className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                      title="Mais ações"
                                    >
                                      <MoreVertical className="w-4 h-4 text-gray-500" />
                                    </button>
                                  </PopoverTrigger>
                                  <PopoverContent align="end" className="w-48 p-1">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleOpenAnalysis(candidate)
                                      }}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                                    >
                                      <Eye className="w-4 h-4" />
                                      Ver perfil completo
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleOpenTriagem(candidate)
                                      }}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                                    >
                                      <Brain className="w-4 h-4 text-wedo-cyan" />
                                      Ver triagem LIA
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        // Abrir modal BigFive
                                        setScoreModalCandidate(candidate)
                                        setShowBigFiveModal(true)
                                      }}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                                    >
                                      <Fingerprint className="w-4 h-4 text-[#8B5CF6]" />
                                      Ver BigFive
                                    </button>
                                    <div className="my-1 border-t border-gray-200 dark:border-gray-700" />
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        const cStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                                        if (cStage === 'screening' || cStage === 'triagem') {
                                          handleApproveFromScreening(candidate)
                                        } else {
                                          openDecisionFlowModal(candidate, 'approve')
                                        }
                                      }}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-800 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-md"
                                    >
                                      <ThumbsUp className="w-4 h-4" />
                                      Aprovar
                                    </button>
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        const cStage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                                        if (cStage === 'screening' || cStage === 'triagem') {
                                          handleRejectFromScreening(candidate)
                                        } else {
                                          openDecisionFlowModal(candidate, 'reject')
                                        }
                                      }}
                                      className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md text-wedo-coral"
                                    >
                                      <XCircle className="w-4 h-4" />
                                      Reprovar
                                    </button>
                                  </PopoverContent>
                                </Popover>
                              </div>
                            )

                          default:
                            return null
                        }
                      }}
                      getNeedsAction={(candidate: any) => {
                        const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                        return stage === 'funil' || stage === 'triagem' || candidate.needsAction === true || candidate.status === 'triado_aprovado'
                      }}
                      renderActions={(candidate: any) => {
                        const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                        const showApproveReject = stage === 'funil' || stage === 'triagem'
                        return (
                          <div className="flex items-center justify-center gap-1" onClick={(e) => e.stopPropagation()}>
                            {showApproveReject && (
                              <>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="h-6 px-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 rounded-full text-[10px] font-semibold" 
                                  title="Aprovar candidato"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    handleApproveCandidate(candidate)
                                  }}
                                >
                                  <ThumbsUp className="w-3 h-3 mr-0.5" />
                                  Aprovar
                                </Button>
                                <Button 
                                  variant="ghost" 
                                  size="sm" 
                                  className="h-6 px-2 bg-red-600 hover:bg-red-700 text-white rounded-full text-[10px] font-semibold" 
                                  title="Reprovar candidato"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    if (stage === 'screening' || stage === 'triagem') {
                                      handleRejectFromScreening(candidate)
                                    } else {
                                      handleRejectCandidate(candidate)
                                    }
                                  }}
                                >
                                  <XCircle className="w-3 h-3 mr-0.5" />
                                  Reprovar
                                </Button>
                              </>
                            )}
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                                  <MoreVertical className="w-4 h-4 text-gray-500 hover:text-gray-800 dark:text-gray-200" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-48">
                                <DropdownMenuItem onClick={() => handleOpenPreview(candidate)}>
                                  <Eye className="w-4 h-4 mr-2" />
                                  Ver Perfil
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleOpenAnalysis(candidate)}>
                                  <Target className="w-4 h-4 mr-2" />
                                  Análise CV
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => handleOpenTriagem(candidate)}>
                                  <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                                  Ver Triagem
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => handleApproveCandidate(candidate)}>
                                  <ThumbsUp className="w-4 h-4 mr-2" />
                                  Aprovar
                                </DropdownMenuItem>
                                <DropdownMenuItem onClick={() => {
                                  if (stage === 'screening' || stage === 'triagem') {
                                    handleRejectFromScreening(candidate)
                                  } else {
                                    handleRejectCandidate(candidate)
                                  }
                                }} className="text-wedo-coral">
                                  <XCircle className="w-4 h-4 mr-2" />
                                  Reprovar
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        )
                      }}
                      getStageBorderColor={(candidate: any) => {
                        const stage = (candidate.stage || candidate.etapa || 'funil').toLowerCase()
                        const stageColors: Record<string, string> = {
                          'funil': '#374151',
                          'triagem': '#F59E0B',
                          'entrevista': '#8B5CF6',
                          'final': '#3B82F6',
                          'aprovados': '#10B981',
                          'reprovados': '#E16162'
                        }
                        return stageColors[stage] || '#111827'
                      }}
                      className="max-h-[calc(100vh-22rem)]"
                    />
                  )
                })()}

                {/* Paginação */}
                {getPaginatedCandidates().totalPages > 1 && (
                  <div className="bg-white dark:bg-gray-900 rounded-md p-3">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-600 dark:text-gray-400">
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
                              // Show first page, last page, current page, and pages around current
                              return page === 1 ||
                                     page === getPaginatedCandidates().totalPages ||
                                     (page >= currentPage - 1 && page <= currentPage + 1)
                            })
                            .map((page, index, array) => (
                              <React.Fragment key={page}>
                                {/* Show ellipsis if there's a gap */}
                                {index > 0 && page - array[index - 1] > 1 && (
                                  <span className="px-2 text-gray-600">...</span>
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
                </div>
              </div>
              {/* Fecha o Conteúdo da Tabela */}

              {/* Preview do Candidato - Painel Lateral Direito */}
              {isPreviewOpen && previewCandidate && (
                <div className={`flex-shrink-0 transition-all duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-[400px]'}`}>
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

              {/* Column Configuration Sidebar - Lado Direito */}
              {showColumnConfig && (
                <div className="flex-shrink-0 w-80 transition-all duration-300">
                  <Card className="h-[calc(100vh-12rem)] flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700 rounded-md">
                    {/* Header */}
                    <div className="flex-shrink-0 p-4 border-b border-gray-100">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Columns className="w-4 h-4 text-gray-600" />
                          <h3 className={textStyles.title}>
                            Configurar Colunas
                          </h3>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowColumnConfig(false)}
                          className="h-7 w-7 p-0 hover:bg-gray-100"
                        >
                          <X className="w-4 h-4 text-gray-600" />
                        </Button>
                      </div>

                      {/* Search and Actions */}
                      <div className="space-y-2">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-600" />
                          <input
                            type="text"
                            placeholder="Buscar coluna..."
                            value={columnSearchTerm}
                            onChange={(e) => setColumnSearchTerm(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-xs rounded-md bg-gray-50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/20 text-gray-950 dark:text-gray-50"
                            style={{ fontFamily: 'Open Sans, sans-serif' }}
                          />
                        </div>
                        <div className="flex gap-2">
                          <button
                            className="flex-1 text-xs h-8 rounded-md bg-gray-50 hover:bg-gray-100 transition-all text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}
                            onClick={() => {
                              setTableColumns(getDefaultTableColumns())
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
                    </div>

                    {/* Column List */}
                    <div className="overflow-y-auto flex-1 p-3">
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
                          col.label.toLowerCase().includes(columnSearchTerm.toLowerCase()) ||
                          col.id.toLowerCase().includes(columnSearchTerm.toLowerCase())
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
                                  className="text-[11px] font-semibold uppercase tracking-wider text-gray-600"
                                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                                >
                                  {categoryLabels[category] || category}
                                </h4>
                                <span 
                                  className="text-[11px] px-2 py-0.5 rounded-full"
                                  style={{ 
                                    backgroundColor: visibleCount > 0 ? 'rgba(31,41,55,0.1)' : '#f3f4f6',
                                    color: visibleCount > 0 ? '#1f2937' : '#9ca3af',
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
                                    className="flex items-center gap-3 p-2.5 rounded-md cursor-pointer transition-all"
                                    style={{ 
                                      backgroundColor: col.visible ? 'rgba(31,41,55,0.05)' : '#fafafa',
                                      border: col.visible ? '1px solid rgba(31,41,55,0.2)' : '1px solid #e5e7eb'
                                    }}
                                  >
                                    <div 
                                      className="w-4 h-4 rounded flex items-center justify-center flex-shrink-0 transition-all"
                                      style={{ 
                                        backgroundColor: col.visible ? '#1f2937' : 'transparent',
                                        border: col.visible ? 'none' : '2px solid #d1d5db'
                                      }}
                                    >
                                      {col.visible && (
                                        <CheckCircle className="w-3 h-3 text-white" strokeWidth={3} />
                                      )}
                                    </div>
                                    <span 
                                      className="text-xs flex-1"
                                      style={{ 
                                        color: col.visible ? '#1f2937' : '#6b7280',
                                        fontFamily: 'Open Sans, sans-serif',
                                        fontWeight: col.visible ? 500 : 400
                                      }}
                                    >
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
                  </Card>
                </div>
              )}
              </>
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
      {showTestLibrary && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-900 rounded-md w-full max-w-6xl max-h-[90vh] overflow-hidden animate-fadeIn">
            {/* Header */}
            <div className="bg-indigo-600 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-md">
                    <Library className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">Biblioteca de Testes da LIA</h2>
                    <p className="text-indigo-100 text-sm">Testes validados e organizados por área de atuação</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowTestLibrary(false)}
                  className="p-2 hover:bg-white/20 rounded-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="flex h-[calc(90vh-100px)]">
              {/* Sidebar de Categorias */}
              <div className="w-64 bg-gray-50 dark:bg-gray-800 p-4 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
                <h3 className="text-xs font-semibold text-gray-800 dark:text-gray-200 uppercase mb-3">Categorias</h3>
                <div className="space-y-1">
                  {[
                    { icon: <Code className="w-4 h-4" />, label: 'Desenvolvimento', count: 24, color: 'text-gray-800 dark:text-gray-200' },
                    { icon: <Pencil className="w-4 h-4" />, label: 'Design & UX', count: 18, color: 'text-gray-950 dark:text-gray-50', active: true },
                    { icon: <BarChart3 className="w-4 h-4" />, label: 'Dados & Analytics', count: 15, color: 'text-gray-800 dark:text-gray-200' },
                    { icon: <Users className="w-4 h-4" />, label: 'Gestão & Liderança', count: 12, color: 'text-gray-800 dark:text-gray-200' },
                    { icon: <Target className="w-4 h-4" />, label: 'Marketing & Vendas', count: 20, color: 'text-gray-800 dark:text-gray-200' },
                    { icon: <Building className="w-4 h-4" />, label: 'Administrativo', count: 10, color: 'text-gray-600 dark:text-gray-400' },
                    { icon: <Globe className="w-4 h-4" />, label: 'Idiomas', count: 8, color: 'text-gray-950 dark:text-gray-50' },
                    { icon: <Brain className="w-4 h-4 text-wedo-cyan" />, label: 'Soft Skills', count: 14, color: 'text-gray-800 dark:text-gray-200' }
                  ].map((category) => (
                    <button
                      key={category.label}
                      className={`w-full flex items-center justify-between p-2.5 rounded-md transition-all ${
                        category.active
                          ? 'bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700'
                          : 'hover:bg-white dark:hover:bg-gray-900'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className={category.color}>{category.icon}</span>
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{category.label}</span>
                      </div>
                      <Badge className="bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs">
                        {category.count}
                      </Badge>
                    </button>
                  ))}
                </div>

                <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-xs font-semibold text-gray-800 dark:text-gray-200 uppercase mb-3">Filtros</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-gray-600 dark:text-gray-400">Nível</label>
                      <select className="w-full mt-1 p-2 text-sm border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-900">
                        <option>Todos</option>
                        <option>Júnior</option>
                        <option>Pleno</option>
                        <option>Sênior</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-gray-600 dark:text-gray-400">Duração</label>
                      <select className="w-full mt-1 p-2 text-sm border border-gray-200 dark:border-gray-600 rounded bg-white dark:bg-gray-900">
                        <option>Qualquer</option>
                        <option>5-10 min</option>
                        <option>10-20 min</option>
                        <option>20-30 min</option>
                        <option>30+ min</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>

              {/* Lista de Testes */}
              <div className="flex-1 p-6 overflow-y-auto">
                <div className="mb-4">
                  <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50 mb-1">
                    Testes de Design & UX
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    18 testes disponíveis • Média de 85% de aprovação
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  {/* Teste 1 */}
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 transition-all">
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                            UX Design - Fundamentos
                          </h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Teste básico de conceitos e heurísticas de UX
                          </p>
                        </div>
                        <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-xs">Popular</Badge>
                      </div>

                      {/* Mini Dashboard de Indicadores */}
                      <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-3 mb-3">
                        {/* Nota Média em Destaque */}
                        <div className="flex items-center justify-between mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-md">
                              <Trophy className="w-5 h-5 text-gray-950 dark:text-gray-50" />
                            </div>
                            <div>
                              <p className="text-xs text-gray-800 dark:text-gray-200">Nota Média Geral</p>
                              <div className="flex items-baseline gap-2">
                                <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">7.4</p>
                                <span className="text-xs text-gray-800 dark:text-gray-200">/10</span>
                                <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-[11px]">
                                  <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                                  +0.3
                                </Badge>
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className={textStyles.description}>Baseado em</p>
                            <p className="text-xs font-medium text-gray-800 dark:text-gray-200">2.5k testes</p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-gray-200 dark:bg-gray-800/30 rounded">
                              <Target className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                            </div>
                            <div>
                              <p className={textStyles.description}>Taxa Sucesso</p>
                              <p className="text-sm font-bold text-gray-950 dark:text-gray-50">78%</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-gray-200 dark:bg-gray-800/30 rounded">
                              <Gauge className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                            </div>
                            <div>
                              <p className={textStyles.description}>Dificuldade Real</p>
                              <p className="text-sm font-bold text-gray-950 dark:text-gray-50">Médio+</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-gray-200 dark:bg-gray-800/30 rounded">
                              <UserCheck className="w-3.5 h-3.5 text-gray-800 dark:text-gray-200" />
                            </div>
                            <div>
                              <p className={textStyles.description}>Conclusão</p>
                              <p className="text-sm font-bold text-gray-950 dark:text-gray-50">92%</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-gray-200 dark:bg-gray-800/30 rounded">
                              <Timer className="w-3.5 h-3.5 text-gray-950 dark:text-gray-50" />
                            </div>
                            <div>
                              <p className={textStyles.description}>Tempo Médio</p>
                              <p className="text-sm font-bold text-gray-950 dark:text-gray-50">13min</p>
                            </div>
                          </div>
                        </div>

                        {/* Barra de Distribuição de Notas */}
                        <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                          <p className={`${textStyles.description} mb-2`}>Distribuição de Notas</p>
                          <div className="flex items-end gap-1 h-8">
                            <div className="flex-1 bg-red-500 rounded-t" style={{ height: '20%' }} title="0-40%: 5%"></div>
                            <div className="flex-1 bg-gray-600 rounded-t" style={{ height: '30%' }} title="40-60%: 15%"></div>
                            <div className="flex-1 bg-gray-600 dark:bg-gray-500 rounded-t" style={{ height: '60%' }} title="60-80%: 35%"></div>
                            <div className="flex-1 bg-gray-700 rounded-t" style={{ height: '80%' }} title="80-100%: 45%"></div>
                          </div>
                          <div className="flex justify-between mt-1">
                            <span className={textStyles.bodySmall}>0%</span>
                            <span className={textStyles.bodySmall}>100%</span>
                          </div>
                        </div>
                      </div>

                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Questões:</span>
                          <span className="font-medium">5 perguntas</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Tempo total:</span>
                          <span className="font-medium">15 minutos</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Nível:</span>
                          <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[11px]">Pleno</Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="flex -space-x-1">
                              <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                                <CheckCircle className="w-3 h-3 text-white" />
                              </div>
                            </div>
                            <span className={textStyles.description}>2.5k usos</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-gray-600 fill-gray-400 dark:text-gray-500 dark:fill-gray-500" />
                            <span className="text-xs font-medium">4.8</span>
                          </div>
                        </div>
                        <div className="flex gap-1.5">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 text-xs"
                            onClick={() => setShowTestPreview(true)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Ver
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 text-xs"
                            onClick={() => {
                              setSelectedTestForHistory('UX Design - Fundamentos')
                              setShowTestHistory(true)
                            }}
                          >
                            <History className="w-3 h-3 mr-1" />
                            Histórico
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                            onClick={() => {
                              setShowTestLibrary(false)
                              // Substituir teste
                            }}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Usar
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Teste 2 */}
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 transition-all">
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                            Design System & Componentes
                          </h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Avaliação sobre criação e manutenção de DS
                          </p>
                        </div>
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">Novo</Badge>
                      </div>

                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Questões:</span>
                          <span className="font-medium">7 perguntas</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Tempo total:</span>
                          <span className="font-medium">20 minutos</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Nível:</span>
                          <Badge className="bg-gray-300 text-gray-800 dark:bg-gray-600 dark:text-gray-200 text-[11px]">Sênior</Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="flex -space-x-1">
                              <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                                <CheckCircle className="w-3 h-3 text-white" />
                              </div>
                            </div>
                            <span className={textStyles.description}>850 usos</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-gray-600 fill-gray-400 dark:text-gray-500 dark:fill-gray-500" />
                            <span className="text-xs font-medium">4.9</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 text-xs"
                            onClick={() => setShowTestPreview(true)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Visualizar
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                            onClick={() => {
                              setShowTestLibrary(false)
                              // Substituir teste
                            }}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Usar Este
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Teste 3 */}
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 transition-all">
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                            Pesquisa com Usuários
                          </h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Métodos de pesquisa e análise de dados
                          </p>
                        </div>
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">Recomendado</Badge>
                      </div>

                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Questões:</span>
                          <span className="font-medium">6 perguntas</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Tempo total:</span>
                          <span className="font-medium">18 minutos</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Nível:</span>
                          <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[11px]">Pleno</Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="flex -space-x-1">
                              <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                                <CheckCircle className="w-3 h-3 text-white" />
                              </div>
                            </div>
                            <span className={textStyles.description}>1.2k usos</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-gray-600 fill-gray-400 dark:text-gray-500 dark:fill-gray-500" />
                            <span className="text-xs font-medium">4.7</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 text-xs"
                            onClick={() => setShowTestPreview(true)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Visualizar
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                            onClick={() => {
                              setShowTestLibrary(false)
                              // Substituir teste
                            }}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Usar Este
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Teste 4 */}
                  <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 transition-all">
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium text-gray-950 dark:text-gray-50 mb-1">
                            Prototipagem e Ferramentas
                          </h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">
                            Figma, Sketch, Adobe XD e prototipagem
                          </p>
                        </div>
                        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-xs">Técnico</Badge>
                      </div>

                      <div className="space-y-2 mb-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Questões:</span>
                          <span className="font-medium">4 perguntas</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Tempo total:</span>
                          <span className="font-medium">12 minutos</span>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-800 dark:text-gray-200">Nível:</span>
                          <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-[11px]">Júnior</Badge>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-gray-100 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="flex -space-x-1">
                              <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                                <CheckCircle className="w-3 h-3 text-white" />
                              </div>
                            </div>
                            <span className={textStyles.description}>3.1k usos</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="w-3 h-3 text-gray-600 fill-gray-400 dark:text-gray-500 dark:fill-gray-500" />
                            <span className="text-xs font-medium">4.6</span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="flex-1 text-xs"
                            onClick={() => setShowTestPreview(true)}
                          >
                            <Eye className="w-3 h-3 mr-1" />
                            Visualizar
                          </Button>
                          <Button
                            size="sm"
                            className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                            onClick={() => {
                              setShowTestLibrary(false)
                              // Substituir teste
                            }}
                          >
                            <RefreshCw className="w-3 h-3 mr-1" />
                            Usar Este
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Botão para carregar mais */}
                <div className="mt-6 text-center">
                  <Button variant="outline">
                    <Plus className="w-4 h-4 mr-2" />
                    Carregar Mais Testes
                  </Button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    121 testes disponíveis
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    Usado por 5.2k empresas
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    87% taxa de sucesso
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowTestLibrary(false)}
                  >
                    Fechar
                  </Button>
                  <Button className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white">
                    <Plus className="w-4 h-4 mr-2" />
                    Criar Novo Teste
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Histórico do Teste */}
      {showTestHistory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-900 rounded-md w-full max-w-5xl max-h-[90vh] overflow-hidden animate-fadeIn">
            {/* Header */}
            <div className="bg-gray-900 dark:bg-gray-800 p-5 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-md">
                    <History className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold">Histórico de Uso do Teste</h2>
                    <p className="text-gray-400 text-sm">{selectedTestForHistory || 'UX Design - Fundamentos'}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowTestHistory(false)}
                  className="p-2 hover:bg-white/20 rounded-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Estatísticas Gerais */}
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
              {/* Nota Média Destacada */}
              <div className="bg-purple-600 rounded-md p-4 mb-4 text-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-white/20 rounded-md">
                      <Trophy className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-sm opacity-90">Nota Média Histórica</p>
                      <div className="flex items-baseline gap-3">
                        <p className="text-3xl font-bold">7.4</p>
                        <span className="text-lg opacity-80">/10</span>
                        <div className="flex items-center gap-2 ml-3">
                          <Badge className="bg-white/20 text-white border-white/30">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            +0.3 vs mês anterior
                          </Badge>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Mini gráfico de evolução */}
                  <div className="bg-white/10 rounded-md p-3">
                    <p className="text-[11px] opacity-80 mb-2">Evolução (6 meses)</p>
                    <div className="flex items-end gap-1 h-10">
                      {[6.8, 7.0, 7.1, 7.2, 7.1, 7.4].map((value, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-white/30 rounded-t hover:bg-white/40 transition-colors relative group"
                          style={{ height: `${((value - 6) / 2) * 100}%` }}
                        >
                          <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-[11px] opacity-0 group-hover:opacity-100 transition-opacity">
                            {value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-5 gap-4">
                <div className="bg-white dark:bg-gray-900 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <BarChart3 className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">Total de Aplicações</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">2,547</p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">↑ 12% este mês</p>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">Taxa de Sucesso</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">78%</p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">Nota ≥ 7.0</p>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <UserCheck className="w-4 h-4 text-gray-950 dark:text-gray-50" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">Taxa de Conclusão</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">92%</p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">Candidatos finalizam</p>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Timer className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">Tempo Médio</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">13min</p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">De 15min esperados</p>
                </div>

                <div className="bg-white dark:bg-gray-900 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Gauge className="w-4 h-4 text-red-600" />
                    <span className="text-xs text-gray-800 dark:text-gray-200">Dificuldade Percebida</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-950 dark:text-gray-50">6.8/10</p>
                  <p className="text-xs text-gray-800 dark:text-gray-200 mt-1">Médio-Alto</p>
                </div>
              </div>
            </div>

            {/* Lista de Vagas que Usaram */}
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-380px)]">
              <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-4">
                Vagas que Utilizaram Este Teste
              </h3>

              <div className="space-y-3">
                {/* Vaga 1 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium text-gray-950 dark:text-gray-50">UX Designer Sênior</h4>
                        <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-xs">Finalizada</Badge>
                        <span className="text-xs text-gray-800 dark:text-gray-200">Sodexo • São Paulo</span>
                      </div>
                      <div className="flex items-center gap-6 text-xs text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          Mar 2024
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          45 candidatos
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          82% aprovação
                        </span>
                        <span className="flex items-center gap-1">
                          <Trophy className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          3 contratados
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-gray-950 dark:text-gray-50">Sucesso</p>
                      <p className="text-xs text-gray-800 dark:text-gray-200">ROI: 320%</p>
                    </div>
                  </div>

                  {/* Mini gráfico de performance */}
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                      <span className={textStyles.description}>Distribuição de Notas</span>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[11px] px-1.5">
                          <Trophy className="w-2.5 h-2.5 mr-0.5" />
                          Nota Média: 7.8/10
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-end gap-0.5 h-6">
                      {[2, 3, 5, 8, 12, 10, 5].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gray-600 dark:bg-gray-500 rounded-t opacity-80"
                          style={{ height: `${(height / 12) * 100}%` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Vaga 2 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium text-gray-950 dark:text-gray-50">Product Designer</h4>
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">Em Andamento</Badge>
                        <span className="text-xs text-gray-800 dark:text-gray-200">Nubank • Remoto</span>
                      </div>
                      <div className="flex items-center gap-6 text-xs text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          Nov 2024
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          28 candidatos
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          75% aprovação
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3 text-gray-800 dark:text-gray-200" />
                          Em entrevistas
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-gray-950 dark:text-gray-50">Ativo</p>
                      <p className="text-xs text-gray-800 dark:text-gray-200">5 finalistas</p>
                    </div>
                  </div>

                  {/* Mini gráfico de performance */}
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                      <span className={textStyles.description}>Distribuição de Notas</span>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[11px] px-1.5">
                          <Trophy className="w-2.5 h-2.5 mr-0.5" />
                          Nota Média: 7.2/10
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-end gap-0.5 h-6">
                      {[3, 4, 6, 7, 8, 4, 2].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gray-600 dark:bg-gray-500 rounded-t opacity-80"
                          style={{ height: `${(height / 8) * 100}%` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                {/* Vaga 3 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium text-gray-950 dark:text-gray-50">UI/UX Designer</h4>
                        <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-xs">Cancelada</Badge>
                        <span className="text-xs text-gray-800 dark:text-gray-200">iFood • Campinas</span>
                      </div>
                      <div className="flex items-center gap-6 text-xs text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          Set 2024
                        </span>
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          18 candidatos
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          65% aprovação
                        </span>
                        <span className="flex items-center gap-1">
                          <XCircle className="w-3 h-3 text-gray-600" />
                          Vaga cancelada
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-gray-600">Encerrada</p>
                      <p className="text-xs text-gray-800 dark:text-gray-200">Sem contratação</p>
                    </div>
                  </div>

                  {/* Mini gráfico de performance */}
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                      <span className={textStyles.description}>Distribuição de Notas</span>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-[11px] px-1.5">
                          <Trophy className="w-2.5 h-2.5 mr-0.5" />
                          Nota Média: 6.5/10
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-end gap-0.5 h-6">
                      {[4, 5, 6, 5, 3, 2, 1].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 bg-gray-400 rounded-t opacity-60"
                          style={{ height: `${(height / 6) * 100}%` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Insights e Recomendações */}
              <div className="mt-6 bg-gray-100 dark:bg-gray-800/20 rounded-md p-4 border border-gray-300 dark:border-gray-700">
                <div className="flex items-start gap-3">
                  <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-2">
                      Insights da LIA
                    </h4>
                    <ul className="space-y-1 text-xs text-gray-800 dark:text-gray-200">
                      <li>• Este teste tem melhor performance com candidatos de nível Pleno e Sênior</li>
                      <li>• A questão 3 tem a menor taxa de acerto (45%) - considere revisar ou adicionar contexto</li>
                      <li>• Candidatos que pontuam acima de 75% têm 3x mais chance de serem contratados</li>
                      <li>• Tempo ideal de aplicação: Segunda a Quinta, entre 10h-12h ou 14h-17h</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                  <span className="flex items-center gap-1">
                    <TrendingUp className="w-3 h-3" />
                    Performance acima da média
                  </span>
                  <span className="flex items-center gap-1">
                    <Award className="w-3 h-3" />
                    Top 10% dos testes mais eficazes
                  </span>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowTestHistory(false)}
                  >
                    Fechar
                  </Button>
                  <Button className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:hover:bg-gray-200 dark:text-gray-900">
                    <Download className="w-4 h-4 mr-2" />
                    Exportar Relatório
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Painel Lateral de Sugestões da LIA */}
      {showLiaSuggestions && (
        <>
          {/* Overlay para fechar o painel ao clicar fora */}
          <div
            className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
            onClick={() => setShowLiaSuggestions(false)}
          />

          {/* Painel Lateral */}
          <div className="fixed right-0 top-0 h-full z-50 w-[450px] bg-white dark:bg-gray-900" style={{ animation: 'slideInRight 0.3s ease-out' }}>
            {/* Header */}
            <div className="bg-purple-600 p-4 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-md">
                    <Wand2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold">Sugestões de Perguntas da LIA</h2>
                    <p className="text-purple-100 text-xs">Baseadas no perfil da vaga</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowLiaSuggestions(false)}
                  className="p-1.5 hover:bg-white/20 rounded-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    Perguntas Recomendadas para UX Design
                  </h3>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Clique em "Substituir" para trocar a pergunta selecionada
                </p>
              </div>

              <div className="space-y-3">
                {/* Sugestão 1 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                  <div className="flex items-start justify-between mb-2">
 <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                      Qual método de pesquisa seria mais apropriado para validar a usabilidade de um protótipo em fase inicial?
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">Recomendada</Badge>
                      <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-xs">2 min</Badge>
                    </div>
                  </div>
                  <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-gray-400">
                    <p>A) Teste A/B com grande amostra</p>
                    <p>B) Card sorting</p>
                    <p className="text-gray-950 dark:text-gray-50 font-bold">C) Teste de usabilidade moderado ✓</p>
                    <p>D) Analytics quantitativo</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                      <span className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        Avalia: Métodos de Pesquisa
                      </span>
                      <span className="flex items-center gap-1">
                        <BarChart3 className="w-3 h-3" />
                        Dificuldade: Médio
                      </span>
                    </div>
                    <Button
                      size="sm"
                      className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                      onClick={() => setShowLiaSuggestions(false)}
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Substituir
                    </Button>
                  </div>
                </div>

                {/* Sugestão 2 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                  <div className="flex items-start justify-between mb-2">
 <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                      Como você priorizaria funcionalidades em um MVP usando a matriz de esforço vs impacto?
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-gray-900 text-xs">Alta Relevância</Badge>
                      <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-xs">3 min</Badge>
                    </div>
                  </div>
                  <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-gray-400">
                    <p className="text-gray-950 dark:text-gray-50 font-bold">A) Alto impacto e baixo esforço primeiro ✓</p>
                    <p>B) Alto esforço e alto impacto primeiro</p>
                    <p>C) Baixo esforço independente do impacto</p>
                    <p>D) Todas as funcionalidades igualmente</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                      <span className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        Avalia: Priorização
                      </span>
                      <span className="flex items-center gap-1">
                        <BarChart3 className="w-3 h-3" />
                        Dificuldade: Fácil
                      </span>
                    </div>
                    <Button
                      size="sm"
                      className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                      onClick={() => setShowLiaSuggestions(false)}
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Substituir
                    </Button>
                  </div>
                </div>

                {/* Sugestão 3 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                  <div className="flex items-start justify-between mb-2">
 <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                      Qual é a diferença fundamental entre Design System e Style Guide?
                    </h4>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">Conceitual</Badge>
                      <Badge className="bg-gray-100 text-gray-800 dark:text-gray-200 text-xs">2 min</Badge>
                    </div>
                  </div>
                  <div className="space-y-1 ml-2 text-xs text-gray-600 dark:text-gray-400">
                    <p>A) Não há diferença, são sinônimos</p>
                    <p className="text-gray-950 dark:text-gray-50 font-bold">B) Design System inclui componentes e padrões, Style Guide foca em visual ✓</p>
                    <p>C) Style Guide é mais completo que Design System</p>
                    <p>D) Design System é apenas para desenvolvedores</p>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                      <span className="flex items-center gap-1">
                        <Target className="w-3 h-3" />
                        Avalia: Conhecimento Técnico
                      </span>
                      <span className="flex items-center gap-1">
                        <BarChart3 className="w-3 h-3" />
                        Dificuldade: Médio
                      </span>
                    </div>
                    <Button
                      size="sm"
                      className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                      onClick={() => setShowLiaSuggestions(false)}
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Substituir
                    </Button>
                  </div>
                </div>

                {/* Botão para gerar mais sugestões */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Button
                    variant="outline"
                    className="w-full text-sm"
                    onClick={() => {
                      // Simular carregamento de mais sugestões
                    }}
                  >
                    <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                    Gerar Mais Sugestões
                  </Button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="absolute bottom-0 left-0 right-0 border-t border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-800 dark:text-gray-200">
                  <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
                  Baseado em 500+ testes
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLiaSuggestions(false)}
                  className="text-xs"
                >
                  Fechar Painel
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Modal de Preview do Teste para Candidato */}
      {showTestPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white dark:bg-gray-900 rounded-md w-full max-w-4xl max-h-[90vh] overflow-hidden animate-fadeIn">
            {/* Header do Modal */}
            <div className="bg-purple-600 p-6 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold mb-2">Teste Técnico - UX Design</h2>
                  <p className="text-purple-100 text-sm">Vaga: UX Designer • Sodexo</p>
                </div>
                <button
                  onClick={() => setShowTestPreview(false)}
                  className="p-2 hover:bg-white/20 rounded-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Conteúdo do Modal */}
            <div className="overflow-y-auto max-h-[calc(90vh-120px)]">
              {/* Informações do Teste */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <div>
                      <p className="text-xs text-gray-800 dark:text-gray-200">Tempo Total</p>
                      <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">14 minutos</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <ListChecks className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <div>
                      <p className="text-xs text-gray-800 dark:text-gray-200">Total de Questões</p>
                      <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">5 questões</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <div>
                      <p className="text-xs text-gray-800 dark:text-gray-200">Pontuação Mínima</p>
                      <p className="text-sm font-semibold text-gray-950 dark:text-gray-50">70%</p>
                    </div>
                  </div>
                </div>

                {/* Instruções */}
                <div className="bg-gray-100 dark:bg-gray-800/20 rounded-md p-4">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-50 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Instruções Importantes
                  </h3>
                  <ul className="text-sm text-gray-800 dark:text-gray-200 space-y-1">
                    <li>• Leia cada questão com atenção antes de responder</li>
                    <li>• Cada questão tem um tempo limite individual (2-4 minutos)</li>
                    <li>• Você pode navegar entre as questões antes de finalizar</li>
                    <li>• O teste será enviado automaticamente ao final do tempo</li>
                    <li>• Certifique-se de ter uma conexão estável com a internet</li>
                  </ul>
                </div>
              </div>

              {/* Questões do Teste - Visão do Candidato */}
              <div className="p-6 space-y-6">
                {/* Questão 1 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                        1
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-950 dark:text-gray-50 font-medium">
                          Qual é a principal heurística de Nielsen violada quando um site não fornece feedback após uma ação do usuário?
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex items-center gap-1 text-xs text-gray-800 dark:text-gray-200">
                            <Clock className="w-3 h-3" />
                            <span className="font-medium">Tempo limite: 3:00</span>
                          </div>
                          <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 max-w-[200px]">
                            <div className="bg-gray-700 dark:bg-gray-400 h-1.5 rounded-full animate-pulse" style={{ width: '75%' }}></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <Badge className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">10 pontos</Badge>
                  </div>
                  <div className="ml-11 space-y-2">
                    {[
                      'Prevenção de erros',
                      'Controle e liberdade do usuário',
                      'Visibilidade do status do sistema',
                      'Consistência e padrões'
                    ].map((option, idx) => (
                      <label key={idx} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                        <input
                          type="radio"
                          name="candidate-q1"
                          className="w-4 h-4 text-gray-950 dark:text-gray-50 border-gray-300 focus:ring-gray-500"
                        />
                        <span className="text-sm text-gray-800 dark:text-gray-200 group-hover:text-gray-900 dark:group-hover:text-gray-100">
                          {option}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Questão 2 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                        2
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-950 dark:text-gray-50 font-medium">
                          No processo de Design Thinking, qual etapa vem imediatamente após a fase de "Definir"?
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex items-center gap-1 text-xs text-gray-800 dark:text-gray-200">
                            <CheckCircle className="w-3 h-3" />
                            <span className="font-medium">Respondida em 0:45</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <Badge className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">10 pontos</Badge>
                  </div>
                  <div className="ml-11 space-y-2">
                    {[
                      'Empatizar',
                      'Idear',
                      'Prototipar',
                      'Testar'
                    ].map((option, idx) => (
                      <label key={idx} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                        <input
                          type="radio"
                          name="candidate-q2"
                          className="w-4 h-4 text-gray-950 dark:text-gray-50 border-gray-300 focus:ring-gray-500"
                        />
                        <span className="text-sm text-gray-800 dark:text-gray-200 group-hover:text-gray-900 dark:group-hover:text-gray-100">
                          {option}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Questão 3 */}
                <div className="bg-gray-50 dark:bg-gray-800 rounded-md p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-3">
                      <div className="bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-full w-8 h-8 flex items-center justify-center font-semibold text-sm">
                        3
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-950 dark:text-gray-50 font-medium">
                          Qual métrica é mais adequada para medir a facilidade de uso de uma interface?
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <div className="flex items-center gap-1 text-xs text-gray-800 dark:text-gray-200">
                            <CheckCircle className="w-3 h-3" />
                            <span className="font-medium">Respondida em 1:23</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <Badge className="bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300">10 pontos</Badge>
                  </div>
                  <div className="ml-11 space-y-2">
                    {[
                      'Taxa de conversão',
                      'Tempo médio de sessão',
                      'System Usability Scale (SUS)',
                      'Net Promoter Score (NPS)'
                    ].map((option, idx) => (
                      <label key={idx} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-900 rounded-md border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                        <input
                          type="radio"
                          name="candidate-q3"
                          className="w-4 h-4 text-gray-950 dark:text-gray-50 border-gray-300 focus:ring-gray-500"
                        />
                        <span className="text-sm text-gray-800 dark:text-gray-200 group-hover:text-gray-900 dark:group-hover:text-gray-100">
                          {option}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Indicador de Progresso */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-gray-800 dark:text-gray-200">Progresso:</span>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map(num => (
                        <div
                          key={num}
                          className={`w-8 h-1 rounded-full ${
 num <= 3 ? 'bg-gray-900' : 'bg-gray-300 dark:bg-gray-600'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                  <span className="text-sm text-gray-800 dark:text-gray-200">3 de 5 questões respondidas</span>
                </div>
              </div>
            </div>

            {/* Footer do Modal */}
            <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-3 bg-gray-100 dark:bg-gray-800/20 px-3 py-1.5 rounded-md">
                    <Clock className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                    <div>
                      <span className="text-xs text-gray-600 dark:text-gray-400">Tempo total:</span>
                      <span className="text-sm font-bold text-gray-950 dark:text-gray-50 ml-1">11:32</span>
                      <span className="text-xs text-gray-800 dark:text-gray-200 mx-2">|</span>
                      <span className="text-xs text-gray-600 dark:text-gray-400">Questão atual:</span>
                      <span className="text-sm font-bold text-gray-950 dark:text-gray-50 ml-1">2:15</span>
                    </div>
                  </div>
                  <div className="text-sm text-gray-800 dark:text-gray-200">
                    <CheckCircle className="w-3 h-3 inline text-gray-800 dark:text-gray-200 mr-1" />
                    Salvamento automático
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowTestPreview(false)}
                  >
                    Fechar Preview
                  </Button>
                  <Button className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white">
                    <Send className="w-4 h-4 mr-2" />
                    Enviar Teste
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Painel Lateral de Sugestões da LIA para Triagem */}
      {showTriagemSuggestions && (
        <>
          {/* Overlay para fechar o painel ao clicar fora */}
          <div
            className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
            onClick={() => setShowTriagemSuggestions(false)}
          />

          {/* Painel Lateral */}
          <div className="fixed right-0 top-0 h-full z-50 w-[450px] bg-white dark:bg-gray-900 animate-slideInRight">
            {/* Header */}
            <div className="bg-purple-600 p-4 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/20 rounded-md">
                    <Wand2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold">Sugestões de Perguntas da LIA</h2>
                    <p className="text-purple-100 text-xs">Para Triagem - {selectedTriagemQuestion}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowTriagemSuggestions(false)}
                  className="p-1.5 hover:bg-white/20 rounded-md transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-4 overflow-y-auto h-[calc(100vh-80px)]">
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <Brain className="w-4 h-4 text-wedo-cyan" />
                  <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    Perguntas Recomendadas para Triagem
                  </h3>
                </div>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Clique em "Substituir" para trocar a pergunta selecionada
                </p>
              </div>

              <div className="space-y-3">
                {/* Sugestões de perguntas baseadas no tipo */}
                {(selectedTriagemQuestion?.includes('tech') ? [
                  'Como você estrutura um Design System escalável para múltiplas plataformas?',
                  'Descreva sua experiência com métodos de pesquisa de usuário e como os aplica',
                  'Como você mede o ROI de iniciativas de UX em produtos digitais?',
                  'Qual sua abordagem para design responsivo e acessibilidade?',
                  'Como você colabora com desenvolvedores para garantir a implementação fiel do design?'
                ] : [
                  'Como você lida com prazos apertados e múltiplas entregas simultâneas?',
                  'Descreva uma situação de conflito em equipe que você resolveu com sucesso',
                  'Como você se mantém atualizado com as tendências e tecnologias da área?',
                  'Qual foi seu maior desafio profissional e como o superou?',
                  'Como você prioriza múltiplas demandas de diferentes stakeholders?'
                ]).map((pergunta, index) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-md p-4 border border-gray-200 dark:border-gray-700 hover:border-gray-400 dark:hover:border-gray-500 cursor-pointer transition-all group">
                    <div className="flex items-start justify-between mb-2">
 <h4 className="text-sm font-medium text-gray-950 group-hover:text-gray-950">
                        {pergunta}
                      </h4>
                      <Badge className="bg-gray-200 text-gray-800 dark:bg-gray-700 dark:text-gray-200 text-xs">
                        {index === 0 ? 'Recomendada' : index === 1 ? 'Popular' : 'Sugerida'}
                      </Badge>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <div className="flex items-center gap-4 text-xs text-gray-800 dark:text-gray-200">
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          Relevância: {index === 0 ? 'Muito Alta' : index < 3 ? 'Alta' : 'Média'}
                        </span>
                      </div>
                      <Button
                        size="sm"
                        className="text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-white"
                        onClick={() => {
                          setShowTriagemSuggestions(false)
                          // Aqui substituiria a pergunta na lista
                        }}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Substituir
                      </Button>
                    </div>
                  </div>
                ))}

                {/* Botão para gerar mais sugestões */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <Button
                    variant="outline"
                    className="w-full text-sm"
                    onClick={() => {
                      // Simular carregamento de mais sugestões
                    }}
                  >
                    <Brain className="w-4 h-4 mr-2 text-wedo-cyan" />
                    Gerar Mais Sugestões
                  </Button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="absolute bottom-0 left-0 right-0 border-t border-gray-200 dark:border-gray-700 p-3 bg-gray-50 dark:bg-gray-800">
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-800 dark:text-gray-200">
                  <Brain className="w-3 h-3 inline mr-1 text-wedo-cyan" />
                  Baseado no perfil da vaga
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowTriagemSuggestions(false)}
                  className="text-xs"
                >
                  Fechar Painel
                </Button>
              </div>
            </div>
          </div>
        </>
      )}

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
            style={{ fontFamily: 'Open Sans, sans-serif' }}
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
            style={{ fontFamily: 'Open Sans, sans-serif' }}
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
                      style={{ backgroundColor: '#A8CED5' }}
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
                      style={{ 
                        backgroundColor: selectedCandidateForModal.technicalTestScore >= 80 ? '#A8D5B7' :
                                         selectedCandidateForModal.technicalTestScore >= 60 ? '#A8CED5' :
                                         selectedCandidateForModal.technicalTestScore >= 40 ? '#BFA8D5' :
                                         '#D5A8C6'
                      }}
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
                      style={{ 
                        backgroundColor: selectedCandidateForModal.englishTestScore >= 80 ? '#A8D5B7' :
                                         selectedCandidateForModal.englishTestScore >= 60 ? '#A8CED5' :
                                         selectedCandidateForModal.englishTestScore >= 40 ? '#BFA8D5' :
                                         '#D5A8C6'
                      }}
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
