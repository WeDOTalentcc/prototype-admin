/**
 * Tests — JobDetailClient (JobPage) — error state coverage
 *
 * Camada 3 (Component — Vitest + @testing-library/react + jsdom)
 *
 * Covers Task #252 acceptance criteria:
 * - When getJobVacancy fails, the error state (not an infinite spinner) renders
 * - The retry button is present and clicking it re-triggers the fetch
 */
import React from "react"
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// ── Mocks — must be hoisted before the component import ─────────────────────

const mockGetJobVacancy = vi.fn()

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    getJobVacancy: (...args: unknown[]) => mockGetJobVacancy(...args),
  },
}))

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "test-job-id" }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}))

vi.mock("@/lib/pricing", () => ({
  formatBRL: (n: number) => `R$ ${n.toFixed(2)}`,
}))

vi.mock("@/components/pages/job-kanban-page", () => ({
  JobKanbanPage: () => <div data-testid="job-kanban-page">Kanban</div>,
}))

vi.mock("@/components/ui/error-boundary-section", () => ({
  ErrorBoundarySection: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

// ── Import component after mocks ─────────────────────────────────────────────

import JobPage from "@/app/[locale]/(dashboard)/jobs/[id]/JobDetailClient"

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("JobDetailClient — error state", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it("shows error message and retry button when getJobVacancy rejects", async () => {
    mockGetJobVacancy.mockRejectedValue(new Error("500 Internal Server Error"))

    render(<JobPage />)

    await waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull()
    })

    expect(screen.getByRole("alert")).toBeInTheDocument()
    expect(screen.getByText("Erro ao carregar a vaga")).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /tentar novamente/i })
    ).toBeInTheDocument()
  })

  it("does not stay in loading state indefinitely on API failure", async () => {
    mockGetJobVacancy.mockRejectedValue(new Error("Network error"))

    render(<JobPage />)

    await waitFor(
      () => {
        expect(screen.queryByRole("status")).toBeNull()
      },
      { timeout: 3000 }
    )

    expect(screen.getByRole("alert")).toBeInTheDocument()
  })

  it("retry button re-triggers getJobVacancy", async () => {
    mockGetJobVacancy.mockRejectedValue(new Error("500"))

    render(<JobPage />)

    await waitFor(() => screen.getByRole("button", { name: /tentar novamente/i }))

    const callCountAfterFirstLoad = mockGetJobVacancy.mock.calls.length

    mockGetJobVacancy.mockRejectedValueOnce(new Error("still failing"))

    fireEvent.click(screen.getByRole("button", { name: /tentar novamente/i }))

    await waitFor(() => {
      expect(mockGetJobVacancy.mock.calls.length).toBeGreaterThan(callCountAfterFirstLoad)
    })
  })

  it("renders the kanban page when getJobVacancy succeeds", async () => {
    mockGetJobVacancy.mockResolvedValue({
      id: "test-job-id",
      title: "Engenheiro Sênior",
      status: "Ativa",
      created_at: "2026-01-01T00:00:00Z",
      technical_requirements: [],
      benefits: [],
      interview_stages: [],
      salary_range: null,
    })

    render(<JobPage />)

    await waitFor(() => {
      expect(screen.getByTestId("job-kanban-page")).toBeInTheDocument()
    })

    expect(screen.queryByRole("alert")).toBeNull()
    expect(screen.queryByRole("status")).toBeNull()
  })

  it("shows error state and retry button when getJobVacancy times out after 15 s", async () => {
    vi.useFakeTimers()

    mockGetJobVacancy.mockImplementation(
      () =>
        new Promise<never>((_, reject) =>
          setTimeout(
            () =>
              reject(
                Object.assign(new Error("signal is aborted without reason"), {
                  name: "AbortError",
                })
              ),
            15000
          )
        )
    )

    render(<JobPage />)

    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000)
    })

    // Restore real timers so waitFor's internal polling works normally.
    // afterEach also calls useRealTimers as a defensive guard.
    vi.useRealTimers()

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument()
    })

    expect(screen.getByText("Erro ao carregar a vaga")).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: /tentar novamente/i })
    ).toBeInTheDocument()
  })
})
