'use client'

import React, { useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Check, X, AlertTriangle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ToolCall } from '../hooks/useToolCalling'

export interface ToolConfirmationMessageProps {
  toolCall: ToolCall
  onConfirm: () => void
  onCancel: () => void
  isExecuting?: boolean
  className?: string
}

const TOOL_DISPLAY_NAMES: Record<string, { label: string; icon: string; description: string }> = {
  publish_job: {
    label: 'Publicar Vaga',
    icon: '🚀',
    description: 'Esta ação irá publicar a vaga e torná-la visível para candidatos.',
  },
  unpublish_job: {
    label: 'Despublicar Vaga',
    icon: '📥',
    description: 'Esta ação irá remover a vaga da listagem pública.',
  },
  close_job: {
    label: 'Encerrar Vaga',
    icon: '🔒',
    description: 'Esta ação irá encerrar o processo seletivo desta vaga.',
  },
  move_candidate: {
    label: 'Mover Candidato',
    icon: '➡️',
    description: 'Esta ação irá mover o candidato para outra etapa do processo.',
  },
  send_email: {
    label: 'Enviar E-mail',
    icon: '📧',
    description: 'Esta ação irá enviar um e-mail para o(s) destinatário(s) selecionado(s).',
  },
  schedule_interview: {
    label: 'Agendar Entrevista',
    icon: '📅',
    description: 'Esta ação irá criar um agendamento de entrevista.',
  },
  reject_candidate: {
    label: 'Reprovar Candidato',
    icon: '❌',
    description: 'Esta ação irá reprovar o candidato no processo seletivo.',
  },
  approve_candidate: {
    label: 'Aprovar Candidato',
    icon: '✅',
    description: 'Esta ação irá aprovar o candidato para a próxima etapa.',
  },
}

function getToolInfo(toolName: string) {
  return TOOL_DISPLAY_NAMES[toolName] || {
    label: toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
    icon: '⚡',
    description: `Executar ação: ${toolName}`,
  }
}

export function ToolConfirmationMessage({
  toolCall,
  onConfirm,
  onCancel,
  isExecuting = false,
  className,
}: ToolConfirmationMessageProps) {
  const toolInfo = getToolInfo(toolCall.tool_name)
  const confirmationMessage = toolCall.confirmation_message || `Deseja ${toolInfo.label.toLowerCase()}?`
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const dialogId = `tool-confirmation-${toolCall.tool_name}`

  // Auto-focus confirm button when component mounts - Accessibility
  useEffect(() => {
    if (confirmButtonRef.current && !isExecuting) {
      confirmButtonRef.current.focus()
    }
  }, [isExecuting])

  // Keyboard navigation for confirmation dialog
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && !isExecuting) {
      e.preventDefault()
      onCancel()
    }
  }

  return (
    <div 
      data-testid="tool-confirmation" 
      role="alertdialog"
      aria-modal="true"
      aria-labelledby={`${dialogId}-title`}
      aria-describedby={`${dialogId}-desc`}
      onKeyDown={handleKeyDown}
      className={cn(
        'flex flex-col gap-3 p-4 bg-status-warning/10 dark:bg-status-warning/30 rounded-md border border-status-warning/30 dark:border-status-warning/30',
        'animate-in fade-in-0 slide-in-from-bottom-2 duration-300',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 text-2xl" aria-hidden="true">{toolInfo.icon}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <AlertTriangle className="h-4 w-4 text-status-warning dark:text-status-warning" aria-hidden="true" />
            <span id={`${dialogId}-title`} className="font-medium text-status-warning dark:text-status-warning">
              Confirmação necessária
            </span>
          </div>
          <p id={`${dialogId}-desc`} className="text-sm text-status-warning dark:text-status-warning mb-2">
            {confirmationMessage}
          </p>
          <p className="text-xs text-status-warning dark:text-status-warning">
            {toolInfo.description}
          </p>
        </div>
      </div>

      {Object.keys(toolCall.parameters).length > 0 && (
        <div className="bg-status-warning/15/50 dark:bg-status-warning/30 rounded-md p-2 text-xs" aria-label="Parâmetros da ação">
          <span className="font-medium text-status-warning dark:text-status-warning">Parâmetros:</span>
          <ul className="mt-1 space-y-0.5" role="list">
            {Object.entries(toolCall.parameters).map(([key, value]) => (
              <li key={key} className="text-status-warning dark:text-status-warning">
                <span className="font-medium">{key}:</span>{' '}
                <span>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex items-center gap-2 pt-1" role="group" aria-label="Ações de confirmação">
        <Button
          ref={confirmButtonRef}
          onClick={onConfirm}
          disabled={isExecuting}
          size="sm"
          data-testid="tool-confirm-button"
          aria-label="Confirmar execução"
          aria-busy={isExecuting}
          className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-all duration-200"
        >
          {isExecuting ? (
            <>
              <Loader2 className="h-4 w-4 mr-1.5 animate-spin" aria-hidden="true" />
              <span>Executando...</span>
            </>
          ) : (
            <>
              <Check className="h-4 w-4 mr-1.5" aria-hidden="true" />
              <span>Confirmar</span>
            </>
          )}
        </Button>
        <Button
          onClick={onCancel}
          disabled={isExecuting}
          variant="outline"
          size="sm"
          data-testid="tool-cancel-button"
          aria-label="Cancelar execução"
          className="border-status-warning/30 dark:border-status-warning/30 hover:bg-status-warning/15 dark:hover:bg-status-warning/50 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 transition-all duration-200"
        >
          <X className="h-4 w-4 mr-1.5" aria-hidden="true" />
          <span>Cancelar</span>
        </Button>
        {!isExecuting && (
          <span className="text-xs text-status-warning dark:text-status-warning ml-2" aria-hidden="true">
            ou digite &quot;sim&quot; / &quot;não&quot;
          </span>
        )}
      </div>
      
      {/* Screen reader announcement */}
      <div className="sr-only" role="status" aria-live="polite">
        {isExecuting ? `Executando ${toolInfo.label}. Aguarde.` : `Confirmação necessária para ${toolInfo.label}. Use Enter para confirmar ou Escape para cancelar.`}
      </div>
    </div>
  )
}
