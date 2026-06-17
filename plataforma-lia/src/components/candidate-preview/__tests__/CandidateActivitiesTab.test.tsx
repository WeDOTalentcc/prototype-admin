/**
 * Tests — CandidateActivitiesTab (F3 — real API wiring, mock elimination)
 *
 * Verifies: renders with real API hook, loading state, empty state, error state.
 * Does NOT use demo-activities or any hardcoded mock data inline.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import { CandidateActivitiesTab } from "../CandidateActivitiesTab"

// ── Mock dependencies ──────────────────────────────────────────────────────
vi.mock("@/lib/design-tokens", () => ({
  textStyles: {
    label: "text-xs font-medium",
    bodySmall: "text-xs text-gray-500",
    description: "text-xs text-gray-400",
  },
  cardStyles: {},
  formatScorePercent: (s: number) => `${s}%`,
}))

vi.mock("@/components/ui/chip", () => ({
  Chip: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}))

vi.mock("@/components/modals/screening-media-modal", () => ({
  ScreeningQuestion: {},
  TranscriptionSegment: {},
}))

vi.mock("@/components/candidate-preview/activities/ActivityFilters", () => ({
  ActivityFilters: ({ totalCount }: { totalCount: number }) => (
    <div data-testid="activity-filters">Total: {totalCount}</div>
  ),
}))

vi.mock("@/components/candidate-preview/activities/ActivityTimeline", () => ({
  ActivityTimeline: ({
    filteredActivities,
    renderActivityCard,
    activityView,
  }: {
    filteredActivities: Array<{ id: string; title?: string; [key: string]: unknown }>
    renderActivityCard: (a: unknown, isTimeline: boolean) => React.ReactNode
    activityView: string
  }) => (
      <div data-testid="activity-timeline">
        {filteredActivities.map((a) => (
          <div key={a.id} data-testid={`activity-${a.id}`}>
            {renderActivityCard(a, activityView === "timeline")}
          </div>
        ))}
      </div>
    ),
}))

const mockActivitiesHook = vi.fn()
vi.mock("@/hooks/candidates/use-candidate-activities", () => ({
  useCandidateActivities: (...args: unknown[]) => mockActivitiesHook(...args),
}))

// ── Helpers ───────────────────────────────────────────────────────────────
const NOOP = () => {}
const defaultProps = {
  candidate: { id: "cand_1", name: "João Silva" },
  onShowLiaModal: NOOP,
  onSetScreeningModalData: NOOP,
  onSetScreeningModalOpen: NOOP,
  onSetDiscModalData: NOOP,
  onSetDiscModalOpen: NOOP,
  onSetBigFiveModalCandidate: NOOP,
  onSetBigFiveModalOpen: NOOP,
  onSetSelectedFile: NOOP,
  onSetPreviewType: NOOP,
  onSetShowPreview: NOOP,
}

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn())
})
afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe("CandidateActivitiesTab", () => {
  it("renders loading spinner while hook is loading", () => {
    mockActivitiesHook.mockReturnValue({
      activities: [],
      isLoading: true,
      error: null,
      total: 0,
      refetch: NOOP,
    })
    render(<CandidateActivitiesTab {...defaultProps} />)
    expect(screen.getByRole("status")).toBeInTheDocument()
    expect(screen.getByText(/Carregando atividades/i)).toBeInTheDocument()
  })

  it("renders error message when hook returns error (fails loud)", () => {
    mockActivitiesHook.mockReturnValue({
      activities: [],
      isLoading: false,
      error: "Activities fetch failed: 500",
      total: 0,
      refetch: NOOP,
    })
    render(<CandidateActivitiesTab {...defaultProps} />)
    expect(screen.getByRole("alert")).toBeInTheDocument()
    expect(screen.getByText(/500/i)).toBeInTheDocument()
  })

  it("renders activity timeline with real API activities (no demo data)", () => {
    mockActivitiesHook.mockReturnValue({
      activities: [
        {
          id: "act_api_1",
          type: "email_sent",
          title: "E-mail enviado",
          summary: "Convite para triagem",
          timestamp: new Date().toISOString(),
          author: "LIA",
        },
      ],
      isLoading: false,
      error: null,
      total: 1,
      refetch: NOOP,
    })
    render(<CandidateActivitiesTab {...defaultProps} />)
    expect(screen.getByTestId("activity-timeline")).toBeInTheDocument()
    expect(screen.getByText("E-mail enviado")).toBeInTheDocument()
  })

  it("shows empty timeline when no activities (not demo data)", () => {
    mockActivitiesHook.mockReturnValue({
      activities: [],
      isLoading: false,
      error: null,
      total: 0,
      refetch: NOOP,
    })
    render(<CandidateActivitiesTab {...defaultProps} />)
    expect(screen.getByTestId("activity-timeline")).toBeInTheDocument()
    // No mock data names should appear
    expect(screen.queryByText(/Maria Oliveira/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Carlos Mendes/)).not.toBeInTheDocument()
  })

  it("calls useCandidateActivities with the candidate prop", () => {
    mockActivitiesHook.mockReturnValue({
      activities: [],
      isLoading: false,
      error: null,
      total: 0,
      refetch: NOOP,
    })
    const candidate = { id: "cand_test_99", name: "Test" }
    render(<CandidateActivitiesTab {...defaultProps} candidate={candidate} />)
    expect(mockActivitiesHook).toHaveBeenCalledWith(
      expect.objectContaining({ id: "cand_test_99" }),
    )
  })
})
