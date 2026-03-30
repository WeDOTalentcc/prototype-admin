"use client"

import { useState, useRef, useCallback, useEffect, useMemo } from "react"
import {
  X, Minimize2, Send, Search, Brain,
  Mic, Paperclip, MessageSquare, LayoutDashboard,
  Plus, Eraser, History, Clock, User
} from "lucide-react"
import { AgentControlCenter } from "@/components/agent-control-center"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Button } from "@/components/ui/button"
import { useDynamicSuggestions, type DynamicSuggestion } from "@/hooks/useDynamicSuggestions"
import { useFloatConversation, formatMessageTime } from "@/hooks/use-float-conversation"
import { useFloatStreaming } from "@/hooks/use-float-streaming"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useActionIntent, actionTypeToDomain } from "@/hooks/use-action-intent"
import { resolveScopeFromPathname } from "@/hooks/use-current-scope"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { useRouter } from "next/navigation"

// [OPT-043] TODO: revisar inline styles dinâmicos (23 ocorrências)
const CATEGORY_COLORS: Record<string, { icon: string; bg: string; border: string; hoverBg: string }> = {
  vagas: { icon: 'var(--gray-600)', bg: 'var(--gray-50)', border: 'var(--gray-200)', hoverBg: 'var(--gray-100)' },
  candidatos: { icon: 'var(--status-success)', bg: 'var(--gray-50)', border: 'var(--status-success)', hoverBg: 'var(--gray-100)' },
  entrevistas: { icon: 'var(--wedo-orange)', bg: 'var(--gray-50)', border: 'var(--wedo-orange)', hoverBg: 'var(--gray-100)' },
  relatorios: { icon: 'var(--wedo-purple)', bg: 'var(--gray-50)', border: 'var(--wedo-purple)', hoverBg: 'var(--gray-100)' }
}

export function LiaSuperPrompt() {
  const {
    isExpanded, collapse, closeAll, conversationId: ctxConvId,
    sharedMessages, addSharedMessage, setSharedMessages,
    sharedConversationId, setSharedConversationId,
    openSplitView,
  } = useLiaFloat()
  const router = useRouter()
  const { suggestions, hasContextualData } = useDynamicSuggestions(isExpanded)
  const { detect: detectAction } = useActionIntent()
  const { detect: detectIntent } = useNavigationIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== "undefined" ? window.location.pathname : "")

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">("conversa")
  const [input, setInput] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; timestamp: number }>>([])

  const inputRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const {
    conversationId: localConvId,
    isCreating,
    initConversation,
    loadHistory,
  } = useFloatConversation(ctxConvId, setSharedMessages)

  const conversationId = sharedConversationId ?? localConvId
  const messages = sharedMessages

  const wsSessionId = conversationId ?? "float-pending"

  const handleStreamComplete = useCallback((content: string) => {
    addSharedMessage({
      id: `lia-${Date.now()}`,
      sender: "lia",
      content,
      timestamp: formatMessageTime(),
    })
  }, [addSharedMessage])

  const {
    isStreaming,
    streamingContent,
    sendMessage: wsSend,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useFloatStreaming(wsSessionId, handleStreamComplete)

  useEffect(() => {
    if (isExpanded && conversationId) {
      wsConnect()
      if (sharedMessages.length === 0) {
        loadHistory(conversationId)
      }
    }
    if (!isExpanded) {
      wsDisconnect()
    }
  }, [isExpanded, conversationId]) // eslint-disable-line react-hooks/exhaustive-deps

  const isEmptyChat = messages.length === 0

  useEffect(() => {
    if (isExpanded && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 300)
    }
  }, [isExpanded])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isStreaming])

  const handleSendMessage = useCallback(async (text?: string) => {
    const messageText = text || input.trim()
    if (!messageText || isCreating || isStreaming) return

    setInput("")

    addSharedMessage({
      id: `user-${Date.now()}`,
      sender: "user",
      content: messageText,
      timestamp: formatMessageTime(),
    })

    const actionResult = detectAction(messageText)

    if (actionResult.actionType === "wizard") {
      collapse()
      openSplitView("Vagas", conversationId ?? undefined)
      return
    }

    detectIntent(messageText).catch(() => {})

    let convId = conversationId
    if (!convId) {
      convId = await initConversation(messageText)
      if (!convId) {
        addSharedMessage({
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
    wsSend(messageText, domain, currentScope)
  }, [
    input, conversationId, isCreating, isStreaming,
    addSharedMessage, initConversation, detectAction, detectIntent,
    collapse, openSplitView, wsSend, wsConnect, setSharedConversationId, currentScope,
  ])

  const handleSuggestionClick = useCallback((suggestion: DynamicSuggestion) => {
    if (suggestion.actionType === "redirect" && suggestion.redirectPath) {
      collapse()
      router.push(suggestion.redirectPath)
      return
    }
    handleSendMessage(suggestion.command)
  }, [collapse, router, handleSendMessage])

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }, [handleSendMessage])

  const handleNewChat = useCallback(() => {
    wsDisconnect()
    setSharedMessages([])
    setSharedConversationId(null)
    setShowHistory(false)
  }, [wsDisconnect, setSharedMessages, setSharedConversationId])

  const handleClear = useCallback(() => {
    setSharedMessages([])
    setShowHistory(false)
  }, [setSharedMessages])

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
    setSharedMessages([])
    setSharedConversationId(id)
    setShowHistory(false)
    loadHistory(id)
  }, [setSharedMessages, setSharedConversationId, loadHistory])

  return (
    <>
      {isExpanded && (
        <div
          className="fixed inset-0 z-overlay flex items-center justify-center animate-in fade-in duration-200"
        >
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={collapse}
            aria-hidden="true"
          />

          {/* OPT-027: CSS scale/fade replacing framer-motion spring */}
          <div
            className="relative flex flex-col overflow-hidden rounded-xl border shadow-2xl bg-white dark:bg-lia-bg-primary animate-in fade-in zoom-in-90 slide-in-from-bottom-4 duration-300"
            style={{width: "95vw",
              height: "95vh",
              maxWidth: "1400px",
              maxHeight: "900px",
              borderColor: "var(--gray-200)"}}
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle dark:border-lia-border-subtle flex-shrink-0"
              style={{backgroundColor: "var(--gray-50)"}}
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-chat-cyan" strokeWidth={2.5} />
                  <span
                    className="text-lg font-bold"
                    style={{color: "var(--gray-800)", fontFamily: '"Inter", sans-serif'}}
                  >
                    LIA
                  </span>
                </div>

                <div className="flex rounded-lg overflow-hidden border" style={{borderColor: "var(--gray-200)"}}>
                  <button
                    onClick={() => setActiveTab("conversa")}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors"
                    style={{backgroundColor: activeTab === "conversa" ? "var(--gray-50)" : "transparent",
                      color: activeTab === "conversa" ? "var(--chat-cyan)" : "var(--gray-400)",
                      borderRight: "1px solid var(--gray-200)"}}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    Conversa
                  </button>
                  <button
                    onClick={() => setActiveTab("controle")}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors"
                    style={{backgroundColor: activeTab === "controle" ? "var(--gray-50)" : "transparent",
                      color: activeTab === "controle" ? "var(--chat-cyan)" : "var(--gray-400)"}}
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    Centro de Controle
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={handleNewChat}
                  className="p-2 rounded-lg lia-text-secondary hover:lia-text-base hover:bg-gray-100 transition-colors"
                  title="Novo chat"
                  aria-label="Iniciar novo chat"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={handleClear}
                  disabled={messages.length === 0}
                  className="p-2 rounded-lg lia-text-secondary hover:lia-text-base hover:bg-gray-100 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Limpar mensagens"
                  aria-label="Limpar mensagens"
                >
                  <Eraser className="w-4 h-4" />
                </button>
                <button
                  onClick={handleToggleHistory}
                  className={`p-2 rounded-lg transition-colors ${
 showHistory
                      ? "text-chat-cyan bg-gray-100"
                      : "lia-text-secondary hover:lia-text-base hover:bg-gray-100"
                  }`}
                  title="Histórico de conversas"
                  aria-label="Ver histórico de conversas"
                >
                  <History className="w-4 h-4" />
                </button>
                <div className="w-px h-5 bg-gray-200 mx-1" />
                <button
                  onClick={collapse}
                  className="p-2 rounded-lg lia-text-secondary hover:lia-text-base hover:bg-gray-100 transition-colors"
                  title="Minimizar para chat pequeno"
                  aria-label="Minimizar"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={closeAll}
                  className="p-2 rounded-lg lia-text-secondary hover:lia-text-base hover:bg-gray-100 transition-colors"
                  title="Fechar"
                  aria-label="Fechar"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col">
              {activeTab === "conversa" && (
                <div className="flex-1 flex flex-col overflow-hidden">
                  {/* History panel */}
                  {showHistory ? (
                    <div className="flex-1 overflow-y-auto px-6 py-4">
                      <p className="text-xs font-semibold lia-text-secondary uppercase tracking-wide mb-3" >
                        Conversas recentes
                      </p>
                      {recentChats.length === 0 ? (
                        <p className="text-base-ui lia-text-secondary text-center mt-10">
                          Nenhuma conversa anterior encontrada.
                        </p>
                      ) : (
                        <div className="space-y-1 max-w-3xl mx-auto">
                          {recentChats.map(chat => (
                            <button
                              key={chat.id}
                              onClick={() => handleLoadConversation(chat.id)}
                              className="w-full flex items-start gap-3 px-4 py-3 rounded-lg hover:bg-gray-50 transition-colors text-left group"
                            >
                              <Clock className="w-4 h-4 lia-text-secondary flex-shrink-0 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <p className="text-base-ui lia-text-base truncate group-hover:lia-text-strong transition-colors">
                                  {chat.title}
                                </p>
                                <p className="text-xs lia-text-secondary mt-0.5">
                                  {new Date(chat.timestamp).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })}
                                </p>
                              </div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto px-6 py-4">
                      {isEmptyChat ? (
                        <div className="flex flex-col items-center justify-center h-full max-w-3xl mx-auto">
                          <div className="text-center mb-8">
                            <LIAIcon size="xl" useChatCyan className="mb-4 mx-auto" />
                            <h2
                              className="text-3xl font-semibold mb-3"
                              style={{color: "var(--gray-800)"}}
                            >
                              Oi, eu sou a <span className="lia-text-base">LIA</span>.
                            </h2>
                            <p
                              className="text-base mb-2"
                              style={{color: "var(--gray-400)"}}
                            >
                              Sua assistente de recrutamento inteligente. Qual das tarefas abaixo quer que eu execute para você?
                            </p>
                            {hasContextualData && (
                              <p className="text-xs text-chat-cyan font-medium">
                                Sugestões personalizadas baseadas na sua atividade recente
                              </p>
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-3 w-full max-w-2xl">
                            {suggestions.map((suggestion) => {
                              const Icon = suggestion.icon
                              const colors = CATEGORY_COLORS[suggestion.category] || CATEGORY_COLORS.vagas
                              return (
                                <button
                                  key={suggestion.id}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className="p-4 rounded-lg transition-colors text-left group"
                                  style={{border: `1px solid ${colors.bg}`,
                                    backgroundColor: "var(--white)"}}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = colors.hoverBg
                                    e.currentTarget.style.borderColor = colors.border
                                    e.currentTarget.style.transform = "translateY(-2px)"
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = "var(--white)"
                                    e.currentTarget.style.borderColor = colors.bg
                                    e.currentTarget.style.transform = "translateY(0)"
                                  }}
                                >
                                  <div className="flex items-start gap-3">
                                    <div
                                      className="p-2 rounded-md flex-shrink-0"
                                      style={{backgroundColor: colors.bg}}
                                    >
                                      <Icon className="w-4 h-4" style={{color: colors.icon}} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h3
                                        className="font-semibold text-sm leading-tight mb-1"
                                        style={{color: "var(--gray-800)"}}
                                      >
                                        {suggestion.title}
                                      </h3>
                                      <p
                                        className="text-xs leading-snug line-clamp-2"
                                        style={{color: "var(--gray-500)"}}
                                      >
                                        {suggestion.description}
                                      </p>
                                      {suggestion.actionType === "redirect" && (
                                        <span className="inline-block mt-1 text-micro px-1.5 py-0.5 rounded-md bg-gray-100 lia-text-secondary">
                                          Abre em nova tela
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      ) : (
                        <div className="max-w-3xl mx-auto space-y-4">
                          {messages.map((message) => (
                            <SuperPromptBubble key={message.id} message={message} conversationId={conversationId} />
                          ))}

                          {isStreaming && streamingContent && (
                            <div className="flex items-start gap-2.5">
                              <div className="flex-shrink-0 pt-1">
                                <div className="w-7 h-7 rounded-full flex items-center justify-center">
                                  <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                                </div>
                              </div>
                              <SuperPromptStreamingBubble content={streamingContent} />
                            </div>
                          )}

                          {isStreaming && !streamingContent && (
                            <div className="flex items-start gap-2.5">
                              <div className="flex-shrink-0 pt-1">
                                <div className="w-7 h-7 rounded-full flex items-center justify-center">
                                  <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                                </div>
                              </div>
                              <div className="bg-lia-bg-primary border border-lia-border-subtle rounded-[14px] rounded-bl-[4px] p-4">
                                <div className="flex items-center gap-1.5">
                                  <div className="w-2 h-2 rounded-full bg-chat-cyan animate-bounce" style={{animationDelay: "0ms"}} />
                                  <div className="w-2 h-2 rounded-full bg-chat-cyan animate-bounce" style={{animationDelay: "150ms"}} />
                                  <div className="w-2 h-2 rounded-full bg-chat-cyan animate-bounce" style={{animationDelay: "300ms"}} />
                                </div>
                              </div>
                            </div>
                          )}

                          <div ref={messagesEndRef} />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Input */}
                  <div className="px-6 py-4 border-t border-lia-border-subtle flex-shrink-0" style={{backgroundColor: "var(--gray-50)"}}>
                    <div className="max-w-3xl mx-auto">
                      <div className="flex items-center gap-2 px-4 py-2.5 rounded-[24px] bg-lia-bg-primary border border-lia-border-subtle">
                        <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center">
                          <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
                        </div>
                        <textarea
                          ref={inputRef}
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyPress}
                          placeholder="Envie mensagem para a LIA..."
                          className="flex-1 resize-none text-base-ui focus:outline-none bg-transparent min-w-0"
                          style={{color: "var(--gray-800)"}}
                          rows={1}
                        />
                        <AudioRecordButton
                          onTranscription={(text) => setInput(prev => prev ? `${prev} ${text}` : text)}
                          className="p-1.5"
                        />
                        <button
                          onClick={() => handleSendMessage()}
                          disabled={!input.trim() || isCreating || isStreaming}
                          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
 input.trim() && !isCreating && !isStreaming
                              ? "bg-chat-cyan text-white hover:opacity-90"
                              : "bg-gray-200 lia-text-secondary cursor-not-allowed"
                          }`}
                          aria-label="Enviar mensagem"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "controle" && (
                <div className="flex-1 overflow-y-auto px-6 py-4">
                  <AgentControlCenter className="max-w-5xl mx-auto" />
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

function SuperPromptBubble({ message, conversationId }: { message: { id: string; sender: string; content: string; timestamp: string }; conversationId: string | null }) {
  const isUser = message.sender === "user"
  const html = useMemo(() => {
    if (isUser) return escapeHtml(message.content).replace(/\n/g, "<br/>")
    const cleaned = cleanAgentResponse(message.content)
    return parseChatMarkdown(cleaned)
  }, [message.content, isUser])

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="flex items-start gap-2.5 max-w-3xl">
          <div className="flex flex-col items-end gap-1">
            <div
              className="rounded-[14px] rounded-br-[4px] px-4 py-3"
              style={{backgroundColor: "var(--gray-50)"}}
            >
              <div
                className="text-base-ui leading-relaxed lia-text-base"
               
                dangerouslySetInnerHTML={{ __html: html }}
              />
            </div>
            <span className="text-xs lia-text-secondary px-1" style={{fontFamily: '"Inter", sans-serif'}}>
              {message.timestamp}
            </span>
          </div>
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center mt-1">
            <User className="w-3.5 h-3.5 lia-text-secondary" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2.5 max-w-4xl">
      <div className="flex-shrink-0 pt-1">
        <div className="w-7 h-7 rounded-full flex items-center justify-center">
          <Brain className="w-4 h-4 text-chat-cyan" strokeWidth={2.5} />
        </div>
      </div>
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold lia-text-strong" style={{fontFamily: '"Inter", sans-serif'}}>LIA</span>
          <span className="text-xs lia-text-secondary" style={{fontFamily: '"Inter", sans-serif'}}>
            {message.timestamp}
          </span>
        </div>
        <div
          className="rounded-[14px] rounded-bl-[4px] px-4 py-3 bg-lia-bg-primary border border-lia-border-subtle"
        >
          <div
            className="text-base-ui leading-relaxed lia-text-base"
           
            dangerouslySetInnerHTML={{ __html: html }}
          />
        </div>
        {conversationId && (
          <MessageFeedback
            sessionId={conversationId}
            messageId={message.id}
            originalResponse={message.content}
            className="px-1"
          />
        )}
      </div>
    </div>
  )
}

function SuperPromptStreamingBubble({ content }: { content: string }) {
  const cleaned = useMemo(() => cleanAgentResponse(content), [content])
  const html = useMemo(() => parseChatMarkdown(cleaned), [cleaned])

  return (
    <div className="flex-1 flex flex-col gap-1">
      <div className="flex items-center gap-1.5 px-1">
        <span className="text-xs font-bold lia-text-strong" style={{fontFamily: '"Inter", sans-serif'}}>LIA</span>
      </div>
      <div className="rounded-[14px] rounded-bl-[4px] px-4 py-3 bg-lia-bg-primary border border-lia-border-subtle">
        <div
          className="text-base-ui leading-relaxed lia-text-base"
         
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <span className="inline-block w-1.5 h-3.5 bg-chat-cyan ml-0.5 animate-pulse align-middle" />
      </div>
    </div>
  )
}
