import { describe, expect, it } from "vitest"
import { mergeCollectedData } from "../UnifiedChat"

/**
 * Sensor — mergeCollectedData (write-back Fase 5b).
 *
 * Pina: shallow-merge correto, edição mais recente vence,
 * salary e competências acumulam conforme esperado pelo backend
 * (right_panel_form no próximo turno → intake_gate/salary_node leem).
 */

describe("mergeCollectedData — write-back Fase 5b", () => {
  it("shallow merge: campos novos adicionados", () => {
    const result = mergeCollectedData({ a: 1 }, { b: 2 })
    expect(result).toEqual({ a: 1, b: 2 })
  })

  it("edição mais recente vence (salary_min)", () => {
    const prev = { salary_min: 10000, salary_max: 18000 }
    const result = mergeCollectedData(prev, { salary_min: 14000 })
    expect(result.salary_min).toBe(14000)
    expect(result.salary_max).toBe(18000)  // intocado
  })

  it("competências técnicas substituem lista anterior", () => {
    const prev = { confirmed_technical_competencies: [{ skill: "Python", contexto: "" }] }
    const next = { confirmed_technical_competencies: [{ skill: "Rust", contexto: "" }] }
    const result = mergeCollectedData(prev, next)
    expect((result.confirmed_technical_competencies as { skill: string }[]).map((c) => c.skill)).toEqual(["Rust"])
  })

  it("campos independentes não interferem entre si", () => {
    const prev = { salary_min: 10000, confirmed_technical_competencies: [{ skill: "Go", contexto: "" }] }
    const result = mergeCollectedData(prev, { salary_max: 20000 })
    expect(result.salary_min).toBe(10000)
    expect(result.confirmed_technical_competencies).toEqual([{ skill: "Go", contexto: "" }])
    expect(result.salary_max).toBe(20000)
  })

  it("merge sobre objeto vazio retorna updates intactos", () => {
    const updates = { salary_min: 5000, salary_max: 9000 }
    expect(mergeCollectedData({}, updates)).toEqual(updates)
  })
})
