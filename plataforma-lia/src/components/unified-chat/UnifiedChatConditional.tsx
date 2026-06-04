"use client"

import { useState, useEffect } from "react"
import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSuperPrompt } from "@/components/lia-float/LiaSuperPrompt"
import { UnifiedChatBubble } from "./UnifiedChatBubble"
import { UnifiedChat } from "./UnifiedChat"
import type { ChatMode } from "./unified-chat-types"

import { isAuthRoute } from "@/lib/auth-routes"
import { getPersisted } from "@/lib/lia-persistence"

export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, close, splitView, hasInlineChat } = useLiaFloat()
  const [chatMode, setChatMode] = useState<ChatMode>(() => {
    if (typeof window === "undefined") return "sidebar"
    const stored = getPersisted<string>("lia-chat-mode", "sidebar")
    if (stored === "floating") return "floating"
    return "sidebar"
  })
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
          setChatMode("sidebar")
          window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: "sidebar" } }))
          open()
        }
      }
    }
    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, open, close])

  if (isAuthRoute(pathname ?? "")) return null

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
        <UnifiedChatBubble onOpen={() => {
          setChatMode("sidebar")
          window.dispatchEvent(new CustomEvent("lia:chat-mode-changed", { detail: { mode: "sidebar" } }))
          open()
        }} />
      )}

      {!splitView.active && !hasInlineChat && <LiaSuperPrompt />}
    </>
  )
}
