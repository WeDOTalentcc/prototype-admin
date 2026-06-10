"use client"

import { useState, useRef, useCallback, useEffect } from "react"

import type { TransportMode } from "./lia-chat-connection-types"
export type { TransportMode }

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`
    : "ws://127.0.0.1:8001")

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== "undefined" ? window.location.origin : "http://127.0.0.1:8001")

export interface TransportEvent {
  type: string
  content?: string
  message?: string
  tokens_sent?: number
  confidence?: number
  pending_id?: string
  thread_id?: string
  action?: string
  description?: string
  data?: Record<string, unknown>
  fairness_warnings?: string[]
  tool_results?: Array<{
    tool_name?: string
    success?: boolean
    section?: string | null
    field?: string | null
    [key: string]: unknown
  }>
  [key: string]: unknown
}

// PR6 (Task #1006) — Bridge IA→UI: canonical save tools whose successful
// execution by the agent must trigger a settings hub refresh. Exported as
// the single source of truth — sentinel tests import this constant rather
// than re-declaring the list (prevents whitelist drift).
export const SETTINGS_PERSIST_TOOLS: ReadonlySet<string> = new Set<string>([
  "save_company_field",
  "save_company_section",
  "save_hiring_policy",
  "import_benefits_from_data",
  "import_workforce_plan",
])

const TOOL_TO_SECTION: Record<string, string> = {
  save_hiring_policy: "hiring_policies",
  import_benefits_from_data: "benefits",
  import_workforce_plan: "workforce",
}

export function maybeDispatchSettingsUpdated(event: TransportEvent): void {
  if (typeof window === "undefined") return
  if (event.type !== "message") return
  const results = event.tool_results
  if (!Array.isArray(results) || results.length === 0) return

  for (const r of results) {
    if (!r || typeof r !== "object") continue
    const toolName = typeof r.tool_name === "string" ? r.tool_name : ""
    if (!SETTINGS_PERSIST_TOOLS.has(toolName)) continue
    if (r.success === false) continue
    const section =
      (typeof r.section === "string" && r.section) ||
      TOOL_TO_SECTION[toolName] ||
      "profile"
    const detail = {
      origin: "agent" as const,
      source: "agent" as const,
      section,
      field: typeof r.field === "string" ? r.field : undefined,
      tool_name: toolName,
      ts: Date.now(),
    }
    try {
      window.dispatchEvent(new CustomEvent("lia:settings-updated", { detail }))
    } catch {
      // fail-silent — bridge must never break chat transport
    }
  }
}

// FE-1 (wizard panel SSE parity) — Bridge the wizard panel signal to the
// `lia:wizard-stage-payload` window event from the SSE/WS transport, mirroring
// useChatSocket.ts (WS) and useChatMessages.ts (REST) 1:1 so the dynamic panel
// opens regardless of transport. Backend ships the signal in THREE shapes over
// this stream:
//   1. a top-level `wizard_stage` frame (mirrors the WS frame, commit 54f2d48d);
//   2. nested as `ws_stage_payload` on the structured `message` frame (bubble);
//   3. a `panel_update` frame with `panel_type:"wizard_stage"` — the ONLY shape
//      the live chat-page SSE backend (agent_chat_sse.py) emits for the wizard.
//      There `panel_title` carries the `stage` string and `panel_data` carries
//      the inner `data` dict (`serialize_panel_update`), so we re-shape it back
//      into the canonical payload before dispatch.
// Dedup: the same logical payload (thread_id:stage:completeness) is fired at
// most once even if it arrives via more than one shape.
let _lastWizardStageKey: string | null = null

// Hash estável (djb2) de string — barato, determinístico, sem deps. Torna a
// chave de dedup SENSÍVEL AO CONTEÚDO (fix 2026-06-05 painel congelado).
function _djb2(input: string): number {
  let h = 5381
  for (let i = 0; i < input.length; i++) h = ((h << 5) + h + input.charCodeAt(i)) | 0
  return h
}

function dispatchWizardStagePayload(src: Record<string, unknown>): void {
  const stage = src.stage
  if (typeof stage !== "string" || stage.length === 0) return // incompleto — ignora
  const threadId = src.thread_id
  const completeness = (src.completeness as number) ?? 0
  const data = (src.data as Record<string, unknown>) || {}
  const requiresApproval = Boolean(src.requires_approval)
  // Dedup SENSÍVEL AO CONTEÚDO: hash de data + requires_approval. Cross-shape
  // duplicates (mesmo payload via WS+SSE+REST) têm data idêntica -> mesma chave
  // -> deduplica. NOVO turno do MESMO stage tem data diferente -> re-despacha.
  // A chave antiga (thread_id:stage:completeness) era constante dentro de um
  // stage (completeness e por-stage em calculate_completeness), entao congelava
  // o painel no 1o payload (ex.: intake mostrava "Aguardando" mesmo apos o
  // recrutador informar titulo/senioridade). Sensor: useChatTransport.wizard-bridge.
  let dataHash = 0
  try { dataHash = _djb2(JSON.stringify(data)) } catch { dataHash = 0 }
  const key = `${String(threadId ?? "")}:${stage}:${completeness}:${dataHash}:${requiresApproval}`
  if (key === _lastWizardStageKey) return // dedup — payload idêntico já despachado
  _lastWizardStageKey = key
  window.dispatchEvent(
    new CustomEvent("lia:wizard-stage-payload", {
      detail: {
        type: "wizard_stage",
        thread_id: threadId,
        stage,
        data,
        completeness,
        requires_approval: requiresApproval,
      },
    }),
  )
}

export function maybeDispatchWizardStage(event: TransportEvent): void {
  if (typeof window === "undefined") return
  // chat-page path — dedicated top-level SSE/WS frame IS the payload.
  if (event.type === "wizard_stage") {
    dispatchWizardStagePayload(event as unknown as Record<string, unknown>)
    return
  }
  // bubble path — nested inside the structured message frame.
  if (event.type === "message") {
    const nested = (event as unknown as Record<string, unknown>)
      .ws_stage_payload
    if (nested && typeof nested === "object") {
      dispatchWizardStagePayload(nested as Record<string, unknown>)
    }
    return
  }
  // chat-page SSE path — agent_chat_sse.py emits the wizard as a `panel_update`
  // frame (panel_type "wizard_stage"), never a bare `wizard_stage` frame. Mirror
  // the WS hook's bridge: re-shape panel_title→stage + panel_data→data into the
  // canonical payload. (thread_id/completeness/requires_approval are not on this
  // frame; dispatchWizardStagePayload defaults them — the panel opens regardless.)
  if (event.type === "panel_update") {
    const pe = event as unknown as Record<string, unknown>
    if (pe.panel_type === "wizard_stage") {
      const stage = pe.panel_title
      const data = pe.panel_data
      dispatchWizardStagePayload({
        stage,
        thread_id: pe.thread_id,
        data: data && typeof data === "object" ? data : {},
        completeness: pe.completeness,
        requires_approval: pe.requires_approval,
      })
    }
  }
}

export interface UseChatTransportOptions {
  autoReconnect?: boolean
  maxReconnectAttempts?: number
  reconnectBaseDelay?: number
  authToken?: string
  maxSseFailures?: number
}

export interface UseChatTransportResult {
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
  sendMessage: (
    content: string,
    context?: Record<string, unknown>,
    domain?: string,
    metadata?: Record<string, unknown>,
  ) => boolean
  sendRaw: (data: Record<string, unknown>) => void
  sendMessageViaSSE: (
    sessionId: string,
    message: string,
    domain?: string,
    context?: Record<string, unknown>,
    conversationId?: string | null,
    onExhausted?: () => void,
  ) => void
}

export function useChatTransport(
  sessionId: string,
  options: UseChatTransportOptions = {},
  onEvent?: (event: TransportEvent) => void,
): UseChatTransportResult {
  const {
    autoReconnect = true,
    maxReconnectAttempts = 3,
    reconnectBaseDelay = 1000,
    authToken,
    maxSseFailures = 3,
  } = options

  const [tokens, setTokens] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [reconnectAttempt, setReconnectAttempt] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [transportMode, setTransportMode] = useState<TransportMode>("disconnected")

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectCountRef = useRef(0)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const mountedRef = useRef(true)
  const wsFailedPermanentlyRef = useRef(false)
  const sseAbortRef = useRef<AbortController | null>(null)
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const sseFailureCountRef = useRef(0)
  const lastEventIdRef = useRef<string>("")
  const onEventRef = useRef(onEvent)

  useEffect(() => {
    onEventRef.current = onEvent
  }, [onEvent])

  const buildWsUrl = useCallback((): string => {
    const base = WS_BASE_URL.replace(/\/$/, "")
    // UC-P0-19: token must NOT be in the URL — sent as first WS message in onopen.
    return `${base}/api/v1/ws/chat/${sessionId}`
  }, [sessionId])

  const disconnectWs = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
    reconnectCountRef.current = 0
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.onclose = null
      wsRef.current.close(1000, "Client disconnect")
      wsRef.current = null
    }
  }, [])

  const disconnect = useCallback(() => {
    disconnectWs()
    if (sseAbortRef.current) {
      sseAbortRef.current.abort()
      sseAbortRef.current = null
    }
    if (mountedRef.current) {
      setIsConnected(false)
      setIsStreaming(false)
      setIsReconnecting(false)
      setReconnectAttempt(0)
      setTransportMode("disconnected")
    }
  }, [disconnectWs])

  const handleParsedEvent = useCallback((event: TransportEvent) => {
    onEventRef.current?.(event)

    // PR6 (Task #1006) — Bridge IA→UI: when the agent persists settings via
    // canonical save tools, the backend ships a `tool_results` array on the
    // message frame. Dispatch the `lia:settings-updated` CustomEvent with
    // `origin: "agent"` so settings hub cards refresh without a page reload.
    // Out-of-band: never fires for UI-originated saves (those carry
    // `source: "ui"` and are handled by the existing origin guard).
    maybeDispatchSettingsUpdated(event)

    // FE-1 — open the wizard side-panel from the SSE/WS transport, at parity
    // with the WS (useChatSocket.ts) and REST (useChatMessages.ts) paths.
    maybeDispatchWizardStage(event)

    switch (event.type) {
      case "thinking":
        setIsStreaming(true)
        setTokens("")
        break
      case "token":
        setIsStreaming(true)
        if (event.content) {
          setTokens((prev) => prev + event.content)
        }
        break
      case "token_done":
        setIsStreaming(false)
        break
      case "message":
        setIsStreaming(false)
        if (event.content) {
          setTokens(event.content)
        }
        break
      case "error":
        setIsStreaming(false)
        setError(event.message ?? "Erro desconhecido no agente.")
        break
      case "pong":
        break
    }
  }, [])

  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    if (!sessionId) return
    if (wsFailedPermanentlyRef.current) return

    try {
      const ws = new WebSocket(buildWsUrl())
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) return
        // UC-P0-19: send JWT as first message to avoid token in URL/logs
        if (authToken) {
          ws.send(JSON.stringify({ type: "auth", token: authToken }))
        }
        reconnectCountRef.current = 0
        sseFailureCountRef.current = 0
        setIsConnected(true)
        setIsReconnecting(false)
        setReconnectAttempt(0)
        setError(null)
        setTransportMode("ws")
        // UC-P1-29: proactive heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }))
          }
        }, 25000) // 25s under 30s proxy idle timeout
      }

      ws.onmessage = (evt: MessageEvent) => {
        if (!mountedRef.current) return
        try {
          const event = JSON.parse(evt.data as string) as TransportEvent
          handleParsedEvent(event)
        } catch {
          // ignore malformed
        }
      }

      ws.onerror = () => {
        if (!mountedRef.current) return
        setIsConnected(false)
        setIsStreaming(false)
      }

      ws.onclose = (evt: CloseEvent) => {
        if (!mountedRef.current) return
        setIsConnected(false)
        setIsStreaming(false)

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
          reconnectTimerRef.current = setTimeout(connectWs, delay)
        } else if (reconnectCountRef.current >= maxReconnectAttempts) {
          // BUG-AUDIT #277: não declarar isConnected=true em modo SSE "fantasma".
          // Fazê-lo capturava todo envio no sendMessageViaSSE (que aqui costuma
          // falhar em dev via rewrite do Next) e impedia o caminho REST — que
          // funciona de ponta a ponta — de ser acionado em useChatMessages.
          // Mantemos disconnected para liberar o branch REST.
          wsFailedPermanentlyRef.current = true
          if (mountedRef.current) {
            setIsReconnecting(false)
            setReconnectAttempt(0)
            setTransportMode("disconnected")
            setIsConnected(false)
            setError(null)
          }
        }
      }
    } catch {
      // BUG-AUDIT #277: ver comentário acima — não fingir conexão SSE.
      wsFailedPermanentlyRef.current = true
      if (mountedRef.current) {
        setTransportMode("disconnected")
        setIsConnected(false)
        setError(null)
      }
    }
  // UC-P0-19: authToken added to deps so connectWs re-creates when token rotates
  }, [sessionId, authToken, buildWsUrl, autoReconnect, maxReconnectAttempts, reconnectBaseDelay, handleParsedEvent])

  const connect = useCallback(() => {
    wsFailedPermanentlyRef.current = false
    sseFailureCountRef.current = 0
    connectWs()
  }, [connectWs])

  const clearTokens = useCallback(() => setTokens(""), [])

  const sendMessage = useCallback(
    (
      content: string,
      context: Record<string, unknown> = {},
      domain = "",
      metadata?: Record<string, unknown>,
    ): boolean => {
      const ws = wsRef.current
      if (!ws || ws.readyState !== WebSocket.OPEN) return false
      try {
        // PR-A FE — embed metadata into context.metadata so backend
        // rail_a_hint_override.try_hint_route() (Tier -1) can read it.
        // Caller-provided context.metadata wins (idempotent merge).
        const wsContext =
          metadata && !context.metadata
            ? { ...context, metadata }
            : context
        // Top-level metadata is also forwarded as a fallback the WS handler
        // promotes into context.metadata when missing (defense-in-depth).
        const frame: Record<string, unknown> = {
          type: "message",
          content,
          context: wsContext,
          domain,
        }
        if (metadata) frame.metadata = metadata
        ws.send(JSON.stringify(frame))
        return true
      } catch {
        // Task #383 (F2): se ws.send lança (socket entrou em CLOSING entre o
        // check e o send), reportar falha pra que useChatMessages caia no REST
        // ao invés de deixar o usuário com spinner eterno.
        return false
      }
    },
    [],
  )

  const sendRaw = useCallback((data: Record<string, unknown>) => {
    if (wsFailedPermanentlyRef.current) {
      fetch(`${API_BASE_URL}/api/v1/chat/action`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify(data),
        credentials: "include",
      }).catch((err) => {
        console.warn("[useChatTransport] SSE sendRaw fallback failed:", err)
      })
      return
    }
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify(data))
  }, [authToken])

  const sendMessageViaSSE = useCallback(
    (
      sseSessionId: string,
      message: string,
      domain = "recruiter_assistant",
      context: Record<string, unknown> = {},
      conversationId: string | null = null,
      onExhausted?: () => void,
    ) => {
      if (sseAbortRef.current) {
        sseAbortRef.current.abort()
      }

      const controller = new AbortController()
      sseAbortRef.current = controller

      setIsStreaming(true)
      setTokens("")
      setError(null)

      // SSE inactivity watchdog — se nenhum dado chegar em 90s, aborta e surface erro.
      // O reader.read() pode travar indefinidamente se o backend parar de enviar
      // sem fechar o stream (done=true nunca chega → isThinking fica preso).
      const SSE_INACTIVITY_TIMEOUT_MS = 90_000
      let inactivityTimerRef: ReturnType<typeof setTimeout> | null = null

      const resetInactivity = () => {
        if (inactivityTimerRef) clearTimeout(inactivityTimerRef)
        inactivityTimerRef = setTimeout(() => {
          if (mountedRef.current) {
            setIsStreaming(false)
            onEventRef.current?.({
              type: "error",
              message: "Sem resposta do servidor por 90 segundos. Tente novamente.",
            } as TransportEvent)
          }
          controller.abort()
        }, SSE_INACTIVITY_TIMEOUT_MS)
      }

      // start watchdog immediately
      resetInactivity()

      // BUG-AUDIT #277 / H7: rastrear se um evento terminal (message/clarification/error)
      // foi recebido. Se o stream fechar (done=true) sem terminal, emitimos "error"
      // pra destravar isThinking em useChatSocket.
      let receivedTerminal = false
      const wrappedHandleParsedEvent = (event: TransportEvent) => {
        if (event.type === "message" || event.type === "clarification" || event.type === "error") {
          receivedTerminal = true
        }
        handleParsedEvent(event)
      }

      // AUD-4 1b-c: levanta approve_pending_id do context pro top-level do
      // body (o backend le req.approve_pending_id). Mantem o context limpo.
      const { approve_pending_id: _approvePendingId, ...ctxRest } =
        (context as Record<string, unknown>) || {}
      const body = JSON.stringify({
        message,
        domain,
        context: ctxRest,
        conversation_id: conversationId,
        approve_pending_id: (_approvePendingId as string | null) ?? null,
      })

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      }
      if (authToken) {
        headers["Authorization"] = `Bearer ${authToken}`
      }
      if (lastEventIdRef.current) {
        headers["Last-Event-ID"] = lastEventIdRef.current
      }

      const attemptSSE = (attempt: number) => {
        fetch(`/api/backend-proxy/chat/${sseSessionId}/stream`, {
          method: "POST",
          headers: {
            ...headers,
            ...(lastEventIdRef.current
              ? { "Last-Event-ID": lastEventIdRef.current }
              : {}),
          },
          body,
          signal: controller.signal,
          credentials: "include",
        })
          .then(async (response) => {
            if (!response.ok) {
              throw new Error(`SSE request failed: ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) throw new Error("No response body")

            const decoder = new TextDecoder()
            let buffer = ""

            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })
              resetInactivity() // reset watchdog on each received chunk
              const lines = buffer.split("\n")
              buffer = lines.pop() || ""

              for (const line of lines) {
                if (line.startsWith("id: ")) {
                  lastEventIdRef.current = line.slice(4).trim()
                } else if (line.startsWith("data: ")) {
                  const jsonStr = line.slice(6)
                  try {
                    const event = JSON.parse(jsonStr) as TransportEvent
                    if (mountedRef.current) {
                      wrappedHandleParsedEvent(event)
                    }
                  } catch {
                    // ignore malformed
                  }
                }
              }
            }

            if (inactivityTimerRef) clearTimeout(inactivityTimerRef)
            sseFailureCountRef.current = 0
            if (mountedRef.current) {
              setIsStreaming(false)
              // BUG-AUDIT #277 / H7: fechamento silencioso — garantir que
              // isThinking/streaming sejam desligados mesmo sem evento terminal.
              if (!receivedTerminal) {
                onEventRef.current?.({
                  type: "error",
                  message: "Resposta incompleta do servidor.",
                } as TransportEvent)
              }
            }
          })
          .catch((err) => {
            if (inactivityTimerRef) clearTimeout(inactivityTimerRef)
            if (err.name === "AbortError") return
            sseFailureCountRef.current += 1

            if (!mountedRef.current) return

            if (sseFailureCountRef.current < maxSseFailures) {
              const retryDelay = reconnectBaseDelay * Math.pow(2, attempt)
              setError(
                `Erro na conexão SSE (tentativa ${sseFailureCountRef.current}/${maxSseFailures}). Reconectando...`,
              )
              reconnectTimerRef.current = setTimeout(
                () => attemptSSE(attempt + 1),
                retryDelay,
              )
            } else if (onExhausted) {
              // 0.3a: esgotou SSE -> fallback de transporte (reenvia via REST no caller).
              setIsStreaming(false)
              setError(null)
              onExhausted?.()
            } else {
              setIsStreaming(false)
              setError(
                "Não foi possível conectar ao servidor. Verifique sua conexão.",
              )
              setIsConnected(false)
              setTransportMode("disconnected")
              // BUG-AUDIT #277 / H7: propagar erro pra useChatSocket limpar
              // isThinking — senão o bubble "LIA digitando" fica preso.
              onEventRef.current?.({
                type: "error",
                message: "Não foi possível conectar ao servidor.",
              } as TransportEvent)
            }
          })
      }

      attemptSSE(0)
    },
    [authToken, handleParsedEvent, maxSseFailures, reconnectBaseDelay],
  )

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
    transportMode,
    connect,
    disconnect,
    clearTokens,
    sendMessage,
    sendRaw,
    sendMessageViaSSE,
  }
}
