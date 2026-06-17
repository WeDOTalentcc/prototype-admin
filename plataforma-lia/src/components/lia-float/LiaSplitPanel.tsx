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
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { ThinkingDots } from "@/components/ui/thinking-dots"
import { formatMessageTime, type LiaChatMessage } from "@/hooks/chat/lia-chat-connection-types"
import { ChatBubbleBase } from "@/components/chat/chat-bubble-base"


const MAX_INPUT_CHARS = 2000

interface LiaSplitPanelProps {
  /** Callback chamado ao clicar em "Ver página completa" */
  onNavigate?: (page: string) => void
}

export function LiaSplitPanel({ onNavigate }: LiaSplitPanelProps) {
  const { splitView, closeSplitView, open: openFloat } = useLiaFloat()
  const {
    chatIsConnected: isConnected,
    chatIsStreaming: isStreaming,
    chatStreamingContent: ctxStreamingContent,
    chatIsCreating: ctxIsCreating,
    chatIsFetchingHistory: ctxIsFetchingHistory,
    sendChatMessage,
    connectChat,
    disconnectChat,
    initChatConversation,
    loadChatHistory,
    addChatMessage,
    chatConversationId,
    setChatConversationId,
  } = useLiaChatContext()

  const conversationId = chatConversationId ?? splitView.conversationId ?? null
  const isCreating = ctxIsCreating
  const isFetchingHistory = ctxIsFetchingHistory
  const streamingContent = ctxStreamingContent

  const { chatMessages: messages, setChatMessages } = useLiaChatContext()

  const initConversation = initChatConversation
  const loadHistory = useCallback(async (id: string) => {
    const history = await loadChatHistory(id)
    setChatMessages(history)
  }, [loadChatHistory, setChatMessages])

  const [inputText, setInputText] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (splitView.active && conversationId) {
      loadHistory(conversationId)
    }
  }, [splitView.active, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (splitView.active && conversationId) connectChat()
    if (!splitView.active) disconnectChat()
    return () => { disconnectChat() }
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

    let convId = conversationId
    if (!convId) {
      convId = await initConversation(text)
      if (!convId) {
        addChatMessage({
          id: `err-${Date.now()}`,
          sender: "lia",
          content: "Não consegui iniciar a conversa. Tente novamente.",
          timestamp: formatMessageTime(),
        })
        return
      }
      setChatConversationId(convId)
      connectChat()
      await new Promise(r => setTimeout(r, 200))
    }

    sendChatMessage(text, "general")
  }, [inputText, conversationId, isCreating, isStreaming, addChatMessage, initConversation, sendChatMessage, setChatConversationId, connectChat])

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
    disconnectChat()
    closeSplitView()
    if (conversationId) openFloat(conversationId)
  }, [closeSplitView, openFloat, conversationId, disconnectChat])

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
        "bg-lia-bg-primary",
        "border-r border-lia-border-subtle order-first",
        "overflow-hidden"
      )}
      role="complementary"
      aria-label="LIA — painel lateral"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-wedo-cyan" />
          <div>
            <span className="text-sm-ui font-semibold text-lia-text-primary block leading-tight">
              LIA
            </span>
            {splitView.page && (
              <span className="text-xs text-lia-text-muted leading-tight">
                {splitView.page}
              </span>
            )}
          </div>
          {isConnected && (
            <span
              className="w-1.5 h-1.5 rounded-full bg-lia-border-medium ml-1"
              title="Conectado"
              aria-label="WebSocket conectado"
            />
          )}
        </div>
        <div className="flex items-center gap-1">
          {splitView.page && onNavigate && (
            <button
              onClick={handleNavigatePage}
              className="p-1.5 rounded-md text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              title={`Ir para ${splitView.page}`}
              aria-label={`Navegar para ${splitView.page}`}
            >
              <ExternalLink className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={handleClose}
            className="p-1.5 rounded-md text-lia-text-secondary hover:text-lia-text-secondary dark:hover:text-lia-text-tertiary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
            title="Fechar painel lateral"
            aria-label="Fechar painel lateral"
            data-dismiss="true"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Page hint banner */}
      {splitView.page && (
        <div className="px-4 py-2 bg-lia-bg-secondary flex-shrink-0">
          <p className="text-xs text-lia-text-tertiary">
            Contexto atual:{" "}
            <span className="font-medium text-lia-text-secondary">
              {splitView.page}
            </span>
          </p>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4" role="status" aria-live="polite" aria-label="Carregando...">
        {isFetchingHistory ? (
          <div className="flex justify-center items-center h-full" role="status" aria-live="polite" aria-label="Carregando...">
            <Loader2 className="w-5 h-5 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
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
      <div className="px-4 pb-4 pt-2 flex-shrink-0 border-t border-lia-border-subtle">
        <div className="flex items-end gap-2 rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-2">
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
 "flex-1 resize-none bg-transparent text-sm-ui",
              "text-lia-text-primary placeholder:text-lia-text-disabled dark:placeholder:text-lia-text-tertiary",
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
                ? "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
                : "bg-lia-bg-tertiary text-lia-text-disabled cursor-not-allowed"
            )}
          >
            {isCreating || isStreaming ? (
              <Loader2 className="w-4 h-4 animate-spin motion-reduce:animate-none" />
            ) : (
              <Send className="w-4 h-4" />
            )}
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

// ─── Sub-componentes ──────────────────────────────────────────────────────────

function SplitEmptyState({ page }: { page: string | null }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
      <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
        <Brain className="w-5 h-5 text-wedo-cyan" />
      </div>
      <div>
        <p className="text-sm-ui font-medium text-lia-text-secondary">
          {page ? `Explorando ${page}` : "Como posso ajudar?"}
        </p>
        <p className="text-sm-ui text-lia-text-disabled mt-1">
          Continue a conversa enquanto navega pela página.
        </p>
      </div>
    </div>
  )
}

function SplitMessageBubble({ msg }: { msg: LiaChatMessage }) {
  const isUser = msg.sender === "user"
  return (
    <ChatBubbleBase
      sender={isUser ? "user" : "lia"}
      timestamp={msg.timestamp}
    >
      <p className="text-xs leading-relaxed text-lia-text-primary whitespace-pre-wrap">{msg.content}</p>
    </ChatBubbleBase>
  )
}

function SplitStreamingBubble({ content }: { content: string }) {
  return (
    <ChatBubbleBase sender="lia">
      {content === "..." ? (
        <span className="flex gap-1 items-center h-5">
          <ThinkingDots dotClassName="bg-lia-border-medium" size="md" />
        </span>
      ) : (
        <p className="text-xs leading-relaxed text-lia-text-primary whitespace-pre-wrap">{content}</p>
      )}
    </ChatBubbleBase>
  )
}
