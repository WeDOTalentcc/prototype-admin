"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import {
  FileText, ChevronUp, ChevronDown,
  CheckCircle, AlertTriangle, XCircle,
  ClipboardList, Code, Heart, Briefcase,
  Pencil, ListChecks, Users
} from "lucide-react"
import { cn } from "@/lib/utils"

interface JDIndicator {
  label: string
  count?: number
  status: "sufficient" | "partial" | "insufficient"
  minimum?: number
  dimension?: string
  weight?: number
  earned?: number
  detail?: string
}

interface JDEvaluationData {
  score: number
  max_score: number
  band?: string
  band_label?: string
  indicators: JDIndicator[]
  lia_suggestion: string
  can_generate: boolean
  details: {
    responsibilities_count: number
    technical_skills_count: number
    behavioral_competencies_count: number
    seniority_defined: boolean
    has_description: boolean
  }
}

interface EnrichedJD {
  description?: string
  responsibilities?: string[]
  technical_skills?: string[]
  behavioral_competencies?: string[]
  generated_jd_text?: string
  updated_at?: string
}

interface JDEvaluationHeaderProps {
  jobTitle: string
  hasQuestions: boolean
  isExpanded: boolean
  isEditing: boolean
  evaluation: JDEvaluationData | null
  onToggleExpand: () => void
  onStartEdit: () => void
  onEditJD?: () => void
  canEdit: boolean
  // collapsed summary counts
  responsibilities: string[]
  technicalSkills: string[]
  behavioralCompetencies: string[]
  description?: string
}

function getStatusDotColor(status: string) {
  switch (status) {
    case "sufficient": return "bg-status-success"
    case "partial": return "bg-status-warning"
    case "insufficient": return "bg-status-error"
    default: return "bg-lia-border-medium"
  }
}

function getIndicatorIcon(label: string) {
  if (label.includes("Responsab")) return <ClipboardList className="h-3 w-3 text-lia-text-secondary" />
  if (label.includes("Técnica")) return <Code className="h-3 w-3 text-lia-text-secondary" />
  if (label.includes("Comportam")) return <Heart className="h-3 w-3 text-lia-text-secondary" />
  if (label.includes("Senior")) return <Briefcase className="h-3 w-3 text-lia-text-secondary" />
  return <FileText className="h-3 w-3 text-lia-text-secondary" />
}

export const JDEvaluationHeader = React.memo(function JDEvaluationHeader({
  jobTitle,
  hasQuestions,
  isExpanded,
  isEditing,
  evaluation,
  onToggleExpand,
  onStartEdit,
  onEditJD,
  canEdit,
  responsibilities,
  technicalSkills,
  behavioralCompetencies,
  description,
}: JDEvaluationHeaderProps) {
  if (!isExpanded) {
    return (
      <div
        className="flex items-center justify-between px-4 py-3 bg-lia-bg-secondary cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-secondary" />
          <span className="text-base-ui font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">
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
      {/* Expanded top bar */}
      <div
        className="flex items-center justify-between px-4 py-3 bg-lia-bg-primary cursor-pointer hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
        onClick={onToggleExpand}
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-lia-text-secondary" />
          <span className="text-base-ui font-semibold text-lia-text-primary font-['Open_Sans',sans-serif]">Descrição do Cargo</span>
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
          {hasQuestions && <ChevronUp className="h-4 w-4 text-lia-text-secondary" />}
        </div>
      </div>

      {/* Score + Indicators row (only shown when expanded and evaluation loaded) */}
      {evaluation && (
        <>
          {/* Band badge + score */}
          {(() => {
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
              <div className="flex items-center gap-3 pb-2 border-b border-lia-border-subtle px-3 pt-3">
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
            )
          })()}

          {/* 9-dimension grid */}
          {evaluation.indicators.some(i => i.dimension) && (
            <div className="grid grid-cols-3 gap-1.5 pb-2 border-b border-lia-border-subtle px-3 pt-2">
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
                    <AlertTriangle className="w-3 h-3 text-status-warning shrink-0" />
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

          {/* Compact row fallback */}
          {!evaluation.indicators.some(i => i.dimension) && (
            <div className="flex items-center gap-3 pb-2 border-b border-lia-border-subtle flex-wrap px-3 pt-2">
              {evaluation.indicators.map((indicator) => (
                <div key={indicator.label} className="flex items-center gap-1.5">
                  {getIndicatorIcon(indicator.label)}
                  <span className="text-micro text-lia-text-secondary">{indicator.label}:</span>
                  <span className="text-xs font-semibold text-lia-text-primary">{indicator.count ?? 0}</span>
                  <span className={cn("w-1.5 h-1.5 rounded-full", getStatusDotColor(indicator.status))} />
                </div>
              ))}
            </div>
          )}

          {/* Suggestion */}
          {evaluation.lia_suggestion && (
            <div className={cn(
              "text-micro px-2.5 py-2 rounded-md border leading-relaxed mx-3 mt-2",
              evaluation.can_generate
                ? "bg-lia-bg-secondary border-lia-border-subtle text-lia-text-secondary/50"
                : "bg-status-error/10 border-status-error/30 text-status-error dark:bg-status-error/10 dark:border-status-error/30 dark:text-status-error"
            )}>
              {evaluation.lia_suggestion}
            </div>
          )}
        </>
      )}
    </>
  )
})

export default JDEvaluationHeader
