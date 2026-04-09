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
  /** When "inline", renders as a flex child (no fixed positioning).
   *  When "overlay", renders with fixed positioning (floating/fullscreen). */
  renderMode?: "inline" | "overlay"
  initialMode?: ChatMode
  className?: string
}

/**
 * UnifiedChat — Single chat component with 3 visual modes (Notion AI-inspired).
 *
 * Modes:
 * - fullscreen: Full page, centered content (Chat LIA menu page)
 * - sidebar: Right panel persistent across navigation (Replit-style)
 * - floating: Overlay panel positioned over content
 *
 * renderMode="inline" is used when embedded in the dashboard flex layout.
 * renderMode="overlay" is used for floating/fullscreen fixed positioning.
 */
export function UnifiedChat({ renderMode = "overlay", initialMode, className }: Props) {
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
      close()
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page", { detail: {} }))
    }
  }, [close])

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

  // For overlay mode, don't render if closed
  if (renderMode === "overlay" && !isOpen) return null

  const isInline = renderMode === "inline"

  return (
    <div
      className={cn(
        "flex flex-col bg-lia-bg-primary",
        isInline
          ? "w-[380px] flex-shrink-0 border-l border-lia-border-subtle h-full"
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle",
        className
      )}
      data-chat-mode={mode}
      data-render-mode={renderMode}
    >
      {/* Header */}
      <UnifiedChatHeader
        mode={isInline ? "sidebar" : mode}
        onModeChange={handleModeChange}
        onClose={close}
        onNewChat={handleNewChat}
        conversationTitle={conversationTitle}
        isConnected={chatIsConnected}
      />

      {/* Content area */}
      {hasMessages ? (
        <UnifiedMessageList
          mode={isInline ? "sidebar" : mode}
          messages={chatMessages}
          isStreaming={chatIsStreaming}
          streamingContent={chatStreamingContent}
          isThinking={chatIsThinking}
          thinkingSteps={chatThinkingSteps}
          userName={userName}
        />
      ) : (
        <UnifiedChatEmptyState
          mode={isInline ? "sidebar" : mode}
          onSuggestionClick={handleSuggestionClick}
        />
      )}

      {/* Input */}
      <UnifiedChatInput
        mode={isInline ? "sidebar" : mode}
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
