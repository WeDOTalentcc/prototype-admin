"use client"

import React, { useState, useEffect, useMemo } from"react"
import { Bell, Loader2, Brain, Check, X, ArrowRight, Clock, User } from"lucide-react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Popover, PopoverContent, PopoverTrigger } from"@/components/ui/popover"
import { cn } from"@/lib/utils"
import { getProactiveActions, acceptProactiveAction, rejectProactiveAction } from"@/services/lia-api"

import { ProactiveAction as ApiProactiveAction } from"@/services/lia-api"

interface ProactiveAction extends ApiProactiveAction {
  action_type?: string
  candidate?: {
    id?: string
    name?: string
    avatar_url?: string
    score?: number
  }
  vacancy?: {
    id?: string
    title?: string
  }
}

interface ProactiveActionsBellProps {
  className?: string
  onActionTaken?: (actionId: string, accepted: boolean) => void
  refreshInterval?: number
}

function getScoreColor(score: number): string {
  if (score >= 80) return"text-status-success bg-status-success/10 dark:text-status-success"
  if (score >= 60) return"text-status-warning bg-status-warning/10 dark:bg-status-warning/30 dark:text-status-warning"
  return"text-status-error bg-status-error/10 dark:bg-status-error/30 dark:text-status-error"
}

interface GroupedActions {
  vacancyId: string
  vacancyTitle: string
  actions: ProactiveAction[]
}

export function ProactiveActionsBell({ 
  className, 
  onActionTaken,
  refreshInterval = 60000
}: ProactiveActionsBellProps) {
  const [actions, setActions] = useState<ProactiveAction[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [deferredIds, setDeferredIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadActions()
    
    const interval = setInterval(loadActions, refreshInterval)
    return () => clearInterval(interval)
  }, [refreshInterval])

  const loadActions = async () => {
    try {
      const result = await getProactiveActions('pending', 10)
      setActions(result || [])
    } catch (error) {
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

  const handleDefer = (actionId: string) => {
    setDeferredIds(prev => new Set([...prev, actionId]))
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return 'Agora'
    if (diffMins < 60) return `${diffMins}min`
    if (diffHours < 24) return `${diffHours}h`
    return `${Math.floor(diffMs / 86400000)}d`
  }

  const visibleActions = useMemo(() => {
    return actions.filter(a => !deferredIds.has(a.id))
  }, [actions, deferredIds])

  const groupedByVacancy = useMemo(() => {
    const groups: GroupedActions[] = []
    const vacancyMap = new Map<string, ProactiveAction[]>()
    const noVacancy: ProactiveAction[] = []

    for (const action of visibleActions) {
      const vacId = action.vacancy?.id || (action.suggested_action as unknown as Record<string, unknown>)?.vacancy_id as string | undefined
      const vacTitle = action.vacancy?.title || (action.suggested_action as unknown as Record<string, unknown>)?.vacancy_title as string | undefined
      if (vacId) {
        if (!vacancyMap.has(vacId)) {
          vacancyMap.set(vacId, [])
        }
        vacancyMap.get(vacId)!.push({ ...action, vacancy: { id: vacId, title: vacTitle } })
      } else {
        noVacancy.push(action)
      }
    }

    for (const [vacId, acts] of vacancyMap.entries()) {
      groups.push({
        vacancyId: vacId,
        vacancyTitle: acts[0]?.vacancy?.title || 'Vaga',
        actions: acts,
      })
    }

    if (noVacancy.length > 0) {
      groups.push({
        vacancyId: '__general__',
        vacancyTitle: 'Geral',
        actions: noVacancy,
      })
    }

    return groups
  }, [visibleActions])

  const pendingCount = visibleActions.length
  const hasUrgent = visibleActions.some(a => a.priority === 'urgent' || a.priority === 'high')

  const renderActionCard = (action: ProactiveAction) => {
    const isProcessing = processingId === action.id
    const suggestedCandidate = typeof action.suggested_action === 'object' && action.suggested_action !== null
      ? (action.suggested_action as Record<string, unknown>).candidate as ProactiveAction['candidate'] | undefined
      : undefined
    const candidate = action.candidate || suggestedCandidate

    return (
      <div
        key={action.id}
        data-testid={`proactive-action-card-${action.id}`}
        className="p-3 hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-start gap-2">
          {candidate ? (
            <Avatar className="h-8 w-8 flex-shrink-0">
              <AvatarImage src={candidate?.avatar_url} alt={candidate?.name} />
              <AvatarFallback className="text-micro bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary">
                {(candidate?.name?.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase() || '??')}
              </AvatarFallback>
            </Avatar>
          ) : (
            <div className={cn("w-2 h-2 rounded-full mt-1.5 shrink-0",
              (action as unknown as Record<string, unknown>).priority === 'urgent' &&"bg-status-error",
              action.priority === 'high' &&"bg-wedo-orange",
              action.priority === 'normal' &&"bg-wedo-cyan",
              action.priority === 'low' &&"bg-lia-border-medium"
            )} />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <p className="text-xs font-medium text-lia-text-primary line-clamp-1">
                  {candidate?.name || action.title}
                </p>
                {candidate?.score && (
                  <span className={cn("text-micro font-bold px-1.5 py-0.5 rounded-full flex-shrink-0",
                    getScoreColor(candidate.score)
                  )}>
                    {Math.round(candidate.score)}
                  </span>
                )}
              </div>
              <span className="text-micro text-lia-text-secondary shrink-0">
                {formatTimeAgo(action.created_at)}
              </span>
            </div>
            {candidate && (
              <p className="text-micro font-medium text-lia-text-secondary line-clamp-1 mt-0.5">
                {action.title}
              </p>
            )}
            <p className="text-micro text-lia-text-tertiary line-clamp-2 mt-0.5">
              {action.description}
            </p>
            <div className="flex items-center gap-1 mt-2">
              <ArrowRight className="h-3 w-3 text-lia-text-secondary shrink-0" />

              <span className="text-micro text-lia-text-secondary font-medium line-clamp-1">
                {typeof action.suggested_action === 'string' 
                  ? action.suggested_action 

                  : (action.suggested_action as Record<string, unknown>)?.label as string || (action.suggested_action as Record<string, unknown>)?.action as string || 'Ver detalhes'}
              </span>
            </div>
            <div className="flex items-center gap-1 mt-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-lia-text-secondary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
                onClick={() => handleReject(action.id)}
                disabled={isProcessing}
              >
                <X className="h-3 w-3 mr-0.5" />
                Ignorar
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-lia-text-secondary hover:text-status-warning hover:bg-status-warning/10 dark:hover:bg-status-warning/20"
                onClick={() => handleDefer(action.id)}
                disabled={isProcessing}
              >
                <Clock className="h-3 w-3 mr-0.5" />
                Depois
              </Button>
              <Button
                variant="primary"
                size="sm"
                className="h-6 px-2 text-micro bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active"
                onClick={() => handleAccept(action.id)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
                ) : (
                  <>
                    <Check className="h-3 w-3 mr-0.5" />
                    Aceitar
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          data-testid="proactive-actions-bell-btn"
          variant="ghost"
          size="sm"
          className={cn("relative h-9 w-9 p-0 rounded-full",
            hasUrgent &&"animate-pulse motion-reduce:animate-none",
            className
          )}
        >
          <Bell className={cn("h-5 w-5",
            hasUrgent ?"text-lia-text-secondary" :"text-lia-text-tertiary"
          )} />
          {pendingCount > 0 && (
            <span data-testid="proactive-actions-count" className={cn("absolute -top-0.5 -right-0.5 h-4 min-w-4 rounded-full flex items-center justify-center text-micro font-bold text-white px-1",
              hasUrgent ?"bg-status-error" :"bg-lia-btn-primary-bg"
            )}>
              {pendingCount > 9 ? '9+' : pendingCount}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent 
        className="w-80 p-0" 
        align="end"
        sideOffset={8}
      >
        <div className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-wedo-cyan-dark" />
              <span className="text-xs font-semibold text-lia-text-primary">
                Sugestões da IA
              </span>
            </div>
            {pendingCount > 0 && (
              <Chip variant="neutral" muted className="text-micro">
                {pendingCount} {pendingCount === 1 ? 'nova' : 'novas'}
              </Chip>
            )}
          </div>
        </div>

        <div className="max-h-content-lg overflow-y-auto" role="status" aria-live="polite" aria-label="Carregando...">
          {loading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          ) : visibleActions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 px-4">
              <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mb-3">
                <Brain className="h-5 w-5 text-wedo-cyan" />
              </div>
              <p className="text-xs text-lia-text-tertiary text-center">
                {deferredIds.size > 0 ? 'Todas as sugestões foram adiadas' : 'Nenhuma sugestão pendente'}
              </p>
              {deferredIds.size > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-2 text-micro text-wedo-cyan-dark hover:text-wedo-cyan-dark"
                  onClick={() => setDeferredIds(new Set())}
                >
                  Mostrar adiadas ({deferredIds.size})
                </Button>
              )}
            </div>
          ) : groupedByVacancy.length > 1 ? (
            <div>
              {groupedByVacancy.map((group) => (
                <div key={group.vacancyId}>
                  <div className="px-3 py-1.5 bg-lia-bg-secondary dark:bg-lia-bg-secondary/50">
                    <span className="text-micro font-semibold text-lia-text-secondary uppercase tracking-wide">
                      {group.vacancyTitle}
                    </span>
                    <Chip variant="neutral" className="ml-2 text-micro py-0 h-4">
                      {group.actions.length}
                    </Chip>
                  </div>
                  <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
                    {group.actions.map(renderActionCard)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
              {visibleActions.map(renderActionCard)}
            </div>
          )}
        </div>

        {(visibleActions.length > 0 || deferredIds.size > 0) && (
          <div className="p-2 border-t border-lia-border-subtle flex items-center justify-between">
            {deferredIds.size > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-micro text-lia-text-secondary hover:text-lia-text-secondary"
                onClick={() => setDeferredIds(new Set())}
              >
                <Clock className="h-3 w-3 mr-1" />
                Adiadas ({deferredIds.size})
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto text-xs text-lia-text-secondary hover:text-wedo-cyan-dark"
              onClick={() => setOpen(false)}
            >
              Ver todas as sugestões
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
