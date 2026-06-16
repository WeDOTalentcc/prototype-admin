/**
 * Task #1177 — proxy classification: ECONNREFUSED / fetch failed → 503
 * (retryable) instead of opaque 500 + console.error. Real upstream HTTP
 * errors (500/404) continue to be propagated with their original status.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import type { NextRequest } from "next/server"

import { GET } from "../route"
import { isBackendUnavailableError } from "../backend-error"

function makeReq(): NextRequest {
  return {
    url: "http://localhost:3000/api/backend-proxy/lia/job-wizard/session/sess-1",
    headers: new Headers({ Authorization: "Bearer test" }),
  } as unknown as NextRequest
}

describe("isBackendUnavailableError (Task #1177)", () => {
  it("classifica ECONNREFUSED como unavailable", () => {
    const err = Object.assign(new Error("connect ECONNREFUSED"), { code: "ECONNREFUSED" })
    const result = isBackendUnavailableError(err)
    expect(result.unavailable).toBe(true)
    expect(result.code).toBe("ECONNREFUSED")
  })

  it("classifica undici TypeError('fetch failed') como unavailable", () => {
    const err = Object.assign(new TypeError("fetch failed"), {
      cause: { code: "ECONNREFUSED" },
    })
    const result = isBackendUnavailableError(err)
    expect(result.unavailable).toBe(true)
    expect(result.code).toBe("ECONNREFUSED")
  })

  it("classifica AbortError (timeout) como unavailable", () => {
    const err = Object.assign(new Error("aborted"), { name: "AbortError" })
    const result = isBackendUnavailableError(err)
    expect(result.unavailable).toBe(true)
  })

  it("NÃO classifica TypeError genérico como unavailable", () => {
    const err = new TypeError("Cannot read property 'foo' of undefined")
    expect(isBackendUnavailableError(err).unavailable).toBe(false)
  })

  it("NÃO classifica erros desconhecidos como unavailable", () => {
    expect(isBackendUnavailableError(new Error("boom")).unavailable).toBe(false)
  })
})

describe("lia proxy route — GET (Task #1177)", () => {
  const originalFetch = global.fetch
  let warnSpy: ReturnType<typeof vi.spyOn>
  let errorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {})
    errorSpy = vi.spyOn(console, "error").mockImplementation(() => {})
  })
  afterEach(() => {
    global.fetch = originalFetch
    warnSpy.mockRestore()
    errorSpy.mockRestore()
  })

  it("ECONNREFUSED → 503 com retryable=true, log em warn (não error)", async () => {
    global.fetch = vi
      .fn()
      .mockRejectedValue(
        Object.assign(new TypeError("fetch failed"), { cause: { code: "ECONNREFUSED" } }),
      ) as unknown as typeof fetch

    const res = await GET(makeReq(), { params: Promise.resolve({ path: ["job-wizard", "session", "sess-1"] }) })
    expect(res.status).toBe(503)
    const body = await res.json()
    expect(body.retryable).toBe(true)
    expect(body.code).toBe("ECONNREFUSED")
    expect(warnSpy).toHaveBeenCalled()
    expect(errorSpy).not.toHaveBeenCalled()
  })

  it("upstream 500 é repassado com o status original (não vira 503)", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({ detail: "endpoint boom" }),
    }) as unknown as typeof fetch

    const res = await GET(makeReq(), { params: Promise.resolve({ path: ["job-wizard", "session", "sess-1"] }) })
    expect(res.status).toBe(500)
    const body = await res.json()
    expect(body.error).toBe("endpoint boom")
  })

  it("erro inesperado (não conexão) cai no catch genérico → 500 + console.error", async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError("unexpected explosion")) as unknown as typeof fetch

    const res = await GET(makeReq(), { params: Promise.resolve({ path: ["job-wizard", "session", "sess-1"] }) })
    expect(res.status).toBe(500)
    expect(errorSpy).toHaveBeenCalled()
  })
})
