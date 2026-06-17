"use client"

import React, { useEffect, useState } from "react"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { UnifiedChat } from "./UnifiedChat"
import type { ChatMode } from "./unified-chat-types"
import { getPersisted } from "@/lib/lia-persistence"

export function DashboardChatPanel() {
  const { isOpen, hasInlineChat } = useLiaFloat()
  const [chatMode, setChatMode] = useState<ChatMode>(() => {
    if (typeof window === "undefined") return "sidebar"
    const stored = getPersisted<string>("lia-chat-mode", "sidebar")
    if (stored === "floating") return "floating"
    return "sidebar"
  })


  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent).detail
      if (detail?.mode) setChatMode(detail.mode)
    }
    window.addEventListener("lia:chat-mode-changed", handler)
    return () => window.removeEventListener("lia:chat-mode-changed", handler)
  }, [])

  if (hasInlineChat || !isOpen || chatMode === "floating" || chatMode === "fullscreen") return null

  return (
    <UnifiedChat renderMode="inline" />
  )
}
