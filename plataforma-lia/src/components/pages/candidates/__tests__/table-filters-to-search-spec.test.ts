import { describe, it, expect } from "vitest"
import { tableFiltersToSearchSpec } from "../filters/tableFiltersToSearchSpec"

const base = {
  statuses: [], tags: [], seniorityLevels: [], workModels: [], contractTypes: [],
  locations: [], remoteOnly: false, hasEmail: false, hasPhone: false, hasLinkedin: false,
  sources: [], jobTitles: [], skills: [], companies: [], industries: [], companySizes: [],
  universities: [], degrees: [], fieldsOfStudy: [], languages: [], isOpenToWork: false,
  isDecisionMaker: false, isTopUniversities: false, isStartup: false, hasGithub: false,
  hasPortfolio: false, softSkills: [], certifications: [], willingToRelocate: null, mobility: null,
} as any

describe("tableFiltersToSearchSpec", () => {
  it("vazio quando nenhum filtro de referencia ativo", () => {
    expect(tableFiltersToSearchSpec(base, {})).toEqual({})
  })

  it("mapeia skills (table + advanced, dedup)", () => {
    const spec = tableFiltersToSearchSpec({ ...base, skills: ["Python"] }, { skills: ["AWS", "Python"] })
    expect(spec.skills).toEqual(expect.arrayContaining(["Python", "AWS"]))
    expect((spec.skills as string[]).length).toBe(2)
  })

  it("location/job_title/seniority como valor unico (primeiro)", () => {
    const spec = tableFiltersToSearchSpec(
      { ...base, locations: ["Sao Paulo", "Rio"], jobTitles: ["Engenheiro"], seniorityLevels: ["senior"] }, {},
    )
    expect(spec.location).toBe("Sao Paulo")
    expect(spec.job_title).toBe("Engenheiro")
    expect(spec.seniority).toBe("senior")
  })

  it("companies/industries/languages como listas", () => {
    const spec = tableFiltersToSearchSpec(
      { ...base, companies: ["Nubank"], industries: ["fintech"], languages: ["en"] }, {},
    )
    expect(spec.companies).toEqual(["Nubank"])
    expect(spec.industries).toEqual(["fintech"])
    expect(spec.languages).toEqual(["en"])
  })

  it("experiencia e salario numericos", () => {
    const spec = tableFiltersToSearchSpec({ ...base, minExperience: 3, maxExperience: 8, minSalary: 5000 }, {})
    expect(spec.years_experience_min).toBe(3)
    expect(spec.years_experience_max).toBe(8)
    expect(spec.salary_min).toBe(5000)
  })

  it("work_model traduz pt->en", () => {
    expect(tableFiltersToSearchSpec({ ...base, workModels: ["remoto"] }, {}).work_model).toBe("remote")
    expect(tableFiltersToSearchSpec({ ...base, workModels: ["híbrido"] }, {}).work_model).toBe("hybrid")
  })

  it("nao inclui filtros utilitarios (hasEmail)", () => {
    const spec = tableFiltersToSearchSpec({ ...base, hasEmail: true }, {})
    expect(spec.has_email).toBeUndefined()
    expect(spec).toEqual({})
  })
})
