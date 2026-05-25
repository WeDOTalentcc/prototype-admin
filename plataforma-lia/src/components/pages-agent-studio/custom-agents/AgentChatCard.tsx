"use client"

import React from "react"
import { Bot, Activity, Clock, Zap } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"

interface AgentChatCardProps {
  agent: CustomAgent
  deploymentCount?: number
  onViewDetails?: () => void
}

export function AgentChatCard({ agent, deploymentCount = 0, onViewDetails }: AgentChatCardProps) {
  const t = useTranslations('agents.customAgents')
  const domainLabel = t('categories.' + agent.domain) || agent.domain
  const statusBadge = agent.status === "active" ? badgeStyles.success :
                      agent.status === "paused" ? badgeStyles.warning :
                      badgeStyles.default

  return (
    <div className={cn(cardStyles.default, "p-3 space-y-2 max-w-md")}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-powder flex items-center justify-center">
            <Bot className="w-4 h-4 text-graphite" />
          </div>
          <div>
            <p className="text-sm font-semibold text-lia-text-primary">{agent.name}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn(badgeStyles.default, "text-[10px]")}>{domainLabel}</span>
              <span className={cn(statusBadge, "text-[10px]")}>{t('statuses.' + agent.status) || agent.status}</span>
            </div>
          </div>
        </div>
        <BetaBadge size="sm" />
      </div>

      {agent.description && (
        <p className="text-[11px] text-lia-text-secondary line-clamp-2">{agent.description}</p>
      )}

      <div className="grid grid-cols-3 gap-2 text-xs">
        <div className="flex items-center gap-1">
          <Activity className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">{agent.total_executions}</span>
          <span className="text-xs text-lia-text-secondary">{t('execLabel')}</span>
        </div>
        <div className="flex items-center gap-1">
          <Zap className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">{deploymentCount}</span>
          <span className="text-xs text-lia-text-secondary">{t('vinc')}</span>
        </div>
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3 text-lia-text-disabled" />
          <span className="font-bold font-inter text-lia-text-primary">
            {agent.avg_confidence > 0 ? `${(agent.avg_confidence * 100).toFixed(0)}%` : "-"}
          </span>
          <span className="text-xs text-lia-text-secondary">{t('conf')}</span>
        </div>
      </div>

      {onViewDetails && (
        <button
          type="button"
          onClick={onViewDetails}
          className="w-full text-[11px] text-graphite hover:underline text-left pt-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
        >
          {t('viewDetails')}
        </button>
      )}
    </div>
  )
}


interface MetricsSummaryCardProps {
  period_days: number
  total_executions: number
  total_tokens: number
  estimated_cost_brl: number
  avg_confidence: number
  active_agents: number
  top_agents: Array<{ agent_id: string; agent_name: string; execution_count: number; total_tokens: number }>
}

export function MetricsSummaryCard({
  period_days,
  total_executions,
  total_tokens,
  estimated_cost_brl,
  avg_confidence,
  active_agents,
  top_agents,
}: MetricsSummaryCardProps) {
  const t = useTranslations('agents.customAgents')
  return (
    <div className={cn(cardStyles.default, "p-3 space-y-3 max-w-md")}>
      <div className="flex items-center gap-2">
        <Activity className="w-4 h-4 text-graphite" />
        <p className="text-sm font-semibold text-lia-text-primary">{t('metricsTitle', { days: period_days })}</p>
        <BetaBadge size="sm" />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-xs text-lia-text-secondary uppercase">{t('executionsMetric')}</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{total_executions}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-xs text-lia-text-secondary uppercase">{t('activeAgentsMetric')}</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{active_agents}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-xs text-lia-text-secondary uppercase">{t('tokensMetric')}</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">{total_tokens.toLocaleString()}</p>
        </div>
        <div className={cn(cardStyles.flat, "p-2")}>
          <p className="text-xs text-lia-text-secondary uppercase">{t('estimatedCost')}</p>
          <p className="text-lg font-bold font-inter text-lia-text-primary">R${estimated_cost_brl.toFixed(4)}</p>
        </div>
      </div>

      {top_agents.length > 0 && (
        <div>
          <p className="text-xs text-lia-text-secondary uppercase mb-1.5">{t('topAgents')}</p>
          <div className="space-y-1">
            {top_agents.map((a, i) => (
              <div key={a.agent_id} className="flex items-center justify-between text-xs">
                <span className="text-lia-text-primary">{i + 1}. {a.agent_name}</span>
                <span className="text-xs text-lia-text-secondary">
                  {a.execution_count} {t('execLabel')} · {a.total_tokens.toLocaleString()} tkn
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {avg_confidence > 0 && (
        <p className="text-xs text-lia-text-secondary">
          {t('avgConfidence')}: {(avg_confidence * 100).toFixed(0)}%
        </p>
      )}
    </div>
  )
}
