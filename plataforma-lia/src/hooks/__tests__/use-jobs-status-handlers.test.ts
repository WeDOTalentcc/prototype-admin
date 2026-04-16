/**
 * Tests — useJobsStatusHandlers.handleJobCreated
 *
 * Camada 2 (Unitário FE — Vitest + @testing-library/react)
 *
 * Covers Task #252 acceptance criteria:
 * - handleJobCreated calls onNavigateToCreatedJob even when onRefreshJobs rejects
 * - handleJobCreated does not throw when the background list refresh fails
 * - handleJobCreated calls onNavigateToCreatedJob BEFORE triggering the refresh
 * - createJobVacancy succeeds + listJobVacancies fails → navigation still happens
 */
import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useJobsStatusHandlers } from "@/components/pages/jobs/useJobsStatusHandlers"
import type { JobsModalsSectionProps } from "@/components/pages/jobs/JobsModalsSectionTypes"

// ── Mocks ───────────────────────────────────────────────────────────────────

const mockSetJobCreationMode = vi.fn()
const mockSetPendingCommunicationAction = vi.fn()

vi.mock("@/stores/job-ui-store", () => ({
  useJobUIStore: {
    getState: () => ({
      setJobCreationMode: mockSetJobCreationMode,
      setPendingCommunicationAction: mockSetPendingCommunicationAction,
    }),
  },
}))

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

const mockCreateJobVacancy = vi.fn()
const mockListJobVacancies = vi.fn()

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    createJobVacancy: (...args: unknown[]) => mockCreateJobVacancy(...args),
    listJobVacancies: (...args: unknown[]) => mockListJobVacancies(...args),
    updateJobVacancyStatus: vi.fn(),
    updateJobVacancy: vi.fn(),
    updateScreeningStatus: vi.fn(),
    sendRecruiterActionNotification: vi.fn(),
    transferCommunications: vi.fn(),
  },
}))

// ── Helpers ─────────────────────────────────────────────────────────────────

function makeProps(overrides: Partial<JobsModalsSectionProps> = {}): JobsModalsSectionProps {
  return {
    allJobs: [],
    selectedJobsForBatch: new Set(),
    showReport: false,
    reportJob: null,
    onCloseReport: vi.fn(),
    showCompareModal: false,
    onCloseCompareModal: vi.fn(),
    showPublishModal: false,
    onClosePublishModal: vi.fn(),
    showUnpublishModal: false,
    onCloseUnpublishModal: vi.fn(),
    showInsightsModal: false,
    onCloseInsightsModal: vi.fn(),
    showDuplicateModal: false,
    onCloseDuplicateModal: vi.fn(),
    showStatusModal: false,
    onCloseStatusModal: vi.fn(),
    statusModalMode: "pause",
    showAssignRecruiterModal: false,
    onCloseAssignRecruiterModal: vi.fn(),
    showCreateJobModal: false,
    onCloseCreateJobModal: vi.fn(),
    showEditJobModal: false,
    onCloseEditJobModal: vi.fn(),
    editingJob: null,
    showScreeningChannelsModal: false,
    onCloseScreeningChannelsModal: vi.fn(),
    showScreeningSettingsModal: false,
    onCloseScreeningSettingsModal: vi.fn(),
    showScreeningSchedulingModal: false,
    onCloseScreeningSchedulingModal: vi.fn(),
    screeningConfig: {} as never,
    updateScreeningConfig: vi.fn(),
    showReactivateScreeningDialog: false,
    reactivateScreeningJobs: [],
    reactivateEndDate: "",
    showWSITutorialModal: false,
    onCloseWSITutorialModal: vi.fn(),
    companyRecruiters: [],
    activeFilter: "all",
    onDeselectAll: vi.fn(),
    onRefreshJobs: vi.fn().mockResolvedValue(undefined),
    onSetBackendJobs: vi.fn(),
    onSetSelectedJob: vi.fn(),
    onSetPreviewJob: vi.fn(),
    onSetEditingJob: vi.fn(),
    onSetActiveFilter: vi.fn(),
    onOpenJobCreationChat: vi.fn(),
    onSetPendingNavigateJobId: vi.fn(),
    onNavigateToCreatedJob: vi.fn(),
    onSetReactivateScreeningDialog: vi.fn(),
    onSetReactivateScreeningJobs: vi.fn(),
    onSetReactivateEndDate: vi.fn(),
    ...overrides,
  }
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("useJobsStatusHandlers — handleJobCreated", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("calls onNavigateToCreatedJob with the new job id and title", async () => {
    const onNavigateToCreatedJob = vi.fn()
    const props = makeProps({ onNavigateToCreatedJob })

    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await act(async () => {
      result.current.handleJobCreated("job-123", "Engenheiro de Software")
    })

    expect(onNavigateToCreatedJob).toHaveBeenCalledOnce()
    expect(onNavigateToCreatedJob).toHaveBeenCalledWith("job-123", "Engenheiro de Software")
  })

  it("calls onNavigateToCreatedJob even when onRefreshJobs rejects (list 500)", async () => {
    const onNavigateToCreatedJob = vi.fn()
    const onRefreshJobs = vi.fn().mockRejectedValue(new Error("500 Internal Server Error"))
    const props = makeProps({ onNavigateToCreatedJob, onRefreshJobs })

    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await act(async () => {
      result.current.handleJobCreated("job-456", "Designer UX")
    })

    expect(onNavigateToCreatedJob).toHaveBeenCalledOnce()
    expect(onNavigateToCreatedJob).toHaveBeenCalledWith("job-456", "Designer UX")
  })

  it("does not throw when onRefreshJobs rejects", async () => {
    const onRefreshJobs = vi.fn().mockRejectedValue(new Error("Network error"))
    const props = makeProps({ onRefreshJobs })

    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await expect(
      act(async () => {
        result.current.handleJobCreated("job-789", "Analista de Dados")
      })
    ).resolves.not.toThrow()
  })

  it("calls onNavigateToCreatedJob before the refresh can settle", async () => {
    const callOrder: string[] = []

    const onNavigateToCreatedJob = vi.fn(() => {
      callOrder.push("navigate")
    })

    let resolveRefresh!: () => void
    const onRefreshJobs = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveRefresh = resolve
          callOrder.push("refresh-started")
        })
    )

    const props = makeProps({ onNavigateToCreatedJob, onRefreshJobs })
    const { result } = renderHook(() => useJobsStatusHandlers(props))

    act(() => {
      result.current.handleJobCreated("job-abc", "Product Manager")
    })

    // navigate must have been called synchronously before any await
    expect(callOrder[0]).toBe("navigate")

    // now settle the refresh
    await act(async () => {
      resolveRefresh()
    })
  })

  it("calls onCloseCreateJobModal before navigating", async () => {
    const callOrder: string[] = []
    const onCloseCreateJobModal = vi.fn(() => callOrder.push("close-modal"))
    const onNavigateToCreatedJob = vi.fn(() => callOrder.push("navigate"))
    const props = makeProps({ onCloseCreateJobModal, onNavigateToCreatedJob })

    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await act(async () => {
      result.current.handleJobCreated("job-xyz", "Tech Lead")
    })

    expect(callOrder).toEqual(["close-modal", "navigate"])
  })

  it("sets pendingNavigateJobId as fallback via onSetPendingNavigateJobId", async () => {
    const onSetPendingNavigateJobId = vi.fn()
    const props = makeProps({ onSetPendingNavigateJobId })

    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await act(async () => {
      result.current.handleJobCreated("job-fallback", "QA Engineer")
    })

    expect(onSetPendingNavigateJobId).toHaveBeenCalledWith("job-fallback")
  })
})

// ── Full creation flow: liaApi.createJobVacancy OK + liaApi.listJobVacancies 500 ──

describe("handleJobCreated — createJobVacancy succeeds, listJobVacancies returns 500", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockCreateJobVacancy.mockResolvedValue({
      id: "new-job-id",
      title: "Desenvolvedor Full-Stack",
      status: "Ativa",
    })
    mockListJobVacancies.mockRejectedValue(new Error("500 Internal Server Error"))
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("navigates to the new job even when the list refresh 500s", async () => {
    const onNavigateToCreatedJob = vi.fn()

    const onRefreshJobs = vi.fn(async () => {
      await mockListJobVacancies()
    })

    const props = makeProps({ onNavigateToCreatedJob, onRefreshJobs })
    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await act(async () => {
      result.current.handleJobCreated("new-job-id", "Desenvolvedor Full-Stack")
    })

    expect(onNavigateToCreatedJob).toHaveBeenCalledOnce()
    expect(onNavigateToCreatedJob).toHaveBeenCalledWith("new-job-id", "Desenvolvedor Full-Stack")
  })

  it("does not throw when create succeeds but list refresh 500s", async () => {
    const onRefreshJobs = vi.fn(async () => {
      await mockListJobVacancies()
    })

    const props = makeProps({ onRefreshJobs })
    const { result } = renderHook(() => useJobsStatusHandlers(props))

    await expect(
      act(async () => {
        result.current.handleJobCreated("new-job-id", "Desenvolvedor Full-Stack")
      })
    ).resolves.not.toThrow()
  })
})
