"use client"

import React, { useEffect } from "react"
import { useLiaFloat, useLiaChatContext } from "@/contexts/lia-float-context"
import { HITLConfirmCard } from "@/components/lia-float/HITLConfirmCard"
import { DynamicContextPanel } from "@/components/lia-float/panels"
import { UnifiedChat } from "./UnifiedChat"

interface Props {
  initialConversationId?: string | null
}

/**
 * ChatPageFullscreen — Wraps UnifiedChat in fullscreen mode for the Chat LIA menu page.
 *
 * This replaces the legacy ChatPage with the unified design while preserving:
 * - HITL confirmation cards
 * - Dynamic context panels (split view)
 * - hasInlineChat flag (prevents sidebar from showing)
 * - Initial conversation loading
 *
 * Advanced features (SmartSearch, CommandPalette, CandidateDetail, etc.)
 * will be progressively integrated in later phases.
 */
export function ChatPageFullscreen({ initialConversationId }: Props) {
  const { setHasInlineChat, dynamicPanel, closeDynamicPanel } = useLiaFloat()
  const {
    chatHitlPending,
    sendApproval,
    loadChatHistory,
    setChatConversationId,
  } = useLiaChatContext()

  // Signal that this page has its own chat (hide sidebar)
  useEffect(() => {
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

  const hasDynamicPanel = !!dynamicPanel

  return (
    <div className="flex flex-1 overflow-hidden h-full">
      {/* Main chat area — shrinks when dynamic panel is open */}
      <div className={hasDynamicPanel ? "flex-1 min-w-0" : "flex-1"}>
        <UnifiedChat
          renderMode="overlay"
          initialMode="fullscreen"
          className="relative inset-auto z-auto h-full"
        />
      </div>

      {/* HITL confirmation overlay */}
      {chatHitlPending && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 w-full max-w-[600px] px-4">
          <HITLConfirmCard
            action={chatHitlPending.action}
            description={chatHitlPending.description}
            onConfirm={() => sendApproval(true)}
            onCancel={() => sendApproval(false)}
          />
        </div>
      )}

      {/* Dynamic context panel (split view) */}
      {hasDynamicPanel && (
        <div className="w-[400px] flex-shrink-0 border-l border-lia-border-subtle overflow-y-auto">
          <DynamicContextPanel panel={dynamicPanel} />
        </div>
      )}
    </div>
  )
}
