"use client"

import React from "react"
import { Bot, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { badgeStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import { StudioCardShell } from "@/components/pages-agent-studio/StudioCardShell"

interface AgentActivityCardProps {
  agentName: string
  candidatesProcessed: number
  candidatesFit: number
  totalCandidates: number
  isActive: boolean
  onViewDetails?: () => void
}

/**
 * AgentActivityCard — refactor cosmetico canonical (2026-05-26).
 * Consome StudioCardShell tone="elevated" seguindo pattern Agent C (7f3b23fc7).
 * Preserva 100% das features: progress bar, candidatos processed/fit, isActive badge.
 */
export function AgentActivityCard({
  agentName,
  candidatesProcessed,
  candidatesFit,
  totalCandidates,
  isActive,
  onViewDetails,
}: AgentActivityCardProps) {
  const t = useTranslations("agents.customAgents")
  const progress =
    totalCandidates > 0 ? Math.round((candidatesProcessed / totalCandidates) * 100) : 0

  const statusBadge = isActive ? (
    <span className={cn(badgeStyles.success, "text-[10px] inline-flex items-center gap-1")}>
      <Zap className="w-3 h-3" aria-hidden="true" />
      {t("statuses.active") || "Ativo"}
    </span>
  ) : undefined

  const bodySlot = (
    <div className="space-y-2">
      <p className="text-[11px] text-lia-text-secondary">
        {t("screened")}{" "}
        <span className="font-bold font-sans text-lia-text-primary">{candidatesProcessed}</span>{" "}
        {t("cvs")}
        {" · "}
        <span className="font-bold font-sans text-emerald-600">{candidatesFit}</span> {t("fit")}
      </p>
      <div className="w-full bg-lia-bg-tertiary rounded-full h-1.5">
        <div
          className="bg-graphite h-1.5 rounded-full transition-colors duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-lia-text-secondary">
          {progress}% {t("processed")}
        </span>
        {onViewDetails && (
          <button
            type="button"
            onClick={onViewDetails}
            className="text-[11px] text-graphite hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
          >
            {t("viewDetailsShort")}
          </button>
        )}
      </div>
    </div>
  )

  return (
    <StudioCardShell
      tone="elevated"
      icon={<Bot className="w-4 h-4 text-graphite" aria-hidden="true" />}
      title={agentName}
      badges={<BetaBadge size="sm" />}
      statusBadge={statusBadge}
      bodySlot={bodySlot}
      data-testid="agent-activity-card"
    />
  )
}
