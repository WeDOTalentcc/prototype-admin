"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { useTranslations } from "next-intl"
import { cn } from "@/lib/utils"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { DynamicContextPanel } from "./wizard/DynamicContextPanel"
import type { WizardStage } from "./wizard/wizard-types"
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal"
import { useNavigationIntent } from "@/hooks/shared/use-navigation-intent"
import { useWizardIntegration } from "./wizard/useWizardIntegration"
import { ProgressiveDisclosure } from "./wizard/ProgressiveDisclosure"
import { UnifiedChatHeader } from "./UnifiedChatHeader"
import { UnifiedChatInput } from "./UnifiedChatInput"
import { UnifiedChatEmptyState } from "./UnifiedChatEmptyState"
import { UnifiedMessageList } from "./UnifiedMessageList"
import type { ChatMode } from "./unified-chat-types"

const MODE_STORAGE_KEY = "lia-chat-mode"
const WIDTH_STORAGE_KEY = "lia-chat-width"
const DEFAULT_WIDTH = 380
const MIN_WIDTH = 300
const MAX_WIDTH = 600

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

function getStoredWidth(): number {
  if (typeof window === "undefined") return DEFAULT_WIDTH
  const stored = localStorage.getItem(WIDTH_STORAGE_KEY)
  if (stored) {
    const n = parseInt(stored, 10)
    if (!isNaN(n) && n >= MIN_WIDTH && n <= MAX_WIDTH) return n
  }
  return DEFAULT_WIDTH
}

interface Props {
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
  const [sidebarWidthPx, setSidebarWidthPx] = useState(getStoredWidth)
  const [isResizing, setIsResizing] = useState(false)
  const widthRef = useRef(sidebarWidthPx)

  useEffect(() => {
    if (!isResizing) return
    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, window.innerWidth - e.clientX))
      widthRef.current = newWidth
      setSidebarWidthPx(newWidth)
    }
    const handleMouseUp = () => {
      setIsResizing(false)
      localStorage.setItem(WIDTH_STORAGE_KEY, String(widthRef.current))
    }
    document.body.style.cursor = "ew-resize"
    document.body.style.userSelect = "none"
    document.addEventListener("mousemove", handleMouseMove)
    document.addEventListener("mouseup", handleMouseUp)
    return () => {
      document.body.style.cursor = ""
      document.body.style.userSelect = ""
      document.removeEventListener("mousemove", handleMouseMove)
      document.removeEventListener("mouseup", handleMouseUp)
    }
  }, [isResizing])

  const authUser = useAuthStore((s) => s.user)
  const tc = useTranslations('common')
  const userName = authUser?.name || authUser?.email || tc('defaultUserName')

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
    chatContextType,
    switchChatContext,
    sendChatMessage,
    sendApproval,
    loadChatHistory,
    chatIsConnected,
    chatTransportMode,
    chatIsReconnecting,
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

    detectNavIntent(text).then((result) => {
      if (result?.page && result.confidence >= 0.85) {
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
    if (newMode === "minimized") {
      close()
      window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: "minimized", prevMode } }))
      return
    }
    setMode(newMode)
    localStorage.setItem(MODE_STORAGE_KEY, newMode)
    window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: newMode, prevMode } }))
    if (newMode === "fullscreen") {
      close()
      window.dispatchEvent(new CustomEvent("lia:navigate-chat-page", { detail: {} }))
    } else if (newMode === "floating") {
      open()
    } else if (newMode === "sidebar") {
      open()
      if (prevMode === "fullscreen") {
        window.dispatchEvent(new CustomEvent("lia:leave-fullscreen-chat", { detail: { targetMode: newMode } }))
      }
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

  if (renderMode === "overlay" && !isOpen && mode !== "fullscreen") return null

  const isInline = renderMode === "inline"
  const effectiveMode: ChatMode = isInline ? "sidebar" : mode

  const dynamicPanelWidth = hasDynamicPanel ? 340 : 0
  const inlineWidth = isInline ? sidebarWidthPx + dynamicPanelWidth : undefined

  return (
    <div
      className={cn(
        "flex bg-lia-bg-primary relative overflow-hidden",
        isInline
          ? "flex-shrink-0 border border-lia-border-subtle rounded-xl h-full"
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : mode === "sidebar"
              ? "fixed top-2 right-2 bottom-2 z-40 border border-lia-border-subtle rounded-xl shadow-xl"
              : "fixed bottom-4 right-4 w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle shadow-xl",
        className
      )}
      style={isInline ? { width: `${inlineWidth}px` } : (!isInline && mode === "sidebar") ? { width: `${sidebarWidthPx + dynamicPanelWidth}px` } : undefined}
      data-chat-mode={effectiveMode}
      data-render-mode={renderMode}
    >
      {(isInline || (!isInline && mode === "sidebar")) && (
        <div
          className="absolute left-0 top-0 w-1.5 h-full cursor-ew-resize z-10 group hover:bg-wedo-cyan/20 active:bg-wedo-cyan/30 transition-colors"
          onMouseDown={(e) => {
            e.preventDefault()
            setIsResizing(true)
          }}
        >
          <div className="absolute left-0.5 top-1/2 -translate-y-1/2 w-0.5 h-8 rounded-full bg-lia-border-subtle group-hover:bg-wedo-cyan transition-colors" />
        </div>
      )}
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
          transportMode={chatTransportMode}
          isReconnecting={chatIsReconnecting}
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
            contextType={chatContextType}
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
            currentStage={(dynamicPanel?.stage as WizardStage) ?? null}
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
            stage={(dynamicPanel?.stage as WizardStage) ?? null}
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
