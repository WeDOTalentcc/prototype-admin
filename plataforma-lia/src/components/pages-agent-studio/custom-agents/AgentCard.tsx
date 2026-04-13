"use client"

import React from "react"
import { Bot, Play, Pause, MoreVertical, Link2, TestTube2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { cardStyles, badgeStyles, textStyles } from "@/lib/design-tokens"
import { BetaBadge } from "@/components/ui/beta-badge"
import type { CustomAgent } from "./types"
import { CATEGORY_LABELS } from "./types"

const STATUS_STYLES: Record<string, { label: string; badge: string }> = {
  draft: { label: "Rascunho", badge: badgeStyles.default },
  active: { label: "Ativo", badge: badgeStyles.success },
  paused: { label: "Pausado", badge: badgeStyles.warning },
  archived: { label: "Arquivado", badge: badgeStyles.error },
}

interface AgentCardProps {
  agent: CustomAgent
  onTest: (agent: CustomAgent) => void
  onDeploy: (agent: CustomAgent) => void
  onToggleStatus: (agent: CustomAgent) => void
}

export function AgentCard({ agent, onTest, onDeploy, onToggleStatus }: AgentCardProps) {
  const statusStyle = STATUS_STYLES[agent.status] || STATUS_STYLES.draft
  const category = (agent.domain || "general") as keyof typeof CATEGORY_LABELS
  const categoryLabel = CATEGORY_LABELS[category] || agent.domain

  return (
    <div className={cn(cardStyles.default, "p-4 flex flex-col gap-3")}>
      {/* Header */}
      <div className="flex items-start justify-between">
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
          <span className="text-lia-text-disabled ml-1">execucoes</span>
        </div>
        {agent.avg_confidence > 0 && (
          <div>
            <span className="font-bold text-lia-text-primary font-inter">{(agent.avg_confidence * 100).toFixed(0)}%</span>
            <span className="text-lia-text-disabled ml-1">confianca</span>
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
          <TestTube2 className="w-3.5 h-3.5" /> Testar
        </button>
        <button
          type="button"
          onClick={() => onDeploy(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-wedo-cyan-dark hover:bg-wedo-cyan/10 transition-colors"
        >
          <Link2 className="w-3.5 h-3.5" /> Vincular
        </button>
        <button
          type="button"
          onClick={() => onToggleStatus(agent)}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-lia-text-secondary hover:bg-lia-bg-tertiary transition-colors ml-auto"
        >
          {agent.status === "active" ? (
            <><Pause className="w-3.5 h-3.5" /> Pausar</>
          ) : (
            <><Play className="w-3.5 h-3.5" /> Ativar</>
          )}
        </button>
      </div>
    </div>
  )
}
