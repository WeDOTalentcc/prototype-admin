import { describe, expect, it } from "vitest"
import { formatWizardSavedLabel } from "../wizard-saved-label"

describe("formatWizardSavedLabel", () => {
  const baseNow = new Date("2026-04-26T13:00:00.000Z")

  it("returns null when the wizard is inactive", () => {
    const savedAt = new Date(baseNow.getTime() - 60_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, false)).toBeNull()
  })

  it("returns null before the first save event (rehydrate guard)", () => {
    expect(formatWizardSavedLabel(null, baseNow, true)).toBeNull()
  })

  it("renders 'Salvando…' inside the 5s window", () => {
    const savedAt = new Date(baseNow.getTime() - 1_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvando…")
  })

  it("renders 'Salvo agora' between 5s and 1min", () => {
    const savedAt = new Date(baseNow.getTime() - 30_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvo agora")
  })

  it("renders singular minute label", () => {
    const savedAt = new Date(baseNow.getTime() - 60_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvo há 1 min")
  })

  it("renders plural minute label", () => {
    const savedAt = new Date(baseNow.getTime() - 5 * 60_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvo há 5 min")
  })

  it("renders singular hour label", () => {
    const savedAt = new Date(baseNow.getTime() - 60 * 60_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvo há 1 hora")
  })

  it("renders plural hour label", () => {
    const savedAt = new Date(baseNow.getTime() - 3 * 60 * 60_000)
    expect(formatWizardSavedLabel(savedAt, baseNow, true)).toBe("Salvo há 3 horas")
  })
})
