"use client"

import React, { useState, useEffect } from "react"
import { 
  Lightbulb, Check, X, Bell, Clock, 
  ArrowRight, Brain, AlertCircle, Info, Loader2
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { getProactiveActions, acceptProactiveAction, rejectProactiveAction } from "@/services/lia-api"

const PRIORITY_STYLES: Record<string, { badge: string; icon: React.ElementType }> = {
  low: { badge: 'bg-gray-500/10 text-gray-500', icon: Info },
  normal: { badge: 'bg-wedo-cyan/10 text-wedo-cyan-dark dark:text-wedo-cyan-dark', icon: Lightbulb },
  high: { badge: 'bg-wedo-orange/10 text-wedo-orange dark:text-wedo-orange', icon: AlertCircle },
  urgent: { badge: 'bg-status-error/10 text-status-error dark:text-status-error', icon: Bell }
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

import { ProactiveAction as ApiProactiveAction } from "@/services/lia-api"

interface ProactiveAction extends ApiProactiveAction {
  action_type?: string
  context?: Record<string, any>
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
      <div className={cn("flex items-center justify-center py-8", className)}>
        <Loader2 className="h-6 w-6 animate-spin text-gray-600 dark:text-gray-400" />
      </div>
    )
  }

  if (actions.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-4">
            <Brain className="h-6 w-6 text-wedo-cyan" />
          </div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
            Tudo em dia!
          </h3>
          <p className="text-xs text-gray-500 dark:text-gray-400 text-center max-w-sm">
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
 className="flex items-start gap-3 p-3 rounded-md border border-gray-100 bg-white dark:bg-gray-900 hover:border-gray-300 dark:border-gray-600 transition-colors"
            >
              <div className={cn(
                "w-8 h-8 rounded-full flex items-center justify-center shrink-0",
                priorityStyle.badge
              )}>
                <PriorityIcon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-900 dark:text-gray-100 truncate">
                  {action.title}
                </p>
                <p className="text-micro text-gray-500 dark:text-gray-400 truncate">
                  {typeof action.suggested_action === 'string' 
                    ? action.suggested_action 
                    : action.suggested_action?.label || action.suggested_action?.action || 'Ver detalhes'}
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
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Check className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-gray-400 hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
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
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Sugestões da LIA
          </h3>
          <Badge variant="secondary">{actions.length}</Badge>
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
              className="hover:border-gray-300 dark:border-gray-600 transition-colors"
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0",
                    priorityStyle.badge
                  )}>
                    <PriorityIcon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-xs font-medium text-gray-900 dark:text-gray-100">
                          {action.title}
                        </h4>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-micro text-gray-400">
                            {action.action_type ? (ACTION_TYPE_LABELS[action.action_type] || action.action_type) : 'Ação'}
                          </span>
                          <span className="text-micro text-gray-300 dark:text-gray-600">•</span>
                          <span className="text-micro text-gray-400">
                            {formatTimeAgo(action.created_at)}
                          </span>
                        </div>
                      </div>
                      <Badge className={cn("shrink-0 text-micro", priorityStyle.badge)}>
                        {PRIORITY_LABELS[action.priority] || action.priority}
                      </Badge>
                    </div>

                    <p className="text-xs text-gray-600 dark:text-gray-400">
                      {action.description}
                    </p>

                    <div className="flex items-center gap-2 p-2 rounded-md bg-gray-50 dark:bg-gray-800/50 border border-gray-300 dark:border-gray-600">
                      <ArrowRight className="h-4 w-4 text-gray-600 dark:text-gray-400 shrink-0" />
                      <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">
                        {typeof action.suggested_action === 'string' 
                          ? action.suggested_action 
                          : action.suggested_action?.label || action.suggested_action?.action || 'Ver detalhes'}
                      </span>
                    </div>

                    <div className="flex items-center justify-end gap-2 pt-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-500 hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
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
                          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
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
