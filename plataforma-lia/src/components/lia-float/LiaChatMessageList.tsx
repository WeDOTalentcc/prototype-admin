"use client"

import React, { useMemo } from "react"
import { useAuthStore } from "@/stores/auth-store"
import {
  Brain, Clock, Loader2, User, Sun, AlertTriangle, Users, Plus, FileText,
  TrendingUp, Search, Activity, ClipboardCheck, DollarSign, Edit, GitMerge,
  Zap, Calendar, Star, ArrowRight, MoveRight, BarChart, CheckCircle, BarChart2,
  CheckSquare, Download, Shield, Link, Home, Briefcase, GitBranch, Settings,
  type LucideIcon
} from "lucide-react"
import { cn } from "@/lib/utils"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { PlanProgressCard, type ExecutionPlanData } from "@/components/chat/plan-progress-card"
import { LIAIcon } from "@/components/ui/lia-icon"
import { type FloatMessage } from "@/hooks/chat/use-float-conversation"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import { QuickReplies, type QuickReplyPreset } from "@/components/onboarding/QuickReplies"

export interface LiaChatMessageListProps {
  showHistory: boolean
  recentChats: Array<{ id: string; title: string; timestamp: number }>
  handleLoadConversation: (id: string) => void
  isFetchingHistory: boolean
  isEmpty: boolean
  messages: FloatMessage[]
  currentScope: string
  contextPage?: string | null
  handleChipSend: (text: string) => void
  hitlPending: { action: string; description: string } | null
  sendApproval: (approved: boolean) => void
  isStreaming: boolean
  streamingContent: string
  conversationId: string | null
  messagesEndRef: React.RefObject<HTMLDivElement | null>
}

export function LiaChatMessageList({
  showHistory, recentChats, handleLoadConversation,
  isFetchingHistory, isEmpty, messages, currentScope, contextPage, handleChipSend,
  hitlPending, sendApproval, isStreaming, streamingContent,
  conversationId, messagesEndRef,
}: LiaChatMessageListProps) {
  if (showHistory) {
    return (
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
        <p className="text-xs font-semibold text-lia-text-tertiary uppercase tracking-wide mb-2" >
          Conversas recentes
        </p>
        {recentChats.length === 0 ? (
          <p className="text-sm-ui text-lia-text-disabled text-center mt-6">
            Nenhuma conversa anterior encontrada.
          </p>
        ) : (
          recentChats.map(chat => (
            <button
              key={chat.id}
              onClick={() => handleLoadConversation(chat.id)}
              className="w-full flex items-start gap-2.5 px-3 py-2.5 rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left group"
            >
              <Clock className="w-3.5 h-3.5 text-lia-text-secondary flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm-ui text-lia-text-secondary truncate group-hover:text-lia-text-primary dark:group-hover:text-lia-text-tertiary transition-colors motion-reduce:transition-none">
                  {chat.title}
                </p>
                <p className="text-xs text-lia-text-disabled mt-0.5">
                  {new Date(chat.timestamp).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>
            </button>
          ))
        )}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
      {isFetchingHistory ? (
        <div className="flex justify-center items-center h-full" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
        </div>
      ) : isEmpty ? (
        <EmptyState scope={currentScope} contextPage={contextPage} onChipClick={handleChipSend} />
      ) : (
        <>
          {messages
            // G5 canonical (2026-05-24): system messages are backstage hints
            // for LIA, never user-facing. Filter before map so MessageBubble
            // only sees msg.sender of type "lia" | "user".
            .filter((msg): msg is FloatMessage & { sender: "lia" | "user" } => msg.sender !== "system")
            .map(msg => (
              <MessageBubble key={msg.id} msg={msg} conversationId={conversationId} onQuickReply={handleChipSend} />
            ))}
          {hitlPending && (
            <ChatBubbleBase
              sender="lia"
              hideTimestamp
            >
              <HITLConfirmCard
                action={hitlPending.action}
                description={hitlPending.description}
                onConfirm={() => sendApproval(true)}
                onCancel={() => sendApproval(false)}
              />
            </ChatBubbleBase>
          )}
          {isStreaming && !hitlPending && (
            streamingContent
              ? <StreamingBubble content={streamingContent} />
              : <ThinkingIndicator />
          )}
        </>
      )}
      <div ref={messagesEndRef} />
    </div>
  )
}

export function pageToUrl(page: string | null): string | null {
  if (!page) return null
  // Onda 4-P0-Fase7 (2026-05-24): "Indicadores" trocado de '/indicadores'
  // (rota inexistente — bug padrão Task #712) pra '/teams-tab/dashboard'
  // (rota canonical DASHBOARD). Descoberto via check_no_broken_window_location.
  const map: Record<string, string> = {
    "Vagas": "/jobs",
    "Funil de Talentos": "/funil-de-talentos",
    "Decidir": "/tasks",
    "Configurações": "/configuracoes",
    "Indicadores": "/teams-tab/dashboard",
  }
  return map[page] ?? null
}

function scopeToContextPage(scope: string): string {
  switch (scope) {
    case "talent_funnel": return "candidato"
    case "in_job":        return "vaga"
    case "job_table":     return "vaga"
    default:              return "home"
  }
}

function contextPageToBackendPage(contextPage: string | null | undefined, fallbackScope: string): string {
  if (contextPage) {
    switch (contextPage) {
      case "Funil de Talentos": return "candidato"
      case "Vagas":             return "vaga"
      case "Painel de Controle": return "home"
      case "Indicadores":       return "relatorios"
      case "Configurações":     return "configuracoes"
    }
  }
  return scopeToContextPage(fallbackScope)
}

const ICON_MAP: Record<string, LucideIcon> = {
  Sun, AlertTriangle, Users, Plus, FileText, TrendingUp, Search, Activity,
  ClipboardCheck, DollarSign, Edit, GitMerge, Zap, Calendar, Star, ArrowRight,
  MoveRight, BarChart, CheckCircle, BarChart2, CheckSquare, Download, Shield,
  Link, Home, Briefcase, User, GitBranch, Settings, Clock, Brain,
}

function EmptyState({ scope, contextPage, onChipClick }: { scope: string; contextPage?: string | null; onChipClick: (prompt: string) => void }) {
  const [suggestions, setSuggestions] = React.useState<Array<{ id: string; icon: string; label: string; prompt: string }>>([])

  React.useEffect(() => {
    const page = contextPageToBackendPage(contextPage, scope)
    fetch(`/api/backend-proxy/lia/context-suggestions?page=${page}&limit=4`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then((data: { suggestions?: typeof suggestions }) => {
        setSuggestions(data.suggestions ?? [])
      })
      .catch((err) => { console.error('[LiaChatMessageList] context-suggestions fetch failed', err) })
  }, [scope, contextPage])

  return (
    <div className="flex flex-col items-start h-full gap-2.5 pt-5 px-1">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0">
          <LIAIcon size="sm" />
        </div>
        <div>
          <p className="text-base-ui font-medium text-lia-text-primary">Como posso ajudar?</p>
        </div>
      </div>
      {suggestions.length > 0 && (
        <div className="w-full flex flex-col gap-1">
          {suggestions.map((s) => {
            const Icon = ICON_MAP[s.icon] || Brain
            return (
              <button
                key={s.id}
                onClick={() => onChipClick(s.prompt)}
                className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-lg text-left
                  bg-white border border-lia-border-subtle
                  hover:border-lia-border-medium hover:bg-lia-interactive-hover
                  text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none"
              >
                <Icon className="w-3.5 h-3.5 flex-shrink-0 text-lia-text-tertiary" />
                <span className="flex-1 text-xs truncate">{s.label}</span>
              </button>
            )
          })}
        </div>
      )}
      {suggestions.length === 0 && (
        <p className="text-xs text-lia-text-disabled px-1">
          Pergunte sobre vagas, candidatos, relatórios e muito mais.
        </p>
      )}
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <ChatBubbleBase
      sender="lia"
      hideTimestamp
      hideLabel
    >
      <div className="flex items-center gap-1.5 mb-0.5">
        <span className="text-xs font-semibold text-lia-text-primary font-['Inter',sans-serif]">LIA</span>
      </div>
      <span className="flex gap-1 items-center h-5">
        <ThinkingDots dotClassName="bg-wedo-cyan" size="md" />
      </span>
    </ChatBubbleBase>
  )
}

function RichContent({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
    />
  )
}

function StreamingBubble({ content }: { content: string }) {
  const cleaned = useMemo(() => cleanAgentResponse(content), [content])
  const html = useMemo(() => parseChatMarkdown(cleaned), [cleaned])

  return (
    <ChatBubbleBase
      sender="lia"
      hideTimestamp
    >
      <RichContent
        html={html}
        className="text-xs text-lia-text-primary leading-relaxed"
      />
      <span className="inline-block w-1.5 h-3.5 bg-wedo-cyan ml-0.5 animate-pulse motion-reduce:animate-none align-middle" />
    </ChatBubbleBase>
  )
}

function MessageBubble({ msg, conversationId, onQuickReply }: { msg: FloatMessage & { sender: "lia" | "user" }; conversationId: string | null; onQuickReply?: (text: string) => void }) {
  const authUser = useAuthStore((s) => s.user)
  const userDisplayName = authUser?.name || authUser?.email || "Usuário"
  const isUser = msg.sender === "user"
  const quickReplyPreset = msg.metadata?.quick_reply_preset as QuickReplyPreset | undefined

  const renderedHtml = useMemo(() => {
    if (isUser) return escapeHtml(msg.content).replace(/\n/g, "<br/>")
    const cleaned = cleanAgentResponse(msg.content)
    return parseChatMarkdown(cleaned)
  }, [msg.content, isUser])

  return (
    <ChatBubbleBase
      sender={msg.sender}
      timestamp={msg.timestamp}
      userName={userDisplayName}
      afterBubble={
        !isUser && conversationId ? (
          <MessageFeedback
            sessionId={conversationId}
            messageId={msg.id}
            originalResponse={msg.content}
            className="mt-1 px-1"
          />
        ) : undefined
      }
    >
      <RichContent
        html={renderedHtml}
        className="text-xs text-lia-text-primary leading-relaxed"
      />
      {!isUser && msg.executionPlan && (
        <PlanProgressCard plan={msg.executionPlan as unknown as ExecutionPlanData} />
      )}
      {/* Sprint B.6 (P2-2): renderiza quick replies inline quando backend
          marca a mensagem com metadata.quick_reply_preset. Só pra LIA. */}
      {!isUser && quickReplyPreset && (
        <QuickReplies
          preset={quickReplyPreset}
          onSelect={(value) => onQuickReply?.(value)}
        />
      )}
    </ChatBubbleBase>
  )
}
