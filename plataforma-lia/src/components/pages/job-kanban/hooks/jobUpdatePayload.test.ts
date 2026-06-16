import { describe, it, expect } from "vitest"
import { buildJobUpdatePayload } from "./jobUpdatePayload"

// Onda 1 / O1.4 — the "Informações Gerais" save was rejected (HTTP 422) because the
// payload (a) sent RemoteCombobox objects {id,name} where the FastAPI JobVacancyUpdate
// schema (extra='forbid') expects scalars, and (b) included keys the schema doesn't
// accept (target_*, published_*, city, the unmapped `level`). This serializer is the
// single producer: it mirrors JobVacancyUpdate, coerces objects to scalars, and drops
// keys the backend forbids.

describe("buildJobUpdatePayload", () => {
  const form: Record<string, unknown> = {
    title: "Dev",
    department: { id: "d1", name: "Tecnologia" },
    priority: { id: "alta", name: "alta" },
    urgencyLevel: { id: 4, name: "4 — Alta" },
    type: { id: "CLT", name: "CLT" },
    level: { id: "Sênior", name: "Sênior" },
    workModel: "híbrido",
    status: "Ativa",
    city: { id: "c1", name: "São Paulo" },
    location: "São Paulo, SP",
    deadlineScreening: "2026-07-15",
    targetSector: "Tech",
    targetSegment: "Fintech",
    targetAudience: "x",
    publishedLinkedIn: true,
    publishedWebsite: true,
    isAffirmative: true,
    affirmativeCriteriaPrimary: "gender",
  }
  const fields = Object.keys(form)

  it("coerces combobox objects to scalar names", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect(p.department).toBe("Tecnologia")
    expect(p.priority).toBe("alta")
    expect(p.employment_type).toBe("CLT")
    expect(p.work_model).toBe("híbrido")
    expect(p.status).toBe("Ativa")
  })

  it("coerces urgency to a number", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect(p.urgency_level).toBe(4)
  })

  it("maps level -> seniority_level", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect(p.seniority_level).toBe("Sênior")
    expect("level" in p).toBe(false)
  })

  it("keeps deadlines and affirmative + location", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect(p.deadline_screening).toBe("2026-07-15")
    expect(p.is_affirmative).toBe(true)
    expect(p.affirmative_criteria_primary).toBe("gender")
    expect(p.location).toBe("São Paulo, SP")
  })

  it("drops keys the backend schema forbids (Mercado-Alvo, publicação)", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect("target_sector" in p).toBe(false)
    expect("target_segment" in p).toBe(false)
    expect("target_audience" in p).toBe(false)
    expect("published_linkedin" in p).toBe(false)
    expect("published_website" in p).toBe(false)
  })

  it("keeps city (persiste desde Onda 2B)", () => {
    const p = buildJobUpdatePayload(fields, form)
    expect(p.city).toBe("São Paulo")
  })

  it("builds salary_range from salaryMin/salaryMax", () => {
    const p = buildJobUpdatePayload(["salaryMin", "salaryMax"], { salaryMin: "5000", salaryMax: "8000" })
    expect(p.salary_range).toEqual({ min: 5000, max: 8000, currency: "BRL" })
  })

  it("maps manager/managerEmail to the canonical schema keys (not hiring_manager)", () => {
    const p = buildJobUpdatePayload(["manager", "managerEmail"], { manager: "Ana", managerEmail: "a@x.com" })
    expect(p.manager).toBe("Ana")
    expect(p.manager_email).toBe("a@x.com")
    expect("hiring_manager" in p).toBe(false)
    expect("hiring_manager_email" in p).toBe(false)
  })
})
