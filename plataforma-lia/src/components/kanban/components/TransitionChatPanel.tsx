"use client"

import { useState, useEffect, useRef } from 'react'
import {
  AlertTriangle,
  Brain,
  CheckCircle2,
  ExternalLink,
  Lightbulb,
  Loader2,
  Mic,
  Plus,
  Eraser,
  History,
  Clock,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  XCircle,
  Send,
  User,
  X,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { isClearChatCommand } from '@/lib/chat-commands'
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from '@/lib/chat-format'
import { MessageFeedback } from '@/components/chat/message-feedback'
import type { ChatMessage, TaskItem, LearnedSuggestion } from '@/hooks/use-interpret-context'

interface TransitionChatPanelProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSendMessage: (message: string) => void
  onClearChat?: () => void
  onNewChat?: () => void
  onToggleHistory?: () => void
  onClose?: () => void
  actionBehavior: string
  placeholder?: string
  extractedPreferences?: Record<string, any> | null
  sessionId?: string
}

const BEHAVIOR_DESCRIPTIONS: Record<string, string> = {
  screening: 'Posso ajudar com triagem, critérios e comunicação.',
  scheduling: 'Posso agendar entrevistas e gerenciar horários.',
  evaluation: 'Posso configurar testes e avaliações técnicas.',
  verification: 'Posso solicitar documentos e verificações.',
  offer: 'Posso ajudar com propostas e negociação.',
  conclusion_rejected: 'Posso ajudar com feedback e notificação.',
  conclusion_hired: 'Posso confirmar contratação e onboarding.',
}

const PREFERENCE_LABELS: Record<string, string> = {
  date: 'Data', time: 'Hora', format: 'Formato', location: 'Local',
  interviewer: 'Entrevistador', duration: 'Duração', urgency: 'Urgência',
  notes: 'Obs', type: 'Tipo', platform: 'Plataforma',
  screening_type: 'Triagem', deadline: 'Prazo',
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

function TasksChecklist({ tasks }: { tasks: TaskItem[] }) {
  return (
    <div className="mt-2 pt-2 border-t border-gray-200/30">
      <p className="text-micro font-semibold text-gray-500 uppercase tracking-wider mb-1" style={{ fontFamily: 'Inter, sans-serif' }}>
        Tarefas agendadas
      </p>
      {tasks.map((task, idx) => (
        <div
          key={idx}
          className="flex items-start gap-1.5 py-0.5"
        >
          <CheckCircle2 className="w-3 h-3 text-chat-cyan flex-shrink-0 mt-0.5" />
          <span className="text-xs text-gray-600">
            {task.description || task.type}
            {task.data_type && <span className="text-gray-400 ml-1">({task.data_type})</span>}
          </span>
        </div>
      ))}
    </div>
  )
}

function OutOfScopeIndicator() {
  return (
    <div className="mt-2 pt-2 border-t border-status-warning/30/50">
      <div className="flex items-center gap-1.5">
        <ExternalLink className="w-3 h-3 text-status-warning flex-shrink-0" />
        <span className="text-micro font-medium text-status-warning" style={{ fontFamily: 'Inter, sans-serif' }}>
          Fora do escopo desta conversa
        </span>
      </div>
    </div>
  )
}

function FairnessWarning({ fairnessResult }: { fairnessResult: { is_fair: boolean; warnings: string[]; educational_message?: string } }) {
  if (fairnessResult.is_fair) return null

  return (
    <div className="mt-2 pt-2 border-t border-status-error/30/50">
      <div className="flex items-start gap-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-status-error flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-xs font-semibold text-status-error" style={{ fontFamily: 'Inter, sans-serif' }}>
            Alerta de Fairness
          </p>
          {fairnessResult.warnings.map((w, idx) => (
            <p key={idx} className="text-micro text-status-error mt-0.5">
              {w}
            </p>
          ))}
        </div>
      </div>
    </div>
  )
}

function LearnedSuggestionsChips({ suggestions, onAccept }: { suggestions: LearnedSuggestion[]; onAccept: (s: LearnedSuggestion) => void }) {
  if (!suggestions.length) return null

  return (
    <div className="mt-2 pt-2 border-t border-gray-200/30">
      <div className="flex items-center gap-1 mb-1">
        <Lightbulb className="w-3 h-3 text-status-warning" />
        <span className="text-micro font-medium text-gray-500" style={{ fontFamily: 'Inter, sans-serif' }}>
          Baseado no seu histórico
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onAccept(s)}
            className="inline-flex items-center gap-1 px-2 py-0.5 bg-status-warning/10 border border-status-warning/30 rounded text-micro text-status-warning hover:bg-status-warning/15 transition-colors"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            <Sparkles className="w-2.5 h-2.5" />
            {s.key}: {s.value}
          </button>
        ))}
      </div>
    </div>
  )
}

function ConfidenceBadge({ confidence, layer }: { confidence?: number; layer?: number }) {
  if (!confidence && confidence !== 0) return null

  const pct = Math.round(confidence * 100)
  const color = pct >= 80 ? 'text-status-success' : pct >= 50 ? 'text-status-warning' : 'text-status-error'

  return (
    <span className={cn("text-micro font-medium ml-1", color)} style={{ fontFamily: 'Inter, sans-serif' }}>
      {pct}%{layer === 3 && <span className="text-gray-400 ml-0.5">AI</span>}
    </span>
  )
}

function RichContent({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export function TransitionChatPanel({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  onNewChat,
  onToggleHistory,
  onClose,
  actionBehavior,
  placeholder,
  extractedPreferences,
  sessionId,
}: TransitionChatPanelProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = () => {
    const trimmed = inputValue.trim()
    if (!trimmed || isLoading) return
    if (isClearChatCommand(trimmed) && onClearChat) {
      onClearChat()
      setInputValue('')
      return
    }
    onSendMessage(trimmed)
    setInputValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleLearnedSuggestionAccept = (s: LearnedSuggestion) => {
    onSendMessage(`Sim, use ${s.key}: ${s.value}`)
  }

  const canSend = inputValue.trim().length > 0 && !isLoading

  return (
    <div className="flex flex-col h-full overflow-hidden p-3">
      <div className="flex flex-col flex-1 overflow-hidden rounded-xl border border-gray-200 bg-white dark:bg-gray-900">
        {/* Header */}
        <div className="flex-shrink-0 px-4 py-3 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full flex items-center justify-center">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <span className="text-base-ui font-bold text-gray-900 dark:text-gray-50" style={{ fontFamily: 'Inter, sans-serif' }}>
                LIA
              </span>
            </div>
            <div className="flex items-center gap-1">
              {onNewChat && (
                <button
                  onClick={onNewChat}
                  title="Novo chat"
                  aria-label="Iniciar novo chat"
                  className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              )}
              {onClearChat && (
                <button
                  onClick={onClearChat}
                  disabled={messages.length === 0}
                  title="Limpar mensagens"
                  aria-label="Limpar mensagens"
                  className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Eraser className="w-3.5 h-3.5" />
                </button>
              )}
              {onToggleHistory && (
                <button
                  onClick={onToggleHistory}
                  title="Histórico de conversas"
                  aria-label="Ver histórico de conversas"
                  className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <History className="w-3.5 h-3.5" />
                </button>
              )}
              {onClose && (
                <>
                  <div className="w-px h-4 bg-gray-200 mx-0.5" />
                  <button
                    onClick={onClose}
                    title="Fechar"
                    aria-label="Fechar"
                    className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div
          className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[240px]"
        >
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-8 opacity-60">
              <p className="text-xs text-gray-400">
                Envie uma mensagem para começar
              </p>
            </div>
          ) : (
            messages.map((msg, i) => {
              const timestamp = new Date(msg.timestamp)

              if (msg.role === 'user') {
                return (
                  <div key={i} className="flex justify-end items-start gap-2">
                    <div className="flex flex-col items-end gap-1">
                      <div className="max-w-[85%] px-3.5 py-2.5 bg-gray-100 dark:bg-gray-800 rounded-[14px] rounded-br-[4px]">
                        <p
                          className="text-base-ui whitespace-pre-wrap text-gray-700 dark:text-gray-200"
                         
                        >
                          {msg.content}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400 px-1" style={{ fontFamily: 'Inter, sans-serif' }}>
                        {formatTime(timestamp)}
                      </span>
                    </div>
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mt-0.5">
                      <User className="w-3.5 h-3.5 text-gray-500 dark:text-gray-400" />
                    </div>
                  </div>
                )
              }

              const meta = msg.metadata
              const hasTasks = meta?.tasks && meta.tasks.length > 0
              const isOutOfScope = meta?.out_of_scope
              const hasFairnessIssue = meta?.fairness_result && !meta.fairness_result.is_fair
              const hasLearnedSuggestions = meta?.learned_suggestions && meta.learned_suggestions.length > 0

              const liaHtml = (() => {
                const cleaned = cleanAgentResponse(msg.content)
                return parseChatMarkdown(cleaned)
              })()

              return (
                <div key={i} className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                  </div>
                  <div className="flex-1 flex flex-col gap-1">
                    <div className="flex items-center gap-1.5 px-1">
                      <span className="text-xs font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Inter, sans-serif' }}>
                        LIA
                      </span>
                      <ConfidenceBadge confidence={meta?.confidence} layer={meta?.layer} />
                    </div>
                    <div
                      className="max-w-[85%] px-3.5 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-[14px] rounded-bl-[4px]"
                    >
                      <RichContent
                        html={liaHtml}
                        className="text-base-ui leading-relaxed text-gray-700 dark:text-gray-200 font-['Open_Sans',sans-serif]"
                      />

                      {meta?.extracted_preferences && Object.keys(meta.extracted_preferences).length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5 pt-1.5 border-t border-gray-200/30">
                          {Object.entries(meta.extracted_preferences).map(([key, value]) => {
                            const label = PREFERENCE_LABELS[key] || key
                            return (
                              <span
                                key={key}
                                className="inline-flex items-center gap-1 text-micro bg-gray-50 rounded-full px-2 py-0.5 text-gray-600"
                                style={{ fontFamily: 'Inter, sans-serif' }}
                              >
                                <span className="font-medium">{label}:</span> {String(value)}
                              </span>
                            )
                          })}
                        </div>
                      )}

                      {hasTasks && <TasksChecklist tasks={meta!.tasks!} />}
                      {isOutOfScope && <OutOfScopeIndicator />}
                      {hasFairnessIssue && <FairnessWarning fairnessResult={meta!.fairness_result!} />}
                      {hasLearnedSuggestions && (
                        <LearnedSuggestionsChips
                          suggestions={meta!.learned_suggestions!}
                          onAccept={handleLearnedSuggestionAccept}
                        />
                      )}
                    </div>
                    <MessageFeedback
                      sessionId={sessionId || 'transition-chat'}
                      messageId={`transition-msg-${i}`}
                      originalResponse={msg.content}
                      className="px-1"
                    />
                    <span className="text-xs text-gray-400 px-1" style={{ fontFamily: 'Inter, sans-serif' }}>
                      {formatTime(timestamp)}
                    </span>
                  </div>
                </div>
              )
            })
          )}
          {isLoading && (
            <div className="flex items-start gap-2.5">
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-1 px-1">
                  <span className="text-xs font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Inter, sans-serif' }}>
                    LIA
                  </span>
                </div>
                <div className="bg-white border border-gray-200 rounded-[14px] rounded-bl-[4px] p-3 inline-block">
                  <div className="flex items-center gap-1">
                    <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-chat-cyan rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {extractedPreferences && Object.keys(extractedPreferences).filter(k => extractedPreferences[k]).length > 0 && (
          <div className="flex-shrink-0 px-4 py-2 border-t border-gray-100 dark:border-gray-800 bg-gray-50/50">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Brain className="w-3 h-3 text-chat-cyan" strokeWidth={2.5} />
              <span className="text-xs font-semibold text-gray-600 dark:text-gray-400">
                Preferências detectadas
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(extractedPreferences).map(([key, value]) => {
                if (!value) return null
                const label = PREFERENCE_LABELS[key] || key
                return (
                  <span
                    key={key}
                    className="inline-flex items-center gap-1 px-2 py-0.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-xs text-gray-700 dark:text-gray-300"
                    style={{ fontFamily: 'Inter, sans-serif' }}
                  >
                    <span className="font-medium text-gray-900 dark:text-gray-100">{label}:</span> {String(value)}
                  </span>
                )
              })}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="flex-shrink-0 p-3 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
              <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
            </div>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder || 'Envie mensagem para a LIA...'}
              className="flex-1 text-base-ui bg-transparent focus:outline-none min-w-0 text-gray-900 dark:text-gray-50 placeholder:text-gray-400"
             
              disabled={isLoading}
            />
            <button
              className="p-1.5 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-300 transition-colors rounded-full"
              type="button"
              title="Gravar áudio"
              aria-label="Gravar áudio"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button
              onClick={handleSend}
              disabled={!canSend}
              aria-label="Enviar mensagem"
              className={cn(
                "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors",
                canSend
                  ? "bg-chat-cyan text-white hover:opacity-90"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed"
              )}
              type="button"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 text-white animate-spin" />
              ) : (
                <Send className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
