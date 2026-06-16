/**
 * Badge consumer tests for TalentPoolsTab (Sprint 7B-3a part 2).
 *
 * Locks: badge prefers assignments_count (real data from Part 1 backend),
 * falls back to "Sourcing legacy" if only legacy flag set, null otherwise.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import React from "react"
import type { TalentPoolSummary } from "@/components/pages-talent-pools/useTalentPools"

// Mock hook so PoolCard renders without backend
vi.mock("@/components/pages-talent-pools/useTalentPools", async () => {
  const actual = await vi.importActual<typeof import("@/components/pages-talent-pools/useTalentPools")>(
    "@/components/pages-talent-pools/useTalentPools"
  )
  return {
    ...actual,
    useTalentPools: () => ({
      pools: testPools,
      activePools: testPools,
      isLoading: false,
      createPool: vi.fn(),
    }),
  }
})

vi.mock("@/components/pages-talent-pools/TalentPoolPage", () => ({
  CreatePoolModal: () => null,
}))

let testPools: TalentPoolSummary[] = []

import TalentPoolsTab from "../TalentPoolsTab"

function makePool(overrides: Partial<TalentPoolSummary>): TalentPoolSummary {
  return {
    id: "p1",
    name: "Test Pool",
    status: "active",
    candidates_count: 10,
    screened_count: 5,
    ready_count: 2,
    ideal_profile_name: null,
    agent_sourcing_enabled: false,
    ...overrides,
  }
}

describe("TalentPoolsTab badge consumer", () => {
  it("renderiza \"3 agentes\" quando assignments_count=3", () => {
    testPools = [makePool({ assignments_count: 3 })]
    render(<TalentPoolsTab onSelectPool={() => {}} />)
    expect(screen.getByText("3 agentes")).toBeInTheDocument()
  })

  it("renderiza \"1 agente\" (singular) quando assignments_count=1", () => {
    testPools = [makePool({ id: "p2", assignments_count: 1 })]
    render(<TalentPoolsTab onSelectPool={() => {}} />)
    expect(screen.getByText("1 agente")).toBeInTheDocument()
  })

  it("renderiza \"Sourcing legacy\" quando assignments_count=0 + agent_sourcing_enabled=true", () => {
    testPools = [makePool({ id: "p3", assignments_count: 0, agent_sourcing_enabled: true })]
    render(<TalentPoolsTab onSelectPool={() => {}} />)
    expect(screen.getByText("Sourcing legacy")).toBeInTheDocument()
  })

  it("não renderiza badge quando assignments_count=0 + agent_sourcing_enabled=false", () => {
    testPools = [makePool({ id: "p4", assignments_count: 0, agent_sourcing_enabled: false })]
    render(<TalentPoolsTab onSelectPool={() => {}} />)
    expect(screen.queryByText(/agente/i)).not.toBeInTheDocument()
    expect(screen.queryByText("Sourcing legacy")).not.toBeInTheDocument()
  })
})
