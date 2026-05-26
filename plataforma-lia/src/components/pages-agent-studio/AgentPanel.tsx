"use client"

import React from "react"
import { useTranslations } from "next-intl"
import {
  Bot, Play, Pause, RefreshCw, Search as SearchIcon,
  ThumbsUp, ThumbsDown,
} from "lucide-react"
import { Chip } from "@/components/ui/chip"
import { Button } from "@/components/ui/button"
import {
  textStyles, badgeStyles, buttonStyles,
} from "@/lib/design-tokens"
import { StudioCardShell } from "./StudioCardShell"
import type { CustomAgent } from "./custom-agents/types"

// SOURCING-LEGACY-EXEMPT: migration comment header (Sprint 7B-3b Part 2 v2 swap concluido)
// Sprint 7B-3b Part 2 v2 (2026-05-26): SourcingAgent local type DELETADO.
// Componente agora consome CustomAgent canonical (Sprint 7B-1 schema).
// Field access via adapter: agent.name (era agent_name), agent.runtime_metrics
// (era profiles_viewed/approved/rejected diretos), agent.config.calibration_v
// (era top-level), agent.search_strategy continua (CustomAgent ja tem o field).
// Snapshot SHA pre-edit: 7c61cafbb7bcc9799d7eb05ba9936cedd717f778.

export interface TimelineEvent {
  id: string
  icon: string
  type: "positive" | "negative"
  reason: string
  criteria: string[]
  candidate_id: string | null
  created_at: string
}

const STATUS_CONFIG_KEYS = {
  active: { labelKey: "statusActive" as const, style: badgeStyles.success },
  paused: { labelKey: "statusPaused" as const, style: badgeStyles.warning },
  completed: { labelKey: "statusCompleted" as const, style: badgeStyles.error },
  draft: { labelKey: "statusPaused" as const, style: badgeStyles.warning },
  pending_approval: { labelKey: "statusPaused" as const, style: badgeStyles.warning },
  archived: { labelKey: "statusCompleted" as const, style: badgeStyles.error },
} as const

type CardStatus = keyof typeof STATUS_CONFIG_KEYS

export interface AgentPanelProps {
  agent: CustomAgent
  timeline: TimelineEvent[]
  onToggle: () => void
  onRecalibrate: () => void
}

// Adapter helpers — extraem runtime metrics + sourcing strategy do CustomAgent canonical.
function metricsOf(agent: CustomAgent) {
  const rm = (agent.runtime_metrics || {}) as Record<string, unknown>
  return {
    profiles_viewed: typeof rm.profiles_viewed === "number" ? rm.profiles_viewed : 0,
    profiles_approved: typeof rm.profiles_approved === "number" ? rm.profiles_approved : 0,
    profiles_rejected: typeof rm.profiles_rejected === "number" ? rm.profiles_rejected : 0,
  }
}

function calibrationVOf(agent: CustomAgent): number {
  const cfg = (agent.config || {}) as Record<string, unknown>
  const v = cfg.calibration_v
  return typeof v === "number" ? v : 0
}

function strategyOf(agent: CustomAgent) {
  return (agent.search_strategy || {}) as {
    required_skills?: string[]
    exclusions?: string[]
    positive_signals?: string[]
    seniority?: string
    location?: string
  }
}

export function AgentPanel({ agent, timeline, onToggle, onRecalibrate }: AgentPanelProps) {
  const t = useTranslations("agents.agentsTab")
  const statusKey = (agent.status as CardStatus) in STATUS_CONFIG_KEYS
    ? (agent.status as CardStatus)
    : "completed"
  const statusCfg = STATUS_CONFIG_KEYS[statusKey]
  const strategy = strategyOf(agent)
  const metrics = metricsOf(agent)
  const calibrationV = calibrationVOf(agent)

  const statusBadge = (
    <Chip variant="neutral" muted className={statusCfg.style}>
      {t(statusCfg.labelKey)}
    </Chip>
  )

  const subtitle = `v${calibrationV}`

  const actionsSlot = (
    <>
      <Button
        className={buttonStyles.outline}
        onClick={onToggle}
        title={agent.status === "active" ? t("pause") : t("resume")}
      >
        {agent.status === "active" ? (
          <Pause className="w-3.5 h-3.5" />
        ) : (
          <Play className="w-3.5 h-3.5" />
        )}
      </Button>
      <Button className={buttonStyles.outline} onClick={onRecalibrate}>
        <RefreshCw className="w-3.5 h-3.5 mr-1" /> {t("recalibrate")}
      </Button>
    </>
  )

  const chipsSlot = (strategy.required_skills?.length ||
    strategy.exclusions?.length ||
    strategy.seniority ||
    strategy.location) ? (
    <div className="flex flex-wrap gap-1.5">
      {strategy.required_skills?.map((s) => (
        <Chip
          density="relaxed"
          variant="neutral"
          muted
          key={s}
          className={badgeStyles.outlineSuccess}
        >
          {s}
        </Chip>
      ))}
      {strategy.exclusions?.map((e) => (
        <Chip
          density="relaxed"
          variant="neutral"
          muted
          key={e}
          className={badgeStyles.outlineError}
        >
          {e}
        </Chip>
      ))}
      {strategy.seniority && (
        <Chip
          density="relaxed"
          variant="neutral"
          muted
          className={badgeStyles.purple}
        >
          {strategy.seniority}
        </Chip>
      )}
      {strategy.location && (
        <Chip
          density="relaxed"
          variant="neutral"
          muted
          className={badgeStyles.default}
        >
          {strategy.location}
        </Chip>
      )}
    </div>
  ) : undefined

  const metricsSlot = (
    <div className="flex items-center gap-6 text-sm text-lia-text-secondary py-2 border-y border-lia-border-subtle">
      <span title={t("profilesAnalyzed")}>
        <SearchIcon className="w-3.5 h-3.5 inline mr-1" />
        {metrics.profiles_viewed}
      </span>
      <span title={t("approved")}>
        <ThumbsUp className="w-3.5 h-3.5 inline mr-1" />
        {metrics.profiles_approved}
      </span>
      <span title={t("rejected")}>
        <ThumbsDown className="w-3.5 h-3.5 inline mr-1" />
        {metrics.profiles_rejected}
      </span>
    </div>
  )

  const bodySlot = timeline.length > 0 ? (
    <div>
      <h4 className={`${textStyles.label} mb-2`}>{t("recentActivity")}</h4>
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {timeline.map((event) => (
          <div key={event.id} className="flex items-start gap-2 text-sm">
            <span className="flex-shrink-0 mt-0.5">{event.icon}</span>
            <div className="min-w-0">
              <p className={textStyles.bodySmall}>{event.reason}</p>
              {event.criteria.length > 0 && (
                <p className={textStyles.caption}>
                  {t("criteria")}: {event.criteria.join(",")}
                </p>
              )}
              {event.created_at && (
                <p className={textStyles.caption}>
                  {new Date(event.created_at).toLocaleDateString(undefined, {
                    day: "2-digit",
                    month: "2-digit",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  ) : undefined

  return (
    <StudioCardShell
      icon={<Bot className="w-4 h-4 text-graphite" />}
      title={agent.name}
      subtitle={subtitle}
      statusBadge={statusBadge}
      metricsSlot={metricsSlot}
      chipsSlot={chipsSlot}
      bodySlot={bodySlot}
      actionsSlot={actionsSlot}
      data-testid={`agent-panel-${agent.id}`}
    />
  )
}
