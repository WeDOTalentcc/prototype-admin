"use client"

import React from "react"
import { Brain, X, Maximize2, Plus, Eraser, History } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ActionType } from "@/hooks/use-action-intent"

export interface LiaChatHeaderProps {
  isConnected: boolean
  showHistory: boolean
  messagesLength: number
  activeActionType: ActionType
  actionLabel: string | null
  isReconnecting: boolean
  reconnectAttempt: number
  handleNewChat: () => void
  handleClear: () => void
  handleToggleHistory: () => void
  handleExpand: () => void
  close: () => void
  setActiveActionType: (v: ActionType) => void
  setActionLabel: (v: string | null) => void
}

export function LiaChatHeader({
  isConnected, showHistory, messagesLength, activeActionType, actionLabel,
  isReconnecting, reconnectAttempt,
  handleNewChat, handleClear, handleToggleHistory, handleExpand, close,
  setActiveActionType, setActionLabel,
}: LiaChatHeaderProps) {
  return (
    <>
      <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
          </div>
          <span className="text-base-ui font-bold text-lia-text-primary" >LIA</span>
          {isConnected && (
            <span className="w-1.5 h-1.5 rounded-full bg-status-success flex-shrink-0" title="Conectado" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Novo chat"
            aria-label="Iniciar novo chat"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleClear}
            disabled={messagesLength === 0}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-30 disabled:cursor-not-allowed"
            title="Limpar mensagens"
            aria-label="Limpar mensagens"
          >
            <Eraser className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleToggleHistory}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              showHistory
                ? "text-wedo-cyan bg-lia-bg-tertiary"
                : "text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
            )}
            title="Histórico de conversas"
            aria-label="Ver histórico de conversas"
            aria-expanded={showHistory}
          >
            <History className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-lia-interactive-active mx-0.5" />
          <button
            onClick={handleExpand}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Expandir para chat completo"
            aria-label="Expandir chat"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={close}
            className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Fechar"
            aria-label="Fechar chat"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {activeActionType && actionLabel && (
        <div className="px-4 py-1.5 bg-lia-bg-secondary border-b border-lia-border-subtle flex items-center justify-between flex-shrink-0">
          <span className="text-xs text-lia-text-tertiary font-medium">
            {actionLabel}
          </span>
          <button
            onClick={() => { setActiveActionType(null); setActionLabel(null) }}
            className="text-xs text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none"
            aria-label="Sair do modo de ação"
          >
            Sair
          </button>
        </div>
      )}

      {isReconnecting && (
        <div className="px-4 py-1.5 border-b flex-shrink-0 bg-status-warning/10 border-status-warning/30 dark:border-status-warning/30">
          <p className="text-xs text-status-warning">
            {`Reconectando… (tentativa ${reconnectAttempt}/3)`}
          </p>
        </div>
      )}
    </>
  )
}
