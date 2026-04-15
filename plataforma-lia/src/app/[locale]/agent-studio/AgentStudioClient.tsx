"use client"

import React, { useEffect } from "react"
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

  useEffect(() => {
    switchChatContext("agent_studio", { conversationId: null })
    return () => {
      switchChatContext("general", { conversationId: null })
    }
  }, [switchChatContext])

  return (
    <div className="h-full">
      <AgentStudioPage />
    </div>
  )
}
