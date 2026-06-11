"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"

const CandidatePreviewDynamic = React.lazy(() =>
  import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })))

const PANEL_MIN_WIDTH = 320
const PANEL_MAX_WIDTH = 700
const PANEL_DEFAULT_WIDTH = 400

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
  const [panelWidth, setPanelWidth] = useState(PANEL_DEFAULT_WIDTH)
  const isDragging = useRef(false)
  const dragStartX = useRef(0)
  const dragStartWidth = useRef(0)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    isDragging.current = true
    dragStartX.current = e.clientX
    dragStartWidth.current = panelWidth
    document.body.style.cursor = 'col-resize'
    e.preventDefault()
  }, [panelWidth])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const delta = dragStartX.current - e.clientX
      const newWidth = Math.min(PANEL_MAX_WIDTH, Math.max(PANEL_MIN_WIDTH, dragStartWidth.current + delta))
      setPanelWidth(newWidth)
    }
    const onMouseUp = () => {
      if (!isDragging.current) return
      isDragging.current = false
      document.body.style.cursor = ''
    }
    document.addEventListener('mousemove', onMouseMove)
    document.addEventListener('mouseup', onMouseUp)
    return () => {
      document.removeEventListener('mousemove', onMouseMove)
      document.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  if (!isPreviewOpen || !previewCandidate) return null

  return (
  <div
    className="flex-shrink-0 h-full flex"
    style={{ width: isPreviewMaximized ? 700 : panelWidth }}
    data-testid="kanban-candidate-preview-panel"
  >
    <div
      className="w-1.5 flex-shrink-0 cursor-col-resize group flex items-center justify-center hover:bg-lia-border-medium/40 transition-colors motion-reduce:transition-none rounded-l-md"
      onMouseDown={onMouseDown}
      title="Arraste para redimensionar"
    >
      <div className="w-0.5 h-8 rounded-full bg-lia-border-medium group-hover:bg-lia-text-disabled transition-colors motion-reduce:transition-none" />
    </div>
    <div className="flex-1 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle h-full overflow-hidden">
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
  )
}
