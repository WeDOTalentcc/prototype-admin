"use client"

import React from "react"
import dynamic from "next/dynamic"
import type { Candidate } from "./types"

const CandidatePreview = dynamic(
  () => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })),
  { ssr: false }
)

export interface CandidatePreviewSidePanelProps {
  showCandidatePreview: boolean
  previewCandidate: Candidate | null
  previewWidth: number
  onPreviewResize: (e: React.MouseEvent) => void
  isPreviewMaximized: boolean
  onCloseCandidatePreview: () => void
  onTogglePreviewMaximize: () => void
  sortedCandidates: Candidate[]
  onCandidatePageOpen: (candidate: Candidate) => void
  setSelectedCandidateForAction: (candidate: Candidate) => void
  setShowScheduleModal: (value: boolean) => void
  setSelectedCandidatesForBatch: React.Dispatch<React.SetStateAction<Set<string>>>
  setShowAddToVacancyModal: (value: boolean) => void
  onToggleFavorite: (id: string) => void
  favorites: Set<string>
  onStartWSITextScreening: (candidate: Candidate) => void
  onSendEmail: (candidate: Candidate) => void
  onSendWhatsApp: (candidate: Candidate) => void
  onSendTriagem: (candidate: Candidate) => void
  onSendAgendamento: (candidate: Candidate) => void
  onSendFeedback: (candidate: Candidate) => void
  setPreviewCandidate: (candidate: Candidate) => void
}

export function CandidatePreviewSidePanel({
  showCandidatePreview,
  previewCandidate,
  previewWidth,
  onPreviewResize,
  isPreviewMaximized,
  onCloseCandidatePreview,
  onTogglePreviewMaximize,
  sortedCandidates,
  onCandidatePageOpen,
  setSelectedCandidateForAction,
  setShowScheduleModal,
  setSelectedCandidatesForBatch,
  setShowAddToVacancyModal,
  onToggleFavorite,
  favorites,
  onStartWSITextScreening,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  setPreviewCandidate,
}: CandidatePreviewSidePanelProps) {
  if (!showCandidatePreview || !previewCandidate) return null

  return (
    <div className="flex-shrink-0 relative" style={{ width: `${previewWidth}px` }}>
      <div
        className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-gray-400 dark:hover:bg-gray-500 transition-colors motion-reduce:transition-none z-10 group"
        onMouseDown={onPreviewResize}
        title="Arraste para redimensionar"
      >
        <div className="absolute inset-0 -left-1 -right-1"></div>
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 dark:bg-lia-bg-elevated group-hover:bg-gray-400 dark:group-hover:bg-gray-500 rounded-full transition-colors motion-reduce:transition-none"></div>
      </div>
      <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
        <CandidatePreview
          candidate={previewCandidate as any}
          isOpen={showCandidatePreview}
          onClose={onCloseCandidatePreview}
          isMaximized={isPreviewMaximized}
          onToggleMaximize={onTogglePreviewMaximize}
          candidates={sortedCandidates as any}
          currentIndex={sortedCandidates.findIndex(c => c.id === previewCandidate.id)}
          onNavigateCandidate={(index) => {
            if (sortedCandidates[index]) {
              setPreviewCandidate(sortedCandidates[index])
            }
          }}
          onOpenFullPage={onCandidatePageOpen as any}
          onScheduleInterview={(candidate: any) => {
            // @ts-ignore TODO: fix type
            setSelectedCandidateForAction(candidate)
            setShowScheduleModal(true)
          }}
          onAddToVacancy={(candidate: any) => {
            // @ts-ignore TODO: fix type
            setSelectedCandidatesForBatch(new Set([candidate.id]))
            setShowAddToVacancyModal(true)
          }}
          onToggleFavorite={(candidateId: any) => onToggleFavorite(candidateId)}
          // @ts-ignore TODO: fix type
          onWSIScreening={(candidate: any) => onStartWSITextScreening(candidate)}
          isFavorite={favorites.has(previewCandidate.id)}
          // @ts-ignore TODO: fix type
          onSendEmail={(candidate: any) => onSendEmail(candidate)}
          // @ts-ignore TODO: fix type
          onSendWhatsApp={(candidate: any) => onSendWhatsApp(candidate)}
          // @ts-ignore TODO: fix type
          onSendTriagem={(candidate: any) => onSendTriagem(candidate)}
          // @ts-ignore TODO: fix type
          onSendAgendamento={(candidate: any) => onSendAgendamento(candidate)}
          // @ts-ignore TODO: fix type
          onSendFeedback={(candidate: any) => onSendFeedback(candidate)}
        />
      </div>
    </div>
  )
}
