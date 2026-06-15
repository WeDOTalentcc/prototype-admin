/**
 * AgentEventListener — EventSource wrapper for agent lifecycle events (FIX-P0-03).
 *
 * Subscribes to /api/backend-proxy/agent-events/{sessionId} and re-emits
 * typed events to registered listeners. Handles reconnection automatically
 * with exponential backoff; forwards Last-Event-ID for server-side replay.
 *
 * Usage:
 *   const listener = new AgentEventListener("session-abc")
 *   listener.on("agent_action", (ev) => setCurrentAction(ev.action_name))
 *   listener.connect()
 *   // ...
 *   listener.close()
 */

export type AgentEventStatus = "thinking" | "executing" | "complete" | "error"

export interface AgentEventPayload {
  type: string
  event_id: string
  session_id: string
  timestamp: number
  message_id: string
  action_name: string
  status: AgentEventStatus
  payload: Record<string, unknown>
}

export type AgentEventType =
  | "agent_thinking"
  | "agent_action"
  | "agent_action_result"
  | "agent_context_update"

export type AgentEventHandler = (event: AgentEventPayload) => void

interface ListenerMap {
  [eventType: string]: Set<AgentEventHandler>
}

const BASE_BACKOFF_MS = 500
const MAX_BACKOFF_MS = 30_000
const BACKOFF_FACTOR = 2

export class AgentEventListener {
  private readonly sessionId: string
  private readonly baseUrl: string
  private source: EventSource | null = null
  private listeners: ListenerMap = {}
  private lastEventId: string | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private closed = false

  constructor(sessionId: string, baseUrl = "/api/backend-proxy/agent-events") {
    this.sessionId = sessionId
    this.baseUrl = baseUrl
  }

  /** Register a handler for a specific event type. */
  on(eventType: AgentEventType, handler: AgentEventHandler): this {
    if (!this.listeners[eventType]) {
      this.listeners[eventType] = new Set()
    }
    this.listeners[eventType].add(handler)
    return this
  }

  /** Remove a registered handler. */
  off(eventType: AgentEventType, handler: AgentEventHandler): this {
    this.listeners[eventType]?.delete(handler)
    return this
  }

  /** Open the SSE connection. Idempotent: calling while open is a no-op. */
  connect(): void {
    if (this.closed || this.source?.readyState === EventSource.OPEN) return
    this._openSource()
  }

  /** Permanently close the connection and cancel reconnection. */
  close(): void {
    this.closed = true
    this._clearReconnect()
    this._closeSource()
  }

  /** True if the EventSource is currently open. */
  get isConnected(): boolean {
    return this.source?.readyState === EventSource.OPEN
  }

  // ── Private ──────────────────────────────────────────────────────────────

  private _url(): string {
    const base = `${this.baseUrl}/${encodeURIComponent(this.sessionId)}`
    return this.lastEventId
      ? `${base}?last_event_id=${encodeURIComponent(this.lastEventId)}`
      : base
  }

  private _openSource(): void {
    this._closeSource()

    const source = new EventSource(this._url())
    this.source = source

    // EventSource fires generic "message" events by default.
    // The server sends named events (event: agent_action etc.) which the
    // browser exposes as addEventListener on the specific event name.
    const AGENT_EVENT_TYPES: AgentEventType[] = [
      "agent_thinking",
      "agent_action",
      "agent_action_result",
      "agent_context_update",
    ]

    for (const type of AGENT_EVENT_TYPES) {
      source.addEventListener(type, (e: Event) => {
        this._handleMessage(e as MessageEvent)
      })
    }

    // Fallback: also listen to generic "message" events for backends that
    // send all events with the same stream (no explicit `event:` line).
    source.onmessage = (e: MessageEvent) => {
      this._handleMessage(e)
    }

    source.onopen = () => {
      this.reconnectAttempts = 0
    }

    source.onerror = () => {
      if (!this.closed) {
        this._scheduleReconnect()
      }
    }
  }

  private _handleMessage(e: MessageEvent): void {
    try {
      const payload = JSON.parse(e.data) as AgentEventPayload
      if (e.lastEventId) {
        this.lastEventId = e.lastEventId
      } else if (payload.event_id) {
        this.lastEventId = payload.event_id
      }
      const type = payload.type as AgentEventType
      const handlers = this.listeners[type]
      if (handlers) {
        for (const h of handlers) {
          try {
            h(payload)
          } catch (err) {
            console.error("[AgentEventListener] handler error", err)
          }
        }
      }
    } catch (err) {
      console.error("[AgentEventListener] parse error", err)
    }
  }

  private _closeSource(): void {
    if (this.source) {
      this.source.close()
      this.source = null
    }
  }

  private _scheduleReconnect(): void {
    this._clearReconnect()
    this._closeSource()

    const backoff = Math.min(
      BASE_BACKOFF_MS * Math.pow(BACKOFF_FACTOR, this.reconnectAttempts),
      MAX_BACKOFF_MS,
    )
    this.reconnectAttempts++

    this.reconnectTimer = setTimeout(() => {
      if (!this.closed) {
        this._openSource()
      }
    }, backoff)
  }

  private _clearReconnect(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}
