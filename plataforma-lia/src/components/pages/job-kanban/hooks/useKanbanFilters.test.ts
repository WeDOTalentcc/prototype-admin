/**
 * Tests for useKanbanFilters — filterCandidates pure logic
 *
 * The hook itself requires React context, so we test the filterCandidates
 * logic by extracting it as a pure function (same algorithm).
 */
import { describe, it, expect } from "vitest"

// Mirror the filterCandidates logic from useKanbanFilters to test in isolation
function filterCandidates(candidates: Record<string, unknown>[], searchQuery: string): Record<string, unknown>[] {
  if (!searchQuery) return candidates
  const query = searchQuery.toLowerCase()
  return candidates.filter(candidate => {
    const name = candidate.name as string | undefined
    const role = candidate.role as string | undefined
    const company = candidate.company as string | undefined
    const location = candidate.location as string | undefined
    const currentCompany = candidate.currentCompany as string | undefined
    return (
      (name?.toLowerCase() ?? "").includes(query) ||
      (role?.toLowerCase() ?? "").includes(query) ||
      (company?.toLowerCase() ?? "").includes(query) ||
      (location?.toLowerCase() ?? "").includes(query) ||
      (currentCompany?.toLowerCase() ?? "").includes(query)
    )
  })
}

const candidates = [
  { id: "1", name: "Alice Souza", role: "Frontend Engineer", company: "TechCorp", location: "São Paulo" },
  { id: "2", name: "Bob Lima", role: "Backend Developer", company: "Nubank", location: "Rio de Janeiro" },
  { id: "3", name: "Carlos Mendes", role: "Product Manager", company: "iFood", location: "São Paulo", currentCompany: "iFood" },
]

describe("filterCandidates — search logic", () => {
  it("returns all candidates when query is empty", () => {
    expect(filterCandidates(candidates, "")).toHaveLength(3)
  })

  it("filters by name (case-insensitive)", () => {
    const result = filterCandidates(candidates, "alice")
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe("1")
  })

  it("filters by role", () => {
    const result = filterCandidates(candidates, "backend")
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe("2")
  })

  it("filters by company", () => {
    const result = filterCandidates(candidates, "nubank")
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe("2")
  })

  it("filters by location", () => {
    const result = filterCandidates(candidates, "são paulo")
    expect(result).toHaveLength(2)
  })

  it("filters by currentCompany", () => {
    const result = filterCandidates(candidates, "ifood")
    expect(result).toHaveLength(1)
    expect(result[0].id).toBe("3")
  })

  it("returns empty array when nothing matches", () => {
    const result = filterCandidates(candidates, "xyznotfound")
    expect(result).toHaveLength(0)
  })

  it("matching is case-insensitive", () => {
    const upper = filterCandidates(candidates, "ALICE")
    const lower = filterCandidates(candidates, "alice")
    expect(upper).toHaveLength(lower.length)
  })

  it("handles candidates with missing fields gracefully", () => {
    const partial = [{ id: "x", name: "Only Name" }]
    const result = filterCandidates(partial, "only name")
    expect(result).toHaveLength(1)
  })
})
