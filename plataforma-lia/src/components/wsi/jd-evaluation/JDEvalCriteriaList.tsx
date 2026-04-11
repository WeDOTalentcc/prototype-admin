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
  const band = evaluation.band || (evaluation.score >= 90 ? 'excelente' : evaluation.score >= 70 ? 'bom' : evaluation.score >= 50 ? 'adequado' : evaluation.score >= 30 ? 'insuficiente' : 'critico')
  const bandLabel = evaluation.band_label || (band === 'excelente' ? 'Excelente' : band === 'bom' ? 'Bom' : band === 'adequado' ? 'Adequado' : band === 'insuficiente' ? 'Insuficiente' : 'Crítico')
  const bandColors: Record<string, string> = {
    excelente: 'bg-status-success/10 text-status-success border-status-success/30',
    bom: 'bg-status-success/10 text-status-success border-status-success/30',
    adequado: 'bg-status-warning/10 text-status-warning border-status-warning/30',
    insuficiente: 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30',
    critico: 'bg-status-error/10 text-status-error border-status-error/30',
  }

  return (
    <>
      <div className="flex items-center gap-3 pb-2">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-lia-text-primary">{evaluation.score}</span>
          <span className="text-micro text-lia-text-secondary">/100</span>
        </div>
        <span className={cn("text-micro font-semibold px-2 py-0.5 rounded-full border", bandColors[band] || bandColors.adequado)}>
          {bandLabel}
        </span>
        {band === 'critico' && (
          <span className="text-micro text-status-error font-medium flex items-center gap-1">
            <XCircle className="w-3 h-3" />
            JD bloqueado — geração de perguntas desabilitada
          </span>
        )}
      </div>

      {evaluation.indicators.some(i => i.dimension) && (
        <div className="grid grid-cols-3 gap-1.5 pb-2">
          {evaluation.indicators.map((indicator) => (
            <div key={indicator.label} className={cn(
              "flex items-center gap-1.5 px-2 py-1.5 rounded-md border text-micro",
              indicator.status === 'sufficient' ? 'bg-status-success/10 border-status-success/30 dark:bg-status-success/10 dark:border-status-success/30' :
              indicator.status === 'partial' ? 'bg-status-warning/10 border-status-warning/30 dark:bg-status-warning/10 dark:border-status-warning/30' :
              'bg-status-error/10 border-status-error/30 dark:bg-status-error/10 dark:border-status-error/30'
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
                  'text-status-error dark:text-status-error'
                )}>{indicator.label}</span>
              </div>
              <span className="text-micro font-semibold text-lia-text-secondary shrink-0">
                {indicator.earned ?? 0}/{indicator.weight ?? 0}
              </span>
            </div>
          ))}
        </div>
      )}

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

      {evaluation.lia_suggestion && (
        <div className={cn(
          "text-micro px-2.5 py-2 rounded-md border leading-relaxed",
          evaluation.can_generate
            ? "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary/50"
            : "bg-status-error/10 border-status-error/30 text-status-error dark:bg-status-error/10 dark:border-status-error/30 dark:text-status-error"
        )}>
          {evaluation.lia_suggestion}
        </div>
      )}
    </>
  )
})

export default JDEvalCriteriaList
