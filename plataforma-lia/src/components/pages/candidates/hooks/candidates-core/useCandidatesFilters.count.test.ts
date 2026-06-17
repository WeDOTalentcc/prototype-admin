import { describe, it, expect } from "vitest"
import { getActiveTableFiltersCount } from "./useCandidatesFilters"

// Pina P2-1: o contador de "filtros ativos" NAO somava skills/jobTitles/
// companies/industries (eliminatorios em useCandidatesFilterSort 104-127).
// Usa deltas relativos p/ ser robusto a defaults de scalars do objeto base.
const base = {
  statuses: [], tags: [], seniorityLevels: [], workModels: [], contractTypes: [],
  locations: [], sources: [], softSkills: [], certifications: [],
  skills: [], jobTitles: [], companies: [], industries: [],
} as unknown as Parameters<typeof getActiveTableFiltersCount>[0]

describe("getActiveTableFiltersCount (P2-1)", () => {
  it("conta os 4 eliminatorios (delta +4 vs base)", () => {
    const withFour = { ...base, skills: ["a"], jobTitles: ["b"], companies: ["c"], industries: ["d"] }
    expect(getActiveTableFiltersCount(withFour) - getActiveTableFiltersCount(base)).toBe(4)
  })
  it("seniorityLevels continua contando (+1, nao regredir)", () => {
    expect(getActiveTableFiltersCount({ ...base, seniorityLevels: ["pleno"] }) - getActiveTableFiltersCount(base)).toBe(1)
  })
})
