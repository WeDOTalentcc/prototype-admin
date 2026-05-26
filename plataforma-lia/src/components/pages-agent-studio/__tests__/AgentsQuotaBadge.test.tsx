/**
 * AgentsQuotaBadge — Sprint 7C / 7B-3b backlog (max_agents_total alias canonical).
 *
 * Valida (1) render canonical "X/Y agentes" + (2) cor per percentage canonical.
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { AgentsQuotaBadge } from "../AgentsQuotaBadge"
import { computeTotalTier } from "@/hooks/agent-studio/use-agents-total-quota"

vi.mock("@/hooks/agent-studio/use-agents-total-quota", async () => {
  const actual = await vi.importActual<typeof import("@/hooks/agent-studio/use-agents-total-quota")>(
    "@/hooks/agent-studio/use-agents-total-quota",
  )
  return {
    ...actual,
    useAgentsTotalQuota: vi.fn(),
  }
})

import { useAgentsTotalQuota } from "@/hooks/agent-studio/use-agents-total-quota"
const mockUse = useAgentsTotalQuota as unknown as ReturnType<typeof vi.fn>

describe("AgentsQuotaBadge — render canonical", () => {
  it("renders 'X/Y' text with green tier when below 70%", () => {
    mockUse.mockReturnValue({
      data: {
        company_id: "c1",
        max_agents_total: 10,
        current_agents_total: 5,
        percentage_agents_total: 50,
        is_unlimited: false,
      },
      tier: "green",
      isLoading: false,
      error: null,
      refetch: async () => {},
    })
    render(<AgentsQuotaBadge />)
    const badge = screen.getByTestId("agents-quota-badge")
    expect(badge.textContent).toBe("5/10")
    expect(badge.getAttribute("data-tier")).toBe("green")
  })

  it("renders null when data has undefined fields (defensive guard)", () => {
    mockUse.mockReturnValue({
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: {} as any,
      tier: "green",
      isLoading: false,
      error: null,
      refetch: async () => {},
    })
    render(<AgentsQuotaBadge />)
    expect(screen.queryByTestId("agents-quota-badge")).toBeNull()
    expect(screen.queryByTestId("agents-quota-badge-dot")).toBeNull()
  })

  it("renders null when data has NaN fields (defensive guard)", () => {
    mockUse.mockReturnValue({
      data: {
        company_id: "c1",
        max_agents_total: Number.NaN,
        current_agents_total: Number.NaN,
        percentage_agents_total: 0,
        is_unlimited: false,
      },
      tier: "green",
      isLoading: false,
      error: null,
      refetch: async () => {},
    })
    render(<AgentsQuotaBadge />)
    expect(screen.queryByTestId("agents-quota-badge")).toBeNull()
  })
})

describe("computeTotalTier — cor canonical per percentage", () => {
  it("returns green<70, amber 70-94, coral≥95, unlimited=green", () => {
    expect(computeTotalTier(0, false)).toBe("green")
    expect(computeTotalTier(69.99, false)).toBe("green")
    expect(computeTotalTier(70, false)).toBe("amber")
    expect(computeTotalTier(94, false)).toBe("amber")
    expect(computeTotalTier(95, false)).toBe("coral")
    expect(computeTotalTier(100, false)).toBe("coral")
    expect(computeTotalTier(0, true)).toBe("green") // unlimited
    expect(computeTotalTier(99999, true)).toBe("green") // unlimited propaga
  })
})
