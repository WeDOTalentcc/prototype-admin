/**
 * useAgentStreaming — recebe tokens LangGraph em tempo real via WebSocket.
 *
 * Conecta ao endpoint WS do backend (/ws/chat/{session_id}) e escuta:
 *   { type: "token",      content: "..." }  — token incremental do LLM
 *   { type: "token_done", tokens_sent: N }  — streaming concluído
 *   { type: "message",    content: "..." }  — resposta final completa
 *   { type: "thinking" }                    — agente processando
 *   { type: "error",      message: "..." }  — erro no agente
 *   { type: "pong" }                        — keep-alive
 *
 * Compatível com Vue/Nuxt: interface { tokens, isStreaming, connect, disconnect }
 * mapeia diretamente para composable `useAgentStreaming()`.
 *
 * Uso:
 *   const { tokens, isStreaming, connect, disconnect } = useAgentStreaming(sessionId)
 *   connect()  // abre conexão WS
 *   // tokens é atualizado incrementalmente conforme chegam tokens
 *   disconnect()  // fecha conexão ao desmontar
 */

import { useState, useRef, useCallback, useEffect } from 'react'

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.hostname}:8000`
    : 'ws://127.0.0.1:8000')

export type StreamingEventType =
  | 'token'
  | 'token_done'
  | 'message'
  | 'thinking'
  | 'error'
  | 'pong'
  | 'approval_required'
  | 'approval_confirmed'
  | 'plan_progress'
  | 'clarification'
  | 'panel_update'
  | 'background_task_update'

export interface StreamingEvent {
  type: StreamingEventType
  content?: string
  message?: string
  tokens_sent?: number
  confidence?: number
  // HITL fields
  pending_id?: string
  thread_id?: string
  action?: string
  description?: string
  data?: Record<string, unknown>
  // FAR-2/C: fairness warnings visíveis ao recrutador
  fairness_warnings?: string[]
}

export interface UseAgentStreamingOptions {
  /** Reconecta automaticamente se a conexão cair (default: true) */
  autoReconnect?: boolean
  /** Máximo de tentativas de reconexão (default: 3) */
  maxReconnectAttempts?: number
  /** Delay base entre reconexões em ms (default: 1000) */
  reconnectBaseDelay?: number
  /** Token JWT para autenticação WS */
  authToken?: string
}

export interface UseAgentStreamingResult {
  /** Tokens acumulados da resposta atual */
  tokens: string
  /** true enquanto o streaming está ativo */
  isStreaming: boolean
  /** true quando a conexão WS está aberta */
  isConnected: boolean
  /** true enquanto aguarda para reconectar (backoff ativo) */
  isReconnecting: boolean
  /** Número da tentativa de reconexão atual (0 = sem tentativa em curso) */
  reconnectAttempt: number
  /** Último erro recebido, ou null */
  error: string | null
  /** Abre a conexão WS */
  connect: () => void
  /** Fecha a conexão WS */
  disconnect: () => void
  /** Limpa os tokens acumulados */
  clearTokens: () => void
  /**
   * Envia uma mensagem ao agente via WebSocket.
   * O backend responde com thinking → token* → token_done → message.
   */
  sendMessage: (content: string, context?: Record<string, unknown>, domain?: string) => void
  /**
   * Envia um payload arbitrário via WebSocket (usado para HITL approval_response).
   */
  sendRaw: (data: Record<string, unknown>) => void
  /** Callback chamado ao receber cada evento (opcional) */
  onEvent?: (event: StreamingEvent) => void
}

export function useAgentStreaming(
  sessionId: string,
  options: UseAgentStreamingOptions = {},
  onEvent?: (event: StreamingEvent) => void
): UseAgentStreamingResult {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 3,
    reconnectBaseDelay = 1000,
    authToken,
  } = options

  const [tokens, setTokens] = useState<string>('')
  const [isStreaming, setIsStreaming] = useState<boolean>(false)
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isReconnecting, setIsReconnecting] = useState<boolean>(false)
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef<number>(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef<boolean>(true)

  const buildWsUrl = useCallback((): string => {
    const base = WS_BASE_URL.replace(/\/$/, '')
    const url = `${base}/ws/chat/${sessionId}`
    return authToken ? `${url}?token=${encodeURIComponent(authToken)}` : url
  }, [sessionId, authToken])

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    reconnectCountRef.current = 0
    if (wsRef.current) {
      wsRef.current.onclose = null  // evitar reconexão ao fechar manualmente
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }
    if (mountedRef.current) {
      setIsConnected(false)
      setIsStreaming(false)
      setIsReconnecting(false)
      setReconnectAttempt(0)
    }
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (!sessionId) return

    try {
      const ws = new WebSocket(buildWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        reconnectCountRef.current = 0
        setIsConnected(true)
        setIsReconnecting(false)
        setReconnectAttempt(0)
        setError(null)
      }

      ws.onmessage = (evt: MessageEvent) => {
        if (!mountedRef.current) return

        let event: StreamingEvent
        try {
          event = JSON.parse(evt.data as string) as StreamingEvent
        } catch {
          return
        }

        onEvent?.(event)

        switch (event.type) {
          case 'thinking':
            setIsStreaming(true)
            setTokens('')
            break

          case 'token':
            setIsStreaming(true)
            if (event.content) {
              setTokens(prev => prev + event.content)
            }
            break

          case 'token_done':
            setIsStreaming(false)
            break

          case 'message':
            setIsStreaming(false)
            if (event.content) {
              setTokens(event.content)
            }
            break

          case 'error':
            setIsStreaming(false)
            setError(event.message ?? 'Erro desconhecido no agente.')
            break

          case 'pong':
            // keep-alive, nenhuma ação necessária
            break
        }
      }

      ws.onerror = () => {
        if (!mountedRef.current) return
        setError('Erro na conexão WebSocket.')
        setIsConnected(false)
        setIsStreaming(false)
      }

      ws.onclose = (evt: CloseEvent) => {
        if (!mountedRef.current) return
        setIsConnected(false)
        setIsStreaming(false)

        // Reconexão automática (exceto fechamento intencional 1000/1001)
        if (
          autoReconnect &&
          evt.code !== 1000 &&
          evt.code !== 1001 &&
          reconnectCountRef.current < maxReconnectAttempts
        ) {
          const attempt = reconnectCountRef.current + 1
          const delay = reconnectBaseDelay * Math.pow(2, reconnectCountRef.current)
          reconnectCountRef.current = attempt
          if (mountedRef.current) {
            setIsReconnecting(true)
            setReconnectAttempt(attempt)
          }
          reconnectTimerRef.current = setTimeout(connect, delay)
        } else if (reconnectCountRef.current >= maxReconnectAttempts) {
          // Esgotou tentativas — sinaliza erro permanente
          if (mountedRef.current) {
            setIsReconnecting(false)
            setReconnectAttempt(0)
          }
        }
      }
    } catch (err) {
      setError('Falha ao iniciar conexão WebSocket.')
      setIsConnected(false)
    }
  }, [sessionId, buildWsUrl, autoReconnect, maxReconnectAttempts, reconnectBaseDelay, onEvent])

  const clearTokens = useCallback(() => {
    setTokens('')
  }, [])

  /**
   * Envia uma mensagem ao agente via WebSocket.
   * Formato esperado pelo endpoint /ws/chat/{session_id}:
   *   { type: "message", content: "...", context: {...}, domain: "..." }
   */
  const sendMessage = useCallback((
    content: string,
    context: Record<string, unknown> = {},
    domain = '',
  ) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }
    ws.send(JSON.stringify({ type: 'message', content, context, domain }))
  }, [])

  /**
   * Envia um payload arbitrário via WebSocket.
   * Usado para HITL: { type: "approval_response", approved, thread_id, pending_id }
   */
  const sendRaw = useCallback((data: Record<string, unknown>) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      return
    }
    ws.send(JSON.stringify(data))
  }, [])

  // Cleanup ao desmontar
  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      disconnect()
    }
  }, [disconnect])

  return {
    tokens,
    isStreaming,
    isConnected,
    isReconnecting,
    reconnectAttempt,
    error,
    connect,
    disconnect,
    clearTokens,
    sendMessage,
    sendRaw,
  }
}
