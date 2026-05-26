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

// Types — kept aligned with AgentsTab.tsx SourcingAgent/TimelineEvent shapes.
// Sprint visual 2026-05-25: extraído de AgentsTab.tsx:181-251 (inline) →
// componente próprio consumindo <StudioCardShell> canonical (Opção A Paulo).
// Não migra SourcingAgent → CustomAgent nesta sprint (backlog 7B-3a part 2).

export interface SourcingAgent {
  id: string
  agent_name: string
  status: "active" | "paused" | "completed"
  calibration_v: number
  search_strategy: {
    required_skills?: string[]
    exclusions?: string[]
    positive_signals?: string[]
    seniority?: string
    location?: string
  }
  preferences: Record<string, unknown>
  profiles_viewed: number
  profiles_approved: number
  profiles_rejected: number
  created_at: string
}

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
}

export interface AgentPanelProps {
  agent: SourcingAgent
  timeline: TimelineEvent[]
  onToggle: () => void
  onRecalibrate: () => void
}

export function AgentPanel({ agent, timeline, onToggle, onRecalibrate }: AgentPanelProps) {
  const t = useTranslations("agents.agentsTab")
  const statusCfg = STATUS_CONFIG_KEYS[agent.status]
  const strategy = agent.search_strategy

  const statusBadge = (
    <Chip variant="neutral" muted className={statusCfg.style}>
      {t(statusCfg.labelKey)}
    </Chip>
  )

  const subtitle = `v${agent.calibration_v}`

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

  // Strategy chips — DS canonical tokens (era hardcode bg-green-50/red-50/blue-50/lia-bg-tertiary).
  // Sprint visual 2026-05-25: migrado pra tokens semânticos. Sem cyan (white-label Studio).
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

  // Stats row — canonical metrics slot.
  const metricsSlot = (
    <div className="flex items-center gap-6 text-sm text-lia-text-secondary py-2 border-y border-lia-border-subtle">
      <span title={t("profilesAnalyzed")}>
        <SearchIcon className="w-3.5 h-3.5 inline mr-1" />
        {agent.profiles_viewed}
      </span>
      <span title={t("approved")}>
        <ThumbsUp className="w-3.5 h-3.5 inline mr-1" />
        {agent.profiles_approved}
      </span>
      <span title={t("rejected")}>
        <ThumbsDown className="w-3.5 h-3.5 inline mr-1" />
        {agent.profiles_rejected}
      </span>
    </div>
  )

  // Timeline as bodySlot — keeps complex layout out of shell.
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
      title={agent.agent_name}
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
