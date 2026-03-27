"use client"

import React, { useState, useCallback } from "react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { ChevronDown, ChevronUp, Brain, Loader2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useScoreBreakdown } from "@/hooks/use-score-breakdown"

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
  { label: "Fit Cultural", value: 0 },
  { label: "Formação", value: 0 },
  { label: "Disponibilidade", value: 0 },
]

function getScoreColor(score: number): string {
  if (score >= 80) return "text-emerald-600 dark:text-emerald-400"
  if (score >= 60) return "text-amber-600 dark:text-amber-400"
  return "text-red-600 dark:text-red-400"
}

function getBarColor(score: number): string {
  if (score >= 80) return "bg-emerald-500"
  if (score >= 60) return "bg-amber-500"
  return "bg-red-500"
}

function getBarBgColor(score: number): string {
  if (score >= 80) return "bg-emerald-100 dark:bg-emerald-900/30"
  if (score >= 60) return "bg-amber-100 dark:bg-amber-900/30"
  return "bg-red-100 dark:bg-red-900/30"
}

function ProgressBar({ value, label, maxValue = 100 }: ScoreDimension) {
  const percentage = Math.min(100, Math.round((value / maxValue) * 100))
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-600 dark:text-gray-400">{label}</span>
        <span className={cn("text-[10px] font-semibold", getScoreColor(percentage))}>{percentage}%</span>
      </div>
      <div className={cn("h-1.5 rounded-full w-full", getBarBgColor(percentage))}>
        <div
          className={cn("h-1.5 rounded-full transition-all duration-500", getBarColor(percentage))}
          style={{ width: `${percentage}%` }}
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

  const sizeClasses = { sm: "text-sm font-bold", md: "text-lg font-bold", lg: "text-2xl font-bold" }

  return (
    <Popover open={open} onOpenChange={handleOpenChange}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "inline-flex items-center gap-1 cursor-pointer select-none rounded hover:opacity-80 transition-opacity",
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
          <div className="flex items-center gap-1.5 pb-2 border-b border-gray-200 dark:border-gray-700">
            <Brain className="h-3.5 w-3.5 text-wedo-cyan-dark" />
            <span className="text-[11px] font-semibold text-gray-900 dark:text-gray-100">
              Score LIA: {Math.round(score)}
            </span>
          </div>

          {loading && (
            <div className="flex items-center justify-center py-4">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
              <span className="ml-2 text-[11px] text-gray-500">Carregando...</span>
            </div>
          )}

          {error && !loading && (
            <div className="flex items-center gap-1.5 py-2 text-[11px] text-gray-500">
              <AlertCircle className="h-3.5 w-3.5 text-amber-500" />
              <span>{error}</span>
            </div>
          )}

          {data && !loading && (
            <>
              {data.strengths.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Pontos fortes
                  </p>
                  <ul className="space-y-0.5">
                    {data.strengths.slice(0, 3).map((s, i) => (
                      <li key={i} className="text-[10px] text-gray-600 dark:text-gray-400 flex gap-1">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.concerns.length > 0 && (
                <div>
                  <p className="text-[10px] font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Pontos de atenção
                  </p>
                  <ul className="space-y-0.5">
                    {data.concerns.slice(0, 3).map((c, i) => (
                      <li key={i} className="text-[10px] text-gray-600 dark:text-gray-400 flex gap-1">
                        <span className="text-amber-500 mt-0.5">•</span>
                        <span>{c}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {data.reasoning && (
                <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                  <p className="text-[10px] text-gray-500 dark:text-gray-400 leading-relaxed line-clamp-3">
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
        { label: "Fit Cultural", value: breakdown.culture_fit ?? 0 },
        { label: "Formação", value: breakdown.education ?? 0 },
        { label: "Disponibilidade", value: breakdown.availability ?? 0 },
      ]
    : DEFAULT_DIMENSIONS

  const sizeClasses = {
    sm: "text-sm font-bold",
    md: "text-lg font-bold",
    lg: "text-2xl font-bold",
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
                <span className="text-[11px] font-semibold text-gray-900 dark:text-gray-100">
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
        <div className="mt-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 max-w-xs">
          <div className="space-y-2 mb-3">
            {dimensions.map((dim) => (
              <ProgressBar key={dim.label} {...dim} />
            ))}
          </div>
          {explanation && (
            <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-start gap-1.5">
                <Brain className="h-3.5 w-3.5 text-wedo-cyan-dark mt-0.5 flex-shrink-0" />
                <p className="text-[10px] text-gray-600 dark:text-gray-400 leading-relaxed">
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
