"use client"

import React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { GripVertical, Star, MessageSquare, Clock, TrendingUp, AlertTriangle, AlertCircle } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { getPercentageScoreColorClass } from "@/lib/score-utils"
import { kanbanCardStyles } from "@/lib/design-tokens"
import { KanbanCardShell } from "./KanbanCardShell"
import { KanbanChip } from "./KanbanChip"
import type { KanbanItem } from "./types"

interface KanbanCardProps {
  item: KanbanItem
  index: number
  onClick: () => void
  isDragDisabled?: boolean
}

const DENSITY = "comfortable" as const

export const KanbanCard = React.memo(function KanbanCard({
  item,
  index,
  onClick,
  isDragDisabled = false,
}: KanbanCardProps) {
  const scoreColor = item.scoreColorClass
    ?? (item.score != null ? getPercentageScoreColorClass(item.score) : "text-lia-text-disabled")

  const chips = item.chips ?? []

  const footer = (
    <div className="flex items-center justify-between p-3 pt-2">
      <TooltipProvider delayDuration={200}>
        <div className="flex items-center gap-2">
          {item.flagFavorite && (
            <Star className="h-3 w-3 text-status-warning fill-amber-500" />
          )}
          {item.flagNotes && (
            <MessageSquare className="h-3 w-3 text-lia-text-disabled" />
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
          {item.flagAttention && (
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
        <span className="text-micro text-lia-text-tertiary">
          {item.dateLabel}
        </span>
      )}
    </div>
  )

  return (
    <KanbanCardShell
      density={DENSITY}
      onClick={onClick}
      footer={footer}
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
            <GripVertical className="h-4 w-4 text-lia-text-disabled" />
          </div>
        )}

        <Avatar className={`${kanbanCardStyles.avatar[DENSITY]} flex-shrink-0`}>
          {item.avatarUrl && <AvatarImage src={item.avatarUrl} alt={item.title} />}
          <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary text-xs">
            {item.avatarFallback ?? item.title.slice(0, 2).toUpperCase()}
          </AvatarFallback>
        </Avatar>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className={kanbanCardStyles.title[DENSITY]}>
              {item.title}
            </span>
            {item.score != null && (
              <span className={`text-sm font-bold ${scoreColor}`}>
                {Math.round(item.score)}
              </span>
            )}
          </div>

          {item.subtitle && (
            <p className={`${kanbanCardStyles.subtitle[DENSITY]} mt-0.5`}>
              {item.subtitle}
            </p>
          )}

          {item.tertiary && (
            <p className={kanbanCardStyles.tertiary[DENSITY]}>
              {item.tertiary}
            </p>
          )}
        </div>
      </div>

      {item.progressPercent != null && (
        <div className="mt-2" role="progressbar" aria-valuenow={Math.round(item.progressPercent)} aria-valuemin={0} aria-valuemax={100} aria-label="Progresso da vaga">
          <div className="h-1.5 w-full rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-elevated overflow-hidden">
            <div
              className="h-full bg-lia-interactive-active transition-[width] motion-reduce:transition-none"
              style={{ width: `${Math.max(0, Math.min(100, item.progressPercent))}%` }}
            />
          </div>
        </div>
      )}

      {item.badge && (
        <div className="mt-2">
          <KanbanChip density={DENSITY}>{item.badge}</KanbanChip>
        </div>
      )}

      {chips.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {chips.slice(0, 3).map((chip) => (
            <KanbanChip key={chip} density={DENSITY}>
              {chip}
            </KanbanChip>
          ))}
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
