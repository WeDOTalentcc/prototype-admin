"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/auth-context"
import { useKanbanStore } from "@/stores/kanban-store"
import { useShortList } from "@/hooks/candidates/use-short-list"
import { useProactiveInsights } from "@/hooks/ai/use-proactive-insights"
import { useNavigationPersistence } from "@/hooks/shared/use-navigation-persistence"
import { useTalentFunnel } from "@/hooks/candidates/use-talent-funnel"
import { useCandidateSuggestions } from "@/hooks/ai/useCandidateSuggestions"
import { useUniversalTransition } from "@/components/kanban"
import { usePipelineInheritance } from "@/hooks/recruitment/use-pipeline-inheritance"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { enrichStagesWithSubStatuses, buildSubStatusMap, applyVacancyStageOverrides } from "@/components/kanban/utils/stage-utils"
import { useReturnEvents } from "@/hooks/recruitment/use-return-events"
import { useBulkCandidateDataRequests } from "@/hooks/candidates/use-candidate-data-requests"
import {
  mapInterviewStagesToKanban,
  createInitialCandidatesData,
} from "@/components/pages/job-kanban/utils/kanbanStageUtils"
import { type DynamicStage } from "@/components/kanban"
import { useKanbanCandidateLoader } from "@/components/pages/job-kanban/hooks/useKanbanCandidateLoader"

export function useKanbanPageSetup({ job }: { job?: Record<string, unknown> }) {
  const router = useRouter()
  const { saveJobsState } = useNavigationPersistence()
  const { user } = useAuth()
  const talentFunnel = useTalentFunnel()
  const _companyIdForSL = ((user as Record<string, unknown>)?.company as string) || "demo"
  const _jobIdForSL = job?.id?.toString()
  const { shortLists, createShortList: _createSL, addCandidate: _addToSL, removeCandidate: _removeFromSL } = useShortList(_companyIdForSL, _jobIdForSL)
  const { insights: proactiveInsights, dismiss: dismissInsight } = useProactiveInsights(_jobIdForSL, _companyIdForSL)

  const {
    suggestions: aiSuggestions,
    approveSuggestion,
    rejectSuggestion,
  } = useCandidateSuggestions(job?.id?.toString() || "")

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
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: pipelineInheritance object excluded to avoid re-runs
  }, [job?.id])

  const viewMode = useKanbanStore((s) => s.viewMode)
  const setViewMode = useKanbanStore((s) => s.setViewMode)
  const [saturationData, setSaturationData] = useState<{ is_saturated: boolean; approved_count: number; saturation_threshold: number; saturation_percentage: number } | null>(null)

  const saturationJobId = job?.backendId || job?.id
  useEffect(() => {
    if (!saturationJobId) return
    fetch(`/api/backend-proxy/job-vacancies/${saturationJobId}/saturation-status/`)
      .then(res => res.ok ? res.json() : null)
      .then(data => { if (data) setSaturationData(data) })
      .catch((err) => { console.error('[useKanbanPageSetup] saturation-status fetch failed', err) })
  }, [saturationJobId])

  const activeTab = useKanbanStore((s) => s.activeTab)
  const setActiveTab = useKanbanStore((s) => s.setActiveTab)
  const selectedCandidate = useKanbanStore((s) => s.selectedCandidate)
  const setSelectedCandidate = useKanbanStore((s) => s.setSelectedCandidate)
  const [selectedTriagemCandidate, setSelectedTriagemCandidate] = useState<Record<string, unknown> | null>(null)
  const showExpandedMetrics = useKanbanStore((s) => s.showExpandedMetrics)
  const setShowExpandedMetrics = useKanbanStore((s) => s.setShowExpandedMetrics)

  useEffect(() => {
    if (job?.id) {
      saveJobsState(String(job.id), viewMode, activeTab)
    }
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
            name: ss.name,
            display_name: ss.display_name,
            is_default: ss.is_default,
            is_waiting: ss.is_waiting,
            waiting_for: ss.waiting_for,
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

  const { modalState: universalModalState, openTransition, closeTransition } = useUniversalTransition(dynamicStages)

  const candidatesData = useKanbanStore((s) => s.candidatesData)
  const setCandidatesData = useKanbanStore((s) => s.setCandidatesData)
  const resetKanbanStore = useKanbanStore((s) => s.resetStore)
  const jobId = job?.id
  const jobStagesJson = JSON.stringify(job?.interviewStages ?? [])
  useEffect(() => {
    const initial = createInitialCandidatesData(mapInterviewStagesToKanban(job?.interviewStages as Parameters<typeof mapInterviewStagesToKanban>[0]))
    setCandidatesData(initial)
    useKanbanStore.getState().clearSelection()
    useKanbanStore.getState().setSearchQuery("")
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: jobStagesJson covers interviewStages; setCandidatesData is stable
  }, [jobId, jobStagesJson])
  useEffect(() => {
    return () => { resetKanbanStore() }
  // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: run only on unmount
  }, [])

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
    mutate: mutateDataRequests,
  } = useBulkCandidateDataRequests({
    candidateIds: allCandidateIds,
    vacancyId: ((job?.backendId || job?.id) as string | number | undefined)?.toString(),
    enabled: allCandidateIds.length > 0,
  })

  const candidateLoader = useKanbanCandidateLoader({ job, dynamicStages, setCandidatesData })
  const { isLoadingCandidates, hasMounted, isClient } = candidateLoader.state
  const { setIsLoadingCandidates, setHasMounted, setIsClient } = candidateLoader.actions

  return {
    router, user, saveJobsState,
    talentFunnel, shortLists, _createSL, _addToSL, _removeFromSL,
    _companyIdForSL, _jobIdForSL,
    proactiveInsights, dismissInsight,
    aiSuggestions, approveSuggestion, rejectSuggestion,
    pipelineInheritance,
    returnEvents, getAlertForCandidate, computeAlerts, hasAlerts,
    viewMode, setViewMode,
    saturationData, setSaturationData,
    activeTab, setActiveTab,
    selectedCandidate, setSelectedCandidate,
    selectedTriagemCandidate, setSelectedTriagemCandidate,
    showExpandedMetrics, setShowExpandedMetrics,
    dynamicStages, setDynamicStages,
    showAddColumnPopover, setShowAddColumnPopover,
    newColumnName, setNewColumnName,
    inferredBehavior, setInferredBehavior,
    isAddingColumn, setIsAddingColumn,
    universalModalState, openTransition, closeTransition,
    candidatesData, setCandidatesData,
    draggedCandidate, setDraggedCandidate,
    dragOverColumn, setDragOverColumn,
    allTableCandidates, allCandidateIds,
    getDataRequestForCandidate, mutateDataRequests,
    isLoadingCandidates, hasMounted, isClient,
    setIsLoadingCandidates, setHasMounted, setIsClient,
  }
}

export type KanbanPageSetupState = ReturnType<typeof useKanbanPageSetup>
