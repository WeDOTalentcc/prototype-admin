import { describe, it, expect } from "vitest"
import { extractTagsFromSearchSpec, suggestArchetypeName, extractIndustryFromSpec, extractSeniorityFromSpec } from "./extract-tags-from-search"

const basicSpec = {
  job_title: "Engenheiro de Software",
  seniority: "senior",
  location: "São Paulo, SP",
  years_experience: "5+ anos",
  skills: ["TypeScript", "React", "Node.js"],
  work_model: "remote",
}

describe("extractTagsFromSearchSpec", () => {
  it("returns empty array for null spec", () => {
    expect(extractTagsFromSearchSpec(null)).toEqual([])
    expect(extractTagsFromSearchSpec(undefined)).toEqual([])
  })

  it("extracts job_title tag", () => {
    const tags = extractTagsFromSearchSpec(basicSpec as never)
    const jobTag = tags.find(t => t.type === "job_title")
    expect(jobTag).toBeDefined()
    expect(jobTag?.value).toBe("Engenheiro de Software")
  })

  it("extracts seniority tag with Portuguese label", () => {
    const tags = extractTagsFromSearchSpec(basicSpec as never)
    const seniorityTag = tags.find(t => t.type === "seniority")
    expect(seniorityTag?.value).toBe("Sênior")
  })

  it("extracts skill tags (up to 5)", () => {
    const tags = extractTagsFromSearchSpec(basicSpec as never)
    const skillTags = tags.filter(t => t.type === "skill")
    expect(skillTags.length).toBeGreaterThan(0)
    expect(skillTags.length).toBeLessThanOrEqual(5)
  })

  it("extracts work_model tag with Portuguese label", () => {
    const tags = extractTagsFromSearchSpec(basicSpec as never)
    const workModelTag = tags.find(t => t.type === "work_model")
    expect(workModelTag?.value).toBe("Remoto")
  })

  it("uses industries array if industry field missing", () => {
    const spec = { industries: ["Tecnologia"] }
    const tags = extractTagsFromSearchSpec(spec as never)
    const industryTag = tags.find(t => t.type === "industry")
    expect(industryTag?.value).toBe("Tecnologia")
  })
})

describe("suggestArchetypeName", () => {
  it("returns 'Novo Arquétipo' for null spec", () => {
    expect(suggestArchetypeName(null)).toBe("Novo Arquétipo")
  })

  it("combines job_title and seniority", () => {
    const name = suggestArchetypeName(basicSpec as never)
    expect(name).toContain("Engenheiro de Software")
    expect(name).toContain("Sênior")
  })

  it("falls back to first skill if no title/seniority", () => {
    const name = suggestArchetypeName({ skills: ["Python"] } as never)
    expect(name).toBe("Python")
  })

  it("returns 'Novo Arquétipo' when no identifying info", () => {
    const name = suggestArchetypeName({} as never)
    expect(name).toBe("Novo Arquétipo")
  })
})

describe("extractIndustryFromSpec", () => {
  it("returns empty string for null spec", () => {
    expect(extractIndustryFromSpec(null)).toBe("")
  })

  it("returns industry field value", () => {
    expect(extractIndustryFromSpec({ industry: "FinTech" } as never)).toBe("FinTech")
  })

  it("falls back to first item in industries array", () => {
    expect(extractIndustryFromSpec({ industries: ["Healthcare"] } as never)).toBe("Healthcare")
  })
})

describe("extractSeniorityFromSpec", () => {
  it("returns empty string for null spec", () => {
    expect(extractSeniorityFromSpec(null)).toBe("")
  })

  it("returns lowercased seniority", () => {
    expect(extractSeniorityFromSpec({ seniority: "Senior" } as never)).toBe("senior")
  })
})
