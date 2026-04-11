"use client"

/**
 * useTriagemChat — Facade hook.
 *
 * Composes useTriagemSession and useTriagemMessages into the original
 * combined interface so existing consumers need zero changes.
 */

// Re-export sub-hooks for direct use
export { useTriagemSession } from "./useTriagemSession"
export { useTriagemMessages } from "./useTriagemMessages"

import { useTriagemSession } from "./useTriagemSession"
import { useTriagemMessages } from "./useTriagemMessages"
import type { UseTriagemChatReturn } from "@/components/triagem/types"

export function useTriagemChat(token: string): UseTriagemChatReturn {
  const sessionHook = useTriagemSession({ token })
  const messagesHook = useTriagemMessages({
    token,
    pageState: sessionHook.pageState,
    setPageState: sessionHook.setPageState,
    session: sessionHook.session,
    setSession: sessionHook.setSession,
    config: sessionHook.config,
    messages: sessionHook.messages,
    setMessages: sessionHook.setMessages,
    progress: sessionHook.progress,
    setProgress: sessionHook.setProgress,
    setError: sessionHook.setError,
    setIsLiaTyping: sessionHook.setIsLiaTyping,
    mountedRef: sessionHook.mountedRef,
    isSending: sessionHook.isSending,
    setIsSending: sessionHook.setIsSending,
  })

  return {
    pageState: sessionHook.pageState,
    session: sessionHook.session,
    config: sessionHook.config,
    messages: sessionHook.messages,
    progress: sessionHook.progress,
    error: sessionHook.error,
    completionSummary: sessionHook.completionSummary,
    isLiaTyping: sessionHook.isLiaTyping,
    isSending: sessionHook.isSending,
    isLoadingHistory: messagesHook.isLoadingHistory,
    initSession: sessionHook.initSession,
    startChat: sessionHook.startChat,
    sendMessage: messagesHook.sendMessage,
    completeSession: sessionHook.completeSession,
    reviewSession: sessionHook.reviewSession,
    loadHistory: messagesHook.loadHistory,
  }
}
