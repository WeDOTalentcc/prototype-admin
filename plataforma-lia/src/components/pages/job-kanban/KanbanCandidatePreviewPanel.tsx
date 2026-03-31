"use client"

import React from "react"

const CandidatePreviewDynamic = React.lazy(() =>
  import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview }))
)

interface KanbanCandidatePreviewPanelProps {
  isPreviewOpen: boolean
  previewCandidate: Record<string, unknown> | null | undefined
  isPreviewMaximized: boolean
  onClosePreview: () => void
  onTogglePreviewMaximize: () => void
  onNavigateCandidate: (index: number) => void
  onCandidatePageOpen: (candidate: Record<string, unknown>) => void
  onScheduleInterview: (candidate: Record<string, unknown>) => void
  onAddToVacancy: (candidate: Record<string, unknown>) => void
  onToggleFavorite: (candidate: Record<string, unknown>) => void
  favoriteCandidates: Set<string>
  onSendWSIInvite: (candidate: Record<string, unknown>) => void
  onSendEmail: (candidate: Record<string, unknown>) => void
  onSendWhatsApp: (candidate: Record<string, unknown>) => void
  onSendTriagem: (candidate: Record<string, unknown>) => void
  onSendAgendamento: (candidate: Record<string, unknown>) => void
  onSendFeedback: (candidate: Record<string, unknown>) => void
  onOpenTriagem: (candidate: Record<string, unknown>) => void
  candidatesData: Record<string, Record<string, unknown>[]>
  jobVacancyId?: string
}

export function KanbanCandidatePreviewPanel({
  isPreviewOpen,
  previewCandidate,
  isPreviewMaximized,
  onClosePreview,
  onTogglePreviewMaximize,
  onNavigateCandidate,
  onCandidatePageOpen,
  onScheduleInterview,
  onAddToVacancy,
  onToggleFavorite,
  favoriteCandidates,
  onSendWSIInvite,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  onOpenTriagem,
  candidatesData,
  jobVacancyId,
}: KanbanCandidatePreviewPanelProps) {
  if (!isPreviewOpen || !previewCandidate) {
    return null
  }

  const currentColumn = Object.keys(candidatesData).find(col =>
    candidatesData[col].some((c) => c.id === previewCandidate?.id)
  )
  const columnCandidates = currentColumn ? candidatesData[currentColumn] : []
  const currentIndex = currentColumn
    ? candidatesData[currentColumn].findIndex((c) => c.id === previewCandidate?.id)
    : 0

  return (
    <div className={}>
      <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
        <React.Suspense fallback={null}>
          <CandidatePreviewDynamic
            candidate={previewCandidate as never}
            isOpen={isPreviewOpen}
            onClose={onClosePreview}
            isMaximized={isPreviewMaximized}
            onToggleMaximize={onTogglePreviewMaximize}
            candidates={columnCandidates as never}
            currentIndex={currentIndex}
            onNavigateCandidate={onNavigateCandidate as never}
            onOpenFullPage={onCandidatePageOpen as never}
            onScheduleInterview={onScheduleInterview as never}
            onAddToVacancy={onAddToVacancy as never}
            onToggleFavorite={onToggleFavorite as never}
            onWSIScreening={onSendWSIInvite as never}
            onOpenTriagemDetails={onOpenTriagem as never}
            isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id as string) : false}
            onSendEmail={(candidate) => onSendEmail(candidate as never)}
            onSendWhatsApp={(candidate) => onSendWhatsApp(candidate as never)}
            onSendTriagem={(candidate) => onSendTriagem(candidate as never)}
            onSendAgendamento={(candidate) => onSendAgendamento(candidate as never)}
            onSendFeedback={(candidate) => onSendFeedback(candidate as never)}
            jobId={jobVacancyId}
          />
        </React.Suspense>
      </div>
    </div>
  )
}
