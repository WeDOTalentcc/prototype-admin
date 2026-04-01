"use client"

import { useRef, useEffect } from "react"

interface UseConversationMemoryInitParams {
  conversationMemory: {
    initConversation: (email: string, type: string, draftId?: string) => Promise<void>
    updateSummary: (force?: boolean) => Promise<void>
  }
  isOpen: boolean
  mode: string
  user: { email?: string } | null | undefined
  wizardDraftId: string
}

export function useConversationMemoryInit({
  conversationMemory,
  isOpen,
  mode,
  user,
  wizardDraftId,
}: UseConversationMemoryInitParams) {
  // Use refs to avoid infinite loops from function dependencies
  const initConversationRef = useRef(conversationMemory.initConversation)
  const updateSummaryRef = useRef(conversationMemory.updateSummary)
  const conversationInitializedRef = useRef(false)

  // Keep refs updated
  useEffect(() => {
    initConversationRef.current = conversationMemory.initConversation
    updateSummaryRef.current = conversationMemory.updateSummary
  }, [conversationMemory.initConversation, conversationMemory.updateSummary])

  useEffect(() => {
    // Only initialize once per modal open
    if (isOpen && mode === 'job-creation' && user?.email && !conversationInitializedRef.current) {
      conversationInitializedRef.current = true
      initConversationRef.current(
        user.email,
        'wizard',
        wizardDraftId
      ).catch(() => {
        // Silently ignore initialization errors - conversation is optional
      })
    }

    // Reset flag when modal closes
    if (!isOpen) {
      conversationInitializedRef.current = false
    }

    return () => {
      if (mode === 'job-creation' && conversationInitializedRef.current) {
        updateSummaryRef.current(true).catch(() => {})
      }
    }
  }, [isOpen, mode, user?.email, wizardDraftId])
}
