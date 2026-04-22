/**
 * @vitest-environment node
 *
 * Task #801 (C3): retry com backoff durante cold-start de backend.
 * Garante que `loginDemoUser` reente quando a 1ª tentativa cai por
 * TypeError("Failed to fetch") e converge ao sucesso na 2ª.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { clearCachedDevToken, loginDemoUser } from "@/lib/auth/dev-auto-login"

describe("dev-auto-login (Task #801 C3)", () => {
  const realFetch = global.fetch
  let consoleWarnSpy: ReturnType<typeof vi.spyOn>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    clearCachedDevToken()
    vi.useFakeTimers()
    consoleWarnSpy = vi.spyOn(console, "warn").mockImplementation(() => {})
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {})
  })

  afterEach(() => {
    vi.useRealTimers()
    consoleWarnSpy.mockRestore()
    consoleErrorSpy.mockRestore()
    global.fetch = realFetch
  })

  it("retenta após TypeError transiente e converge ao sucesso na 2ª tentativa", async () => {
    const transientErr = new TypeError("Failed to fetch")
    const okBody = {
      access_token: "demo-jwt-success",
      refresh_token: "demo-refresh",
    }

    const fetchMock = vi
      .fn()
      .mockRejectedValueOnce(transientErr)
      .mockResolvedValueOnce(
        new Response(JSON.stringify(okBody), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
    global.fetch = fetchMock as unknown as typeof fetch

    const promise = loginDemoUser()
    // Avança o backoff de 1s até a 2ª tentativa rodar.
    await vi.advanceTimersByTimeAsync(1500)
    const result = await promise

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(result).toEqual({
      accessToken: "demo-jwt-success",
      refreshToken: "demo-refresh",
    })
    // Logs: indisponibilidade transiente NÃO deve emitir console.error
    // (apenas console.warn no caminho final, e nem isso aqui pois sucesso).
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it("desiste imediatamente em erro determinístico 401 e loga via warn (não error)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response("invalid credentials", { status: 401, statusText: "Unauthorized" }),
    )
    global.fetch = fetchMock as unknown as typeof fetch

    const result = await loginDemoUser()

    expect(result).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(consoleWarnSpy).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
