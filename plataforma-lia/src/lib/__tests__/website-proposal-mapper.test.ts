import { describe, it, expect } from "vitest"
import {
  mapExtractedToProposedSaves,
  payloadHash,
} from "@/lib/website-proposal-mapper"

describe("website-proposal-mapper (Task #1180)", () => {
  it("produces 4 blocks at most, never includes workforce_plan", () => {
    const extracted = {
      mission: "Mudar o mundo",
      values: ["transparência", "inovação"],
      tech_stack: ["React", "Node", "AWS"],
      engineering_culture: "trunk-based + CI/CD",
      industry: "Fintech",
      employee_count: 120,
      headquarters: "São Paulo, SP",
      // Pista de workforce que o LLM PODERIA extrair no futuro:
      workforce_plan: [{ department: "Eng", quantity: 5 }],
      headcount_target: 200,
    }
    const proposed = mapExtractedToProposedSaves(extracted)
    const blockKeys = proposed.blocks.map((b) => b.key)
    expect(blockKeys).not.toContain("workforce")
    expect(blockKeys.length).toBeLessThanOrEqual(4)
    for (const blk of proposed.blocks) {
      for (const f of blk.fields) {
        expect(f.key).not.toMatch(/workforce|headcount|hiring_plan/i)
      }
    }
  })

  it("basic_complementary respects updateExisting=false (skips filled)", () => {
    const extracted = { industry: "Fintech", employee_count: 50 }
    const proposed = mapExtractedToProposedSaves(extracted, {
      existingBasic: { industry: "Tecnologia" },
      updateExisting: false,
    })
    const basic = proposed.blocks.find((b) => b.key === "basic_complementary")
    expect(basic).toBeDefined()
    const industryField = basic?.fields.find((f) => f.key === "industry")
    expect(industryField).toBeUndefined()
    const empField = basic?.fields.find((f) => f.key === "employee_count")
    expect(empField?.value).toBe(50)
  })

  it("basic_complementary updateExisting=true overrides filled values", () => {
    const extracted = { industry: "Fintech" }
    const proposed = mapExtractedToProposedSaves(extracted, {
      existingBasic: { industry: "Tecnologia" },
      updateExisting: true,
    })
    const basic = proposed.blocks.find((b) => b.key === "basic_complementary")
    expect(basic?.fields.some((f) => f.key === "industry")).toBe(true)
  })

  it("emits no blocks for empty extraction", () => {
    const proposed = mapExtractedToProposedSaves({})
    expect(proposed.blocks).toEqual([])
  })

  it("payload hash is deterministic and changes on payload change", () => {
    const h1 = payloadHash([{ key: "culture", fields: [{ key: "mission", value: "X" }] }])
    const h2 = payloadHash([{ key: "culture", fields: [{ key: "mission", value: "X" }] }])
    const h3 = payloadHash([{ key: "culture", fields: [{ key: "mission", value: "Y" }] }])
    expect(h1).toBe(h2)
    expect(h1).not.toBe(h3)
  })
})
