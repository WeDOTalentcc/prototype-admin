/**
 * Tests — Fallback banner on the jobs page (Task #256, follow-up to Task #250)
 *
 * When the backend cannot reach the external Rails job source it returns
 * `source: "local-fallback"` on the `/job-vacancies` response. The jobs page
 * must surface that condition with an amber WifiOff banner so users know some
 * external listings may be missing.
 *
 * Two layers are exercised:
 *
 *  1. `useJobsData` — mocks `liaApi.listJobVacancies` and asserts that the
 *     `source: "local-fallback"` flag is propagated to the
 *     `isExternalSourceFallback` state, while a normal response (no `source`
 *     field) leaves it `false`.
 *
 *  2. `JobsPage` — mocks `useJobsPageCore` so we can drive
 *     `isExternalSourceFallback` directly, then asserts the amber banner
 *     renders when the flag is `true` and is absent when `false`.
 */
import React from "react"
import { render, renderHook, screen, waitFor } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// ── Service mock (shared by both describe blocks) ────────────────────────────

const mockListJobVacancies = vi.fn()
const mockGetOverview = vi.fn()

vi.mock("@/services/lia-api", async () => {
  const real = await vi.importActual<typeof import("@/services/lia-api/base")>(
    "@/services/lia-api/base",
  )
  return {
    HttpError: real.HttpError,
    liaApi: {
      listJobVacancies: (...args: unknown[]) => mockListJobVacancies(...args),
      getJobVacanciesOverview: (...args: unknown[]) => mockGetOverview(...args),
    },
  }
})

vi.mock("@/lib/pricing", () => ({
  formatBRL: (n: number) => `R$ ${n}`,
}))

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// ── Heavy child mocks for JobsPage rendering ─────────────────────────────────

vi.mock("@/components/pages/JobsListContent", () => ({
  JobsListContent: () => <div data-testid="jobs-list-content" />,
}))

vi.mock("@/components/pages/jobs/JobsModalsSection", () => ({
  JobsModalsSection: () => null,
}))

vi.mock("@/components/pages/job-kanban-page", () => ({
  JobKanbanPage: () => <div data-testid="kanban" />,
}))

vi.mock("@/components/ui/page-tab-navigation", () => ({
  PageTabNavigation: () => <div data-testid="tabs" />,
}))

vi.mock("@/components/ui/error-boundary-section", () => ({
  ErrorBoundarySection: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

vi.mock("@/components/ui/loading", () => ({
  LoadingModal: () => null,
}))

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() },
}))

// ── Mock useJobsPageCore for the JobsPage banner tests ───────────────────────

const mockState: Record<string, unknown> = {}
vi.mock("@/components/pages/jobs/hooks/useJobsPageCore", () => ({
  useJobsPageCore: () => mockState,
}))

// ── Imports after mocks ──────────────────────────────────────────────────────

import { useJobsData } from "../hooks/useJobsData"
import { JobsPage } from "@/components/pages/jobs-page"

// ── Helpers ──────────────────────────────────────────────────────────────────

function makePageState(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  const noop = vi.fn()
  return {
    hasMounted: true,
    showKanban: false,
    selectedJob: null,
    activeFilter: "todas",
    allJobs: [],
    filteredJobs: [],
    isLoadingJobs: false,
    jobsError: null,
    navigationFilters: [],
    dashboardStats: null,
    selectedJobsForBatch: new Set(),
    companyRecruiters: [],
    deselectAllJobs: noop,
    setActiveFilter: noop,
    setShowCreateJobModal: noop,
    openJobCreationChat: noop,
    showReport: false,
    reportJob: null,
    handleCloseReport: noop,
    showCompareModal: false,
    setShowCompareModal: noop,
    showPublishModal: false,
    setShowPublishModal: noop,
    showUnpublishModal: false,
    setShowUnpublishModal: noop,
    showInsightsModal: false,
    setShowInsightsModal: noop,
    showDuplicateModal: false,
    setShowDuplicateModal: noop,
    showStatusModal: false,
    setShowStatusModal: noop,
    statusModalMode: null,
    showAssignRecruiterModal: false,
    setShowAssignRecruiterModal: noop,
    showCreateJobModal: false,
    showScreeningChannelsModal: false,
    setShowScreeningChannelsModal: noop,
    showScreeningSettingsModal: false,
    setShowScreeningSettingsModal: noop,
    showScreeningSchedulingModal: false,
    setShowScreeningSchedulingModal: noop,
    screeningConfig: undefined,
    updateScreeningConfig: noop,
    showReactivateScreeningDialog: false,
    setShowReactivateScreeningDialog: noop,
    reactivateScreeningJobs: [],
    setReactivateScreeningJobs: noop,
    reactivateEndDate: null,
    setReactivateEndDate: noop,
    showWSITutorialModal: false,
    setShowWSITutorialModal: noop,
    setBackendJobs: noop,
    setSelectedJob: noop,
    setPreviewJob: noop,
    setEditingJob: noop,
    setPendingNavigateJobId: noop,
    loadBackendJobs: vi.fn().mockResolvedValue(undefined),
    setActivePreviewTab: noop,
    navigateToCreatedJob: noop,
    handleBackToJobs: noop,
    toggleJobFilter: noop,
    activePreviewTab: "pipeline",
    isExternalSourceFallback: false,
    ...overrides,
  }
}

function setMockState(overrides: Record<string, unknown> = {}): void {
  for (const key of Object.keys(mockState)) delete mockState[key]
  Object.assign(mockState, makePageState(overrides))
}

// ── 1. Hook layer: API source flag → isExternalSourceFallback ────────────────

describe("useJobsData — propagates `source: \"local-fallback\"` to isExternalSourceFallback", () => {
  beforeEach(() => {
    mockListJobVacancies.mockReset()
    mockGetOverview.mockReset()
    // Overview call is best-effort; failing is fine and exercises the fallback
    // stats branch without affecting `isExternalSourceFallback`.
    mockGetOverview.mockRejectedValue(new Error("overview not needed"))
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("sets isExternalSourceFallback=true when the API response carries source=local-fallback", async () => {
    mockListJobVacancies.mockResolvedValue({ items: [], source: "local-fallback" })

    const { result } = renderHook(() => useJobsData())

    await waitFor(() => {
      expect(result.current.state.isLoadingJobs).toBe(false)
    })

    expect(result.current.state.isExternalSourceFallback).toBe(true)
    expect(result.current.state.jobsError).toBeNull()
  })

  it("leaves isExternalSourceFallback=false on a normal response without a source flag", async () => {
    mockListJobVacancies.mockResolvedValue({ items: [] })

    const { result } = renderHook(() => useJobsData())

    await waitFor(() => {
      expect(result.current.state.isLoadingJobs).toBe(false)
    })

    expect(result.current.state.isExternalSourceFallback).toBe(false)
    expect(result.current.state.jobsError).toBeNull()
  })
})

// ── 2. Component layer: JobsPage banner visibility ───────────────────────────

describe("JobsPage — external-source fallback banner", () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it("renders the amber WifiOff banner when isExternalSourceFallback is true", () => {
    setMockState({ isExternalSourceFallback: true, isLoadingJobs: false })

    const { container } = render(<JobsPage />)

    // Banner copy (i18n key surfaced by the next-intl mock)
    const banner = screen.getByText("externalSourceUnavailable")
    expect(banner).toBeInTheDocument()

    // The banner must carry the amber palette classes (visual signal)
    const bannerContainer = banner.parentElement as HTMLElement
    expect(bannerContainer.className).toMatch(/amber/)

    // And it must include the WifiOff icon (lucide renders an <svg>)
    expect(bannerContainer.querySelector("svg")).not.toBeNull()

    // Sanity: container actually mounted the page chrome
    expect(container.querySelector('[data-testid="jobs-list-content"]')).not.toBeNull()
  })

  it("does NOT render the banner on a normal response (isExternalSourceFallback=false)", () => {
    setMockState({ isExternalSourceFallback: false, isLoadingJobs: false })

    render(<JobsPage />)

    expect(screen.queryByText("externalSourceUnavailable")).toBeNull()
  })

  it("hides the banner while jobs are still loading, even if the fallback flag is true", () => {
    // Avoids flashing the warning during the initial spinner — the banner
    // renders only when `!isLoadingJobs && isExternalSourceFallback`.
    setMockState({ isExternalSourceFallback: true, isLoadingJobs: true })

    render(<JobsPage />)

    expect(screen.queryByText("externalSourceUnavailable")).toBeNull()
  })
})
