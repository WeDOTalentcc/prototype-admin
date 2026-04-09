"use client"

import React, { useEffect } from "react"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { UnifiedChat } from "./UnifiedChat"

/**
 * DashboardChatPanel — Renders UnifiedChat inline in the dashboard flex layout.
 *
 * This component sits inside the dashboard-app.tsx content area as a flex child,
 * causing the main content to shrink when the chat opens (Replit-style).
 *
 * - When open: renders UnifiedChat with renderMode="inline" (flex child, 380px)
 * - When closed: returns null (bubble is rendered by UnifiedChatConditional)
 * - When ChatPage is active (hasInlineChat=true): hides completely
 */
export function DashboardChatPanel() {
  const { isOpen, open, close, hasInlineChat } = useLiaFloat()

  // Keyboard shortcut: ⌘⇧K to toggle chat
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

  // Hide when ChatPage is active or chat is closed
  if (hasInlineChat || !isOpen) return null

  return (
    <UnifiedChat renderMode="inline" />
  )
}
