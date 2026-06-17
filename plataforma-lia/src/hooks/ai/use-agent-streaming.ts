/**
 * useAgentStreaming — recebe tokens LangGraph em tempo real via WebSocket/SSE.
 *
 * Conecta ao endpoint WS do backend (/api/v1/ws/chat/{session_id}) e escuta:
 *   { type: "token",      content: "..." }  — token incremental do LLM
 *   { type: "token_done", tokens_sent: N }  — streaming concluído
 *   { type: "message",    content: "..." }  — resposta final completa
 *   { type: "thinking" }                    — agente processando
 *   { type: "error",      message: "..." }  — erro no agente
 *   { type: "pong" }                        — keep-alive
 *
 * Quando WebSocket falha após tentativas de reconexão, faz fallback
 * automático para SSE via useChatTransport.
 *
 * Compatível com Vue/Nuxt: interface { tokens, isStreaming, connect, disconnect }
 * mapeia diretamente para composable `useAgentStreaming()`.
 */

import { useChatTransport, type TransportEvent, type TransportMode } from '@/hooks/chat/useChatTransport'

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
  | 'tool_started'
  | 'tool_finished'
  | 'reasoning_step'

export type StreamingEvent = TransportEvent & {
  type: StreamingEventType
}

export interface UseAgentStreamingOptions {
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectBaseDelay?: number
  authToken?: string
}

export interface UseAgentStreamingResult {
  tokens: string
  isStreaming: boolean
  isConnected: boolean
  isReconnecting: boolean
  reconnectAttempt: number
  error: string | null
  transportMode: TransportMode
  connect: () => void
  disconnect: () => void
  clearTokens: () => void
  sendMessage: (content: string, context?: Record<string, unknown>, domain?: string) => boolean
  sendRaw: (data: Record<string, unknown>) => void
  sendMessageViaSSE: (
    sessionId: string,
    message: string,
    domain?: string,
    context?: Record<string, unknown>,
    conversationId?: string | null,
  ) => void
}

export function useAgentStreaming(
  sessionId: string,
  options: UseAgentStreamingOptions = {},
  onEvent?: (event: StreamingEvent) => void
): UseAgentStreamingResult {
  return useChatTransport(sessionId, options, onEvent as ((event: TransportEvent) => void) | undefined)
}
