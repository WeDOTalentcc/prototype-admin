'use client'

import React, { useEffect, useRef } from 'react'
import { CheckCircle2, XCircle, Loader2, Clock, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { ToolExecutionResult } from '../hooks/useToolCalling'

export interface ToolExecutionFeedbackProps {
  result?: ToolExecutionResult
  isExecuting?: boolean
  toolName?: string
  onRetry?: () => void
  onRollback?: () => void
  canRollback?: boolean
  className?: string
}

const TOOL_DISPLAY_NAMES: Record<string, string> = {
  publish_job: 'Publicação de Vaga',
  unpublish_job: 'Despublicação de Vaga',
  close_job: 'Encerramento de Vaga',
  move_candidate: 'Movimentação de Candidato',
  send_email: 'Envio de E-mail',
  schedule_interview: 'Agendamento de Entrevista',
  reject_candidate: 'Reprovação de Candidato',
  approve_candidate: 'Aprovação de Candidato',
}

function getToolDisplayName(toolName: string): string {
  return TOOL_DISPLAY_NAMES[toolName] || toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

export function ToolExecutionFeedback({
  result,
  isExecuting = false,
  toolName,
  onRetry,
  onRollback,
  canRollback = false,
  className,
}: ToolExecutionFeedbackProps) {
  const displayName = getToolDisplayName(result?.tool_name || toolName || '')
  const retryButtonRef = useRef<HTMLButtonElement>(null)

  // Focus retry button when error occurs - Accessibility
  useEffect(() => {
    if (result && !result.success && retryButtonRef.current) {
      retryButtonRef.current.focus()
    }
  }, [result])

  if (isExecuting) {
    return (
      <div 
        data-testid="tool-feedback" 
        data-status="executing" 
        role="status"
        aria-live="polite"
        aria-busy="true"
        aria-label={`Executando ${displayName}`}
        className={cn(
          'flex items-center gap-3 p-3 bg-wedo-cyan/10 rounded-md border border-wedo-cyan/30 dark:border-wedo-cyan/30',
          'animate-in fade-in-0 duration-300',
          className
        )}
      >
        <Loader2 className="h-5 w-5 text-wedo-cyan-dark dark:text-wedo-cyan-dark animate-spin flex-shrink-0" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-wedo-cyan-dark dark:text-wedo-cyan-dark">
            Executando {displayName}...
          </p>
          <p className="text-xs text-wedo-cyan-dark dark:text-wedo-cyan-dark">
            Aguarde enquanto processo sua solicitação
          </p>
        </div>
      </div>
    )
  }

  if (!result) return null

  if (result.success) {
    return (
      <div 
        data-testid="tool-feedback" 
        data-status="success" 
        role="status"
        aria-live="polite"
        aria-label={`${displayName} concluída com sucesso`}
        className={cn(
          'flex items-start gap-3 p-3 bg-status-success/10 rounded-md border border-status-success/30 dark:border-status-success/30',
          'animate-in fade-in-0 slide-in-from-bottom-2 duration-300',
          className
        )}
      >
        <CheckCircle2 className="h-5 w-5 text-status-success dark:text-status-success flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-status-success dark:text-status-success">
            {displayName} concluída com sucesso!
          </p>
          <p className="text-xs text-status-success dark:text-status-success mt-0.5">
            {result.message}
          </p>
          {result.execution_time_ms > 0 && (
            <div className="flex items-center gap-1 mt-1.5 text-xs text-status-success dark:text-status-success" aria-label={`Tempo de execução: ${result.execution_time_ms} milissegundos`}>
              <Clock className="h-3 w-3" aria-hidden="true" />
              <span>Executado em {result.execution_time_ms}ms</span>
            </div>
          )}
          {canRollback && onRollback && (
            <Button
              onClick={onRollback}
              variant="ghost"
              size="sm"
              aria-label="Desfazer ação"
              className="mt-2 h-7 text-xs text-status-success hover:text-status-success hover:bg-status-success/15 dark:text-status-success dark:hover:bg-status-success/50 focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 transition-all duration-200"
            >
              <RefreshCw className="h-3 w-3 mr-1" aria-hidden="true" />
              Desfazer
            </Button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div 
      data-testid="tool-feedback" 
      data-status="error" 
      role="alert"
      aria-live="assertive"
      aria-label={`Erro ao executar ${displayName}`}
      className={cn(
        'flex items-start gap-3 p-3 bg-status-error/10 dark:bg-status-error/30 rounded-md border border-status-error/30 dark:border-status-error/30',
        'animate-in fade-in-0 shake-x duration-300',
        className
      )}
    >
      <XCircle className="h-5 w-5 text-status-error dark:text-status-error flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-status-error dark:text-status-error">
          Erro ao executar {displayName}
        </p>
        <p className="text-xs text-status-error dark:text-status-error mt-0.5">
          {result.error || result.message}
        </p>
        {onRetry && (
          <Button
            ref={retryButtonRef}
            onClick={onRetry}
            variant="ghost"
            size="sm"
            aria-label="Tentar novamente"
            className="mt-2 h-7 text-xs text-status-error hover:text-status-error hover:bg-status-error/15 dark:text-status-error dark:hover:bg-status-error/50 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-all duration-200"
          >
            <RefreshCw className="h-3 w-3 mr-1" aria-hidden="true" />
            Tentar novamente
          </Button>
        )}
      </div>
    </div>
  )
}
