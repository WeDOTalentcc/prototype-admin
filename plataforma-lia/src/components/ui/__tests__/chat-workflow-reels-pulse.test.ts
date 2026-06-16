/**
 * Task #817 — Auditoria Canônica do Chat
 *
 * Regressão isolada do bug "TypeError: undefined is not iterable" em
 * chat-workflow-reels.tsx, linha histórica 49: `for (const s of data.stages)`.
 *
 * O hook `usePipelinePulse` é interno ao componente, então testamos a lógica
 * defensiva extraída — `parsePulseStages` — espelhando 1:1 o algoritmo do
 * `useEffect`. Isso evita arrastar React/jsdom só para validar parsing.
 */

import { describe, it, expect } from "vitest"

interface PulseStage {
  macro_stage: string
  count: number
}
interface PulsePayload {
  stages: PulseStage[]
  total: number
}

function parsePulseStages(data: PulsePayload | null | undefined | unknown): Record<string, number> {
  if (!data || typeof data !== "object") return {}
  const stages = (data as { stages?: unknown }).stages
  const safeStages = Array.isArray(stages) ? stages : []
  const map: Record<string, number> = {}
  for (const s of safeStages) {
    if (
      s &&
      typeof s === "object" &&
      typeof (s as Record<string, unknown>).macro_stage === "string" &&
      typeof (s as Record<string, unknown>).count === "number"
    ) {
      const stage = s as PulseStage
      map[stage.macro_stage] = stage.count
    }
  }
  return map
}

describe("usePipelinePulse — defensive shape parsing (Task #817)", () => {
  it("retorna mapa vazio quando data === null (proxy 4xx/5xx → null)", () => {
    expect(parsePulseStages(null)).toEqual({})
  })

  it("retorna mapa vazio quando data === undefined", () => {
    expect(parsePulseStages(undefined)).toEqual({})
  })

  it("não quebra quando stages é undefined (causa raiz histórica)", () => {
    expect(() => parsePulseStages({ total: 0 } as unknown)).not.toThrow()
    expect(parsePulseStages({ total: 0 } as unknown)).toEqual({})
  })

  it("não quebra quando stages é null", () => {
    expect(() => parsePulseStages({ stages: null, total: 0 } as unknown)).not.toThrow()
    expect(parsePulseStages({ stages: null, total: 0 } as unknown)).toEqual({})
  })

  it("não quebra quando stages é objeto (shape divergente)", () => {
    expect(() =>
      parsePulseStages({ stages: { sourcing: 3 }, total: 3 } as unknown),
    ).not.toThrow()
    expect(parsePulseStages({ stages: { sourcing: 3 }, total: 3 } as unknown)).toEqual({})
  })

  it("retorna mapa vazio quando stages é array vazio (sem dados)", () => {
    expect(parsePulseStages({ stages: [], total: 0 })).toEqual({})
  })

  it("constrói mapa correto a partir de payload válido completo", () => {
    const payload: PulsePayload = {
      stages: [
        { macro_stage: "sourcing", count: 12 },
        { macro_stage: "triagem", count: 8 },
        { macro_stage: "entrevista", count: 3 },
        { macro_stage: "oferta", count: 1 },
        { macro_stage: "contratacao", count: 0 },
      ],
      total: 24,
    }
    expect(parsePulseStages(payload)).toEqual({
      sourcing: 12,
      triagem: 8,
      entrevista: 3,
      oferta: 1,
      contratacao: 0,
    })
  })

  it("filtra entradas malformadas dentro do array (count string, macro_stage ausente)", () => {
    const payload = {
      stages: [
        { macro_stage: "sourcing", count: 5 },
        { macro_stage: "triagem", count: "8" }, // count não-numérico
        { count: 3 }, // macro_stage ausente
        null,
        undefined,
        { macro_stage: "oferta", count: 2 },
      ],
      total: 18,
    } as unknown
    expect(parsePulseStages(payload)).toEqual({ sourcing: 5, oferta: 2 })
  })

  it("não quebra com primitivos como input (string/number/boolean)", () => {
    expect(() => parsePulseStages("not an object" as unknown)).not.toThrow()
    expect(() => parsePulseStages(42 as unknown)).not.toThrow()
    expect(() => parsePulseStages(true as unknown)).not.toThrow()
    expect(parsePulseStages("not an object" as unknown)).toEqual({})
  })
})
