"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
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

  const [fetchedEligibility, setFetchedEligibility] = useState<EligibilityResultItem[] | null>(null)
  const [isEliminated, setIsEliminated] = useState(false)
  const [eliminationReasonText, setEliminationReasonText] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) {
      setFetchedEligibility(null)
      setIsEliminated(false)
      setEliminationReasonText(null)
      return
    }
    const candidateId = candidate?.id
    const resolvedJobId = jobId ?? jobVacancyId
    if (!candidateId || !resolvedJobId) return
    const controller = new AbortController()
    const params = new URLSearchParams({ candidate_id: String(candidateId), job_id: String(resolvedJobId) })
    fetch(`/api/backend-proxy/triagem/sessions?${params.toString()}`, { signal: controller.signal })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return

        // Campos de eliminação por elegibilidade
        if (data.eliminated === true) {
          setIsEliminated(true)
          setEliminationReasonText(data.elimination_reason_text ?? null)
        }

        const items: EligibilityResultItem[] = (data?.eligibility_results ?? [])
          .filter((r: Record<string, unknown>) => r && typeof r.question === "string" && r.question)
          .map((r: Record<string, unknown>, i: number) => ({
            id: String(r.id ?? i),
            question: String(r.question),
            answer: r.answer != null ? String(r.answer) : undefined,
            passed: Boolean(r.passed),
            is_eliminatory: r.is_eliminatory !== false,
            reconsideration: r.reconsideration != null ? String(r.reconsideration) : undefined,
          }))
        if (items.length > 0) setFetchedEligibility(items)
      })
      .catch(() => {})
    return () => controller.abort()
  }, [isOpen, candidate?.id, jobId, jobVacancyId])

  const resolvedEligibilityResults = fetchedEligibility ?? eligibilityResults

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
        <div className="w-full max-w-3xl max-h-[85vh] overflow-y-auto flex flex-col gap-4 rounded-xl border border-lia-border-subtle bg-lia-bg-secondary">
          <div className="flex flex-col items-center gap-3 pt-8 px-8">
            <AlertCircle className="w-8 h-8 text-lia-text-secondary" />
            <p className="text-sm text-lia-text-secondary">{state.error || "Dados não disponíveis."}</p>
            <button onClick={onClose} className="mt-2 px-4 py-2 text-sm rounded-md bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover">Fechar</button>
          </div>
          {resolvedEligibilityResults && resolvedEligibilityResults.length > 0 && (
            <div className="px-4 pb-6">
              <EligibilityResultsSection results={resolvedEligibilityResults} initialExpanded={isEliminated} />
            </div>
          )}
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

        {/* Banner LGPD / EU AI Act — aparece ACIMA do header quando eliminado por elegibilidade */}
        {isEliminated && (
          <div
            role="alert"
            className="flex items-start gap-2 px-4 py-2.5 text-xs"
            style={{
              background: "var(--status-warning-bg)",
              borderBottom: "1px solid var(--status-warning-border)",
              color: "var(--status-warning)",
            }}
          >
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p>
              <span className="font-semibold">LGPD / EU AI Act:</span> Triagem encerrada na fase de pré-elegibilidade. O candidato pode solicitar revisão da decisão via{" "}
              <Link
                href="/privacidade"
                className="underline underline-offset-2 font-medium hover:opacity-80 transition-opacity"
                style={{ color: "var(--status-warning)" }}
              >
                Central de Privacidade
              </Link>
              .
            </p>
          </div>
        )}

        {/* Audit task #529 (G23-02 frontend) — Banner análise semântica degradada */}
        {state.details.degraded_quality && (() => {
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
                Análise semântica não disponível para {degradedCount} resposta{degradedCount === 1 ? "" : "s"}
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
          isEligibilityEliminated={isEliminated}
        />

        <div className="flex-1 overflow-y-auto p-4 bg-lia-bg-secondary">
          {state.activeTab === "triagem" && (
            <div className="space-y-4">
              {/* Callout vermelho de eliminação — aparece antes da seção de elegibilidade */}
              {isEliminated && eliminationReasonText && (
                <div
                  className="rounded-lg p-3 flex gap-2 items-start"
                  style={{
                    background: "var(--status-error-bg)",
                    border: "1px solid var(--status-error-border)",
                  }}
                >
                  <AlertTriangle
                    className="w-4 h-4 flex-shrink-0 mt-0.5"
                    style={{ color: "var(--status-error)" }}
                  />
                  <div>
                    <p className="text-sm font-semibold" style={{ color: "var(--status-error)" }}>
                      Triagem encerrada na fase de elegibilidade
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "var(--lia-text-secondary)" }}>
                      {eliminationReasonText} As seções de Score WSI e Respostas não foram aplicadas.
                    </p>
                  </div>
                </div>
              )}

              {resolvedEligibilityResults && resolvedEligibilityResults.length > 0 && (
                <EligibilityResultsSection
                  results={resolvedEligibilityResults}
                  initialExpanded={isEliminated}
                />
              )}
              <TriagemScoresPanel
                scores={scores}
                sessionInfo={sessionInfo}
                f11Report={state.f11Report}
                details={state.details}
                isEligibilityEliminated={isEliminated}
              />
              <TriagemResponsesSection
                responses={responses}
                f11Report={state.f11Report}
                expandedSections={state.expandedSections}
                toggleSection={state.toggleSection}
              />
            </div>
          )}

          {state.activeTab === "parecer" && (
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

          {state.activeTab === "comparativo" && (
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
