"use client"

import React from "react"
import {
  Brain, X, Maximize2, Plus, Eraser, History, ArrowRightLeft,
  Users, Briefcase, LayoutDashboard, Target, Settings,
  BarChart2, BookOpen, MessageCircle,
  type LucideIcon
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { ActionType } from "@/hooks/shared/use-action-intent"
import type { EntityContext } from "@/contexts/lia-float-context"

const CONTEXT_PAGE_ICONS: Record<string, LucideIcon> = {
  "Funil de Talentos": Users,
  "Vagas": Briefcase,
  "Painel de Controle": LayoutDashboard,
  "Decidir": Target,
  "Configurações": Settings,
  "Indicadores": BarChart2,
  "Biblioteca LIA": BookOpen,
  "Conversar": MessageCircle,
}

export interface LiaChatHeaderProps {
  isConnected: boolean
  showHistory: boolean
  messagesLength: number
  activeActionType: ActionType
  actionLabel: string | null
  isReconnecting: boolean
  reconnectAttempt: number
  contextPage?: string | null
  entityContext?: EntityContext | null
  handleNewChat: () => void
  handleClear: () => void
  handleToggleHistory: () => void
  handleExpand: () => void
  close: () => void
  setActiveActionType: (v: ActionType) => void
  setActionLabel: (v: string | null) => void
  onSwitchTask?: () => void
}

export function LiaChatHeader({
  isConnected, showHistory, messagesLength, activeActionType, actionLabel,
  isReconnecting, reconnectAttempt, contextPage, entityContext,
  handleNewChat, handleClear, handleToggleHistory, handleExpand, close,
  setActiveActionType, setActionLabel, onSwitchTask,
}: LiaChatHeaderProps) {
  const ContextIcon = contextPage ? (CONTEXT_PAGE_ICONS[contextPage] || null) : null
  const entityLabel = entityContext?.name
    ? `${entityContext.type === "candidate" ? "Candidato" : "Vaga"}: ${entityContext.name}`
    : null

  return (
    <>
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
          </div>
          <div className="flex flex-col">
            <span className="text-base-ui font-bold text-lia-text-primary leading-tight">LIA</span>
            {(entityLabel || (contextPage && contextPage !== "Conversar")) && (
              <span className="inline-flex items-center gap-1 text-xs text-lia-text-tertiary leading-tight">
                {ContextIcon && <ContextIcon className="w-3 h-3" />}
                <span className="truncate max-w-[180px]">
                  {entityLabel || contextPage}
                </span>
              </span>
            )}
          </div>
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
          {onSwitchTask && (
            <button
              onClick={onSwitchTask}
              className="p-1.5 rounded-md text-lia-text-disabled hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              title="Trocar tarefa (Cmd+K)"
              aria-label="Trocar tarefa"
            >
              <ArrowRightLeft className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={handleToggleHistory}
            className={cn(
              "p-1.5 rounded-md transition-colors",
              showHistory
                ? "text-wedo-cyan-text bg-lia-bg-tertiary"
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
            data-dismiss="true"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

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
