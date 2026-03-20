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

export interface UseFloatStreamingResult {
  isConnected: boolean
  isStreaming: boolean
  /** true enquanto aguarda para reconectar (backoff ativo) */
  isReconnecting: boolean
  /** Número da tentativa de reconexão atual (0 = sem tentativa em curso) */
  reconnectAttempt: number
  /** Tokens acumulados durante streaming — mostrar em tempo real */
  streamingContent: string
  error: string | null
  /** Preenchido quando o agente solicita aprovação humana */
  hitlPending: HITLPending | null
  /** E7: etapas de raciocínio ReAct acumuladas durante processamento */
  thinkingSteps: string[]
  /** E7: true enquanto o agente está no loop ReAct */
  isThinking: boolean
  /** FAR-2/C: warnings de viés implícito detectados na última resposta */
  fairnessWarnings: string[]
  /** Envia mensagem ao agente especificando o domain e opcionalmente o scope */
  sendMessage: (content: string, domain?: string, scope?: string) => void
  /** Confirma ou rejeita a ação HITL pendente */
  sendApproval: (approved: boolean) => void
  /** FAR-2/C: limpa fairness warnings (após dismiss pelo recrutador) */
  dismissFairnessWarnings: () => void
  connect: () => void
  disconnect: () => void
}

export function useFloatStreaming(
  sessionId: string,
  onComplete: (content: string) => void,
): UseFloatStreamingResult {
  const [hitlPending, setHitlPending] = useState<HITLPending | null>(null)
  const hitlRef = useRef<HITLPending | null>(null)
  const onCompleteRef = useRef(onComplete)

  // E7: estado de pensamentos ReAct
  const [thinkingSteps, setThinkingSteps] = useState<string[]>([])
  const [isThinking, setIsThinking] = useState(false)
  // FAR-2/C: warnings de viés implícito
  const [fairnessWarnings, setFairnessWarnings] = useState<string[]>([])

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  const handleEvent = useCallback((event: StreamingEvent) => {
    switch (event.type) {
      case 'thinking':
        // E7: acumula etapas de raciocínio ReAct
        setIsThinking(true)
        if (event.content) {
          setThinkingSteps(prev => [...prev, event.content as string])
        }
        break

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

      case 'message':
        // resposta final (direto ou pós-HITL) — encerra modo thinking
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
          onCompleteRef.current(event.content)
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
  } = useAgentStreaming(sessionId, {}, handleEvent)

  const sendMessage = useCallback(async (content: string, domain = '', scope?: string) => {
    // E7: limpa etapas de thinking ao enviar nova mensagem
    setThinkingSteps([])
    setIsThinking(false)
    clearTokens()
    const context = scope ? { scope } : {}

    if (isConnected) {
      wsSend(content, context, domain)
      return
    }

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (token) headers['Authorization'] = `Bearer ${token}`

      const res = await fetch('/api/backend-proxy/chat/message', {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: content, domain, session_id: sessionId, context }),
      })
      const data = await res.json()
      if (data.content) {
        onCompleteRef.current(data.content)
      }
    } catch {
      onCompleteRef.current('Erro ao conectar com a LIA. Tente novamente.')
    }
  }, [wsSend, clearTokens, isConnected, sessionId])

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

  return {
    isConnected,
    isStreaming,
    isReconnecting,
    reconnectAttempt,
    streamingContent: tokens,
    error,
    hitlPending,
    thinkingSteps,
    isThinking,
    fairnessWarnings,
    dismissFairnessWarnings,
    sendMessage,
    sendApproval,
    connect,
    disconnect,
  }
}
