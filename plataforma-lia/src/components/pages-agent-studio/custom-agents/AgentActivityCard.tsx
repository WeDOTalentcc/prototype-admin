"use client"

import React from "react"
import { Bot, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"

interface AgentActivityCardProps {
  agentName: string
  candidatesProcessed: number
  candidatesFit: number
  totalCandidates: number
  isActive: boolean
  onViewDetails?: () => void
}

export function AgentActivityCard({
  agentName,
  candidatesProcessed,
  candidatesFit,
  totalCandidates,
  isActive,
  onViewDetails,
}: AgentActivityCardProps) {
  const t = useTranslations('agents.customAgents')
  const progress = totalCandidates > 0 ? Math.round((candidatesProcessed / totalCandidates) * 100) : 0

  return (
    <div className={cn(cardStyles.compact, "space-y-2")}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-graphite" />
          <span className="text-xs font-semibold text-lia-text-primary">{agentName}</span>
        </div>
        <div className="flex items-center gap-1">
          {isActive && <Zap className="w-3 h-3 text-emerald-500" />}
          <BetaBadge size="sm" />
        </div>
      </div>

      <p className="text-[10px] text-lia-text-secondary">
        {t('screened')} <span className="font-bold font-inter">{candidatesProcessed}</span> {t('cvs')}
        {" · "}
        <span className="font-bold font-inter text-emerald-600">{candidatesFit}</span> {t('fit')}
      </p>

      {/* Progress bar */}
      <div className="w-full bg-lia-bg-tertiary rounded-full h-1.5">
        <div
          className="bg-graphite h-1.5 rounded-full transition-colors duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-xs text-lia-text-secondary">{progress}% {t('processed')}</span>
        {onViewDetails && (
          <button
            type="button"
            onClick={onViewDetails}
            className="text-[10px] text-graphite hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
          >
            {t('viewDetailsShort')}
          </button>
        )}
      </div>
    </div>
  )
}
