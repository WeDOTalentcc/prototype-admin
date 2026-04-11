/**
 * useFloatStreaming — WebSocket + HITL para o LiaChatPanel flutuante.
 *
 * Estende useAgentStreaming com:
 *   - HITL: detecta approval_required, expõe sendApproval()
 *   - Domain routing: recebe domain explícito por mensagem
 *   - onComplete callback: chamado com o conteúdo final ao receber "message"
 *
 * Compatível com Vue/Nuxt: interface mapeia para composable useFloatStreaming().
 */

import { useState, useRef, useCallback, useEffect } from 'react'
import { useAgentStreaming, type StreamingEvent } from './use-agent-streaming'

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

import type { TransportMode } from './useChatTransport'

export interface UseFloatStreamingResult {
  isConnected: boolean
  isStreaming: boolean
  isReconnecting: boolean
  reconnectAttempt: number
  streamingContent: string
  error: string | null
  transportMode: TransportMode
  hitlPending: HITLPending | null
  thinkingSteps: string[]
  isThinking: boolean
  fairnessWarnings: string[]
  backgroundTasks: BackgroundTaskEvent[]
  sendMessage: (content: string, domain?: string, scope?: string) => void
  sendApproval: (approved: boolean) => void
  dismissFairnessWarnings: () => void
  clearBackgroundTask: (taskId: string) => void
  resetBackgroundTasks: () => void
  planProgressSteps: Array<{ task_id: string; action_id: string; domain_id: string; status: string }>
  activePlanId: string | null
  connect: () => void
  disconnect: () => void
}

export function useFloatStreaming(
  sessionId: string,
  onComplete: (content: string, executionPlan?: Record<string, unknown>) => void,
  onPanelUpdate?: (event: PanelUpdateEvent) => void,
): UseFloatStreamingResult {
  const [hitlPending, setHitlPending] = useState<HITLPending | null>(null)
  const hitlRef = useRef<HITLPending | null>(null)
  const onCompleteRef = useRef(onComplete)
  const onPanelUpdateRef = useRef(onPanelUpdate)
  const [planProgressSteps, setPlanProgressSteps] = useState<Array<{task_id: string; action_id: string; domain_id: string; status: string}>>([])
  const [activePlanId, setActivePlanId] = useState<string | null>(null)
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([])
  const [isThinking, setIsThinking] = useState(false)
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([])
  const [backgroundTasks, setBackgroundTasks] = useState<BackgroundTaskEvent[]>([])
  const [wsAuthToken, setWsAuthToken] = useState<string | undefined>(undefined)

  useEffect(() => {
    let cancelled = false
    fetch('/api/auth/ws-token')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!cancelled && data?.token) setWsAuthToken(data.token)
      })
      .catch((err) => { console.warn('[useFloatStreaming] ws-token fetch failed', err) })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  useEffect(() => {
    onPanelUpdateRef.current = onPanelUpdate
  }, [onPanelUpdate])

  const handleEvent = useCallback((event: StreamingEvent) => {
    switch (event.type) {
      case 'thinking':
        // E7: acumula etapas de raciocínio ReAct
        setIsThinking(true)
        if (event.content) {
          setThinkingSteps(prev => [...prev, event.content as string])
        }
        break

      case 'plan_progress': {
        const planEvent = event as unknown as Record<string, unknown>
        const planEventType = planEvent.event as string
        if (planEventType === 'plan_started') {
          setActivePlanId(planEvent.plan_id as string || null)
          setPlanProgressSteps([])
        } else if (planEventType === 'step_running' || planEventType === 'step_completed' || planEventType === 'step_skipped') {
          setPlanProgressSteps(prev => {
            const taskId = planEvent.task_id as string
            const existing = prev.findIndex(s => s.task_id === taskId)
            const step = {
              task_id: taskId,
              action_id: planEvent.action_id as string || '',
              domain_id: planEvent.domain_id as string || '',
              status: planEventType === 'step_running' ? 'running' : planEventType === 'step_skipped' ? 'skipped' : (planEvent.status as string || 'completed'),
            }
            if (existing >= 0) {
              const updated = [...prev]
              updated[existing] = step
              return updated
            }
            return [...prev, step]
          })
        } else if (planEventType === 'plan_completed') {
          // Plan done — final state will come via 'message' event
          setActivePlanId(null)
        }
        break
      }

      case 'approval_required': {
        const pending: HITLPending = {
          pendingId: event.pending_id ?? '',
          threadId: event.thread_id ?? '',
          action: event.action ?? '',
          description: event.description ?? '',
          data: event.data ?? {},
        }
        hitlRef.current = pending
        setHitlPending(pending)
        break
      }

      case 'approval_confirmed':
        // backend confirmou — aguardar resposta do agente via 'message'
        break

      case 'panel_update': {
        const panelEvent = event as unknown as Record<string, unknown>
        onPanelUpdateRef.current?.({
          panel_type: (panelEvent.panel_type as string) || "",
          panel_data: (panelEvent.panel_data as Record<string, unknown>) || {},
          panel_title: panelEvent.panel_title as string | undefined,
          action: (panelEvent.action as "open" | "update" | "close") || "open",
        })
        break
      }

      case 'background_task_update': {
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

      case 'message':
        setIsThinking(false)
        hitlRef.current = null
        setHitlPending(null)
        // FAR-2/C: capturar fairness warnings se presentes
        if (event.fairness_warnings && event.fairness_warnings.length > 0) {
          setFairnessWarnings(event.fairness_warnings)
        } else {
          setFairnessWarnings([])
        }
        if (event.content) {
          const _execPlan = (event as unknown as Record<string, unknown>).execution_plan as Record<string, unknown> | undefined
          onCompleteRef.current(event.content, _execPlan)
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
    transportMode,
    connect,
    disconnect,
    sendMessage: wsSend,
    sendRaw,
    clearTokens,
    sendMessageViaSSE,
  } = useAgentStreaming(sessionId, { authToken: wsAuthToken }, handleEvent)

  useEffect(() => {
    if (wsAuthToken && isConnected) {
      disconnect()
      setTimeout(() => connect(), 50)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [wsAuthToken])

  const sendMessage = useCallback(async (content: string, domain = '', scope?: string) => {
    setThinkingSteps([])
    setIsThinking(false)
    clearTokens()
    const context = scope ? { scope } : {}

    if (isConnected && transportMode === 'ws') {
      wsSend(content, context, domain)
      return
    }

    if (isConnected && transportMode === 'sse') {
      sendMessageViaSSE(sessionId, content, domain || 'recruiter_assistant', context, null)
      return
    }

    try {
      const res = await fetch('/api/backend-proxy/chat/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ message: content, domain, session_id: sessionId, context }),
      })
      const data = await res.json()
      if (data.content) {
        onCompleteRef.current(data.content)
      }
    } catch {
      onCompleteRef.current('Erro ao conectar com a LIA. Tente novamente.')
    }
  }, [wsSend, clearTokens, isConnected, transportMode, sessionId, sendMessageViaSSE])

  const sendApproval = useCallback((approved: boolean) => {
    const pending = hitlRef.current
    if (!pending) return
    // Clear ref immediately to prevent double-submit on rapid clicks.
    // For approval: UI (hitlPending state) stays until handleEvent('message') clears it.
    // For rejection: clear UI immediately below.
    hitlRef.current = null
    sendRaw({
      type: 'approval_response',
      approved,
      thread_id: pending.threadId,
      pending_id: pending.pendingId,
    })
    if (!approved) {
      // rejeição imediata — limpa o estado sem aguardar backend
      setHitlPending(null)
    }
  }, [sendRaw])

  const dismissFairnessWarnings = useCallback(() => setFairnessWarnings([]), [])

  const clearBackgroundTask = useCallback((taskId: string) => {
    setBackgroundTasks(prev => prev.filter(t => t.task_id !== taskId))
  }, [])

  const resetBackgroundTasks = useCallback(() => {
    setBackgroundTasks([])
  }, [])

  return {
    isConnected,
    isStreaming,
    isReconnecting,
    reconnectAttempt,
    streamingContent: tokens,
    error,
    transportMode,
    hitlPending,
    thinkingSteps,
    isThinking,
    fairnessWarnings,
    backgroundTasks,
    dismissFairnessWarnings,
    clearBackgroundTask,
    resetBackgroundTasks,
    planProgressSteps,
    activePlanId,
    sendMessage,
    sendApproval,
    connect,
    disconnect,
  }
}
