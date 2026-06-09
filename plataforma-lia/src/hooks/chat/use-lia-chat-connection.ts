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
import type { BackgroundTaskEvent } from "./lia-chat-connection-types"

/**
 * Merge a synchronously-seeded background task into the existing list.
 *
 * Race guard: if a WS terminal update (`completed`/`failed`) for the same
 * `task_id` has already landed BEFORE the synchronous seed runs (very fast
 * worker / slow await on the originating HTTP response body), do NOT
 * overwrite the terminal row with `queued`/`running`. Downgrading would
 * silently strip the terminal status and prevent consumers from ever
 * firing their completion / failure handlers.
 *
 * Exported as a pure function so the merge semantics are unit-testable
 * without spinning up the full connection facade hook.
 */
export function mergeSeededBackgroundTask(
  prev: BackgroundTaskEvent[],
  event: BackgroundTaskEvent,
): BackgroundTaskEvent[] {
  const idx = prev.findIndex(t => t.task_id === event.task_id)
  if (idx >= 0) {
    const existing = prev[idx]
    const existingIsTerminal = existing.status === "completed" || existing.status === "failed"
    const incomingIsNonTerminal = event.status === "queued" || event.status === "running"
    if (existingIsTerminal && incomingIsNonTerminal) {
      return prev
    }
    const next = [...prev]
    next[idx] = event
    return next
  }
  return [...prev, event]
}

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
    wsEventTickRef: socket.wsEventTickRef,
    hitlRef: socket.hitlRef,
    setHitlPending: socket.setHitlPending,
    onMessageComplete,
    conversationIdFromWs: socket.conversationIdFromWs,
    setIsThinking: socket.setIsThinking,
  })

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const dismissFairnessWarnings = useCallback(() => socket.setFairnessWarnings([]), [socket.setFairnessWarnings])

  const clearBackgroundTask = useCallback((taskId: string) => {
    socket.setBackgroundTasks(prev => prev.filter(t => t.task_id !== taskId))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket.setBackgroundTasks])

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const resetBackgroundTasks = useCallback(() => socket.setBackgroundTasks([]), [socket.setBackgroundTasks])

  // Audit B-02 / Task #865 — seed a queued/running task synchronously when
  // the caller already knows the `task_id` (e.g. just got 202 + task_id back
  // from the JD upload proxy) so the UI shows progress before the WS
  // worker's first `background_task_update` arrives. Merge semantics live
  // in `mergeSeededBackgroundTask` so the race guard is unit-testable.
  const seedBackgroundTask = useCallback((event: import("./lia-chat-connection-types").BackgroundTaskEvent) => {
    socket.setBackgroundTasks(prev => mergeSeededBackgroundTask(prev, event))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket.setBackgroundTasks])

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
    seedBackgroundTask,
    initConversation: messaging.initConversation,
    loadHistory: messaging.loadHistory,
    connect: socket.connect,
    disconnect: socket.disconnect,
    clearActivityState: socket.clearActivityState,
  }
}
