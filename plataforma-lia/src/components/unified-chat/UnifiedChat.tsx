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
import { requestRegeneration } from "@/services/lia-api/feedback-api"
import { toast } from "@/lib/toast"

import {
  FLOATING_POSITION_STORAGE_KEY,
  FLOATING_RESET_EVENT,
  BUBBLE_RESET_EVENT,
  FLOATING_WIDTH,
  FLOATING_HEIGHT,
  FLOATING_DRAG_THRESHOLD,
  ARROW_STEP,
  ARROW_STEP_LARGE,
  clampFloatingPosition,
  readPersistedFloatingPosition,
  getUserScopedKey,
  type Point,
} from "./floating-position"

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

function getStoredFloatingPositionFor(userId: string | null | undefined): Point | null {
  if (typeof window === "undefined") return null
  const viewport = { width: window.innerWidth, height: window.innerHeight }
  // Try the user-scoped key first, then migrate from the legacy unscoped key.
  const scopedKey = getUserScopedKey(FLOATING_POSITION_STORAGE_KEY, userId)
  const scoped = readPersistedFloatingPosition(window.localStorage, viewport, scopedKey)
  if (scoped) return scoped
  return readPersistedFloatingPosition(window.localStorage, viewport, FLOATING_POSITION_STORAGE_KEY)
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
  // Task #570 (review fix #2): assistant message ids the user has just
  // regenerated. We hide them from the rendered list so the thread does
  // NOT inflate by one bubble per retry. The set is in-memory only —
  // backend metadata.regenerated=true is the durable record.
  const [supersededMessageIds, setSupersededMessageIds] = useState<Set<string>>(() => new Set())
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [sidebarWidthPx, setSidebarWidthPx] = useState(getStoredWidth)
  const [isResizing, setIsResizing] = useState(false)
  const widthRef = useRef(sidebarWidthPx)
  const userId = useAuthStore(s => s.user?.id ?? null)
  const [floatingPosition, setFloatingPosition] = useState<{ x: number; y: number } | null>(
    () => getStoredFloatingPositionFor(userId),
  )
  const floatingDragRef = useRef<{ startX: number; startY: number; bx: number; by: number; moved: boolean; origin: { x: number; y: number } | null } | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Reload position when the active user changes (login/logout)
  const lastUserIdRef = useRef<string | null>(userId)
  useEffect(() => {
    if (lastUserIdRef.current === userId) return
    lastUserIdRef.current = userId
    setFloatingPosition(getStoredFloatingPositionFor(userId))
  }, [userId])

  // Persist floating position under a per-user key.
  // Always also drop the legacy unscoped key so that resets are durable
  // for users who had been migrated from the old global key.
  useEffect(() => {
    if (typeof window === "undefined") return
    const key = getUserScopedKey(FLOATING_POSITION_STORAGE_KEY, userId)
    if (floatingPosition) {
      localStorage.setItem(key, JSON.stringify(floatingPosition))
    } else {
      localStorage.removeItem(key)
    }
    localStorage.removeItem(FLOATING_POSITION_STORAGE_KEY)
  }, [floatingPosition, userId])

  // Reposition on resize
  useEffect(() => {
    const handleResize = () => {
      setFloatingPosition(prev => {
        if (!prev) return prev
        const next = clampFloatingPosition(prev)
        if (next.x === prev.x && next.y === prev.y) return prev
        return next
      })
    }
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  // Reset event listener
  useEffect(() => {
    const handleReset = () => setFloatingPosition(null)
    window.addEventListener(FLOATING_RESET_EVENT, handleReset)
    return () => window.removeEventListener(FLOATING_RESET_EVENT, handleReset)
  }, [])

  const handleHeaderPointerDown = useCallback((e: React.PointerEvent) => {
    // Ignore drag if clicking on interactive elements
    const target = e.target as HTMLElement
    if (target.closest('button, input, [role="menu"], [role="menuitem"]')) return
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    floatingDragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      bx: rect.left,
      by: rect.top,
      moved: false,
      origin: floatingPosition,
    }
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)

    const handleMove = (ev: PointerEvent) => {
      const ref = floatingDragRef.current
      if (!ref) return
      const dx = ev.clientX - ref.startX
      const dy = ev.clientY - ref.startY
      if (!ref.moved && (Math.abs(dx) > FLOATING_DRAG_THRESHOLD || Math.abs(dy) > FLOATING_DRAG_THRESHOLD)) {
        ref.moved = true
      }
      if (!ref.moved) return
      setFloatingPosition(clampFloatingPosition({ x: ref.bx + dx, y: ref.by + dy }))
    }
    const cleanup = () => {
      window.removeEventListener("pointermove", handleMove)
      window.removeEventListener("pointerup", handleUp)
      window.removeEventListener("pointercancel", handleUp)
      window.removeEventListener("keydown", handleKey)
      try {
        ;(e.currentTarget as HTMLElement)?.releasePointerCapture?.(e.pointerId)
      } catch {}
    }
    const handleUp = () => {
      floatingDragRef.current = null
      cleanup()
    }
    const handleKey = (ev: KeyboardEvent) => {
      if (ev.key !== "Escape") return
      const ref = floatingDragRef.current
      if (!ref) return
      ev.preventDefault()
      // Restore origin (may be null, meaning back to default position)
      setFloatingPosition(ref.origin)
      floatingDragRef.current = null
      cleanup()
    }
    window.addEventListener("pointermove", handleMove)
    window.addEventListener("pointerup", handleUp)
    window.addEventListener("pointercancel", handleUp)
    window.addEventListener("keydown", handleKey)
  }, [floatingPosition])

  const handleResetFloatingPosition = useCallback(() => {
    setFloatingPosition(null)
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(BUBBLE_RESET_EVENT))
    }
  }, [])

  // Keyboard arrow movement when header has focus (only floating mode)
  const handleContainerKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (mode !== "floating") return
    const target = e.target as HTMLElement
    if (target.closest('input, textarea, [contenteditable="true"]')) return
    const arrowMap: Record<string, [number, number]> = {
      ArrowUp: [0, -1],
      ArrowDown: [0, 1],
      ArrowLeft: [-1, 0],
      ArrowRight: [1, 0],
    }
    const delta = arrowMap[e.key]
    if (!delta) return
    if (!target.closest('[data-drag-handle]')) return
    e.preventDefault()
    const step = e.shiftKey ? ARROW_STEP_LARGE : ARROW_STEP
    setFloatingPosition(prev => {
      const base = prev ?? { x: window.innerWidth - FLOATING_WIDTH - 16, y: window.innerHeight - FLOATING_HEIGHT - 16 }
      return clampFloatingPosition({ x: base.x + delta[0] * step, y: base.y + delta[1] * step })
    })
  }, [mode])

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
      // BUG-18 fix: 0.85 era muito alto — frases naturais como "me leva pra vagas"
      // atingiam no máximo ~0.70 mesmo após fix do dampening no backend.
      // 0.65 captura imperativos de navegação sem falso-positivar perguntas genéricas.
      if (result?.page && result.confidence >= 0.65) {
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

  const isFloatingOverlay = !isInline && mode === "floating"
  const floatingStyle: React.CSSProperties | undefined = isFloatingOverlay && floatingPosition
    ? { left: floatingPosition.x, top: floatingPosition.y, right: "auto", bottom: "auto" }
    : undefined

  return (
    <div
      ref={containerRef}
      onKeyDown={handleContainerKeyDown}
      className={cn(
        "flex bg-lia-bg-primary relative overflow-hidden",
        isInline
          ? "flex-shrink-0 border border-lia-border-subtle rounded-xl h-full"
          : mode === "fullscreen"
            ? "fixed inset-0 z-50"
            : mode === "sidebar"
              ? "fixed top-2 right-2 bottom-2 z-40 border border-lia-border-subtle rounded-xl shadow-xl"
              : "fixed w-[360px] h-[520px] z-30 rounded-xl border border-lia-border-subtle shadow-xl",
        isFloatingOverlay && !floatingPosition && "bottom-4 right-4",
        className
      )}
      style={
        isInline
          ? { width: `${inlineWidth}px` }
          : (!isInline && mode === "sidebar")
            ? { width: `${sidebarWidthPx + dynamicPanelWidth}px` }
            : floatingStyle
      }
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
          isDraggable={isFloatingOverlay}
          onHeaderPointerDown={isFloatingOverlay ? handleHeaderPointerDown : undefined}
          onResetPosition={isFloatingOverlay ? handleResetFloatingPosition : undefined}
        />

        {/* Content area */}
        {hasMessages ? (
          <UnifiedMessageList
            mode={effectiveMode}
            // Task #570 (review fix #2): hide assistant bubbles that the
            // user superseded via Regenerate so the thread doesn't grow
            // by one extra question/answer pair on every retry. The IDs
            // are tracked in `supersededMessageIds` and unioned with the
            // also-orphaned user prompt that triggered the supersede.
            messages={chatMessages.filter((m) => !supersededMessageIds.has(m.id))}
            isStreaming={chatIsStreaming}
            streamingContent={chatStreamingContent}
            isThinking={chatIsThinking}
            thinkingSteps={chatThinkingSteps}
            userName={userName}
            conversationId={chatConversationId}
            onChipClick={(value) => sendChatMessage(value)}
            onRegenerate={async (assistantMessageId) => {
              // Task #570 (review fix): server-side regeneration handshake.
              // Backend verifies ownership, marks the old assistant row as
              // superseded, returns the prior user message text. We then
              // (a) hide the old assistant bubble locally and (b) re-invoke
              // the pipeline. Fallback to a pure client-side scan when the
              // endpoint isn't reachable or the message id isn't a UUID
              // (optimistic local-only turns).
              const supersedeLocally = () => {
                setSupersededMessageIds((prev) => {
                  const next = new Set(prev)
                  next.add(assistantMessageId)
                  return next
                })
              }

              const fallback = () => {
                const idx = chatMessages.findIndex((m) => m.id === assistantMessageId)
                if (idx <= 0) return false
                for (let i = idx - 1; i >= 0; i--) {
                  if (chatMessages[i].sender === "user") {
                    supersedeLocally()
                    sendChatMessage(chatMessages[i].content)
                    return true
                  }
                }
                return false
              }

              if (!chatConversationId) {
                fallback()
                return
              }
              try {
                const res = await requestRegeneration(chatConversationId, assistantMessageId)
                if (res?.user_message) {
                  supersedeLocally()
                  sendChatMessage(res.user_message)
                  return
                }
                fallback()
              } catch {
                if (!fallback()) {
                  toast.error("Não foi possível regenerar a resposta")
                }
              }
            }}
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
