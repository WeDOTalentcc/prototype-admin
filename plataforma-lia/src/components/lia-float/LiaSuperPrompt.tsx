"use client"

import { useState, useRef, useCallback, useEffect, useMemo } from "react"
import {
  X, Minimize2, Send, Search, Brain,
  Mic, Paperclip, MessageSquare, LayoutDashboard,
  Plus, Eraser, History, Clock, User
} from "lucide-react"
import { useAuthStore } from "@/stores/auth-store"
import { AgentControlCenter } from "@/components/agent-control-center"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Button } from "@/components/ui/button"
import { useDynamicSuggestions, type DynamicSuggestion } from "@/hooks/ai/useDynamicSuggestions"
import { formatMessageTime } from "@/hooks/chat/lia-chat-connection-types"
import { useNavigationIntent } from "@/hooks/shared/use-navigation-intent"
import { useActionIntent, actionTypeToDomain } from "@/hooks/shared/use-action-intent"
import { resolveScopeFromPathname } from "@/hooks/company/use-current-scope"
import { cleanAgentResponse, parseChatMarkdown, escapeHtml } from "@/lib/chat-format"
import { sanitizeHtml } from "@/lib/sanitize"
import { MessageFeedback } from "@/components/chat/message-feedback"
import { AudioRecordButton } from "@/components/ui/audio-record-button"
import { useRouter } from "next/navigation"
import { AgentActivityTimeline } from "@/components/unified-chat/AgentActivityTimeline"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import { ContextBadge } from "@/components/lia-float/ContextBadge"
import { ComplianceBadge } from "@/components/lia-float/ComplianceBadge"

const CATEGORY_COLORS: Record<string, { icon: string; bg: string; border: string; hoverBg: string }> = {
  vagas: { icon: 'var(--lia-text-secondary)', bg: 'var(--lia-bg-secondary)', border: 'var(--lia-border-subtle)', hoverBg: 'var(--lia-bg-tertiary)' },
  candidatos: { icon: 'var(--status-success)', bg: 'var(--lia-bg-secondary)', border: 'var(--status-success)', hoverBg: 'var(--lia-bg-tertiary)' },
  entrevistas: { icon: 'var(--wedo-orange)', bg: 'var(--lia-bg-secondary)', border: 'var(--wedo-orange)', hoverBg: 'var(--lia-bg-tertiary)' },
  relatorios: { icon: 'var(--wedo-purple)', bg: 'var(--lia-bg-secondary)', border: 'var(--wedo-purple)', hoverBg: 'var(--lia-bg-tertiary)' }
}

export function LiaSuperPrompt() {
  const {
    isExpanded, collapse, closeAll, conversationId: ctxConvId,
    sharedMessages, addSharedMessage, setSharedMessages,
    sharedConversationId, setSharedConversationId,
    openSplitView, contextPage,
  } = useLiaFloat()
  const {
    chatConversationId,
    setChatConversationId,
    chatIsStreaming,
    chatIsThinking,
    chatThinkingSteps,
    chatStreamingContent,
    chatIsCreating,
    sendChatMessage,
    connectChat,
    disconnectChat,
    initChatConversation,
    loadChatHistory,
  } = useLiaChatContext()
  const router = useRouter()
  const { suggestions, hasContextualData } = useDynamicSuggestions(isExpanded)
  const { detect: detectAction } = useActionIntent()
  const { detect: detectIntent } = useNavigationIntent()
  const currentScope = resolveScopeFromPathname(typeof window !== "undefined" ? window.location.pathname : "")

  const [activeTab, setActiveTab] = useState<"conversa" | "controle">("conversa")
  const [input, setInput] = useState("")
  const [showHistory, setShowHistory] = useState(false)
  const [recentChats, setRecentChats] = useState<Array<{ id: string; title: string; timestamp: number }>>([])
  const [contextDismissed, setContextDismissed] = useState(false)

  // AgentActivityTimeline lifecycle — mirrors UnifiedMessageList.
  // ON when thinking/streaming starts; OFF after timeline fires onFinished.
  const [liveActive, setLiveActive] = useState(false)
  useEffect(() => {
    if (isThinking || isStreaming) {
      setLiveActive(true)
    }
  }, [isThinking, isStreaming])
  // Failsafe: force-clear if onFinished never fires (e.g. timeline never mounts)
  useEffect(() => {
    if (!liveActive || isThinking || isStreaming) return
    const t = setTimeout(() => setLiveActive(false), 3000)
    return () => clearTimeout(t)
  }, [liveActive, isThinking, isStreaming])
  useEffect(() => { setContextDismissed(false) }, [contextPage])

  const inputRef = useRef<HTMLTextAreaElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const conversationId = chatConversationId ?? sharedConversationId
  const messages = sharedMessages
  const isCreating = chatIsCreating
  const isStreaming = chatIsStreaming
  const isThinking = chatIsThinking
  const thinkingSteps = chatThinkingSteps
  const streamingContent = chatStreamingContent
  const initConversation = initChatConversation
  const loadHistory = useCallback(async (id: string) => {
    const history = await loadChatHistory(id)
    setSharedMessages(history)
  }, [loadChatHistory, setSharedMessages])

  useEffect(() => {
    if (isExpanded && conversationId) {
      connectChat()
      if (sharedMessages.length === 0) {
        loadHistory(conversationId)
      }
    }
    if (!isExpanded) {
      disconnectChat()
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
  }, [messages, isStreaming, streamingContent])

  const handleSendMessage = useCallback(async (text?: string) => {
    const messageText = text || input.trim()
    if (!messageText || isCreating || isStreaming) return

    setInput("")

    const actionResult = detectAction(messageText)

    if (actionResult.actionType === "wizard") {
      collapse()
      openSplitView("Vagas", conversationId ?? undefined)
      return
    }

    detectIntent(messageText).catch((err) => { console.warn('[LiaSuperPrompt] detectIntent fire-and-forget failed', err) })

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
      setChatConversationId(convId)
      connectChat()
    }

    const domain = actionResult.actionType ? actionTypeToDomain(actionResult.actionType) : ""
    const effectiveScope = contextDismissed ? "global" : currentScope
    sendChatMessage(messageText, domain, effectiveScope)
  }, [
    input, conversationId, isCreating, isStreaming,
    addSharedMessage, initConversation, detectAction, detectIntent,
    collapse, openSplitView, sendChatMessage, connectChat, setSharedConversationId, setChatConversationId, currentScope,
    contextDismissed,
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
    disconnectChat()
    setSharedMessages([])
    setSharedConversationId(null)
    setChatConversationId(null)
    setShowHistory(false)
    setContextDismissed(false)
  }, [disconnectChat, setSharedMessages, setSharedConversationId, setChatConversationId])

  const handleClear = useCallback(() => {
    disconnectChat()
    setSharedMessages([])
    setSharedConversationId(null)
    setChatConversationId(null)
    setShowHistory(false)
    setContextDismissed(false)
  }, [disconnectChat, setSharedMessages, setSharedConversationId, setChatConversationId])

  const handleToggleHistory = useCallback(() => {
    if (!showHistory) {
      const items = useUIPreferencesStore.getState().liaRecentItems
      setRecentChats(items.filter(i => i.type === "chat").slice(0, 10))
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
            className="absolute inset-0 bg-lia-overlay backdrop-blur-sm"
            onClick={collapse}
            aria-hidden="true"
          />

          {/* OPT-027: CSS scale/fade replacing framer-motion spring */}
          <div
            className="relative flex flex-col overflow-hidden rounded-xl border border-lia-border-subtle shadow-2xl bg-lia-bg-primary animate-in fade-in zoom-in-90 slide-in-from-bottom-4 duration-300 w-[95vw] h-[95vh] max-w-[1400px] max-h-[900px]"
          >
            {/* Header */}
            <div
              className="flex items-center justify-between px-6 py-4 flex-shrink-0"
             
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-wedo-cyan" strokeWidth={2.5} />
                  <span
                    className="text-lg font-semibold text-lia-text-primary"
                  >
                    LIA
                  </span>
                </div>

                <div className="flex rounded-lg overflow-hidden border">
                  <button
                    onClick={() => setActiveTab("conversa")}
                    className={`flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors motion-reduce:transition-none border-r border-lia-border-subtle ${activeTab === "conversa" ? "bg-lia-bg-secondary text-wedo-cyan" : "bg-transparent text-lia-text-tertiary"}`}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    Conversa
                  </button>
                  <button
                    onClick={() => setActiveTab("controle")}
                    className={`flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors motion-reduce:transition-none ${activeTab === "controle" ? "bg-lia-bg-secondary text-wedo-cyan" : "bg-transparent text-lia-text-tertiary"}`}
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    Centro de Controle
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={handleNewChat}
                  className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Novo chat"
                  aria-label="Iniciar novo chat"
                >
                  <Plus className="w-4 h-4" />
                </button>
                <button
                  onClick={handleClear}
                  disabled={messages.length === 0}
                  className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Limpar mensagens"
                  aria-label="Limpar mensagens"
                >
                  <Eraser className="w-4 h-4" />
                </button>
                <button
                  onClick={handleToggleHistory}
                  className={`p-2 rounded-lg transition-colors motion-reduce:transition-none ${
 showHistory
                      ? "text-wedo-cyan bg-lia-bg-tertiary"
                      : "lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover"
                  }`}
                  title="Histórico de conversas"
                  aria-label="Ver histórico de conversas"
                >
                  <History className="w-4 h-4" />
                </button>
                <div className="w-px h-5 bg-lia-interactive-active mx-1" />
                <button
                  onClick={collapse}
                  className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Minimizar para chat pequeno"
                  aria-label="Minimizar"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
                <button
                  onClick={closeAll}
                  className="p-2 rounded-lg text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
                  title="Fechar"
                  aria-label="Fechar"
                  data-dismiss="true"
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
                      <p className="text-xs font-semibold text-lia-text-secondary uppercase tracking-wide mb-3" >
                        Conversas recentes
                      </p>
                      {recentChats.length === 0 ? (
                        <p className="text-base-ui text-lia-text-secondary text-center mt-10">
                          Nenhuma conversa anterior encontrada.
                        </p>
                      ) : (
                        <div className="space-y-1 max-w-3xl mx-auto">
                          {recentChats.map(chat => (
                            <button
                              key={chat.id}
                              onClick={() => handleLoadConversation(chat.id)}
                              className="w-full flex items-start gap-3 px-4 py-3 rounded-lg hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none text-left group"
                            >
                              <Clock className="w-4 h-4 text-lia-text-secondary flex-shrink-0 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <p className="text-base-ui text-lia-text-secondary truncate group-hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                                  {chat.title}
                                </p>
                                <p className="text-xs text-lia-text-secondary mt-0.5">
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
                            <LIAIcon size="xl" className="mb-4 mx-auto" />
                            <h2
                              className="text-3xl font-semibold mb-3"
                             
                            >
                              Oi, eu sou a <span className="text-lia-text-secondary">LIA</span>.
                            </h2>
                            <p
                              className="text-base mb-2"
                             
                            >
                              Sua assistente de recrutamento inteligente. Qual das tarefas abaixo quer que eu execute para você?
                            </p>
                            {hasContextualData && (
                              <p className="text-xs text-wedo-cyan font-medium">
                                Sugestões personalizadas baseadas na sua atividade recente
                              </p>
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-2 w-full max-w-2xl">
                            {suggestions.map((suggestion) => {
                              const Icon = suggestion.icon
                              const colors = CATEGORY_COLORS[suggestion.category] || CATEGORY_COLORS.vagas
                              return (
                                <button
                                  key={suggestion.id}
                                  onClick={() => handleSuggestionClick(suggestion)}
                                  className="p-3 rounded-lg transition-colors motion-reduce:transition-none text-left group"
                                  style={{border: `1px solid ${colors.bg}`,
                                    backgroundColor: "var(--white)"}}
                                  onMouseEnter={(e) => {
                                    e.currentTarget.style.backgroundColor = colors.hoverBg
                                    e.currentTarget.style.borderColor = colors.border
                                    e.currentTarget.style.transform = "translateY(-1px)"
                                  }}
                                  onMouseLeave={(e) => {
                                    e.currentTarget.style.backgroundColor = "var(--white)"
                                    e.currentTarget.style.borderColor = colors.bg
                                    e.currentTarget.style.transform = "translateY(0)"
                                  }}
                                >
                                  <div className="flex items-start gap-2.5">
                                    <div
                                      className="p-1.5 rounded-md flex-shrink-0"
                                      style={{backgroundColor: colors.bg}}
                                    >
                                      <Icon className="w-3.5 h-3.5" style={{color: colors.icon}} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h3
                                        className="font-medium text-xs leading-tight mb-0.5"
                                       
                                      >
                                        {suggestion.title}
                                      </h3>
                                      <p
                                        className="text-xs leading-snug line-clamp-2"
                                       
                                      >
                                        {suggestion.description}
                                      </p>
                                      {suggestion.actionType === "redirect" && (
                                        <span className="inline-block mt-1 text-micro px-1.5 py-0.5 rounded-xl bg-lia-bg-tertiary text-lia-text-secondary">
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
                                  <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
                                </div>
                              </div>
                              <SuperPromptStreamingBubble content={streamingContent} />
                            </div>
                          )}

                          {liveActive && (
                            <div className="mt-1">
                              <AgentActivityTimeline
                                fallbackSteps={thinkingSteps}
                                showFallback={isThinking && !streamingContent}
                                completed={!isThinking && !isStreaming}
                                onFinished={() => setLiveActive(false)}
                              />
                            </div>
                          )}

                          <div ref={messagesEndRef} />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Input */}
                  <div className="px-6 py-4 border-t border-lia-border-subtle flex-shrink-0">
                    <div className="max-w-3xl mx-auto">
                      <div className="flex items-center gap-2 px-4 py-2.5 rounded-[24px] bg-lia-bg-primary border border-lia-border-subtle">
                        {!contextDismissed && contextPage && contextPage !== "Conversar" && (
                          <ContextBadge
                            contextPage={contextPage}
                            onRemove={() => setContextDismissed(true)}
                          />
                        )}
                        <textarea
                          ref={inputRef}
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyDown={handleKeyPress}
                          placeholder="Envie mensagem para a LIA..."
                          className="flex-1 resize-none text-base-ui focus:outline-none bg-transparent min-w-0"
                         
                          rows={1}
                        />
                        <AudioRecordButton
                          onTranscription={(text) => setInput(prev => prev ? `${prev} ${text}` : text)}
                          className="p-1.5"
                        />
                        <button
                          onClick={() => handleSendMessage()}
                          disabled={!input.trim() || isCreating || isStreaming}
                          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors motion-reduce:transition-none ${
 input.trim() && !isCreating && !isStreaming
                              ? "bg-wedo-cyan text-white hover:opacity-90"
                              : "bg-lia-interactive-active text-lia-text-secondary cursor-not-allowed"
                          }`}
                          aria-label="Enviar mensagem"
                        >
                          <Send className="w-4 h-4" />
                        </button>
                      </div>
                      <ComplianceBadge />
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
  const authUser = useAuthStore((s) => s.user)
  const userDisplayName = authUser?.name || authUser?.email || "Usuário"
  const userInitials = userDisplayName.charAt(0).toUpperCase()
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
             
            >
              <div
                className="text-base-ui leading-relaxed text-lia-text-secondary"
               
                dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
              />
            </div>
            <span className="text-xs text-lia-text-secondary px-1">
              {message.timestamp}
            </span>
          </div>
          <div className="flex-shrink-0 w-7 h-7 rounded-full bg-lia-interactive-active flex items-center justify-center mt-1 text-xs font-medium text-lia-text-secondary">
            {userInitials}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-2.5 max-w-4xl">
      <div className="flex-shrink-0 pt-1">
        <div className="w-7 h-7 rounded-full flex items-center justify-center">
          <Brain className="w-4 h-4 text-wedo-cyan" strokeWidth={2.5} />
        </div>
      </div>
      <div className="flex-1 flex flex-col gap-1">
        <div className="flex items-center gap-1.5 px-1">
          <span className="text-xs font-bold text-lia-text-primary">LIA</span>
          <span className="text-xs text-lia-text-secondary">
            {message.timestamp}
          </span>
        </div>
        <div
          className="rounded-[14px] rounded-bl-[4px] px-4 py-3 bg-lia-bg-primary border border-lia-border-subtle"
        >
          <div
            className="text-base-ui leading-relaxed text-lia-text-secondary"
           
            dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
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
        <span className="text-xs font-bold text-lia-text-primary">LIA</span>
      </div>
      <div className="rounded-[14px] rounded-bl-[4px] px-4 py-3 bg-lia-bg-primary border border-lia-border-subtle">
        <div
          className="text-base-ui leading-relaxed text-lia-text-secondary"
         
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }}
        />
        <span className="inline-block w-1.5 h-3.5 bg-wedo-cyan ml-0.5 animate-pulse motion-reduce:animate-none align-middle" />
      </div>
    </div>
  )
}
