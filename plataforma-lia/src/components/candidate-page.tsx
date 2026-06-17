"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Chip } from "@/components/ui/chip"
import { CandidatePageHeader } from "@/components/candidate-page/CandidatePageHeader"
import { CandidatePageSummary } from "@/components/candidate-page/CandidatePageSummary"
import { CandidatePreviewProfileTab } from "@/components/candidate-preview/CandidatePreviewProfileTab"
import { CandidateActivitiesTab } from "@/components/candidate-preview/CandidateActivitiesTab"
import { CandidateFilesTab } from "@/components/candidate-preview/CandidateFilesTab"
import { CandidateOpinionsTab } from "@/components/candidate-preview/CandidateOpinionsTab"
import { CandidateConsentTab } from "@/components/candidate-preview/CandidateConsentTab"
import { CandidatePreviewModals } from "@/components/candidate-preview/CandidatePreviewModals"
import { useCandidatePreviewCore } from "@/components/candidate-preview/useCandidatePreviewCore"
import { CandidateEditProvider } from "@/components/candidate-profile/CandidateEditContext"
import { useCandidateFieldUpdate } from "@/hooks/candidates/use-candidate-field-update"
import { isFeatureEnabled, FF_CANDIDATE_EDIT } from "@/lib/feature-flags"
import { UserCheck, Activity, FileText, Brain, ChevronLeft, ChevronRight, ShieldCheck } from "lucide-react"

export type CandidatePageMode = "modal" | "page"

interface CandidatePageProps {
  candidate: Record<string, unknown>
  /** Layout mode. 'modal' = full-screen overlay (kanban). 'page' = standalone route layout. */
  mode?: CandidatePageMode
  /** Only relevant in mode='modal' — controls visibility. */
  isOpen?: boolean
  onClose?: () => void
  onBackToKanban?: () => void
  jobId?: string
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
  onContact?: (candidate: Record<string, unknown>, channel?: "email" | "whatsapp") => void
  onSchedule?: (candidate: Record<string, unknown>) => void
  onScheduleInterview?: (candidate: Record<string, unknown>) => void
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  onNavigateCandidate?: (direction: "prev" | "next") => void
  hasPrev?: boolean
  hasNext?: boolean
}

type CandidateLite = {
  name?: string
  id?: string
  candidateId?: string
  avatar_url?: string
  avatar?: string
  email?: string
  phone?: string
  position?: string
  location?: string
  linkedin_url?: string
  linkedinUrl?: string
  github_url?: string
  liaAnalysis?: { score?: number; fitScore?: number }
  [key: string]: unknown
}

const TABS = [
  { id: "profile" as const, label: "Perfil Completo", icon: UserCheck },
  { id: "activities" as const, label: "Atividades", icon: Activity },
  { id: "files" as const, label: "Arquivos", icon: FileText },
  { id: "opinions" as const, label: "Pareceres", icon: Brain },
  { id: "consent" as const, label: "Consentimento", icon: ShieldCheck },
]

export function CandidatePage({
  candidate,
  mode = "modal",
  isOpen = true,
  onClose,
  onBackToKanban: _onBackToKanban = () => {},
  jobId,
  onSendEmail,
  onSendWhatsApp,
  onSendAgendamento,
  onWSIScreening,
  onAddToVacancy,
  onAddToList,
  onSendFeedback,
  onContact,
  onSchedule,
  onScheduleInterview,
  onOpenTriagemDetails,
  onNavigateCandidate,
  hasPrev = false,
  hasNext = false,
}: CandidatePageProps) {
  const core = useCandidatePreviewCore(candidate)
  const candidateId = (candidate?.id ?? candidate?.candidateId ?? candidate?.candidate_id) as string | undefined
  const editHook = useCandidateFieldUpdate(candidateId)
  // Edit pattern (D7): enabled by default in 'page' mode; drawer ('modal' default) stays read-only.
  // Behind feature flag ff_candidate_edit (env or runtime). For now: gate via mode only.
  // Edit only enabled in mode=page AND feature flag NEXT_PUBLIC_FF_CANDIDATE_EDIT=true
  const editableInline = mode === "page" && isFeatureEnabled(FF_CANDIDATE_EDIT)
  const router = useRouter()
  const handleClose = onClose ?? (mode === "page" ? () => router.back() : () => {})

  if (mode === "modal" && !isOpen) return null
  if (!candidate) return null

  const c = candidate as CandidateLite
  const liaScore = c.liaAnalysis?.score ?? 0
  const getScoreColor = (score: number) => {
    if (score >= 7.5) return "text-status-success"
    if (score >= 6) return "text-wedo-orange-text"
    return "text-status-error"
  }

  const containerClass =
    mode === "modal"
      ? "fixed inset-0 bg-lia-bg-primary dark:bg-lia-bg-primary z-[200] overflow-hidden flex flex-col"
      : "min-h-screen bg-lia-bg-primary dark:bg-lia-bg-primary flex flex-col"

  return (
    <CandidateEditProvider
      editable={editableInline}
      candidateId={candidateId}
      updateField={editHook.updateField}
      isSaving={editHook.isSaving}
    >
    <TooltipProvider>
      <div className={containerClass}>
        <CandidatePageHeader
          _candidate={c as Parameters<typeof CandidatePageHeader>[0]["_candidate"]}
          liaScore={liaScore}
          getScoreColor={getScoreColor}
          onClose={handleClose}
          onSendEmail={onSendEmail}
          onSendWhatsApp={onSendWhatsApp}
          onSendAgendamento={onSendAgendamento}
          onWSIScreening={onWSIScreening}
          onAddToVacancy={onAddToVacancy}
          onAddToList={onAddToList}
          onSendFeedback={onSendFeedback}
          candidate={candidate}
        />

        {onNavigateCandidate && (
          <div className="flex items-center gap-1 px-4 py-1.5 border-b border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
            <button
              type="button"
              onClick={() => onNavigateCandidate("prev")}
              disabled={!hasPrev}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Candidato anterior"
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </button>
            <button
              type="button"
              onClick={() => onNavigateCandidate("next")}
              disabled={!hasNext}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Próximo candidato"
            >
              Próximo
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="bg-lia-bg-primary dark:bg-lia-bg-secondary dark:border-lia-border-subtle px-6">
          <div className="flex">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => core.setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
                  core.activeTab === tab.id
                    ? "rounded-lg bg-lia-bg-tertiary text-lia-text-secondary"
                    : "text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse"
                }`}
                aria-current={core.activeTab === tab.id ? "page" : undefined}
              >
                <tab.icon className="w-3 h-3" aria-hidden="true" />
                {tab.label}
                {tab.id === "opinions" && core.opinionsHistory.length > 0 && (
                  <Chip variant="neutral" muted className="text-micro px-1.5 py-0 h-4 flex items-center ml-1 bg-wedo-cyan/15">
                    {core.opinionsHistory.length}
                  </Chip>
                )}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto bg-lia-bg-primary dark:bg-lia-bg-primary">
          {/*
            F9 Item 3 (2-col polish): em mode="page" + viewport >= lg, exibe grid
            5-col (3/2) com aside sticky no rail direito. Em viewport menor ou
            mode="modal", mantém layout single-column existente.
          */}
          <div className="max-w-7xl mx-auto p-6">
            <div
              className={
                mode === "page"
                  ? "grid grid-cols-1 lg:grid-cols-5 gap-6"
                  : ""
              }
            >
              <div className={mode === "page" ? "lg:col-span-3 min-w-0" : ""}>
            {core.activeTab === "profile" && (
              <CandidatePreviewProfileTab
                candidate={candidate}
                jobId={jobId}
                opinionsData={core.opinionsData}
                isLoadingOpinions={core.isLoadingOpinions}
                isAnalyzingWithLia={core.isAnalyzingWithLia}
                lastAnalysisDate={core.lastAnalysisDate}
                formatAnalysisDate={core.formatAnalysisDate}
                handleAnalyzeWithLia={core.handleAnalyzeWithLia}
                formatCurrency={core.formatCurrency}
                languagesData={core.getLanguagesData()}
                hasSalaryData={core.hasSalaryData}
                hasAddressData={core.hasAddressData}
                getAddressString={core.getAddressString}
              />
            )}

            {core.activeTab === "activities" && (
              <CandidateActivitiesTab
                candidate={candidate}
                jobId={jobId}
                onShowLiaModal={() => core.setShowLiaModal(true)}
                onOpenTriagemDetails={onOpenTriagemDetails}
                onSetScreeningModalData={core.setScreeningModalData}
                onSetScreeningModalOpen={core.setScreeningModalOpen}
                onSetDiscModalData={core.setDiscModalData}
                onSetDiscModalOpen={core.setDiscModalOpen}
                onSetBigFiveModalCandidate={core.setBigFiveModalCandidate}
                onSetBigFiveModalOpen={core.setBigFiveModalOpen}
                onSetSelectedFile={core.setSelectedFile}
                onSetPreviewType={core.setPreviewType}
                onSetShowPreview={core.setShowPreview}
              />
            )}

            {core.activeTab === "files" && (
              <CandidateFilesTab candidate={candidate} />
            )}

            {core.activeTab === "opinions" && (
              <CandidateOpinionsTab
                opinionsHistory={core.opinionsHistory}
                isLoadingHistory={core.isLoadingHistory}
                isErrorHistory={core.isErrorHistory}
                onRetryHistory={core.retryOpinionsHistory}
                expandedOpinionId={core.expandedOpinionId as never}
                setExpandedOpinionId={core.setExpandedOpinionId as never}
                copiedItemId={core.copiedItemId}
                handleCopyOpinion={core.handleCopyOpinion as never}
              />
            )}

            {core.activeTab === "consent" && candidateId && (
              <CandidateConsentTab candidateId={candidateId} />
            )}

            {core.activeTab === "consent" && !candidateId && (
              <div className="py-8 text-center text-sm text-lia-text-secondary">
                ID do candidato não disponível para carregar histórico de consentimento.
              </div>
            )}
              </div>
              {mode === "page" && (
                <aside className="lg:col-span-2 lg:sticky lg:top-4 lg:self-start min-w-0">
                  <CandidatePageSummary
                    candidate={candidate as Parameters<typeof CandidatePageSummary>[0]["candidate"]}
                    liaScore={liaScore}
                  />
                </aside>
              )}
            </div>
          </div>
        </div>

        <CandidatePreviewModals
          c={c as Parameters<typeof CandidatePreviewModals>[0]["c"]}
          candidate={candidate}
          showLiaModal={core.showLiaModal}
          setShowLiaModal={core.setShowLiaModal}
          liaActions={[]}
          liaChatMessages={core.liaChatMessages}
          isLiaChatLoading={core.isLiaChatLoading}
          liaConversation={core.liaConversation}
          setLiaConversation={core.setLiaConversation}
          sendLiaMessage={core.sendLiaMessage}
          onContact={onContact}
          onSendEmail={onSendEmail}
          onSchedule={onSchedule}
          onScheduleInterview={onScheduleInterview}
          onSendAgendamento={onSendAgendamento}
          onAddToList={onAddToList}
          onAddToVacancy={onAddToVacancy}
          showUpdateOpinionAlert={core.showUpdateOpinionAlert}
          setShowUpdateOpinionAlert={core.setShowUpdateOpinionAlert}
          lastOpinionDate={core.lastOpinionDate}
          generateNewOpinion={core.generateNewOpinion}
          showInsufficientDataModal={core.showInsufficientDataModal}
          setShowInsufficientDataModal={core.setShowInsufficientDataModal}
          dataRequirements={core.dataRequirements}
          handleProceedWithLimitedData={core.handleProceedWithLimitedData}
          screeningModalOpen={core.screeningModalOpen}
          setScreeningModalOpen={core.setScreeningModalOpen}
          screeningModalData={core.screeningModalData}
          setScreeningModalData={core.setScreeningModalData}
          onOpenTriagemDetails={onOpenTriagemDetails}
          discModalOpen={core.discModalOpen}
          setDiscModalOpen={core.setDiscModalOpen}
          discModalData={core.discModalData}
          setDiscModalData={core.setDiscModalData}
          bigFiveModalOpen={core.bigFiveModalOpen}
          setBigFiveModalOpen={core.setBigFiveModalOpen}
          bigFiveModalCandidate={core.bigFiveModalCandidate}
          setBigFiveModalCandidate={core.setBigFiveModalCandidate}
        />
      </div>
    </TooltipProvider>
    </CandidateEditProvider>
  )
}
