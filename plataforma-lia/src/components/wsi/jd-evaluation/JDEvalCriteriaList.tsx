"use client"

import React from "react"
import {
  FileText,
  Brain,
  CheckCircle, XCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { JDEvaluationData } from "./useJDEvaluation"

interface JDEvalCriteriaListProps {
  evaluation: JDEvaluationData
}

export const JDEvalCriteriaList = React.memo(function JDEvalCriteriaList({
  evaluation,
}: JDEvalCriteriaListProps) {
  if (!evaluation.indicators || evaluation.indicators.length === 0) {
    return null
  }

  return (
    <>
      {/* D1–D9 structured grid (canonical source — summary is in JDEvaluationHeader) */}
      {evaluation.indicators.some(i => i.dimension) && (
        <div className="grid grid-cols-3 gap-1.5 pb-2">
          {evaluation.indicators.map((indicator) => (
            <div key={indicator.label} className={cn(
              "flex items-center gap-1.5 px-2 py-1.5 rounded-md border text-micro",
              indicator.status === 'sufficient' ? 'bg-status-success/10 border-status-success/30' :
              indicator.status === 'partial' ? 'bg-status-warning/10 border-status-warning/30' :
              'bg-status-error/10 border-status-error/30'
            )}>
              {indicator.status === 'sufficient' ? (
                <CheckCircle className="w-3 h-3 text-status-success shrink-0" />
              ) : indicator.status === 'partial' ? (
                <Brain className="w-3 h-3 text-status-warning shrink-0" />
              ) : (
                <XCircle className="w-3 h-3 text-status-error shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide block">{indicator.dimension}</span>
                <span className={cn(
                  "truncate block font-medium",
                  indicator.status === 'sufficient' ? 'text-status-success' :
                  indicator.status === 'partial' ? 'text-status-warning' :
                  'text-status-error'
                )}>{indicator.label}</span>
              </div>
              <span className="text-micro font-semibold text-lia-text-secondary shrink-0">
                {indicator.earned ?? 0}/{indicator.weight ?? 0}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Compact row for legacy indicators without dimension field */}
      {!evaluation.indicators.some(i => i.dimension) && (
        <div className="flex items-center gap-3 pb-2 flex-wrap">
          {evaluation.indicators.map((indicator) => (
            <div key={indicator.label} className="flex items-center gap-1.5">
              <FileText className="h-3 w-3 text-lia-text-secondary" />
              <span className="text-micro text-lia-text-secondary">{indicator.label}:</span>
              <span className="text-xs font-semibold text-lia-text-primary">{indicator.count ?? 0}</span>
              <span className={cn("w-1.5 h-1.5 rounded-full",
                indicator.status === 'sufficient' ? 'bg-status-success' :
                indicator.status === 'partial' ? 'bg-status-warning' : 'bg-status-error'
              )} />
            </div>
          ))}
        </div>
      )}
    </>
  )
})

export default JDEvalCriteriaList
