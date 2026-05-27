"use client"

import React, { useState } from "react"
import { Brain, AlertTriangle, AlertCircle, CheckCircle2, Clock, ChevronDown, ChevronUp, Lightbulb, BarChart3 } from "lucide-react"
import { cn } from "@/lib/utils"

interface ParecerSection {
  title: string
  status: "good" | "attention" | "missing"
  items: string[]
  suggestions?: string[]
}

interface MarketComparison {
  field: string
  yourValue: string
  marketValue: string
  status: "above" | "aligned" | "below"
}

export interface ParecerLIAData {
  overallNota: number
  completenessNota: number
  /** Alias canonical (acessado pela UI). Optional pra retro-compat. */
  overallScore?: number
  completenessScore?: number
  sections: ParecerSection[]
  marketComparisons?: MarketComparison[]
  timeToFillEstimate?: {
    days: number
    rangeMin: number
    rangeMax: number
    confidence: number
  }
  similarJobsCount?: number
  dataSourcesUsed?: string[]
  recommendations: string[]
}

interface ParecerLIACardProps {
  data: ParecerLIAData
  onAcceptSuggestion?: (suggestion: string) => void
  className?: string
}

function ScoreCircle({ score }: { score: number }) {
  const radius = 28
  const stroke = 4
  const normalizedRadius = radius - stroke / 2
  const circumference = normalizedRadius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  const scoreColor = "text-wedo-cyan"

  return (
    <div className="relative flex items-center justify-center w-[60px] h-[60px]">
      <svg width={radius * 2} height={radius * 2} className="-rotate-90" aria-hidden="true">
        <circle
          stroke="currentColor"
          className="text-lia-text-disabled"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke="currentColor"
          fill="transparent"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          className="text-wedo-cyan transition-colors motion-reduce:transition-none duration-700 ease-out"
        />
      </svg>
      <span className={cn("absolute font-['Inter',sans-serif] text-sm font-semibold tabular-nums", scoreColor)}>
        {score}%
      </span>
    </div>
  )
}

function CompletenessBar({ score }: { score: number }) {
  const barColor = "bg-wedo-cyan"

  return (
    <div className="flex items-center gap-2 flex-1">
      <span className="text-micro font-medium text-lia-text-secondary whitespace-nowrap">Completude</span>
      <div className="flex-1 h-1.5 bg-lia-interactive-active rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-[width,height] duration-700 ease-out", barColor)}
          style={{width: `${score}%`}}
        />
      </div>
      <span className="font-['Inter',sans-serif] text-micro font-medium tabular-nums text-lia-text-secondary">
        {score}%
      </span>
    </div>
  )
}

const sectionStatusConfig = {
  good: {
    icon: CheckCircle2,
    iconColor: "text-wedo-cyan",
    textColor: "text-lia-text-primary",
    bg: "bg-lia-bg-secondary/50",
    border: "border-lia-border-subtle",
    extraBorder: "",
  },
  attention: {
    icon: AlertTriangle,
    iconColor: "text-lia-text-secondary",
    textColor: "text-lia-text-secondary",
    bg: "bg-lia-bg-tertiary/50/30",
    border: "border-lia-border-default",
    extraBorder: "",
  },
  missing: {
    icon: AlertCircle,
    iconColor: "text-lia-text-tertiary",
    textColor: "text-lia-text-secondary",
    bg: "bg-lia-bg-tertiary/20",
    border: "border-lia-border-default",
    extraBorder: "border-dashed",
  },
}

const marketStatusColor = {
  above: "text-wedo-cyan-dark",
  aligned: "text-lia-text-secondary",
  below: "text-lia-text-primary font-semibold",
}

export function ParecerLIACard({ data, onAcceptSuggestion, className }: ParecerLIACardProps) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className={cn(
      "rounded-md border border-wedo-cyan/30 bg-gradient-to-br from-cyan-500/5 to-transparent dark:from-cyan-500/10 p-4 mt-3",
      className
    )}>
      <div className="flex items-start gap-3">
        <ScoreCircle score={data.overallScore ?? data.overallNota} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="w-4 h-4 text-wedo-cyan flex-shrink-0" />
            <span className="text-xs font-semibold text-lia-text-primary uppercase tracking-wide">
              Parecer IA
            </span>
          </div>
          <CompletenessBar score={data.completenessScore ?? data.completenessNota} />
        </div>
      </div>

      {!expanded && data.recommendations.length > 0 && (
        <div className="mt-3 flex items-start gap-2">
          <Brain className="w-3.5 h-3.5 text-wedo-cyan flex-shrink-0 mt-0.5" />
          <p className="text-xs text-lia-text-primary line-clamp-2">
            {data.recommendations[0]}
          </p>
        </div>
      )}

      <button
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
        aria-label={expanded ? "Ocultar detalhes do parecer LIA" : "Ver análise completa do parecer LIA"}
        className="mt-3 flex items-center gap-1.5 text-xs font-medium text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-lia-border-default rounded-md"
      >
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        {expanded ? "Ocultar detalhes" : "Ver análise completa"}
      </button>

      {expanded && (
        <div className="mt-3 space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {data.sections.map((section, idx) => {
              const config = sectionStatusConfig[section.status]
              const Icon = config.icon
              return (
                <div key={idx} className={cn("rounded-md p-3 border", config.bg, config.border, config.extraBorder)}>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Icon className={cn("w-3.5 h-3.5", config.iconColor)} />
                    <span className="text-xs font-semibold text-lia-text-primary">
                      {section.title}
                    </span>
                  </div>
                  <ul className="space-y-0.5 ml-5">
                    {section.items.map((item, i) => (
                      <li key={`item-${i}`} className="text-micro text-lia-text-secondary list-disc">
                        {item}
                      </li>
                    ))}
                  </ul>
                  {section.suggestions && section.suggestions.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-lia-border-subtle/50/50 space-y-1">
                      {section.suggestions.map((sug, i) => (
                        <div key={`sug-${i}`} className="flex items-start gap-1.5">
                          <Lightbulb className="w-3 h-3 text-lia-text-tertiary flex-shrink-0 mt-0.5" />
                          <span className="text-micro text-lia-text-secondary flex-1">
                            {sug}
                          </span>
                          {onAcceptSuggestion && (
                            <button
                              onClick={() => onAcceptSuggestion(sug)}
                              aria-label={`Aplicar sugestão: ${sug.slice(0, 50)}`}
                              className="text-micro font-medium text-lia-text-secondary hover:text-lia-text-primary hover:underline flex-shrink-0 focus:outline-none focus-visible:ring-1 focus-visible:ring-lia-border-default rounded-md"
                            >
                              Aplicar
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {data.marketComparisons && data.marketComparisons.length > 0 && (
            <div className="rounded-xl bg-lia-bg-primary/60/40 p-3">
              <div className="flex items-center gap-1.5 mb-2">
                <BarChart3 className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Comparativo de Mercado
                </span>
              </div>
              <div className="space-y-1">
                <div className="grid grid-cols-3 gap-2 text-micro font-medium text-lia-text-tertiary uppercase tracking-wider pb-1/50/50">
                  <span>Campo</span>
                  <span>Sua vaga</span>
                  <span>Mercado</span>
                </div>
                {data.marketComparisons.map((comp, idx) => (
                  <div key={`comp-${idx}`} className="grid grid-cols-3 gap-2 py-1">
                    <span className="text-micro text-lia-text-secondary">
                      {comp.field}
                    </span>
                    <span className={cn("text-micro font-medium font-['Inter',sans-serif] tabular-nums", marketStatusColor[comp.status])}>
                      {comp.yourValue}
                    </span>
                    <span className="text-micro text-lia-text-secondary font-['Inter',sans-serif] tabular-nums">
                      {comp.marketValue}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {data.timeToFillEstimate && (
            <div className="rounded-xl bg-lia-bg-primary/60/40 p-3">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Clock className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Tempo estimado para preenchimento
                </span>
              </div>
              <div className="flex items-baseline gap-1.5">
                <span className="font-['Inter',sans-serif] text-lg font-semibold text-lia-text-primary tabular-nums">
                  {data.timeToFillEstimate.days}
                </span>
                <span className="text-micro text-lia-text-secondary">dias</span>
                <span className="text-micro text-lia-text-tertiary ml-1">
                  ({data.timeToFillEstimate.rangeMin}-{data.timeToFillEstimate.rangeMax} dias)
                </span>
              </div>
              <div className="flex items-center gap-1 mt-1">
                <span className="text-micro text-lia-text-tertiary">Confiança:</span>
                <span className="font-['Inter',sans-serif] text-micro font-medium tabular-nums text-lia-text-secondary">
                  {data.timeToFillEstimate.confidence}%
                </span>
              </div>
            </div>
          )}

          <div className="rounded-xl bg-lia-bg-primary/60/40 p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
              <span className="text-xs font-semibold text-lia-text-primary">
                Recomendações
              </span>
            </div>
            <ol className="space-y-1 ml-4">
              {data.recommendations.map((rec, idx) => (
                <li key={`rec-${idx}`} className="text-micro text-lia-text-secondary list-decimal">
                  {rec}
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}

      {data.dataSourcesUsed && data.dataSourcesUsed.length > 0 && (
        <p className="text-micro text-lia-text-tertiary mt-3 italic">
          Baseado em: {data.dataSourcesUsed.join(", ")}
        </p>
      )}
    </div>
  )
}
