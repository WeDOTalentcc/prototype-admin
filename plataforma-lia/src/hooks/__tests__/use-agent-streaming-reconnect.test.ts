/**
 * P2-E — Testes unitários: WebSocket reconnect automático em useAgentStreaming
 *
 * Camada 2 — Unitária (jsdom)
 * Cobre:
 * 1. isReconnecting=false e reconnectAttempt=0 no estado inicial
 * 2. Após onclose não-intencional → isReconnecting=true, reconnectAttempt=1
 * 3. Após reconexão bem-sucedida → isReconnecting=false, reconnectAttempt=0
 * 4. Backoff exponencial: delay dobra a cada tentativa
 * 5. Após maxReconnectAttempts → isReconnecting=false (deu up)
 * 6. disconnect() cancela timer e reseta isReconnecting
 * 7. Fechamento intencional (code 1000) não dispara reconexão
 * 8. Fechamento intencional (code 1001) não dispara reconexão
 * 9. autoReconnect=false não dispara reconexão
 * 10. reconnectAttempt incrementa a cada tentativa
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useAgentStreaming } from "../ai/use-agent-streaming"

// ── Mock WebSocket ─────────────────────────────────────────────────────────────

class MockWebSocket {
  static OPEN = 1
  static CLOSED = 3

  readyState: number = MockWebSocket.OPEN
  onopen: (() => void) | null = null
  onclose: ((evt: { code: number; reason: string }) => void) | null = null
  onerror: (() => void) | null = null
  onmessage: ((evt: { data: string }) => void) | null = null
  url: string

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  send = vi.fn()
  close = vi.fn((code = 1000) => {
    this.readyState = MockWebSocket.CLOSED
  })

  // Helpers para simular eventos nos testes
  simulateOpen() { this.readyState = MockWebSocket.OPEN; this.onopen?.() }
  simulateClose(code = 1006) { this.readyState = MockWebSocket.CLOSED; this.onclose?.({ code, reason: "" }) }
  simulateError() { this.readyState = MockWebSocket.CLOSED; this.onerror?.() }

  static instances: MockWebSocket[] = []
  static reset() { MockWebSocket.instances = [] }
  static latest(): MockWebSocket { return MockWebSocket.instances[MockWebSocket.instances.length - 1] }
}

// ── Setup ─────────────────────────────────────────────────────────────────────

beforeEach(() => {
  MockWebSocket.reset()
  vi.useFakeTimers()
  // @ts-expect-error — substituir WebSocket global
  global.WebSocket = MockWebSocket
})

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("P2-E — useAgentStreaming: reconnect automático", () => {
  it("1. estado inicial: isReconnecting=false, reconnectAttempt=0", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true })
    )
    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it("2. onclose não-intencional → isReconnecting=true, reconnectAttempt=1", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true, maxReconnectAttempts: 3 })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })

    act(() => { MockWebSocket.latest().simulateClose(1006) })

    expect(result.current.isReconnecting).toBe(true)
    expect(result.current.reconnectAttempt).toBe(1)
  })

  it("3. reconexão bem-sucedida → isReconnecting=false, reconnectAttempt=0", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true, reconnectBaseDelay: 100 })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })
    act(() => { MockWebSocket.latest().simulateClose(1006) })

    expect(result.current.isReconnecting).toBe(true)

    // Avança timer para disparar reconexão
    act(() => { vi.advanceTimersByTime(200) })
    act(() => { MockWebSocket.latest().simulateOpen() })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it("4. backoff exponencial: segundo delay = base * 2", () => {
    const BASE = 500
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", {
        autoReconnect: true,
        maxReconnectAttempts: 5,
        reconnectBaseDelay: BASE,
      })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })

    // Primeira queda → delay = 500ms (BASE * 2^0)
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    expect(result.current.reconnectAttempt).toBe(1)

    // Avança 500ms → dispara reconnect, mas falha
    act(() => { vi.advanceTimersByTime(BASE) })
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    expect(result.current.reconnectAttempt).toBe(2)

    // Segunda queda → delay = 1000ms (BASE * 2^1). Avança só 500ms → não conecta ainda
    act(() => { vi.advanceTimersByTime(BASE) })
    expect(MockWebSocket.instances.length).toBe(2) // sem nova instância

    // Avança mais 500ms → agora sim
    act(() => { vi.advanceTimersByTime(BASE) })
    expect(MockWebSocket.instances.length).toBe(3)
  })

  it("5. esgotou maxReconnectAttempts → isReconnecting=false", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", {
        autoReconnect: true,
        maxReconnectAttempts: 2,
        reconnectBaseDelay: 50,
      })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })

    // Tentativa 1
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    act(() => { vi.advanceTimersByTime(50) })

    // Tentativa 2
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    act(() => { vi.advanceTimersByTime(200) })

    // Esgotou (reconnectCountRef == maxReconnectAttempts agora)
    act(() => { MockWebSocket.latest().simulateClose(1006) })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it("6. disconnect() cancela timer e reseta isReconnecting", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true, reconnectBaseDelay: 1000 })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })
    act(() => { MockWebSocket.latest().simulateClose(1006) })

    expect(result.current.isReconnecting).toBe(true)

    act(() => { result.current.disconnect() })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)

    // Avança timer — não deve haver nova conexão
    const instanceCount = MockWebSocket.instances.length
    act(() => { vi.advanceTimersByTime(2000) })
    expect(MockWebSocket.instances.length).toBe(instanceCount)
  })

  it("7. fechamento intencional (code 1000) não dispara reconexão", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })
    act(() => { MockWebSocket.latest().simulateClose(1000) })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it("8. fechamento intencional (code 1001) não dispara reconexão", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: true })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })
    act(() => { MockWebSocket.latest().simulateClose(1001) })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
  })

  it("9. autoReconnect=false não dispara reconexão", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", { autoReconnect: false })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })
    act(() => { MockWebSocket.latest().simulateClose(1006) })

    expect(result.current.isReconnecting).toBe(false)
    expect(result.current.reconnectAttempt).toBe(0)
    act(() => { vi.advanceTimersByTime(5000) })
    expect(MockWebSocket.instances.length).toBe(1)
  })

  it("10. reconnectAttempt incrementa a cada tentativa", () => {
    const { result } = renderHook(() =>
      useAgentStreaming("session-1", {
        autoReconnect: true,
        maxReconnectAttempts: 5,
        reconnectBaseDelay: 50,
      })
    )
    act(() => { result.current.connect() })
    act(() => { MockWebSocket.latest().simulateOpen() })

    act(() => { MockWebSocket.latest().simulateClose(1006) })
    expect(result.current.reconnectAttempt).toBe(1)

    act(() => { vi.advanceTimersByTime(50) })
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    expect(result.current.reconnectAttempt).toBe(2)

    act(() => { vi.advanceTimersByTime(200) })
    act(() => { MockWebSocket.latest().simulateClose(1006) })
    expect(result.current.reconnectAttempt).toBe(3)
  })
})
