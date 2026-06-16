/**
 * Task #817 — Auditoria Canônica do Chat
 *
 * Cobre o produtor: o proxy `/api/backend-proxy/pipeline-pulse` deve garantir
 * `{stages: PipelinePulseStage[], total: number}` em respostas 2xx OU
 * propagar erro estruturado. Nunca pode vazar payload corrompido com 200.
 *
 * Estratégia em 2 camadas:
 *   1. Validador puro `isValidPulsePayload` (espelho 1:1 do route)
 *   2. Integração: importa o `GET` real do route.ts e exercita os 5 caminhos
 *      canônicos com `fetch` mockado (200 ok, 200 com shape inválido, 4xx,
 *      5xx, falha de rede). Garante que a validação de shape (ADR-0817-2)
 *      está plugada no caminho real, não só no espelho.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import type { NextRequest } from "next/server"

vi.mock("@/lib/api/auth-headers", () => ({
  getAuthHeaders: () => ({ "Content-Type": "application/json" }),
}))

interface PipelinePulseStage {
  macro_stage: string
  count: number
}
interface PipelinePulsePayload {
  stages: PipelinePulseStage[]
  total: number
}

function isValidPulsePayload(value: unknown): value is PipelinePulsePayload {
  if (!value || typeof value !== "object") return false
  const v = value as Record<string, unknown>
  if (!Array.isArray(v.stages)) return false
  if (typeof v.total !== "number") return false
  return v.stages.every(
    (s) =>
      s !== null &&
      typeof s === "object" &&
      typeof (s as Record<string, unknown>).macro_stage === "string" &&
      typeof (s as Record<string, unknown>).count === "number",
  )
}

describe("pipeline-pulse proxy — isValidPulsePayload (Task #817)", () => {
  it("aceita payload válido vazio", () => {
    expect(isValidPulsePayload({ stages: [], total: 0 })).toBe(true)
  })

  it("aceita payload válido completo", () => {
    expect(
      isValidPulsePayload({
        stages: [
          { macro_stage: "sourcing", count: 5 },
          { macro_stage: "triagem", count: 3 },
        ],
        total: 8,
      }),
    ).toBe(true)
  })

  it("rejeita null/undefined/primitivos", () => {
    expect(isValidPulsePayload(null)).toBe(false)
    expect(isValidPulsePayload(undefined)).toBe(false)
    expect(isValidPulsePayload("ok")).toBe(false)
    expect(isValidPulsePayload(42)).toBe(false)
    expect(isValidPulsePayload(true)).toBe(false)
  })

  it("rejeita payload sem stages (causa raiz)", () => {
    expect(isValidPulsePayload({ total: 0 })).toBe(false)
  })

  it("rejeita stages que não é array", () => {
    expect(isValidPulsePayload({ stages: "list", total: 0 })).toBe(false)
    expect(isValidPulsePayload({ stages: { sourcing: 3 }, total: 3 })).toBe(false)
    expect(isValidPulsePayload({ stages: null, total: 0 })).toBe(false)
  })

  it("rejeita total ausente ou não-numérico", () => {
    expect(isValidPulsePayload({ stages: [] })).toBe(false)
    expect(isValidPulsePayload({ stages: [], total: "0" })).toBe(false)
    expect(isValidPulsePayload({ stages: [], total: null })).toBe(false)
  })

  it("rejeita stage individual malformado", () => {
    expect(
      isValidPulsePayload({ stages: [{ macro_stage: "x", count: "5" }], total: 1 }),
    ).toBe(false)
    expect(
      isValidPulsePayload({ stages: [{ count: 5 }], total: 1 }),
    ).toBe(false)
    expect(
      isValidPulsePayload({ stages: [null], total: 0 }),
    ).toBe(false)
  })
})

// ─── Camada 2: integração — exercita o GET real do route handler ──────────
// Confirma que `isValidPulsePayload` está plugado no caminho real, não só
// duplicado no teste. Cobre os 5 desfechos canônicos que `useChatWorkflowReels`
// pode encontrar em runtime.
describe("pipeline-pulse proxy — GET handler integrado (Task #817)", () => {
  let originalFetch: typeof globalThis.fetch
  const fakeRequest = {} as unknown as NextRequest

  beforeEach(() => {
    originalFetch = globalThis.fetch
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
    vi.restoreAllMocks()
  })

  async function loadRoute() {
    return await import("../route")
  }

  it("200 OK + payload válido → 200 + repassa body", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({ stages: [{ macro_stage: "sourcing", count: 3 }], total: 3 }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    ) as typeof globalThis.fetch

    const { GET } = await loadRoute()
    const res = await GET(fakeRequest)
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body).toEqual({
      stages: [{ macro_stage: "sourcing", count: 3 }],
      total: 3,
    })
  })

  it("200 OK + shape inválido → 502 invalid_pulse_payload (ADR-0817-2)", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ unexpected: "shape" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ) as typeof globalThis.fetch

    const { GET } = await loadRoute()
    const res = await GET(fakeRequest)
    const body = await res.json()

    expect(res.status).toBe(502)
    expect(body).toMatchObject({
      error: "invalid_pulse_payload",
      detail: expect.stringContaining("PipelinePulseResponse"),
    })
  })

  it("200 OK + stages null (causa raiz reportada) → 502, não vaza payload", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ stages: null, total: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ) as typeof globalThis.fetch

    const { GET } = await loadRoute()
    const res = await GET(fakeRequest)

    expect(res.status).toBe(502)
  })

  it("backend 4xx/5xx → propaga status original com body de erro", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Unauthorized" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      }),
    ) as typeof globalThis.fetch

    const { GET } = await loadRoute()
    const res = await GET(fakeRequest)
    const body = await res.json()

    expect(res.status).toBe(401)
    expect(body).toEqual({ detail: "Unauthorized" })
  })

  it("falha de rede no fetch → 500 estruturado, não throw", async () => {
    globalThis.fetch = vi
      .fn()
      .mockRejectedValue(new Error("ECONNREFUSED")) as typeof globalThis.fetch

    const { GET } = await loadRoute()
    const res = await GET(fakeRequest)
    const body = await res.json()

    expect(res.status).toBe(500)
    expect(body).toEqual({ error: "Failed to connect to backend" })
  })
})
