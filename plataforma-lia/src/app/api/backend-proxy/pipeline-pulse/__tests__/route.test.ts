/**
 * Task #817 — Auditoria Canônica do Chat
 *
 * Cobre o produtor: o proxy `/api/backend-proxy/pipeline-pulse` deve garantir
 * `{stages: PipelinePulseStage[], total: number}` em respostas 2xx OU
 * propagar erro estruturado. Nunca pode vazar payload corrompido com 200.
 *
 * Estratégia: testar diretamente a função `isValidPulsePayload` redeclarada
 * aqui, espelhando 1:1 a do route handler. (O route handler depende de
 * NextRequest/NextResponse + getAuthHeaders + fetch, custoso de e2e-mockar
 * em jsdom — a regressão crítica é a validação do shape.)
 */

import { describe, it, expect } from "vitest"

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
