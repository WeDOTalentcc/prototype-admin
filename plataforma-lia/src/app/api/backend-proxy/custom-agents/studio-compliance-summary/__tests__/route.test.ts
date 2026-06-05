/**
 * Task #1314 — Proxy studio-compliance-summary (espelho dos factory-based proxies).
 *
 * Garante o contrato de produtor que `StudioComplianceView` consome:
 *   1. `period_days` da query é encaminhado verbatim ao backend FastAPI.
 *   2. O envelope FastAPI `{ok, data, meta}` é desembrulhado — o cliente recebe
 *      só `data` (mesmo padrão de `createProxyHandlers`).
 *   3. Payload "cru" (sem envelope) passa direto, sem mexer.
 *   4. Erros do backend (502/504) são propagados sem mascarar.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import type { NextRequest } from "next/server"

vi.mock("@/lib/api/auth-headers", () => ({
  getAuthHeaders: () => ({ "Content-Type": "application/json" }),
}))

function buildRequest(query = ""): NextRequest {
  return {
    url: `http://localhost/api/backend-proxy/custom-agents/studio-compliance-summary${query}`,
  } as unknown as NextRequest
}

describe("studio-compliance-summary proxy — GET (Task #1314)", () => {
  let originalFetch: typeof globalThis.fetch
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalFetch = globalThis.fetch
    fetchMock = vi.fn()
    globalThis.fetch = fetchMock as unknown as typeof globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  async function loadRoute() {
    return await import("../route")
  }

  it("encaminha period_days e desembrulha o envelope {ok,data,meta}", async () => {
    const payload = { total_executions: 12, trend: [], top_blocked_agents: [] }
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ ok: true, data: payload, meta: {} }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    )

    const { GET } = await loadRoute()
    const res = await GET(buildRequest("?period_days=7"), {
      params: Promise.resolve({}),
    })
    const body = await res.json()

    // Backend recebeu o period_days verbatim.
    const calledUrl = fetchMock.mock.calls[0][0] as string
    expect(calledUrl).toContain("/api/v1/custom-agents/studio/compliance-summary")
    expect(calledUrl).toContain("period_days=7")

    // Cliente recebeu só `data`, sem o envelope.
    expect(res.status).toBe(200)
    expect(body).toEqual(payload)
  })

  it("payload cru (sem envelope) passa direto", async () => {
    const raw = { total_executions: 0 }
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify(raw), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    )

    const { GET } = await loadRoute()
    const res = await GET(buildRequest("?period_days=30"), {
      params: Promise.resolve({}),
    })
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body).toEqual(raw)
  })

  it("erro do backend (504) é propagado sem mascarar", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: "Backend timeout" }), {
        status: 504,
        headers: { "Content-Type": "application/json" },
      }),
    )

    const { GET } = await loadRoute()
    const res = await GET(buildRequest("?period_days=90"), {
      params: Promise.resolve({}),
    })
    const body = await res.json()

    expect(res.status).toBe(504)
    expect(body).toEqual({ detail: "Backend timeout" })
  })
})
