"use client"

/**
 * useChatSocket — WebSocket connection management and event handling for LIA chat.
 *
 * Manages: WS auth token, streaming connection, event dispatch (HITL, panels,
 * background tasks, plan progress, thinking steps, fairness warnings).
 */

import { useState, useRef, useCallback, useEffect } from "react"
import { useAgentStreaming, type StreamingEvent } from "./use-agent-streaming"
import type {
  HITLPending,
  PanelUpdateEvent,
  BackgroundTaskEvent,
} from "./lia-chat-connection-types"

export interface UseChatSocketOptions {
  sessionId: string
  onMessageComplete?: (content: string, executionPlan?: Record<string, unknown>) => void
  onPanelUpdate?: (event: PanelUpdateEvent) => void
}

export interface UseChatSocketReturn {
  /** Current WS streaming tokens (partial content) */
  tokens: string
  isStreaming: boolean
  isConnected: boolean
  isReconnecting: boolean
  reconnectAttempt: number
  error: string | null
  connect: () => void
  disconnect: () => void
  wsSend: (content: string, context: Record<string, unknown>, domain: string) => void
  sendRaw: (data: Record<string, unknown>) => void
  clearTokens: () => void

  // Event-derived state
  hitlPending: HITLPending | null
  hitlRef: React.MutableRefObject<HITLPending | null>
  setHitlPending: React.Dispatch<React.SetStateAction<HITLPending | null>>
  thinkingSteps: string[]
  isThinking: boolean
  fairnessWarnings: string[]
  setFairnessWarnings: React.Dispatch<React.SetStateAction<string[]>>
  backgroundTasks: BackgroundTaskEvent[]
  setBackgroundTasks: React.Dispatch<React.SetStateAction<BackgroundTaskEvent[]>>
  planProgressSteps: Array<{ task_id: string; action_id: string; domain_id: string; status: string }>
  activePlanId: string | null

  // Conversation ID synced from WS events
  conversationIdFromWs: string | null
}

export function useChatSocket({
  sessionId,
  onMessageComplete,
  onPanelUpdate,
}: UseChatSocketOptions): UseChatSocketReturn {
  const [hitlPending, setHitlPending] = useState<HITLPending | null>(null)
  const hitlRef = useRef<HITLPending | null>(null)
  const onCompleteRef = useRef(onMessageComplete)
  const onPanelUpdateRef = useRef(onPanelUpdate)

  const [planProgressSteps, setPlanProgressSteps] = useState<Array<{ task_id: string; action_id: string; domain_id: string; status: string }>>([])
  const [activePlanId, setActivePlanId] = useState<string | null>(null)
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([])
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTaskEvent[]>([])
  const [wsAuthToken, setWsAuthToken] = useState<string | undefined>(undefined)
  const [conversationIdFromWs, setConversationIdFromWs] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch("/api/auth/ws-token")
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!cancelled && data?.token) setWsAuthToken(data.token)
      })
      .catch((err) => { console.warn('[useChatSocket] ws-token fetch failed', err) })
    return () => { cancelled = true }
  }, [])

  useEffect(() => { onCompleteRef.current = onMessageComplete }, [onMessageComplete])
  useEffect(() => { onPanelUpdateRef.current = onPanelUpdate }, [onPanelUpdate])

  const handleEvent = useCallback((event: StreamingEvent) => {
    switch (event.type) {
      case "thinking":
        setIsThinking(true)
        if (event.content) {
          setThinkingSteps(prev => [...prev, event.content as string])
        }
        break

      case "plan_progress": {
        const planEvent = event as unknown as Record<string, unknown>
        const planEventType = planEvent.event as string
        if (planEventType === "plan_started") {
          setActivePlanId(planEvent.plan_id as string || null)
          setPlanProgressSteps([])
        } else if (
          planEventType === "step_running" ||
          planEventType === "step_completed" ||
          planEventType === "step_skipped"
        ) {
          setPlanProgressSteps(prev => {
            const taskId = planEvent.task_id as string
            const existing = prev.findIndex(s => s.task_id === taskId)
            const step = {
              task_id: taskId,
              action_id: planEvent.action_id as string || "",
              domain_id: planEvent.domain_id as string || "",
              status:
                planEventType === "step_running"
                  ? "running"
                  : planEventType === "step_skipped"
                    ? "skipped"
                    : (planEvent.status as string || "completed"),
            }
            if (existing >= 0) {
              const updated = [...prev]
              updated[existing] = step
              return updated
            }
            return [...prev, step]
          })
        } else if (planEventType === "plan_completed") {
          setActivePlanId(null)
        }
        break
      }

      case "approval_required": {
        const pending: HITLPending = {
          pendingId: event.pending_id ?? "",
          threadId: event.thread_id ?? "",
          action: event.action ?? "",
          description: event.description ?? "",
          data: event.data ?? {},
        }
        hitlRef.current = pending
        setHitlPending(pending)
        break
      }

      case "approval_confirmed":
        break

      case "panel_update": {
        const panelEvent = event as unknown as Record<string, unknown>
        onPanelUpdateRef.current?.({
          panel_type: (panelEvent.panel_type as string) || "",
          panel_data: (panelEvent.panel_data as Record<string, unknown>) || {},
          panel_title: panelEvent.panel_title as string | undefined,
          action: (panelEvent.action as "open" | "update" | "close") || "open",
        })
        break
      }

      case "background_task_update": {
        const bgEvent = event as unknown as Record<string, unknown>
        const taskUpdate: BackgroundTaskEvent = {
          task_id: (bgEvent.task_id as string) || "",
          task_type: (bgEvent.task_type as BackgroundTaskEvent["task_type"]) || "analysis",
          label: (bgEvent.label as string) || "",
          status: (bgEvent.status as BackgroundTaskEvent["status"]) || "running",
          progress: bgEvent.progress as number | undefined,
          message: bgEvent.message as string | undefined,
          result: bgEvent.result as Record<string, unknown> | undefined,
        }
        setBackgroundTasks(prev => {
          const idx = prev.findIndex(t => t.task_id === taskUpdate.task_id)
          if (idx >= 0) {
            const updated = [...prev]
            updated[idx] = taskUpdate
            return updated
          }
          return [...prev, taskUpdate]
        })
        break
      }

      case "message":
        setIsThinking(false)
        hitlRef.current = null
        setHitlPending(null)
        if ((event as any).conversation_id && typeof (event as any).conversation_id === "string") {
          setConversationIdFromWs((event as any).conversation_id)
        }
        if (event.fairness_warnings && (event.fairness_warnings as string[]).length > 0) {
          setFairnessWarnings(event.fairness_warnings as string[])
        } else {
          setFairnessWarnings([])
        }
        if (event.content) {
          const execPlan = (event as unknown as Record<string, unknown>).execution_plan as Record<string, unknown> | undefined
          onCompleteRef.current?.(event.content, execPlan)
        }
        break

      default:
        break
    }
  }, [])

  const {
    tokens,
    isStreaming,
    isConnected,
    isReconnecting,
    reconnectAttempt,
    error,
    connect,
    disconnect,
    sendMessage: wsSend,
    sendRaw,
    clearTokens,
  } = useAgentStreaming(sessionId, { authToken: wsAuthToken }, handleEvent)

  useEffect(() => {
    if (wsAuthToken && isConnected) {
      disconnect()
      setTimeout(() => connect(), 50)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsAuthToken])

  return {
    tokens,
    isStreaming,
    isConnected,
    isReconnecting,
    reconnectAttempt,
    error,
    connect,
    disconnect,
    wsSend,
    sendRaw,
    clearTokens,
    hitlPending,
    hitlRef,
    setHitlPending,
    thinkingSteps,
    isThinking,
    fairnessWarnings,
    setFairnessWarnings,
    backgroundTasks,
    setBackgroundTasks,
    planProgressSteps,
    activePlanId,
    conversationIdFromWs,
  }
}
