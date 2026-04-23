"use client"

import React, { useEffect, useRef } from "react"
import AgentStudioPage from "@/components/pages-agent-studio/AgentStudioPage"
import { useLiaChatContext } from "@/contexts/lia-float-context"

/**
 * AgentStudioClient — wraps AgentStudioPage and notifies the global UnifiedChat
 * provider that the user is in the Agent Studio context.
 *
 * Without this, getPageContext() fallback would treat /agent-studio as
 * "general", and short messages like "oi" would route to recruiter_assistant
 * (default) and end up in the Tier 8 clarification fallback — which the
 * UnifiedChat does not render today, producing a silent chat.
 *
 * On unmount we revert to "general" so the next page starts clean.
 */
export default function AgentStudioClient() {
  const { switchChatContext } = useLiaChatContext()
  // `switchChatContext` from the provider changes reference on every parent
  // render (its useCallback depends on `connection`, which is re-created each
  // render). Pin it behind a ref so this effect runs once on mount and once
  // on unmount, without retriggering on every render.
  const switchRef = useRef(switchChatContext)
  switchRef.current = switchChatContext

  useEffect(() => {
    switchRef.current("agent_studio", { conversationId: null })
    return () => {
      switchRef.current("general", { conversationId: null })
    }
  }, [])

  return (
    <div className="h-full">
      <AgentStudioPage />
    </div>
  )
}
