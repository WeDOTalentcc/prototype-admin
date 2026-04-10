"use client"

import React, { useEffect, useState } from "react"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { UnifiedChat } from "./UnifiedChat"
import type { ChatMode } from "./unified-chat-types"

const MODE_STORAGE_KEY = "lia-chat-mode"

function getStoredMode(): ChatMode {
  if (typeof window === "undefined") return "sidebar"
  const stored = localStorage.getItem(MODE_STORAGE_KEY)
  if (stored === "sidebar" || stored === "floating" || stored === "fullscreen") return stored
  return "sidebar"
}

export function DashboardChatPanel() {
  const { isOpen, open, close, hasInlineChat } = useLiaFloat()
  const [chatMode, setChatMode] = useState<ChatMode>(getStoredMode)

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.mode) setChatMode(detail.mode)
    }
    window.addEventListener("lia:chat-mode-changed", handler)
    return () => window.removeEventListener("lia:chat-mode-changed", handler)
  }, [])

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

  if (hasInlineChat || !isOpen || chatMode === "floating" || chatMode === "fullscreen") return null

  return (
    <UnifiedChat renderMode="inline" />
  )
}
