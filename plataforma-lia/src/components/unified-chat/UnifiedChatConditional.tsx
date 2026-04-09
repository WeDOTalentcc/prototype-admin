"use client"

import { usePathname } from "next/navigation"
import { useLiaFloat } from "@/contexts/lia-float-context"
import { LiaSuperPrompt } from "@/components/lia-float/LiaSuperPrompt"
import { UnifiedChatBubble } from "./UnifiedChatBubble"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

/**
 * UnifiedChatConditional — Global wrapper in layout.tsx.
 *
 * In the new architecture, the sidebar UnifiedChat is rendered
 * INSIDE dashboard-app.tsx (as flex child). This conditional
 * only handles:
 * - The bubble button (when chat is closed outside dashboard)
 * - LiaSuperPrompt
 * - Path-based visibility
 *
 * The inline sidebar is rendered by DashboardChatPanel in dashboard-app.
 */
export function UnifiedChatConditional() {
  const pathname = usePathname()
  const { isOpen, open, splitView, hasInlineChat } = useLiaFloat()

  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null

  // Check if we're inside the dashboard shell
  const isDashboard = typeof document !== "undefined"
    ? !!document.querySelector("[data-dashboard-shell]")
    : false

  return (
    <>
      {/* Bubble: show when chat closed and not on ChatPage */}
      {!hasInlineChat && !isOpen && !isDashboard && (
        <UnifiedChatBubble onOpen={() => open()} />
      )}

      {/* LiaSuperPrompt: preserved from original */}
      {!splitView.active && <LiaSuperPrompt />}
    </>
  )
}
