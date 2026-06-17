/**
 * Sensor #5 Fase 2: applyVacancyStageOverrides — override de sub-status POR VAGA
 * tem precedência sobre o default da empresa no seletor de transição do kanban.
 * Consumer-first: garante que o mecanismo lê o override de job.interview_stages.
 */
import { describe, it, expect } from "vitest"
import { applyVacancyStageOverrides, buildSubStatusMap } from "../stage-utils"

const companyPipeline = [
  { name: "screening", sub_statuses: [{ name: "a", display_name: "A da empresa" }] },
  { name: "interview", sub_statuses: [{ name: "x", display_name: "X da empresa" }] },
]

describe("applyVacancyStageOverrides (#5 Fase 2)", () => {
  it("override da vaga substitui o sub-status da empresa para a etapa", () => {
    const base = buildSubStatusMap(companyPipeline)
    const merged = applyVacancyStageOverrides(base, [
      { name: "screening", subStatuses: [{ name: "vaga1", display_name: "Custom da vaga" }] },
    ])
    expect(merged.screening.map(s => s.name)).toEqual(["vaga1"])
    // etapa sem override mantém o default da empresa
    expect(merged.interview.map(s => s.name)).toEqual(["x"])
  })

  it("etapa sem subStatuses no override não altera o default herdado", () => {
    const base = buildSubStatusMap(companyPipeline)
    const merged = applyVacancyStageOverrides(base, [{ name: "screening" }])
    expect(merged.screening.map(s => s.name)).toEqual(["a"])
  })

  it("sem interviewStages retorna o mapa original (identidade)", () => {
    const base = buildSubStatusMap(companyPipeline)
    expect(applyVacancyStageOverrides(base, undefined)).toBe(base)
    expect(applyVacancyStageOverrides(base, [])).toBe(base)
  })

  it("casa override por stageName quando name ausente", () => {
    const base = buildSubStatusMap(companyPipeline)
    const merged = applyVacancyStageOverrides(base, [
      { stageName: "interview", subStatuses: [{ name: "y", display_name: "Y vaga" }] },
    ])
    expect(merged.interview.map(s => s.name)).toEqual(["y"])
  })
})
