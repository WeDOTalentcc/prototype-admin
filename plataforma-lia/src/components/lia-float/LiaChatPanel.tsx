"use client"

/**
 * LiaChatPanel — Painel flutuante de conversa com a LIA.
 *
 * Dimensões: 420×580px, fixo bottom-right acima do LiaChatButton.
 *
 * Nível 3 — capacidades:
 *   - WebSocket com streaming de tokens em tempo real
 *   - HITL: card de aprovação para ações reais (mover candidato, agendar, enviar email)
 *   - Roteamento inteligente: detecta intent e abre área especializada
 *   - Wizard: redireciona para Vagas + split-view com o agente
 *   - Markdown: renderização completa (bold, links, listas)
 *
 * Compatível com Vue/Nuxt: sem React-only patterns; lógica em hooks separados.
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react"
import { Brain, X, Maximize2, Loader2, Send, ArrowRight, Plus, Eraser, History, Clock, User } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useActionIntent, actionTypeToDomain, type ActionType } from "@/hooks/use-action-intent"
import { useFloatStreaming } from "@/hooks/use-float-streaming"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { FairnessWarningBanner } from "@/components/fairness-warning-banner"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { MessageFeedback } from "@/components/chat/message-feedback"
import {
  useFloatConversation,
  formatMessageTime,
  type FloatMessage,
} from "@/hooks/use-float-conversation"
import { resolveScopeFromPathname } from "@/hooks/use-current-scope"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"
import { ThinkingDots } from "@/components/ui/thinking-dots"

const MAX_INPUT_CHARS = 2000

export function LiaChatPanel() {
  const {
    isOpen, conversationId: ctxConvId, close, expand, openSplitView,
    sharedMessages, addSharedMessage, setSharedMessages,
    sharedConversationId, setSharedConversationId,
  } = useLiaFloat()
  const { result: navIntent, detect: detectIntent, clear: clearIntent } = useNavigationIntent()
  const { detect: detectAction } = useActionIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== 'undefined' ? window.location.pathname : '')
  const [activeActionType, setActiveActionType] = useState<ActionType>(null)
  const [actionLabel, setActionLabel] = useState<string | null>(null)

  const {
    conversationId: localConvId,
    isCreating,
    isFetchingHistory,
    initConversation,
    loadHistory,
  } = useFloatConversation(ctxConvId, setSharedMessages)

  const conversationId = sharedConversationId ?? localConvId
  const messages = sharedMessages
  const addMessage = addSharedMessage
  const setMessages = setSharedMessages
  const setConversationId = useCallback((id: string | null) => {
    setSharedConversationId(id)
  }, [setSharedConversationId])

  const [inputText, setInputText] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; timestamp: number }>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const wsSessionId = conversationId ?? "float-pending"

  const handleStreamComplete = useCallback((content: string) => {
    addMessage({
      id: `lia-${Date.now()}`,
      sender: "lia",
      content,
      timestamp: formatMessageTime(),
    })
  }, [addMessage])

  const {
    isConnected,
    isStreaming,
    isReconnecting,
    reconnectAttempt,
    streamingContent,
    error: wsError,
    hitlPending,
    fairnessWarnings,
    dismissFairnessWarnings,
    sendMessage: wsSend,
    sendApproval,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useFloatStreaming(wsSessionId, handleStreamComplete)

  useEffect(() => {
    if (isOpen && conversationId) {
      wsConnect()
    }
    if (!isOpen) {
      wsDisconnect()
    }
  }, [isOpen, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (ctxConvId && ctxConvId !== conversationId) {
      setConversationId(ctxConvId)
      setMessages([])
      setActiveActionType(null)
      setActionLabel(null)
    }
  }, [ctxConvId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (isOpen && conversationId) {
      loadHistory(conversationId)
    }
  }, [isOpen, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isStreaming, hitlPending])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || isCreating || isStreaming) return
    setInputText("")

    addMessage({
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: formatMessageTime(),
    })

    const actionResult = detectAction(text)

    if (actionResult.actionType === "wizard") {
      openSplitView("Vagas", conversationId ?? undefined)
      return
    }

    if (actionResult.actionType) {
      setActiveActionType(actionResult.actionType)
      setActionLabel(actionResult.label)
    }

    detectIntent(text).catch(() => {})

    let convId = conversationId
    if (!convId) {
      convId = await initConversation(text)
      if (!convId) {
        addMessage({
          id: `err-${Date.now()}`,
          sender: "lia",
          content: "Não consegui iniciar a conversa. Tente novamente.",
          timestamp: formatMessageTime(),
        })
        return
      }
      setSharedConversationId(convId)
      wsConnect()
    }

    const domain = actionResult.actionType ? actionTypeToDomain(actionResult.actionType) : ""
    wsSend(text, domain, currentScope)

  }, [
    inputText, conversationId, isCreating, isStreaming,
    addMessage, initConversation, detectAction, detectIntent,
    openSplitView, wsSend, wsConnect, setSharedConversationId, currentScope,
  ])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleExpand = useCallback(() => {
    expand()
  }, [expand])

  const handleNewChat = useCallback(() => {
    wsDisconnect()
    setMessages([])
    setConversationId(null)
    setActiveActionType(null)
    setActionLabel(null)
    clearIntent()
    setShowHistory(false)
  }, [wsDisconnect, setMessages, setConversationId, clearIntent])

  const handleClear = useCallback(() => {
    setMessages([])
    setShowHistory(false)
  }, [setMessages])

  const handleToggleHistory = useCallback(() => {
    if (!showHistory) {
      try {
        const raw = localStorage.getItem("lia-recent-items")
        const items = raw
          ? (JSON.parse(raw) as Array<{ id: string; type: string; title: string; timestamp: number }>)
          : []
        setRecentChats(items.filter(i => i.type === "chat").slice(0, 10))
      } catch {
        setRecentChats([])
      }
    }
    setShowHistory(prev => !prev)
  }, [showHistory])

  const handleLoadConversation = useCallback((id: string) => {
    setMessages([])
    setConversationId(id)
    setActiveActionType(null)
    setActionLabel(null)
    setShowHistory(false)
    loadHistory(id)
  }, [setMessages, setConversationId, loadHistory])

  const canSend = inputText.trim().length > 0 && !isCreating && !isStreaming
  const isEmpty = messages.length === 0 && !isStreaming && !isFetchingHistory

  if (!isOpen) return null

  return (
    <div
      className={cn(
 "fixed bottom-[84px] right-6 z-50" /* [OPT-022] bottom-[84px] px arbitrário — sem canônico Tailwind */,
        "w-[420px] h-[580px]",
        "flex flex-col",
        "bg-lia-bg-primary",
        "border border-lia-border-subtle",
        "rounded-xl shadow-lia-lg overflow-hidden"
      )}
      role="dialog"
      aria-label="Chat LIA"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-lia-border-subtle flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
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
            disabled={messages.length === 0}
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
                ? "text-chat-cyan bg-lia-bg-tertiary"
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

      {/* Action mode banner */}
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

      {/* WebSocket status banner */}
      {isReconnecting && (
        <div className="px-4 py-1.5 border-b flex-shrink-0 bg-status-warning/10 border-status-warning/30 dark:border-status-warning/30">
          <p className="text-xs text-status-warning">
            {`Reconectando… (tentativa ${reconnectAttempt}/3)`}
          </p>
        </div>
      )}

      {/* History panel */}
      {showHistory && (
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
      )}

      {!showHistory && (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
          {isFetchingHistory ? (
            <div className="flex justify-center items-center h-full" role="status" aria-live="polite" aria-label="Carregando...">
              <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
            </div>
          ) : isEmpty ? (
            <EmptyState />
          ) : (
            <>
              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} conversationId={conversationId} />
              ))}

              {hitlPending && (
                <div className="flex gap-2">
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
                    </div>
                    <HITLConfirmCard
                      action={hitlPending.action}
                      description={hitlPending.description}
                      onConfirm={() => sendApproval(true)}
                      onCancel={() => sendApproval(false)}
                    />
                  </div>
                </div>
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
      )}

      {/* FAR-2/C: Fairness warning banner */}
      <FairnessWarningBanner
        warnings={fairnessWarnings}
        onDismiss={dismissFairnessWarnings}
      />

      {/* Navigation hint */}
      {navIntent?.page && (
        <div className="px-4 py-2 border-t border-lia-border-subtle flex-shrink-0">
          <button
            onClick={() => {
              if (navIntent.page) {
                openSplitView(navIntent.page, conversationId ?? undefined)
                clearIntent()
              }
            }}
            className="flex items-center gap-2 text-sm-ui text-lia-text-tertiary hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none group w-full text-left"
            aria-label={`Abrir ${navIntent.page}`}
          >
            <ArrowRight className="w-3.5 h-3.5 flex-shrink-0 text-chat-cyan group-hover:translate-x-0.5 transition-transform motion-reduce:transition-none" />
            <span>{navIntent.hint ?? `Ver em ${navIntent.page}`}</span>
          </button>
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-lia-border-subtle">
        <div className="flex items-center gap-2 px-3 py-2 rounded-[24px] bg-lia-bg-primary border border-lia-border-subtle">
          <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
            <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
          </div>
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => {
              if (e.target.value.length <= MAX_INPUT_CHARS) setInputText(e.target.value)
            }}
            onKeyDown={handleKeyDown}
            placeholder={hitlPending ? "Confirme ou cancele a ação acima..." : "Envie mensagem para a LIA..."}
            disabled={isCreating || isStreaming || !!hitlPending}
            maxLength={MAX_INPUT_CHARS}
            aria-label="Mensagem para a LIA"
            className="flex-1 text-base-ui bg-transparent focus:outline-none text-lia-text-primary placeholder:text-lia-text-disabled disabled:opacity-50 min-w-0"
           
          />
          <AudioRecordButton
            onTranscription={(text) => setInputText(prev => prev ? `${prev} ${text}` : text)}
            className="p-1.5"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Enviar mensagem"
            className={cn(
 "flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center transition-colors",
              canSend
                ? "bg-chat-cyan text-white hover:opacity-90"
                : "bg-lia-interactive-active text-lia-text-disabled"
            )}
          >
            {isCreating || isStreaming
              ? <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none text-white" />
              : <Send className="w-3.5 h-3.5" />
            }
          </button>
        </div>
        {inputText.length > MAX_INPUT_CHARS * 0.9 && (
          <p className="text-xs text-lia-text-secondary mt-1 text-right">
            {inputText.length}/{MAX_INPUT_CHARS}
          </p>
        )}
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
      <div className="w-10 h-10 rounded-full flex items-center justify-center">
        <Brain className="w-5 h-5 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div>
        <p className="text-base-ui font-medium text-lia-text-secondary" >
          Como posso ajudar?
        </p>
        <p className="text-sm-ui text-lia-text-disabled mt-1" aria-live="polite" aria-atomic="true">
          Pergunte sobre vagas, candidatos, relatórios e muito mais.
        </p>
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
        </div>
        <span className="flex gap-1 items-center h-5">
          <ThinkingDots dotClassName="bg-chat-cyan" size="md" />
        </span>
      </div>
    </div>
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
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
        </div>
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-[14px] rounded-bl-[4px] px-3.5 py-2.5 max-w-[340px]">
          <RichContent
            html={html}
            className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
          />
          <span className="inline-block w-1.5 h-3.5 bg-chat-cyan ml-0.5 animate-pulse motion-reduce:animate-none align-middle" />
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg, conversationId }: { msg: FloatMessage; conversationId: string | null }) {
  const isUser = msg.sender === "user"

  const renderedHtml = useMemo(() => {
    if (isUser) return escapeHtml(msg.content).replace(/\n/g, "<br/>")
    const cleaned = cleanAgentResponse(msg.content)
    return parseChatMarkdown(cleaned)
  }, [msg.content, isUser])

  if (isUser) {
    return (
      <div className="flex gap-2.5 justify-end">
        <div className="flex flex-col items-end gap-1 max-w-[340px]">
          <div className="bg-lia-bg-tertiary rounded-[14px] rounded-br-[4px] px-3.5 py-2.5">
            <RichContent
              html={renderedHtml}
              className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
            />
          </div>
          <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums px-1">
            {msg.timestamp}
          </span>
        </div>
        <div className="w-7 h-7 rounded-full bg-lia-interactive-active flex items-center justify-center flex-shrink-0 mt-0.5">
          <User className="w-3.5 h-3.5 text-lia-text-tertiary" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-2.5">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-xs font-bold text-lia-text-primary" >LIA</span>
          <span className="text-xs text-lia-text-disabled font-['Inter',sans-serif] tabular-nums">{msg.timestamp}</span>
        </div>
        <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-[14px] rounded-bl-[4px] px-3.5 py-2.5 max-w-[340px]">
          <RichContent
            html={renderedHtml}
            className="text-base-ui text-lia-text-secondary leading-relaxed font-['Open_Sans',sans-serif]"
          />
        </div>
        {conversationId && (
          <MessageFeedback
            sessionId={conversationId}
            messageId={msg.id}
            originalResponse={msg.content}
            className="mt-1 px-1"
          />
        )}
      </div>
    </div>
  )
}
