"use client"

import React from "react"
import { Target, X, FileText, User, Briefcase, Loader2, ThumbsUp, ThumbsDown } from "lucide-react"
import type { RubricEvaluationModalProps } from "./rubric-evaluation-types"
import { useRubricEvaluation } from "@/hooks/ai/use-rubric-evaluation"
import { RubricOverviewSection } from "./rubric-overview-section"
import { RubricDetailsSection } from "./rubric-details-section"

export type { RubricEvaluationData, RubricEvaluationModalProps } from "./rubric-evaluation-types"

const sectionTabs = [
  { id: 'overview', label: 'Visão Geral', icon: Target },
  { id: 'details', label: 'Detalhes', icon: FileText },
] as const

export function RubricEvaluationModal({
  isOpen,
  onClose,
  evaluation,
  candidateId,
  candidateName,
  jobId,
  onApprove,
  onReject,
}: RubricEvaluationModalProps) {
  const hook = useRubricEvaluation(
    evaluation,
    candidateId,
    candidateName,
    jobId,
    onApprove,
    onReject,
    onClose,
  )

  if (!isOpen || !evaluation) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay" data-testid="rubric-evaluation-modal">
      <div className="w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col rounded-xl dark:bg-lia-bg-secondary dark:border-lia-border-subtle border border-lia-border-subtle bg-[var(--lia-bg-secondary)]">
        <div className="flex items-center justify-between px-4 py-3 border-b border-b-lia-border-subtle">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/[.12]">
              <Target className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h2 className="text-base-ui font-semibold text-lia-text-primary">
                Análise CV vs Vaga
              </h2>
              <div className="flex items-center gap-2 text-xs">
                <span className="flex items-center gap-1 text-lia-text-primary">
                  <User className="w-3 h-3 text-lia-text-secondary" />
                  {hook.displayName}
                </span>
                <span className="text-lia-text-tertiary">|</span>
                <span className="flex items-center gap-1 text-lia-text-secondary">
                  <Briefcase className="w-3 h-3" />
                  {hook.jobTitle}
                </span>
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-bg-tertiary rounded-full text-lia-text-secondary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-1 px-4 py-2 border-b border-b-lia-border-subtle">
          {sectionTabs.map((tab) => {
            const TabIcon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => hook.setActiveSection(tab.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors motion-reduce:transition-none"
                style={{
                  backgroundColor: hook.activeSection === tab.id ? 'var(--wedo-cyan-bg-12)' : 'transparent',
                  color: hook.activeSection === tab.id ? 'var(--lia-btn-primary-bg)' : 'var(--lia-text-tertiary)',
                }}
              >
                <TabIcon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            )
          })}
        </div>

        <div className="flex-1 overflow-y-auto p-4 bg-lia-bg-secondary">
          {hook.activeSection === 'overview' && (
            <RubricOverviewSection
              score={hook.score}
              scoreBadge={hook.scoreBadge}
              decisionBadge={hook.decisionBadge}
              evaluation={evaluation}
              essentialMet={hook.essentialMet}
              essentialReqsLength={hook.essentialReqs.length}
              importantMet={hook.importantMet}
              importantReqsLength={hook.importantReqs.length}
              desirableMet={hook.desirableMet}
              desirableReqsLength={hook.desirableReqs.length}
              mockParecer={hook.mockParecer}
              mockWhyCandidate={hook.mockWhyCandidate}
            />
          )}
          {hook.activeSection === 'details' && (
            <RubricDetailsSection
              sortedRequirements={hook.sortedRequirements}
              requirements={hook.requirements}
              mockRedFlags={hook.mockRedFlags}
              showAudit={hook.showAudit}
              setShowAudit={hook.setShowAudit}
              essentialMet={hook.essentialMet}
              essentialReqsLength={hook.essentialReqs.length}
              evaluation={evaluation}
            />
          )}
        </div>

        <div className="flex-shrink-0 px-4 py-3 flex items-center justify-between border-t border-lia-border-subtle bg-lia-bg-secondary dark:bg-lia-bg-primary dark:border-lia-border-subtle">
          <div className="flex items-center gap-2">
            <span className="text-micro text-lia-text-secondary">
              Decisão do Recrutador
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={hook.handleReject}
              disabled={hook.isLoading || !onReject}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-xl transition-colors motion-reduce:transition-none hover:bg-status-error/10 disabled:opacity-50 disabled:cursor-not-allowed bg-lia-bg-primary border border-lia-border-default text-status-error dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse dark:text-status-error"
            >
              {hook.isRejecting ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              ) : (
                <ThumbsDown className="w-3.5 h-3.5" />
              )}
              Reprovar
            </button>
            <button
              onClick={hook.handleApprove}
              disabled={hook.isLoading || !onApprove}
              className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-xl transition-colors motion-reduce:transition-none hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed bg-lia-btn-primary-bg text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              {hook.isApproving ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none" />
              ) : (
                <ThumbsUp className="w-3.5 h-3.5" />
              )}
              Aprovar para Triagem
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RubricEvaluationModal
