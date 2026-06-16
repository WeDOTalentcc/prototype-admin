"use client"

import React, { useState, useCallback } from "react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ChevronDown, ChevronUp, Brain, Loader2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useScoreBreakdown } from "@/hooks/candidates/use-score-breakdown"

interface ScoreDimension {
  label: string
  value: number
  maxValue?: number
}

interface ScoreBreakdownBadgeProps {
  score: number
  breakdown?: {
    skills?: number
    experience?: number
    culture_fit?: number
    education?: number
    availability?: number
  }
  explanation?: string
  size?: "sm" | "md" | "lg"
  showExpand?: boolean
  className?: string
}

const DEFAULT_DIMENSIONS: ScoreDimension[] = [
  { label: "Skills Técnicas", value: 0 },
  { label: "Experiência", value: 0 },
  { label: "Aderência Cultural", value: 0 },
  { label: "Formação", value: 0 },
  { label: "Disponibilidade", value: 0 },
]

function getScoreColor(score: number): string {
  if (score >= 80) return "text-status-success dark:text-status-success"
  if (score >= 60) return "text-status-warning dark:text-status-warning"
  return "text-status-error dark:text-status-error"
}

function getBarColor(score: number): string {
  if (score >= 80) return "bg-status-success"
  if (score >= 60) return "bg-status-warning"
  return "bg-status-error"
}

function getBarBgColor(score: number): string {
  if (score >= 80) return "bg-status-success/15"
  if (score >= 60) return "bg-status-warning/15 dark:bg-status-warning/30"
  return "bg-status-error/15 dark:bg-status-error/30"
}

function ProgressBar({ value, label, maxValue = 100 }: ScoreDimension) {
  const percentage = Math.min(100, Math.round((value / maxValue) * 100))
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between">
        <span className="text-micro text-lia-text-secondary">{label}</span>
        <span className={cn("text-micro font-semibold", getScoreColor(percentage))}>{percentage}%</span>
      </div>
      <div className={cn("h-1.5 rounded-full w-full", getBarBgColor(percentage))}>
        <div
          className={cn("h-1.5 rounded-full transition-[width,height] duration-500", getBarColor(percentage))}
          style={{width: `${percentage}%`}}
        />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// E1 — ScoreBreakdownBadgeLazy: lazy-load via API (job + candidate)
// ---------------------------------------------------------------------------

interface ScoreBreakdownBadgeLazyProps {
  score: number
  jobId: string
  candidateId: string
  size?: "sm" | "md" | "lg"
  className?: string
}

export function ScoreBreakdownBadgeLazy({
  score,
  jobId,
  candidateId,
  size = "md",
  className,
}: ScoreBreakdownBadgeLazyProps) {
  const { data, loading, error, fetch, reset } = useScoreBreakdown()
  const [open, setOpen] = useState(false)

  const handleOpenChange = useCallback(
    (isOpen: boolean) => {
      setOpen(isOpen)
      if (isOpen && !data && !loading) {
        fetch(jobId, candidateId)
      }
      if (!isOpen) {
        reset()
      }
    },
    [data, loading, fetch, reset, jobId, candidateId]
  )

  const sizeClasses = { sm: "text-sm font-semibold", md: "text-lg font-semibold", lg: "text-2xl font-semibold" }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          className={cn(
 "inline-flex items-center gap-1 cursor-pointer select-none rounded-md hover:opacity-80 transition-opacity motion-reduce:transition-none",
            sizeClasses[size],
            getScoreColor(score),
            className
          )}
          aria-label={`Score ${Math.round(score)} — clique para detalhamento`}
        >
          <span>{Math.round(score)}</span>
          <ChevronDown className="h-3 w-3 opacity-60" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-3" side="left" align="start">
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 pb-2 dark:border-lia-border-subtle">
            <Brain className="h-3.5 w-3.5 text-wedo-cyan-dark" />
            <span className="text-xs font-semibold text-lia-text-primary">
              Score LIA: {Math.round(score)}
            </span>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
              <span className="ml-2 text-xs text-lia-text-secondary">Carregando...</span>
            </div>
          )}

          {error && !loading && (
            <div className="flex items-center gap-1.5 py-2 text-xs text-lia-text-secondary">
              <AlertCircle className="h-3.5 w-3.5 text-status-warning" />
              <span>{error}</span>
            </div>
          )}

          {data && !loading && (
            <>
              {data.strengths.length > 0 && (
                <div>
                  <p className="text-micro font-semibold text-lia-text-secondary mb-1">
                    Pontos fortes
                  </p>
                  <ul className="space-y-0.5">
                    {data.strengths.slice(0, 3).map((s, i) => (
                      <li key={i} className="text-micro text-lia-text-secondary flex gap-1">
                        <span className="text-status-success mt-0.5">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.concerns.length > 0 && (
                <div>
                  <p className="text-micro font-semibold text-lia-text-secondary mb-1">
                    Pontos de atenção
                  </p>
                  <ul className="space-y-0.5">
                    {data.concerns.slice(0, 3).map((c, i) => (
                      <li key={i} className="text-micro text-lia-text-secondary flex gap-1">
                        <span className="text-status-warning mt-0.5">•</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.reasoning && (
                <div className="pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                  <p className="text-micro text-lia-text-tertiary leading-relaxed line-clamp-3">
                    {data.reasoning}
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

// ---------------------------------------------------------------------------
// Original ScoreBreakdownBadge (static, kept for backward compatibility)
// ---------------------------------------------------------------------------

export function ScoreBreakdownBadge({
  score,
  breakdown,
  explanation,
  size = "md",
  showExpand = true,
  className,
}: ScoreBreakdownBadgeProps) {
  const [expanded, setExpanded] = useState(false)

  const dimensions: ScoreDimension[] = breakdown
    ? [
        { label: "Skills Técnicas", value: breakdown.skills ?? 0 },
        { label: "Experiência", value: breakdown.experience ?? 0 },
        { label: "Aderência Cultural", value: breakdown.culture_fit ?? 0 },
        { label: "Formação", value: breakdown.education ?? 0 },
        { label: "Disponibilidade", value: breakdown.availability ?? 0 },
      ]
    : DEFAULT_DIMENSIONS

  const sizeClasses = {
    sm: "text-sm font-bold",
    md: "text-lg font-semibold",
    lg: "text-2xl font-semibold",
  }

  const badgeContent = (
    <div
      className={cn(
 "inline-flex items-center gap-1 cursor-pointer select-none",
        sizeClasses[size],
        getScoreColor(score),
        className
      )}
      onClick={showExpand ? () => setExpanded(!expanded) : undefined}
    >
      <span>{Math.round(score)}</span>
      {showExpand && breakdown && (
        expanded 
          ? <ChevronUp className="h-3 w-3 opacity-60" /> 
          : <ChevronDown className="h-3 w-3 opacity-60" />
      )}
    </div>
  )

  return (
    <div className="inline-block">
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            {badgeContent}
          </TooltipTrigger>
          <TooltipContent className="w-56 p-3" side="left">
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 mb-2">
                <Brain className="h-3.5 w-3.5 text-wedo-cyan-dark" />
                <span className="text-xs font-semibold text-lia-text-primary">
                  Score LIA: {Math.round(score)}
                </span>
              </div>
              {dimensions.map((dim) => (
                <ProgressBar key={dim.label} {...dim} />
              ))}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      {expanded && showExpand && (
        <div className="mt-2 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-lg border border-lia-border-subtle dark:border-lia-border-subtle max-w-xs">
          <div className="space-y-2 mb-3">
            {dimensions.map((dim) => (
              <ProgressBar key={dim.label} {...dim} />
            ))}
          </div>
          {explanation && (
            <div className="pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start gap-1.5">
                <Brain className="h-3.5 w-3.5 text-wedo-cyan-dark mt-0.5 flex-shrink-0" />
                <p className="text-micro text-lia-text-secondary leading-relaxed">
                  {explanation}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

ScoreBreakdownBadge.displayName = 'ScoreBreakdownBadge'
ScoreBreakdownBadgeLazy.displayName = 'ScoreBreakdownBadgeLazy'
ProgressBar.displayName = 'ProgressBar'
