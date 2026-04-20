"use client"

import { useEffect, useState, useCallback } from "react"
import type { ChatMode } from "@/components/unified-chat/unified-chat-types"

// Mantém paridade com a chave usada por UnifiedChat e UnifiedChatConditional.
const MODE_STORAGE_KEY = "lia-chat-mode"

function readStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = window.localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

export interface ActiveChatPresence {
  /** Last-known chat mode (mirrors what UnifiedChat stores). */
  mode: ChatMode
  /** True while at least one chat empty state is showing its internal reels rail. */
  isShowingReels: boolean
  /** True when the chat is visible in any of its non-minimized modes. */
  isChatVisible: boolean
  /** Helper to focus / re-open the chat in its current mode (or sidebar fallback). */
  focusChat: () => void
}

/**
 * Single source of truth for the floating WorkflowRail to know what the chat is doing.
 *
 * Listens to:
 *   - `lia:chat-mode-changed` — emitted by UnifiedChat when user toggles modes.
 *   - `lia:chat-reels-visibility` — emitted by UnifiedChatEmptyState mounts/unmounts.
 *     Uses a ref-counted approach (count >= 1 => visible) to tolerate multiple
 *     concurrent empty-state mounts (e.g. sidebar + dashboard inline) without
 *     one unmount silently re-showing the global rail while another is still
 *     visible.
 *
 * Emits (via focusChat):
 *   - `lia:focus-chat` { mode } — consumed by UnifiedChatConditional to open()
 *     the chat in the given mode.
 */
export function useActiveChatPresence(): ActiveChatPresence {
  const [mode, setMode] = useState<ChatMode>("sidebar")
  const [isShowingReels, setIsShowingReels] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setMode(readStoredMode())
    // Reconstroi o estado inicial a partir do contador global (caso o
    // empty state tenha montado antes do hook).
    if (typeof window !== "undefined") {
      const w = window as unknown as { __liaChatReelsCount?: number }
      setIsShowingReels((w.__liaChatReelsCount ?? 0) > 0)
    }
  }, [])

  useEffect(() => {
    if (!mounted) return
    const onModeChanged = (e: Event) => {
      const detail = (e as CustomEvent<{ mode?: ChatMode }>).detail
      if (detail?.mode) setMode(detail.mode)
    }
    const onReelsVisibility = (e: Event) => {
      const detail = (e as CustomEvent<{ count?: number }>).detail
      const count = typeof detail?.count === "number" ? detail.count : 0
      setIsShowingReels(count > 0)
    }
    window.addEventListener("lia:chat-mode-changed", onModeChanged)
    window.addEventListener("lia:chat-reels-visibility", onReelsVisibility)
    return () => {
      window.removeEventListener("lia:chat-mode-changed", onModeChanged)
      window.removeEventListener("lia:chat-reels-visibility", onReelsVisibility)
    }
  }, [mounted])

  const focusChat = useCallback(() => {
    if (typeof window === "undefined") return
    const target: ChatMode = mode === "minimized" ? "sidebar" : mode
    // 1) Sinaliza o modo para qualquer ouvinte (estado interno em cascata).
    window.dispatchEvent(
      new CustomEvent("lia:chat-mode-changed", { detail: { mode: target } })
    )
    // 2) Pede para o conditional mount realmente abrir o chat (open() do contexto).
    window.dispatchEvent(
      new CustomEvent("lia:focus-chat", { detail: { mode: target } })
    )
  }, [mode])

  const isChatVisible = mode !== "minimized"

  return { mode, isShowingReels, isChatVisible, focusChat }
}
