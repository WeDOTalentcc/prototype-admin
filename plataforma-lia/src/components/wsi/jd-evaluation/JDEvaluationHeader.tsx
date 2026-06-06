"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  FileText, ChevronUp, ChevronDown,
  Pencil, XCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { JDEvaluationData } from "./useJDEvaluation"

interface JDEvaluationHeaderProps {
  jobTitle: string
  isExpanded: boolean
  isEditing: boolean
  evaluation?: JDEvaluationData | null
  onToggleExpand: () => void
  onStartEdit: () => void
  canEdit: boolean
}

const BAND_COLORS: Record<string, string> = {
  excelente: 'bg-status-success/10 text-status-success border-status-success/30',
  bom: 'bg-status-success/10 text-status-success border-status-success/30',
  adequado: 'bg-status-warning/10 text-status-warning border-status-warning/30',
  insuficiente: 'bg-wedo-orange/10 text-wedo-orange border-wedo-orange/30',
  critico: 'bg-status-error/10 text-status-error border-status-error/30',
}

function deriveBand(evaluation: JDEvaluationData): { band: string; bandLabel: string } {
  const band = evaluation.band ||
    (evaluation.score >= 90 ? 'excelente' :
     evaluation.score >= 70 ? 'bom' :
     evaluation.score >= 50 ? 'adequado' :
     evaluation.score >= 30 ? 'insuficiente' : 'critico')
  const bandLabel = evaluation.band_label ||
    (band === 'excelente' ? 'Excelente' :
     band === 'bom' ? 'Bom' :
     band === 'adequado' ? 'Adequado' :
     band === 'insuficiente' ? 'Insuficiente' : 'Crítico')
  return { band, bandLabel }
}

export const JDEvaluationHeader = React.memo(function JDEvaluationHeader({
  jobTitle,
  isExpanded,
  isEditing,
  evaluation,
  onToggleExpand,
  onStartEdit,
  canEdit,
}: JDEvaluationHeaderProps) {
  if (!isExpanded) {
    return (
      <div
        className="flex items-center justify-between px-4 py-3 bg-lia-bg-secondary cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-secondary" />
          <span className="text-base-ui font-semibold text-lia-text-primary">
            Descrição do Cargo
          </span>
          <span className="text-xs text-lia-text-tertiary">
            — {jobTitle}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {canEdit && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs px-3 border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
              onClick={(e) => {
                e.stopPropagation()
                onStartEdit()
              }}
            >
              <Pencil className="h-3 w-3 mr-1.5" />
              Editar Descrição
            </Button>
          )}
          <ChevronDown className="h-4 w-4 text-lia-text-tertiary" />
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Title bar */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-lia-bg-primary cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-secondary" />
          <span className="text-base-ui font-semibold text-lia-text-primary">Descrição do Cargo</span>
          <span className="text-xs text-lia-text-tertiary">— {jobTitle}</span>
        </div>
        <div className="flex items-center gap-2">
          {!isEditing && canEdit && (
            <Button
              variant="outline"
              size="sm"
              className="h-7 text-xs px-3 border-lia-border-default text-lia-text-secondary hover:bg-lia-interactive-hover"
              onClick={(e) => {
                e.stopPropagation()
                onStartEdit()
              }}
            >
              <Pencil className="h-3 w-3 mr-1.5" />
              Editar Descrição
            </Button>
          )}
          <ChevronUp className="h-4 w-4 text-lia-text-secondary" />
        </div>
      </div>

      {/* Summary row: score + band + suggestion (no D1–D9 grid — that lives in JDEvalCriteriaList) */}
      {evaluation && (() => {
        const { band, bandLabel } = deriveBand(evaluation)
        return (
          <div className="px-3 pt-3 pb-2 space-y-2 border-b border-lia-border-subtle">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-lia-text-primary">{evaluation.score}</span>
                <span className="text-micro text-lia-text-secondary">/100</span>
              </div>
              <span className={cn("text-micro font-semibold px-2 py-0.5 rounded-full border", BAND_COLORS[band] || BAND_COLORS.adequado)}>
                {bandLabel}
              </span>
              {band === 'critico' && (
                <span className="text-micro text-status-error font-medium flex items-center gap-1">
                  <XCircle className="w-3 h-3" />
                  JD bloqueado — geração de perguntas desabilitada
                </span>
              )}
            </div>
            <p className="text-micro text-lia-text-tertiary leading-relaxed">
              Mede os campos estruturados (responsabilidades, competências e
              critérios D1–D9), não o texto livre da descrição enriquecida (LIA).
            </p>
            {evaluation.lia_suggestion && (
              <div className={cn(
                "text-micro px-2.5 py-2 rounded-md border leading-relaxed",
                evaluation.can_generate
                  ? "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary/70"
                  : "bg-status-error/10 border-status-error/30 text-status-error"
              )}>
                {evaluation.lia_suggestion}
              </div>
            )}
          </div>
        )
      })()}
    </>
  )
})

export default JDEvaluationHeader
