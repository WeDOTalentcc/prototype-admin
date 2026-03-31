"use client"

import React from "react"

const CandidatePreviewDynamic = React.lazy(() =>
  import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview }))

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
  if (!isPreviewOpen || !previewCandidate) return null

  const currentColumn = Object.keys(candidatesData).find(col =>
    candidatesData[col].some((c) => c.id === previewCandidate?.id)
  )
  const columnCandidates = currentColumn ? candidatesData[currentColumn] : []
  const currentIndex = currentColumn
    ? candidatesData[currentColumn].findIndex((c) => c.id === previewCandidate?.id)
    : 0

{isPreviewOpen && previewCandidate && (
  <div className={`flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 ${isPreviewMaximized ? 'w-[600px]' : 'w-panel-lg'}`}>
    <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
    <React.Suspense fallback={null}>
      <CandidatePreviewDynamic
        candidate={previewCandidate}
        isOpen={isPreviewOpen}
        onClose={onClosePreview}
        isMaximized={isPreviewMaximized}
        onToggleMaximize={onTogglePreviewMaximize}
        candidates={(() => {
          const currentColumn = Object.keys(candidatesData).find(col =>
            candidatesData[col].some((c) => c.id === previewCandidate?.id)
          )
          return currentColumn ? candidatesData[currentColumn] : []
        })()}
        currentIndex={(() => {
          const currentColumn = Object.keys(candidatesData).find(col =>
            candidatesData[col].some((c) => c.id === previewCandidate?.id)
          )
          return currentColumn ? candidatesData[currentColumn].findIndex((c) => c.id === previewCandidate?.id) : 0
        })()}
        onNavigateCandidate={onNavigateCandidate as unknown as never}
        onOpenFullPage={onCandidatePageOpen as unknown as never}
        onScheduleInterview={onScheduleInterview as unknown as never}
        onAddToVacancy={onAddToVacancy as unknown as never}
        onToggleFavorite={onToggleFavorite as unknown as never}
        onWSIScreening={onSendWSIInvite as unknown as never}
        onOpenTriagemDetails={onOpenTriagem as unknown as never}
        isFavorite={previewCandidate ? favoriteCandidates.has(previewCandidate.id as string) : false}
        onSendEmail={(candidate) => onSendEmail(candidate as unknown as Parameters<typeof onSendEmail>[0])}
        onSendWhatsApp={(candidate) => onSendWhatsApp(candidate as unknown as Parameters<typeof onSendWhatsApp>[0])}
        onSendTriagem={(candidate) => onSendTriagem(candidate as unknown as Parameters<typeof onSendTriagem>[0])}
        onSendAgendamento={(candidate) => onSendAgendamento(candidate as unknown as Parameters<typeof onSendAgendamento>[0])}
        onSendFeedback={(candidate) => onSendFeedback(candidate as unknown as Parameters<typeof onSendFeedback>[0])}
        jobId={jobVacancyId}
      />
    </React.Suspense>
    </div>
  </div>
)}

}
