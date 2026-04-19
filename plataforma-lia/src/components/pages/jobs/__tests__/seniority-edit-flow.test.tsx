/**
 * Integration test — Seniority edit flow (Task #560)
 *
 * Validates the full pipeline after the legacy `level` field was removed:
 *   form (`seniority`) → payload (`seniority_level`) → backend mapper
 *   (`seniority_level` → `seniority`) → listing/filter/preview UI.
 *
 * Camadas cobertas:
 *   1. useEditJob.handleSave: form.seniority é serializada como
 *      `seniority_level` no payload enviado ao backend.
 *   2. convertBackendJobToFrontend: `seniority_level` é remapeado para
 *      `seniority` ao voltar do backend.
 *   3. useJobsFilters: filtro avançado por `seniority_levels` filtra a
 *      lista corretamente, lendo o campo canônico `seniority`.
 *   4. JobPreviewHeader: chip de senioridade renderiza o valor canônico
 *      sem regressão visual (sanity check).
 */

import React from "react"
import { render, screen, act } from "@testing-library/react"
import { renderHook, act as actHook } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach } from "vitest"

// ─── Mocks (must come before importing the SUT modules) ───────────────────

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}))

// Stable references — useEditJob's hydration effect depends on
// `companyStages` and `sla` identity; new refs each render would
// cause an infinite re-render loop.
const STABLE_INTERVIEW_STAGES: never[] = []
vi.mock("@/hooks/recruitment/use-recruitment-stages", () => ({
  useRecruitmentStages: () => ({
    interviewStages: STABLE_INTERVIEW_STAGES,
    sla: undefined,
    isLoading: false,
  }),
}))

vi.mock("@/hooks/company/use-company-lia-instructions", () => ({
  useCompanyLiaInstructions: () => ({
    buildContextPrompt: () => "",
    isFieldActive: () => true,
    getActiveFields: () => [],
  }),
}))

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    listDepartments: vi.fn().mockResolvedValue([]),
    listBenefits: vi.fn().mockResolvedValue([]),
  },
}))

vi.mock("@/hooks/jobs/useJobFiltersPersistence", () => ({
  useJobFiltersPersistence: () => ({
    filtersState: {
      selectedStatusFilter: "todas",
      selectedDaysFilter: "todas",
      advancedFilters: {
        job_titles: [], departments: [], locations: [], work_models: [],
        job_types: [], seniority_levels: [], salary_ranges: [], status: [],
        stages: [], priorities: [], managers: [], benefits: [], requirements: [],
        industries: [], budget_ranges: [], urgency_levels: [],
        contract_duration: [], team_size: [],
      },
      booleanSearch: "",
      searchTerm: "",
    },
    updateFilter: vi.fn(),
    savedSearches: [],
    saveCurrentSearch: vi.fn(),
    applySavedSearch: vi.fn(),
    deleteSavedSearch: vi.fn(),
    renameSavedSearch: vi.fn(),
    getActiveFiltersCount: () => 0,
    hasActiveFilters: false,
    isLoaded: true,
  }),
}))

// fetch is exercised by useEditJob.handleSave (screening-config sync) and
// fetchPipelineTemplates. We stub it to a noop ok-response.
const fetchMock = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ items: [] }),
  } as unknown as Response),
)
vi.stubGlobal("fetch", fetchMock)

// ─── Imports (after mocks) ────────────────────────────────────────────────

import { useEditJob } from "@/components/modals/edit-job/useEditJob"
import { convertBackendJobToFrontend } from "@/components/pages/jobs/utils/jobsPageUtils"
import { useJobsFilters } from "@/components/pages/jobs/hooks/useJobsFilters"
import { JobPreviewHeader } from "@/components/pages/jobs/job-preview/sections/JobPreviewHeader"
import type { Job as PageJob } from "@/components/jobs/jobsPageTypes"
import type { JobVacancy } from "@/services/lia-api"

// ─── Helpers ──────────────────────────────────────────────────────────────

function makeJob(overrides: Partial<PageJob> = {}): PageJob {
  return {
    id: 1,
    jobId: "WDT-ABC12345",
    backendId: "abc12345-0000-0000-0000-000000000001",
    title: "Engenheiro de Software",
    department: "Tecnologia",
    location: "São Paulo, SP",
    workModel: "híbrido",
    type: "CLT",
    seniority: "Pleno",
    salary: "R$ 10.000 - R$ 15.000",
    benefits: [],
    status: "Ativa",
    stage: "Triagem",
    openDate: "2026-01-01",
    description: "",
    requirements: [],
    manager: "Manager",
    managerEmail: "manager@x.com",
    recruiter: "Recruiter",
    recruiterEmail: "recruiter@x.com",
    priority: "média",
    funnel: { total: 0, screening: 0, interview: 0, final: 0, hired: 0 },
    publishedLinkedIn: false,
    publishedWebsite: false,
    isConfidential: false,
    visibility: "public",
    nps: 0,
    nextActions: [],
    urgencyLevel: 3,
    approvalStatus: "pendente",
    tags: [],
    technicalRequirements: [],
    languages: [],
    behavioralCompetencies: [],
    screeningQuestions: [],
    interviewStages: [],
    hiringProcess: [],
    isAffirmative: false,
    ...overrides,
  } as unknown as PageJob
}

// ─── Tests ────────────────────────────────────────────────────────────────

describe("Seniority edit flow — end-to-end (form → payload → mapper → UI)", () => {
  beforeEach(() => {
    fetchMock.mockClear()
  })

  it("useEditJob.handleSave envia o novo valor como `seniority_level`", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const job = makeJob({ seniority: "Pleno" })

    const { result, rerender } = renderHook(
      ({ open }: { open: boolean }) =>
        useEditJob({ isOpen: open, job, onSave, onClose }),
      { initialProps: { open: false } },
    )

    // Open the modal so the hook hydrates `formData` from `job`.
    rerender({ open: true })

    // Recruiter changes seniority in the modal Select.
    actHook(() => {
      result.current.updateField("seniority", "Sênior")
    })

    expect(result.current.formData.seniority).toBe("Sênior")

    await actHook(async () => {
      await result.current.handleSave()
    })

    expect(onSave).toHaveBeenCalledTimes(1)
    const [savedJobId, payload] = onSave.mock.calls[0] as [
      string,
      Partial<JobVacancy>,
    ]
    expect(savedJobId).toBe(job.backendId)
    // The legacy `level` field was removed: payload must use `seniority_level`.
    expect(payload.seniority_level).toBe("Sênior")
    expect((payload as Record<string, unknown>).level).toBeUndefined()
    expect((payload as Record<string, unknown>).seniority).toBeUndefined()
    expect(onClose).toHaveBeenCalled()
  })

  it("convertBackendJobToFrontend remapeia `seniority_level` → `seniority`", () => {
    const backend = {
      id: "abc12345-0000-0000-0000-000000000001",
      title: "Engenheiro de Software",
      department: "Tecnologia",
      location: "São Paulo, SP",
      work_model: "híbrido",
      employment_type: "CLT",
      seniority_level: "Sênior",
      status: "Ativa",
      stage: "Triagem",
      created_at: "2026-01-01T00:00:00Z",
      open_date: "2026-01-01T00:00:00Z",
      description: "",
      requirements: [],
      benefits: [],
      interview_stages: [],
      hiring_process: [],
      technical_requirements: [],
      languages: [],
      behavioral_competencies: [],
      screening_questions: [],
    } as unknown as JobVacancy

    const mapped = convertBackendJobToFrontend(backend, 0)
    expect(mapped.seniority).toBe("Sênior")
    // Legacy field must not leak through.
    expect((mapped as unknown as Record<string, unknown>).level).toBeUndefined()
  })

  it("useJobsFilters filtra a listagem pelo filtro avançado de senioridade", () => {
    const backendJobs = [
      makeJob({ id: 1, jobId: "WDT-1", seniority: "Sênior" }),
      makeJob({ id: 2, jobId: "WDT-2", seniority: "Pleno" }),
      makeJob({ id: 3, jobId: "WDT-3", seniority: "Júnior" }),
    ]

    const { result } = renderHook(() => useJobsFilters({ backendJobs }))

    // Sanity: nothing is filtered out yet.
    expect(result.current.state.filteredJobs).toHaveLength(3)

    // Apply the advanced filter for "Sênior" + "Pleno".
    actHook(() => {
      result.current.actions.setAdvancedFilters((prev) => ({
        ...prev,
        seniority_levels: ["Sênior", "Pleno"],
      }))
    })

    const ids = result.current.state.filteredJobs.map((j) => j.jobId).sort()
    expect(ids).toEqual(["WDT-1", "WDT-2"])
  })

  it("JobPreviewHeader renderiza o chip de senioridade sem regressão", () => {
    const job = makeJob({ seniority: "Sênior" })

    render(
      <JobPreviewHeader
        previewJob={job}
        onClose={() => {}}
        onJobClick={() => {}}
      />,
    )

    expect(screen.getByTestId("job-preview-header")).toBeInTheDocument()
    expect(screen.getByText("Sênior")).toBeInTheDocument()
  })

  it("fluxo completo: novo valor salvo no modal aparece no chip do preview e na listagem filtrada", async () => {
    // 1. Recruiter saves "Sênior" via the edit modal.
    const onSave = vi.fn().mockResolvedValue(undefined)
    const onClose = vi.fn()
    const initialJob = makeJob({ seniority: "Pleno" })

    const { result: editResult, rerender } = renderHook(
      ({ open }: { open: boolean }) =>
        useEditJob({ isOpen: open, job: initialJob, onSave, onClose }),
      { initialProps: { open: false } },
    )
    rerender({ open: true })
    actHook(() => editResult.current.updateField("seniority", "Sênior"))
    await actHook(async () => {
      await editResult.current.handleSave()
    })

    const [, payload] = onSave.mock.calls[0] as [string, Partial<JobVacancy>]

    // 2. Backend echoes the payload back (simulating a refetch).
    const backendEcho = {
      id: initialJob.backendId,
      title: initialJob.title,
      department: initialJob.department,
      location: initialJob.location,
      work_model: payload.work_model,
      employment_type: payload.employment_type,
      seniority_level: payload.seniority_level,
      status: "Ativa",
      stage: "Triagem",
      created_at: "2026-01-01T00:00:00Z",
      open_date: "2026-01-01T00:00:00Z",
      description: "",
      requirements: [],
      benefits: [],
      interview_stages: [],
    } as unknown as JobVacancy

    const mappedJob = convertBackendJobToFrontend(backendEcho, 0)
    expect(mappedJob.seniority).toBe("Sênior")

    // 3. Listing/filter sees the new value.
    const { result: filterResult } = renderHook(() =>
      useJobsFilters({ backendJobs: [mappedJob] }),
    )
    actHook(() => {
      filterResult.current.actions.setAdvancedFilters((prev) => ({
        ...prev,
        seniority_levels: ["Sênior"],
      }))
    })
    expect(filterResult.current.state.filteredJobs).toHaveLength(1)

    // 4. Preview header chip shows the new value.
    render(
      <JobPreviewHeader
        previewJob={mappedJob}
        onClose={() => {}}
        onJobClick={() => {}}
      />,
    )
    expect(screen.getByText("Sênior")).toBeInTheDocument()
  })
})
