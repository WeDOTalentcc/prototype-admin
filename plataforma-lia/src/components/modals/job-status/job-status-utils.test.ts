import { describe, it, expect } from "vitest"
import { formatPausedDuration, replaceTemplateVariables } from "./job-status-utils"

// Helpers to build ISO dates relative to now
function daysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString()
}

describe("formatPausedDuration", () => {
  it("returns — when pausedSince is undefined", () => {
    expect(formatPausedDuration(undefined)).toBe("—")
  })

  it("returns Hoje for 0 days", () => {
    expect(formatPausedDuration(daysAgo(0))).toBe("Hoje")
  })

  it("returns 1 dia for exactly 1 day", () => {
    expect(formatPausedDuration(daysAgo(1))).toBe("1 dia")
  })

  it("returns N dias for 2–6 days", () => {
    expect(formatPausedDuration(daysAgo(3))).toBe("3 dias")
    expect(formatPausedDuration(daysAgo(6))).toBe("6 dias")
  })

  it("returns weeks for 7–29 days", () => {
    expect(formatPausedDuration(daysAgo(7))).toBe("1 semanas")
    expect(formatPausedDuration(daysAgo(14))).toBe("2 semanas")
    expect(formatPausedDuration(daysAgo(29))).toBe("5 semanas")
  })

  it("returns months for 30+ days", () => {
    expect(formatPausedDuration(daysAgo(30))).toBe("1 meses")
    expect(formatPausedDuration(daysAgo(60))).toBe("2 meses")
  })
})

describe("replaceTemplateVariables", () => {
  it("replaces {{job_title}} with jobTitle", () => {
    expect(replaceTemplateVariables("Olá, candidato para {{job_title}}", "Engenheiro")).toBe("Olá, candidato para Engenheiro")
  })

  it("replaces {{vaga}} with jobTitle", () => {
    expect(replaceTemplateVariables("Vaga: {{vaga}}", "Dev Senior")).toBe("Vaga: Dev Senior")
  })

  it("replaces {{company_name}} with WeDO Talent", () => {
    expect(replaceTemplateVariables("Empresa: {{company_name}}", "Qualquer")).toBe("Empresa: WeDO Talent")
  })

  it("replaces {{empresa}} with WeDO Talent", () => {
    expect(replaceTemplateVariables("{{empresa}} te contrata!", "Qualquer")).toBe("WeDO Talent te contrata!")
  })

  it("replaces all occurrences in the same string", () => {
    const result = replaceTemplateVariables("{{job_title}} em {{company_name}} — {{job_title}}", "Analista")
    expect(result).toBe("Analista em WeDO Talent — Analista")
  })
})
