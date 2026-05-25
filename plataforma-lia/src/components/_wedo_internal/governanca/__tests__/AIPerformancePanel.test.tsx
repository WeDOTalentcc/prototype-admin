/**
 * AIPerformancePanel — Wave 2 Agent A T-19 Fase 6 dashboard.
 *
 * Verifica:
 *  - render dos 4 tabs canonical (experiments / bandit / early-stop / history)
 *  - fetch inicial /experiments + /dashboard/summary on mount
 *  - promote-winner POST canonical (use_thompson_sampling)
 *  - bandit posteriors α/β render
 *  - empty state quando 0 experiments
 */
import React from "react"
import { describe, it, expect, beforeEach, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import "@testing-library/jest-dom/vitest"

vi.mock("next-intl", () => {
  const tFn = (k: string) => k
  return { useTranslations: () => tFn }
})
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1" }),
}))

import { AIPerformancePanel } from "@/components/_wedo_internal/governanca/AIPerformancePanel"

const fetchMock = vi.fn()

function buildExperiment(overrides: Record<string, unknown> = {}) {
  return {
    name: "wsi_v1_vs_v2",
    variants: [
      { variant_name: "control", traffic_percentage: 50, is_active: true },
      { variant_name: "variant_b", traffic_percentage: 50, is_active: true },
    ],
    current_winner: "variant_b",
    p_value: 0.003,
    n_arms: 2,
    status: "active",
    total_observations: 400,
    ...overrides,
  }
}

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal("fetch", fetchMock)
})

describe("AIPerformancePanel — Wave 2 T-19", () => {
  it("renders 4 canonical tabs", async () => {
    fetchMock.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/experiments")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ experiments: [buildExperiment()] }),
        })
      }
      if (typeof url === "string" && url.includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              summary: {
                active_count: 1,
                promoted_ready: 1,
                pending_fairness_gate: 0,
                total_observations: 400,
              },
            }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    render(<AIPerformancePanel />)

    await waitFor(() => {
      expect(screen.getByTestId("ai-performance-tab-experiments")).toBeInTheDocument()
    })
    expect(screen.getByTestId("ai-performance-tab-bandit")).toBeInTheDocument()
    expect(screen.getByTestId("ai-performance-tab-early-stop")).toBeInTheDocument()
    expect(screen.getByTestId("ai-performance-tab-history")).toBeInTheDocument()
  })

  it("fetches experiments + summary on mount", async () => {
    fetchMock.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/experiments")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ experiments: [buildExperiment()] }),
        })
      }
      if (typeof url === "string" && url.includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              summary: {
                active_count: 1,
                promoted_ready: 1,
                pending_fairness_gate: 0,
                total_observations: 400,
              },
            }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    render(<AIPerformancePanel />)

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]))
      expect(calls.some((u) => u.includes("/ai-performance/experiments"))).toBe(true)
      expect(calls.some((u) => u.includes("/ai-performance/dashboard/summary"))).toBe(true)
    })
  })

  it("calls promote-winner endpoint when button clicked", async () => {
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (typeof url === "string" && url.includes("/promote-winner") && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              promoted: true,
              winner: "variant_b",
              reason: "auto_promoted",
              gate_used: "frequentist",
            }),
        })
      }
      if (typeof url === "string" && url.includes("/experiments")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ experiments: [buildExperiment()] }),
        })
      }
      if (typeof url === "string" && url.includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              summary: {
                active_count: 1,
                promoted_ready: 1,
                pending_fairness_gate: 0,
                total_observations: 400,
              },
            }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    render(<AIPerformancePanel />)

    const btn = await screen.findByTestId("promote-frequentist-wsi_v1_vs_v2")
    fireEvent.click(btn)

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]))
      expect(calls.some((u) => u.includes("/promote-winner"))).toBe(true)
    })
    await waitFor(() => {
      expect(screen.getByTestId("promote-result")).toBeInTheDocument()
    })
  })

  it("renders empty state when no experiments", async () => {
    fetchMock.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/experiments")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ experiments: [] }),
        })
      }
      if (typeof url === "string" && url.includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              summary: {
                active_count: 0,
                promoted_ready: 0,
                pending_fairness_gate: 0,
                total_observations: 0,
              },
            }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    render(<AIPerformancePanel />)

    await waitFor(() => {
      expect(screen.getByText("empty.experiments")).toBeInTheDocument()
    })
  })

  it("loads bandit posteriors when bandit tab is active", async () => {
    fetchMock.mockImplementation((url: string) => {
      if (typeof url === "string" && url.includes("/posteriors")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              test_name: "wsi_v1_vs_v2",
              posteriors: [
                { arm: "control", alpha: 4, beta: 2, expected_value: 0.6667, n_observations: 4 },
                { arm: "variant_b", alpha: 6, beta: 2, expected_value: 0.75, n_observations: 6 },
              ],
            }),
        })
      }
      if (typeof url === "string" && url.includes("/experiments")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ experiments: [buildExperiment()] }),
        })
      }
      if (typeof url === "string" && url.includes("/dashboard/summary")) {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({
              summary: {
                active_count: 1,
                promoted_ready: 1,
                pending_fairness_gate: 0,
                total_observations: 400,
              },
            }),
        })
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) })
    })

    render(<AIPerformancePanel />)

    const banditTab = await screen.findByTestId("ai-performance-tab-bandit")
    fireEvent.click(banditTab)

    await waitFor(() => {
      expect(screen.getByTestId("bandit-row-control")).toBeInTheDocument()
      expect(screen.getByTestId("bandit-row-variant_b")).toBeInTheDocument()
    })
  })
})
