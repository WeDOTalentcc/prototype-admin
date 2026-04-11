"use client"

import { Loader2, AlertCircle } from "lucide-react"
import type { Candidate } from "@/components/pages/candidates/types"
import {
  TriagemScoresPanel,
  TriagemComparativoTab,
  TriagemSummaryBar,
  TriagemDetailsHeader,
  TriagemResponsesSection,
  TriagemParecerTab,
  TriagemDetailsFooter,
} from "./triagem-details"
import {
  useTriagemDetailsState,
  getClassificationColor,
  getDecisionDisplay,
  getScoreColor,
  getClassificationLabel,
} from "./triagem-details/useTriagemDetailsState"

interface TriagemDetailsModalProps {
  candidate: Candidate
  isOpen: boolean
  onClose: () => void
  jobVacancyId?: string
  onApprove?: (candidate: Candidate) => void
  onReject?: (candidate: Candidate) => void
}

export function TriagemDetailsModal({
  candidate,
  isOpen,
  onClose,
  jobVacancyId,
  onApprove,
  onReject
}: TriagemDetailsModalProps) {
  const state = useTriagemDetailsState(candidate, isOpen, jobVacancyId)

  if (!isOpen) return null

  if (state.loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay" role="status" aria-live="polite" aria-label="Carregando...">
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-xl bg-lia-bg-primary" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-8 h-8 animate-spin motion-reduce:animate-none text-wedo-cyan" />
          <p className="text-sm text-lia-text-secondary">Carregando dados da triagem...</p>
        </div>
      </div>
    )
  }

  if (state.error || !state.details) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay">
        <div className="w-full max-w-3xl p-8 flex flex-col items-center gap-3 rounded-xl bg-lia-bg-primary">
          <AlertCircle className="w-8 h-8 text-lia-text-secondary" />
          <p className="text-sm text-lia-text-secondary">{state.error || 'Dados não disponíveis.'}</p>
          <button onClick={onClose} className="mt-2 px-4 py-2 text-sm rounded-xl bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover">Fechar</button>
        </div>
      </div>
    )
  }

  const { scores, session: sessionInfo, responses, report, feedback } = state.details
  const classColors = getClassificationColor(scores.classification)
  const decisionDisplay = getDecisionDisplay(feedback?.decision)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay">
      <div className="w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col rounded-xl border border-lia-border-subtle bg-lia-bg-secondary">
        <TriagemDetailsHeader
          candidate={candidate}
          details={state.details}
          ranking={state.ranking}
          onClose={onClose}
        />

        <TriagemSummaryBar
          scores={scores}
          sessionInfo={sessionInfo}
          ranking={state.ranking}
          classColors={classColors}
          decisionDisplay={decisionDisplay}
          activeTab={state.activeTab}
          onTabChange={state.setActiveTab}
          getClassificationLabel={getClassificationLabel}
          getScoreColor={getScoreColor}
        />

        <div className="flex-1 overflow-y-auto p-4 bg-lia-bg-secondary">
          {state.activeTab === 'triagem' && (
            <div className="space-y-4">
              <TriagemScoresPanel
                scores={scores}
                sessionInfo={sessionInfo}
                f11Report={state.f11Report}
                details={state.details}
              />
              <TriagemResponsesSection
                responses={responses}
                f11Report={state.f11Report}
                expandedSections={state.expandedSections}
                toggleSection={state.toggleSection}
              />
            </div>
          )}

          {state.activeTab === 'parecer' && (
            <TriagemParecerTab
              scores={scores}
              sessionInfo={sessionInfo}
              report={report}
              feedback={feedback}
              f11Report={state.f11Report}
              details={state.details}
              decisionDisplay={decisionDisplay}
              isPendingDecision={state.isPendingDecision}
              canTriggerFeedback={state.canTriggerFeedback}
              feedbackAlreadySent={state.feedbackAlreadySent}
              sendingFeedback={state.sendingFeedback}
              feedbackSuccess={state.feedbackSuccess}
              feedbackError={state.feedbackError}
              handleSendFeedback={state.handleSendFeedback}
              bigFiveHint={state.bigFiveHint}
              setBigFiveHint={state.setBigFiveHint}
              copiedFeedback={state.copiedFeedback}
              setCopiedFeedback={state.setCopiedFeedback}
            />
          )}

          {state.activeTab === 'comparativo' && (
            <TriagemComparativoTab
              vacancyRanking={state.vacancyRanking}
              ranking={state.ranking}
              candidate={candidate}
            />
          )}
        </div>

        <TriagemDetailsFooter
          candidate={candidate}
          approving={state.approving}
          setApproving={state.setApproving}
          rejecting={state.rejecting}
          setRejecting={state.setRejecting}
          confirmReject={state.confirmReject}
          setConfirmReject={state.setConfirmReject}
          onApprove={onApprove}
          onReject={onReject}
        />
      </div>
    </div>
  )
}
