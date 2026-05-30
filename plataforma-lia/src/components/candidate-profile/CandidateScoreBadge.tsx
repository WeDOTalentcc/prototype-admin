"use client"

import React, { memo } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { getWsiScoreColor } from "@/lib/wsi/visual"

/** Score format.  is @deprecated (legacy 0-100); prefer  or  (canonical 0-10 per Task #512). */
type ScoreFormat = "percent" | "decimal" | "wsi"

interface CandidateScoreBadgeProps {
  score: number | null | undefined
  label?: string
  format?: ScoreFormat
  size?: "sm" | "md"
  className?: string
}

function getScoreColor(score: number, format: ScoreFormat): string {
  // Task #512: WSI e decimal usam escala 0-10 via helper canônico
  // (WSI_VISUAL_3TIER: verde >=7.5, amarelo >=6.0, vermelho <6.0).
  if (format === "wsi" || format === "decimal") return getWsiScoreColor(score)
  if (score >= 80) return "text-status-success"
  if (score >= 60) return "text-wedo-orange"
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
  // F1 canonical: null/undefined score renders em-dash with gray class
  if (score == null) {
    return (
      <span
        aria-label={t("scoreUnavailable")}
        className={cn(
          "inline-flex items-center gap-1 font-medium",
          size === "sm" ? "text-xs" : "text-sm",
          "text-lia-text-secondary",
          className
        )}
      >
        {label && (
          <span className="text-lia-text-secondary font-normal">{label}</span>
        )}
        {"—"}
      </span>
    )
  }

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
