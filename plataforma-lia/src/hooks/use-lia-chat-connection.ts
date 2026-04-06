"use client"

/**
 * useLiaChatConnection — Hook unificado de comunicação com o backend LIA.
 *
 * Unifica useFloatStreaming, useFloatConversation e os fetch diretos dos
 * handlers de kanban/candidates em um único canal de comunicação.
 *
 * Suporta:
 *   - WebSocket streaming (via useAgentStreaming)
 *   - Fallback para fetch quando WS não está disponível
 *   - Criação e carregamento de conversas
 *   - HITL (approval_required)
 *   - Panel updates, background tasks, plan progress
 *   - PII masking no título da conversa
 *
 * Usado por LiaChatContext como única fonte de comunicação com backend.
 */

import { useState, useRef, useCallback, useEffect } from "react"
import { useAgentStreaming, type StreamingEvent } from "./use-agent-streaming"
import { useRecentItemsStore } from "@/stores/recent-items-store"

// ─── Tipos públicos ────────────────────────────────────────────────────────────

export interface LiaChatMessage {
  id: string
  sender: "lia" | "user"
  content: string
  timestamp: string
  executionPlan?: Record<string, unknown>
  planProgressSteps?: Array<{ task_id: string; action_id: string; status: string }>
  metadata?: Record<string, unknown>
}

export interface HITLPending {
  pendingId: string
  threadId: string
  action: string
  description: string
  data: Record<string, unknown>
}

export interface PanelUpdateEvent {
  panel_type: string
  panel_data: Record<string, unknown>
  panel_title?: string
  action: "open" | "update" | "close"
}

export interface BackgroundTaskEvent {
  task_id: string
  task_type: "sourcing" | "screening" | "communication" | "analysis"
  label: string
  status: "running" | "completed" | "failed"
  progress?: number
  message?: string
  result?: Record<string, unknown>
}

export interface UseLiaChatConnectionOptions {
  sessionId: string
  onMessageComplete?: (content: string, executionPlan?: Record<string, unknown>) => void
  onPanelUpdate?: (event: PanelUpdateEvent) => void
}

export interface UseLiaChatConnectionResult {
  conversationId: string | null
  setConversationId: (id: string | null) => void
  isConnected: boolean
  isStreaming: boolean
  isReconnecting: boolean
  reconnectAttempt: number
  streamingContent: string
  error: string | null
  isCreating: boolean
  isFetchingHistory: boolean
  hitlPending: HITLPending | null
  thinkingSteps: string[]
  isThinking: boolean
  fairnessWarnings: string[]
  backgroundTasks: BackgroundTaskEvent[]
  planProgressSteps: Array<{ task_id: string; action_id: string; domain_id: string; status: string }>
  activePlanId: string | null
  sendMessage: (content: string, domain?: string, scope?: string) => Promise<void>
  sendApproval: (approved: boolean) => void
  dismissFairnessWarnings: () => void
  clearBackgroundTask: (taskId: string) => void
  resetBackgroundTasks: () => void
  initConversation: (firstMessage: string, contextType?: string) => Promise<string | null>
  loadHistory: (id: string) => Promise<LiaChatMessage[]>
  connect: () => void
  disconnect: () => void
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function maskPII(text: string): string {
  return text
    .replace(/\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b/g, "[CPF]")
    .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, "[email]")
    .replace(/\b(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\d{4}|\d{4})-?\d{4}\b/g, "[tel]")
}

export function formatMessageTime(isoDate?: string): string {
  const d = isoDate ? new Date(isoDate) : new Date()
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useLiaChatConnection({
  sessionId,
  onMessageComplete,
  onPanelUpdate,
}: UseLiaChatConnectionOptions): UseLiaChatConnectionResult {
  const recentItemsStore = useRecentItemsStore()

  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)
  const [isFetchingHistory, setIsFetchingHistory] = useState(false)

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

  useEffect(() => {
    let cancelled = false
    fetch("/api/auth/ws-token")
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!cancelled && data?.token) setWsAuthToken(data.token)
      })
      .catch(() => {})
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
        if (event.conversation_id && typeof event.conversation_id === "string" && event.conversation_id !== conversationId) {
          setConversationId(event.conversation_id)
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

  const sendMessage = useCallback(async (content: string, domain = "", scope?: string) => {
    setThinkingSteps([])
    setIsThinking(false)
    clearTokens()
    const context: Record<string, unknown> = scope ? { scope } : {}
    if (conversationId) {
      context.conversation_id = conversationId
    }

    if (isConnected) {
      wsSend(content, context, domain)
      return
    }

    try {
      const res = await fetch("/api/backend-proxy/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          message: content,
          domain,
          session_id: sessionId,
          conversation_id: conversationId,
          context,
        }),
      })
      const data = await res.json() as { content?: string; conversation_id?: string }
      if (data.conversation_id && data.conversation_id !== conversationId) {
        setConversationId(data.conversation_id)
      }
      if (data.content) {
        onCompleteRef.current?.(data.content)
      }
    } catch {
      onCompleteRef.current?.("Erro ao conectar com a LIA. Tente novamente.")
    }
  }, [wsSend, clearTokens, isConnected, sessionId, conversationId])

  const sendApproval = useCallback((approved: boolean) => {
    const pending = hitlRef.current
    if (!pending) return
    hitlRef.current = null
    sendRaw({
      type: "approval_response",
      approved,
      thread_id: pending.threadId,
      pending_id: pending.pendingId,
    })
    if (!approved) {
      setHitlPending(null)
    }
  }, [sendRaw])

  const initConversation = useCallback(async (
    firstMessage: string,
    contextType = "general"
  ): Promise<string | null> => {
    setIsCreating(true)
    try {
      const title = maskPII(firstMessage.length > 50 ? firstMessage.slice(0, 47) + "…" : firstMessage)
      const res = await fetch("/api/backend-proxy/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, context_type: contextType }),
      })
      if (!res.ok) return null
      const data = await res.json() as { id?: string }
      const id = data.id ?? null
      if (id) {
        setConversationId(id)
        recentItemsStore.addItem({
          id,
          type: "chat",
          title,
          timestamp: Date.now(),
          meta: { conversationId: id },
        })
      }
      return id
    } catch {
      return null
    } finally {
      setIsCreating(false)
    }
  }, [recentItemsStore])

  const loadHistory = useCallback(async (id: string): Promise<LiaChatMessage[]> => {
    setIsFetchingHistory(true)
    try {
      const res = await fetch(
        `/api/backend-proxy/conversations/${id}?include_messages=true&message_limit=50`
      )
      if (!res.ok) return []
      const data = await res.json() as {
        messages?: Array<{ id: string; role: string; content: string; created_at?: string }>
      }
      return (data.messages ?? []).map(m => ({
        id: m.id,
        sender: m.role === "assistant" ? "lia" : "user",
        content: m.content,
        timestamp: formatMessageTime(m.created_at),
      }))
    } catch {
      return []
    } finally {
      setIsFetchingHistory(false)
    }
  }, [])

  const dismissFairnessWarnings = useCallback(() => setFairnessWarnings([]), [])

  const clearBackgroundTask = useCallback((taskId: string) => {
    setBackgroundTasks(prev => prev.filter(t => t.task_id !== taskId))
  }, [])

  const resetBackgroundTasks = useCallback(() => setBackgroundTasks([]), [])

  return {
    conversationId,
    setConversationId,
    isConnected,
    isStreaming,
    isReconnecting,
    reconnectAttempt,
    streamingContent: tokens,
    error,
    isCreating,
    isFetchingHistory,
    hitlPending,
    thinkingSteps,
    isThinking,
    fairnessWarnings,
    backgroundTasks,
    planProgressSteps,
    activePlanId,
    sendMessage,
    sendApproval,
    dismissFairnessWarnings,
    clearBackgroundTask,
    resetBackgroundTasks,
    initConversation,
    loadHistory,
    connect,
    disconnect,
  }
}
