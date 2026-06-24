/**
 * TalentPoolInsightsModal — unit tests
 *
 * Rules of Hooks discipline: smoke test isOpen=false → true → false.
 * TDD canonical: Red → Green written together with the component (2026-06-17).
 */

import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { TalentPoolInsightsModal } from "../TalentPoolInsightsModal"

// ── Mocks ──────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}))

// Mock Dialog — radix-ui headless works in jsdom but may need this shim
vi.mock("@/components/ui/dialog", () => ({
  Dialog: ({ open, onOpenChange, children }: { open: boolean; onOpenChange: (v: boolean) => void; children: React.ReactNode }) =>
    open ? <div data-testid="dialog">{children}</div> : null,
  DialogContent: ({ children, ...props }: { children: React.ReactNode } & Record<string, unknown>) => (
    <div data-testid="dialog-content" {...props}>{children}</div>
  ),
  DialogHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DialogTitle: ({ children }: { children: React.ReactNode }) => <h2>{children}</h2>,
}))

vi.mock("@/components/settings/_shared/HubLoadingState", () => ({
  HubLoadingState: ({ message }: { message?: string }) => (
    <div data-testid="hub-loading">{message ?? "Carregando..."}</div>
  ),
}))

vi.mock("@/components/settings/_shared/HubErrorState", () => ({
  HubErrorState: ({ message, onRetry }: { message?: string; onRetry?: () => void }) => (
    <div data-testid="hub-error">
      {message}
      {onRetry && (
        <button type="button" onClick={onRetry} data-testid="retry-btn">
          Tentar novamente
        </button>
      )}
    </div>
  ),
}))

// ── Helpers ────────────────────────────────────────────────────────────────

const MOCK_DATA = {
  job_id: "job-123",
  metrics: {
    total_candidates: 42,
    in_screening: 10,
    in_interview: 5,
    in_offer: 2,
    hired: 1,
    rejected: 8,
    conversion_rate: 0.24,
    avg_time_to_fill_days: 30,
  },
  hiring_probability: {
    probability: 72,
    confidence: "high" as const,
  },
  pipeline_prediction: {
    closure_probability: 60,
    estimated_days_to_close: 14,
    confidence_level: "medium",
  },
  top_skills: [
    { skill: "Python", count: 30, percentage: 71 },
    { skill: "SQL", count: 20, percentage: 47 },
    { skill: "React", count: 15, percentage: 35 },
  ],
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>
}

// ── Tests ──────────────────────────────────────────────────────────────────

describe("TalentPoolInsightsModal", () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it("does not render when isOpen=false", () => {
    render(
      <TalentPoolInsightsModal
        isOpen={false}
        onClose={vi.fn()}
        jobId="job-123"
      />,
      { wrapper }
    )
    expect(screen.queryByTestId("dialog")).toBeNull()
    expect(screen.queryByTestId("talent-pool-insights-modal")).toBeNull()
  })

  it("renders loading state while fetching", async () => {
    // Never resolves — stays loading
    global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch

    render(
      <TalentPoolInsightsModal
        isOpen
        onClose={vi.fn()}
        jobId="job-123"
        jobTitle="Engenheiro de Software"
      />,
      { wrapper }
    )

    expect(screen.getByTestId("hub-loading")).toBeDefined()
    // Modal header should be visible even while loading
    expect(screen.getByText("Talent Pool Insights")).toBeDefined()
    expect(screen.getByText("Engenheiro de Software")).toBeDefined()
  })

  it("renders KPI cards and skills when data loads", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_DATA),
    }) as unknown as typeof fetch

    render(
      <TalentPoolInsightsModal
        isOpen
        onClose={vi.fn()}
        jobId="job-123"
      />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getByText("72%")).toBeDefined()
    })

    // KPI values
    expect(screen.getByText("60%")).toBeDefined()
    expect(screen.getByText("14 dias")).toBeDefined()
    // Candidate count in header
    expect(screen.getByText("42 candidatos")).toBeDefined()
    // Top skills
    expect(screen.getByText("Python")).toBeDefined()
    expect(screen.getByText("SQL")).toBeDefined()
    // Confidence badge
    expect(screen.getByText("Alta confiança")).toBeDefined()
    // Premium lock text
    expect(screen.getByText("Disponível no plano Enterprise")).toBeDefined()
    // Pipeline mini-stats
    expect(screen.getByText("Triagem")).toBeDefined()
    expect(screen.getByText("Entrevista")).toBeDefined()
    expect(screen.getByText("Oferta")).toBeDefined()
  })

  it("calls onClose when dialog onOpenChange fires with false", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_DATA),
    }) as unknown as typeof fetch

    const onClose = vi.fn()
    render(
      <TalentPoolInsightsModal
        isOpen
        onClose={onClose}
        jobId="job-123"
      />,
      { wrapper }
    )

    await waitFor(() => screen.getByText("72%"))

    // Footer CTA "Ver análise completa →" is a button
    const cta = screen.getByText("Ver análise completa →")
    await userEvent.click(cta)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("shows premium locked section with overlay", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(MOCK_DATA),
    }) as unknown as typeof fetch

    render(
      <TalentPoolInsightsModal
        isOpen
        onClose={vi.fn()}
        jobId="job-123"
      />,
      { wrapper }
    )

    await waitFor(() => screen.getByText("72%"))

    expect(screen.getByText("Disponível no plano Enterprise")).toBeDefined()
    expect(screen.getByText("Upgrade Plan →")).toBeDefined()
  })

  it("shows error state and retry button on fetch failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: "Internal error" }),
    }) as unknown as typeof fetch

    render(
      <TalentPoolInsightsModal
        isOpen
        onClose={vi.fn()}
        jobId="job-123"
      />,
      { wrapper }
    )

    await waitFor(() => {
      expect(screen.getByTestId("hub-error")).toBeDefined()
    })

    expect(screen.getByText("Não foi possível carregar os insights.")).toBeDefined()
    expect(screen.getByTestId("retry-btn")).toBeDefined()
  })
})
