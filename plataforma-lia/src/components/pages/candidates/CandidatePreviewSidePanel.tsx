"use client"

import React from "react"
import { useTranslations } from "next-intl"
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
  searchCriteria?: Record<string, unknown> | null
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
  searchCriteria,
}: CandidatePreviewSidePanelProps) {
  const t = useTranslations('candidates.preview')
  if (!showCandidatePreview || !previewCandidate) return null

  return (
    <div data-testid="candidate-preview-side-panel" className="flex-shrink-0 relative" style={{ width: `${previewWidth}px` }}>
      <div
        className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-lia-border-medium dark:hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none z-10 group"
        onMouseDown={onPreviewResize}
        title={t('dragToResize')}
      >
        <div className="absolute inset-0 -left-1 -right-1"></div>
        <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-12 bg-lia-border-default dark:bg-lia-bg-elevated group-hover:bg-lia-border-medium dark:group-hover:bg-lia-bg-secondary rounded-full transition-colors motion-reduce:transition-none"></div>
      </div>
      <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle h-[calc(100vh-6rem)] overflow-hidden">
        <CandidatePreview
          candidate={previewCandidate as any}
          searchCriteria={searchCriteria}
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
          onScheduleInterview={(candidate: unknown) => {
            setSelectedCandidateForAction(candidate as unknown as Candidate)
            setShowScheduleModal(true)
          }}
          onAddToVacancy={(candidate: unknown) => {
            setSelectedCandidatesForBatch(new Set([(candidate as Record<string, unknown>).id as string]))
            setShowAddToVacancyModal(true)
          }}
          onToggleFavorite={(candidateId: unknown) => onToggleFavorite(candidateId as string)}
          onWSIScreening={(candidate: unknown) => (onStartWSITextScreening as (c: unknown) => void)(candidate)}
          isFavorite={favorites.has(previewCandidate.id)}
          onSendEmail={(candidate: unknown) => (onSendEmail as (c: unknown) => void)(candidate)}
          onSendWhatsApp={(candidate: unknown) => (onSendWhatsApp as (c: unknown) => void)(candidate)}
          onSendTriagem={(candidate: unknown) => (onSendTriagem as (c: unknown) => void)(candidate)}
          onSendAgendamento={(candidate: unknown) => (onSendAgendamento as (c: unknown) => void)(candidate)}
          onSendFeedback={(candidate: unknown) => (onSendFeedback as (c: unknown) => void)(candidate)}
        />
      </div>
    </div>
  )
}
