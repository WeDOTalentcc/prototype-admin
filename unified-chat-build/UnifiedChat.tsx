"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { DynamicContextPanel } from "./wizard/DynamicContextPanel"
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useWizardIntegration } from "./wizard/useWizardIntegration"
import { ProgressiveDisclosure } from "./wizard/ProgressiveDisclosure"
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
  /** "inline" = flex child in dashboard, "overlay" = fixed position */
  renderMode?: "inline" | "overlay"
  initialMode?: ChatMode
  className?: string
}

/**
 * UnifiedChat — Single chat component with 3 visual modes (Notion AI-inspired).
 *
 * Includes:
 * - HITL confirmation cards (all modes)
 * - DynamicContextPanel split view (sidebar expands, fullscreen adds panel)
 * - Auto-scroll, streaming, thinking indicators
 */
export function UnifiedChat({ renderMode = "overlay", initialMode, className }: Props) {
  const [mode, setMode] = useState<ChatMode>(initialMode ?? getStoredMode())
  const [inputText, setInputText] = useState("")
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [showSwitchTask, setShowSwitchTask] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const authUser = useAuthStore((s) => s.user)
  const userName = authUser?.name || authUser?.email || "Usuário"

  const {
    isOpen,
    open,
    close,
    contextPage,
    dynamicPanel,
    closeDynamicPanel,
  } = useLiaFloat()

  const {
    chatMessages,
    setChatMessages,
    chatConversationId,
    setChatConversationId,
    switchChatContext,
    sendChatMessage,
    sendApproval,
    loadChatHistory,
    chatIsConnected,
    chatIsStreaming,
    chatStreamingContent,
    chatIsCreating,
    chatIsThinking,
    chatThinkingSteps,
    chatHitlPending,
  } = useLiaChatContext()

  const { detect: detectNavIntent } = useNavigationIntent()

  // Wire wizard integration (file→wizard, question events, slash commands)
  const { handleSlashCommand } = useWizardIntegration({
    isWizardActive: !!dynamicPanel,
    currentStage: dynamicPanel?.stage ?? null,
    sendMessage: sendChatMessage,
  })

  // Persist mode preference
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, mode)
  }, [mode])

  const handleSend = useCallback(() => {
    const text = inputText.trim()
    if (!text) return
    // Intercept slash commands before sending to backend
    if (text.startsWith("/") && handleSlashCommand(text)) {
      setInputText("")
      return
    }
    sendChatMessage(text)
    setInputText("")
    setAttachedFile(null)

    // Detect navigation intent and auto-navigate if confident
    detectNavIntent(text).then((result) => {
      if (result?.page) {
        // Dispatch navigation event for dashboard-app to handle
        window.dispatchEvent(new CustomEvent("lia:navigation-hint", {
          detail: { page: result.page, hint: result.hint },
        }))
      }
    })
  }, [inputText, sendChatMessage, detectNavIntent, handleSlashCommand])

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

  // Switch to a different conversation
  const handleSelectSession = useCallback(async (sessionId: string) => {
    setChatConversationId(sessionId)
    await loadChatHistory(sessionId)
    setShowSwitchTask(false)
  }, [setChatConversationId, loadChatHistory])

  const currentModeRef = useRef(mode)
  currentModeRef.current = mode

  const handleModeChange = useCallback((newMode: ChatMode) => {
    const prevMode = currentModeRef.current
    setMode(newMode)
    if (newMode === "fullscreen") {
      close()
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page", { detail: {} }))
    } else if (prevMode === "fullscreen") {
      open()
      window.dispatchEvent(new CustomEvent("lia:leave-fullscreen-chat", { detail: { targetMode: newMode } }))
    }
  }, [close, open])

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

  const conversationTitle = chatMessages.find(m => m.sender === "user")?.content?.slice(0, 40) || null
  const hasMessages = chatMessages.length > 0
  const hasDynamicPanel = !!dynamicPanel

  // For overlay mode, don't render if closed
  if (renderMode === "overlay" && !isOpen) return null

  const isInline = renderMode === "inline"
  const effectiveMode: ChatMode = isInline ? "sidebar" : mode

  // Sidebar width: wider when split view is active
  const sidebarWidth = isInline
    ? hasDynamicPanel ? "w-[720px]" : "w-[380px]"
    : ""

  return (
    <div
      className={cn(
        "flex bg-lia-bg-primary transition-[width] duration-200 ease-in-out motion-reduce:transition-none",
        isInline
          ? `${sidebarWidth} flex-shrink-0 border-l border-lia-border-subtle h-full`
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle",
        className
      )}
      data-chat-mode={effectiveMode}
      data-render-mode={renderMode}
    >
      {/* Chat column */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <UnifiedChatHeader
          mode={effectiveMode}
          onModeChange={handleModeChange}
          onClose={close}
          onNewChat={handleNewChat}
          onSwitchTask={() => setShowSwitchTask(true)}
          conversationTitle={conversationTitle}
          isConnected={chatIsConnected}
        />

        {/* Content area */}
        {hasMessages ? (
          <UnifiedMessageList
            mode={effectiveMode}
            messages={chatMessages}
            isStreaming={chatIsStreaming}
            streamingContent={chatStreamingContent}
            isThinking={chatIsThinking}
            thinkingSteps={chatThinkingSteps}
            userName={userName}
          />
        ) : (
          <UnifiedChatEmptyState
            mode={effectiveMode}
            onSuggestionClick={handleSuggestionClick}
          />
        )}

        {/* HITL Confirmation — inline above input (all modes) */}
        {chatHitlPending && (
          <div className="px-4 pb-2">
            <HITLConfirmCard
              action={chatHitlPending.action}
              description={chatHitlPending.description}
              onConfirm={() => sendApproval(true)}
              onCancel={() => sendApproval(false)}
            />
          </div>
        )}

        {/* Progressive disclosure tips (wizard active) */}
        {hasDynamicPanel && (
          <ProgressiveDisclosure
            currentStage={dynamicPanel?.stage ?? null}
            interactionCount={chatMessages.filter(m => m.sender === "user").length}
          />
        )}

        {/* Input */}
        <UnifiedChatInput
          mode={effectiveMode}
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

      {/* Split View: DynamicContextPanel (sidebar + fullscreen) */}
      {hasDynamicPanel && (
        <div className="w-[340px] flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto">
          <DynamicContextPanel
            stage={dynamicPanel?.stage ?? null}
            data={dynamicPanel?.data ?? {}}
            requiresApproval={dynamicPanel?.requires_approval ?? false}
            onApprove={() => sendApproval(true)}
            onReject={() => sendApproval(false)}
            onClose={closeDynamicPanel}
            onUpdate={(updates) => sendChatMessage(JSON.stringify({ type: "wizard_update", updates }))}
          />
        </div>
      )}

      {/* Switch Task Modal (⌘K) */}
      <SwitchTaskModal
        isOpen={showSwitchTask}
        onClose={() => setShowSwitchTask(false)}
        onSelectSession={handleSelectSession}
        currentSessionId={chatConversationId}
      />
    </div>
  )
}
