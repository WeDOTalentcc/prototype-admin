"use client"

import React from "react"
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
} from "lucide-react"
import {
  buildCandidateEvaluationCard,
  evaluationTierClasses,
  type CandidateEvaluationCardData,
} from "./candidate-card-data"

/**
 * CandidateEvaluationCard — renders the BARS / CV-screening result in the chat
 * feed using the same visual vocabulary as the CV modal (WSIScorecard /
 * WSIDetailedReport): score circle, recommendation badge, strengths/concerns,
 * and an expandable per-requirement breakdown.
 *
 * Honesty: when the evaluation is a non-persisted dry-run (`standalone`), the
 * card shows a "Pré-avaliação — não salva" seal so the recruiter never assumes
 * it was written to the pipeline.
 */

interface CandidateEvaluationCardProps {
  /** Raw screening payload (`_build_screening_result` schema) from metadata. */
  raw: unknown
  /** Optional shortcut to open the full WSI report. */
  onViewReport?: (data: CandidateEvaluationCardData) => void
}

export function CandidateEvaluationCard({
  raw,
  onViewReport,
}: CandidateEvaluationCardProps) {
  const data = React.useMemo(() => buildCandidateEvaluationCard(raw), [raw])
  const [showEvaluations, setShowEvaluations] = React.useState(false)

  if (!data) return null

  const tier = evaluationTierClasses(data)
  const score = Math.round(data.rubricScore)
  const recommendation = data.recommendationLabel ?? data.recommendation
  const header = [data.candidateName, data.jobTitle].filter(Boolean).join(" • ")

  return (
    <div className="mt-2 space-y-3 rounded-md border border-lia-border-subtle bg-lia-bg-primary p-4 shadow-lia-sm dark:bg-lia-bg-secondary">
      {/* Header — name • job title + recommendation badge */}
      <div className="flex items-start justify-between gap-3">
        <p className="min-w-0 text-sm font-medium text-lia-text-primary">{header}</p>
        {recommendation && (
          <span
            className={`inline-flex flex-shrink-0 items-center rounded-full border px-2 py-0.5 text-xs font-medium ${tier.bg} ${tier.text} ${tier.border}`}
          >
            {recommendation}
          </span>
        )}
      </div>

      {data.standalone && (
        <span className="inline-flex items-center rounded-full border border-status-warning/30 bg-status-warning/10 px-2 py-0.5 text-[11px] font-medium text-status-warning">
          Pré-avaliação — não salva
        </span>
      )}

      {/* Score block — rubric circle + CV-fit indicator */}
      <div className="flex items-center gap-4">
        <div
          className={`flex h-16 w-16 flex-shrink-0 flex-col items-center justify-center rounded-full ${tier.bg}`}
        >
          <span className={`text-xl font-semibold ${tier.text}`}>{score}</span>
          <span className="text-[10px] text-lia-text-tertiary">/100</span>
        </div>
        {(data.cvFitScore !== null || data.cvFitClassification) && (
          <div className="space-y-0.5">
            <p className="text-xs text-lia-text-tertiary">Fit de CV</p>
            <p className="text-sm font-medium text-lia-text-primary">
              {data.cvFitClassification ?? "—"}
              {data.cvFitScore !== null && (
                <span className="ml-1 text-xs font-normal text-lia-text-secondary">
                  {data.cvFitScore.toFixed(1)}/5
                </span>
              )}
            </p>
            <p className="text-[10px] text-lia-text-tertiary">
              Baseado apenas em CV
            </p>
          </div>
        )}
      </div>

      {/* Strengths */}
      {data.strengths.length > 0 && (
        <div>
          <p className="mb-1.5 flex items-center gap-1 text-xs font-medium text-status-success">
            <CheckCircle className="h-3.5 w-3.5" /> Pontos fortes
          </p>
          <ul className="space-y-1">
            {data.strengths.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-lia-text-secondary"
              >
                <CheckCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-status-success" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Concerns */}
      {data.concerns.length > 0 && (
        <div>
          <p className="mb-1.5 flex items-center gap-1 text-xs font-medium text-status-warning">
            <AlertTriangle className="h-3.5 w-3.5" /> Pontos de atenção
          </p>
          <ul className="space-y-1">
            {data.concerns.map((item, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-lia-text-secondary"
              >
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-status-warning" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {data.reasoning && (
        <p className="text-xs italic leading-relaxed text-lia-text-tertiary">
          {data.reasoning}
        </p>
      )}

      {/* Expandable per-requirement BARS breakdown */}
      {data.evaluations.length > 0 && (
        <div className="border-t border-lia-border-subtle pt-2">
          <button
            type="button"
            onClick={() => setShowEvaluations((prev) => !prev)}
            className="flex w-full items-center justify-between text-xs font-medium text-lia-text-secondary transition-colors hover:text-lia-text-primary"
          >
            <span>Avaliação por requisito ({data.evaluations.length})</span>
            {showEvaluations ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>

          {showEvaluations && (
            <div className="mt-2 space-y-2">
              {data.evaluations.map((item, i) => (
                <div
                  key={i}
                  className="rounded-md border border-lia-border-subtle bg-lia-bg-tertiary/40 p-2.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="min-w-0 truncate text-xs font-medium text-lia-text-primary">
                      {item.requirement}
                    </span>
                    {item.level && (
                      <span className="flex-shrink-0 rounded-full bg-lia-bg-tertiary px-2 py-0.5 text-[10px] text-lia-text-secondary">
                        {item.level}
                      </span>
                    )}
                  </div>
                  {(item.points !== null || item.weightedPoints !== null) && (
                    <p className="mt-1 text-[11px] text-lia-text-tertiary">
                      {item.points !== null && <>{item.points} pts</>}
                      {item.weightedPoints !== null && (
                        <span className="ml-2">
                          ponderado: {item.weightedPoints}
                        </span>
                      )}
                    </p>
                  )}
                  {item.evidence && (
                    <p className="mt-1 text-[11px] italic text-lia-text-secondary">
                      {item.evidence}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {onViewReport && (
        <button
          type="button"
          onClick={() => onViewReport(data)}
          className="flex w-full items-center justify-center gap-1 rounded-md border border-lia-border-default px-2.5 py-1.5 text-xs text-lia-text-secondary transition-colors hover:bg-lia-bg-tertiary"
        >
          <FileText className="h-3.5 w-3.5" /> Ver relatório completo
        </button>
      )}
    </div>
  )
}
