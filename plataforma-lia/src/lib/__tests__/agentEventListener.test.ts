/**
 * Tests for AgentEventListener (FIX-P0-03).
 *
 * 10 test cases:
 *  1.  Creates EventSource with correct URL
 *  2.  Parses message and calls registered handler
 *  3.  Multiple handlers for same event type called
 *  4.  off() removes handler
 *  5.  Unknown event type ignored (no crash)
 *  6.  close() stops EventSource and cancels reconnect
 *  7.  Reconnect scheduled on error
 *  8.  lastEventId forwarded to URL on reconnect
 *  9.  Handler exception does not crash listener
 * 10.  Multiple event types routed correctly
 */

import { describe, test, expect, beforeAll, afterEach, vi, type Mock } from "vitest"
import { AgentEventListener, AgentEventPayload } from "../agentEventListener"

// ─── EventSource mock ────────────────────────────────────────────────────────

interface MockEventSourceInstance {
  url: string
  readyState: number
  close: Mock
  onopen: ((e: Event) => void) | null
  onerror: ((e: Event) => void) | null
  onmessage: ((e: MessageEvent) => void) | null
  eventListeners: Map<string, ((e: Event) => void)[]>
  addEventListener: Mock
  dispatchEvent: (type: string, data: string, lastEventId?: string) => void
}

const mockInstances: MockEventSourceInstance[] = []

class MockEventSource implements MockEventSourceInstance {
  static readonly OPEN = 1
  static readonly CLOSED = 2

  url: string
  readyState = MockEventSource.OPEN
  onopen: ((e: Event) => void) | null = null
  onerror: ((e: Event) => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null
  eventListeners: Map<string, ((e: Event) => void)[]> = new Map()
  close: Mock = vi.fn(() => { this.readyState = MockEventSource.CLOSED })
  addEventListener: Mock = vi.fn((type: string, handler: (e: Event) => void) => {
    if (!this.eventListeners.has(type)) this.eventListeners.set(type, [])
    this.eventListeners.get(type)!.push(handler)
  })

  constructor(url: string) {
    this.url = url
    mockInstances.push(this)
  }

  dispatchEvent(type: string, data: string, lastEventId = ""): void {
    const event = new MessageEvent(type, { data, lastEventId })
    const handlers = this.eventListeners.get(type) ?? []
    for (const h of handlers) h(event)
    if (type === "message" && this.onmessage) this.onmessage(event)
  }
}

// Install mock globally
beforeAll(() => {
  ;(global as unknown as Record<string, unknown>).EventSource = MockEventSource
})

afterEach(() => {
  mockInstances.length = 0
  vi.clearAllTimers()
})

// ─── Test cases ───────────────────────────────────────────────────────────────

describe("AgentEventListener", () => {
  test("1. Creates EventSource with correct URL", () => {
    const listener = new AgentEventListener("session-xyz")
    listener.connect()

    expect(mockInstances.length).toBe(1)
    expect(mockInstances[0].url).toContain("session-xyz")
    listener.close()
  })

  test("2. Parses message and calls registered handler", () => {
    const listener = new AgentEventListener("s-1")
    const handler = vi.fn()
    listener.on("agent_thinking", handler)
    listener.connect()

    const payload: AgentEventPayload = {
      type: "agent_thinking",
      event_id: "evt-1",
      session_id: "s-1",
      timestamp: 1000,
      message_id: "msg-1",
      action_name: "",
      status: "thinking",
      payload: {},
    }
    mockInstances[0].dispatchEvent("agent_thinking", JSON.stringify(payload))

    expect(handler).toHaveBeenCalledWith(payload)
    listener.close()
  })

  test("3. Multiple handlers for same event type all called", () => {
    const listener = new AgentEventListener("s-2")
    const h1 = vi.fn()
    const h2 = vi.fn()
    listener.on("agent_action", h1).on("agent_action", h2)
    listener.connect()

    const payload: AgentEventPayload = {
      type: "agent_action",
      event_id: "evt-2",
      session_id: "s-2",
      timestamp: 2000,
      message_id: "",
      action_name: "navigate",
      status: "executing",
      payload: {},
    }
    mockInstances[0].dispatchEvent("agent_action", JSON.stringify(payload))

    expect(h1).toHaveBeenCalledWith(payload)
    expect(h2).toHaveBeenCalledWith(payload)
    listener.close()
  })

  test("4. off() removes handler", () => {
    const listener = new AgentEventListener("s-3")
    const handler = vi.fn()
    listener.on("agent_action", handler)
    listener.off("agent_action", handler)
    listener.connect()

    const payload: AgentEventPayload = {
      type: "agent_action",
      event_id: "e",
      session_id: "s-3",
      timestamp: 0,
      message_id: "",
      action_name: "test",
      status: "executing",
      payload: {},
    }
    mockInstances[0].dispatchEvent("agent_action", JSON.stringify(payload))
    expect(handler).not.toHaveBeenCalled()
    listener.close()
  })

  test("5. Unknown/extra event type is ignored without crash", () => {
    const listener = new AgentEventListener("s-4")
    listener.connect()

    expect(() => {
      mockInstances[0].dispatchEvent(
        "message",
        JSON.stringify({ type: "some_unknown_type", event_id: "x", session_id: "s-4",
                         timestamp: 0, message_id: "", action_name: "", status: "thinking", payload: {} }),
      )
    }).not.toThrow()

    listener.close()
  })

  test("6. close() stops EventSource", () => {
    const listener = new AgentEventListener("s-5")
    listener.connect()
    const src = mockInstances[0]

    listener.close()
    expect(src.close).toHaveBeenCalled()
    expect(listener.isConnected).toBe(false)
  })

  test("7. Reconnect is scheduled on error", () => {
    vi.useFakeTimers()
    const listener = new AgentEventListener("s-6")
    listener.connect()

    // Trigger error
    if (mockInstances[0].onerror) mockInstances[0].onerror(new Event("error"))

    // After timer fires, a new EventSource should be created
    vi.runAllTimers()
    expect(mockInstances.length).toBeGreaterThan(1)

    listener.close()
    vi.useRealTimers()
  })

  test("8. lastEventId forwarded in URL after reconnect", () => {
    vi.useFakeTimers()
    const listener = new AgentEventListener("s-7")
    listener.connect()

    // Dispatch an event with a lastEventId
    const payload: AgentEventPayload = {
      type: "agent_thinking",
      event_id: "evt-last",
      session_id: "s-7",
      timestamp: 0,
      message_id: "",
      action_name: "",
      status: "thinking",
      payload: {},
    }
    mockInstances[0].dispatchEvent("agent_thinking", JSON.stringify(payload), "evt-last")

    // Trigger reconnect
    if (mockInstances[0].onerror) mockInstances[0].onerror(new Event("error"))
    vi.runAllTimers()

    const newUrl = mockInstances[mockInstances.length - 1].url
    expect(newUrl).toContain("evt-last")

    listener.close()
    vi.useRealTimers()
  })

  test("9. Handler exception does not crash listener", () => {
    const listener = new AgentEventListener("s-8")
    listener.on("agent_thinking", () => { throw new Error("handler crashed") })
    listener.connect()

    const payload: AgentEventPayload = {
      type: "agent_thinking",
      event_id: "e",
      session_id: "s-8",
      timestamp: 0,
      message_id: "",
      action_name: "",
      status: "thinking",
      payload: {},
    }
    expect(() => {
      mockInstances[0].dispatchEvent("agent_thinking", JSON.stringify(payload))
    }).not.toThrow()

    listener.close()
  })

  test("10. Multiple event types routed to correct handlers", () => {
    const listener = new AgentEventListener("s-9")
    const thinkingH = vi.fn()
    const actionH = vi.fn()
    const resultH = vi.fn()
    listener
      .on("agent_thinking", thinkingH)
      .on("agent_action", actionH)
      .on("agent_action_result", resultH)
    listener.connect()

    const src = mockInstances[0]
    const mkPayload = (type: string): string =>
      JSON.stringify({
        type, event_id: "e", session_id: "s-9", timestamp: 0,
        message_id: "", action_name: "", status: "complete", payload: {},
      })

    src.dispatchEvent("agent_thinking", mkPayload("agent_thinking"))
    src.dispatchEvent("agent_action", mkPayload("agent_action"))
    src.dispatchEvent("agent_action_result", mkPayload("agent_action_result"))

    expect(thinkingH).toHaveBeenCalledTimes(1)
    expect(actionH).toHaveBeenCalledTimes(1)
    expect(resultH).toHaveBeenCalledTimes(1)

    listener.close()
  })
})
