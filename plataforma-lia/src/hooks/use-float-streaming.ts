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
  /** Tokens acumulados durante streaming — mostrar em tempo real */
  streamingContent: string
  error: string | null
  /** Preenchido quando o agente solicita aprovação humana */
  hitlPending: HITLPending | null
  /** Envia mensagem ao agente especificando o domain */
  sendMessage: (content: string, domain?: string) => void
  /** Confirma ou rejeita a ação HITL pendente */
  sendApproval: (approved: boolean) => void
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

  useEffect(() => {
    onCompleteRef.current = onComplete
  }, [onComplete])

  const handleEvent = useCallback((event: StreamingEvent) => {
    switch (event.type) {
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
        // resposta final (direto ou pós-HITL)
        hitlRef.current = null
        setHitlPending(null)
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
    error,
    connect,
    disconnect,
    sendMessage: wsSend,
    sendRaw,
    clearTokens,
  } = useAgentStreaming(sessionId, {}, handleEvent)

  const sendMessage = useCallback((content: string, domain = '') => {
    clearTokens()
    wsSend(content, {}, domain)
  }, [wsSend, clearTokens])

  const sendApproval = useCallback((approved: boolean) => {
    const pending = hitlRef.current
    if (!pending) return
    sendRaw({
      type: 'approval_response',
      approved,
      thread_id: pending.threadId,
      pending_id: pending.pendingId,
    })
    if (!approved) {
      // rejeição imediata — limpa o estado sem aguardar backend
      hitlRef.current = null
      setHitlPending(null)
    }
  }, [sendRaw])

  return {
    isConnected,
    isStreaming,
    streamingContent: tokens,
    error,
    hitlPending,
    sendMessage,
    sendApproval,
    connect,
    disconnect,
  }
}
