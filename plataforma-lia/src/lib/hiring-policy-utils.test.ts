import { describe, it, expect } from "vitest"
import {
  formatFieldValue,
  FIELD_CONFIGS,
  FIELD_LABELS,
  POLICY_BLOCKS,
} from "./hiring-policy-utils"

describe("formatFieldValue", () => {
  it("returns 'Nao definido' for null", () => {
    expect(formatFieldValue(null)).toBe("Nao definido")
  })

  it("returns 'Nao definido' for undefined", () => {
    expect(formatFieldValue(undefined)).toBe("Nao definido")
  })

  it("returns 'Sim' for true", () => {
    expect(formatFieldValue(true)).toBe("Sim")
  })

  it("returns 'Nao' for false", () => {
    expect(formatFieldValue(false)).toBe("Nao")
  })

  it("returns 'Nenhum' for empty array", () => {
    expect(formatFieldValue([])).toBe("Nenhum")
  })

  it("joins array values with comma", () => {
    expect(formatFieldValue(["a", "b", "c"])).toBe("a, b, c")
  })

  it("returns string representation of a number", () => {
    expect(formatFieldValue(42)).toBe("42")
  })

  it("returns string value unchanged", () => {
    expect(formatFieldValue("hello")).toBe("hello")
  })

  it("returns 'Nao definido' for empty object", () => {
    expect(formatFieldValue({})).toBe("Nao definido")
  })

  it("formats object entries as key: value", () => {
    const result = formatFieldValue({ status: "active" })
    expect(result).toContain("status: active")
  })
})

describe("FIELD_CONFIGS", () => {
  it("has entries for known fields", () => {
    expect(FIELD_CONFIGS["min_interviews_before_offer"]).toBeDefined()
    expect(FIELD_CONFIGS["manager_approval_for_offer"]).toBeDefined()
    expect(FIELD_CONFIGS["autonomy_level"]).toBeDefined()
  })

  it("each field has label and type", () => {
    for (const [, config] of Object.entries(FIELD_CONFIGS)) {
      expect(config.label).toBeTruthy()
      expect(config.type).toBeTruthy()
    }
  })

  it("select fields have options array", () => {
    const selectFields = Object.values(FIELD_CONFIGS).filter(c => c.type === "select")
    for (const field of selectFields) {
      expect(Array.isArray(field.options)).toBe(true)
      expect((field.options ?? []).length).toBeGreaterThan(0)
    }
  })
})

describe("FIELD_LABELS", () => {
  it("mirrors FIELD_CONFIGS labels", () => {
    for (const [key, config] of Object.entries(FIELD_CONFIGS)) {
      expect(FIELD_LABELS[key]).toBe(config.label)
    }
  })
})

describe("POLICY_BLOCKS", () => {
  it("has at least 4 policy blocks", () => {
    expect(POLICY_BLOCKS.length).toBeGreaterThanOrEqual(4)
  })

  it("each block has key, title, iconName, and fields", () => {
    for (const block of POLICY_BLOCKS) {
      expect(block.key).toBeTruthy()
      expect(block.title).toBeTruthy()
      expect(block.iconName).toBeTruthy()
      expect(Array.isArray(block.fields)).toBe(true)
    }
  })

  it("automation block contains auto_screening", () => {
    const automationBlock = POLICY_BLOCKS.find(b => b.key === "automation_rules")
    expect(automationBlock?.fields).toContain("auto_screening")
  })
})
