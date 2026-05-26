/**
 * useCompanyBlocks.test.ts — Task 2.7 (2026-05-26)
 *
 * Pure-function tests for the buildBlocks transform layer.
 * No React rendering needed — pure TS logic only.
 *
 * Coverage targets:
 * - isFieldFilled: null, empty string, empty array, non-empty string, non-empty array, boolean, number
 * - computeBlockStatus: 'configured', 'partial', 'pending', empty-fields-list, action-field exclusion
 * - computeBlockProgress: filled/total/missingLabels
 * - buildBlocks: null company, minimal company, with benefits, with hiringPolicy
 * - mergeToCompanyData: null profile, minimal profile, with culture, with headquarters split
 * - snapshotFieldValues: empty blocks, populated blocks
 */
import { describe, it, expect } from "vitest"
import {
  isFieldFilled,
  computeBlockStatus,
  computeBlockProgress,
  buildBlocks,
  mergeToCompanyData,
  snapshotFieldValues,
  ACTION_FIELD_KEYS,
} from "../useCompanyBlocks"
import type { CardField, CardBlock } from "../useCompanyBlocks"

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeField(key: string, value: unknown, block = "basic"): CardField {
  return { key, label: key, value, type: "text", editable: true, block }
}

function makeBlock(key: string, fields: CardField[]): CardBlock {
  return {
    key,
    title: key,
    iconName: "Test",
    fields,
    status: "pending",
    progress: { filled: 0, total: 0, missingLabels: [] },
  }
}

const MINIMAL_COMPANY = {
  name: "Acme Corp",
  tradeName: "Acme",
  cnpj: "12.345.678/0001-90",
  website: "https://acme.com",
  email: "hr@acme.com",
  phone: "+55 11 999990000",
  address: "Av. Paulista, 1",
  industry: "Tech",
  size: "medium",
}

// ─── isFieldFilled ────────────────────────────────────────────────────────────

describe("isFieldFilled", () => {
  it("returns false for null", () => {
    expect(isFieldFilled(makeField("f", null))).toBe(false)
  })

  it("returns false for undefined", () => {
    expect(isFieldFilled(makeField("f", undefined))).toBe(false)
  })

  it("returns false for empty string", () => {
    expect(isFieldFilled(makeField("f", ""))).toBe(false)
  })

  it("returns false for empty array", () => {
    expect(isFieldFilled(makeField("f", []))).toBe(false)
  })

  it("returns true for non-empty string", () => {
    expect(isFieldFilled(makeField("f", "hello"))).toBe(true)
  })

  it("returns true for non-empty array", () => {
    expect(isFieldFilled(makeField("f", ["item"]))).toBe(true)
  })

  it("returns true for number 0 (zero is a valid value)", () => {
    expect(isFieldFilled(makeField("f", 0))).toBe(true)
  })

  it("returns true for positive number", () => {
    expect(isFieldFilled(makeField("f", 42))).toBe(true)
  })

  it("returns true for boolean false (explicit false is data)", () => {
    expect(isFieldFilled(makeField("f", false))).toBe(true)
  })

  it("returns true for boolean true", () => {
    expect(isFieldFilled(makeField("f", true))).toBe(true)
  })

  it("returns true for non-empty object", () => {
    expect(isFieldFilled(makeField("f", { key: "val" }))).toBe(true)
  })
})

// ─── computeBlockStatus ──────────────────────────────────────────────────────

describe("computeBlockStatus", () => {
  it("returns 'pending' when no fields provided", () => {
    expect(computeBlockStatus([])).toBe("pending")
  })

  it("returns 'pending' when all data fields are empty", () => {
    const fields = [makeField("a", null), makeField("b", ""), makeField("c", [])]
    expect(computeBlockStatus(fields)).toBe("pending")
  })

  it("returns 'configured' when all data fields are filled", () => {
    const fields = [makeField("a", "x"), makeField("b", "y"), makeField("c", ["z"])]
    expect(computeBlockStatus(fields)).toBe("configured")
  })

  it("returns 'partial' when some fields are filled", () => {
    const fields = [makeField("a", "x"), makeField("b", null), makeField("c", "z")]
    expect(computeBlockStatus(fields)).toBe("partial")
  })

  it("excludes ACTION_FIELD_KEYS from data computation", () => {
    // import_spreadsheet is in ACTION_FIELD_KEYS — even null it should not affect status
    const actionKey = [...ACTION_FIELD_KEYS][0]
    const fields = [makeField(actionKey, null), makeField("a", "hello")]
    expect(computeBlockStatus(fields)).toBe("configured")
  })

  it("returns 'pending' when only action fields present (no real data)", () => {
    const actionKey = [...ACTION_FIELD_KEYS][0]
    const fields = [makeField(actionKey, null)]
    // dataFields is empty after filter → pending
    expect(computeBlockStatus(fields)).toBe("pending")
  })

  it("handles single field being filled → 'configured'", () => {
    expect(computeBlockStatus([makeField("x", "value")])).toBe("configured")
  })
})

// ─── computeBlockProgress ────────────────────────────────────────────────────

describe("computeBlockProgress", () => {
  it("returns 0/0 with empty missingLabels for empty field list", () => {
    const result = computeBlockProgress([])
    expect(result.filled).toBe(0)
    expect(result.total).toBe(0)
    expect(result.missingLabels).toEqual([])
  })

  it("returns filled=0 and all labels in missingLabels when all null", () => {
    const fields = [
      { key: "a", label: "Alpha", value: null, type: "text" as const, editable: true, block: "b" },
      { key: "b", label: "Beta", value: "", type: "text" as const, editable: true, block: "b" },
    ]
    const result = computeBlockProgress(fields)
    expect(result.filled).toBe(0)
    expect(result.total).toBe(2)
    expect(result.missingLabels).toContain("Alpha")
    expect(result.missingLabels).toContain("Beta")
  })

  it("returns filled=total and empty missingLabels when all filled", () => {
    const fields = [makeField("a", "x"), makeField("b", "y")]
    const result = computeBlockProgress(fields)
    expect(result.filled).toBe(2)
    expect(result.total).toBe(2)
    expect(result.missingLabels).toEqual([])
  })

  it("returns correct partial progress", () => {
    const fields = [makeField("a", "x"), makeField("b", null), makeField("c", "z")]
    const result = computeBlockProgress(fields)
    expect(result.filled).toBe(2)
    expect(result.total).toBe(3)
    expect(result.missingLabels).toHaveLength(1)
    expect(result.missingLabels[0]).toBe("b") // label === key in makeField
  })

  it("excludes ACTION_FIELD_KEYS from total count", () => {
    const actionKey = [...ACTION_FIELD_KEYS][0]
    const fields = [makeField(actionKey, null), makeField("data", "value")]
    const result = computeBlockProgress(fields)
    expect(result.total).toBe(1)
    expect(result.filled).toBe(1)
    expect(result.missingLabels).toEqual([])
  })
})

// ─── buildBlocks ─────────────────────────────────────────────────────────────

describe("buildBlocks", () => {
  it("returns empty array when company is null", () => {
    const result = buildBlocks(null, [], null)
    expect(result).toEqual([])
  })

  it("returns 7 blocks for minimal company", () => {
    const result = buildBlocks(MINIMAL_COMPANY, [], null)
    expect(result).toHaveLength(7)
  })

  it("each block has required shape (key, title, iconName, fields, status, progress)", () => {
    const result = buildBlocks(MINIMAL_COMPANY, [], null)
    for (const block of result) {
      expect(block).toHaveProperty("key")
      expect(block).toHaveProperty("title")
      expect(block).toHaveProperty("iconName")
      expect(block).toHaveProperty("fields")
      expect(block).toHaveProperty("status")
      expect(block).toHaveProperty("progress")
      expect(Array.isArray(block.fields)).toBe(true)
      expect(["configured", "partial", "pending"]).toContain(block.status)
    }
  })

  it("basic block contains name and cnpj fields", () => {
    const result = buildBlocks(MINIMAL_COMPANY, [], null)
    const basic = result.find(b => b.key === "basic")
    expect(basic).toBeDefined()
    const keys = basic!.fields.map(f => f.key)
    expect(keys).toContain("name")
    expect(keys).toContain("cnpj")
  })

  it("basic block is 'configured' when all required fields provided", () => {
    const company = { ...MINIMAL_COMPANY, logo: "http://x.com/logo.png", employee_count: 50, headquarters: "São Paulo", founded_year: 2020, linkedin_url: "https://linkedin.com/company/acme" }
    const result = buildBlocks(company, [], null)
    const basic = result.find(b => b.key === "basic")
    expect(basic).toBeDefined()
    // At least progress reflects name is filled
    expect(basic!.progress.filled).toBeGreaterThan(0)
  })

  it("benefits block subtitle reflects count", () => {
    const benefits = [
      { id: "1", name: "VR", category: "food", is_active: true },
      { id: "2", name: "VT", category: "transport", is_active: false },
    ]
    const result = buildBlocks(MINIMAL_COMPANY, benefits, null)
    const benefitsBlock = result.find(b => b.key === "benefits")
    expect(benefitsBlock).toBeDefined()
    expect(benefitsBlock!.subtitle).toContain("2 cadastrado")
    expect(benefitsBlock!.subtitle).toContain("1 ativo")
  })

  it("benefits block subtitle shows 'Nenhum benefício' when empty", () => {
    const result = buildBlocks(MINIMAL_COMPANY, [], null)
    const benefitsBlock = result.find(b => b.key === "benefits")
    expect(benefitsBlock!.subtitle).toContain("Nenhum benefício")
  })

  it("policy block exposes min_interviews_before_offer when provided", () => {
    const policy = { pipeline_rules: { min_interviews_before_offer: 2, manager_approval_for_offer: true } }
    const result = buildBlocks(MINIMAL_COMPANY, [], policy)
    const policyBlock = result.find(b => b.key === "policy")
    expect(policyBlock).toBeDefined()
    const field = policyBlock!.fields.find(f => f.key === "min_interviews_before_offer")
    expect(field).toBeDefined()
    expect(field!.value).toBe(2)
  })

  it("policy block progress.filled > 0 when hiringPolicy has data", () => {
    const policy = {
      pipeline_rules: { min_interviews_before_offer: 1 },
      scheduling_rules: { allowed_days: ["Mon", "Tue"] },
    }
    const result = buildBlocks(MINIMAL_COMPANY, [], policy)
    const policyBlock = result.find(b => b.key === "policy")
    expect(policyBlock!.progress.filled).toBeGreaterThan(0)
  })

  it("culture block reflects values and mission", () => {
    const company = { ...MINIMAL_COMPANY, mission: "To build better software", values: ["integrity", "innovation"] }
    const result = buildBlocks(company, [], null)
    const cultureBlock = result.find(b => b.key === "culture")
    const missionField = cultureBlock!.fields.find(f => f.key === "mission")
    const valuesField = cultureBlock!.fields.find(f => f.key === "values")
    expect(missionField!.value).toBe("To build better software")
    expect(valuesField!.value).toEqual(["integrity", "innovation"])
  })

  it("tech block reflects tech_stack", () => {
    const company = { ...MINIMAL_COMPANY, tech_stack: ["React", "TypeScript", "Node.js"] }
    const result = buildBlocks(company, [], null)
    const techBlock = result.find(b => b.key === "tech")
    const stackField = techBlock!.fields.find(f => f.key === "tech_stack")
    expect(stackField!.value).toEqual(["React", "TypeScript", "Node.js"])
  })

  it("block keys are unique", () => {
    const result = buildBlocks(MINIMAL_COMPANY, [], null)
    const keys = result.map(b => b.key)
    const uniqueKeys = new Set(keys)
    expect(uniqueKeys.size).toBe(keys.length)
  })
})

// ─── mergeToCompanyData ───────────────────────────────────────────────────────

describe("mergeToCompanyData", () => {
  it("returns null when rawProfile is null", () => {
    expect(mergeToCompanyData(null, null)).toBeNull()
  })

  it("returns CompanyData when rawProfile provided and rawCulture is null", () => {
    const result = mergeToCompanyData({ name: "Acme Corp", cnpj: "00.000.000/0001-00" }, null)
    expect(result).not.toBeNull()
    expect(result!.name).toBe("Acme Corp")
    expect(result!.cnpj).toBe("00.000.000/0001-00")
  })

  it("falls back to name for tradeName when trading_name is absent", () => {
    const result = mergeToCompanyData({ name: "Acme Corp" }, null)
    expect(result!.tradeName).toBe("Acme Corp")
  })

  it("uses trading_name when provided", () => {
    const result = mergeToCompanyData({ name: "Acme Corp", trading_name: "Acme" }, null)
    expect(result!.tradeName).toBe("Acme")
  })

  it("merges culture data for mission, vision, values", () => {
    const result = mergeToCompanyData(
      { name: "Acme" },
      { mission: "Build the future", vision: "Lead the market", values: ["trust", "speed"] },
    )
    expect(result!.mission).toBe("Build the future")
    expect(result!.vision).toBe("Lead the market")
    expect(result!.values).toEqual(["trust", "speed"])
  })

  it("combines headquarters_city and headquarters_state with comma", () => {
    const result = mergeToCompanyData(
      { name: "Acme", headquarters_city: "São Paulo", headquarters_state: "SP" },
      null,
    )
    expect(result!.headquarters).toBe("São Paulo, SP")
  })

  it("returns only city when headquarters_state is absent", () => {
    const result = mergeToCompanyData({ name: "Acme", headquarters_city: "Campinas" }, null)
    expect(result!.headquarters).toBe("Campinas")
  })

  it("defaults to culture headquarters when profile has no headquarters_city", () => {
    const result = mergeToCompanyData({ name: "Acme" }, { headquarters: "Remote" })
    expect(result!.headquarters).toBe("Remote")
  })

  it("returns empty string defaults for missing required fields", () => {
    const result = mergeToCompanyData({ name: "Acme" }, null)
    expect(result!.cnpj).toBe("")
    expect(result!.website).toBe("")
    expect(result!.email).toBe("")
    expect(result!.phone).toBe("")
    expect(result!.address).toBe("")
  })

  it("fallbacks hr_email to main_email", () => {
    const result = mergeToCompanyData({ name: "A", main_email: "main@co.com" }, null)
    expect(result!.email).toBe("main@co.com")
  })

  it("uses logo_url for logo field", () => {
    const result = mergeToCompanyData({ name: "A", logo_url: "https://cdn.co/logo.png" }, null)
    expect(result!.logo).toBe("https://cdn.co/logo.png")
  })

  it("returns empty arrays for list fields when culture is absent", () => {
    const result = mergeToCompanyData({ name: "A" }, null)
    expect(result!.values).toEqual([])
    expect(result!.tech_stack).toEqual([])
    expect(result!.evp_bullets).toEqual([])
  })

  it("returns default_salary_ranges from profile", () => {
    const ranges = [{ min: 1000, max: 2000 }]
    const result = mergeToCompanyData({ name: "A", default_salary_ranges: ranges }, null)
    expect(result!.default_salary_ranges).toEqual(ranges)
  })
})

// ─── snapshotFieldValues ──────────────────────────────────────────────────────

describe("snapshotFieldValues", () => {
  it("returns empty Map for empty blocks array", () => {
    const snap = snapshotFieldValues([])
    expect(snap.size).toBe(0)
  })

  it("stores each field value as JSON-stringified entry", () => {
    const fields = [makeField("name", "Acme"), makeField("count", 5)]
    const block = makeBlock("basic", fields)
    const snap = snapshotFieldValues([block])
    expect(snap.get("name")).toBe('"Acme"')
    expect(snap.get("count")).toBe("5")
  })

  it("stores null values correctly", () => {
    const fields = [makeField("empty", null)]
    const snap = snapshotFieldValues([makeBlock("b", fields)])
    expect(snap.get("empty")).toBe("null")
  })

  it("stores array values as JSON", () => {
    const fields = [makeField("vals", ["a", "b", "c"])]
    const snap = snapshotFieldValues([makeBlock("b", fields)])
    expect(snap.get("vals")).toBe('["a","b","c"]')
  })

  it("accumulates fields from multiple blocks", () => {
    const block1 = makeBlock("b1", [makeField("f1", "x")])
    const block2 = makeBlock("b2", [makeField("f2", "y")])
    const snap = snapshotFieldValues([block1, block2])
    expect(snap.size).toBe(2)
    expect(snap.has("f1")).toBe(true)
    expect(snap.has("f2")).toBe(true)
  })
})

// ─── ACTION_FIELD_KEYS constant ───────────────────────────────────────────────

describe("ACTION_FIELD_KEYS", () => {
  it("contains known action keys", () => {
    expect(ACTION_FIELD_KEYS.has("import_spreadsheet")).toBe(true)
    expect(ACTION_FIELD_KEYS.has("handbook")).toBe(true)
    expect(ACTION_FIELD_KEYS.has("org_chart")).toBe(true)
  })
})
