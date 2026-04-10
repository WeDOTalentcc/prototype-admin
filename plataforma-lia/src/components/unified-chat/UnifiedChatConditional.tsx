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
  const { isOpen, open, close, splitView, hasInlineChat } = useLiaFloat()
  const [chatMode, setChatMode] = useState<ChatMode>(getStoredMode)
  const [hasDashboardShell, setHasDashboardShell] = useState(false)

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.mode) setChatMode(detail.mode)
    }
    window.addEventListener("lia:chat-mode-changed", handler)
    return () => window.removeEventListener("lia:chat-mode-changed", handler)
  }, [])

  useEffect(() => {
    const check = () => setHasDashboardShell(!!document.querySelector("[data-dashboard-shell]"))
    check()
    const raf = requestAnimationFrame(check)
    return () => cancelAnimationFrame(raf)
  }, [pathname])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "K") {
        e.preventDefault()
        if (isOpen) {
          close()
        } else {
          open()
        }
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, open, close])

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  const showFloating = isOpen && chatMode === "floating" && !hasInlineChat
  const showSidebarOverlay = isOpen && chatMode === "sidebar" && !hasInlineChat && !hasDashboardShell
  const showFullscreen = isOpen && chatMode === "fullscreen" && !hasInlineChat

  return (
    <>
      {showFloating && (
        <UnifiedChat renderMode="overlay" initialMode="floating" />
      )}

      {showSidebarOverlay && (
        <UnifiedChat renderMode="overlay" initialMode="sidebar" />
      )}

      {showFullscreen && (
        <UnifiedChat renderMode="overlay" initialMode="fullscreen" />
      )}

      {!hasInlineChat && !isOpen && (
        <UnifiedChatBubble onOpen={() => open()} />
      )}

      {!splitView.active && !hasInlineChat && <LiaSuperPrompt />}
    </>
  )
}
