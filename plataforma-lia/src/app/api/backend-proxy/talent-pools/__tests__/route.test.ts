/**
 * Bug "Banco criado mas não foi possível abrir" (P1).
 *
 * Root cause: o backend POST /api/v1/talent_pools retorna {"data": <jsonapi>}
 * e o ResponseEnvelopeMiddleware global re-embrulha em
 * {ok:true, data:{data:{id}}, meta:{}}. A rota proxy hand-rolled (res.text()
 * passthrough) NÃO desembrulhava, ao contrário da canônica createProxyHandlers
 * (proxy-handler.ts:265). O FE lia data.data.id = objeto interno {data:{...}}
 * cujo .id é undefined → caía no fallback "não foi possível abrir".
 *
 * Sensor: confirma que a rota desembrulha o envelope (sucesso) tanto no POST
 * (create → data.data.id resolve) quanto no GET (list → data.data é array).
 */
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { NextRequest } from "next/server"

vi.mock("@/lib/api/auth-headers", () => ({
  getAuthHeaders: () => ({ "Content-Type": "application/json" }),
}))

describe("talent-pools proxy — desembrulha envelope FastAPI", () => {
  let originalFetch: typeof globalThis.fetch
  beforeEach(() => {
    originalFetch = globalThis.fetch
  })
  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  it("POST create: {ok,data:{data:{id}},meta} → proxy retorna {data:{id}} (data.data.id resolve)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          data: { data: { id: "pool-123", type: "talent_pool", attributes: { name: "X" } } },
          meta: { request_id: "r1" },
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      ),
    ) as typeof globalThis.fetch

    const { POST } = await import("../route")
    const req = new NextRequest("http://localhost/api/backend-proxy/talent-pools", {
      method: "POST",
      body: JSON.stringify({ talent_pool: { name: "X" } }),
      headers: { "content-type": "application/json" },
    })
    const res = await POST(req)
    const body = (await res.json()) as Record<string, any>

    expect(res.ok).toBe(true) // createProxyHandlers normaliza sucesso para 200; FE usa res.ok
    expect(body.data.id).toBe("pool-123")
  })

  it("GET list: {ok,data:{data:[...]},meta} → proxy retorna {data:[...]} (data.data é array)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          ok: true,
          data: { data: [{ id: "p1", type: "talent_pool", attributes: { name: "A" } }] },
          meta: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    ) as typeof globalThis.fetch

    const { GET } = await import("../route")
    const req = new NextRequest("http://localhost/api/backend-proxy/talent-pools")
    const res = await GET(req)
    const body = (await res.json()) as Record<string, any>

    expect(res.status).toBe(200)
    expect(Array.isArray(body.data)).toBe(true)
    expect(body.data[0].id).toBe("p1")
  })
})
