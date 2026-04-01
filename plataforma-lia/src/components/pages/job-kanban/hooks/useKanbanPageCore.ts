"use client"

import { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
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
} from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { type DynamicStage } from "@/components/kanban"
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
import { useKanbanFilters } from "@/components/pages/job-kanban/hooks/useKanbanFilters"
import { useKanbanPublishing } from "@/components/pages/job-kanban/hooks/useKanbanPublishing"
import { useKanbanColumnConfig } from "@/components/pages/job-kanban/hooks/useKanbanColumnConfig"
import { useKanbanCandidateHandlers } from "@/components/pages/job-kanban/hooks/useKanbanCandidateHandlers"
import { useKanbanTransitionHandlers } from "@/components/pages/job-kanban/hooks/useKanbanTransitionHandlers"
import { useKanbanNavigation } from "@/components/pages/job-kanban/hooks/useKanbanNavigation"

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

  const [activeTab, setActiveTab] = useState<"management" | "edit">("management")
  const [selectedCandidate, setSelectedCandidate] = useState<Record<string, unknown> | null>(null)
  const [selectedTriagemCandidate, setSelectedTriagemCandidate] = useState<Record<string, unknown> | null>(null)
  const [showExpandedMetrics, setShowExpandedMetrics] = useState(false)

  const [jobEditForm, setJobEditForm] = useState<Record<string, unknown>>({})

  // Publishing state + handler extracted to useKanbanPublishing
  const {
    isCreationMode, setIsCreationMode,
    isPublishing, setIsPublishing,
    publicLink, setPublicLink,
    showPublishSuccess, setShowPublishSuccess,
    handlePublishJob,
  } = useKanbanPublishing({ job, jobEditForm, setJobEditForm, setActiveTab, toast: toast as unknown as Parameters<typeof useKanbanPublishing>[0]["toast"] })

  // Persistência de navegação - salva estado quando muda
  useEffect(() => {
    if (job?.id) {
      saveJobsState(String(job.id), viewMode, activeTab)
    }
  }, [job?.id, viewMode, activeTab, saveJobsState])

  // Estados para etapas dinâmicas do Kanban
  const [dynamicStages, setDynamicStages] = useState<DynamicStage[]>(() =>
    mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]) as unknown as DynamicStage[]
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

  // handleTransitionRequired — extracted to useKanbanTransitionHandlers

  // Estados para candidatesData (hoisted before useKanbanTransitions)
  const [candidatesData, setCandidatesData] = useState<Record<string, Record<string, unknown>[]>>(() =>
    createInitialCandidatesData(mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]))
  )

  // ── handleUniversalTransitionConfirm — extraído para useKanbanTransitions ──
  const { handleUniversalTransitionConfirm } = useKanbanTransitions({
    candidatesData,
    setCandidatesData,
    universalModalState: universalModalState as unknown as Parameters<typeof useKanbanTransitions>[0]["universalModalState"],
    closeTransition,
    toast,
  })

  // handleOpenSpecializedModal — extracted to useKanbanTransitionHandlers

  // Estados para drag and drop
  const [draggedCandidate, setDraggedCandidate] = useState<Record<string, unknown> | null>(null)
  const [dragOverColumn, setDragOverColumn] = useState<string | null>(null)

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


  // ── Carregamento de candidatos — extraído para useKanbanCandidateLoader ──
  const candidateLoader = useKanbanCandidateLoader({ job, dynamicStages, setCandidatesData })
  const { isLoadingCandidates, hasMounted, isClient } = candidateLoader.state
  const { setIsLoadingCandidates, setHasMounted, setIsClient } = candidateLoader.actions

  // ── Filtros, seleção e favoritos — extraído para useKanbanFilters ──
  const kanbanFilters = useKanbanFilters({
    talentFunnel,
    shortLists,
    createShortList: _createSL,
    addCandidateToShortList: _addToSL,
    removeCandidateFromShortList: _removeFromSL,
    jobId: _jobIdForSL,
    jobTitle: job?.title as string | undefined,
  })
  const {
    searchQuery, setSearchQuery,
    filterCandidates,
    selectedCandidates, setSelectedCandidates,
    favoriteCandidates, setFavoriteCandidates,
    handleToggleFavorite,
    shortListedCandidateIds, setShortListedCandidateIds,
    activeShortListId, setActiveShortListId,
    handleToggleShortList,
  } = kanbanFilters

  // ── Modais e UI — extraído para useKanbanUIModals ──
  const uiModals = useKanbanUIModals({ job, toast: toast as unknown as Parameters<typeof useKanbanUIModals>[0]["toast"] })
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

  // Transition handlers extracted to useKanbanTransitionHandlers
  const { handleTransitionRequired, handleOpenSpecializedModal } = useKanbanTransitionHandlers({
    openTransition,
    closeTransition,
    setTransitionInitialPrompt,
    setTransitionAllowStageSelection,
    setTransitionInterviewAlert,
    setWsiInviteCandidate: setWsiInviteCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal,
    setUnifiedModalCandidate: setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setUnifiedModalCandidate"],
    setUnifiedModalType: setUnifiedModalType as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setUnifiedModalType"],
    setUnifiedModalSituation,
    setUnifiedModalOpen,
    setDataRequestModalCandidate: setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal,
    setDecisionFlowCandidate: setDecisionFlowCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDecisionFlowCandidate"],
    setDecisionFlowType: setDecisionFlowType as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDecisionFlowType"],
    setShowDecisionFlowModal,
  })

  const handleDataRequestSubmit = useCallback(async (_data: DataRequestSubmitData) => {
    toast({
      title: "Solicitação Enviada",
      description: `Solicitação de dados enviada para ${(dataRequestModalCandidate as Record<string,unknown>|null)?.name as string || 'candidato'}`,
    })
    setShowDataRequestModal(false)
    setDataRequestModalCandidate(null)
  }, [dataRequestModalCandidate, toast, setShowDataRequestModal, setDataRequestModalCandidate])

  const { handleBulkAction, handleBulkActionExecute } = useKanbanBulkActions({
    selectedCandidates,
    setSelectedCandidates,
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanBulkActions>[0]["allTableCandidates"],
    toast,
    setBulkActionType,
    setShowBulkActionModal,
    setDataRequestModalCandidate: setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal,
    setUnifiedModalType,
    setUnifiedModalCandidate: setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setUnifiedModalCandidate"],
    setUnifiedModalOpen,
    setWsiInviteCandidate: setWsiInviteCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal,
    setShowShareGestorModal,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanBulkActions>[0]["setCandidatesData"],
  })


  // Navigation — extracted to useKanbanNavigation
  const { pendingNavigationRef, processPendingNavigation } = useKanbanNavigation({
    jobId: job?.id?.toString(),
    candidatesData,
    dynamicStages,
    openTransition,
    setTransitionInitialPrompt,
    setTransitionAllowStageSelection,
    setLiaPromptValue,
    setShowExpandedLIA,
    setPreviewCandidate,
    setIsPreviewOpen,
    toast: toast as unknown as Parameters<typeof useKanbanNavigation>[0]["toast"],
    setUnifiedModalCandidate: setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanNavigation>[0]["setUnifiedModalCandidate"],
    setUnifiedModalType: setUnifiedModalType as unknown as Parameters<typeof useKanbanNavigation>[0]["setUnifiedModalType"],
    setUnifiedModalOpen,
  })

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
        salaryMax: (currentJob.salaryRange as Record<string,unknown>|undefined)?.max || currentJob.salaryMax || '',
        bonusMin: (currentJob.bonusRange as Record<string,unknown>|undefined)?.min || (currentJob.bonus_range as Record<string,unknown>|undefined)?.min || '',
        bonusMax: (currentJob.bonusRange as Record<string,unknown>|undefined)?.max || (currentJob.bonus_range as Record<string,unknown>|undefined)?.max || '',
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
    if (jobEditForm.languages && (jobEditForm.languages as unknown[]).length > 0) return

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
              const wsiData = data.candidates[c.id as string]
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
    setUnifiedModalCandidate(candidate as unknown as Parameters<typeof setUnifiedModalCandidate>[0])
    setUnifiedModalType(type)
    setUnifiedModalOpen(true)
  }, [setUnifiedModalCandidate, setUnifiedModalType, setUnifiedModalOpen])

  const { handleLiaUiAction, handleAICommand, handleOrchestratedMessage } = useKanbanLIAHandlers({
    liaMessages,
    setLiaMessages: setLiaMessages as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setLiaMessages"],
    setLiaPromptValue,
    setIsLiaLoading,
    setShowExpandedLIA,
    setShowSuperChat,
    setUserCollapsedLIA,
    liaConversationId,
    setLiaConversationId,
    currentJob,
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["allTableCandidates"],
    selectedCandidates,
    candidatesData: candidatesData as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["candidatesData"],
    user,
    findCandidateById: findCandidateById as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["findCandidateById"],
    openUnifiedModal: openUnifiedModal as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["openUnifiedModal"],
    openTransition,
    setWsiCandidate: setWsiCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setWsiCandidate"],
    setShowWSIModal,
    setWsiInviteCandidate: setWsiInviteCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal,
    setDataRequestModalCandidate: setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal,
    setRubricCandidate: setRubricCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setRubricCandidate"],
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
    dynamicStages: dynamicStages as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["dynamicStages"],
    candidatesData: candidatesData as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["candidatesData"],
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["allTableCandidates"],
    currentJob,
    liaMessages,
    companyId: _companyIdForSL,
    setLiaMessages: setLiaMessages as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["setLiaMessages"],
  })

  const { handleDragStart, handleDragEnd, handleDragOver, handleDragLeave, getSuggestedSubStatus, getAvailableSubStatuses, getSubStatusColor, stagesRequiringConfirmation, handleDrop, confirmMove, cancelMove } = useKanbanDragDrop({
    draggedCandidate: draggedCandidate as unknown as Parameters<typeof useKanbanDragDrop>[0]["draggedCandidate"],
    setDraggedCandidate: setDraggedCandidate as unknown as Parameters<typeof useKanbanDragDrop>[0]["setDraggedCandidate"],
    dragOverColumn,
    setDragOverColumn,
    dynamicStages,
    openTransition,
    pendingMove: pendingMove as unknown as Parameters<typeof useKanbanDragDrop>[0]["pendingMove"],
    setPendingMove: setPendingMove as unknown as Parameters<typeof useKanbanDragDrop>[0]["setPendingMove"],
    statusModalOpen,
    setStatusModalOpen,
    selectedSubStatus,
    setSelectedSubStatus,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanDragDrop>[0]["setCandidatesData"],
    job: job as unknown as Parameters<typeof useKanbanDragDrop>[0]["job"],
  })

  // Candidate handlers — extracted to useKanbanCandidateHandlers
  const {
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
    handleInteractiveStatusChange,
    handleTableTransitionRequest,
    handleScheduleInterview,
    handleNavigateCandidate,
    handleSendWSIInvite,
    handleCloseTriagem,
    handleRubricModalClose,
    handleShowReport,
    handleCloseReport,
  } = useKanbanCandidateHandlers({
    setPreviewCandidate,
    setIsPreviewOpen,
    setShowCandidatePage,
    isPreviewMaximized,
    setIsPreviewMaximized,
    previewCandidate,
    setViewedCandidateIds,
    openUnifiedModal,
    setUnifiedModalOpen,
    setUnifiedModalCandidate: setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setUnifiedModalCandidate"],
    setUnifiedModalSituation,
    setUnifiedModalType: setUnifiedModalType as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setUnifiedModalType"],
    setWsiCandidate: setWsiCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setWsiCandidate"],
    setShowWSIModal,
    setCandidateForVacancy: setCandidateForVacancy as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setCandidateForVacancy"],
    setShowAddToVacancyModal,
    setWsiInviteCandidate: setWsiInviteCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal,
    setIsTriagemOpen,
    setTriagemCandidate: setTriagemCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setTriagemCandidate"],
    setShowRubricModal,
    setRubricCandidate: setRubricCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setRubricCandidate"],
    setRubricEvaluationData: setRubricEvaluationData as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setRubricEvaluationData"],
    setShowReport,
    setCandidatesData,
    candidatesData,
    jobDataId: jobData?.id,
    openTransition,
  })

  // Handlers para Rubric Evaluation Modal
  // Funções para abrir modal de fluxo de decisão
  const { handleDecisionFlowConfirm, handleApproveCandidate, handleRejectCandidate, handleApproveFromScreening, handleRejectFromScreening, handleTriagemApprove, handleTriagemReject, handleOpenAnalysis, openDecisionFlowModal } = useKanbanCandidateDecisions({
    toast,
    job: job as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["job"],
    dynamicStages,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setCandidatesData"],
    setShowDecisionFlowModal,
    setDecisionFlowCandidate: setDecisionFlowCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setDecisionFlowCandidate"],
    decisionFlowCandidate: decisionFlowCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["decisionFlowCandidate"],
    openTransition,
    setTransitionInitialPrompt,
    onCloseTriagem: handleCloseTriagem,
    setRubricCandidate: setRubricCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setRubricCandidate"],
    setShowRubricModal,
    setRubricEvaluationData: setRubricEvaluationData as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setRubricEvaluationData"],
    setDecisionFlowType: setDecisionFlowType as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setDecisionFlowType"],
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
        handleOpenAnalysis(candidate as unknown as Parameters<typeof handleOpenAnalysis>[0])
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
    toast: toast as unknown as Parameters<typeof useKanbanJobEditing>[0]["toast"],
    currentJob: currentJob as unknown as Parameters<typeof useKanbanJobEditing>[0]["currentJob"],
    jobEditForm,
    setSavingJobSection,
    setEditingSection,
    setDynamicStages: setDynamicStages as unknown as Parameters<typeof useKanbanJobEditing>[0]["setDynamicStages"],
    setCandidatesData,
    mapInterviewStagesToKanban: mapInterviewStagesToKanban as unknown as Parameters<typeof useKanbanJobEditing>[0]["mapInterviewStagesToKanban"],
    createInitialCandidatesData: createInitialCandidatesData as unknown as Parameters<typeof useKanbanJobEditing>[0]["createInitialCandidatesData"],
  })

  // Funções para o relatório

  // Backgrounds para colunas do Kanban - suporta etapas dinâmicas
  // Usa a cor da etapa dinâmica e fornece estilo padrão para etapas não conhecidas
  // Column config — extracted to useKanbanColumnConfig
  const { getColumnStyle, getStageAccentStyle, getStageCategory, getStageDisplayName, STAGE_PASTEL_COLORS } = useKanbanColumnConfig({ dynamicStages })

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
