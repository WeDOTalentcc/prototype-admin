"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { UnifiedChatHeader } from "./UnifiedChatHeader"
import { UnifiedChatInput } from "./UnifiedChatInput"
import { UnifiedChatEmptyState } from "./UnifiedChatEmptyState"
import { UnifiedMessageList } from "./UnifiedMessageList"
import type { ChatMode } from "./unified-chat-types"

const MODE_STORAGE_KEY = "lia-chat-mode"

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

interface Props {
  initialMode?: ChatMode
  className?: string
}

/**
 * UnifiedChat — Single chat component with 3 visual modes (Notion AI-inspired).
 *
 * Modes:
 * - fullscreen: Full page, centered content (like Chat LIA menu page)
 * - sidebar: Fixed right panel persistent across navigation
 * - floating: Overlay panel positioned over content
 *
 * Connects to existing LiaFloatContext for WebSocket, messages, and state.
 */
export function UnifiedChat({ initialMode, className }: Props) {
  const [mode, setMode] = useState<ChatMode>(initialMode ?? getStoredMode())
  const [inputText, setInputText] = useState("")
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const authUser = useAuthStore((s) => s.user)
  const userName = authUser?.name || authUser?.email || "Usuário"

  const {
    isOpen,
    close,
    contextPage,
  } = useLiaFloat()

  const {
    chatMessages,
    setChatMessages,
    chatConversationId,
    setChatConversationId,
    switchChatContext,
    sendChatMessage,
    chatIsConnected,
    chatIsStreaming,
    chatStreamingContent,
    chatIsCreating,
    chatIsThinking,
    chatThinkingSteps,
    chatHitlPending,
  } = useLiaChatContext()

  // Persist mode preference
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, mode)
  }, [mode])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text) return
    sendChatMessage(text)
    setInputText("")
    setAttachedFile(null)
  }, [inputText, sendChatMessage])

  const handleSuggestionClick = useCallback((prompt: string) => {
    setInputText(prompt)
    // Auto-send after small delay for UX feel
    setTimeout(() => {
      sendChatMessage(prompt)
      setInputText("")
    }, 100)
  }, [sendChatMessage])

  const handleNewChat = useCallback(() => {
    switchChatContext("general", { conversationId: null })
    setChatMessages([])
    setInputText("")
    setAttachedFile(null)
  }, [switchChatContext, setChatMessages])

  const handleModeChange = useCallback((newMode: ChatMode) => {
    setMode(newMode)
    if (newMode === "fullscreen") {
      // Navigate to fullscreen chat page
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page", { detail: {} }))
    }
  }, [])

  const handleFileButtonClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileAttach = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.size <= 10 * 1024 * 1024) {
      setAttachedFile(file)
    }
    if (e.target) e.target.value = ""
  }, [])

  // Derive conversation title from first user message
  const conversationTitle = chatMessages.find(m => m.sender === "user")?.content?.slice(0, 40) || null

  const hasMessages = chatMessages.length > 0

  // Don't render if closed (sidebar/floating modes)
  if (mode !== "fullscreen" && !isOpen) return null

  return (
    <div
      className={cn(
        "flex flex-col bg-lia-bg-primary",
        // Mode-specific layouts
        mode === "fullscreen" && "fixed inset-0 z-50",
        mode === "sidebar" && "fixed top-0 right-0 bottom-0 w-[380px] z-30 border-l border-lia-border-subtle",
        mode === "floating" && "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle",
        className
      )}
      data-chat-mode={mode}
    >
      {/* Header */}
      <UnifiedChatHeader
        mode={mode}
        onModeChange={handleModeChange}
        onClose={close}
        onNewChat={handleNewChat}
        conversationTitle={conversationTitle}
        isConnected={chatIsConnected}
      />

      {/* Content area */}
      {hasMessages ? (
        <UnifiedMessageList
          mode={mode}
          messages={chatMessages}
          isStreaming={chatIsStreaming}
          streamingContent={chatStreamingContent}
          isThinking={chatIsThinking}
          thinkingSteps={chatThinkingSteps}
          userName={userName}
        />
      ) : (
        <UnifiedChatEmptyState
          mode={mode}
          onSuggestionClick={handleSuggestionClick}
        />
      )}

      {/* Input */}
      <UnifiedChatInput
        mode={mode}
        inputText={inputText}
        setInputText={setInputText}
        onSend={handleSend}
        isStreaming={chatIsStreaming}
        isCreating={chatIsCreating}
        isDisabled={!!chatHitlPending}
        contextPage={contextPage}
        attachedFile={attachedFile}
        setAttachedFile={setAttachedFile}
        fileInputRef={fileInputRef}
        onFileButtonClick={handleFileButtonClick}
        onFileAttach={handleFileAttach}
      />
    </div>
  )
}
