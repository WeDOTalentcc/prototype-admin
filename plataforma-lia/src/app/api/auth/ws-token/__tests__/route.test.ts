/**
 * Task #817 — Auditoria Canônica do Chat (regressão runtime)
 *
 * Cobre o canônico de emissão de token WebSocket:
 *   `src/app/api/auth/ws-token/route.ts`
 *
 * O ÚNICO consumidor produtivo em runtime é `useChatSocket.ts`, que faz
 * retry 3× com backoff. O sintoma reportado ("Failed to fetch /api/auth/
 * ws-token") só acontece em 4 cenários canônicos — todos exercitados aqui:
 *   1. Cookie `lia_access_token` presente   → 200 + authMode=jwt-cookie
 *   2. Cookie `workos_session` válido       → 200 + authMode=workos
 *   3. Sem cookies + dev-auto-login on      → 200 + authMode=dev-auto-login
 *      + Set-Cookie lia_access_token (httpOnly)
 *   4. Sem cookies + dev-auto-login off     → 401 no_credentials
 *      + Cache-Control: no-store
 *
 * Cenários adicionais (defesa em profundidade):
 *   5. Cookie `_sso_session_` placeholder NÃO é tratado como JWT real
 *   6. workos_session corrompido → 401 invalid_workos_session
 *   7. dev-auto-login on mas backend não devolve token → 503
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"

vi.mock("@/lib/session-crypto", () => ({
  verifyAndDecodeSession: vi.fn(),
}))

vi.mock("@/lib/auth/dev-auto-login", () => ({
  isDevAutoLoginEnabled: vi.fn(),
  getDevToken: vi.fn(),
}))

import { GET } from "../route"
import { verifyAndDecodeSession } from "@/lib/session-crypto"
import { getDevToken, isDevAutoLoginEnabled } from "@/lib/auth/dev-auto-login"
import type { NextRequest } from "next/server"

function makeRequest(cookies: Record<string, string> = {}): NextRequest {
  const headers = new Headers()
  return {
    headers,
    cookies: {
      get: (name: string) =>
        cookies[name] !== undefined ? { value: cookies[name] } : undefined,
    },
  } as unknown as NextRequest
}

describe("/api/auth/ws-token GET — canonical issuer (Task #817)", () => {
  beforeEach(() => {
    vi.mocked(verifyAndDecodeSession).mockReset()
    vi.mocked(isDevAutoLoginEnabled).mockReset()
    vi.mocked(getDevToken).mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("modo 1 — JWT cookie: devolve 200 com token e authMode=jwt-cookie", async () => {
    const req = makeRequest({ lia_access_token: "real-jwt-abc.def.ghi" })

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body).toEqual({
      token: "real-jwt-abc.def.ghi",
      authMode: "jwt-cookie",
    })
    expect(isDevAutoLoginEnabled).not.toHaveBeenCalled()
  })

  it("modo 1 (defesa) — placeholder _sso_session_ NÃO conta como JWT real", async () => {
    vi.mocked(isDevAutoLoginEnabled).mockReturnValue(false)
    const req = makeRequest({ lia_access_token: "_sso_session_" })

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(401)
    expect(body.code).toBe("no_credentials")
  })

  it("modo 2 — workos_session válido: devolve 200 com authMode=workos", async () => {
    vi.mocked(verifyAndDecodeSession).mockReturnValue({
      accessToken: "workos-jwt-xyz",
    } as ReturnType<typeof verifyAndDecodeSession>)
    const req = makeRequest({ workos_session: "encrypted-blob-here" })

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body).toEqual({
      token: "workos-jwt-xyz",
      authMode: "workos",
    })
    expect(verifyAndDecodeSession).toHaveBeenCalledWith("encrypted-blob-here")
  })

  it("modo 2 (falha) — workos_session corrompido: 401 invalid_workos_session + no-store", async () => {
    vi.mocked(verifyAndDecodeSession).mockReturnValue(null)
    const req = makeRequest({ workos_session: "tampered" })

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(401)
    expect(body).toMatchObject({
      token: null,
      code: "invalid_workos_session",
      authMode: "workos",
    })
    expect(res.headers.get("Cache-Control")).toBe("no-store")
  })

  it("modo 3 — dev-auto-login on + backend OK: 200, set-cookie httpOnly", async () => {
    vi.mocked(isDevAutoLoginEnabled).mockReturnValue(true)
    vi.mocked(getDevToken).mockResolvedValue("dev-token-123")
    const req = makeRequest({})

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body).toEqual({
      token: "dev-token-123",
      authMode: "dev-auto-login",
    })
    const setCookie = res.headers.get("set-cookie") ?? ""
    expect(setCookie).toContain("lia_access_token=dev-token-123")
    expect(setCookie.toLowerCase()).toContain("httponly")
    expect(setCookie).toContain("Path=/")
  })

  it("modo 3 (falha) — dev-auto-login on mas backend sem token: 503 + no-store", async () => {
    vi.mocked(isDevAutoLoginEnabled).mockReturnValue(true)
    vi.mocked(getDevToken).mockResolvedValue(null)
    const req = makeRequest({})

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body).toMatchObject({
      token: null,
      code: "dev_auto_login_failed",
      authMode: "dev-auto-login",
    })
    expect(res.headers.get("Cache-Control")).toBe("no-store")
  })

  it("modo 4 — sem credenciais + dev-auto-login off: 401 no_credentials + no-store", async () => {
    vi.mocked(isDevAutoLoginEnabled).mockReturnValue(false)
    const req = makeRequest({})

    const res = await GET(req)
    const body = await res.json()

    expect(res.status).toBe(401)
    expect(body).toMatchObject({
      token: null,
      code: "no_credentials",
      authMode: "none",
    })
    expect(res.headers.get("Cache-Control")).toBe("no-store")
    expect(getDevToken).not.toHaveBeenCalled()
  })

  it("contrato — JWT cookie tem prioridade sobre workos_session", async () => {
    vi.mocked(verifyAndDecodeSession).mockReturnValue({
      accessToken: "should-not-be-used",
    } as ReturnType<typeof verifyAndDecodeSession>)
    const req = makeRequest({
      lia_access_token: "winner",
      workos_session: "ignored",
    })

    const res = await GET(req)
    const body = await res.json()

    expect(body.authMode).toBe("jwt-cookie")
    expect(body.token).toBe("winner")
    expect(verifyAndDecodeSession).not.toHaveBeenCalled()
  })

  it("contrato — workos tem prioridade sobre dev-auto-login", async () => {
    vi.mocked(verifyAndDecodeSession).mockReturnValue({
      accessToken: "workos-wins",
    } as ReturnType<typeof verifyAndDecodeSession>)
    vi.mocked(isDevAutoLoginEnabled).mockReturnValue(true)
    const req = makeRequest({ workos_session: "valid" })

    const res = await GET(req)
    const body = await res.json()

    expect(body.authMode).toBe("workos")
    expect(isDevAutoLoginEnabled).not.toHaveBeenCalled()
    expect(getDevToken).not.toHaveBeenCalled()
  })
})
