/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from"@/components/unified-chat"
 */"use client"

import React from"react"
import { X, MessageSquare, UserPlus, ChevronRight, Mic, Send } from"lucide-react"
import { Calendar as CalendarIcon } from"lucide-react"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { textStyles, formatScorePercent } from"@/lib/design-tokens"
import { ThinkingDots } from"@/components/ui/thinking-dots"
import { useModalA11y } from"@/hooks/ui/use-modal-a11y"
import { useLiaFloat } from"@/contexts/lia-float-context"
import { cleanAgentResponse } from"@/lib/chat-format"
import { ContextBadge } from"@/components/lia-float/ContextBadge"

interface LiaAction {
  id: string
  icon: string
  title: string
  buttonText: string
}

interface ChatMessage {
  role: 'user' | 'lia'
  content: string
}

interface Candidate {
  name?: string
  nome?: string
  candidateId?: string
  id?: string
  position?: string
  score?: number
  lia_score?: number
  email?: string
}

interface LiaChatModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Candidate
  liaActions: LiaAction[]
  chatMessages: ChatMessage[]
  isLiaChatLoading: boolean
  liaConversation: string
  onConversationChange: (text: string) => void
  onSendMessage: (message: string) => void
  onContact?: (candidate: Candidate) => void
  onSendEmail?: (candidate: Candidate) => void
  onSchedule?: (candidate: Candidate) => void
  onScheduleInterview?: (candidate: Candidate) => void
  onSendAgendamento?: (candidate: Candidate) => void
  onAddToList?: (candidate: Candidate) => void
  onAddToVacancy?: (candidate: Candidate) => void
}

export function LiaChatModal({
  isOpen,
  onClose,
  candidate,
  liaActions,
  chatMessages,
  isLiaChatLoading,
  liaConversation,
  onConversationChange,
  onSendMessage,
  onContact,
  onSendEmail,
  onSchedule,
  onScheduleInterview,
  onSendAgendamento,
  onAddToList,
  onAddToVacancy,
}: LiaChatModalProps) {
  const dialogRef = useModalA11y(isOpen, onClose)
  const { openWithEntity, contextPage } = useLiaFloat()

  React.useEffect(() => {
    if (isOpen && candidate) {
      openWithEntity({
        type:"candidate",
        id: candidate.id,
        name: candidate.name || candidate.nome,
        meta: {
          email: candidate.email,
          score: candidate.score ?? candidate.lia_score,
        },
      })
      onClose()
    }
  }, [isOpen]) // eslint-disable-line react-hooks/exhaustive-deps

  if (!isOpen) return null

  const handleContact = () => {
    if (onContact) onContact(candidate)
    else if (onSendEmail) onSendEmail(candidate)
  }

  const handleSchedule = () => {
    if (onSchedule) onSchedule(candidate)
    else if (onScheduleInterview) onScheduleInterview(candidate)
    else if (onSendAgendamento) onSendAgendamento(candidate)
  }

  const handleAddTo = () => {
    if (onAddToList) onAddToList(candidate)
    else if (onAddToVacancy) onAddToVacancy(candidate)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (liaConversation.trim() && !isLiaChatLoading) {
      onSendMessage(liaConversation)
    }
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-label="Chat com LIA" className="bg-lia-bg-primary rounded-xl max-w-2xl w-full max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="bg-lia-bg-primary">
          <div className="p-3">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Avatar className="w-6 h-6">
                  <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-primary text-xs font-bold">
                    LIA
                  </AvatarFallback>
                </Avatar>
                <div>
                  <span className={`${textStyles.bodySmall} font-medium`}>
                    Análise LIA para candidato específico
                  </span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-6 w-6 p-0"
                aria-label="Fechar chat IA"
                data-dismiss="true"
              >
                <X className="w-3 h-3" aria-hidden="true" />
              </Button>
            </div>

            {/* Context Badge */}
            {contextPage && contextPage !== "Conversar" && (
              <div className="px-1 mb-2">
                <ContextBadge contextPage={contextPage} />
              </div>
            )}
            {/* Candidate info */}
            <div className="flex items-center gap-2 bg-lia-bg-primary rounded-xl px-3 py-2">
              <Avatar className="w-6 h-6">
                <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-primary text-xs">
                  {candidate.name?.split(' ').map((n: string) => n[0]).join('')}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1">
                <div className="font-medium text-lia-text-primary text-xs">
                  {candidate.candidateId || candidate.id} • {candidate.name}
                </div>
                <div className="text-xs text-lia-text-secondary">
                  {candidate.position} • Nota: {formatScorePercent(candidate.score ?? 0)}
                </div>
              </div>
              <Chip density="relaxed" variant="neutral" muted className="bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle px-2 py-0.5">
                Foco Individual
              </Chip>
            </div>
          </div>
        </div>

        {/* Ações rápidas */}
        <div className="px-4 py-2 bg-lia-bg-primary/50/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-lia-text-secondary">Ações rápidas sugeridas</span>
            <Chip density="relaxed" variant="neutral" muted className="bg-status-success/15 text-lia-text-primary dark:bg-status-success px-1.5 py-0.5">
              Score {formatScorePercent(candidate.score ?? 0)}
            </Chip>
          </div>
          <div className="flex gap-1">
            <button
              onClick={handleContact}
              className="flex-1 flex items-center justify-center gap-1 py-2 bg-lia-bg-primary rounded-xl text-xs hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none border border-lia-border-subtle"
            >
              <MessageSquare className="w-3 h-3 text-lia-text-primary" />
              Contatar
            </button>
            <button
              onClick={handleSchedule}
              className="flex-1 flex items-center justify-center gap-1 py-2 bg-lia-bg-primary rounded-xl text-xs hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none border border-lia-border-subtle"
            >
              <CalendarIcon className="w-3 h-3 text-lia-text-primary" />
              Agendar
            </button>
            <button
              onClick={handleAddTo}
              className="flex-1 flex items-center justify-center gap-1 py-2 bg-lia-bg-primary rounded-xl text-xs hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none border border-lia-border-subtle"
            >
              <UserPlus className="w-3 h-3 text-lia-text-primary" />
              Adicionar
            </button>
          </div>
        </div>

        {/* Lista de sugestões + chat */}
        <div className="p-3 max-h-[45vh] overflow-y-auto">
          <div className="space-y-2">
            {liaActions.slice(0, 4).map((action) => (
              <div
                key={action.id}
                className="flex items-center gap-2 p-2 bg-lia-bg-primary rounded-xl hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg transition-colors motion-reduce:transition-none duration-200 cursor-pointer group"
                onClick={() => onConversationChange(action.title)}
              >
                <span className="text-base flex-shrink-0">{action.icon}</span>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-medium text-lia-text-primary group-hover:text-lia-text-primary">
                    {action.title}
                  </h4>
                  <p className="text-xs text-lia-text-primary truncate">
                    {action.buttonText}
                  </p>
                </div>
                <ChevronRight className="w-3 h-3 text-lia-text-secondary group-hover:text-lia-text-secondary" />
              </div>
            ))}
          </div>

          {/* Chat Messages */}
          {chatMessages.length > 0 && (
            <div className="p-3 border-t border-lia-border-subtle max-h-48 overflow-y-auto">
              <div className="space-y-2">
                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'lia' && (
                      <Avatar className="w-6 h-6 flex-shrink-0">
                        <AvatarFallback className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro font-medium">LIA</AvatarFallback>
                      </Avatar>
                    )}
                    <div className={`max-w-[80%] rounded-md px-3 py-2 ${
 msg.role === 'user'
                        ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                        : 'bg-lia-bg-tertiary text-lia-text-primary'
                    }`}>
                      <p className="text-xs whitespace-pre-wrap">{msg.role === 'lia' ? cleanAgentResponse(msg.content) : msg.content}</p>
                    </div>
                  </div>
                ))}
                {isLiaChatLoading && (
                  <div className="flex gap-2 justify-start">
                    <Avatar className="w-6 h-6 flex-shrink-0">
                      <AvatarFallback className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro font-medium">LIA</AvatarFallback>
                    </Avatar>
                    <div className="bg-lia-bg-tertiary rounded-xl px-3 py-2">
                      <div className="flex items-center gap-1">
                        <ThinkingDots dotClassName="bg-lia-border-medium" size="lg" />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Prompt Input */}
          <div className="p-4 border-t border-lia-border-subtle">
            <div className="bg-lia-bg-primary rounded-xl border border-lia-border-subtle p-3">
              <form onSubmit={handleSubmit} className="flex items-center gap-2">
                <Avatar className="w-8 h-8 flex-shrink-0">
                  <AvatarFallback className="bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-bold">
                    LIA
                  </AvatarFallback>
                </Avatar>

                <input
                  type="text"
                  value={liaConversation}
                  onChange={(e) => onConversationChange(e.target.value)}
                  placeholder={`Peça à LIA para analisar ${candidate.name}, agendar entrevista, enviar email...`}
                  className="flex-1 bg-transparent text-lia-text-primary placeholder-lia-text-secondary text-xs focus:outline-none"
                  disabled={isLiaChatLoading}
                />

                <div className="text-xs text-lia-text-primary flex items-center gap-1">
                  {isLiaChatLoading ? (
                    <><span className="animate-pulse motion-reduce:animate-none">●</span>Processando...</>
                  ) : (
                    <><span>●</span>Pronta</>
                  )}
                </div>

                <button
                  type="button"
                  className="w-6 h-6 rounded-md flex items-center justify-center hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
                  disabled={isLiaChatLoading}
                >
                  <Mic className="w-3 h-3 text-lia-text-primary" />
                </button>

                <button
                  type="submit"
                  disabled={!liaConversation.trim() || isLiaChatLoading}
                  className={`w-6 h-6 rounded-md flex items-center justify-center transition-colors motion-reduce:transition-none ${
 liaConversation.trim() && !isLiaChatLoading
                      ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-bg'
                      : 'bg-lia-interactive-active text-lia-text-secondary cursor-not-allowed'
                  }`}
                >
                  <Send className="w-3 h-3" />
                </button>
              </form>

              {/* Quick suggestions */}
              <div className="flex flex-wrap gap-1 mt-2">
                <button
                  onClick={() => onConversationChange(`Agendar entrevista com ${candidate.name}`)}
                  className="text-xs px-2 py-1 bg-lia-bg-primary rounded-full border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  disabled={isLiaChatLoading}
                >
                  📅 Agendar entrevista
                </button>
                <button
                  onClick={() => onConversationChange(`Enviar email de follow-up para ${candidate.name}`)}
                  className="text-xs px-2 py-1 bg-lia-bg-primary rounded-full border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  disabled={isLiaChatLoading}
                >
                  📧 Enviar email
                </button>
                <button
                  onClick={() => onConversationChange(`Fazer análise completa de ${candidate.name}`)}
                  className="text-xs px-2 py-1 bg-lia-bg-primary rounded-full border border-lia-border-subtle hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  disabled={isLiaChatLoading}
                >
                  🔍 Análise completa
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
