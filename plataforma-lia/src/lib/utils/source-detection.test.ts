import { describe, it, expect } from "vitest"
import {
  normalizeSourceField,
  isGlobalSource,
  isLocalSource,
  getSourceDetails,
  getSourceCreditsEstimate,
} from "./source-detection"

describe("normalizeSourceField", () => {
  it("lowercases and trims the input", () => {
    expect(normalizeSourceField("  Pearch  ")).toBe("pearch")
  })

  it("replaces dashes with underscores", () => {
    expect(normalizeSourceField("pearch-ai")).toBe("pearch_ai")
  })

  it("returns empty string for null/undefined", () => {
    expect(normalizeSourceField(null)).toBe("")
    expect(normalizeSourceField(undefined)).toBe("")
  })

  it("replaces multiple spaces with single underscore", () => {
    expect(normalizeSourceField("ai search")).toBe("ai_search")
  })
})

describe("isGlobalSource", () => {
  it("returns true for 'pearch'", () => {
    expect(isGlobalSource("pearch")).toBe(true)
  })

  it("returns true for 'global'", () => {
    expect(isGlobalSource("global")).toBe(true)
  })

  it("returns true for 'pearch_fast'", () => {
    expect(isGlobalSource("pearch_fast")).toBe(true)
  })

  it("returns true for 'apify_search' (fallback Apify nao some do balde global)", () => {
    expect(isGlobalSource("apify_search")).toBe(true)
  })

  it("returns true for 'apify' (enriquecimento Apify)", () => {
    expect(isGlobalSource("apify")).toBe(true)
  })

  it("returns false for 'local'", () => {
    expect(isGlobalSource("local")).toBe(false)
  })

  it("returns false for 'manual'", () => {
    expect(isGlobalSource("manual")).toBe(false)
  })
})

describe("isLocalSource", () => {
  it("returns true for 'local'", () => {
    expect(isLocalSource("local")).toBe(true)
  })

  it("returns false for 'pearch'", () => {
    expect(isLocalSource("pearch")).toBe(false)
  })

  it("returns true for 'csv'", () => {
    expect(isLocalSource("csv")).toBe(true)
  })
})

describe("getSourceDetails", () => {
  it("returns isGlobal true for pearch source", () => {
    const details = getSourceDetails("pearch")
    expect(details.isGlobal).toBe(true)
    expect(details.isLocal).toBe(false)
  })

  it("returns isLocal true for local source", () => {
    const details = getSourceDetails("local")
    expect(details.isLocal).toBe(true)
    expect(details.isGlobal).toBe(false)
  })

  it("includes credits for global sources", () => {
    const details = getSourceDetails("pearch_pro")
    expect(details.credits).toBeTruthy()
  })

  it("returns sensible label for manual import", () => {
    const details = getSourceDetails("manual")
    expect(details.label).toBe("Cadastro Manual")
  })
})

describe("getSourceCreditsEstimate", () => {
  it("returns 0 for local source", () => {
    expect(getSourceCreditsEstimate("local")).toBe(0)
  })

  it("returns 3 for pearch_fast", () => {
    expect(getSourceCreditsEstimate("pearch_fast")).toBe(3)
  })

  it("returns 7 for pearch_pro", () => {
    expect(getSourceCreditsEstimate("pearch_pro")).toBe(7)
  })

  it("returns 7 for generic pearch", () => {
    expect(getSourceCreditsEstimate("pearch")).toBe(7)
  })
})
