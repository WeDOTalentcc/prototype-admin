"use client"

/**
 * useLiaChatConnection -- Facade hook.
 *
 * Composes useChatSocket and useChatMessages into the original combined
 * interface so existing consumers need zero changes.
 */

import { useCallback } from "react"
import { useChatSocket } from "./useChatSocket"
import { useChatMessages } from "./useChatMessages"

// Re-export all public types from the shared types module
export type {
  LiaChatMessage,
  HITLPending,
  PanelUpdateEvent,
  BackgroundTaskEvent,
  UseLiaChatConnectionOptions,
  UseLiaChatConnectionResult,
  TransportMode,
} from "./lia-chat-connection-types"

// Re-export sub-hooks for direct use
export { useChatSocket } from "./useChatSocket"
export { useChatMessages } from "./useChatMessages"

import type {
  UseLiaChatConnectionOptions,
  UseLiaChatConnectionResult,
} from "./lia-chat-connection-types"

export function useLiaChatConnection({
  sessionId,
  onMessageComplete,
  onPanelUpdate,
}: UseLiaChatConnectionOptions): UseLiaChatConnectionResult {
  const socket = useChatSocket({ sessionId, onMessageComplete, onPanelUpdate })

  const messaging = useChatMessages({
    sessionId,
    isConnected: socket.isConnected,
    transportMode: socket.transportMode,
    wsSend: socket.wsSend,
    sendRaw: socket.sendRaw,
    clearTokens: socket.clearTokens,
    sendMessageViaSSE: socket.sendMessageViaSSE,
    hitlRef: socket.hitlRef,
    setHitlPending: socket.setHitlPending,
    onMessageComplete,
    conversationIdFromWs: socket.conversationIdFromWs,
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const dismissFairnessWarnings = useCallback(() => socket.setFairnessWarnings([]), [socket.setFairnessWarnings])

  const clearBackgroundTask = useCallback((taskId: string) => {
    socket.setBackgroundTasks(prev => prev.filter(t => t.task_id !== taskId))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket.setBackgroundTasks])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const resetBackgroundTasks = useCallback(() => socket.setBackgroundTasks([]), [socket.setBackgroundTasks])

  return {
    conversationId: messaging.conversationId,
    setConversationId: messaging.setConversationId,
    isConnected: socket.isConnected,
    isStreaming: socket.isStreaming,
    isReconnecting: socket.isReconnecting,
    reconnectAttempt: socket.reconnectAttempt,
    streamingContent: socket.tokens,
    error: socket.error,
    transportMode: socket.transportMode,
    isCreating: messaging.isCreating,
    isFetchingHistory: messaging.isFetchingHistory,
    hitlPending: socket.hitlPending,
    thinkingSteps: socket.thinkingSteps,
    isThinking: socket.isThinking,
    fairnessWarnings: socket.fairnessWarnings,
    backgroundTasks: socket.backgroundTasks,
    planProgressSteps: socket.planProgressSteps,
    activePlanId: socket.activePlanId,
    sendMessage: messaging.sendMessage,
    sendApproval: messaging.sendApproval,
    dismissFairnessWarnings,
    clearBackgroundTask,
    resetBackgroundTasks,
    initConversation: messaging.initConversation,
    loadHistory: messaging.loadHistory,
    connect: socket.connect,
    disconnect: socket.disconnect,
  }
}
