"use client"

import React, { useState } from"react"
import { cn } from"@/lib/utils"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Brain, Check, X } from"lucide-react"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import type { AISuggestion } from"@/hooks/ai/useCandidateSuggestions"

interface AISuggestionBadgeProps {
  suggestion: AISuggestion
  onApprove?: (suggestionId: string) => Promise<void>
  onReject?: (suggestionId: string, reason?: string) => Promise<void>
  compact?: boolean
  className?: string
}

const actionLabels: Record<string, string> = {
  move_to_interview:"Agendar Entrevista",
  generate_parecer:"Gerar Parecer",
  send_followup:"Enviar Follow-up",
  reschedule_or_reject:"Reagendar/Reprovar",
  monitor_response:"Aguardar Resposta",
  sync_ats_onboarding:"Sincronizar ATS",
  send_feedback_talent_pool:"Banco de Talentos",
  notify_recruiter:"Notificar Recrutador",
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
    confidencePercent >= 90 ?"text-status-success" :
    confidencePercent >= 75 ?"text-lia-text-primary" :"text-status-warning"

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
          <Chip 
            variant="neutral" 
            className={cn("cursor-pointer gap-1 border-lia-border-default dark:border-lia-border-default text-lia-text-primary hover:bg-lia-bg-tertiary dark:bg-lia-bg-secondary",
 className
            )}
          >
            <Brain className="h-3 w-3 text-wedo-cyan" />
            IA
          </Chip>
        </PopoverTrigger>
        <PopoverContent className="w-64 p-3" align="start">
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-wedo-cyan" />
              <span className="font-medium text-sm">Sugestão da IA</span>
            </div>
            <p className="text-sm text-lia-text-tertiary">{actionLabel}</p>
            <div className="flex items-center justify-between text-xs">
              <span className="text-lia-text-tertiary">Confiança:</span>
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
    <div className={cn("flex items-center gap-2 p-2 rounded-md bg-lia-bg-secondary dark:bg-lia-bg-primary border border-lia-border-default dark:border-lia-border-default",
      className
    )}>
      <Brain className="h-4 w-4 text-wedo-cyan flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-lia-text-primary truncate">
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
          className="h-7 w-7 text-status-success hover:bg-status-success/15"
          onClick={handleApprove}
          disabled={isLoading}
        >
          <Check className="h-4 w-4" />
        </Button>
        <Button 
          size="icon" 
          variant="ghost" 
          className="h-7 w-7 text-status-error hover:bg-status-error/15"
          onClick={handleReject}
          disabled={isLoading}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

AISuggestionBadge.displayName = 'AISuggestionBadge'
