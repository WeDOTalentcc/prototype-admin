"use client"

import React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  GripVertical,
  Star,
  MessageSquare,
  Clock,
  TrendingUp,
  AlertTriangle,
  AlertCircle,
  Building,
  MapPin,
  CalendarClock,
  Flag,
  Briefcase,
  Users,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { getPercentageScoreColorClass } from "@/lib/score-utils"
import { kanbanCardStyles } from "@/lib/design-tokens"
import { KanbanCardShell } from "./KanbanCardShell"
import { KanbanChip } from "./KanbanChip"
import { JobKanbanMiniFunnel } from "./JobKanbanMiniFunnel"
import { JobCampaignBadge } from "@/components/jobs/JobCampaignBadge"
import type { KanbanItem } from "./types"

interface KanbanCardProps {
  item: KanbanItem
  index: number
  onClick: () => void
  isDragDisabled?: boolean
  /** Task #562 — Labels do mini funil (opcional; quando ausente, omite). */
  funnelLabels?: {
    screening: string
    interview: string
    final: string
    hired: string
  }
  /** Task #562 — Labels para chips estratégicos (idade, deadline). */
  infoLabels?: {
    ageDays: (days: number) => string
    ownerLabel?: string
  }
}

// Task #562 — Densidade alinhada ao card de candidato (compact).
const DENSITY = "compact" as const

const RIBBON_VARIANT_CLS = {
  warning: "text-status-warning",
  danger: "text-status-error",
  info: "text-wedo-cyan-text dark:text-wedo-cyan",
} as const

const DEADLINE_CHIP_VARIANT = {
  ok: "neutral",
  warning: "warning",
  danger: "danger",
} as const

// Task #562 — Mapa de ícone semântico para chips (paridade com card de
// candidato). Mapper emite a chave; card resolve o componente.
const CHIP_ICON_MAP: Record<"briefcase" | "users" | "star", LucideIcon> = {
  briefcase: Briefcase,
  users: Users,
  star: Star,
}

export const KanbanCard = React.memo(function KanbanCard({
  item,
  index,
  onClick,
  isDragDisabled = false,
  funnelLabels,
  infoLabels,
}: KanbanCardProps) {
  const scoreColor = item.scoreColorClass
    ?? (item.score != null ? getPercentageScoreColorClass(item.score) : "text-lia-text-disabled")

  const chips = item.chips ?? []

  const ribbon = item.ribbon ? (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className="flex items-center gap-1.5 min-w-0"
            data-testid="job-card-ribbon"
            data-variant={item.ribbon.variant}
          >
            <Flag className={`w-3 h-3 flex-shrink-0 ${RIBBON_VARIANT_CLS[item.ribbon.variant]}`} />
            <span className="text-micro font-bold text-lia-text-tertiary flex-shrink-0">
              {item.ribbon.label}
            </span>
            <span className="text-micro text-lia-text-secondary truncate">
              · {item.ribbon.reason}
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs">
          {item.ribbon.label}: {item.ribbon.reason}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  ) : null

  const footer = (
    <div className="flex items-center justify-between p-2 pt-1.5">
      <TooltipProvider delayDuration={200}>
        <div className="flex items-center gap-2 min-w-0">
          {item.owner && (
            <div className="flex items-center gap-1.5 min-w-0" title={infoLabels?.ownerLabel ? `${infoLabels.ownerLabel}: ${item.owner.name}` : item.owner.name}>
              <Avatar className="w-4 h-4 flex-shrink-0">
                {item.owner.avatarUrl && <AvatarImage src={item.owner.avatarUrl} alt={item.owner.name} />}
                <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary text-[8px] font-medium">
                  {item.owner.initials}
                </AvatarFallback>
              </Avatar>
              <span className="text-micro text-lia-text-secondary truncate max-w-[80px]">
                {item.owner.name}
              </span>
            </div>
          )}
          {item.flagFavorite && (
            <Star className="h-3 w-3 text-status-warning fill-amber-500" />
          )}
          {item.flagNotes && (
            <MessageSquare className="h-3 w-3 text-lia-text-muted" />
          )}
          {item.flagStaleTooltip && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Clock className="h-3 w-3 text-status-warning" />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {item.flagStaleTooltip}
              </TooltipContent>
            </Tooltip>
          )}
          {item.flagHighScoreTooltip && (
            <Tooltip>
              <TooltipTrigger asChild>
                <TrendingUp className="h-3 w-3 text-status-success" />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {item.flagHighScoreTooltip}
              </TooltipContent>
            </Tooltip>
          )}
          {item.flagLowScoreTooltip && (
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertTriangle className="h-3 w-3 text-status-error" />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {item.flagLowScoreTooltip}
              </TooltipContent>
            </Tooltip>
          )}
          {item.flagAttention && !item.ribbon && (
            <Tooltip>
              <TooltipTrigger asChild>
                <AlertCircle className="h-3 w-3 text-status-warning" />
              </TooltipTrigger>
              <TooltipContent side="top" className="text-xs">
                {item.flagAttention.tooltip}
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </TooltipProvider>

      {item.dateLabel && (
        <KanbanChip
          density={DENSITY}
          variant={DEADLINE_CHIP_VARIANT[item.deadlineStatus ?? "ok"] as "neutral" | "warning" | "danger"}
          className="gap-0.5"
        >
          <CalendarClock className="w-2.5 h-2.5" />
          {item.dateLabel}
        </KanbanChip>
      )}
    </div>
  )

  return (
    <KanbanCardShell
      density={DENSITY}
      onClick={onClick}
      footer={footer}
      ribbon={ribbon}
      className="cursor-pointer"
      data-testid="kanban-item-card"
      data-item-id={item.id}
      data-index={index}
    >
      <div className="flex items-start gap-2">
        {!isDragDisabled && (
          <div
            className="opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none cursor-grab"
            data-testid="drag-handle"
          >
            <GripVertical className="h-4 w-4 text-lia-text-muted" />
          </div>
        )}

        <Avatar className={`${kanbanCardStyles.avatar[DENSITY]} flex-shrink-0`}>
          {item.avatarUrl && <AvatarImage src={item.avatarUrl} alt={item.title} />}
          <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary text-xs">
            {item.avatarFallback ?? item.title.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className={kanbanCardStyles.title[DENSITY]}>
              {item.title}
            </span>
            {item.score != null && (
              <span className={`text-sm font-bold ${scoreColor} flex-shrink-0`}>
                {Math.round(item.score)}
              </span>
            )}
          </div>

          {item.subtitle && (
            <p className={`${kanbanCardStyles.subtitle[DENSITY]} mt-0.5 flex items-center gap-1`}>
              <Building className="w-3 h-3 text-lia-text-tertiary flex-shrink-0" />
              <span className="truncate">{item.subtitle}</span>
            </p>
          )}

          {item.tertiary && (
            <p className={`${kanbanCardStyles.tertiary[DENSITY]} flex items-center gap-1`}>
              <MapPin className="w-3 h-3 text-lia-text-tertiary flex-shrink-0" />
              <span className="truncate">{item.tertiary}</span>
            </p>
          )}
        </div>
      </div>

      {/* Mini funil quando há candidatos; senão, barra de progresso simples
          como fallback visual (Task #562). Sem default silencioso. */}
      {item.funnel && funnelLabels ? (
        <div className="mt-2">
          <JobKanbanMiniFunnel funnel={item.funnel} labels={funnelLabels} />
        </div>
      ) : item.progressPercent != null ? (
        <div className="mt-2" role="progressbar" aria-valuenow={Math.round(item.progressPercent)} aria-valuemin={0} aria-valuemax={100} aria-label="Progresso da vaga">
          <div className="h-1.5 w-full rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated overflow-hidden">
            <div
              className="h-full bg-lia-interactive-active transition-[width] motion-reduce:transition-none"
              style={{ width: `${Math.max(0, Math.min(100, item.progressPercent))}%` }}
            />
          </div>
        </div>
      ) : null}

      {item.badge && (
        <div className="mt-2">
          <KanbanChip density={DENSITY}>{item.badge}</KanbanChip>
        </div>
      )}

      {/* Task #592 — Campaign badge (informativo, fase educativa). */}
      <div className="mt-2">
        <JobCampaignBadge jobId={item.id} status={item.campaignStatus} />
      </div>


      {(chips.length > 0 || item.ageDays != null) && (
        <div className="flex flex-wrap gap-1 mt-2">
          {item.ageDays != null && infoLabels?.ageDays && (
            <KanbanChip density={DENSITY} variant="neutral" className="gap-0.5">
              <Clock className="w-2.5 h-2.5" />
              {infoLabels.ageDays(item.ageDays)}
            </KanbanChip>
          )}
          {chips.slice(0, 3).map((chip, i) => {
            const isObj = typeof chip !== "string"
            const label = isObj ? chip.label : chip
            const Icon: LucideIcon | null = isObj && chip.icon
              ? CHIP_ICON_MAP[chip.icon]
              : null
            return (
              <KanbanChip key={`${label}-${i}`} density={DENSITY} className={Icon ? "gap-0.5" : undefined}>
                {Icon && <Icon className="w-2.5 h-2.5" />}
                {label}
              </KanbanChip>
            )
          })}
          {chips.length > 3 && (
            <KanbanChip density={DENSITY} muted>
              +{chips.length - 3}
            </KanbanChip>
          )}
        </div>
      )}
    </KanbanCardShell>
  )
})

KanbanCard.displayName = 'KanbanCard'
