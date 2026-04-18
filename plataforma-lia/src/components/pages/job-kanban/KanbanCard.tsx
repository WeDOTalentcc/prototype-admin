"use client"

import React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { GripVertical, Star, MessageSquare, Clock, TrendingUp, AlertTriangle, AlertCircle } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { getPercentageScoreColorClass } from "@/lib/score-utils"
import type { KanbanItem } from "./types"

interface KanbanCardProps {
  item: KanbanItem
  index: number
  onClick: () => void
  isDragDisabled?: boolean
}

export const KanbanCard = React.memo(function KanbanCard({
  item,
  index,
  onClick,
  isDragDisabled = false,
}: KanbanCardProps) {
  const scoreColor = item.scoreColorClass
    ?? (item.score != null ? getPercentageScoreColorClass(item.score) : "text-lia-text-disabled")

  const chips = item.chips ?? []

  return (
    <Card
      className="bg-lia-bg-primary dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-lia-border-medium cursor-pointer transition-colors motion-reduce:transition-none hover:group rounded-xl"
      onClick={onClick}
      data-testid="kanban-item-card"
      data-item-id={item.id}
      data-index={index}
    >
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          {!isDragDisabled && (
            <div
              className="opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none cursor-grab"
              data-testid="drag-handle"
            >
              <GripVertical className="h-4 w-4 text-lia-text-disabled" />
            </div>
          )}

          <Avatar className="h-8 w-8 flex-shrink-0">
            {item.avatarUrl && <AvatarImage src={item.avatarUrl} alt={item.title} />}
            <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary text-xs">
              {item.avatarFallback ?? item.title.slice(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-medium text-lia-text-primary text-sm truncate">
                {item.title}
              </span>
              {item.score != null && (
                <span className={`text-sm font-bold ${scoreColor}`}>
                  {Math.round(item.score)}
                </span>
              )}
            </div>

            {item.subtitle && (
              <p className="text-xs text-lia-text-secondary truncate mt-0.5">
                {item.subtitle}
              </p>
            )}

            {item.tertiary && (
              <p className="text-xs text-lia-text-tertiary truncate">
                {item.tertiary}
              </p>
            )}
          </div>
        </div>

        {item.badge && (
          <Badge
            variant="outline"
            className="mt-2 text-xs border-lia-border-default dark:border-lia-border-default text-lia-text-secondary"
          >
            {item.badge}
          </Badge>
        )}

        {chips.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {chips.slice(0, 3).map((chip) => (
              <Badge
                key={chip}
                variant="outline"
                className="text-micro border-lia-border-default dark:border-lia-border-default text-lia-text-secondary py-0"
              >
                {chip}
              </Badge>
            ))}
            {chips.length > 3 && (
              <Badge
                variant="outline"
                className="text-micro border-lia-border-default dark:border-lia-border-default text-lia-text-tertiary py-0"
              >
                +{chips.length - 3}
              </Badge>
            )}
          </div>
        )}

        <div className="flex items-center justify-between mt-2 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
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
      </CardContent>
    </Card>
  )
})

KanbanCard.displayName = 'KanbanCard'
