"use client"

import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { UnifiedChat } from "./UnifiedChat"
import { UnifiedChatBubble } from "./UnifiedChatBubble"
import { useState, useCallback } from "react"
import type { ChatMode } from "./unified-chat-types"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

/**
 * UnifiedChatConditional — Global wrapper that replaces LiaFloatConditional.
 *
 * Renders the UnifiedChat in sidebar/floating mode when open,
 * or the bubble button when closed. Fullscreen mode is handled
 * by the ChatPage integration.
 */
export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, splitView } = useLiaFloat()
  const [mode, setMode] = useState<ChatMode>("sidebar")

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  // In split view, don't render the overlay chat (it's inline)
  if (splitView.active) return null

  return (
    <>
      {isOpen ? (
        <UnifiedChat
          initialMode={mode}
        />
      ) : (
        <UnifiedChatBubble onOpen={() => open()} />
      )}
    </>
  )
}
