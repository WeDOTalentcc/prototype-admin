/**
 * Tests — useJobsData timeout path (jobs list page)
 *
 * Camada 2 (Component/Hook — Vitest + @testing-library/react)
 *
 * Covers Task #263 acceptance criteria:
 * - When listJobVacancies takes 15 s and the AbortController fires, the jobs
 *   list page must not spin forever — isLoadingJobs must become false and
 *   jobsError must be populated so the UI can render an error/empty state.
 * - The JobsListContent component renders an error state (not a spinner)
 *   when it receives isLoadingJobs=false and a non-null jobsError.
 */
import React from "react"
import { renderHook, render, screen, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// ── Global fetch stub ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal("fetch", mockFetch)

// ── Service mock ─────────────────────────────────────────────────────────────

const mockListJobVacancies = vi.fn()

vi.mock("@/services/lia-api", async () => {
  const real = await vi.importActual<typeof import("@/services/lia-api/base")>(
    "@/services/lia-api/base",
  )
  return {
    HttpError: real.HttpError,
    liaApi: {
      listJobVacancies: (...args: unknown[]) => mockListJobVacancies(...args),
      getJobVacanciesOverview: vi.fn().mockRejectedValue(new Error("overview not needed")),
    },
  }
})

vi.mock("@/lib/pricing", () => ({
  formatBRL: (n: number) => `R$ ${n}`,
}))

// ── next-intl mock (returns translation key as-is) ────────────────────────────

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}))

// ── Heavy child component mocks ───────────────────────────────────────────────

vi.mock("@/components/pages/jobs/TableFiltersPanel", () => ({
  TableFiltersPanel: () => null,
}))
vi.mock("@/components/pages/jobs/JobPreviewPanel", () => ({
  JobPreviewPanel: () => null,
}))
vi.mock("@/components/pages/jobs/JobsCompactTableView", () => ({
  JobsCompactTableView: () => null,
}))
vi.mock("@/components/pages/jobs/ColumnConfigPanel", () => ({
  ColumnConfigPanel: () => null,
}))
vi.mock("@/components/ui/bulk-actions-bar", () => ({
  BulkActionsBar: () => null,
}))
vi.mock("@/components/ui/empty-state", () => ({
  EmptyState: () => <div data-testid="empty-state" />,
}))
vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))

// ── Import after mocks ────────────────────────────────────────────────────────

import { useJobsData } from "../hooks/useJobsData"
import { JobsListContent } from "../../JobsListContent"

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeAbortError(): Error {
  const e = new Error("The operation was aborted due to timeout")
  e.name = "AbortError"
  return e
}

/** Simulates listJobVacancies hanging for 15 s then aborting — exactly
 *  what the AbortController in jobs-api.ts produces on timeout. */
function hangingAbortAfter15s(): Promise<never> {
  return new Promise((_, reject) =>
    setTimeout(() => reject(makeAbortError()), 15_000),
  )
}

async function drainAllTimers(rounds = 8): Promise<void> {
  for (let i = 0; i < rounds; i++) {
    await act(async () => {
      await vi.runAllTimersAsync()
    })
  }
}

function makeMinimalProps(
  overrides: Record<string, unknown> = {},
// eslint-disable-next-line @typescript-eslint/no-explicit-any
): any {
  const noop = vi.fn()
  const noopAsync = vi.fn().mockResolvedValue(undefined)
  return {
    showExpandedLIA: false, setShowExpandedLIA: noop,
    showInlineChat: false, chatMode: null, isChatFullscreen: false,
    selectedJobsForBatch: new Set(), filteredJobs: [],
    isLoadingJobs: false, isTableCollapsed: false,
    searchTerm: "", selectedDaysFilter: "all",
    showTableFiltersPanel: false, setShowTableFiltersPanel: noop,
    showColumnConfig: false, setShowColumnConfig: noop,
    handleToggleColumnConfig: noop, getActiveJobFiltersCount: () => 0,
    selectAllJobs: noop, deselectAllJobs: noop,
    handleJobPublish: noop, handleJobInsights: noop,
    handleJobDuplicate: noop, handleJobToggleStatus: noop,
    handleJobAssignRecruiter: noop, getSelectedJobsHaveActiveStatus: () => false,
    toggleTableExpansion: noop, setChatMode: noop,
    setSearchTerm: noop, jobFilters: {}, toggleJobFilter: noop,
    clearAllJobFilters: noop, hasActiveFilters: () => false,
    savedSearches: [], saveSearchAsTemplate: noop,
    handleApplySavedSearch: noop, handleRenameSavedSearch: noop,
    handleDeleteSavedSearch: noop,
    inlineChatInitialMessage: undefined,
    liaInlineMessages: [], liaInlineLoading: false,
    liaWidth: 320, isResizingLIA: false, userCollapsedLIA: false,
    liaPromptValue: "", setLiaPromptValue: noop,
    closeChat: noop, openGeneralChat: noop,
    openJobCreationChat: noop, returnToGeneralChat: noop,
    returnToLateralPrompt: noop, sendLiaInlineMessage: noopAsync,
    setUserCollapsedLIA: noop, setIsChatFullscreen: noop,
    setIsResizingLIA: noop, setLiaWidth: noop,
    setLiaInlineMessages: noop,
    liaInlineMessagesEndRef: { current: null },
    onAddRecentItem: undefined,
    showJobPreview: false, previewJob: null,
    activePreviewTab: "pipeline", setActivePreviewTab: noop,
    previewWidth: 320, setPreviewWidth: noop,
    setIsResizingPreview: noop, setShowJobPreview: noop,
    setPreviewJob: noop, handleJobClick: noop,
    screeningConfig: undefined, isLoadingScreeningConfig: false,
    jobMetrics: null, isLoadingJobMetrics: false,
    columnConfig: [], visibleColumnIds: [], savedColumnViews: [],
    toggleColumn: noop, applyColumnView: noop, deleteColumnView: noop,
    saveColumnView: noop, resetColumnsToDefault: noop,
    statusOrder: [], groupedJobs: {},
    jobsColumnOrder: [], hookToTableColumnMap: {},
    jobsColumnWidths: {},
    pinnedJobs: new Set(), urgentJobs: new Set(), favoriteJobs: new Set(),
    draggedJobColumnId: null, dragOverJobColumnId: null,
    jobsSortColumn: null, jobsSortDirection: "asc",
    toggleJobSelection: noop, handleJobPreview: noop,
    handleJobsSort: noop, handleJobsColumnDragStart: noop,
    handleJobsColumnDragOver: noop, handleJobsColumnDragLeave: noop,
    handleJobsColumnDrop: noop, handleJobsColumnDragEnd: noop,
    startJobsColumnResize: noop,
    toggleUrgentJob: noop, togglePinJob: noop, toggleFavoriteJob: noop,
    jobsError: null, loadBackendJobs: noopAsync,
    ...overrides,
  }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useJobsData — listJobVacancies 15 s timeout path", () => {
  beforeEach(() => {
    vi.useFakeTimers()
    mockFetch.mockResolvedValue({ ok: true })
    mockListJobVacancies.mockImplementation(hangingAbortAfter15s)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.clearAllMocks()
  })

  it("keeps spinner until the 15 s timeout fires, then clears it and sets jobsError", async () => {
    const { result } = renderHook(() => useJobsData())

    // Initial state — loading, no error
    expect(result.current.state.isLoadingJobs).toBe(true)
    expect(result.current.state.jobsError).toBeNull()

    // Just before the first 15 s timeout — still loading
    await act(async () => {
      vi.advanceTimersByTime(14_999)
    })
    expect(result.current.state.isLoadingJobs).toBe(true)
    expect(result.current.state.jobsError).toBeNull()

    // Exhaust timeout + all retry back-off delays
    await drainAllTimers()

    // Spinner must clear and error must be set
    expect(result.current.state.isLoadingJobs).toBe(false)
    expect(result.current.state.jobsError).toBeTruthy()
    expect(typeof result.current.state.jobsError).toBe("string")
  }, 60_000)
})

describe("JobsListContent — error state after timeout", () => {
  it("renders error message and hides spinner when isLoadingJobs=false and jobsError is set", () => {
    const ERROR_MSG = "The operation was aborted due to timeout"
    render(
      <JobsListContent
        {...makeMinimalProps({
          isLoadingJobs: false,
          jobsError: ERROR_MSG,
        })}
      />,
    )

    // Error message must be visible
    expect(screen.getByText(ERROR_MSG)).toBeInTheDocument()

    // Loading spinner must NOT be present
    expect(screen.queryByText("loadingJobs")).toBeNull()
  })

  it("renders loading spinner when isLoadingJobs=true regardless of jobsError", () => {
    render(
      <JobsListContent
        {...makeMinimalProps({
          isLoadingJobs: true,
          jobsError: null,
        })}
      />,
    )

    // Loading indicator should be present
    expect(screen.getByText("loadingJobs")).toBeInTheDocument()

    // No error banner
    expect(screen.queryByText(/aborted/i)).toBeNull()
  })
})
