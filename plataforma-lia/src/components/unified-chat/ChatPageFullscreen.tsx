"use client"

import React, { useEffect, useLayoutEffect } from "react"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { UnifiedChat } from "./UnifiedChat"

interface Props {
  initialConversationId?: string | null
}

/**
 * ChatPageFullscreen — Wraps UnifiedChat in fullscreen mode for the Chat LIA menu page.
 *
 * Responsibilities:
 * - Set hasInlineChat flag (prevents sidebar from showing)
 * - Load initial conversation if provided
 * - HITL and DynamicPanel are handled inside UnifiedChat directly
 */
export function ChatPageFullscreen({ initialConversationId }: Props) {
  const { setHasInlineChat } = useLiaFloat()
  const { setChatConversationId, loadChatHistory } = useLiaChatContext()

  // Signal that this page has its own chat (hide sidebar + bubble before paint)
  useLayoutEffect(() => {
    setHasInlineChat(true)
    return () => { setHasInlineChat(false) }
  }, [setHasInlineChat])

  // Load initial conversation if provided
  useEffect(() => {
    if (initialConversationId) {
      setChatConversationId(initialConversationId)
      loadChatHistory(initialConversationId)
    }
  }, [initialConversationId, setChatConversationId, loadChatHistory])

  return (
    <UnifiedChat
      renderMode="overlay"
      initialMode="fullscreen"
      className="relative inset-auto z-auto h-full overflow-hidden"
    />
  )
}
