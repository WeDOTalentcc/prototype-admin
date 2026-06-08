"use client"

import { Loader2, AlertCircle, AlertTriangle } from "lucide-react"
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
import { EligibilityResultsSection } from "@/components/wsi/eligibility-results-section"
import type { EligibilityResultItem } from "@/components/wsi/eligibility-results-section"

interface TriagemDetailsModalProps {
  candidate: Candidate
  isOpen: boolean
  onClose: () => void
  jobVacancyId?: string
  /** Task #425 — optional context to enable the Twilio PSTN trigger button. */
  jobId?: string
  jobTitle?: string
  companyId?: string
  onApprove?: (candidate: Candidate) => void
  onReject?: (candidate: Candidate) => void
  eligibilityResults?: EligibilityResultItem[]
}

export function TriagemDetailsModal({
  candidate,
  isOpen,
  onClose,
  jobVacancyId,
  jobId,
  jobTitle,
  companyId,
  onApprove,
  onReject,
  eligibilityResults,
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
        {/* Audit task #529 (G23-02 frontend) — Banner LGPD/EU AI Act:
            renderizado ACIMA do header (conforme spec) para máxima visibilidade
            quando a Camada 2 (análise semântica) não está disponível. */}
        {state.details.degraded_quality && (() => {
          // Fallback: se backend não populou degraded_count, derivamos das respostas.
          const degradedCount = state.details.degraded_count
            ?? state.details.responses.filter(r => r.degraded_quality).length
          return (
          <div
            role="status"
            aria-live="polite"
            className="mx-4 mt-3 flex items-start gap-2 rounded-lg border border-status-warning/30 bg-status-warning/10 px-3 py-2"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-status-warning" />
            <div className="flex-1 text-xs leading-relaxed">
              <p className="font-semibold text-status-warning">
                Análise semântica não disponível para {degradedCount} resposta{degradedCount === 1 ? '' : 's'}
              </p>
              <p className="mt-0.5 text-lia-text-secondary">
                Resultado calculado por regras determinísticas (Camada 1). Pontuação válida, com transparência reduzida na análise contextual.
              </p>
              {state.details.degraded_reasons && state.details.degraded_reasons.length > 0 && (
                <ul className="mt-1.5 list-disc space-y-0.5 pl-4 text-lia-text-secondary">
                  {state.details.degraded_reasons.slice(0, 5).map((reason, i) => (
                    <li key={`deg-${i}`}>{reason}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
          )
        })()}

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
              {eligibilityResults && eligibilityResults.length > 0 && (
                <EligibilityResultsSection results={eligibilityResults} />
              )}
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
          jobTitle={jobTitle}
          jobId={jobId ?? jobVacancyId}
          companyId={companyId}
        />
      </div>
    </div>
  )
}
