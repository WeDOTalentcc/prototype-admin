"use client"

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/components/auth-context"
import { useToast } from "@/hooks/use-toast"
import { useShortList } from "@/hooks/use-short-list"
import { useProactiveInsights } from "@/hooks/use-proactive-insights"
import { useNavigationPersistence } from "@/hooks/use-navigation-persistence"
import { useTalentFunnel } from "@/hooks/use-talent-funnel"
import { useCandidateSuggestions } from "@/hooks/useCandidateSuggestions"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"
import { type TableColumn } from "@/components/tables"
import { useUniversalTransition, type KanbanCandidate } from "@/components/kanban"
import { liaApi } from "@/services/lia-api"
import { type UniversalTransitionConfirmData } from "@/components/kanban"
import {
  RECRUITMENT_STAGES,
  getCompanyPipelineStages,
} from "@/lib/recruitment-stages"
import { type BulkActionType } from "@/components/ui/bulk-selection-bar"
import { mockJobData } from "@/components/kanban/mock/candidates"
import { useCompanyDefaults } from "@/hooks/use-company-defaults"
import { usePipelineInheritance } from "@/hooks/use-pipeline-inheritance"
import { useRecruitmentStages } from "@/hooks/use-recruitment-stages"
import { enrichStagesWithSubStatuses, buildSubStatusMap } from "@/components/kanban/utils/stage-utils"
import { useReturnEvents } from '@/hooks/use-return-events'
import { useBulkCandidateDataRequests } from "@/hooks/use-candidate-data-requests"
import { type DataRequestSubmitData } from "@/components/modals/data-request-modal"
import {
  mapInterviewStagesToKanban,
  createInitialCandidatesData,
  type DynamicStage,
} from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { calculateNotaLiaGeral } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import { useKanbanBulkActions } from "@/components/pages/job-kanban/hooks/useKanbanBulkActions"
import { useKanbanLIAHandlers } from "@/components/pages/job-kanban/hooks/useKanbanLIAHandlers"
import { useKanbanCandidateDecisions } from "@/components/pages/job-kanban/hooks/useKanbanCandidateDecisions"
import { useKanbanJobEditing } from "@/components/pages/job-kanban/hooks/useKanbanJobEditing"
import { useKanbanDragDrop } from "@/components/pages/job-kanban/hooks/useKanbanDragDrop"
import { useKanbanUIModals } from "@/components/pages/job-kanban/hooks/useKanbanUIModals"
import { useKanbanTableView } from "@/components/pages/job-kanban/hooks/useKanbanTableView"
import { useKanbanCandidateLoader } from "@/components/pages/job-kanban/hooks/useKanbanCandidateLoader"
import { useKanbanLIASuggestions } from "@/components/pages/job-kanban/hooks/useKanbanLIASuggestions"
import { useKanbanTransitions } from "@/components/pages/job-kanban/hooks/useKanbanTransitions"

const jobData = mockJobData

export function useKanbanPageCore({ job, onBack }: { job?: Record<string, unknown>; onBack?: () => void }) {
  const router = useRouter()
  const { toast } = useToast()
  const { saveJobsState } = useNavigationPersistence()
  const { user } = useAuth()
  const talentFunnel = useTalentFunnel()
  const _companyIdForSL = ((user as Record<string, unknown>)?.company as string) || 'demo'
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
  const [selectedCandidate, setSelectedCandidate] = useState<Record<string, unknown> | null>(null)
  const [selectedTriagemCandidate, setSelectedTriagemCandidate] = useState<Record<string, unknown> | null>(null)
  const [showExpandedMetrics, setShowExpandedMetrics] = useState(false)
  
  useEffect(() => {
    if (!job?.backendId) return
    const creationJobId = localStorage.getItem("jobCreationMode")
    if (creationJobId && creationJobId === job.backendId) {
      setIsCreationMode(true)
      setActiveTab("edit")
      localStorage.removeItem("jobCreationMode")
    }
  }, [job?.backendId])

  const [jobEditForm, setJobEditForm] = useState<Record<string, unknown>>({})

  const handlePublishJob = useCallback(async () => {
    const vacancyId = job?.backendId as string | undefined
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
      const autoSavePayload: Record<string, unknown> = {}
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

      await liaApi.updateJobVacancy(vacancyId, { status: "Ativa" } as Record<string, unknown>)

      setPublicLink(linkResult.public_url)
      setShowPublishSuccess(true)
      setIsCreationMode(false)

      setJobEditForm((prev: Record<string, unknown>) => ({
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
    mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0])
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

  // Estados para candidatesData (hoisted before useKanbanTransitions)
  const [candidatesData, setCandidatesData] = useState<Record<string, KanbanCandidate[]>>(() => 
    createInitialCandidatesData(mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]))
  )

  // ── handleUniversalTransitionConfirm — extraído para useKanbanTransitions ──
  const { handleUniversalTransitionConfirm } = useKanbanTransitions({
    candidatesData, setCandidatesData,
    universalModalState,
    closeTransition,
    toast,
  })

  const handleOpenSpecializedModal = useCallback((modalType: string, context: { candidates?: Record<string, unknown>[]; toStage?: string; [key: string]: unknown }) => {
    switch (modalType) {
      case 'wsi-triagem-invite':
        if ((context.candidates ?? []).length > 0) {
          setWsiInviteCandidate(context.candidates![0])
          setShowWSIInviteModal(true)
        }
        break
      case 'scheduling':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('agendamento')
          setUnifiedModalSituation('agendamento')
          setUnifiedModalOpen(true)
        }
        break
      case 'data-request':
        if ((context.candidates ?? []).length > 0) {
          setDataRequestModalCandidate(context.candidates![0])
          setShowDataRequestModal(true)
        }
        break
      case 'decision-flow':
        if ((context.candidates ?? []).length > 0) {
          const candidate = context.candidates![0]
          setDecisionFlowCandidate(candidate)
          setDecisionFlowType(context.toStage === 'hired' ? 'confirm_hire' : 'reject_pre_triage')
          setShowDecisionFlowModal(true)
        }
        break
      case 'rejection-feedback':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('feedback')
          setUnifiedModalSituation('feedback_construtivo')
          setUnifiedModalOpen(true)
        }
        break
      case 'evaluation-send':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
          setUnifiedModalType('email')
          setUnifiedModalSituation('avaliacao_tecnica')
          setUnifiedModalOpen(true)
        }
        break
      case 'offer-send':
        if ((context.candidates ?? []).length > 0) {
          setUnifiedModalCandidate(context.candidates![0])
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
  const [draggedCandidate, setDraggedCandidate] = useState<Record<string, unknown> | null>(null)
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)
  const pendingNavigationRef = useRef<{ nav: { candidateId?: string; candidateName?: string; jobId?: string; jobTitle?: string; currentStage?: string; action?: string; openTransitionModal?: boolean }; prompt: string | null } | null>(null)

  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set())

  const allTableCandidates = useMemo(() => {
    return dynamicStages.reduce((acc: Record<string, unknown>[], stage) => {
      const stageCandidates = candidatesData[stage.id] || []
      return [...acc, ...stageCandidates]
    }, [])
  }, [dynamicStages, candidatesData])

  const allCandidateIds = useMemo(() => {
    return Object.values(candidatesData).flat().map((c: Record<string, unknown>) => c.id as string).filter(Boolean) as string[]
  }, [candidatesData])

  const { 
    getDataRequestForCandidate,
    mutate: mutateDataRequests 
  } = useBulkCandidateDataRequests({
    candidateIds: allCandidateIds,
    vacancyId: job?.id?.toString(),
    enabled: allCandidateIds.length > 0,
  })

  const handleDataRequestResend = useCallback((candidateId: string) => {
    const candidate = Object.values(candidatesData)
      .flat()
      .find((c: Record<string, unknown>) => c.id === candidateId)
    
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
      .find((c: Record<string, unknown>) => c.id === candidateId)
    
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

  // ── Carregamento de candidatos — extraído para useKanbanCandidateLoader ──
  const candidateLoader = useKanbanCandidateLoader({ job, dynamicStages, setCandidatesData })
  const { isLoadingCandidates, hasMounted, isClient } = candidateLoader.state
  const { setIsLoadingCandidates, setHasMounted, setIsClient } = candidateLoader.actions

  // Estado para busca
  const [searchQuery, setSearchQuery] = useState("")

  // ── Modais e UI — extraído para useKanbanUIModals ──
  const uiModals = useKanbanUIModals({ job, toast })
  const {
    previewCandidate, isPreviewOpen, showCandidatePage, isPreviewMaximized,
    triagemCandidate, showReport, isTriagemOpen, showTestPreview, editingQuestion,
    showTestLibrary, showTestHistory, selectedTestForHistory,
    showConceptualPrompt, isEditModeTriagem, showConceptualPromptTriagem,
    showApresentacaoPrompt, showFechamentoPrompt, isEditMode,
    showTriagemSuggestions, selectedTriagemQuestion,
    expandedCronograma, expandedTesteTecnico, expandedTesteIngles, expandedRoteiro,
    perguntasEliminatorias, perguntasInformativas, habilidadesTecnicas,
    perguntasTecnicasAvaliacao, skillWeights, originalSkillWeights, isSkillWeightsModified, perguntasSituacionais,
    showLiaSuggestions, liaSuggestionsData, showLiaSuggestionsPanel,
    showExpandedLIA, transitionInitialPrompt, transitionAllowStageSelection, transitionInterviewAlert,
    showSuperChat, liaPromptValue, liaMessages, isLiaLoading, liaConversationId,
    chatScrollRef, liaSearchQuery, userCollapsedLIA, liaExpandedWidth, isResizingLIA,
    showEmailModal, emailCandidate, showShareGestorModal,
    unifiedModalOpen, unifiedModalType, unifiedModalCandidate, unifiedModalSituation,
    showWSIModal, wsiCandidate, showWSIInviteModal, wsiInviteCandidate,
    showAddToVacancyModal, candidateForVacancy,
    showRubricModal, rubricCandidate, rubricEvaluationData,
    selectedCandidateForModal, activeModal, showBigFiveModal,
    showGeneralScoreModal, showTechnicalTestModal, showEnglishTestModal, scoreModalCandidate,
    showCompareModal, compareCandidates, selectedForCompare,
    showDecisionFlowModal, decisionFlowCandidate, decisionFlowType,
    pendingMove, statusModalOpen, selectedSubStatus,
    showJobStatusModal, jobStatusModalMode, showCloseVacancyModal,
    showAddToListModal, isAddingToList, showBulkActionModal, bulkActionType,
    showDataRequestModal, dataRequestModalCandidate, viewedCandidateIds,
  } = uiModals.state
  const {
    setPreviewCandidate, setIsPreviewOpen, setShowCandidatePage, setIsPreviewMaximized,
    setTriagemCandidate, setShowReport, setIsTriagemOpen, setShowTestPreview, setEditingQuestion,
    setShowTestLibrary, setShowTestHistory, setSelectedTestForHistory,
    setShowConceptualPrompt, setIsEditModeTriagem, setShowConceptualPromptTriagem,
    setShowApresentacaoPrompt, setShowFechamentoPrompt, setIsEditMode,
    setShowTriagemSuggestions, setSelectedTriagemQuestion,
    setExpandedCronograma, setExpandedTesteTecnico, setExpandedTesteIngles, setExpandedRoteiro,
    setPerguntasEliminatorias, setPerguntasInformativas, setHabilidadesTecnicas,
    setPerguntasTecnicasAvaliacao, setSkillWeights, setIsSkillWeightsModified, setPerguntasSituacionais,
    setShowLiaSuggestions, setLiaSuggestionsData, setShowLiaSuggestionsPanel,
    setShowExpandedLIA, setTransitionInitialPrompt, setTransitionAllowStageSelection, setTransitionInterviewAlert,
    setShowSuperChat, setLiaPromptValue, setLiaMessages, setIsLiaLoading, setLiaConversationId,
    setLiaSearchQuery, setUserCollapsedLIA, setLiaExpandedWidth, setIsResizingLIA,
    setShowEmailModal, setEmailCandidate, setShowShareGestorModal,
    setUnifiedModalOpen, setUnifiedModalType, setUnifiedModalCandidate, setUnifiedModalSituation,
    setShowWSIModal, setWsiCandidate, setShowWSIInviteModal, setWsiInviteCandidate,
    setShowAddToVacancyModal, setCandidateForVacancy,
    setShowRubricModal, setRubricCandidate, setRubricEvaluationData,
    setSelectedCandidateForModal, setActiveModal, setShowBigFiveModal,
    setShowGeneralScoreModal, setShowTechnicalTestModal, setShowEnglishTestModal, setScoreModalCandidate,
    setShowCompareModal, setCompareCandidates, setSelectedForCompare,
    setShowDecisionFlowModal, setDecisionFlowCandidate, setDecisionFlowType,
    setPendingMove, setStatusModalOpen, setSelectedSubStatus,
    setShowJobStatusModal, setJobStatusModalMode, setShowCloseVacancyModal,
    setShowAddToListModal, setIsAddingToList, setShowBulkActionModal, setBulkActionType,
    setShowDataRequestModal, setDataRequestModalCandidate, setViewedCandidateIds,
    openSuperChat, returnToExpandedPrompt,
  } = uiModals.actions

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

  // Favorites State
  const [favoriteCandidates, setFavoriteCandidates] = useState<Set<string>>(new Set())
  const [shortListedCandidateIds, setShortListedCandidateIds] = useState<Set<string>>(new Set())
  const [activeShortListId, setActiveShortListId] = useState<string | null>(null)

  // Sync favorites from useTalentFunnel hook
  useEffect(() => {
    const favoriteIds = talentFunnel.getFavoriteIds()
    setFavoriteCandidates(favoriteIds)
  }, [talentFunnel.favorites])

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
      (c: Record<string, unknown>) =>
        (nav.candidateId && String(c.id) === String(nav.candidateId)) ||
        (nav.candidateName && c.name === nav.candidateName)
    )

    if (nav.openTransitionModal) {
      if (matched) {
        const candidateStage = Object.entries(candidatesData).find(
          ([, cands]) => (cands as Record<string, unknown>[]).some((c: Record<string, unknown>) => c.id === matched.id)
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
          const interviewStageId = interviewSlugMap[(nav as Record<string, unknown>).interviewType] || 'interview_hr'
          const matchedStage = dynamicStages.find(s => s.id === interviewStageId || s.actionBehavior === 'scheduling')
          if (matchedStage) {
            fromStage = matchedStage.id
            toStage = matchedStage.id
          }
        }

        const kanbanCandidate: KanbanCandidate = {
          id: matched.id as string,
          name: matched.name as string,
          email: (matched as Record<string, unknown>).email as string | undefined,
          phone: (matched as Record<string, unknown>).phone as string | undefined,
          avatar: (matched as Record<string, unknown>).avatar as string | undefined,
          role: ((matched as Record<string, unknown>).role || (matched as Record<string, unknown>).currentTitle) as string | undefined,
          currentTitle: (matched as Record<string, unknown>).currentTitle as string | undefined,
          currentCompany: ((matched as Record<string, unknown>).currentCompany || (matched as Record<string, unknown>).company) as string | undefined,
          location: (matched as Record<string, unknown>).location as string | undefined,
          stage: fromStage,
          sub_status: (matched as Record<string, unknown>).sub_status as string | undefined,
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

  // ── Tabela view — extraído para useKanbanTableView ──
  const tableView = useKanbanTableView({ dynamicStages, candidatesData, viewMode })
  const {
    showColumnConfig, tableColumns, columnSearchTerm,
    showTableFiltersPanel, showKanbanFiltersPanel,
    kanbanScoreMin, kanbanStatusFilter, kanbanWorkModelFilter, kanbanOriginFilter,
    tableSortColumn, tableSortDirection, tableStageFilter, currentPage, itemsPerPage,
    tableColumnWidths, draggedTableColumnId, dragOverTableColumnId, tableColumnOrder,
    pipelineStages, kanbanColumns,
  } = tableView.state
  const {
    setShowColumnConfig, setTableColumns, setColumnSearchTerm,
    setShowTableFiltersPanel, setShowKanbanFiltersPanel,
    setKanbanScoreMin, setKanbanStatusFilter, setKanbanWorkModelFilter, setKanbanOriginFilter,
    setTableSortColumn, setTableSortDirection, setTableStageFilter, setCurrentPage,
    setTableColumnWidths, setDraggedTableColumnId, setDragOverTableColumnId, setTableColumnOrder,
    handleTableColumnResize, handleTableSort, startTableColumnResize,
    handleTableColumnDragStart, handleTableColumnDragOver, handleTableColumnDragLeave,
    handleTableColumnDrop, handleTableColumnDragEnd,
    getAllCandidates, getFilteredAndSortedCandidates: _getFilteredAndSortedCandidates,
    getPaginatedCandidates: _getPaginatedCandidates,
    toggleStageFilter, clearStageFilters, getStageCount, getConversionRate,
  } = tableView.actions

  // Wrappers that pass searchQuery
  const getFilteredAndSortedCandidates = () => _getFilteredAndSortedCandidates(searchQuery)
  const getPaginatedCandidates = () => _getPaginatedCandidates(searchQuery)

  const [jobLocalOverrides, setJobLocalOverrides] = useState<Record<string, unknown>>({})
  const currentJob = (job ? { ...job, ...jobLocalOverrides } : jobData) as Record<string, unknown>

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
        salaryMin: (currentJob.salaryRange as Record<string,unknown>|undefined)?.min || currentJob.salaryMin || '',
        salaryMax: currentJob.salaryRange?.max || currentJob.salaryMax || '',
        bonusMin: (currentJob.bonusRange as Record<string,unknown>|undefined)?.min || (currentJob.bonus_range as Record<string,unknown>|undefined)?.min || '',
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
        interviewStages: ((currentJob.interviewStages as unknown[]) && (currentJob.interviewStages as unknown[]).length > 0 && (currentJob.interviewStages as Record<string, unknown>[])[0]?.stageCategory)
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
          const updated: Record<string, Record<string, unknown>[]> = {}
          for (const [stageId, candidates] of Object.entries(prev)) {
            updated[stageId] = candidates.map((c: Record<string, unknown>) => {
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
    return allTableCandidates.find((c: Record<string, unknown>) => String(c.id) === String(id))
  }, [allTableCandidates])

  const openUnifiedModal = useCallback((candidate: Record<string, unknown>, type: CommunicationType) => {
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

  // ── computedSuggestions + LIA briefing — extraídos para useKanbanLIASuggestions ──
  const { computedSuggestions, hasShownProactiveSuggestion, lastBriefingJobId } = useKanbanLIASuggestions({
    dynamicStages,
    candidatesData,
    allTableCandidates,
    currentJob,
    liaMessages,
    companyId: _companyIdForSL,
    setLiaMessages,
  })

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

  const getStageDisplayName = (stageId: string): string => {
    const stage = dynamicStages.find(s => s.id === stageId)
    if (stage) return stage.displayName
    const recruitmentStage = RECRUITMENT_STAGES.find(s => s.name === stageId)
    return recruitmentStage?.displayName || stageId
  }

  // Função para filtrar candidatos baseado na busca
  const filterCandidates = (candidates: Record<string, unknown>[]) => {
    if (!searchQuery) return candidates

    const query = searchQuery.toLowerCase()
    return candidates.filter(candidate => {
      const name = candidate.name as string | undefined
      const role = candidate.role as string | undefined
      const company = candidate.company as string | undefined
      const location = candidate.location as string | undefined
      const currentCompany = candidate.currentCompany as string | undefined
      return (
        (name?.toLowerCase() ?? '').includes(query) ||
        (role?.toLowerCase() ?? '').includes(query) ||
        (company?.toLowerCase() ?? '').includes(query) ||
        (location?.toLowerCase() ?? '').includes(query) ||
        (currentCompany?.toLowerCase() ?? '').includes(query)
      )
    })
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
  const handleOpenPreview = (candidate: Record<string, unknown>) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(true)
    if (candidate?.id) {
      markCandidateAsViewed(candidate.id as string)
    }
  }

  // Função para fechar o preview
  const handleClosePreview = () => {
    setIsPreviewOpen(false)
    setPreviewCandidate(null)
  }

  // Função para abrir a página completa do candidato
  const handleCandidatePageOpen = (candidate: Record<string, unknown>) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(false) // Fecha o preview
    setShowCandidatePage(true) // Abre a página completa
  }

  // Função para fechar a página completa do candidato
  const handleCloseCandidatePage = () => {
    setShowCandidatePage(false)
  }

  const handleSendEmail = (candidate: Record<string, unknown>) => openUnifiedModal(candidate, 'email')
  const handleSendWhatsApp = (candidate: Record<string, unknown>) => openUnifiedModal(candidate, 'whatsapp')
  const handleSendTriagem = (candidate: Record<string, unknown>) => openUnifiedModal(candidate, 'triagem')
  const handleSendAgendamento = (candidate: Record<string, unknown>) => openUnifiedModal(candidate, 'agendamento')
  const handleSendFeedback = (candidate: Record<string, unknown>) => openUnifiedModal(candidate, 'feedback')

  const handleUnifiedModalClose = () => {
    setUnifiedModalOpen(false)
    setUnifiedModalCandidate(null)
    setUnifiedModalSituation(undefined)
  }

  // Handlers para WSI Text Screening e Add to Vacancy
  const handleStartWSITextScreening = (candidate: Record<string, unknown>) => {
    setWsiCandidate(candidate)
    setShowWSIModal(true)
  }

  const handleAddToVacancy = (candidate: Record<string, unknown>) => {
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
      setCandidatesData((prevData: Record<string, Record<string, unknown>[]>) => {
        const newData = { ...prevData }
        for (const stageKey in newData) {
          newData[stageKey] = newData[stageKey].map((c: Record<string, unknown>) => 
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

  const handleScheduleInterview = (candidate: Record<string, unknown>) => {
    setUnifiedModalCandidate(candidate)
    setUnifiedModalType('agendamento')
    setUnifiedModalOpen(true)
  }

  const handleNavigateCandidate = (index: number) => {
    const data = candidatesData as Record<string, Record<string, unknown>[]>
    const currentColumn = Object.keys(data).find(col => 
      data[col].some((c: Record<string, unknown>) => c.id === previewCandidate?.id)
    )
    if (currentColumn && data[currentColumn][index]) {
      setPreviewCandidate(data[currentColumn][index])
    }
  }

  const handleSendWSIInvite = (candidate: Record<string, unknown>) => {
    setWsiInviteCandidate(candidate)
    setShowWSIInviteModal(true)
  }

  const handleCloseTriagem = useCallback(() => {
    setIsTriagemOpen(false)
    setTriagemCandidate(null)
  }, [setIsTriagemOpen, setTriagemCandidate])

  const handleRubricModalClose = useCallback(() => {
    setShowRubricModal(false)
    setRubricCandidate(null)
    setRubricEvaluationData(null)
  }, [setShowRubricModal, setRubricCandidate, setRubricEvaluationData])

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

  const handleOpenTriagem = useCallback((candidate: Record<string, unknown>) => {
    setTriagemCandidate(candidate)
    setIsTriagemOpen(true)
  }, [])

  // Função para abrir modais de scores (dos cards do Kanban)
  const handleOpenScoreModal = (candidate: Record<string, unknown>, modalType: 'geral' | 'triagem' | 'cv' | 'tecnico' | 'ingles' | 'b5') => {
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

  // Backgrounds para colunas do Kanban - suporta etapas dinâmicas
  // Usa a cor da etapa dinâmica e fornece estilo padrão para etapas não conhecidas
  const getColumnStyle = (columnId: string) => {
    // Estilos fixos para etapas conhecidas
    const fixedStyles: Record<string, { bg: string; border: string; dot: string; header: string; accentColor: string }> = {
      sourcing: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-600)'
      },
      hired: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-700 dark:bg-gray-300',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-600)'
      },
      rejected: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-300 dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
        accentColor: 'var(--gray-200)'
      },
      offer_declined: {
        bg: 'bg-white dark:bg-lia-bg-primary',
        border: 'border-lia-border-subtle dark:border-lia-border-subtle',
        dot: 'bg-gray-300 dark:bg-lia-bg-elevated',
        header: 'text-lia-text-primary dark:text-lia-text-primary',
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
      bg: 'bg-white dark:bg-lia-bg-primary',
      border: 'border-lia-border-subtle dark:border-lia-border-subtle',
      dot: 'bg-gray-500 dark:bg-gray-400',
      header: 'text-lia-text-primary dark:text-lia-text-primary',
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


  return {
    viewMode, setViewMode,
    saturationData, setSaturationData,
    isCreationMode, setIsCreationMode,
    isPublishing, setIsPublishing,
    publicLink, setPublicLink,
    showPublishSuccess, setShowPublishSuccess,
    activeTab, setActiveTab,
    selectedCandidate, setSelectedCandidate,
    selectedTriagemCandidate, setSelectedTriagemCandidate,
    showExpandedMetrics, setShowExpandedMetrics,
    isClient, setIsClient,
    jobEditForm, setJobEditForm,
    dynamicStages, setDynamicStages,
    showAddColumnPopover, setShowAddColumnPopover,
    newColumnName, setNewColumnName,
    inferredBehavior, setInferredBehavior,
    isAddingColumn, setIsAddingColumn,
    draggedCandidate, setDraggedCandidate,
    dragOverColumn, setDragOverColumn,
    candidatesData, setCandidatesData,
    isLoadingCandidates, setIsLoadingCandidates,
    hasMounted, setHasMounted,
    showDataRequestModal, setShowDataRequestModal,
    dataRequestModalCandidate, setDataRequestModalCandidate,
    selectedCandidates, setSelectedCandidates,
    searchQuery, setSearchQuery,
    previewCandidate, setPreviewCandidate,
    isPreviewOpen, setIsPreviewOpen,
    showCandidatePage, setShowCandidatePage,
    triagemCandidate, setTriagemCandidate,
    showReport, setShowReport,
    isTriagemOpen, setIsTriagemOpen,
    showTestPreview, setShowTestPreview,
    editingQuestion, setEditingQuestion,
    showLiaSuggestions, setShowLiaSuggestions,
    liaSuggestionsData, setLiaSuggestionsData,
    showLiaSuggestionsPanel, setShowLiaSuggestionsPanel,
    showExpandedLIA, setShowExpandedLIA,
    transitionInitialPrompt, setTransitionInitialPrompt,
    transitionAllowStageSelection, setTransitionAllowStageSelection,
    transitionInterviewAlert, setTransitionInterviewAlert,
    showSuperChat, setShowSuperChat,
    liaPromptValue, setLiaPromptValue,
    liaMessages, setLiaMessages,
    isLiaLoading, setIsLiaLoading,
    liaConversationId, setLiaConversationId,
    liaSearchQuery, setLiaSearchQuery,
    userCollapsedLIA, setUserCollapsedLIA,
    liaExpandedWidth, setLiaExpandedWidth,
    isResizingLIA, setIsResizingLIA,
    showTestLibrary, setShowTestLibrary,
    showTestHistory, setShowTestHistory,
    selectedTestForHistory, setSelectedTestForHistory,
    showConceptualPrompt, setShowConceptualPrompt,
    isEditModeTriagem, setIsEditModeTriagem,
    showConceptualPromptTriagem, setShowConceptualPromptTriagem,
    showApresentacaoPrompt, setShowApresentacaoPrompt,
    showFechamentoPrompt, setShowFechamentoPrompt,
    isEditMode, setIsEditMode,
    showTriagemSuggestions, setShowTriagemSuggestions,
    selectedTriagemQuestion, setSelectedTriagemQuestion,
    expandedCronograma, setExpandedCronograma,
    expandedTesteTecnico, setExpandedTesteTecnico,
    expandedTesteIngles, setExpandedTesteIngles,
    expandedRoteiro, setExpandedRoteiro,
    showEmailModal, setShowEmailModal,
    emailCandidate, setEmailCandidate,
    showShareGestorModal, setShowShareGestorModal,
    unifiedModalOpen, setUnifiedModalOpen,
    unifiedModalType, setUnifiedModalType,
    unifiedModalCandidate, setUnifiedModalCandidate,
    unifiedModalSituation, setUnifiedModalSituation,
    showWSIModal, setShowWSIModal,
    wsiCandidate, setWsiCandidate,
    showWSIInviteModal, setShowWSIInviteModal,
    wsiInviteCandidate, setWsiInviteCandidate,
    showAddToVacancyModal, setShowAddToVacancyModal,
    candidateForVacancy, setCandidateForVacancy,
    showRubricModal, setShowRubricModal,
    rubricCandidate, setRubricCandidate,
    rubricEvaluationData, setRubricEvaluationData,
    selectedCandidateForModal, setSelectedCandidateForModal,
    activeModal, setActiveModal,
    showBigFiveModal, setShowBigFiveModal,
    showGeneralScoreModal, setShowGeneralScoreModal,
    showTechnicalTestModal, setShowTechnicalTestModal,
    showEnglishTestModal, setShowEnglishTestModal,
    scoreModalCandidate, setScoreModalCandidate,
    showCompareModal, setShowCompareModal,
    compareCandidates, setCompareCandidates,
    selectedForCompare, setSelectedForCompare,
    showDecisionFlowModal, setShowDecisionFlowModal,
    decisionFlowCandidate, setDecisionFlowCandidate,
    decisionFlowType, setDecisionFlowType,
    pendingMove, setPendingMove,
    statusModalOpen, setStatusModalOpen,
    selectedSubStatus, setSelectedSubStatus,
    showJobStatusModal, setShowJobStatusModal,
    jobStatusModalMode, setJobStatusModalMode,
    showCloseVacancyModal, setShowCloseVacancyModal,
    perguntasEliminatorias, setPerguntasEliminatorias,
    perguntasInformativas, setPerguntasInformativas,
    habilidadesTecnicas, setHabilidadesTecnicas,
    perguntasTecnicasAvaliacao, setPerguntasTecnicasAvaliacao,
    skillWeights, setSkillWeights,
    isSkillWeightsModified, setIsSkillWeightsModified,
    perguntasSituacionais, setPerguntasSituacionais,
    showAddToListModal, setShowAddToListModal,
    isAddingToList, setIsAddingToList,
    showBulkActionModal, setShowBulkActionModal,
    bulkActionType, setBulkActionType,
    isPreviewMaximized, setIsPreviewMaximized,
    favoriteCandidates, setFavoriteCandidates,
    shortListedCandidateIds, setShortListedCandidateIds,
    activeShortListId, setActiveShortListId,
    viewedCandidateIds, setViewedCandidateIds,
    showColumnConfig, setShowColumnConfig,
    tableColumns, setTableColumns,
    columnSearchTerm, setColumnSearchTerm,
    showTableFiltersPanel, setShowTableFiltersPanel,
    showKanbanFiltersPanel, setShowKanbanFiltersPanel,
    kanbanScoreMin, setKanbanScoreMin,
    kanbanStatusFilter, setKanbanStatusFilter,
    kanbanWorkModelFilter, setKanbanWorkModelFilter,
    kanbanOriginFilter, setKanbanOriginFilter,
    tableSortColumn, setTableSortColumn,
    tableSortDirection, setTableSortDirection,
    tableStageFilter, setTableStageFilter,
    currentPage, setCurrentPage,
    tableColumnWidths, setTableColumnWidths,
    draggedTableColumnId, setDraggedTableColumnId,
    dragOverTableColumnId, setDragOverTableColumnId,
    tableColumnOrder, setTableColumnOrder,
    jobLocalOverrides, setJobLocalOverrides,
    showJobEditor, setShowJobEditor,
    editingSection, setEditingSection,
    savingJobSection, setSavingJobSection,
    router,
    toast,
    user,
    saveJobsState,
    talentFunnel,
    _companyIdForSL,
    _jobIdForSL,
    shortLists,
    _createSL,
    _addToSL,
    _removeFromSL,
    proactiveInsights,
    dismissInsight,
    aiSuggestions,
    approveSuggestion,
    rejectSuggestion,
    pipelineInheritance,
    returnEvents,
    getAlertForCandidate,
    computeAlerts,
    hasAlerts,
    companyDefaults,
    allTableCandidates,
    allCandidateIds,
    handleBulkAction,
    handleBulkActionExecute,
    handleLiaUiAction,
    handleAICommand,
    handleOrchestratedMessage,
    handleDragStart,
    handleDragEnd,
    handleDragOver,
    handleDragLeave,
    getSuggestedSubStatus,
    getAvailableSubStatuses,
    getSubStatusColor,
    stagesRequiringConfirmation,
    handleDrop,
    confirmMove,
    cancelMove,
    handleDecisionFlowConfirm,
    handleApproveCandidate,
    handleRejectCandidate,
    handleApproveFromScreening,
    handleRejectFromScreening,
    handleTriagemApprove,
    handleTriagemReject,
    handleOpenAnalysis,
    openDecisionFlowModal,
    handleSaveJobSection,
    handleInlineRename,
    handleInlineToggleActive,
    handleInlineRemove,
    handleInlineMoveLeft,
    handleInlineMoveRight,
    handleInlineUpdateSLA,
    universalModalState,
    openTransition,
    closeTransition,
    findCandidateById,
    openUnifiedModal,
    computedSuggestions,
    filterCandidates,
    markCandidateAsViewed,
    handleOpenPreview,
    handleClosePreview,
    handleCandidatePageOpen,
    handleCloseCandidatePage,
    handleSendEmail,
    handleSendWhatsApp,
    handleSendTriagem,
    handleSendAgendamento,
    handleSendFeedback,
    handleUnifiedModalClose,
    handleStartWSITextScreening,
    handleAddToVacancy,
    handleTogglePreviewMaximize,
    handleToggleFavorite,
    handleToggleShortList,
    handleInteractiveStatusChange,
    handleTableTransitionRequest,
    handleTableSort,
    startTableColumnResize,
    handleTableColumnDragStart,
    handleTableColumnDragOver,
    handleTableColumnDragLeave,
    handleTableColumnDrop,
    handleTableColumnDragEnd,
    handleShowReport,
    handleCloseReport,
    getAllCandidates,
    getPaginatedCandidates,
    toggleStageFilter,
    clearStageFilters,
    getStageCount,
    getConversionRate,
    pipelineStages,
    kanbanColumns,
    getColumnStyle,
    getStageAccentStyle,
    getStageCategory,
    STAGE_PASTEL_COLORS,
    handleOpenScoreModal,
    handleScheduleInterview,
    handleSendWSIInvite,
    handleNavigateCandidate,
    handlePublishJob,
    handleRubricModalClose,
    chatScrollRef,
    hasShownProactiveSuggestion,
    lastBriefingJobId,
    openSuperChat,
    returnToExpandedPrompt,
    handleOpenTriagem,
    handleCloseTriagem,
    handleTransitionRequired,
    handleUniversalTransitionConfirm,
    handleOpenSpecializedModal,
    handleDataRequestSubmit,
    handleDataRequestResend,
    handleDataRequestViewDetails,
    getDataRequestForCandidate,
    handleTableColumnResize,
    currentJob,
    jobData,
    getFilteredAndSortedCandidates,
    calculateNotaLiaGeral,
    getStageDisplayName,
  }
}

export type KanbanPageCoreState = ReturnType<typeof useKanbanPageCore>
