import { describe, it, expect } from "vitest"
import { countActiveFilterMatches } from "../hooks/useCandidatesFilterSort"

// Fase 3: re-score por grau de match dos filtros ativos.
// Pina: quem satisfaz MAIS condicoes de filtro tem contagem maior (sobe no ranking).
const noFilters = { skills: [], locations: [], jobTitles: [], companies: [], seniorityLevels: [] }
const noAdvanced = {} as Record<string, string[]>

describe("countActiveFilterMatches", () => {
  it("zero quando nao ha filtros ativos", () => {
    expect(countActiveFilterMatches({ skills: ["Python"] }, noFilters, noAdvanced)).toBe(0)
  })

  it("conta cada skill casada (2 skills > 1 skill)", () => {
    const f = { ...noFilters, skills: ["python", "aws"] }
    const both = countActiveFilterMatches({ skills: ["Python", "AWS", "Docker"] }, f, noAdvanced)
    const one = countActiveFilterMatches({ skills: ["Python", "Go"] }, f, noAdvanced)
    expect(both).toBe(2)
    expect(one).toBe(1)
    expect(both).toBeGreaterThan(one)
  })

  it("soma match de location e job title", () => {
    const f = { ...noFilters, locations: ["sao paulo"], jobTitles: ["engenheiro"] }
    const c = { location: "Sao Paulo, BR", position: "Engenheiro de Dados" }
    expect(countActiveFilterMatches(c, f, noAdvanced)).toBe(2)
  })

  it("case-insensitive e substring", () => {
    const f = { ...noFilters, companies: ["nubank"] }
    expect(countActiveFilterMatches({ workHistory: [{ company: "NuBank S.A." }] }, f, noAdvanced)).toBe(1)
  })

  it("considera advancedFilters (skills/locations/job_titles/companies)", () => {
    const adv = { skills: ["react"], locations: [], job_titles: [], companies: [] }
    expect(countActiveFilterMatches({ skills: ["React", "Node"] }, noFilters, adv)).toBe(1)
  })

  it("seniority via position ou level", () => {
    const f = { ...noFilters, seniorityLevels: ["senior"] }
    expect(countActiveFilterMatches({ position: "Senior Engineer" }, f, noAdvanced)).toBe(1)
    expect(countActiveFilterMatches({ level: "Senior" }, f, noAdvanced)).toBe(1)
  })
})
