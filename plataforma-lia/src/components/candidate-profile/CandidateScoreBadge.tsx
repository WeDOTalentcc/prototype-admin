"use client"

import React, { memo } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"

type ScoreFormat = "percent" | "decimal" | "wsi"

interface CandidateScoreBadgeProps {
  score: number | null | undefined
  label?: string
  format?: ScoreFormat
  size?: "sm" | "md"
  className?: string
}

function getScoreColor(score: number, format: ScoreFormat): string {
  // WSI já é 0-10 (Task #512). `decimal` também é 0-10. `percent` é 0-100.
  const normalized = format === "wsi" || format === "decimal" ? score * 10 : score
  if (normalized >= 80) return "text-status-success"
  if (normalized >= 60) return "text-wedo-orange"
  return "text-status-error"
}

function formatScore(score: number, format: ScoreFormat): string {
  switch (format) {
    case "wsi":
      return `${score.toFixed(1)}/10`
    case "decimal":
      return `${score.toFixed(1)}/10`
    case "percent":
    default:
      return `${Math.round(score)}%`
  }
}

const CandidateScoreBadge = memo(function CandidateScoreBadge({
  score,
  label,
  format = "percent",
  size = "sm",
  className,
}: CandidateScoreBadgeProps) {
  const t = useTranslations('candidates.profile')
  if (score == null) return null

  const colorClass = getScoreColor(score, format)
  const formattedScore = formatScore(score, format)

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-medium",
        size === "sm" ? "text-xs" : "text-sm",
        colorClass,
        className
      )}
    >
      {label && (
        <span className="text-lia-text-secondary font-normal">{label}</span>
      )}
      {formattedScore}
    </span>
  )
})

CandidateScoreBadge.displayName = "CandidateScoreBadge"

export { CandidateScoreBadge, getScoreColor, formatScore }
export type { CandidateScoreBadgeProps, ScoreFormat }
