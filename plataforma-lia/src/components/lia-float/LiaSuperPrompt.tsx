"use client"

import { useState, useRef, useCallback, useEffect, useMemo } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  X, Minimize2, Send, Search, Brain,
  Mic, Paperclip, MessageSquare, LayoutDashboard
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
import { useRouter } from "next/navigation"

const CATEGORY_COLORS: Record<string, { icon: string; bg: string; border: string; hoverBg: string }> = {
  vagas: { icon: '#374151', bg: '#F3F4F6', border: '#D1D5DB', hoverBg: '#D0EFF5' },
  candidatos: { icon: '#5DA47A', bg: '#E5F5EB', border: '#5DA47A', hoverBg: '#D5EFE0' },
  entrevistas: { icon: '#E5A853', bg: '#FDF4E8', border: '#E5A853', hoverBg: '#FAECD8' },
  relatorios: { icon: '#8B5CF6', bg: '#F3EAFF', border: '#8B5CF6', hoverBg: '#EBE0FF' }
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

  return (
    <AnimatePresence>
      {isExpanded && (
        <motion.div
          className="fixed inset-0 z-[60] flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={collapse}
            aria-hidden="true"
          />

          <motion.div
            className="relative flex flex-col overflow-hidden rounded-2xl border shadow-2xl"
            style={{
              width: "95vw",
              height: "95vh",
              maxWidth: "1400px",
              maxHeight: "900px",
              backgroundColor: "#FFFFFF",
              borderColor: "#E5E7EB"
            }}
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
          >
            <div
              className="flex items-center justify-between px-6 py-4 border-b"
              style={{ borderColor: "#E5E7EB", backgroundColor: "#FAFBFC" }}
            >
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                  <span
                    className="text-lg font-semibold"
                    style={{ color: "#1F2937", fontFamily: '"Open Sans", sans-serif' }}
                  >
                    LIA
                  </span>
                  {conversationId && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
                      {conversationId.slice(0, 8)}
                    </span>
                  )}
                </div>

                <div className="flex rounded-lg overflow-hidden border" style={{ borderColor: "#E5E7EB" }}>
                  <button
                    onClick={() => setActiveTab("conversa")}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors"
                    style={{
                      backgroundColor: activeTab === "conversa" ? "#F0FDFF" : "transparent",
                      color: activeTab === "conversa" ? "#0891B2" : "#6B7280",
                      borderRight: "1px solid #E5E7EB"
                    }}
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    Conversa
                  </button>
                  <button
                    onClick={() => setActiveTab("controle")}
                    className="flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium transition-colors"
                    style={{
                      backgroundColor: activeTab === "controle" ? "#F0FDFF" : "transparent",
                      color: activeTab === "controle" ? "#0891B2" : "#6B7280"
                    }}
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    Centro de Controle
                  </button>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={collapse}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  title="Minimizar para chat pequeno"
                  aria-label="Minimizar"
                >
                  <Minimize2 className="w-4 h-4 text-gray-500" />
                </button>
                <button
                  onClick={closeAll}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
                  title="Fechar"
                  aria-label="Fechar"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-hidden flex flex-col">
              {activeTab === "conversa" && (
                <div className="flex-1 flex flex-col overflow-hidden">
                  <div className="flex-1 overflow-y-auto px-6 py-4">
                    {isEmptyChat ? (
                      <div className="flex flex-col items-center justify-center h-full max-w-3xl mx-auto">
                        <div className="text-center mb-8">
                          <LIAIcon size="xl" className="mb-4 mx-auto" />
                          <h2
                            className="text-3xl font-semibold mb-3"
                            style={{ color: "#1F2937" }}
                          >
                            Oi, eu sou a <span className="text-gray-700">LIA</span>.
                          </h2>
                          <p
                            className="text-base mb-2"
                            style={{ color: "#6B7280" }}
                          >
                            Sua assistente de recrutamento inteligente. Qual das tarefas abaixo quer que eu execute para você?
                          </p>
                          {hasContextualData && (
                            <p className="text-xs text-wedo-cyan font-medium">
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
                                className="p-4 rounded-lg transition-all text-left group"
                                style={{
                                  border: `1px solid ${colors.bg}`,
                                  backgroundColor: "#FFFFFF"
                                }}
                                onMouseEnter={(e) => {
                                  e.currentTarget.style.backgroundColor = colors.hoverBg
                                  e.currentTarget.style.borderColor = colors.border
                                  e.currentTarget.style.transform = "translateY(-2px)"
                                }}
                                onMouseLeave={(e) => {
                                  e.currentTarget.style.backgroundColor = "#FFFFFF"
                                  e.currentTarget.style.borderColor = colors.bg
                                  e.currentTarget.style.transform = "translateY(0)"
                                }}
                              >
                                <div className="flex items-start gap-3">
                                  <div
                                    className="p-2 rounded-md flex-shrink-0"
                                    style={{ backgroundColor: colors.bg }}
                                  >
                                    <Icon className="w-4 h-4" style={{ color: colors.icon }} />
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <h3
                                      className="font-semibold text-sm leading-tight mb-1"
                                      style={{ color: "#2D2D2D", fontFamily: '"Open Sans", sans-serif' }}
                                    >
                                      {suggestion.title}
                                    </h3>
                                    <p
                                      className="text-xs leading-snug line-clamp-2"
                                      style={{ color: "#555555", fontFamily: '"Open Sans", sans-serif' }}
                                    >
                                      {suggestion.description}
                                    </p>
                                    {suggestion.actionType === "redirect" && (
                                      <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
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
                          <div
                            key={message.id}
                            className="flex justify-start"
                          >
                            <div className={`flex ${
                              message.sender === "lia"
                                ? "items-start gap-2 max-w-4xl"
                                : "items-start gap-3 max-w-3xl ml-16"
                            }`}>
                              {message.sender === "lia" && (
                                <div className="flex-shrink-0 pt-3">
                                  <LIAIcon size="md" />
                                </div>
                              )}
                              <SuperPromptBubble message={message} />
                            </div>
                          </div>
                        ))}

                        {isStreaming && streamingContent && (
                          <div className="flex items-start gap-2">
                            <div className="flex-shrink-0 pt-3">
                              <LIAIcon size="md" />
                            </div>
                            <SuperPromptStreamingBubble content={streamingContent} />
                          </div>
                        )}

                        {isStreaming && !streamingContent && (
                          <div className="flex items-start gap-2">
                            <div className="flex-shrink-0 pt-3">
                              <LIAIcon size="md" />
                            </div>
                            <div
                              className="rounded-lg p-4"
                              style={{ backgroundColor: "#F0FDFF" }}
                            >
                              <div className="flex items-center gap-1.5">
                                <div className="w-2 h-2 rounded-full bg-wedo-cyan animate-bounce" style={{ animationDelay: "0ms" }} />
                                <div className="w-2 h-2 rounded-full bg-wedo-cyan animate-bounce" style={{ animationDelay: "150ms" }} />
                                <div className="w-2 h-2 rounded-full bg-wedo-cyan animate-bounce" style={{ animationDelay: "300ms" }} />
                              </div>
                            </div>
                          </div>
                        )}

                        <div ref={messagesEndRef} />
                      </div>
                    )}
                  </div>

                  <div className="px-6 py-4 border-t" style={{ borderColor: "#E5E7EB", backgroundColor: "#FAFBFC" }}>
                    <div className="max-w-3xl mx-auto">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 relative">
                          <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyPress}
                            placeholder="Digite sua mensagem para a LIA..."
                            className="w-full resize-none rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-cyan-500/30 border"
                            style={{
                              backgroundColor: "#FFFFFF",
                              color: "#1F2937",
                              borderColor: "#E5E7EB"
                            }}
                            rows={1}
                          />
                        </div>

                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-gray-600"
                            title="Busca avançada"
                          >
                            <Search className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-gray-600"
                            title="Anexar arquivo"
                          >
                            <Paperclip className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-gray-400 hover:text-gray-600"
                            title="Gravar áudio"
                          >
                            <Mic className="w-4 h-4" />
                          </Button>
                          <Button
                            onClick={() => handleSendMessage()}
                            disabled={!input.trim() || isCreating || isStreaming}
                            size="sm"
                            className="bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-40"
                          >
                            <Send className="w-4 h-4" />
                          </Button>
                        </div>
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
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

function SuperPromptBubble({ message }: { message: { sender: string; content: string; timestamp: string } }) {
  const isUser = message.sender === "user"
  const html = useMemo(() => {
    if (isUser) return escapeHtml(message.content).replace(/\n/g, "<br/>")
    const cleaned = cleanAgentResponse(message.content)
    return parseChatMarkdown(cleaned)
  }, [message.content, isUser])

  return (
    <div
      className="rounded-lg p-4 flex-1"
      style={{
        backgroundColor: isUser ? "#F3F4F6" : "#F0FDFF",
        color: "#1F2937",
        borderWidth: 1,
        borderColor: isUser ? "#E5E7EB" : "#D0EFF5",
      }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm font-medium" style={{ fontFamily: '"Inter", sans-serif' }}>
          {isUser ? "Voce" : "Lia"}
        </span>
        <span className="text-xs text-gray-400" style={{ fontFamily: '"Inter", sans-serif' }}>
          {message.timestamp}
        </span>
      </div>
      <div
        className="text-[13px] leading-relaxed"
        style={{ fontFamily: '"Open Sans", sans-serif' }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  )
}

function SuperPromptStreamingBubble({ content }: { content: string }) {
  const cleaned = useMemo(() => cleanAgentResponse(content), [content])
  const html = useMemo(() => parseChatMarkdown(cleaned), [cleaned])

  return (
    <div
      className="rounded-lg p-4 flex-1"
      style={{ backgroundColor: "#F0FDFF", color: "#1F2937", borderWidth: 1, borderColor: "#D0EFF5" }}
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm font-medium" style={{ fontFamily: '"Inter", sans-serif' }}>Lia</span>
      </div>
      <div
        className="text-[13px] leading-relaxed"
        style={{ fontFamily: '"Open Sans", sans-serif' }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
      <span className="inline-block w-1.5 h-3.5 bg-wedo-cyan ml-0.5 animate-pulse align-middle" />
    </div>
  )
}
