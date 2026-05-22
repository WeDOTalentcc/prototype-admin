"use client"

import React from "react"
import { Bot, Play, Pause, MoreVertical, Link2, TestTube2, Copy } from "lucide-react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
// Sprint B QW#15 audit 2026-05-22: 3-dot menu para Clone (era enterrado em drawer)
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { getCustomAgentStatusConfig } from "@/lib/agent-studio/status-config"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"
import { safeCategoryKey } from "./types"

interface AgentCardProps {
  agent: CustomAgent
  onTest: (agent: CustomAgent) => void
  onDeploy: (agent: CustomAgent) => void
  onToggleStatus: (agent: CustomAgent) => void
  /** Sprint B QW#15 audit 2026-05-22: Clone handler — opcional (caller decide se expõe) */
  onClone?: (agent: CustomAgent) => void
}

export function AgentCard({ agent, onTest, onDeploy, onToggleStatus, onClone }: AgentCardProps) {
  const t = useTranslations('agents.card')
  const tStatus = useTranslations('agents.status')
  const tCat = useTranslations('agents.customAgents')

  // UX-Sprint-A QW#18 Batch 3 (audit 2026-05-21): STATUS_STYLES extraído para
  // lib/agent-studio/status-config.ts canonical. Label fica local (i18n tStatus).
  const statusConfig = getCustomAgentStatusConfig(agent.status)
  const statusStyle = {
    label: tStatus(agent.status as "draft" | "active" | "paused" | "archived") || tStatus("draft"),
    badge: statusConfig.badge,
  }
  const category = safeCategoryKey(agent.domain)
  const categoryLabel = tCat('categories.' + category) || agent.domain || 'general'

  return (
    <div className={cn(cardStyles.default, "p-4 flex flex-col gap-3 relative")}>
      {/* Header */}
      <div className="flex items-start justify-between">
        {/* Sprint B QW#15 audit 2026-05-22: 3-dot menu via DropdownMenu shadcn */}
        {onClone && (
          <div className="absolute top-3 right-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="p-1 rounded-md text-lia-text-disabled hover:text-lia-text-primary hover:bg-lia-bg-tertiary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-lia-btn-primary-bg/30"
                  aria-label={t('moreActions') || 'Mais ações'}
                >
                  <MoreVertical className="w-4 h-4" aria-hidden="true" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-40">
                <DropdownMenuItem onClick={() => onClone(agent)} className="gap-2 cursor-pointer">
                  <Copy className="w-3.5 h-3.5" aria-hidden="true" />
                  {t('clone') || 'Duplicar'}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-wedo-cyan/10 flex items-center justify-center">
            <Bot className="w-4 h-4 text-wedo-cyan-dark" />
          </div>
          <div>
            <h4 className={cn(textStyles.subtitle, "text-sm font-semibold leading-tight")}>
              {agent.name}
            </h4>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn(badgeStyles.default, "text-[10px]")}>{categoryLabel}</span>
              <span className={cn(statusStyle.badge, "text-[10px]")}>{statusStyle.label}</span>
            </div>
          </div>
        </div>
        <BetaBadge size="sm" />
      </div>

      {/* Description */}
      {agent.description && (
        <p className={cn(textStyles.caption, "text-xs line-clamp-2")}>{agent.description}</p>
      )}

      {/* Metrics */}
      <div className="flex items-center gap-4 text-xs">
        <div>
          <span className="font-bold text-lia-text-primary font-inter">{agent.total_executions}</span>
          <span className="text-lia-text-disabled ml-1">{t('executions')}</span>
        </div>
        {agent.avg_confidence > 0 && (
          <div>
            <span className="font-bold text-lia-text-primary font-inter">{(agent.avg_confidence * 100).toFixed(0)}%</span>
            <span className="text-lia-text-disabled ml-1">{t('confidence')}</span>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-lia-border-subtle">
        <button
          type="button"
          onClick={() => onTest(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors"
        >
          <TestTube2 className="w-3.5 h-3.5" /> {t('test')}
        </button>
        <button
          type="button"
          onClick={() => onDeploy(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-wedo-cyan-dark hover:bg-wedo-cyan/10 transition-colors"
        >
          <Link2 className="w-3.5 h-3.5" /> {t('link')}
        </button>
        <button
          type="button"
          onClick={() => onToggleStatus(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors ml-auto"
        >
          {agent.status === "active" ? (
            <><Pause className="w-3.5 h-3.5" /> {t('pause')}</>
          ) : (
            <><Play className="w-3.5 h-3.5" /> {t('activate')}</>
          )}
        </button>
      </div>
    </div>
  )
}
