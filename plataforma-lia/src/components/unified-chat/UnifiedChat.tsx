"use client"

import React, { useState, useCallback, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { useAuthStore } from "@/stores/auth-store"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { DynamicContextPanel } from "@/components/lia-float/panels"
import { SwitchTaskModal } from "@/components/lia-float/SwitchTaskModal"
import { BackgroundAgentsStatus } from "@/components/lia-float/BackgroundAgentsStatus"
import { BackgroundTaskNotification } from "@/components/lia-float/BackgroundTaskNotification"
import { FairnessWarningBanner } from "@/components/fairness-warning-banner"
import { useNavigationIntent } from "@/hooks/use-navigation-intent"
import { useCvScreening } from "@/hooks/use-cv-screening"
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
 * - Background task notifications
 * - Fairness warning banners
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
    addChatMessage,
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
    chatBackgroundTasks,
    clearBackgroundTask,
    chatFairnessWarnings,
    dismissFairnessWarnings,
  } = useLiaChatContext()

  const { detect: detectNavIntent } = useNavigationIntent()
  const { screenCv, isScreening } = useCvScreening()

  // Persist mode preference
  useEffect(() => {
    localStorage.setItem(MODE_STORAGE_KEY, mode)
  }, [mode])

  // F3: Prefill message listener
  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ message: string }>).detail
      if (detail?.message) {
        setInputText(detail.message)
      }
    }
    window.addEventListener("lia:prefill-message", handler)
    return () => window.removeEventListener("lia:prefill-message", handler)
  }, [])

  const handleSend = useCallback(async () => {
    const text = inputText.trim()
    if (!text) return

    // If file is attached, screen it via CV upload API
    if (attachedFile) {
      const result = await screenCv({
        file: attachedFile,
        onProgress: (step) => {
          addChatMessage({
            id: "progress-" + Date.now(),
            sender: "lia",
            content: step,
            timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
          })
        },
      })
      if (result.message) {
        addChatMessage({
          id: "cv-result-" + Date.now(),
          sender: "lia",
          content: result.message,
          timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
        })
      }
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
  }, [inputText, sendChatMessage, detectNavIntent, attachedFile, screenCv, addChatMessage])

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

  // F1: Map background tasks to the simpler BackgroundTask shape
  const bgTasks = chatBackgroundTasks.map(t => ({
    id: t.task_id,
    type: t.task_type,
    label: t.label,
    status: t.status,
    progress: t.progress,
    message: t.message,
    result: t.result,
  }))
  const completedTasks = bgTasks.filter(t => t.status === "completed" || t.status === "failed")
  const runningTasks = bgTasks.filter(t => t.status === "running")

  // F1: When viewing a background task result, add it as a LIA message
  const handleViewTaskResult = useCallback((task: { id: string; result?: Record<string, unknown> }) => {
    const resultContent = task.result
      ? JSON.stringify(task.result, null, 2)
      : "Resultado não disponível."
    addChatMessage({
      id: `bg-result-${task.id}-${Date.now()}`,
      sender: "lia",
      content: resultContent,
      timestamp: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    })
    clearBackgroundTask(task.id)
  }, [addChatMessage, clearBackgroundTask])

  const conversationTitle = chatMessages.find(m => m.sender === "user")?.content?.slice(0, 40) || null
  const hasMessages = chatMessages.length > 0
  const hasDynamicPanel = !!dynamicPanel

  // For overlay mode, don't render if closed (except fullscreen mode which is always visible)
  if (renderMode === "overlay" && !isOpen && mode !== "fullscreen") return null

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
      <div className="flex flex-col flex-1 min-w-0 min-h-0 overflow-hidden">
        {/* Header */}
        <UnifiedChatHeader
          mode={effectiveMode}
          onModeChange={handleModeChange}
          onClose={close}
          onNewChat={handleNewChat}
          onSwitchTask={() => setShowSwitchTask(true)}
          conversationTitle={conversationTitle}
          isConnected={chatIsConnected}
          onRename={(newTitle) => { if (chatConversationId) { fetch("/api/backend-proxy/conversations/" + chatConversationId, { method: "PATCH", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ title: newTitle }) }) } }}
          onDelete={() => { if (chatConversationId) { fetch("/api/backend-proxy/conversations/" + chatConversationId, { method: "DELETE", credentials: "include" }).then(() => { handleNewChat() }) } }}
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
            conversationId={chatConversationId}
          />
        ) : (
          <UnifiedChatEmptyState
            mode={effectiveMode}
            onSuggestionClick={handleSuggestionClick}
          />
        )}

        {/* F1: Background task completed notifications — between messages and HITL */}
        {completedTasks.length > 0 && (
          <div className="px-4 pb-2 space-y-2">
            {completedTasks.map(task => (
              <BackgroundTaskNotification
                key={task.id}
                task={task}
                onDismiss={(taskId) => clearBackgroundTask(taskId)}
                onViewResult={handleViewTaskResult}
              />
            ))}
          </div>
        )}

        {/* HITL Confirmation — inline above input (all modes) */}
        {chatHitlPending && (
          <div className="px-4 pb-2">
            <HITLConfirmCard
              action={chatHitlPending.action}
              description={chatHitlPending.description}
              onConfirm={(autoConfirm) => sendApproval(true)}
              onCancel={() => sendApproval(false)}
            />
          </div>
        )}

        {/* F2: Fairness warnings — above input */}
        {chatFairnessWarnings.length > 0 && (
          <FairnessWarningBanner
            warnings={chatFairnessWarnings}
            onDismiss={dismissFairnessWarnings}
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
          currentScope="page"
          onScopeChange={(scope) => { /* Scope toggle: page uses contextPage, universal uses all tools */ }}
        />

        {/* F1: Background agents status — after input */}
        {runningTasks.length > 0 && (
          <BackgroundAgentsStatus tasks={runningTasks} />
        )}
      </div>

      {/* Split View: DynamicContextPanel (sidebar + fullscreen) */}
      {hasDynamicPanel && (
        <div className="w-[340px] flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto">
          <DynamicContextPanel panel={dynamicPanel} />
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
