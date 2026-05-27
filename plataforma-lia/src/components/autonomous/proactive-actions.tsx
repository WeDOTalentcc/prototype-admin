"use client"

import React, { useState, useEffect } from"react"
import { 
  Lightbulb, Check, X, Bell, Clock, 
  ArrowRight, Brain, AlertCircle, Info, Loader2
} from"lucide-react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { cn } from"@/lib/utils"
import { getProactiveActions, acceptProactiveAction, rejectProactiveAction } from"@/services/lia-api"

const PRIORITY_STYLES: Record<string, { badge: string; icon: React.ElementType }> = {
  low: { badge: 'bg-lia-bg-secondary/10 text-lia-text-secondary', icon: Info },
  normal: { badge: '-dark dark:text-wedo-cyan-dark', icon: Lightbulb },
  high: { badge: ' dark:text-wedo-orange', icon: AlertCircle },
  urgent: { badge: ' dark:text-status-error', icon: Bell }
}

const PRIORITY_LABELS: Record<string, string> = {
  low: 'Baixa',
  normal: 'Normal',
  high: 'Alta',
  urgent: 'Urgente'
}

const ACTION_TYPE_LABELS: Record<string, string> = {
  candidate_follow_up: 'Follow-up de Candidato',
  job_optimization: 'Otimização de Vaga',
  pipeline_alert: 'Alerta de Pipeline',
  engagement_suggestion: 'Sugestão de Engajamento',
  deadline_reminder: 'Lembrete de Prazo',
  quality_improvement: 'Melhoria de Qualidade'
}

import { ProactiveAction as ApiProactiveAction } from"@/services/lia-api"

interface ProactiveAction extends ApiProactiveAction {
  action_type?: string
  context?: Record<string, unknown>
  expires_at?: string
}

interface ProactiveActionsProps {
  className?: string
  limit?: number
  compact?: boolean
  onActionTaken?: (actionId: string, accepted: boolean) => void
}

export function ProactiveActions({ 
  className, 
  limit = 5,
  compact = false,
  onActionTaken 
}: ProactiveActionsProps) {
  const [actions, setActions] = useState<ProactiveAction[]>([])
  const [loading, setLoading] = useState(true)
  const [processingId, setProcessingId] = useState<string | null>(null)

  useEffect(() => {
    loadActions()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit])

  const loadActions = async () => {
    setLoading(true)
    try {
      const result = await getProactiveActions('pending', limit)
      setActions(result || [])
    } catch (error) {
      setActions([])
    }
    setLoading(false)
  }

  const handleAccept = async (actionId: string) => {
    setProcessingId(actionId)
    try {
      await acceptProactiveAction(actionId)
      setActions(actions.filter(a => a.id !== actionId))
      onActionTaken?.(actionId, true)
    } catch (error) {
    }
    setProcessingId(null)
  }

  const handleReject = async (actionId: string) => {
    setProcessingId(actionId)
    try {
      await rejectProactiveAction(actionId)
      setActions(actions.filter(a => a.id !== actionId))
      onActionTaken?.(actionId, false)
    } catch (error) {
    }
    setProcessingId(null)
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `${diffMins}min atrás`
    if (diffHours < 24) return `${diffHours}h atrás`
    return `${diffDays}d atrás`
  }

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center py-8", className)} role="status" aria-live="polite" aria-label="Carregando...">
        <Loader2 className="h-6 w-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
      </div>
    )
  }

  if (actions.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mb-4">
            <Brain className="h-6 w-6 text-wedo-cyan" />
          </div>
          <h3 className="text-sm font-medium text-lia-text-primary mb-1">
            Tudo em dia!
          </h3>
          <p className="text-xs text-lia-text-tertiary text-center max-w-sm">
            Não há ações proativas pendentes no momento. A LIA está monitorando e notificará quando houver sugestões.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (compact) {
    return (
      <div className={cn("space-y-2", className)}>
        {actions.map((action) => {
          const priorityStyle = PRIORITY_STYLES[action.priority] || PRIORITY_STYLES.normal
          const PriorityIcon = priorityStyle.icon
          const isProcessing = processingId === action.id

          return (
            <div
              key={action.id}
 className="flex items-start gap-3 p-3 rounded-xl border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary hover:border-lia-border-default dark:border-lia-border-default transition-colors motion-reduce:transition-none"
            >
              <div className={cn("w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                priorityStyle.badge
              )}>
                <PriorityIcon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-lia-text-primary truncate">
                  {action.title}
                </p>

                <p className="text-micro text-lia-text-tertiary truncate">
                  {typeof action.suggested_action === 'string' 
                    ? action.suggested_action 
                    : (action.suggested_action as Record<string, string>)?.label || (action.suggested_action as Record<string, string>)?.action || 'Ver detalhes'}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-status-success hover:text-status-success hover:bg-status-success/10 dark:hover:bg-status-success/20"
                  onClick={() => handleAccept(action.id)}
                  disabled={isProcessing}
                >
                  {isProcessing ? (
                    <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
                  ) : (
                    <Check className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-lia-text-secondary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
                  onClick={() => handleReject(action.id)}
                  disabled={isProcessing}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-5 w-5 text-wedo-cyan" />
          <h3 className="text-sm font-semibold text-lia-text-primary">
            Sugestões da IA
          </h3>
          <Chip variant="neutral" muted>{actions.length}</Chip>
        </div>
      </div>

      <div className="space-y-3">
        {actions.map((action) => {
          const priorityStyle = PRIORITY_STYLES[action.priority] || PRIORITY_STYLES.normal
          const PriorityIcon = priorityStyle.icon
          const isProcessing = processingId === action.id

          return (
            <Card
              key={action.id}
              className="hover:border-lia-border-default dark:border-lia-border-default transition-colors motion-reduce:transition-none"
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className={cn("w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                    priorityStyle.badge
                  )}>
                    <PriorityIcon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-xs font-medium text-lia-text-primary">
                          {action.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-micro text-lia-text-secondary">
                            {action.action_type ? (ACTION_TYPE_LABELS[action.action_type] || action.action_type) : 'Ação'}
                          </span>
                          <span className="text-micro text-lia-text-disabled">•</span>
                          <span className="text-micro text-lia-text-secondary">
                            {formatTimeAgo(action.created_at)}
                          </span>
                        </div>
                      </div>
                      <Chip variant="neutral" muted className={cn("shrink-0 text-micro", priorityStyle.badge)}>
                        {PRIORITY_LABELS[action.priority] || action.priority}
                      </Chip>
                    </div>

                    <p className="text-xs text-lia-text-secondary">
                      {action.description}
                    </p>

                    <div className="flex items-center gap-2 p-2 rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-secondary/50 border border-lia-border-default dark:border-lia-border-default">
                      <ArrowRight className="h-4 w-4 text-lia-text-secondary shrink-0" />

                      <span className="text-xs text-lia-text-secondary font-medium">
                        {typeof action.suggested_action === 'string' 
                          ? action.suggested_action 
                          : (action.suggested_action as Record<string, string>)?.label || (action.suggested_action as Record<string, string>)?.action || 'Ver detalhes'}
                      </span>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="lia-text-secondary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
                        onClick={() => handleReject(action.id)}
                        disabled={isProcessing}
                      >
                        <X className="h-4 w-4 mr-1" />
                        Ignorar
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleAccept(action.id)}
                        disabled={isProcessing}
                      >
                        {isProcessing ? (
                          <Loader2 className="h-4 w-4 mr-1 animate-spin motion-reduce:animate-none" />
                        ) : (
                          <Check className="h-4 w-4 mr-1" />
                        )}
                        Aceitar
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
