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

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Brain, X, Maximize2, Loader2, Send, ArrowRight, Plus, Eraser, History, Clock } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useActionIntent, actionTypeToDomain, type ActionType } from "@/hooks/use-action-intent"
import { useFloatStreaming } from "@/hooks/use-float-streaming"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import {
  useFloatConversation,
  formatMessageTime,
  type FloatMessage,
} from "@/hooks/use-float-conversation"
import { resolveScopeFromPathname } from "@/hooks/use-current-scope"

const MAX_INPUT_CHARS = 2000

export function LiaChatPanel() {
  const { isOpen, conversationId: ctxConvId, close, openSplitView } = useLiaFloat()
  const { result: navIntent, detect: detectIntent, clear: clearIntent } = useNavigationIntent()
  const { detect: detectAction } = useActionIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== 'undefined' ? window.location.pathname : '')
  const [activeActionType, setActiveActionType] = useState<ActionType>(null)
  const [actionLabel, setActionLabel] = useState<string | null>(null)

  const {
    conversationId,
    messages,
    isCreating,
    isFetchingHistory,
    initConversation,
    loadHistory,
    addMessage,
    setMessages,
    setConversationId,
  } = useFloatConversation(ctxConvId)

  const [inputText, setInputText] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; timestamp: number }>>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // ── WebSocket (Nível 2/3) ──────────────────────────────────────────────────

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
    sendMessage: wsSend,
    sendApproval,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useFloatStreaming(wsSessionId, handleStreamComplete)

  // Conecta WebSocket quando o painel abre e há conversationId
  useEffect(() => {
    if (isOpen && conversationId) {
      wsConnect()
    }
    if (!isOpen) {
      wsDisconnect()
    }
  }, [isOpen, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Sincronização de estado ────────────────────────────────────────────────

  useEffect(() => {
    if (ctxConvId !== conversationId) {
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

  // ── Envio de mensagem ──────────────────────────────────────────────────────

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

    // Classificação de intent de ação (local, sem LLM)
    const actionResult = detectAction(text)

    // Wizard → redireciona para Vagas com split-view (agente wizard no painel)
    if (actionResult.actionType === "wizard") {
      openSplitView("Vagas", conversationId ?? undefined)
      return
    }

    // Outros modos de ação → ativa banner
    if (actionResult.actionType) {
      setActiveActionType(actionResult.actionType)
      setActionLabel(actionResult.label)
    }

    // Detecção de navegação (async, backend)
    detectIntent(text).catch(() => {})

    // Garante conversationId (cria via REST na primeira mensagem)
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
      // Reconecta WebSocket com o sessionId real
      wsConnect()
    }

    // Determina domain do agente pelo tipo de ação detectado
    const domain = actionResult.actionType ? actionTypeToDomain(actionResult.actionType) : ""
    // P2-B: inclui scope atual para o backend selecionar ferramentas corretas
    wsSend(text, domain, currentScope)

  }, [
    inputText, conversationId, isCreating, isStreaming,
    addMessage, initConversation, detectAction, detectIntent,
    openSplitView, wsSend, wsConnect,
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
    close()
    window.location.href = conversationId
      ? `/chat?conversationId=${conversationId}`
      : "/chat"
  }, [conversationId, close])

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
        "fixed bottom-[84px] right-6 z-50",
        "w-[420px] h-[580px]",
        "flex flex-col",
        "bg-white dark:bg-gray-900",
        "border border-gray-200 dark:border-gray-800",
        "rounded-md shadow-xl overflow-hidden"
      )}
      role="dialog"
      aria-label="Chat LIA"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-white dark:bg-gray-800 flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
          </div>
          <span className="text-[13px] font-bold text-gray-900 dark:text-gray-50" style={{ fontFamily: "Inter, sans-serif" }}>LIA</span>
          {/* Indicador de conexão WebSocket */}
          {isConnected && (
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 flex-shrink-0" title="Conectado" />
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleNewChat}
            className="p-1.5 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Novo chat"
            aria-label="Iniciar novo chat"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleClear}
            disabled={messages.length === 0}
            className="p-1.5 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
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
                ? "text-wedo-cyan bg-gray-100 dark:bg-gray-800"
                : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
            )}
            title="Histórico de conversas"
            aria-label="Ver histórico de conversas"
            aria-expanded={showHistory}
          >
            <History className="w-3.5 h-3.5" />
          </button>
          <div className="w-px h-4 bg-gray-200 dark:bg-gray-700 mx-0.5" />
          <button
            onClick={handleExpand}
            className="p-1.5 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Expandir para chat completo"
            aria-label="Expandir chat"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={close}
            className="p-1.5 rounded-md text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Fechar"
            aria-label="Fechar chat"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Action mode banner */}
      {activeActionType && actionLabel && (
        <div className="px-4 py-1.5 bg-gray-50 dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
          <span className="text-[11px] text-gray-500 dark:text-gray-400 font-medium" style={{ fontFamily: "Open Sans, sans-serif" }}>
            {actionLabel}
          </span>
          <button
            onClick={() => { setActiveActionType(null); setActionLabel(null) }}
            className="text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            aria-label="Sair do modo de ação"
          >
            Sair
          </button>
        </div>
      )}

      {/* WebSocket status banner — reconectando ou erro permanente */}
      {(isReconnecting || wsError) && (
        <div className={cn(
          "px-4 py-1.5 border-b flex-shrink-0",
          isReconnecting
            ? "bg-amber-50 dark:bg-amber-950/30 border-amber-100 dark:border-amber-900"
            : "bg-red-50 dark:bg-red-950/30 border-red-100 dark:border-red-900"
        )}>
          <p className={cn(
            "text-[11px]",
            isReconnecting
              ? "text-amber-700 dark:text-amber-400"
              : "text-red-600 dark:text-red-400"
          )} style={{ fontFamily: "Open Sans, sans-serif" }}>
            {isReconnecting
              ? `Reconectando… (tentativa ${reconnectAttempt}/3)`
              : "Conexão perdida. Recarregue a página ou abra um novo chat."
            }
          </p>
        </div>
      )}

      {/* History panel */}
      {showHistory && (
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-1">
          <p className="text-[11px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2" style={{ fontFamily: "Inter, sans-serif" }}>
            Conversas recentes
          </p>
          {recentChats.length === 0 ? (
            <p className="text-[12px] text-gray-400 dark:text-gray-500 text-center mt-6" style={{ fontFamily: "Open Sans, sans-serif" }}>
              Nenhuma conversa anterior encontrada.
            </p>
          ) : (
            recentChats.map(chat => (
              <button
                key={chat.id}
                onClick={() => handleLoadConversation(chat.id)}
                className="w-full flex items-start gap-2.5 px-3 py-2.5 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left group"
              >
                <Clock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-[12px] text-gray-700 dark:text-gray-300 truncate group-hover:text-gray-900 dark:group-hover:text-gray-100 transition-colors" style={{ fontFamily: "Open Sans, sans-serif" }}>
                    {chat.title}
                  </p>
                  <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5" style={{ fontFamily: "Open Sans, sans-serif" }}>
                    {new Date(chat.timestamp).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {!showHistory && (
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {isFetchingHistory ? (
            <div className="flex justify-center items-center h-full">
              <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
            </div>
          ) : isEmpty ? (
            <EmptyState />
          ) : (
            <>
              {messages.map(msg => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}

              {hitlPending && (
                <div className="flex gap-2">
                  <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="text-[10px] font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: "Inter, sans-serif" }}>LIA</span>
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

      {/* Navigation hint */}
      {navIntent?.page && (
        <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-800 flex-shrink-0">
          <button
            onClick={() => {
              if (navIntent.page) {
                openSplitView(navIntent.page, conversationId ?? undefined)
                clearIntent()
              }
            }}
            className="flex items-center gap-2 text-[12px] text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors group w-full text-left"
            aria-label={`Abrir ${navIntent.page}`}
          >
            <ArrowRight className="w-3.5 h-3.5 flex-shrink-0 text-wedo-cyan group-hover:translate-x-0.5 transition-transform" />
            <span>{navIntent.hint ?? `Ver em ${navIntent.page}`}</span>
          </button>
        </div>
      )}

      {/* Input */}
      <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2 p-2 rounded-md bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
          <div className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center">
            <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
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
            className="flex-1 text-xs bg-transparent focus:outline-none text-gray-950 dark:text-gray-50 disabled:opacity-50"
            style={{ fontFamily: "Open Sans, sans-serif" }}
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
            className="flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center transition-colors disabled:opacity-50 bg-gray-900 dark:bg-gray-50"
          >
            {isCreating || isStreaming
              ? <Loader2 className="w-3.5 h-3.5 animate-spin text-white dark:text-gray-900" />
              : <Send className="w-3.5 h-3.5 text-white dark:text-gray-900" />
            }
          </button>
        </div>
        {inputText.length > MAX_INPUT_CHARS * 0.9 && (
          <p className="text-[11px] text-gray-400 mt-1 text-right" style={{ fontFamily: "Open Sans, sans-serif" }}>
            {inputText.length}/{MAX_INPUT_CHARS}
          </p>
        )}
      </div>
    </div>
  )
}

// ── Sub-componentes ────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
      <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <Brain className="w-5 h-5 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div>
        <p className="text-[13px] font-medium text-gray-700 dark:text-gray-300" style={{ fontFamily: "Inter, sans-serif" }}>
          Como posso ajudar?
        </p>
        <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1" style={{ fontFamily: "Open Sans, sans-serif" }}>
          Pergunte sobre vagas, candidatos, relatórios e muito mais.
        </p>
      </div>
    </div>
  )
}

function ThinkingIndicator() {
  return (
    <div className="flex gap-2">
      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-[10px] font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: "Inter, sans-serif" }}>LIA</span>
        </div>
        <span className="flex gap-1 items-center h-5">
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }} />
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "150ms" }} />
          <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }} />
        </span>
      </div>
    </div>
  )
}

function StreamingBubble({ content }: { content: string }) {
  return (
    <div className="flex gap-2">
      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-[10px] font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: "Inter, sans-serif" }}>LIA</span>
        </div>
        <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2 max-w-[320px]">
          <p className="text-[12px] text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap" style={{ fontFamily: "Open Sans, sans-serif" }}>
            {renderFormattedContent(content)}
            <span className="inline-block w-1.5 h-3.5 bg-wedo-cyan ml-0.5 animate-pulse align-middle" />
          </p>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ msg }: { msg: FloatMessage }) {
  const isUser = msg.sender === "user"

  if (isUser) {
    return (
      <div className="flex gap-2 justify-end">
        <div className="flex flex-col items-end gap-0.5 max-w-[320px]">
          <div className="rounded-md bg-gray-100 dark:bg-gray-800 px-3 py-2">
            <p className="text-[12px] text-gray-800 dark:text-gray-200 leading-relaxed" style={{ fontFamily: "Open Sans, sans-serif" }}>
              {msg.content}
            </p>
          </div>
          <span className="text-[10px] text-gray-400 dark:text-gray-500" style={{ fontFamily: "Open Sans, sans-serif" }}>
            {msg.timestamp}
          </span>
        </div>
        <div className="w-6 h-6 rounded-md bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0 mt-0.5">
          <span className="text-[10px] font-bold text-gray-500 dark:text-gray-400">V</span>
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-2">
      <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-1.5 mb-0.5">
          <span className="text-[10px] font-bold text-gray-800 dark:text-gray-200" style={{ fontFamily: "Inter, sans-serif" }}>LIA</span>
          <span className="text-[10px] text-gray-400 dark:text-gray-500" style={{ fontFamily: "Open Sans, sans-serif" }}>{msg.timestamp}</span>
        </div>
        <div className="rounded-md bg-gray-50 dark:bg-gray-800 px-3 py-2 max-w-[320px]">
          <div className="text-[12px] text-gray-800 dark:text-gray-200 leading-relaxed" style={{ fontFamily: "Open Sans, sans-serif" }}>
            {renderFormattedContent(msg.content)}
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Renderiza markdown básico: bold, links internos/externos, quebras de linha.
 * Links internos (começam com /) usam navegação SPA; externos abrem em nova aba.
 */
function renderFormattedContent(content: string): React.ReactNode[] {
  // Divide por bold (**texto**) e links markdown ([texto](url))
  const parts = content.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/)
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    const linkMatch = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/)
    if (linkMatch) {
      const [, label, href] = linkMatch
      const isInternal = href.startsWith("/")
      return (
        <a
          key={i}
          href={href}
          target={isInternal ? undefined : "_blank"}
          rel={isInternal ? undefined : "noopener noreferrer"}
          className="text-wedo-cyan underline hover:opacity-80 transition-opacity"
        >
          {label}
        </a>
      )
    }
    return <span key={i}>{part}</span>
  })
}
