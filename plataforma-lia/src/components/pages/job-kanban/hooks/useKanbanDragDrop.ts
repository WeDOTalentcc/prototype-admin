"use client"

import { type KanbanCandidate } from "@/components/kanban"
import { SUB_STATUSES, type SubStatus } from "@/lib/recruitment-stages"

export interface KanbanDragDropContext {
  draggedCandidate: any | null
  setDraggedCandidate: (candidate: any | null) => void
  dragOverColumn: string | null
  setDragOverColumn: (column: string | null) => void
  dynamicStages: any[]
  openTransition: (candidates: KanbanCandidate[], fromStage: string, toStage: string) => void
  // confirmMove state
  pendingMove: { candidate: any; fromColumn: string; toColumn: string } | null
  setPendingMove: (move: { candidate: any; fromColumn: string; toColumn: string } | null) => void
  statusModalOpen: boolean
  setStatusModalOpen: (open: boolean) => void
  selectedSubStatus: string
  setSelectedSubStatus: (status: string) => void
  setCandidatesData: (updater: (prev: Record<string, any[]>) => Record<string, any[]>) => void
  job: any
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

  const handleDragStart = (e: React.DragEvent, candidate: any, fromColumn: string) => {
    setDraggedCandidate({ ...candidate, fromColumn })
    e.dataTransfer.effectAllowed = 'move'
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
    const stage = dynamicStages.find(s => s.id === toColumn)
    if (stage?.subStatuses?.length) {
      return stage.subStatuses.map((ss: any) => ({
        name: ss.name,
        displayName: ss.display_name,
        isDefault: ss.is_default,
        isWaiting: ss.is_waiting,
      }))
    }
    return SUB_STATUSES[toColumn] || []
  }

  const getSubStatusColor = (status: SubStatus): { bg: string; text: string } => {
    if (status.isApproval) return { bg: 'bg-status-success/15 dark:bg-status-success/30', text: 'text-status-success dark:text-status-success' }
    if (status.isRejection) return { bg: 'bg-status-error/15 dark:bg-status-error/30', text: 'text-status-error dark:text-status-error' }
    if (status.isWaiting) return { bg: 'bg-status-warning/15 dark:bg-status-warning/30', text: 'text-status-warning dark:text-status-warning' }
    return { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-700 dark:text-gray-300' }
  }

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

  const confirmMove = async () => {
    if (!pendingMove) return

    const { candidate, fromColumn, toColumn } = pendingMove
    const candidateId = candidate.id

    setCandidatesData(prev => {
      const newData = { ...prev }

      const fromKey = fromColumn as keyof typeof newData
      if (newData[fromKey]) {
        ;(newData[fromKey] as any[]) = (newData[fromKey] as any[]).filter((c: any) => c.id !== candidateId)
      }

      const toKey = toColumn as keyof typeof newData
      const candidateToMove = { ...candidate }
      delete candidateToMove.fromColumn

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
