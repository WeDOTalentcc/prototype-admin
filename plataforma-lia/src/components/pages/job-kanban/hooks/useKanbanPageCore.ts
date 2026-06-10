"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import { useSearchParams } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { useAuthStore } from "@/stores/auth-store"
import { useKanbanStore } from "@/stores/kanban-store"
import { useShortList } from "@/hooks/candidates/use-short-list"
import { useProactiveInsights } from "@/hooks/ai/use-proactive-insights"
import { useNavigationPersistence } from "@/hooks/shared/use-navigation-persistence"
import { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"
import { useCandidateSuggestions } from "@/hooks/ai/useCandidateSuggestions"
import { type TableColumn } from "@/components/tables"
import { useUniversalTransition, type KanbanCandidate } from "@/components/kanban"
import { type UniversalTransitionConfirmData } from "@/components/kanban"
import { type BulkActionType } from "@/components/ui/bulk-actions-bar"
import { usePipelineInheritance } from "@/hooks/recruitment/use-pipeline-inheritance"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { enrichStagesWithSubStatuses, buildSubStatusMap, applyVacancyStageOverrides } from "@/components/kanban/utils/stage-utils"
import { useReturnEvents } from '@/hooks/recruitment/use-return-events'
import { useBulkCandidateDataRequests } from "@/hooks/candidates/use-candidate-data-requests"
import { type DataRequestSubmitData } from "@/components/modals/data-request-modal"
import { DEFAULT_DATA_FIELDS } from "@/hooks/company/use-data-request-config"
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
import { useOfferReviewFlow } from "@/hooks/offers/useOfferReviewFlow"
import { useKanbanJobFormInit } from "@/components/pages/job-kanban/hooks/useKanbanJobFormInit"
import { useKanbanDataEffects } from "@/components/pages/job-kanban/hooks/useKanbanDataEffects"
import { toast } from "sonner"

/**
 * Extract the company UUID from the authenticated user shape.
 * The backend expects a real `company_id` (UUID); historically this hook
 * read `user.company` (which doesn't exist on AuthenticatedUser) and fell
 * back to the literal string `'demo'`, which then made the backend reject
 * the request and return an empty insights list. Returns null when the
 * user is not yet loaded or has no company_id, so callers can skip the
 * remote fetch instead of issuing a guaranteed-bad request.
 */
export function getCompanyIdFromUser(user: unknown): string | null {
  if (!user || typeof user !== 'object') return null
  const candidate = (user as Record<string, unknown>).company_id
  return typeof candidate === 'string' && candidate.length > 0 ? candidate : null
}

const EMPTY_JOB_FALLBACK: Record<string, unknown> & { id: number; jobId: string } = {
  id: 0,
  jobId: "",
  title: "Vaga não carregada",
  department: "",
  location: "",
  status: "Inativa",
  funnel: { total: 0, screening: 0, interview: 0, final: 0, hired: 0 },
}

export function useKanbanPageCore({ job, onBack }: { job?: Record<string, unknown>; onBack?: () => void }) {
  const { saveJobsState } = useNavigationPersistence()
  const { user } = useAuth()
  const authStoreUser = useAuthStore((s) => s.user)
  const talentFunnel = useTalentFunnel()
  // Read the real `company_id` UUID from the auth store. The `useAuth()`
  // wrapper omits it, and the previous code mistakenly read `user.company`
  // (which doesn't exist) and fell back to the literal `'demo'`, causing
  // the backend to reject every proactive-insights request.
  const _companyIdForSL = getCompanyIdFromUser(authStoreUser)
  const _jobIdForSL = job?.id?.toString()
  const { shortLists, createShortList: _createSL, addCandidate: _addToSL, removeCandidate: _removeFromSL } = useShortList(_companyIdForSL ?? '', _jobIdForSL)
  const { insights: proactiveInsights, dismiss: dismissInsight } = useProactiveInsights(_jobIdForSL, _companyIdForSL)
  const { suggestions: aiSuggestions, approveSuggestion, rejectSuggestion } = useCandidateSuggestions(job?.id?.toString() || '')
  const pipelineInheritance = usePipelineInheritance(job?.id?.toString())
  const { events: returnEvents, getAlertForCandidate, computeAlerts, hasAlerts } = useReturnEvents({
    jobId: job?.id?.toString(),
    enabled: true,
    pollingIntervalMs: 30000,
  })

  useEffect(() => {
    if (job?.id) pipelineInheritance.checkStatus()
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: pipelineInheritance object excluded to avoid re-runs
  }, [job?.id])

  const viewMode = useKanbanStore((s) => s.viewMode)
  const setViewMode = useKanbanStore((s) => s.setViewMode)
  const activeTab = useKanbanStore((s) => s.activeTab)
  const setActiveTab = useKanbanStore((s) => s.setActiveTab)

  // Phase A.4 — deep-link support: when the page mounts with ?tab=edit
  // (e.g. opened via vacancy preview "Continuar JD" / "Configurar WSI"),
  // hydrate the Zustand store. Only runs once on mount per job; subsequent
  // user-driven tab changes go through setActiveTab as usual.
  // See .planning/vacancy-pipeline-plan.md > Phase A.4.
  const _searchParams = useSearchParams()
  useEffect(() => {
    const requested = _searchParams?.get("tab")
    if (requested === "edit" || requested === "management") {
      if (requested !== activeTab) {
        setActiveTab(requested)
      }
    }
    // We intentionally only sync when job changes — eslint-disable-next-line
    // is unnecessary because `_searchParams` and `activeTab` are stable across
    // renders for the same URL/store state, but we list them all.
  }, [job?.id, _searchParams, activeTab, setActiveTab])
  const selectedCandidate = useKanbanStore((s) => s.selectedCandidate)
  const setSelectedCandidate = useKanbanStore((s) => s.setSelectedCandidate)
  const [selectedTriagemCandidate, setSelectedTriagemCandidate] = useState<Record<string, unknown> | null>(null)
  const showExpandedMetrics = useKanbanStore((s) => s.showExpandedMetrics)
  const setShowExpandedMetrics = useKanbanStore((s) => s.setShowExpandedMetrics)

  const [jobLocalOverrides, setJobLocalOverrides] = useState<Record<string, unknown>>({})
  const currentJob = (job ? { ...job, ...jobLocalOverrides } : EMPTY_JOB_FALLBACK) as Record<string, unknown>

  const { jobEditForm, setJobEditForm, companyDefaults } = useKanbanJobFormInit(currentJob)

  const {
    isCreationMode, setIsCreationMode,
    isPublishing, setIsPublishing,
    publicLink, setPublicLink,
    showPublishSuccess, setShowPublishSuccess,
    handlePublishJob,
  } = useKanbanPublishing({ job, jobEditForm, setJobEditForm, setActiveTab })

  useEffect(() => {
    if (job?.id) saveJobsState(String(job.id), viewMode, activeTab)
  }, [job?.id, viewMode, activeTab, saveJobsState])

  const [dynamicStages, setDynamicStages] = useState<DynamicStage[]>(() =>
    mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]) as unknown as DynamicStage[]
  )

  const { stages: companyPipelineStages } = useRecruitmentStages()
  useEffect(() => {
    if (!companyPipelineStages.length) return
    const subStatusMap = applyVacancyStageOverrides(
      buildSubStatusMap(
        companyPipelineStages.map(s => ({
          name: s.name,
          sub_statuses: (s.sub_statuses || []).map(ss => ({
            name: ss.name, display_name: ss.display_name, is_default: ss.is_default,
            is_waiting: ss.is_waiting, waiting_for: ss.waiting_for,
          })),
        }))
      ),
      job?.interviewStages as Parameters<typeof applyVacancyStageOverrides>[1]
    )
    setDynamicStages(prev => enrichStagesWithSubStatuses(prev, subStatusMap))
  }, [companyPipelineStages, job?.interviewStages])

  const [showAddColumnPopover, setShowAddColumnPopover] = useState(false)
  const [newColumnName, setNewColumnName] = useState("")
  const [inferredBehavior, setInferredBehavior] = useState<{suggested_behavior: string, confidence: number} | null>(null)
  const [isAddingColumn, setIsAddingColumn] = useState(false)

  const { modalState: universalModalState, openTransition: openTransitionRaw, closeTransition } = useUniversalTransition(dynamicStages)

  // PR-B: hook de criação de draft de proposta
  const { openOfferReview } = useOfferReviewFlow()

  // Intercept drag/drop para coluna "oferta" → abre OfferReviewModal antes do TransitionModal
  const openTransition = useCallback(
    (candidates: KanbanCandidate[], fromStage: string, toStage: string) => {
      if ((toStage === "oferta" || toStage === "offer") && candidates.length > 0 && job?.id) {
        openOfferReview({ candidateId: String((candidates[0] as { candidateId?: string; id: string }).candidateId ?? candidates[0].id), jobId: String((job as { backendId?: string })?.backendId ?? job?.id ?? "") })
        return
      }
      openTransitionRaw(candidates, fromStage, toStage)
    },
    [openTransitionRaw, openOfferReview, job],
  )

  const candidatesData = useKanbanStore((s) => s.candidatesData)
  const setCandidatesData = useKanbanStore((s) => s.setCandidatesData)
  const resetKanbanStore = useKanbanStore((s) => s.resetStore)
  const jobId = job?.id
  const jobStagesJson = JSON.stringify(job?.interviewStages ?? [])
  useEffect(() => {
    const initial = createInitialCandidatesData(mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]))
    setCandidatesData(initial)
    useKanbanStore.getState().clearSelection()
    useKanbanStore.getState().setSearchQuery('')
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: jobStagesJson covers interviewStages; setCandidatesData is stable
  }, [jobId, jobStagesJson])
  useEffect(() => {
    return () => { resetKanbanStore() }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: run only on unmount
  }, [])

  const { handleUniversalTransitionConfirm } = useKanbanTransitions({
    candidatesData,
    setCandidatesData,
    universalModalState: universalModalState as unknown as Parameters<typeof useKanbanTransitions>[0]["universalModalState"],
    closeTransition,
  })

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

  const { getDataRequestForCandidate, mutate: mutateDataRequests } = useBulkCandidateDataRequests({
    candidateIds: allCandidateIds,
    vacancyId: ((job?.backendId || job?.id) as string | number | undefined)?.toString(),
    enabled: allCandidateIds.length > 0,
  })

  const candidateLoader = useKanbanCandidateLoader({ job, dynamicStages, setCandidatesData })
  const { isLoadingCandidates, hasMounted, isClient } = candidateLoader.state
  const { setIsLoadingCandidates, setHasMounted, setIsClient } = candidateLoader.actions

  const uiModals = useKanbanUIModals({ job })

  const kanbanFilters = useKanbanFilters({
    talentFunnel, shortLists,
    createShortList: _createSL, addCandidateToShortList: _addToSL, removeCandidateFromShortList: _removeFromSL,
    jobId: _jobIdForSL, jobTitle: job?.title as string | undefined,
  })

  const { saturationData, setSaturationData, findCandidateById, openUnifiedModal, router } = useKanbanDataEffects({
    job, candidatesData, setCandidatesData, isLoadingCandidates, currentJob, allTableCandidates,
    chatScrollRef: uiModals.state.chatScrollRef,
    liaMessages: uiModals.state.liaMessages,
    isLiaLoading: uiModals.state.isLiaLoading,
    setUnifiedModalCandidate: uiModals.actions.setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanDataEffects>[0]["setUnifiedModalCandidate"],
    setUnifiedModalType: uiModals.actions.setUnifiedModalType,
    setUnifiedModalOpen: uiModals.actions.setUnifiedModalOpen,
  })

  const { handleTransitionRequired, handleOpenSpecializedModal } = useKanbanTransitionHandlers({
    openTransition, closeTransition,
    setTransitionInitialPrompt: uiModals.actions.setTransitionInitialPrompt,
    setTransitionAllowStageSelection: uiModals.actions.setTransitionAllowStageSelection,
    setTransitionInterviewAlert: uiModals.actions.setTransitionInterviewAlert,
    setWsiInviteCandidate: uiModals.actions.setWsiInviteCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal: uiModals.actions.setShowWSIInviteModal,
    setUnifiedModalCandidate: uiModals.actions.setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setUnifiedModalCandidate"],
    setUnifiedModalType: uiModals.actions.setUnifiedModalType as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setUnifiedModalType"],
    setUnifiedModalSituation: uiModals.actions.setUnifiedModalSituation,
    setUnifiedModalOpen: uiModals.actions.setUnifiedModalOpen,
    setDataRequestModalCandidate: uiModals.actions.setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal: uiModals.actions.setShowDataRequestModal,
    setDecisionFlowCandidate: uiModals.actions.setDecisionFlowCandidate as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDecisionFlowCandidate"],
    setDecisionFlowType: uiModals.actions.setDecisionFlowType as unknown as Parameters<typeof useKanbanTransitionHandlers>[0]["setDecisionFlowType"],
    setShowDecisionFlowModal: uiModals.actions.setShowDecisionFlowModal,
  })

  const handleDataRequestSubmit = useCallback(async (data: DataRequestSubmitData) => {
    const candidateIds = (data.candidateIds || []).filter(Boolean)
    if (candidateIds.length === 0) {
      toast.error("Solicitação de Dados", { description: "Nenhum candidato selecionado." })
      return
    }

    // channel -> backend notification_channels (BE allow-list: email | whatsapp | voice)
    const notificationChannels =
      data.channel === "both"
        ? ["email", "whatsapp"]
        : data.channel === "voice"
          ? ["voice"]
          : data.channel === "whatsapp"
            ? ["whatsapp"]
            : ["email"]

    // map selected field names -> backend FieldSchema objects (label/type from catalog)
    const fields = (data.fields || []).map((fieldName) => {
      const def = DEFAULT_DATA_FIELDS.find((f) => f.name === fieldName || f.id === fieldName)
      return {
        name: fieldName,
        label: def?.displayName || fieldName,
        field_type: def?.type || "text",
        is_required: def?.required ?? true,
      }
    })

    const vacancyId = ((job?.backendId || job?.id) as string | number | undefined)?.toString()

    const results = await Promise.allSettled(
      candidateIds.map(async (candidateId) => {
        const res = await fetch("/api/backend-proxy/data-requests", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            candidate_id: candidateId,
            vacancy_id: vacancyId,
            fields,
            expiration_days: data.expirationDays,
            send_notification: true,
            notification_channels: notificationChannels,
          }),
        })
        if (!res.ok) {
          const detail = await res.text().catch(() => "")
          throw new Error(detail || `HTTP ${res.status}`)
        }
        return res.json()
      })
    )

    const failed = results.filter((r) => r.status === "rejected").length
    const succeeded = results.length - failed

    if (failed === 0) {
      toast.success("Solicitação Enviada", {
        description:
          succeeded === 1
            ? "Solicitação de dados enviada para 1 candidato."
            : `Solicitação de dados enviada para ${succeeded} candidatos.`,
      })
    } else if (succeeded === 0) {
      toast.error("Falha na Solicitação", {
        description: `Não foi possível enviar a solicitação (${failed} ${failed === 1 ? "falha" : "falhas"}).`,
      })
    } else {
      toast.warning("Solicitação Parcial", {
        description: `${succeeded} enviada(s), ${failed} com falha.`,
      })
    }

    mutateDataRequests()
    uiModals.actions.setShowDataRequestModal(false)
    uiModals.actions.setDataRequestModalCandidate(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: uiModals.actions is a stable object from zustand
  }, [job?.backendId, job?.id, mutateDataRequests])

  const { handleBulkAction, handleBulkActionExecute } = useKanbanBulkActions({
    selectedCandidates: kanbanFilters.selectedCandidates,
    setSelectedCandidates: kanbanFilters.setSelectedCandidates,
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanBulkActions>[0]["allTableCandidates"],
    setBulkActionType: uiModals.actions.setBulkActionType,
    setShowBulkActionModal: uiModals.actions.setShowBulkActionModal,
    setDataRequestModalCandidate: uiModals.actions.setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal: uiModals.actions.setShowDataRequestModal,
    setUnifiedModalType: uiModals.actions.setUnifiedModalType,
    setUnifiedModalCandidate: uiModals.actions.setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setUnifiedModalCandidate"],
    setUnifiedModalOpen: uiModals.actions.setUnifiedModalOpen,
    setWsiInviteCandidate: uiModals.actions.setWsiInviteCandidate as unknown as Parameters<typeof useKanbanBulkActions>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal: uiModals.actions.setShowWSIInviteModal,
    setShowShareGestorModal: uiModals.actions.setShowShareGestorModal,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanBulkActions>[0]["setCandidatesData"],
  })

  const { pendingNavigationRef, processPendingNavigation } = useKanbanNavigation({
    jobId: job?.id?.toString(),
    candidatesData, dynamicStages, openTransition,
    setTransitionInitialPrompt: uiModals.actions.setTransitionInitialPrompt,
    setTransitionAllowStageSelection: uiModals.actions.setTransitionAllowStageSelection,
    setLiaPromptValue: uiModals.actions.setLiaPromptValue,
    setPreviewCandidate: uiModals.actions.setPreviewCandidate,
    setIsPreviewOpen: uiModals.actions.setIsPreviewOpen,
    setUnifiedModalCandidate: uiModals.actions.setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanNavigation>[0]["setUnifiedModalCandidate"],
    setUnifiedModalType: uiModals.actions.setUnifiedModalType as unknown as Parameters<typeof useKanbanNavigation>[0]["setUnifiedModalType"],
    setUnifiedModalOpen: uiModals.actions.setUnifiedModalOpen,
  })

  const tableView = useKanbanTableView({ dynamicStages, candidatesData, viewMode })

  const getFilteredAndSortedCandidates = () => tableView.actions.getFilteredAndSortedCandidates(kanbanFilters.searchQuery)
  const getPaginatedCandidates = () => tableView.actions.getPaginatedCandidates(kanbanFilters.searchQuery)

  const [showJobEditor, setShowJobEditor] = useState(false)
  const [editingSection, setEditingSection] = useState<string | null>(null)
  const [savingJobSection, setSavingJobSection] = useState<string | null>(null)

  const { handleLiaUiAction, handleAICommand, handleOrchestratedMessage } = useKanbanLIAHandlers({
    liaMessages: uiModals.state.liaMessages,
    setLiaMessages: uiModals.actions.setLiaMessages as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setLiaMessages"],
    setLiaPromptValue: uiModals.actions.setLiaPromptValue,
    setIsLiaLoading: uiModals.actions.setIsLiaLoading,
    liaConversationId: uiModals.state.liaConversationId,
    setLiaConversationId: uiModals.actions.setLiaConversationId,
    currentJob,
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["allTableCandidates"],
    selectedCandidates: kanbanFilters.selectedCandidates,
    candidatesData: candidatesData as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["candidatesData"],
    user: user as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["user"],
    findCandidateById: findCandidateById as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["findCandidateById"],
    openUnifiedModal: openUnifiedModal as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["openUnifiedModal"],
    openTransition,
    setWsiCandidate: uiModals.actions.setWsiCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setWsiCandidate"],
    setShowWSIModal: uiModals.actions.setShowWSIModal,
    setWsiInviteCandidate: uiModals.actions.setWsiInviteCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal: uiModals.actions.setShowWSIInviteModal,
    setDataRequestModalCandidate: uiModals.actions.setDataRequestModalCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setDataRequestModalCandidate"],
    setShowDataRequestModal: uiModals.actions.setShowDataRequestModal,
    setRubricCandidate: uiModals.actions.setRubricCandidate as unknown as Parameters<typeof useKanbanLIAHandlers>[0]["setRubricCandidate"],
    setShowRubricModal: uiModals.actions.setShowRubricModal,
  })

  const { computedSuggestions, hasShownProactiveSuggestion, lastBriefingJobId } = useKanbanLIASuggestions({
    dynamicStages: dynamicStages as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["dynamicStages"],
    candidatesData: candidatesData as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["candidatesData"],
    allTableCandidates: allTableCandidates as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["allTableCandidates"],
    currentJob,
    liaMessages: uiModals.state.liaMessages,
    companyId: _companyIdForSL ?? '',
    setLiaMessages: uiModals.actions.setLiaMessages as unknown as Parameters<typeof useKanbanLIASuggestions>[0]["setLiaMessages"],
  })

  const dragDrop = useKanbanDragDrop({
    draggedCandidate: draggedCandidate as unknown as Parameters<typeof useKanbanDragDrop>[0]["draggedCandidate"],
    setDraggedCandidate: setDraggedCandidate as unknown as Parameters<typeof useKanbanDragDrop>[0]["setDraggedCandidate"],
    dragOverColumn, setDragOverColumn, dynamicStages, openTransition,
    pendingMove: uiModals.state.pendingMove as unknown as Parameters<typeof useKanbanDragDrop>[0]["pendingMove"],
    setPendingMove: uiModals.actions.setPendingMove as unknown as Parameters<typeof useKanbanDragDrop>[0]["setPendingMove"],
    statusModalOpen: uiModals.state.statusModalOpen,
    setStatusModalOpen: uiModals.actions.setStatusModalOpen,
    selectedSubStatus: uiModals.state.selectedSubStatus,
    setSelectedSubStatus: uiModals.actions.setSelectedSubStatus,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanDragDrop>[0]["setCandidatesData"],
    job: job as unknown as Parameters<typeof useKanbanDragDrop>[0]["job"],
  })

  const candidateHandlers = useKanbanCandidateHandlers({
    setPreviewCandidate: uiModals.actions.setPreviewCandidate,
    setIsPreviewOpen: uiModals.actions.setIsPreviewOpen,
    setShowCandidatePage: uiModals.actions.setShowCandidatePage,
    isPreviewMaximized: uiModals.state.isPreviewMaximized,
    setIsPreviewMaximized: uiModals.actions.setIsPreviewMaximized,
    previewCandidate: uiModals.state.previewCandidate,
    setViewedCandidateIds: uiModals.actions.setViewedCandidateIds,
    openUnifiedModal,
    setUnifiedModalOpen: uiModals.actions.setUnifiedModalOpen,
    setUnifiedModalCandidate: uiModals.actions.setUnifiedModalCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setUnifiedModalCandidate"],
    setUnifiedModalSituation: uiModals.actions.setUnifiedModalSituation,
    setUnifiedModalType: uiModals.actions.setUnifiedModalType as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setUnifiedModalType"],
    setWsiCandidate: uiModals.actions.setWsiCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setWsiCandidate"],
    setShowWSIModal: uiModals.actions.setShowWSIModal,
    setCandidateForVacancy: uiModals.actions.setCandidateForVacancy as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setCandidateForVacancy"],
    setShowAddToVacancyModal: uiModals.actions.setShowAddToVacancyModal,
    setWsiInviteCandidate: uiModals.actions.setWsiInviteCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setWsiInviteCandidate"],
    setShowWSIInviteModal: uiModals.actions.setShowWSIInviteModal,
    setIsTriagemOpen: uiModals.actions.setIsTriagemOpen,
    setTriagemCandidate: uiModals.actions.setTriagemCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setTriagemCandidate"],
    setShowRubricModal: uiModals.actions.setShowRubricModal,
    setRubricCandidate: uiModals.actions.setRubricCandidate as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setRubricCandidate"],
    setRubricEvaluationData: uiModals.actions.setRubricEvaluationData as unknown as Parameters<typeof useKanbanCandidateHandlers>[0]["setRubricEvaluationData"],
    setShowReport: uiModals.actions.setShowReport,
    setCandidatesData, candidatesData,
    jobDataId: currentJob?.id as string | number | undefined,
    openTransition,
  })

  const decisions = useKanbanCandidateDecisions({
    toast, job: job as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["job"],
    dynamicStages,
    setCandidatesData: setCandidatesData as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setCandidatesData"],
    setShowDecisionFlowModal: uiModals.actions.setShowDecisionFlowModal,
    setDecisionFlowCandidate: uiModals.actions.setDecisionFlowCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setDecisionFlowCandidate"],
    decisionFlowCandidate: uiModals.state.decisionFlowCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["decisionFlowCandidate"],
    openTransition,
    setTransitionInitialPrompt: uiModals.actions.setTransitionInitialPrompt,
    onCloseTriagem: candidateHandlers.handleCloseTriagem,
    setRubricCandidate: uiModals.actions.setRubricCandidate as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setRubricCandidate"],
    setShowRubricModal: uiModals.actions.setShowRubricModal,
    setRubricEvaluationData: uiModals.actions.setRubricEvaluationData as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setRubricEvaluationData"],
    setDecisionFlowType: uiModals.actions.setDecisionFlowType as unknown as Parameters<typeof useKanbanCandidateDecisions>[0]["setDecisionFlowType"],
    setShowCloseVacancyModal: uiModals.actions.setShowCloseVacancyModal,
  })

  const handleOpenTriagem = useCallback((candidate: Record<string, unknown>) => {
    uiModals.actions.setTriagemCandidate(candidate)
    uiModals.actions.setIsTriagemOpen(true)
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: uiModals.actions is stable from zustand store
  }, [])

  const handleOpenScoreModal = (candidate: Record<string, unknown>, modalType: 'geral' | 'triagem' | 'cv' | 'tecnico' | 'ingles' | 'b5') => {
    uiModals.actions.setScoreModalCandidate(candidate)
    switch (modalType) {
      case 'geral': uiModals.actions.setShowGeneralScoreModal(true); break
      case 'triagem': handleOpenTriagem(candidate); break
      case 'cv': decisions.handleOpenAnalysis(candidate as unknown as Parameters<typeof decisions.handleOpenAnalysis>[0]); break
      case 'tecnico': uiModals.actions.setShowTechnicalTestModal(true); break
      case 'ingles': uiModals.actions.setShowEnglishTestModal(true); break
      case 'b5': uiModals.actions.setShowBigFiveModal(true); break
    }
  }

  const jobEditing = useKanbanJobEditing({
    currentJob: currentJob as unknown as Parameters<typeof useKanbanJobEditing>[0]["currentJob"],
    jobEditForm, setSavingJobSection, setEditingSection,
    setDynamicStages: setDynamicStages as unknown as Parameters<typeof useKanbanJobEditing>[0]["setDynamicStages"],
    setCandidatesData,
    mapInterviewStagesToKanban: mapInterviewStagesToKanban as unknown as Parameters<typeof useKanbanJobEditing>[0]["mapInterviewStagesToKanban"],
    createInitialCandidatesData: createInitialCandidatesData as unknown as Parameters<typeof useKanbanJobEditing>[0]["createInitialCandidatesData"],
  })

  const { getColumnStyle, getStageAccentStyle, getStageCategory, getStageDisplayName, STAGE_PASTEL_COLORS } = useKanbanColumnConfig({ dynamicStages })

  return {
    ...uiModals.state,
    ...uiModals.actions,
    ...kanbanFilters,
    ...tableView.state,
    ...tableView.actions,
    ...candidateHandlers,
    ...dragDrop,
    ...decisions,
    ...jobEditing,
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
    jobLocalOverrides, setJobLocalOverrides,
    showJobEditor, setShowJobEditor,
    editingSection, setEditingSection,
    savingJobSection, setSavingJobSection,
    router, toast, user, saveJobsState,
    talentFunnel, _companyIdForSL, _jobIdForSL,
    shortLists, _createSL, _addToSL, _removeFromSL,
    proactiveInsights, dismissInsight,
    aiSuggestions, approveSuggestion, rejectSuggestion,
    pipelineInheritance,
    returnEvents, getAlertForCandidate, computeAlerts, hasAlerts,
    companyDefaults,
    allTableCandidates, allCandidateIds,
    handleBulkAction, handleBulkActionExecute,
    handleLiaUiAction, handleAICommand, handleOrchestratedMessage,
    computedSuggestions,
    universalModalState, openTransition, closeTransition,
    findCandidateById, openUnifiedModal,
    handlePublishJob,
    hasShownProactiveSuggestion, lastBriefingJobId,
    handleOpenTriagem,
    handleTransitionRequired,
    handleUniversalTransitionConfirm,
    handleOpenSpecializedModal,
    handleDataRequestSubmit,
    getDataRequestForCandidate,
    handleDataRequestResend: (_candidateId: string) => {},
    handleDataRequestViewDetails: (_candidateId: string) => {},
    handleOpenScoreModal,
    currentJob,
    jobData: currentJob,
    getFilteredAndSortedCandidates,
    getPaginatedCandidates,
    calculateNotaLiaGeral,
    getColumnStyle, getStageAccentStyle, getStageCategory, getStageDisplayName, STAGE_PASTEL_COLORS,
  }
}

export type KanbanPageCoreState = ReturnType<typeof useKanbanPageCore>
