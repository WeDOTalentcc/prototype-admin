"use client"

import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSuperPrompt } from "@/components/lia-float/LiaSuperPrompt"
import { UnifiedChat } from "./UnifiedChat"
import { UnifiedChatBubble } from "./UnifiedChatBubble"
import { useState } from "react"
import type { ChatMode } from "./unified-chat-types"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

/**
 * UnifiedChatConditional — Global wrapper that replaces LiaFloatConditional.
 *
 * Renders the UnifiedChat in sidebar/floating mode when open,
 * or the bubble button when closed. Fullscreen mode is handled
 * by the ChatPage integration.
 *
 * Preserves:
 * - hasInlineChat check (hide when ChatPage is active)
 * - LiaSuperPrompt rendering (outside split view)
 * - HIDDEN_PATHS exclusion (login, etc.)
 */
export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, splitView, hasInlineChat } = useLiaFloat()
  const [mode] = useState<ChatMode>("sidebar")

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  return (
    <>
      {/* UnifiedChat: only when no inline chat (ChatPage sets hasInlineChat=true) */}
      {!hasInlineChat && (
        isOpen ? (
          <UnifiedChat initialMode={mode} />
        ) : (
          <UnifiedChatBubble onOpen={() => open()} />
        )
      )}

      {/* LiaSuperPrompt: preserved from original LiaFloatConditional */}
      {!splitView.active && <LiaSuperPrompt />}
    </>
  )
}
