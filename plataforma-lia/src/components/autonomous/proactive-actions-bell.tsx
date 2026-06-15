"use client"

import React, { useState, useMemo } from "react"
import { Bell, Loader2, Brain, X, ArrowRight, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { useProactiveHints, type ProactiveHint } from "@/hooks/proactive/use-proactive-hints"

interface ProactiveActionsBellProps {
  className?: string
}

function getSeverityColor(severity: string): string {
  if (severity === "critical") return "bg-status-error"
  if (severity === "high") return "bg-wedo-orange"
  if (severity === "medium") return "bg-lia-btn-primary-bg"
  return "bg-lia-border-medium"
}

function getSeverityDotClass(severity: string): string {
  if (severity === "critical") return "bg-status-error"
  if (severity === "high") return "bg-wedo-orange"
  if (severity === "medium") return "bg-wedo-cyan"
  return "bg-lia-border-medium"
}

export function ProactiveActionsBell({
  className,
}: ProactiveActionsBellProps) {
  const { hints, isLoading, dismiss } = useProactiveHints()
  const [open, setOpen] = useState(false)
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [deferredIds, setDeferredIds] = useState<Set<string>>(new Set())

  const handleDismiss = async (hintId: string) => {
    setProcessingId(hintId)
    try {
      await dismiss(hintId)
    } catch {
      // dismiss errors are non-fatal — SWR will revalidate
    }
    setProcessingId(null)
  }

  const handleDefer = (hintId: string) => {
    setDeferredIds(prev => new Set([...prev, hintId]))
  }

  const formatTimeAgo = (dateString: string | null) => {
    if (!dateString) return ""
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)

    if (diffMins < 1) return "Agora"
    if (diffMins < 60) return `${diffMins}min`
    if (diffHours < 24) return `${diffHours}h`
    return `${Math.floor(diffMs / 86400000)}d`
  }

  const visibleHints = useMemo(() => {
    return hints.filter(h => !deferredIds.has(h.id))
  }, [hints, deferredIds])

  const pendingCount = visibleHints.length
  const hasUrgent = visibleHints.some(h => h.severity === "critical" || h.severity === "high")

  const renderHintCard = (hint: ProactiveHint) => {
    const isProcessing = processingId === hint.id

    return (
      <div
        key={hint.id}
        data-testid={`proactive-hint-card-${hint.id}`}
        className="p-3 hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover/50 transition-colors motion-reduce:transition-none"
      >
        <div className="flex items-start gap-2">
          <div className={cn(
            "w-2 h-2 rounded-full mt-1.5 shrink-0",
            getSeverityDotClass(hint.severity)
          )} />
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <p className="text-xs font-medium text-lia-text-primary line-clamp-1">
                {hint.title}
              </p>
              <span className="text-micro text-lia-text-secondary shrink-0">
                {formatTimeAgo(hint.created_at)}
              </span>
            </div>
            <p className="text-micro text-lia-text-tertiary line-clamp-2 mt-0.5">
              {hint.message}
            </p>
            {hint.action && (
              <div className="flex items-center gap-1 mt-2">
                <ArrowRight className="h-3 w-3 text-lia-text-secondary shrink-0" />
                <span className="text-micro text-lia-text-secondary font-medium line-clamp-1">
                  {hint.action}
                </span>
              </div>
            )}
            <div className="flex items-center gap-1 mt-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-lia-text-secondary hover:text-status-error hover:bg-status-error/10 dark:hover:bg-status-error/20"
                onClick={() => handleDismiss(hint.id)}
                disabled={isProcessing}
              >
                {isProcessing ? (
                  <Loader2 className="h-3 w-3 animate-spin motion-reduce:animate-none" />
                ) : (
                  <>
                    <X className="h-3 w-3 mr-0.5" />
                    Dispensar
                  </>
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-micro text-lia-text-secondary hover:text-status-warning hover:bg-status-warning/10 dark:hover:bg-status-warning/20"
                onClick={() => handleDefer(hint.id)}
                disabled={isProcessing}
              >
                <Clock className="h-3 w-3 mr-0.5" />
                Depois
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
          className={cn(
            "relative h-9 w-9 p-0 rounded-full",
            hasUrgent && "animate-pulse motion-reduce:animate-none",
            className
          )}
        >
          <Bell className={cn(
            "h-5 w-5",
            hasUrgent ? "text-lia-text-secondary" : "text-lia-text-tertiary"
          )} />
          {pendingCount > 0 && (
            <span
              data-testid="proactive-actions-count"
              className={cn(
                "absolute -top-0.5 -right-0.5 h-4 min-w-4 rounded-full flex items-center justify-center text-micro font-bold text-white px-1",
                getSeverityColor(hasUrgent ? "critical" : "medium")
              )}
            >
              {pendingCount > 9 ? "9+" : pendingCount}
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
                {pendingCount} {pendingCount === 1 ? "nova" : "novas"}
              </Chip>
            )}
          </div>
        </div>

        <div
          className="max-h-content-lg overflow-y-auto"
          role="status"
          aria-live="polite"
          aria-label="Sugestões proativas da IA"
        >
          {isLoading ? (
            <div className="flex items-center justify-center py-8" role="status" aria-live="polite">
              <Loader2 className="h-5 w-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          ) : visibleHints.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 px-4">
              <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mb-3">
                <Brain className="h-5 w-5 text-wedo-cyan" />
              </div>
              <p className="text-xs text-lia-text-tertiary text-center">
                {deferredIds.size > 0
                  ? "Todas as sugestões foram adiadas"
                  : "Nenhuma sugestão pendente"}
              </p>
              {deferredIds.size > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="mt-2 text-micro text-lia-text-muted hover:text-wedo-cyan-dark"
                  onClick={() => setDeferredIds(new Set())}
                >
                  Mostrar adiadas ({deferredIds.size})
                </Button>
              )}
            </div>
          ) : (
            <div className="divide-y divide-lia-border-subtle dark:divide-lia-border-strong">
              {visibleHints.map(renderHintCard)}
            </div>
          )}
        </div>

        {(visibleHints.length > 0 || deferredIds.size > 0) && (
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
              Fechar
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  )
}
