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
  RotateCcw,
  ShieldAlert,
  Sparkles,
  XCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { isClearChatCommand } from '@/lib/chat-commands'
import type { ChatMessage, TaskItem, LearnedSuggestion } from '@/hooks/use-interpret-context'

interface TransitionChatPanelProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSendMessage: (message: string) => void
  onClearChat?: () => void
  actionBehavior: string
  placeholder?: string
  extractedPreferences?: Record<string, any> | null
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

const renderContent = (text: string) => {
  return text.split('**').map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
}

function TasksChecklist({ tasks }: { tasks: TaskItem[] }) {
  return (
    <div className="mt-2 pt-2 border-t border-gray-200/30">
      <p className="text-[9px] font-semibold text-gray-500 uppercase tracking-wider mb-1" style={{ fontFamily: 'Inter, sans-serif' }}>
        Tarefas agendadas
      </p>
      {tasks.map((task, idx) => (
        <div
          key={idx}
          className="flex items-start gap-1.5 py-0.5"
        >
          <CheckCircle2 className="w-3 h-3 text-wedo-cyan flex-shrink-0 mt-0.5" />
          <span className="text-[10px] text-gray-600" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
    <div className="mt-2 pt-2 border-t border-amber-200/50">
      <div className="flex items-center gap-1.5">
        <ExternalLink className="w-3 h-3 text-amber-500 flex-shrink-0" />
        <span className="text-[9px] font-medium text-amber-600" style={{ fontFamily: 'Inter, sans-serif' }}>
          Fora do escopo desta conversa
        </span>
      </div>
    </div>
  )
}

function FairnessWarning({ fairnessResult }: { fairnessResult: { is_fair: boolean; warnings: string[]; educational_message?: string } }) {
  if (fairnessResult.is_fair) return null

  return (
    <div className="mt-2 pt-2 border-t border-red-200/50">
      <div className="flex items-start gap-1.5">
        <ShieldAlert className="w-3.5 h-3.5 text-red-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-[10px] font-semibold text-red-600" style={{ fontFamily: 'Inter, sans-serif' }}>
            Alerta de Fairness
          </p>
          {fairnessResult.warnings.map((w, idx) => (
            <p key={idx} className="text-[9px] text-red-500 mt-0.5" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
        <Lightbulb className="w-3 h-3 text-amber-400" />
        <span className="text-[9px] font-medium text-gray-500" style={{ fontFamily: 'Inter, sans-serif' }}>
          Baseado no seu histórico
        </span>
      </div>
      <div className="flex flex-wrap gap-1">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onAccept(s)}
            className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-50 border border-amber-200 rounded text-[9px] text-amber-700 hover:bg-amber-100 transition-colors"
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
  const color = pct >= 80 ? 'text-emerald-600' : pct >= 50 ? 'text-amber-600' : 'text-red-500'

  return (
    <span className={cn("text-[8px] font-medium ml-1", color)} style={{ fontFamily: 'Inter, sans-serif' }}>
      {pct}%{layer === 3 && <span className="text-gray-400 ml-0.5">AI</span>}
    </span>
  )
}

export function TransitionChatPanel({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  actionBehavior,
  placeholder,
  extractedPreferences,
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

  return (
    <div className="flex flex-col h-full overflow-hidden p-3">
      <div className="flex flex-col flex-1 overflow-hidden rounded-md border" style={{ borderColor: '#E4EBEF', backgroundColor: '#FFFFFF' }}>
      <div
        className="flex-shrink-0 px-4 py-3"
      >
        <div className="flex items-center gap-3">
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0"
            style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}
          >
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <div className="min-w-0 flex-1">
            <h3
              className="text-[14px] font-semibold leading-tight text-gray-950 dark:text-gray-50"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              Olá! Sou a Lia.
            </h3>
            <p
              className="text-[11px] leading-tight mt-0.5 text-gray-500"
              style={{ fontFamily: 'Open Sans, sans-serif' }}
            >
              {BEHAVIOR_DESCRIPTIONS[actionBehavior] || 'Como posso te ajudar hoje?'}
            </p>
          </div>
          {onClearChat && messages.length > 0 && (
            <button
              onClick={onClearChat}
              title="Nova conversa"
              className="flex-shrink-0 p-1.5 rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div
        className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-[240px]"
        style={{ backgroundColor: '#FFFFFF' }}
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center py-8 opacity-60">
            <p className="text-[11px] text-gray-400" style={{ fontFamily: 'Open Sans, sans-serif' }}>
              Envie uma mensagem para começar
            </p>
          </div>
        ) : (
          messages.map((msg, i) => {
            const timestamp = new Date(msg.timestamp)

            if (msg.role === 'user') {
              return (
                <div key={i} className="flex justify-end items-end gap-2">
                  <div>
                    <div
                      className="max-w-[85%] p-3 bg-gray-100 text-gray-800 rounded-md rounded-br-none ml-auto"
                    >
                      <p
                        className="text-xs whitespace-pre-wrap"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        {renderContent(msg.content)}
                      </p>
                      <p
                        className="text-[10px] text-gray-400 mt-1.5"
                        style={{ fontFamily: 'Open Sans, sans-serif' }}
                      >
                        {formatTime(timestamp)}
                      </p>
                    </div>
                  </div>
                  <div
                    className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-semibold bg-gray-700" style={{ fontFamily: 'Inter, sans-serif' }}
                  >
                    U
                  </div>
                </div>
              )
            }

            const meta = msg.metadata
            const hasTasks = meta?.tasks && meta.tasks.length > 0
            const isOutOfScope = meta?.out_of_scope
            const hasFairnessIssue = meta?.fairness_result && !meta.fairness_result.is_fair
            const hasLearnedSuggestions = meta?.learned_suggestions && meta.learned_suggestions.length > 0

            return (
              <div key={i} className="flex justify-start">
                <div
                  className="max-w-[85%] p-3 rounded-md rounded-bl-none"
                  style={{ backgroundColor: isOutOfScope ? 'rgba(251, 191, 36, 0.08)' : hasFairnessIssue ? 'rgba(239, 68, 68, 0.06)' : 'rgba(96, 190, 209, 0.08)' }}
                >
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Brain className="w-3 h-3 text-wedo-cyan" />
                    <span
                      className="text-[10px] font-medium"
                      style={{ fontFamily: 'Open Sans, sans-serif' }}
                    >
                      LIA
                    </span>
                    <ConfidenceBadge confidence={meta?.confidence} layer={meta?.layer} />
                  </div>
                  <p
                    className="text-xs whitespace-pre-wrap text-gray-800"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                  >
                    {renderContent(msg.content)}
                  </p>

                  {meta?.extracted_preferences && Object.keys(meta.extracted_preferences).length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5 pt-1.5 border-t border-gray-200/30">
                      {Object.entries(meta.extracted_preferences).map(([key, value]) => {
                        const label = PREFERENCE_LABELS[key] || key
                        return (
                          <span
                            key={key}
                            className="inline-flex items-center gap-1 text-[9px] bg-white/60 rounded-full px-2 py-0.5 text-gray-600"
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

                  <p
                    className="text-[10px] text-gray-400 mt-1.5"
                    style={{ fontFamily: 'Open Sans, sans-serif' }}
                  >
                    {formatTime(timestamp)}
                  </p>
                </div>
              </div>
            )
          })
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div
              className="rounded-md rounded-bl-none p-3 max-w-[85%]"
              style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)' }}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                <span
                  className="text-[10px] font-medium"
                  style={{ fontFamily: 'Open Sans, sans-serif' }}
                >
                  LIA
                </span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-900 dark:bg-gray-50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {extractedPreferences && Object.keys(extractedPreferences).filter(k => extractedPreferences[k]).length > 0 && (
        <div className="flex-shrink-0 px-4 py-2" style={{ borderTop: '1px solid #E4EBEF', backgroundColor: 'rgba(96, 190, 209, 0.04)' }}>
          <div className="flex items-center gap-1.5 mb-1.5">
            <Brain className="w-3 h-3 text-wedo-cyan" />
            <span className="text-[10px] font-semibold text-gray-600 dark:text-gray-400" style={{ fontFamily: 'Open Sans, sans-serif' }}>
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
                  className="inline-flex items-center gap-1 px-2 py-0.5 bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded text-[10px] text-gray-700 dark:text-gray-300"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  <span className="font-medium text-gray-900 dark:text-gray-100">{label}:</span> {String(value)}
                </span>
              )
            })}
          </div>
        </div>
      )}

      <div
        className="flex-shrink-0 p-3"
      >
        <div className="flex items-center gap-2 p-2 rounded-md border bg-white" style={{ borderColor: '#E4EBEF' }}>
          <div
            className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center"
            style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}
          >
            <Brain className="w-4 h-4 text-wedo-cyan" />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || 'Como posso te ajudar hoje?'}
            className="flex-1 text-xs bg-transparent focus:outline-none min-w-0"
            style={{ fontFamily: 'Open Sans, sans-serif' }}
            disabled={isLoading}
          />
          <div className="flex items-center gap-1 flex-shrink-0">
            <button
              className="p-1.5 text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
              type="button"
              title="Gravar áudio"
              aria-label="Gravar áudio"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
              aria-label="Enviar mensagem"
              className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors disabled:opacity-50 bg-wedo-cyan"
              type="button"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 text-white animate-spin" />
              ) : (
                <svg
                  className="w-4 h-4 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>
      </div>
    </div>
  )
}
