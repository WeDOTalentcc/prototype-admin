"use client"

import React, { useState, useEffect, useMemo } from "react"
import { Bell, Loader2, Brain, Check, X, ArrowRight, Clock, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { getProactiveActions, acceptProactiveAction, rejectProactiveAction } from "@/services/lia-api"

import { ProactiveAction as ApiProactiveAction } from "@/services/lia-api"

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
  if (score >= 80) return "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 dark:text-emerald-400"
  if (score >= 60) return "text-amber-600 bg-amber-50 dark:bg-amber-900/30 dark:text-amber-400"
  return "text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400"
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
      console.error('Erro ao carregar ações:', error)
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
      console.error('Erro ao aceitar ação:', error)
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
      console.error('Erro ao rejeitar ação:', error)
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
      const vacId = action.vacancy?.id || (action.suggested_action as any)?.vacancy_id
      const vacTitle = action.vacancy?.title || (action.suggested_action as any)?.vacancy_title
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
    const candidate = action.candidate || (action.suggested_action as any)?.candidate

    return (
      <div
        key={action.id}
        className="p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-start gap-2">
          {candidate ? (
            <Avatar className="h-8 w-8 flex-shrink-0">
              <AvatarImage src={candidate.avatar_url} alt={candidate.name} />
              <AvatarFallback className="text-micro bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                {candidate.name?.split(' ').map((n: string) => n[0]).slice(0, 2).join('').toUpperCase() || '??'}
              </AvatarFallback>
            </Avatar>
          ) : (
            <div className={cn(
              "w-2 h-2 rounded-full mt-1.5 shrink-0",
              action.priority === 'urgent' && "bg-red-500",
              action.priority === 'high' && "bg-orange-500",
              action.priority === 'normal' && "bg-blue-500",
              action.priority === 'low' && "bg-gray-400"
            )} />
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 min-w-0">
                <p className="text-xs font-medium text-gray-900 dark:text-gray-100 line-clamp-1">
                  {candidate?.name || action.title}
                </p>
                {candidate?.score && (
                  <span className={cn(
                    "text-micro font-bold px-1.5 py-0.5 rounded-full flex-shrink-0",
                    getScoreColor(candidate.score)
                  )}>
                    {Math.round(candidate.score)}
                  </span>
                )}
              </div>
              <span className="text-micro text-gray-400 shrink-0">
                {formatTimeAgo(action.created_at)}
              </span>
            </div>
            {candidate && (
              <p className="text-micro font-medium text-gray-700 dark:text-gray-300 line-clamp-1 mt-0.5">
                {action.title}
              </p>
            )}
            <p className="text-micro text-gray-500 dark:text-gray-400 line-clamp-2 mt-0.5">
              {action.description}
            </p>
            <div className="flex items-center gap-1 mt-2">
              <ArrowRight className="h-3 w-3 text-gray-600 dark:text-gray-400 shrink-0" />
              <span className="text-micro text-gray-600 dark:text-gray-400 font-medium line-clamp-1">
                {typeof action.suggested_action === 'string' 
                  ? action.suggested_action 
                  : action.suggested_action?.label || action.suggested_action?.action || 'Ver detalhes'}
              </span>
            </div>
            <div className="flex items-center gap-1 mt-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-gray-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                onClick={() => handleReject(action.id)}
                disabled={isProcessing}
              >
                <X className="h-3 w-3 mr-0.5" />
                Ignorar
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-gray-500 hover:text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-900/20"
                onClick={() => handleDefer(action.id)}
                disabled={isProcessing}
              >
                <Clock className="h-3 w-3 mr-0.5" />
                Depois
              </Button>
              <Button
                variant="default"
                size="sm"
                className="h-6 px-2 text-micro bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-100 dark:text-gray-900 dark:hover:bg-gray-200"
                onClick={() => handleAccept(action.id)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
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
          variant="ghost"
          size="sm"
          className={cn(
            "relative h-9 w-9 p-0 rounded-full",
            hasUrgent && "animate-pulse",
            className
          )}
        >
          <Bell className={cn(
            "h-5 w-5",
            hasUrgent ? "text-gray-600 dark:text-gray-400" : "text-gray-500"
          )} />
          {pendingCount > 0 && (
            <span className={cn(
              "absolute -top-0.5 -right-0.5 h-4 min-w-4 rounded-full flex items-center justify-center text-micro font-bold text-white px-1",
              hasUrgent ? "bg-red-500" : "bg-gray-900 dark:bg-gray-50"
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
        <div className="p-3 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-wedo-cyan-dark" />
              <span className="text-xs font-semibold text-gray-900 dark:text-gray-100">
                Sugestões da LIA
              </span>
            </div>
            {pendingCount > 0 && (
              <Badge variant="secondary" className="text-micro">
                {pendingCount} {pendingCount === 1 ? 'nova' : 'novas'}
              </Badge>
            )}
          </div>
        </div>

        <div className="max-h-[400px] overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-gray-600 dark:text-gray-400" />
            </div>
          ) : visibleActions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 px-4">
              <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mb-3">
                <Brain className="h-5 w-5 text-wedo-cyan" />
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
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
                  <div className="px-3 py-1.5 bg-gray-50 dark:bg-gray-800/50 border-b border-gray-100 dark:border-gray-800">
                    <span className="text-micro font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">
                      {group.vacancyTitle}
                    </span>
                    <Badge variant="outline" className="ml-2 text-micro py-0 h-4">
                      {group.actions.length}
                    </Badge>
                  </div>
                  <div className="divide-y divide-gray-100 dark:divide-gray-800">
                    {group.actions.map(renderActionCard)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {visibleActions.map(renderActionCard)}
            </div>
          )}
        </div>

        {(visibleActions.length > 0 || deferredIds.size > 0) && (
          <div className="p-2 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between">
            {deferredIds.size > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-micro text-gray-500 hover:text-gray-700"
                onClick={() => setDeferredIds(new Set())}
              >
                <Clock className="h-3 w-3 mr-1" />
                Adiadas ({deferredIds.size})
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              className="ml-auto text-xs text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark"
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
