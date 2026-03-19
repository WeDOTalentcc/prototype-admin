"use client"

/**
 * LiaSplitPanel — Painel lateral fixo da LIA em modo split-view.
 *
 * Renderizado à direita do conteúdo principal quando splitView.active = true.
 * Largura fixa: 360px. Mantém a conversa ativa enquanto o recrutador navega
 * na página sugerida pela LIA.
 *
 * Compatível com Vue/Nuxt: sem patterns React-only; lógica em hooks.
 */

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Brain, X, ExternalLink, Loader2, Send } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { useAgentStreaming } from "@/hooks/use-agent-streaming"
import {
  useFloatConversation,
  formatMessageTime,
  type FloatMessage,
} from "@/hooks/use-float-conversation"

const MAX_INPUT_CHARS = 2000

interface LiaSplitPanelProps {
  /** Callback chamado ao clicar em "Ver página completa" */
  onNavigate?: (page: string) => void
}

export function LiaSplitPanel({ onNavigate }: LiaSplitPanelProps) {
  const { splitView, closeSplitView, open: openFloat } = useLiaFloat()

  const {
    conversationId,
    messages,
    isCreating,
    isFetchingHistory,
    initConversation,
    loadHistory,
    addMessage,
  } = useFloatConversation(splitView.conversationId)

  const [inputText, setInputText] = useState("")
  const [streamingContent, setStreamingContent] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Carregar histórico ao ativar split-view com conversa existente
  useEffect(() => {
    if (splitView.active && conversationId) {
      loadHistory(conversationId)
    }
  }, [splitView.active, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  // ─── WebSocket streaming ──────────────────────────────────────────────────

  const sessionId = conversationId ?? "split-pending"

  const onStreamEvent = useCallback(
    (event: { type: string; content?: string }) => {
      if (event.type === "thinking") {
        setStreamingContent("...")
      } else if (event.type === "token" && event.content) {
        setStreamingContent(prev =>
          prev === "..." ? event.content! : prev + event.content!
        )
      } else if (event.type === "message" && event.content) {
        setStreamingContent("")
        addMessage({
          id: `lia-${Date.now()}`,
          sender: "lia",
          content: event.content,
          timestamp: formatMessageTime(),
        })
      } else if (event.type === "error") {
        setStreamingContent("")
        addMessage({
          id: `err-${Date.now()}`,
          sender: "lia",
          content:
            "Desculpe, tive um problema ao processar sua mensagem. Tente novamente.",
          timestamp: formatMessageTime(),
        })
      }
    },
    [addMessage]
  )

  const { isConnected, isStreaming, connect, disconnect, sendMessage: wsSend } =
    useAgentStreaming(sessionId, { autoReconnect: true }, onStreamEvent)

  useEffect(() => {
    if (splitView.active && conversationId) connect()
    if (!splitView.active) disconnect()
    return () => { disconnect() }
  }, [splitView.active, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamingContent])

  // ─── Envio ───────────────────────────────────────────────────────────────

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text || isCreating || isStreaming) return
    setInputText("")
    if (textareaRef.current) textareaRef.current.style.height = "auto"

    addMessage({
      id: `user-${Date.now()}`,
      sender: "user",
      content: text,
      timestamp: formatMessageTime(),
    })

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
      await new Promise(r => setTimeout(r, 200))
    }

    wsSend(text, { context_type: "general" }, "general")
  }, [inputText, conversationId, isCreating, isStreaming, addMessage, initConversation, wsSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend]
  )

  const handleTextChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const val = e.target.value
      if (val.length > MAX_INPUT_CHARS) return
      setInputText(val)
      const ta = textareaRef.current
      if (ta) {
        ta.style.height = "auto"
        ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`
      }
    },
    []
  )

  const handleClose = useCallback(() => {
    disconnect()
    closeSplitView()
    // Reabre como float para não perder contexto
    if (conversationId) openFloat(conversationId)
  }, [closeSplitView, openFloat, conversationId, disconnect])

  const handleNavigatePage = useCallback(() => {
    if (splitView.page && onNavigate) {
      onNavigate(splitView.page)
    }
  }, [splitView.page, onNavigate])

  if (!splitView.active) return null

  const canSend = inputText.trim().length > 0 && !isCreating && !isStreaming
  const isEmpty = messages.length === 0 && !streamingContent && !isFetchingHistory

  return (
    <div
      className={cn(
        "flex flex-col flex-shrink-0",
        "w-[360px] h-full",
        "bg-white dark:bg-gray-900",
        "border-l border-gray-200 dark:border-gray-800",
        "overflow-hidden"
      )}
      role="complementary"
      aria-label="LIA — painel lateral"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-cyan-500" />
          <div>
            <span className="text-[13px] font-semibold text-gray-900 dark:text-gray-50 block leading-tight">
              LIA
            </span>
            {splitView.page && (
              <span className="text-[11px] text-gray-400 dark:text-gray-500 leading-tight">
                {splitView.page}
              </span>
            )}
          </div>
          {isConnected && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-gray-500 ml-1"
              title="Conectado"
              aria-label="WebSocket conectado"
            />
          )}
        </div>
        <div className="flex items-center gap-1">
          {splitView.page && onNavigate && (
            <button
              onClick={handleNavigatePage}
              className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title={`Ir para ${splitView.page}`}
              aria-label={`Navegar para ${splitView.page}`}
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={handleClose}
            className="p-1.5 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Fechar painel lateral"
            aria-label="Fechar painel lateral"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Page hint banner */}
      {splitView.page && (
        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 flex-shrink-0">
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            Contexto atual:{" "}
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {splitView.page}
            </span>
          </p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {isFetchingHistory ? (
          <div className="flex justify-center items-center h-full">
            <Loader2 className="w-5 h-5 animate-spin text-gray-400" />
          </div>
        ) : isEmpty ? (
          <SplitEmptyState page={splitView.page} />
        ) : (
          <>
            {messages.map(msg => (
              <SplitMessageBubble key={msg.id} msg={msg} />
            ))}
            {streamingContent && (
              <SplitStreamingBubble content={streamingContent} />
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-end gap-2 rounded-md border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-2">
          <textarea
            ref={textareaRef}
            value={inputText}
            onChange={handleTextChange}
            onKeyDown={handleKeyDown}
            placeholder="Pergunte à LIA… (Enter para enviar)"
            rows={1}
            disabled={isCreating}
            maxLength={MAX_INPUT_CHARS}
            aria-label="Mensagem para a LIA"
            className={cn(
              "flex-1 resize-none bg-transparent text-[13px]",
              "text-gray-900 dark:text-gray-50 placeholder:text-gray-400 dark:placeholder:text-gray-500",
              "focus:outline-none py-1.5 px-1 max-h-[120px] leading-relaxed"
            )}
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Enviar mensagem"
            className={cn(
              "flex-shrink-0 p-2 rounded-md transition-colors",
              canSend
                ? "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-200"
                : "bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500 cursor-not-allowed"
            )}
          >
            {isCreating || isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        {inputText.length > MAX_INPUT_CHARS * 0.9 && (
          <p className="text-[11px] text-gray-400 mt-1 text-right">
            {inputText.length}/{MAX_INPUT_CHARS}
          </p>
        )}
      </div>
    </div>
  )
}

// ─── Sub-componentes ──────────────────────────────────────────────────────────

function SplitEmptyState({ page }: { page: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
      <div className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
        <Brain className="w-5 h-5 text-cyan-500" />
      </div>
      <div>
        <p className="text-[13px] font-medium text-gray-700 dark:text-gray-300">
          {page ? `Explorando ${page}` : "Como posso ajudar?"}
        </p>
        <p className="text-[12px] text-gray-400 dark:text-gray-500 mt-1">
          Continue a conversa enquanto navega pela página.
        </p>
      </div>
    </div>
  )
}

function SplitMessageBubble({ msg }: { msg: FloatMessage }) {
  const isUser = msg.sender === "user"
  return (
    <div className={cn("flex gap-2", isUser ? "flex-row-reverse" : "flex-row")}>
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0 mt-0.5">
          <Brain className="w-3.5 h-3.5 text-cyan-500" />
        </div>
      )}
      <div
        className={cn(
          "max-w-[85%] px-3 py-2 rounded-md text-[13px] leading-relaxed",
          isUser
            ? "bg-gray-900 dark:bg-gray-50 text-white dark:text-gray-900"
            : "bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-50"
        )}
      >
        <p className="whitespace-pre-wrap">{msg.content}</p>
        <span className="text-[10px] opacity-50 mt-1 block">{msg.timestamp}</span>
      </div>
    </div>
  )
}

function SplitStreamingBubble({ content }: { content: string }) {
  return (
    <div className="flex gap-2">
      <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Brain className="w-3.5 h-3.5 text-cyan-500" />
      </div>
      <div className="max-w-[85%] px-3 py-2 rounded-md text-[13px] leading-relaxed bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-50">
        {content === "..." ? (
          <span className="flex gap-1 items-center h-5">
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: "300ms" }} />
          </span>
        ) : (
          <p className="whitespace-pre-wrap">{content}</p>
        )}
      </div>
    </div>
  )
}
