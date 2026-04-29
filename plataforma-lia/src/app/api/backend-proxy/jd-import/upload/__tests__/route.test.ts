/**
 * Task #838 — Privacy & audit hardening on JD upload
 *
 * Cobre o proxy `/api/backend-proxy/jd-import/upload` apos o backend ter sido
 * trocado para `get_current_user_strict` (M-09). Garante:
 *   1. Auth bem-formada (Authorization header) e flag de consentimento sao
 *      encaminhados ao backend FastAPI.
 *   2. Request sem token nem cookies retorna 401 no proprio proxy (fail-fast),
 *      evitando log de 500 no FastAPI.
 *   3. Status >=400 do backend (ex.: 428 consent_required) e propagado para o
 *      cliente sem mascarar.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import type { NextRequest } from "next/server"

// O modulo real chama `verifyAndDecodeSession` para o cookie `workos_session`.
// Para os testes unitarios do proxy queremos exercitar o helper de verdade
// sobre as fontes mais comuns (Authorization header e cookie `lia_access_token`),
// entao stubamos apenas a verificacao de sessao WorkOS.
vi.mock("@/lib/session-crypto", () => ({
  verifyAndDecodeSession: () => null,
}))

interface MockRequestOpts {
  authorization?: string
  cookies?: Record<string, string>
  query?: string
  fileBytes?: Uint8Array
}

function buildRequest(opts: MockRequestOpts = {}): NextRequest {
  const headers = new Headers()
  if (opts.authorization) headers.set("Authorization", opts.authorization)

  const cookieJar: Record<string, string> = opts.cookies ?? {}
  if (Object.keys(cookieJar).length > 0) {
    const cookieHeader = Object.entries(cookieJar)
      .map(([k, v]) => `${k}=${v}`)
      .join("; ")
    headers.set("cookie", cookieHeader)
  }

  const formData = new FormData()
  const bytes = opts.fileBytes ?? new TextEncoder().encode("Vaga de engenheiro")
  const blob = new Blob([bytes], { type: "text/plain" })
  formData.append("file", blob, "vaga.txt")

  const url = `http://localhost/api/backend-proxy/jd-import/upload${opts.query ?? "?consent_acknowledged=true"}`

  // Mimica o NextRequest no que o handler usa: headers, cookies.get(), formData(),
  // url. Suficiente para o caminho exercitado pelo route.ts.
  const fakeRequest = {
    headers,
    cookies: {
      get: (name: string) =>
        cookieJar[name] !== undefined ? { name, value: cookieJar[name] } : undefined,
    },
    url,
    formData: async () => formData,
  } as unknown as NextRequest

  return fakeRequest
}

describe("jd-import/upload proxy — auth forwarding (Task #838)", () => {
  let originalFetch: typeof globalThis.fetch
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    originalFetch = globalThis.fetch
    // mockImplementation (nao mockResolvedValue) para gerar uma Response fresca
    // por chamada — body streams sao consumidos uma unica vez.
    fetchMock = vi.fn().mockImplementation(async () =>
      new Response(
        JSON.stringify({
          success: true,
          task_id: "task-uuid-123",
          status: "queued",
          message: "Upload aceito.",
          audit: { uuid: "task-uuid-123", filename_hash: "hash", size_bytes: 18 },
        }),
        { status: 202, headers: { "Content-Type": "application/json" } },
      ),
    )
    globalThis.fetch = fetchMock as typeof globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  async function loadRoute() {
    return await import("../route")
  }

  it("encaminha Authorization header ao backend quando presente", async () => {
    const { POST } = await loadRoute()
    const req = buildRequest({ authorization: "Bearer real-user-token" })

    const res = await POST(req)
    expect(res.status).toBe(202)

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [calledUrl, init] = fetchMock.mock.calls[0]
    expect(String(calledUrl)).toContain("/api/v1/import/upload-file")
    expect(String(calledUrl)).toContain("consent_acknowledged=true")

    const sentHeaders = init?.headers as Record<string, string>
    expect(sentHeaders["Authorization"]).toBe("Bearer real-user-token")
  })

  it("converte cookie lia_access_token em Bearer token", async () => {
    const { POST } = await loadRoute()
    const req = buildRequest({ cookies: { lia_access_token: "cookie-jwt" } })

    const res = await POST(req)
    expect(res.status).toBe(202)

    const init = fetchMock.mock.calls[0][1]
    const sentHeaders = init?.headers as Record<string, string>
    expect(sentHeaders["Authorization"]).toBe("Bearer cookie-jwt")
  })

  it("sem token nem cookies retorna 401 no proxy e NAO chama o backend", async () => {
    const { POST } = await loadRoute()
    const req = buildRequest({})

    const res = await POST(req)
    expect(res.status).toBe(401)

    const body = await res.json()
    expect(body).toMatchObject({ success: false, error: "Authentication required" })
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("encaminha session_id para o backend para roteamento dos WS background_task_update (Task #858 / B-02)", async () => {
    const { POST } = await loadRoute()
    const req = buildRequest({
      authorization: "Bearer real-user-token",
      query: "?consent_acknowledged=true&session_id=ws-session-abc-123",
    })

    const res = await POST(req)
    expect(res.status).toBe(202)

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const calledUrl = String(fetchMock.mock.calls[0][0])
    expect(calledUrl).toContain("session_id=ws-session-abc-123")
    expect(calledUrl).toContain("consent_acknowledged=true")
  })

  it("propaga status 4xx do backend (ex.: 428 consent_required) sem mascarar", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          detail: { error: "consent_required", purpose: "jd_processing" },
        }),
        { status: 428, headers: { "Content-Type": "application/json" } },
      ),
    )
    const { POST } = await loadRoute()
    const req = buildRequest({
      authorization: "Bearer real-user-token",
      query: "?consent_acknowledged=false",
    })

    const res = await POST(req)
    expect(res.status).toBe(428)
  })
})
