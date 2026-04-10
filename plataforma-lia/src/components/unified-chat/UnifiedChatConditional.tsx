"use client"

import { useState, useEffect } from "react"
import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSuperPrompt } from "@/components/lia-float/LiaSuperPrompt"
import { UnifiedChatBubble } from "./UnifiedChatBubble"
import { UnifiedChat } from "./UnifiedChat"
import type { ChatMode } from "./unified-chat-types"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]
const MODE_STORAGE_KEY = "lia-chat-mode"

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, splitView, hasInlineChat } = useLiaFloat()
  const [chatMode, setChatMode] = useState<ChatMode>(getStoredMode)

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.mode) setChatMode(detail.mode)
    }
    window.addEventListener("lia:chat-mode-changed", handler)
    return () => window.removeEventListener("lia:chat-mode-changed", handler)
  }, [])

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  const showFloating = isOpen && chatMode === "floating" && !hasInlineChat

  return (
    <>
      {showFloating && (
        <UnifiedChat renderMode="overlay" initialMode="floating" />
      )}

      {!hasInlineChat && !isOpen && (
        <UnifiedChatBubble onOpen={() => open()} />
      )}

      {!splitView.active && !hasInlineChat && <LiaSuperPrompt />}
    </>
  )
}
