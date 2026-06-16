import { describe, it, expect } from "vitest"
import {
  getAllVariables,
  getVariableByKey,
  getGroupByVariableKey,
  formatVariable,
  extractVariables,
  validateVariables,
  VARIABLE_REGISTRY,
} from "./template-variables"

describe("VARIABLE_REGISTRY", () => {
  it("has multiple groups", () => {
    expect(VARIABLE_REGISTRY.length).toBeGreaterThan(0)
  })

  it("each group has id, label and variables array", () => {
    for (const group of VARIABLE_REGISTRY) {
      expect(group.id).toBeTruthy()
      expect(group.label).toBeTruthy()
      expect(Array.isArray(group.variables)).toBe(true)
    }
  })
})

describe("getAllVariables", () => {
  it("returns a flat array of all variables", () => {
    const all = getAllVariables()
    expect(Array.isArray(all)).toBe(true)
    expect(all.length).toBeGreaterThan(0)
  })

  it("each variable has key, label, and description", () => {
    const all = getAllVariables()
    for (const variable of all) {
      expect(variable.key).toBeTruthy()
      expect(variable.label).toBeTruthy()
      expect(variable.description).toBeTruthy()
    }
  })
})

describe("getVariableByKey", () => {
  it("returns variable for known key 'candidato_nome'", () => {
    const v = getVariableByKey("candidato_nome")
    expect(v).toBeDefined()
    expect(v?.key).toBe("candidato_nome")
  })

  it("returns undefined for unknown key", () => {
    const v = getVariableByKey("non_existent_key_xyz")
    expect(v).toBeUndefined()
  })
})

describe("getGroupByVariableKey", () => {
  it("returns the correct group for 'job_title'", () => {
    const group = getGroupByVariableKey("job_title")
    expect(group).toBeDefined()
    expect(group?.id).toBe("vaga")
  })

  it("returns undefined for unknown variable key", () => {
    const group = getGroupByVariableKey("unknown_xyz_abc")
    expect(group).toBeUndefined()
  })
})

describe("formatVariable", () => {
  it("wraps key in double curly braces", () => {
    expect(formatVariable("candidato_nome")).toBe("{{candidato_nome}}")
  })

  it("works for any string key", () => {
    expect(formatVariable("my_key")).toBe("{{my_key}}")
  })
})

describe("extractVariables", () => {
  it("extracts a single variable from text", () => {
    const vars = extractVariables("Olá {{candidato_nome}}!")
    expect(vars).toContain("candidato_nome")
  })

  it("extracts multiple variables", () => {
    const vars = extractVariables("{{vaga}} em {{company_name}}")
    expect(vars).toContain("vaga")
    expect(vars).toContain("company_name")
  })

  it("returns empty array for text with no variables", () => {
    expect(extractVariables("plain text")).toEqual([])
  })

  it("deduplicates repeated variables", () => {
    const vars = extractVariables("{{vaga}} and {{vaga}}")
    expect(vars.filter(v => v === "vaga")).toHaveLength(1)
  })
})

describe("validateVariables", () => {
  it("returns valid list for known keys", () => {
    const result = validateVariables("Olá {{candidato_nome}}, sua {{vaga}} foi aprovada")
    expect(result.valid).toContain("candidato_nome")
    expect(result.valid).toContain("vaga")
  })

  it("returns invalid list for unknown keys", () => {
    const result = validateVariables("{{unknown_xyz}} and {{another_invalid}}")
    expect(result.invalid).toContain("unknown_xyz")
    expect(result.invalid).toContain("another_invalid")
  })

  it("separates valid and invalid keys", () => {
    const result = validateVariables("{{candidato_nome}} {{invalid_key_xyz}}")
    expect(result.valid).toContain("candidato_nome")
    expect(result.invalid).toContain("invalid_key_xyz")
  })
})
