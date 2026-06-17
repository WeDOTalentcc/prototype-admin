import { describe, it, expect, vi, beforeEach } from "vitest"

vi.mock("next/headers", () => ({
  cookies: vi.fn(async () => ({ get: () => undefined, set: () => {} })),
}))
vi.mock("@/lib/api/auth-headers", () => ({
  getAuthHeaders: () => ({ Authorization: "Bearer test" }),
}))

import { proxyFetchWithRetry } from "../proxy-fetch-with-retry"

const fakeReq = { headers: new Headers() } as never

describe("proxyFetchWithRetry — bound de duração (audit 2026-06-03 #6 FE)", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("retorna 504 sintético quando o backend estoura o timeout (não pendura → evita 502 do gateway)", async () => {
    const timeoutErr = Object.assign(new Error("timed out"), { name: "TimeoutError" })
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(timeoutErr)))

    const res = await proxyFetchWithRetry(fakeReq, "/api/v1/chat", {
      method: "POST",
      body: "{}",
      timeoutMs: 50,
    })

    expect(res.status).toBe(504)
    const json = (await res.json()) as { error?: string }
    expect(json.error).toBe("upstream_timeout")
  })

  it("passa um AbortSignal no fetch ao backend", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ ok: true }), { status: 200 })),
    )
    vi.stubGlobal("fetch", fetchMock)

    const res = await proxyFetchWithRetry(fakeReq, "/api/v1/chat", { method: "POST", body: "{}" })

    expect(res.status).toBe(200)
    expect(fetchMock).toHaveBeenCalledTimes(1)
    const init = fetchMock.mock.calls[0][1] as RequestInit
    expect(init.signal).toBeDefined()
  })
})
