"use client"

import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSuperPrompt } from "@/components/lia-float/LiaSuperPrompt"
import { UnifiedChatBubble } from "./UnifiedChatBubble"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

/**
 * UnifiedChatConditional — Global wrapper in layout.tsx.
 *
 * Responsibilities:
 * - Render bubble button when chat is closed (single source of truth)
 * - Render LiaSuperPrompt outside split view
 * - Hide on auth pages
 *
 * The inline sidebar is rendered by DashboardChatPanel in dashboard-app.
 * The bubble is always rendered here (fixed position, outside flex layout).
 */
export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, splitView, hasInlineChat } = useLiaFloat()

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  return (
    <>
      {/* Bubble: single source — show when chat closed and not on ChatPage */}
      {!hasInlineChat && !isOpen && (
        <UnifiedChatBubble onOpen={() => open()} />
      )}

      {/* LiaSuperPrompt: preserved from original */}
      {!splitView.active && <LiaSuperPrompt />}
    </>
  )
}
