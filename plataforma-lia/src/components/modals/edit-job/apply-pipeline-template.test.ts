/**
 * Tests — `applyPipelineTemplateCore` canonical endpoint dispatch
 * (Sprint Pipeline Templates Gap #4)
 *
 * Producer canonical: POST /api/backend-proxy/job-vacancies/{id}/apply-pipeline-template
 *   → backend `PipelineTemplateService.apply_to_vacancy` emits audit log (LGPD/SOX).
 * Consumer (this helper, used by `useEditJob.applyPipelineTemplate`): MUST call
 * the canonical endpoint when `vacancyId` is present (edit mode). When
 * `vacancyId` is null/undefined (create mode), keep state-local apply — stages
 * persist with the vacancy on save.
 *
 * Three scenarios:
 *   1. edit mode + endpoint 200 → mode='persisted', stages translated
 *   2. create mode (no vacancyId)  → mode='local', increment-usage legacy fired
 *   3. edit mode + endpoint 422   → mode='error', state must NOT mutate
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import {
  applyPipelineTemplateCore,
  translateTemplateStages,
} from "./apply-pipeline-template"
import type { PipelineTemplate } from "./edit-job.types"

const TEMPLATE: PipelineTemplate = {
  id: "tmpl-canonical-uuid",
  name: "Pipeline Canonical Tech",
  stages: [
    { id: "s1", name: "Triagem CV", order: 1, sla_days: 2, type: "automatic" },
    { id: "s2", name: "Entrevista RH", order: 2, sla_days: 3, type: "manual" },
    { id: "s3", name: "Tech Test", order: 3, sla_days: 5, type: "hybrid" },
    { id: "s4", name: "Entrevista Final", order: 4, sla_days: 3, type: "manual" },
    { id: "s5", name: "Oferta", order: 5, sla_days: 1, type: "manual" },
  ],
  description: "Canonical 5-stage pipeline",
  is_default: true,
  usage_count: 7,
} as unknown as PipelineTemplate

function makeFetchMock(
  endpointBehavior: "success" | "error",
): {
  fetchImpl: typeof fetch
  calls: Array<{ url: string; init?: RequestInit }>
} {
  const calls: Array<{ url: string; init?: RequestInit }> = []
  const fetchImpl = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
    const u = String(url)
    calls.push({ url: u, init })
    if (u.includes("/apply-pipeline-template")) {
      if (endpointBehavior === "error") {
        return new Response(
          JSON.stringify({ detail: "Template scope mismatch" }),
          { status: 422 },
        )
      }
      return new Response(
        JSON.stringify({
          vacancy_id: "backend-uuid-1",
          template_id: TEMPLATE.id,
          template_name: TEMPLATE.name,
          stages_applied: 5,
          usage_count: 8,
          source: "manual_modal",
        }),
        { status: 200 },
      )
    }
    if (u.includes("/increment-usage")) {
      return new Response("{}", { status: 200 })
    }
    return new Response("{}", { status: 200 })
  }) as unknown as typeof fetch
  return { fetchImpl, calls }
}

describe("translateTemplateStages", () => {
  it("maps backend stage shape to InterviewStage with 'automatic' → 'automated'", () => {
    const stages = translateTemplateStages(TEMPLATE)
    expect(stages).toHaveLength(5)
    expect(stages[0]).toMatchObject({
      stageName: "Triagem CV",
      order: 1,
      sla: 2,
      type: "automated",
    })
    expect(stages[1].type).toBe("manual")
    expect(stages[2].type).toBe("hybrid")
  })
})

describe("applyPipelineTemplateCore — edit mode (vacancyId exists)", () => {
  let mock: ReturnType<typeof makeFetchMock>

  beforeEach(() => {
    mock = makeFetchMock("success")
  })

  it("calls canonical apply endpoint with POST + correct body, returns mode='persisted'", async () => {
    const result = await applyPipelineTemplateCore(
      { vacancyId: "backend-uuid-1", template: TEMPLATE, fetchImpl: mock.fetchImpl },
      TEMPLATE.id,
    )

    expect(result.mode).toBe("persisted")
    if (result.mode !== "persisted") throw new Error("unreachable")
    expect(result.stages).toHaveLength(5)
    expect(result.stages[0]).toMatchObject({
      stageName: "Triagem CV",
      type: "automated",
    })
    expect(result.templateName).toBe(TEMPLATE.name)

    const applyCall = mock.calls.find((c) =>
      c.url.includes("/apply-pipeline-template"),
    )
    expect(applyCall).toBeDefined()
    expect(applyCall!.url).toBe(
      "/api/backend-proxy/job-vacancies/backend-uuid-1/apply-pipeline-template",
    )
    expect(applyCall!.init?.method).toBe("POST")
    const body = JSON.parse(String(applyCall!.init?.body))
    expect(body).toEqual({ template_id: TEMPLATE.id, source: "manual_modal" })

    // canonical path: NO increment-usage legacy fire-and-forget
    const incCall = mock.calls.find((c) => c.url.includes("/increment-usage"))
    expect(incCall).toBeUndefined()
  })
})

describe("applyPipelineTemplateCore — create mode (no vacancyId)", () => {
  it("skips canonical endpoint, returns mode='local', fires legacy increment-usage", async () => {
    const mock = makeFetchMock("success")

    const result = await applyPipelineTemplateCore(
      { vacancyId: null, template: TEMPLATE, fetchImpl: mock.fetchImpl },
      TEMPLATE.id,
    )

    expect(result.mode).toBe("local")
    if (result.mode !== "local") throw new Error("unreachable")
    expect(result.stages).toHaveLength(5)
    expect(result.templateName).toBe(TEMPLATE.name)

    // canonical apply NOT called
    expect(
      mock.calls.find((c) => c.url.includes("/apply-pipeline-template")),
    ).toBeUndefined()
    // legacy increment-usage IS called
    expect(
      mock.calls.find((c) => c.url.includes("/increment-usage")),
    ).toBeDefined()
  })

  it("returns mode='local' when vacancyId is undefined", async () => {
    const mock = makeFetchMock("success")
    const result = await applyPipelineTemplateCore(
      { vacancyId: undefined, template: TEMPLATE, fetchImpl: mock.fetchImpl },
      TEMPLATE.id,
    )
    expect(result.mode).toBe("local")
  })
})

describe("applyPipelineTemplateCore — edit mode endpoint error", () => {
  it("returns mode='error' with descriptive message on 422 (no state mutation)", async () => {
    const mock = makeFetchMock("error")

    const result = await applyPipelineTemplateCore(
      { vacancyId: "backend-uuid-1", template: TEMPLATE, fetchImpl: mock.fetchImpl },
      TEMPLATE.id,
    )

    expect(result.mode).toBe("error")
    if (result.mode !== "error") throw new Error("unreachable")
    expect(result.message).toContain("Erro ao aplicar template")
    expect(result.message).toContain("Template scope mismatch")
  })

  it("returns mode='error' on network exception", async () => {
    const throwingFetch = vi.fn(async () => {
      throw new Error("ECONNREFUSED")
    }) as unknown as typeof fetch

    const result = await applyPipelineTemplateCore(
      {
        vacancyId: "backend-uuid-1",
        template: TEMPLATE,
        fetchImpl: throwingFetch,
      },
      TEMPLATE.id,
    )

    expect(result.mode).toBe("error")
    if (result.mode !== "error") throw new Error("unreachable")
    expect(result.message).toContain("ECONNREFUSED")
  })
})

describe("applyPipelineTemplateCore — template not found", () => {
  it("returns mode='error' when template is undefined", async () => {
    const result = await applyPipelineTemplateCore(
      { vacancyId: "backend-uuid-1", template: undefined, fetchImpl: vi.fn() as unknown as typeof fetch },
      "nonexistent-tmpl-id",
    )
    expect(result.mode).toBe("error")
    if (result.mode !== "error") throw new Error("unreachable")
    expect(result.message).toBe("Template não encontrado")
  })
})
