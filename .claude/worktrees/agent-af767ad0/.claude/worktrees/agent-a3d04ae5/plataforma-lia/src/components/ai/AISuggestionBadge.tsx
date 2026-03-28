"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Brain, Check, X } from "lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import type { AISuggestion } from "@/hooks/useCandidateSuggestions"

interface AISuggestionBadgeProps {
  suggestion: AISuggestion
  onApprove?: (suggestionId: string) => Promise<void>
  onReject?: (suggestionId: string, reason?: string) => Promise<void>
  compact?: boolean
  className?: string
}

const actionLabels: Record<string, string> = {
  move_to_interview: "Agendar Entrevista",
  generate_parecer: "Gerar Parecer",
  send_followup: "Enviar Follow-up",
  reschedule_or_reject: "Reagendar/Reprovar",
  monitor_response: "Aguardar Resposta",
  sync_ats_onboarding: "Sincronizar ATS",
  send_feedback_talent_pool: "Banco de Talentos",
  notify_recruiter: "Notificar Recrutador",
}

export function AISuggestionBadge({
  suggestion,
  onApprove,
  onReject,
  compact = false,
  className,
}: AISuggestionBadgeProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)

  const actionLabel = actionLabels[suggestion.suggested_action] || suggestion.suggested_action
  const confidencePercent = Math.round(suggestion.confidence_score * 100)
  
  const confidenceColor = 
    confidencePercent >= 90 ? "text-green-600" :
    confidencePercent >= 75 ? "text-gray-900 dark:text-gray-50" :
    "text-amber-600"

  const handleApprove = async () => {
    if (!onApprove) return
    setIsLoading(true)
    try {
      await onApprove(suggestion.id)
      setIsOpen(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleReject = async () => {
    if (!onReject) return
    setIsLoading(true)
    try {
      await onReject(suggestion.id)
      setIsOpen(false)
    } finally {
      setIsLoading(false)
    }
  }

  if (compact) {
    return (
      <Popover open={isOpen} onOpenChange={setIsOpen}>
        <PopoverTrigger asChild>
          <Badge 
            variant="outline" 
            className={cn(
 "cursor-pointer gap-1 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-50 hover:bg-gray-100 dark:bg-gray-800",
              className
            )}
          >
            <Brain className="h-3 w-3 text-wedo-cyan" />
            LIA
          </Badge>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-3" align="start">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-wedo-cyan" />
              <span className="font-medium text-sm">Sugestão da LIA</span>
            </div>
            <p className="text-sm text-muted-foreground">{actionLabel}</p>
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Confiança:</span>
              <span className={cn("font-medium", confidenceColor)}>
                {confidencePercent}%
              </span>
            </div>
            <div className="flex gap-2">
              <Button 
                size="sm" 
                className="flex-1 h-8"
                onClick={handleApprove}
                disabled={isLoading}
              >
                <Check className="h-3 w-3 mr-1" />
                Aprovar
              </Button>
              <Button 
                size="sm" 
                variant="outline" 
                className="flex-1 h-8"
                onClick={handleReject}
                disabled={isLoading}
              >
                <X className="h-3 w-3 mr-1" />
                Rejeitar
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    )
  }

  return (
    <div className={cn(
      "flex items-center gap-2 p-2 rounded-md bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-600",
      className
    )}>
      <Brain className="h-4 w-4 text-wedo-cyan flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-50 truncate">
          {actionLabel}
        </p>
        <p className={cn("text-xs", confidenceColor)}>
          {confidencePercent}% confiança
        </p>
      </div>
      <div className="flex gap-1">
        <Button 
          size="icon" 
          variant="ghost" 
          className="h-7 w-7 text-green-600 hover:bg-green-100"
          onClick={handleApprove}
          disabled={isLoading}
        >
          <Check className="h-4 w-4" />
        </Button>
        <Button 
          size="icon" 
          variant="ghost" 
          className="h-7 w-7 text-red-600 hover:bg-red-100"
          onClick={handleReject}
          disabled={isLoading}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
