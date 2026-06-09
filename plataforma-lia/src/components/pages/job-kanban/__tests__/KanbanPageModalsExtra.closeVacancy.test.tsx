import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, act, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import ptBRMessages from "../../../../../messages/pt-BR.json"

// `next/dynamic` in jsdom: resolves loader and renders the resolved module.
vi.mock("next/dynamic", () => ({
  default: (loader: () => Promise<{ default?: React.ComponentType<Record<string, unknown>> }>, options?: { loading?: () => React.ReactNode }) => {
    function DynamicMock(props: Record<string, unknown>) {
      const [Comp, setComp] = React.useState<React.ComponentType<Record<string, unknown>> | null>(null)
      React.useEffect(() => {
        let mounted = true
        Promise.resolve(loader()).then((mod) => {
          if (!mounted) return
          const Resolved = (mod && (mod.default ?? (mod as unknown as React.ComponentType<Record<string, unknown>>))) || null
          setComp(() => Resolved)
        })
        return () => { mounted = false }
      }, [])
      if (!Comp) return options?.loading ? <>{options.loading()}</> : null
      return <Comp {...props} />
    }
    DynamicMock.displayName = "NextDynamicMock"
    return DynamicMock
  },
}))

// Mock close-vacancy-modal — exposes onConfirm directly via test button
vi.mock("@/components/modals/close-vacancy-modal", () => ({
  CloseVacancyModal: ({ onConfirm, isOpen }: {
    onConfirm: (data: Record<string, unknown>) => Promise<void>
    isOpen: boolean
  }) => isOpen
    ? (
      <button
        data-testid="confirm-btn"
        onClick={() => onConfirm({
          hired_candidate_id: "cand-1",
          close_reason: "filled",
          hired_notification: { channel: "email", message: "Parabéns!" },
          other_notifications: {
            candidate_ids: [],
            channel: "email",
            message: "Obrigado",
            candidate_emails: {},
            candidate_phones: {},
          },
        })}
      >
        Confirm
      </button>
    )
    : null,
}))

// Stub out all other modals used by KanbanPageModalsExtra
vi.mock("@/components/modals/general-score-modal", () => ({ GeneralScoreModal: () => null }))
vi.mock("@/components/modals/technical-test-modal", () => ({ TechnicalTestModal: () => null }))
vi.mock("@/components/modals/english-test-modal", () => ({ EnglishTestModal: () => null }))
vi.mock("@/components/modals/candidate-compare-modal", () => ({ CandidateCompareModal: () => null }))
vi.mock("@/components/kanban", () => ({ UniversalTransitionModal: () => null }))
vi.mock("@/components/modals/data-request-modal", () => ({ DataRequestModal: () => null }))
vi.mock("@/components/modals/job-status-modal", () => ({ JobStatusModal: () => null }))
vi.mock("@/components/modals/share-search-modal", () => ({ ShareSearchModal: () => null }))
vi.mock("@/components/modals/bulk-action-modal", () => ({ BulkActionModal: () => null }))
vi.mock("@/components/offer-review-modal/OfferReviewModal", () => ({ OfferReviewModal: () => null }))
vi.mock("@/components/ui/loading", () => ({ LoadingModal: () => null }))
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "company-123" }),
}))
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

import { toast } from "sonner"
import { KanbanPageModalsExtra } from "../KanbanPageModalsExtra"
import type { KanbanPageCoreState } from "../hooks/useKanbanPageCore"

function makeState(overrides: Partial<KanbanPageCoreState> = {}): KanbanPageCoreState {
  return {
    showCloseVacancyModal: true,
    setShowCloseVacancyModal: vi.fn(),
    setJobEditForm: vi.fn(),
    currentJob: { id: "job-uuid-1", backendId: "job-uuid-1", jobId: null, title: "Dev", department: "Eng" },
    candidatesData: { hired: [{ id: "cand-1", name: "Fulano", email: "f@e.com" }] },
    showGeneralScoreModal: false, setShowGeneralScoreModal: vi.fn(),
    showTechnicalTestModal: false, setShowTechnicalTestModal: vi.fn(),
    showEnglishTestModal: false, setShowEnglishTestModal: vi.fn(),
    scoreModalCandidate: null,
    showCompareModal: false, setShowCompareModal: vi.fn(),
    compareCandidates: [], setCompareCandidates: vi.fn(),
    _jobIdForSL: null, _companyIdForSL: null,
    selectedForCompare: new Set<string>(), setSelectedForCompare: vi.fn(),
    allTableCandidates: [],
    universalModalState: { isOpen: false, candidates: [], fromStage: "", toStage: "", toStageDisplayName: "", actionBehavior: "move", subStatusOptions: [] },
    closeTransition: vi.fn(), setTransitionInitialPrompt: vi.fn(),
    setTransitionAllowStageSelection: vi.fn(), setTransitionInterviewAlert: vi.fn(),
    handleUniversalTransitionConfirm: vi.fn(), handleOpenSpecializedModal: vi.fn(),
    dynamicStages: [],
    transitionInitialPrompt: undefined, transitionAllowStageSelection: false, transitionInterviewAlert: null,
    showDataRequestModal: false, setShowDataRequestModal: vi.fn(),
    dataRequestModalCandidate: null, setDataRequestModalCandidate: vi.fn(),
    handleDataRequestSubmit: vi.fn(),
    showBulkActionModal: false, setShowBulkActionModal: vi.fn(),
    bulkActionType: "move", handleBulkActionExecute: vi.fn(),
    selectedCandidates: new Set<string>(), user: null,
    showJobStatusModal: false, setShowJobStatusModal: vi.fn(),
    jobStatusModalMode: "pause",
    showPublishSuccess: false, setShowPublishSuccess: vi.fn(), publicLink: null,
    showShareGestorModal: false, setShowShareGestorModal: vi.fn(),
    allCandidateIds: [], setSelectedCandidates: vi.fn(),
    ...overrides,
  } as unknown as KanbanPageCoreState
}

async function renderAndWait(state: KanbanPageCoreState) {
  const result = render(
    <NextIntlClientProvider locale="pt-BR" messages={ptBRMessages}>
      <KanbanPageModalsExtra {...state} />
    </NextIntlClientProvider>
  )
  // Wait for dynamic imports to resolve
  await waitFor(() => screen.getByTestId("confirm-btn"))
  return result
}

describe("KanbanPageModalsExtra — CloseVacancyModal onConfirm wiring", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("test_close_vacancy_success — calls real endpoint, updates state and closes modal", async () => {
    const setJobEditForm = vi.fn()
    const setShowCloseVacancyModal = vi.fn()
    const state = makeState({ setJobEditForm, setShowCloseVacancyModal })

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "job-uuid-1", status: "closed" }),
    } as Response)

    await renderAndWait(state)
    const btn = screen.getByTestId("confirm-btn")
    await act(async () => { btn.click() })

    expect(global.fetch).toHaveBeenCalledWith(
      "/api/backend-proxy/job-vacancies/job-uuid-1/close",
      expect.objectContaining({ method: "POST" })
    )
    expect(setJobEditForm).toHaveBeenCalled()
    const updaterFn = (setJobEditForm.mock.calls[0] as Array<unknown>)[0] as (prev: Record<string, unknown>) => Record<string, unknown>
    expect(updaterFn({ foo: "bar" })).toEqual({ foo: "bar", status: "Encerrada" })
    expect(toast.success).toHaveBeenCalled()
    expect(setShowCloseVacancyModal).toHaveBeenCalledWith(false)
  })

  it("test_close_vacancy_http_error — shows error toast, does NOT close modal", async () => {
    const setShowCloseVacancyModal = vi.fn()
    const setJobEditForm = vi.fn()
    const state = makeState({ setShowCloseVacancyModal, setJobEditForm })

    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Validation error" }),
    } as Response)

    await renderAndWait(state)
    const btn = screen.getByTestId("confirm-btn")
    await act(async () => { btn.click() })

    expect(toast.error).toHaveBeenCalledWith(
      "Erro ao fechar vaga",
      expect.objectContaining({ description: "Validation error" })
    )
    expect(setShowCloseVacancyModal).not.toHaveBeenCalled()
    expect(setJobEditForm).not.toHaveBeenCalled()
  })

  it("test_close_vacancy_network_error — shows connection error toast", async () => {
    const setShowCloseVacancyModal = vi.fn()
    const state = makeState({ setShowCloseVacancyModal })

    global.fetch = vi.fn().mockRejectedValueOnce(new Error("Network failure"))

    await renderAndWait(state)
    const btn = screen.getByTestId("confirm-btn")
    await act(async () => { btn.click() })

    expect(toast.error).toHaveBeenCalledWith(
      "Erro de conexão",
      expect.objectContaining({ description: "Não foi possível conectar ao servidor." })
    )
    expect(setShowCloseVacancyModal).not.toHaveBeenCalled()
  })
})
