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

export function KanbanCard({
  candidate,
  index,
  onClick,
  isDragDisabled = false,
}: KanbanCardProps) {
  const getScoreColor = (score?: number) => {
    if (!score) return "text-gray-400 dark:text-gray-500"
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
      className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 cursor-pointer transition-all hover:group rounded-md"
      onClick={onClick}
      data-testid="candidate-card"
      data-candidate-id={candidate.id}
      data-index={index}
    >
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          {!isDragDisabled && (
            <div 
              className="opacity-0 group-hover:opacity-100 transition-opacity cursor-grab"
              data-testid="drag-handle"
            >
              <GripVertical className="h-4 w-4 text-gray-400 dark:text-gray-500" />
            </div>
          )}
          
          <Avatar className="h-8 w-8 flex-shrink-0">
            <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
            <AvatarFallback className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs">
              {getInitials(candidate.name)}
            </AvatarFallback>
          </Avatar>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900 dark:text-gray-50 text-sm truncate">
                {candidate.name}
              </span>
              {candidate.lia_score && (
                <span className={`text-sm font-bold ${getScoreColor(candidate.lia_score)}`}>
                  {Math.round(candidate.lia_score)}
                </span>
              )}
            </div>
            
            {candidate.current_title && (
              <p className="text-xs text-gray-600 dark:text-gray-400 truncate mt-0.5">
                {candidate.current_title}
              </p>
            )}
            
            {candidate.current_company && (
              <p className="text-xs text-gray-500 dark:text-gray-500 truncate">
                {candidate.current_company}
              </p>
            )}
          </div>
        </div>
        
        {candidate.substatus && (
          <Badge 
            variant="outline" 
            className="mt-2 text-xs border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400"
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
                className="text-micro border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 py-0"
              >
                {skill}
              </Badge>
            ))}
            {candidate.skills.length > 3 && (
              <Badge 
                variant="outline" 
                className="text-micro border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-500 py-0"
              >
                +{candidate.skills.length - 3}
              </Badge>
            )}
          </div>
        )}
        
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
          <TooltipProvider delayDuration={200}>
            <div className="flex items-center gap-2">
              {candidate.tags?.includes("favorite") && (
                <Star className="h-3 w-3 text-status-warning fill-amber-500" />
              )}
              {candidate.notes && (
                <MessageSquare className="h-3 w-3 text-gray-400 dark:text-gray-500" />
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
          
          <span className="text-micro text-gray-500 dark:text-gray-500">
            {new Date(candidate.addedAt).toLocaleDateString("pt-BR", {
              day: "2-digit",
              month: "short"
            })}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
