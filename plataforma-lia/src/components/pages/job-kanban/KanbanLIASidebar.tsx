"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { CandidateQueriesGuide } from "@/components/ui/candidate-queries-guide"
import { LIASuggestionsPanel } from "@/components/pages/job-kanban/LIASuggestionsPanel"
import { ActionResultCard } from "@/components/chat/action-result-card"
import {
  Brain,
  RotateCcw,
  Maximize2,
  X,
  Users,
  Lightbulb,
  ChevronUp,
  ChevronDown,
  Clock,
  TrendingUp,
  AlertTriangle,
  Loader2,
  Send,
  Star,
} from "lucide-react"

interface LIAMessage {
  id: string
  type: "user" | "assistant"
  content: string
  metadata?: Record<string, unknown>
}

interface LIASuggestion {
  type: string
  message: string
  suggested_action: string
  candidate_id: string
}

interface KanbanLIASidebarProps {
  liaMessages: LIAMessage[]
  liaPromptValue: string
  isLiaLoading: boolean
  liaExpandedWidth: number
  computedSuggestions: LIASuggestion[]
  showLiaSuggestionsPanel: boolean
  selectedCandidates: Set<string>
  isResizingLIA: boolean
  candidatesData: Record<string, unknown[]>
  chatScrollRef: React.RefObject<HTMLDivElement>
  setLiaMessages: (messages: LIAMessage[] | ((prev: LIAMessage[]) => LIAMessage[])) => void
  setLiaPromptValue: (value: string | ((prev: string) => string)) => void
  setLiaExpandedWidth: (width: number | ((prev: number) => number)) => void
  setShowExpandedLIA: (value: boolean) => void
  setUserCollapsedLIA: (value: boolean) => void
  setShowLiaSuggestionsPanel: (value: boolean | ((prev: boolean) => boolean)) => void
  setSelectedCandidates: (value: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  setIsResizingLIA: (value: boolean) => void
  setSelectedCandidate: (candidate: Record<string, unknown>) => void
  setShowCandidatePage: (value: boolean) => void
  openSuperChat: () => void
  handleAICommand: (command: string) => void
  handleLiaUiAction: (action: string, params: Record<string, unknown>) => void
}

export function KanbanLIASidebar({
  liaMessages,
  liaPromptValue,
  isLiaLoading,
  liaExpandedWidth,
  computedSuggestions,
  showLiaSuggestionsPanel,
  selectedCandidates,
  isResizingLIA,
  candidatesData,
  chatScrollRef,
  setLiaMessages,
  setLiaPromptValue,
  setLiaExpandedWidth,
  setShowExpandedLIA,
  setUserCollapsedLIA,
  setShowLiaSuggestionsPanel,
  setSelectedCandidates,
  setIsResizingLIA,
  setSelectedCandidate,
  setShowCandidatePage,
  openSuperChat,
  handleAICommand,
  handleLiaUiAction,
}: KanbanLIASidebarProps) {
  return (
    <div
      className="flex-shrink-0 transition-colors motion-reduce:transition-none duration-300 pl-4 py-4 pr-0 relative"
      style={{width: `${liaExpandedWidth}px`}}
    >
      <Card className="h-[calc(100vh-16rem)] flex flex-col overflow-hidden border border-lia-border-default bg-lia-bg-primary dark:bg-lia-bg-secondary max-h-[calc(100vh-16rem)]">
        {/* Mensagem de Apresentação da LIA */}
        <div className="flex-shrink-0 px-4 py-3 bg-lia-bg-primary dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div
                className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0 bg-lia-bg-secondary dark:bg-lia-bg-primary"
              >
                <Brain className="w-6 h-6 text-wedo-cyan" strokeWidth={2.5} />
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="text-sm font-semibold leading-tight truncate text-lia-text-primary">
                  Olá! Sou a Lia.
                </h3>
                <p className="text-xs leading-tight truncate mt-0.5 text-lia-text-tertiary">
                  Como posso te ajudar hoje?
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {liaMessages.length > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setLiaMessages([])}
                  title="Nova conversa"
                  className="h-7 w-7 p-0 rounded-full hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none flex-shrink-0"
                >
                  <RotateCcw className="w-3.5 h-3.5 text-lia-text-disabled" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => openSuperChat()}
                title="Expandir chat"
                className="h-7 w-7 p-0 rounded-full hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none flex-shrink-0"
              >
                <Maximize2 className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowExpandedLIA(false)
                  setUserCollapsedLIA(true)
                }}
                className="h-7 w-7 p-0 rounded-full hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none flex-shrink-0"
              >
                <X className="w-4 h-4 text-lia-text-tertiary" />
              </Button>
            </div>
          </div>
        </div>

        {/* Indicador de candidatos selecionados - Estilo padronizado */}
        {selectedCandidates.size > 0 && (
          <div className="flex-shrink-0 px-4 py-2">
            <div className="px-3 py-2 bg-lia-bg-tertiary rounded-md border border-lia-border-subtle flex items-center gap-2">
              <Users className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0" />
              <span className="text-xs text-lia-text-secondary font-medium" aria-live="polite" aria-atomic="true">
                {selectedCandidates.size} candidato{selectedCandidates.size > 1 ? 's' : ''} selecionado{selectedCandidates.size > 1 ? 's' : ''}
              </span>
              <button
                onClick={() => setSelectedCandidates(new Set())}
                className="ml-auto p-1 rounded-md hover:bg-lia-interactive-active"
              >
                <X className="w-3 h-3 text-lia-text-tertiary" />
              </button>
            </div>
          </div>
        )}

        {/* Sugestões Proativas da LIA */}
        {computedSuggestions.length > 0 && (
          <div className="flex-shrink-0 px-4 py-2">
            <button
              onClick={() => setShowLiaSuggestionsPanel(prev => !prev)}
              className="w-full flex items-center justify-between px-3 py-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
            >
              <div className="flex items-center gap-2">
                <Lightbulb className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-semibold text-lia-text-secondary">Sugestões da LIA</span>
                <Badge className="bg-wedo-cyan text-white border-0 text-micro px-1.5 py-0 h-4 min-w-[18px] flex items-center justify-center">
                  {computedSuggestions.length}
                </Badge>
              </div>
              {showLiaSuggestionsPanel ? (
                <ChevronUp className="w-3.5 h-3.5 text-lia-text-tertiary" />
              ) : (
                <ChevronDown className="w-3.5 h-3.5 text-lia-text-tertiary" />
              )}
            </button>
            {showLiaSuggestionsPanel && (
              <div className="space-y-1.5 mt-2 max-h-chart-sm overflow-y-auto">
                {computedSuggestions.map((suggestion, idx) => {
                  const borderColor = suggestion.type === 'stale_candidate' ? 'border-l-status-warning' : suggestion.type === 'high_score' ? 'border-l-status-success' : 'border-l-status-error'
                  const IconComponent = suggestion.type === 'stale_candidate' ? Clock : suggestion.type === 'high_score' ? TrendingUp : AlertTriangle
                  const iconColor = suggestion.type === 'stale_candidate' ? 'text-status-warning' : suggestion.type === 'high_score' ? 'text-status-success' : 'text-status-error'
                  return (
                    <div key={`suggestion-${idx}`} className={`border-l-2 ${borderColor} bg-lia-bg-primary rounded-md px-2.5 py-2 border border-lia-border-subtle`}>
                      <div className="flex items-start gap-2">
                        <IconComponent className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${iconColor}`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs text-lia-text-secondary leading-tight">{suggestion.message}</p>
                          <p className="text-micro text-lia-text-tertiary mt-0.5">{suggestion.suggested_action}</p>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            const candidate = Object.values(candidatesData).flat().find((c: { id?: string }) => c.id === suggestion.candidate_id)
                            if (candidate) {
                              setSelectedCandidate(candidate as any)
                              setShowCandidatePage(true)
                            }
                          }}
                          className="text-wedo-cyan"
                        >
                          Ver
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* Área de Mensagens do Chat - Só aparece quando há mensagens */}
        {liaMessages.length > 0 ? (
          <div className="flex-1 overflow-y-auto px-3 py-2 space-y-3">
            {liaMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.type === 'user' ? (
                  <div className="flex items-start gap-2 max-w-[90%]">
                    <div className="w-6 h-6 rounded-full bg-lia-bg-elevated flex items-center justify-center flex-shrink-0 text-xs font-medium text-lia-text-secondary">
                      U
                    </div>
                    <div
                      className="px-2.5 py-2 rounded-md bg-lia-bg-tertiary"
                    >
                      <p className="text-xs text-lia-text-primary leading-relaxed">{msg.content}</p>
                    </div>
                  </div>
                ) : (
                  <div
                    className="max-w-[90%] group"
                  >
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0">
                        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                      </div>
                      <div className="pt-0.5 flex-1">
                        <div className="flex items-center gap-1 mb-0.5">
                          <span className="text-micro font-bold text-lia-text-primary" >LIA</span>
                        </div>
                        <div className="text-xs text-lia-text-primary space-y-1 leading-relaxed">
                          {msg.content.split('\n').map((line, i) => {
                            if (line.startsWith('•')) {
                              return <p key={i} className="pl-2">{line}</p>
                            }
                            if (line.match(/^\d+\./)) {
                              return <p key={i} className="pl-2">{line}</p>
                            }
                            if (line.includes('**')) {
                              const parts = line.split(/\*\*(.*?)\*\*/g)
                              return (
                                <p key={i}>
                                  {parts.map((part, j) =>
                                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                                  )}
                                </p>
                              )
                            }
                            return line ? <p key={i}>{line}</p> : null
                          })}
                        </div>
                        {(msg as any).metadata?.action_executed && (msg as any).metadata?.action_result && (
                          <ActionResultCard
                            actionType={((msg as { metadata?: { action_executed?: boolean; action_result?: unknown; action_type?: string; is_fallback?: boolean; ui_action?: string; ui_action_params?: Record<string, unknown> } }).metadata?.action_type || 'move_candidate') as any}
                            result={((msg as { metadata?: { action_executed?: boolean; action_result?: unknown; action_type?: string; is_fallback?: boolean; ui_action?: string; ui_action_params?: Record<string, unknown> } }).metadata?.action_result) as any}
                          />
                        )}
                        {(msg as { metadata?: { action_executed?: boolean; action_result?: unknown; action_type?: string; is_fallback?: boolean; ui_action?: string; ui_action_params?: Record<string, unknown> } }).metadata?.is_fallback && (
                          <button
                            onClick={() => handleLiaUiAction(
                              (msg as { metadata?: { action_executed?: boolean; action_result?: unknown; action_type?: string; is_fallback?: boolean; ui_action?: string; ui_action_params?: Record<string, unknown> } }).metadata?.ui_action as string,
                              (msg as { metadata?: { action_executed?: boolean; action_result?: unknown; action_type?: string; is_fallback?: boolean; ui_action?: string; ui_action_params?: Record<string, unknown> } }).metadata?.ui_action_params || {}
                            )}
                            className="mt-2 px-3 py-1.5 text-xs font-medium text-white bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover rounded-md transition-colors motion-reduce:transition-none"
                            
                          >
                            Abrir manualmente
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {isLiaLoading && (
              <div className="flex justify-start" role="status" aria-live="polite" aria-label="Carregando...">
                <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-lia-bg-tertiary dark:bg-lia-bg-secondary" role="status" aria-live="polite" aria-label="Carregando...">
                  <div className="w-5 h-5 rounded-md bg-lia-bg-primary flex items-center justify-center" role="status" aria-live="polite" aria-label="Carregando...">
                    <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
                  </div>
                  <span className="text-micro text-lia-text-tertiary">Pensando...</span>
                </div>
              </div>
            )}

            <div ref={chatScrollRef} />
          </div>
        ) : (
          /* Espaço flexível vazio quando não há mensagens - empurra conteúdo para baixo */
          <div className="flex-1" />
        )}

        {/* Input Area - Fixo na parte inferior */}
        <div className="flex-shrink-0 px-4 pb-4 pt-2">
          {/* Campo de Input */}
          <div className="flex items-center gap-2 p-2 rounded-md border bg-lia-bg-primary border-lia-border-subtle">
            <input
              type="text"
              placeholder="Envie mensagem para a LIA..."
              value={liaPromptValue}
              onChange={(e) => setLiaPromptValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && liaPromptValue.trim() && !isLiaLoading) {
                  handleAICommand(liaPromptValue);
                  setLiaPromptValue('');
                }
              }}
              disabled={isLiaLoading}
              className="flex-1 text-xs bg-transparent focus:outline-none text-lia-text-primary disabled:opacity-50"
            />
            <AudioRecordButton
              onTranscription={(text) => setLiaPromptValue(prev => prev ? `${prev} ${text}` : text)}
              className="w-7 h-7 rounded-md flex items-center justify-center hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none"
            />
            <button
              type="button"
              onClick={() => {
                if (liaPromptValue.trim() && !isLiaLoading) {
                  handleAICommand(liaPromptValue);
                  setLiaPromptValue('');
                }
              }}
              disabled={!liaPromptValue.trim() || isLiaLoading}
              className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none disabled:opacity-50 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover dark:bg-lia-bg-secondary dark:hover:bg-lia-interactive-active"
            >
              <Send className="w-3.5 h-3.5 text-white" />
            </button>
          </div>

          {/* Sugestões de Análises - Abaixo do input */}
          <div className="flex items-center gap-1.5 mt-2">
            <span className="text-micro font-medium text-lia-text-tertiary">Sugestões:</span>
            <button
              onClick={() => setLiaPromptValue('Rankear candidatos desta vaga')}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full hover:bg-lia-interactive-active transition-[width,height]"
            >
              <Star className="w-2.5 h-2.5 text-lia-text-tertiary" />
              Rankear
            </button>
            <button
              onClick={() => setLiaPromptValue('Comparar os melhores candidatos')}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-micro font-medium text-lia-text-secondary bg-lia-bg-tertiary rounded-full hover:bg-lia-interactive-active transition-[width,height]"
            >
              <Users className="w-2.5 h-2.5 text-lia-text-tertiary" />
              Comparar
            </button>
            <CandidateQueriesGuide
              onSelectQuery={(query) => setLiaPromptValue(query)}
              className="!px-2 !py-0.5 !text-micro !bg-lia-bg-tertiary !border-0 hover:!bg-lia-interactive-active"
            />
          </div>
        </div>
      </Card>
      {/* Barra de redimensionamento */}
      <div
        className="absolute right-0 top-0 w-2 h-full cursor-ew-resize group flex items-center justify-center z-10"
        onMouseDown={(e) => {
          e.preventDefault()
          setIsResizingLIA(true)
        }}
      >
        <div className="w-0.5 h-12 bg-lia-border-default dark:bg-lia-bg-elevated group-hover:bg-lia-border-medium dark:group-hover:bg-lia-border-medium rounded-full transition-colors motion-reduce:transition-none" />
      </div>
    </div>
  )
}
