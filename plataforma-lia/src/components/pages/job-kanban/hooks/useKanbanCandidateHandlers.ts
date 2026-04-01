"use client"

import { useCallback } from "react"
import { type KanbanCandidate } from "@/components/kanban"
import { type CommunicationType } from "@/components/modals/unified-communication-modal"

interface UseKanbanCandidateHandlersProps {
  // Preview / page state
  setPreviewCandidate: (c: Record<string, unknown> | null) => void
  setIsPreviewOpen: (v: boolean) => void
  setShowCandidatePage: (v: boolean) => void
  isPreviewMaximized: boolean
  setIsPreviewMaximized: (v: boolean) => void
  previewCandidate: Record<string, unknown> | null
  setViewedCandidateIds: React.Dispatch<React.SetStateAction<Set<string>>>
  // Unified modal
  openUnifiedModal: (candidate: Record<string, unknown>, type: CommunicationType) => void
  setUnifiedModalOpen: (v: boolean) => void
  setUnifiedModalCandidate: (c: unknown) => void
  setUnifiedModalSituation: (s: string | undefined) => void
  setUnifiedModalType: (t: string) => void
  // WSI / Vacancy modals
  setWsiCandidate: (c: unknown) => void
  setShowWSIModal: (v: boolean) => void
  setCandidateForVacancy: (c: unknown) => void
  setShowAddToVacancyModal: (v: boolean) => void
  setWsiInviteCandidate: (c: unknown) => void
  setShowWSIInviteModal: (v: boolean) => void
  // Triagem / Rubric
  setIsTriagemOpen: (v: boolean) => void
  setTriagemCandidate: (c: unknown) => void
  setShowRubricModal: (v: boolean) => void
  setRubricCandidate: (c: unknown) => void
  setRubricEvaluationData: (d: unknown) => void
  setShowReport: (v: boolean) => void
  // Sub-status / candidates data
  setCandidatesData: React.Dispatch<React.SetStateAction<Record<string, Record<string, unknown>[]>>>
  candidatesData: Record<string, Record<string, unknown>[]>
  jobDataId?: string | number
  // Transition
  openTransition: (candidates: KanbanCandidate[], from: string, to: string) => void
}

export function useKanbanCandidateHandlers({
  setPreviewCandidate,
  setIsPreviewOpen,
  setShowCandidatePage,
  isPreviewMaximized,
  setIsPreviewMaximized,
  previewCandidate,
  setViewedCandidateIds,
  openUnifiedModal,
  setUnifiedModalOpen,
  setUnifiedModalCandidate,
  setUnifiedModalSituation,
  setUnifiedModalType,
  setWsiCandidate,
  setShowWSIModal,
  setCandidateForVacancy,
  setShowAddToVacancyModal,
  setWsiInviteCandidate,
  setShowWSIInviteModal,
  setIsTriagemOpen,
  setTriagemCandidate,
  setShowRubricModal,
  setRubricCandidate,
  setRubricEvaluationData,
  setShowReport,
  setCandidatesData,
  candidatesData,
  jobDataId,
  openTransition,
}: UseKanbanCandidateHandlersProps) {

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

  const handleOpenPreview = (candidate: Record<string, unknown>) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(true)
    if (candidate?.id) {
      markCandidateAsViewed(candidate.id as string)
    }
  }

  const handleClosePreview = () => {
    setIsPreviewOpen(false)
    setPreviewCandidate(null)
  }

  const handleCandidatePageOpen = (candidate: Record<string, unknown>) => {
    setPreviewCandidate(candidate)
    setIsPreviewOpen(false)
    setShowCandidatePage(true)
  }

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
          job_vacancy_id: jobVacancyId || jobDataId?.toString()
        })
      })

      if (!response.ok) {
        return false
      }

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

  const handleShowReport = () => {
    setShowReport(true)
  }

  const handleCloseReport = () => {
    setShowReport(false)
  }

  return {
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
  }
}
