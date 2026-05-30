import { describe, expect, it } from "vitest"
import { wizardUpdateToMessage, mergeCollectedData } from "../UnifiedChat"

/**
 * Fase 5b — fechar o loop dos chips de competência.
 * wizardUpdateToMessage produz mensagem NL coerente para edições de competência
 * (não mais JSON cru); mergeCollectedData acumula os campos estruturados que
 * viajam como context.right_panel_form pro backend (lê confirmed_* na Fase 3).
 */
describe("wizardUpdateToMessage — competências (Fase 5b)", () => {
  it("técnicas → mensagem NL legível", () => {
    const msg = wizardUpdateToMessage({
      confirmed_technical_competencies: [{ skill: "Python" }, { skill: "SQL" }],
    })
    expect(msg).toMatch(/Python/)
    expect(msg).toMatch(/SQL/)
    expect(msg).not.toMatch(/wizard_update/) // não cai no JSON cru
  })

  it("comportamentais → mensagem NL legível", () => {
    const msg = wizardUpdateToMessage({
      confirmed_behavioral_competencies: [{ competencia: "Comunicação" }],
    })
    expect(msg).toMatch(/Comunicação/)
    expect(msg).not.toMatch(/wizard_update/)
  })

  it("técnicas + comportamentais juntas", () => {
    const msg = wizardUpdateToMessage({
      confirmed_technical_competencies: [{ skill: "Go" }],
      confirmed_behavioral_competencies: [{ competencia: "Autonomia" }],
    })
    expect(msg).toMatch(/Go/)
    expect(msg).toMatch(/Autonomia/)
  })

  it("update desconhecido ainda cai no fallback JSON", () => {
    const msg = wizardUpdateToMessage({ foo: "bar" })
    expect(msg).toMatch(/wizard_update/)
  })
})

describe("mergeCollectedData — acumula campos estruturados (Fase 5b)", () => {
  it("acumula técnicas e comportamentais de edições separadas", () => {
    const a = mergeCollectedData({}, { confirmed_technical_competencies: [{ skill: "Python" }] })
    const b = mergeCollectedData(a, { confirmed_behavioral_competencies: [{ competencia: "Comunicação" }] })
    expect(b.confirmed_technical_competencies).toEqual([{ skill: "Python" }])
    expect(b.confirmed_behavioral_competencies).toEqual([{ competencia: "Comunicação" }])
  })

  it("update mais recente sobrescreve o mesmo campo", () => {
    const a = mergeCollectedData({}, { confirmed_technical_competencies: [{ skill: "Python" }] })
    const b = mergeCollectedData(a, { confirmed_technical_competencies: [{ skill: "Python" }, { skill: "SQL" }] })
    expect(b.confirmed_technical_competencies).toHaveLength(2)
  })
})
