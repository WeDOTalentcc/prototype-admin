"use client"

import type React from "react"
import { type KanbanCandidate, type DynamicStage } from "@/components/kanban"
// WT-2022 P0.SUB_STATUSES: hook canonical-first via useRecruitmentStages.
// SUB_STATUSES hardcoded mantido apenas como transitional fallback quando
// backend nao retorna sub_statuses pro stage (boot/timeout/stage custom novo).
import { SUB_STATUSES, type SubStatus } from "@/lib/recruitment-stages"
import { useRecruitmentStages } from "@/hooks/recruitment/use-recruitment-stages"
import { type KanbanJob } from "@/components/pages/job-kanban/types"
import { type SubStatusOption } from "@/components/settings/recruitment-journey.types"

interface DraggedCandidate extends KanbanCandidate {
  fromColumn: string
}

export interface KanbanDragDropContext {
  draggedCandidate: DraggedCandidate | null
  setDraggedCandidate: (candidate: DraggedCandidate | null) => void
  dragOverColumn: string | null
  setDragOverColumn: (column: string | null) => void
  dynamicStages: DynamicStage[]
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  // confirmMove state
  pendingMove: { candidate: KanbanCandidate; fromColumn: string; toColumn: string } | null
  setPendingMove: (move: { candidate: KanbanCandidate; fromColumn: string; toColumn: string } | null) => void
  statusModalOpen: boolean
  setStatusModalOpen: (open: boolean) => void
  selectedSubStatus: string
  setSelectedSubStatus: (status: string) => void
  setCandidatesData: (updater: (prev: Record<string, KanbanCandidate[]>) => Record<string, KanbanCandidate[]>) => void
  job: KanbanJob | null
}

export function useKanbanDragDrop(ctx: KanbanDragDropContext) {
  const {
    draggedCandidate,
    setDraggedCandidate,
    setDragOverColumn,
    dynamicStages,
    openTransition,
    pendingMove,
    setPendingMove,
    setStatusModalOpen,
    selectedSubStatus,
    setSelectedSubStatus,
    setCandidatesData,
    job,
  } = ctx

  // WT-2022 P0.SUB_STATUSES: hook canonical no topo (Rules of Hooks).
  // legacySubStatuses reflete sub-statuses customizados em Configuracoes >
  // Pipeline (snake_case backend convertido pro shape legacy camelCase).
  const { legacySubStatuses } = useRecruitmentStages()

  const handleDragStart = (e: React.DragEvent<Element>, candidate: KanbanCandidate, fromColumn: string) => {
    setDraggedCandidate({ ...candidate, fromColumn })
    if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragEnd = (_e: React.DragEvent<Element>) => {
    setDraggedCandidate(null)
    setDragOverColumn(null)
  }

  const handleDragOver = (e: React.DragEvent<Element>, column: string) => {
    e.preventDefault()
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
    setDragOverColumn(column)
  }

  const handleDragLeave = () => {
    setDragOverColumn(null)
  }

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

  const getAvailableSubStatuses = (toColumn: string): SubStatus[] => {
    // Prioridade 1: sub_statuses embedded em dynamicStages (vem do mesmo hook
    // canonical company-pipeline via parent). Cobre stages customizados.
    const stage = dynamicStages.find(s => s.id === toColumn)
    if (stage?.subStatuses?.length) {
      return stage.subStatuses.map((ss: SubStatusOption) => ({
        name: ss.name,
        displayName: ss.display_name,
        isDefault: ss.is_default,
        isWaiting: ss.is_waiting,
      }))
    }
    // Prioridade 2: legacySubStatuses do hook canonical (reflete Configuracoes
    // > Pipeline). Stage names canonical batem com toColumn aqui.
    const canonical = legacySubStatuses[toColumn]
    if (canonical?.length) return canonical
    // Prioridade 3 (fallback transitional): SUB_STATUSES hardcoded — so dispara
    // se backend nao tem sub_statuses pro stage (boot/timeout/stage novo).
    return SUB_STATUSES[toColumn] || []
  }

  const getSubStatusColor = (status: SubStatus): { bg: string; text: string } => {
    if (status.isApproval) return { bg: 'bg-status-success/15 dark:bg-status-success/30', text: 'text-status-success dark:text-status-success' }
    if (status.isRejection) return { bg: 'bg-status-error/15 dark:bg-status-error/30', text: 'text-status-error dark:text-status-error' }
    if (status.isWaiting) return { bg: 'bg-status-warning/15 dark:bg-status-warning/30', text: 'text-status-warning dark:text-status-warning' }
    return { bg: 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary', text: 'text-lia-text-secondary' }
  }

  const stagesRequiringConfirmation = ['hired', 'rejected', 'offer_declined']

  const handleDrop = async (e: React.DragEvent<Element>, toColumn: string) => {
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

    // PR-B Trigger B: drag to "offer" column → open OfferReviewModal first.
    // Optimistically moves candidate to offer column so the kanban reflects
    // recruiter intent; OfferReviewModal handles offer review and send.
    // Skips UniversalTransitionModal — offer flow is self-contained in
    // OfferReviewModal (auto or manual send).
    if (validTargetColumn === "offer") {
      setCandidatesData(prev => {
        const next = { ...prev }
        for (const col of Object.keys(next)) {
          next[col] = (next[col] as KanbanCandidate[]).filter(c => c.id !== kanbanCandidate.id)
        }
        next["offer"] = [...(next["offer"] ?? []), { ...kanbanCandidate, stage: "offer" }]
        return next as Record<string, KanbanCandidate[]>
      })
      window.dispatchEvent(
        new CustomEvent("lia:open_offer_review", {
          detail: { candidate_id: kanbanCandidate.id, job_id: (job as { backendId?: string })?.backendId ?? job?.id ?? "" },
        }),
      )
      setDragOverColumn(null)
      setDraggedCandidate(null)
      return
    }

    openTransition([kanbanCandidate], fromColumn, validTargetColumn)
    setDragOverColumn(null)
    setDraggedCandidate(null)
  }

  const confirmMove = async () => {
    if (!pendingMove) return

    const { candidate, fromColumn, toColumn } = pendingMove
    const candidateId = candidate.id

    setCandidatesData(prev => {
      const newData = { ...prev }

      const fromKey = fromColumn as keyof typeof newData
      if (newData[fromKey]) {
        newData[fromKey] = newData[fromKey].filter((c: KanbanCandidate) => c.id !== candidateId)
      }

      const toKey = toColumn as keyof typeof newData
      const candidateToMove = { ...candidate }

      candidateToMove.stage = toColumn
      candidateToMove.sub_status = selectedSubStatus

      if (toColumn === 'sourcing') candidateToMove.needsAction = true
      else if (toColumn === 'screening') candidateToMove.needsAction = false
      else if (toColumn.startsWith('interview') || toColumn.includes('entrevista')) candidateToMove.needsAction = false
      else if (toColumn === 'hired' || toColumn === 'rejected' || toColumn === 'offer_declined') candidateToMove.needsAction = false

      if (toColumn === 'hired') candidateToMove.status = 'contratado'
      else if (toColumn === 'rejected') candidateToMove.status = 'reprovado'
      else if (toColumn === 'offer_declined') candidateToMove.status = 'proposta_recusada'
      else if (toColumn === 'offer') candidateToMove.status = 'proposta'

      if (!newData[toKey]) {
        newData[toKey] = []
      }
      newData[toKey] = [...newData[toKey], candidateToMove]

      return newData
    })

    setStatusModalOpen(false)
    setPendingMove(null)
    setSelectedSubStatus('')

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
        await response.json().catch(() => ({}))
      }
    } catch (error) {
      // Network error — state already updated optimistically
    }
  }

  const cancelMove = () => {
    setStatusModalOpen(false)
    setPendingMove(null)
    setSelectedSubStatus('')
  }

  return {
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
  }
}
