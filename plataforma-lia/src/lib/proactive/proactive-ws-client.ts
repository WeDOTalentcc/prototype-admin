/**
 * WT-2022: WebSocket client canonical pra ProactiveHints.
 *
 * Lifecycle:
 * - Connect com JWT em query param.
 * - Send {type: "ping"} a cada 30s pra keepalive.
 * - Receive {type: "hint", data: ...} → invoke onHint(data).
 * - Receive {type: "pong"} → no-op.
 * - On close/error: auto-reconnect com backoff exponencial (1s, 2s, 4s, ...
 *   capped em 30s). Cleanup function cancela tudo.
 *
 * Degraded mode: se WS falhar persistentemente, hook frontend continua
 * com SWR polling 60s (fallback canonical, não-degradado funcionalmente).
 */
"use client"

import type { ProactiveHint } from "@/hooks/proactive/use-proactive-hints"

export interface ProactiveWSOptions {
  /** Invocado para cada `{type: "hint", data}` recebido do server. */
  onHint: (hint: ProactiveHint) => void
  /** Opcional: chamado em erros (connect/onerror). */
  onError?: (err: unknown) => void
  /**
   * Override do token getter pra testes / SSR. Default: lê de
   * localStorage("auth_token") OU cookie httpOnly compartilhado com REST.
   */
  getToken?: () => string | null
}

interface WSMessage {
  type: string
  data?: unknown
}

const PING_INTERVAL_MS = 30_000
const MAX_BACKOFF_MS = 30_000
const INITIAL_BACKOFF_MS = 1_000

function defaultGetToken(): string | null {
  if (typeof window === "undefined") return null
  // Canonical: REST API usa cookie httpOnly que WS não acessa via JS.
  // Fallback para localStorage("auth_token") que algumas surfaces preenchem
  // pós-login. Caller pode passar `getToken` custom para Rails JWT pipeline.
  try {
    return window.localStorage.getItem("auth_token")
  } catch {
    return null
  }
}

function buildWsUrl(token: string): string {
  if (typeof window === "undefined") {
    throw new Error("connectProactiveWS chamado em ambiente sem window")
  }
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:"
  const encoded = encodeURIComponent(token)
  return `${proto}//${window.location.host}/ws/proactive-hints?token=${encoded}`
}

export function connectProactiveWS(opts: ProactiveWSOptions): () => void {
  const getToken = opts.getToken ?? defaultGetToken
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null
  let reconnectAttempt = 0
  let cancelled = false

  const clearTimers = () => {
    if (pingTimer !== null) {
      clearInterval(pingTimer)
      pingTimer = null
    }
    if (reconnectTimer !== null) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  const scheduleReconnect = () => {
    if (cancelled) return
    const delay = Math.min(
      INITIAL_BACKOFF_MS * 2 ** reconnectAttempt,
      MAX_BACKOFF_MS,
    )
    reconnectAttempt += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  const connect = () => {
    if (cancelled) return
    const token = getToken()
    if (!token) {
      // Sem token, não tem como conectar. Hook fallback (polling) cobre.
      opts.onError?.(new Error("ProactiveWS: no auth token available"))
      scheduleReconnect()
      return
    }

    let url: string
    try {
      url = buildWsUrl(token)
    } catch (err) {
      opts.onError?.(err)
      return
    }

    try {
      ws = new WebSocket(url)
    } catch (err) {
      opts.onError?.(err)
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      reconnectAttempt = 0
      pingTimer = setInterval(() => {
        if (ws !== null && ws.readyState === WebSocket.OPEN) {
          try {
            ws.send(JSON.stringify({ type: "ping" }))
          } catch {
            // ignore — onclose vai disparar reconnect
          }
        }
      }, PING_INTERVAL_MS)
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed = JSON.parse(event.data as string) as WSMessage
        if (parsed.type === "hint" && parsed.data !== undefined) {
          opts.onHint(parsed.data as ProactiveHint)
        }
        // type === "pong": no-op (keepalive ack)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      clearTimers()
      ws = null
      if (cancelled) return
      scheduleReconnect()
    }

    ws.onerror = (err: Event) => {
      opts.onError?.(err)
      // ws.onclose dispara depois automaticamente — não precisa scheduleReconnect aqui
    }
  }

  connect()

  return () => {
    cancelled = true
    clearTimers()
    if (ws !== null) {
      try {
        ws.close(1000, "client cleanup")
      } catch {
        // ignore
      }
      ws = null
    }
  }
}
