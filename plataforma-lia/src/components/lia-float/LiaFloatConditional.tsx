/**
 * @deprecated Use UnifiedChat (sidebar mode) via InlineChatBridge instead.
 * This component is replaced by the unified chat architecture (Phase 6).
 * Migration: import { InlineChatBridge } from "@/components/unified-chat"
 */
"use client"

import { usePathname } from "next/navigation"
import { LiaChatButton } from "./LiaChatButton"
import { LiaChatPanel } from "./LiaChatPanel"
import { LiaSuperPrompt } from "./LiaSuperPrompt"
import { useLiaFloat } from "@/contexts/lia-float-context"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

export function LiaFloatConditional() {
  const pathname = usePathname()
  const { splitView, hasInlineChat } = useLiaFloat()
  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null
  return (
    <>
      {!hasInlineChat && <LiaChatPanel />}
      {!hasInlineChat && <LiaChatButton />}
      {!splitView.active && <LiaSuperPrompt />}
    </>
  )
}
