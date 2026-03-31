"use client"

import React from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { GripVertical, Star, MessageSquare, Clock, TrendingUp, AlertTriangle } from "lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from "@/lib/design-tokens"
import type { KanbanCandidate } from "./types"

interface KanbanCardProps {
  candidate: KanbanCandidate
  index: number
  onClick: () => void
  isDragDisabled?: boolean
}

export const KanbanCard = React.memo(function KanbanCard({
  candidate,
  index,
  onClick,
  isDragDisabled = false,
}: KanbanCardProps) {
  const getScoreColor = (score?: number) => {
    if (!score) return "text-lia-text-disabled dark:text-lia-text-tertiary"
    if (score >= 80) return "text-status-success dark:text-status-success"
    if (score >= 60) return "text-status-warning dark:text-status-warning"
    return "text-status-error dark:text-status-error"
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase()
  }

  const isStale = (candidate.days_in_stage ?? 0) > 7
  const isHighScore = (candidate.lia_score ?? 0) >= 80
  const isLowScore = (candidate.lia_score ?? 0) < 40 && (candidate.lia_score ?? 0) > 0

  return (
    <Card
      className="bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-default dark:hover:border-gray-600 cursor-pointer transition-colors motion-reduce:transition-none hover:group rounded-md"
      onClick={onClick}
      data-testid="candidate-card"
      data-candidate-id={candidate.id}
      data-index={index}
    >
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          {!isDragDisabled && (
            <div 
              className="opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none cursor-grab"
              data-testid="drag-handle"
            >
              <GripVertical className="h-4 w-4 text-lia-text-disabled dark:text-lia-text-tertiary" />
            </div>
          )}
          
          <Avatar className="h-8 w-8 flex-shrink-0">
            <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
            <AvatarFallback className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary text-xs">
              {getInitials(candidate.name)}
            </AvatarFallback>
          </Avatar>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-medium text-lia-text-primary dark:text-lia-text-primary text-sm truncate">
                {candidate.name}
              </span>
              {candidate.lia_score && (
                <span className={`text-sm font-bold ${getScoreColor(candidate.lia_score)}`}>
                  {Math.round(candidate.lia_score)}
                </span>
              )}
            </div>
            
            {candidate.current_title && (
              <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary truncate mt-0.5">
                {candidate.current_title}
              </p>
            )}
            
            {candidate.current_company && (
              <p className="text-xs text-lia-text-tertiary dark:text-lia-text-tertiary truncate">
                {candidate.current_company}
              </p>
            )}
          </div>
        </div>
        
        {candidate.substatus && (
          <Badge 
            variant="outline" 
            className="mt-2 text-xs border-lia-border-default dark:border-lia-border-default text-lia-text-secondary dark:text-lia-text-tertiary"
          >
            {candidate.substatus}
          </Badge>
        )}
        
        {candidate.skills && candidate.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {candidate.skills.slice(0, 3).map((skill) => (
              <Badge 
                key={skill} 
                variant="outline" 
                className="text-micro border-lia-border-default dark:border-lia-border-default text-lia-text-secondary dark:text-lia-text-tertiary py-0"
              >
                {skill}
              </Badge>
            ))}
            {candidate.skills.length > 3 && (
              <Badge 
                variant="outline" 
                className="text-micro border-lia-border-default dark:border-lia-border-default text-lia-text-tertiary dark:text-lia-text-tertiary py-0"
              >
                +{candidate.skills.length - 3}
              </Badge>
            )}
          </div>
        )}
        
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
          <TooltipProvider delayDuration={200}>
            <div className="flex items-center gap-2">
              {candidate.tags?.includes("favorite") && (
                <Star className="h-3 w-3 text-status-warning fill-amber-500" />
              )}
              {candidate.notes && (
                <MessageSquare className="h-3 w-3 text-lia-text-disabled dark:text-lia-text-tertiary" />
              )}
              {isStale && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Clock className="h-3 w-3 text-status-warning" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Parado há {candidate.days_in_stage} dias — considere avançar ou dar retorno
                  </TooltipContent>
                </Tooltip>
              )}
              {isHighScore && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <TrendingUp className="h-3 w-3 text-status-success" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Score WSI alto ({Math.round(candidate.lia_score!)}) — considere priorizar
                  </TooltipContent>
                </Tooltip>
              )}
              {isLowScore && (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <AlertTriangle className="h-3 w-3 text-status-error" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="text-xs">
                    Score WSI baixo ({Math.round(candidate.lia_score!)}) — avaliar permanência
                  </TooltipContent>
                </Tooltip>
              )}
            </div>
          </TooltipProvider>
          
          <span className="text-micro text-lia-text-tertiary dark:text-lia-text-tertiary">
            {new Date(candidate.addedAt).toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "short"
            })}
          </span>
        </div>
      </CardContent>
    </Card>
  )
})

// Vue migration prep: displayName for DevTools compatibility
KanbanCard.displayName = 'KanbanCard'
