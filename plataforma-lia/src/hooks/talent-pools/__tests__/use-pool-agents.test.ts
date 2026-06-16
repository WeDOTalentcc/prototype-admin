/**
 * use-pool-agents.test.ts — Sprint 7B-1 RED scaffolding.
 *
 * Cobre 6 paths críticos:
 *  1. usePoolAgents desempacota envelope `{ok, data}` (pattern canonical)
 *  2. usePoolAgents aceita array direto sem envelope (defensive)
 *  3. usePoolAgents `poolId=null` → não dispara fetch
 *  4. assignAgentToPool POST + invalidation
 *  5. updateAssignment PATCH + invalidation
 *  6. unassignAgent DELETE (204) + invalidation
 *
 * Mock SWR `mutate` global pra observar invalidation calls.
 * Mock fetch global per-test.
 *
 * Status esperado: parte RED (mutations RED até PoolAgentsTab consumir em 7B-2).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { SWRConfig } from "swr"
import * as React from "react"

const swrMutateSpy = vi.fn()
vi.mock("swr", async () => {
  const actual: any = await vi.importActual("swr")
  return {
    ...actual,
    mutate: (...args: unknown[]) => {
      swrMutateSpy(...args)
      return actual.mutate(...(args as Parameters<typeof actual.mutate>))
    },
  }
})

import {
  assignAgentToPool,
  dispatchAgent,
  poolAgentsKey,
  unassignAgent,
  updateAssignment,
  usePoolAgents,
} from "../use-pool-agents"

const SAMPLE: any = {
  id: "a1",
  talent_pool_id: "p1",
  custom_agent_id: "agent-1",
  custom_agent_name: "Sourcer",
  custom_agent_category: "sourcing",
  status: "active",
  schedule_type: "on_demand",
  schedule_config: {},
  config_overrides: {},
  last_run_at: null,
  last_run_status: null,
  runtime_metrics: {},
  created_at: "2026-05-25T00:00:00Z",
  updated_at: "2026-05-25T00:00:00Z",
  created_by: "user-1",
}

function wrapper({ children }: { children: React.ReactNode }) {
  return React.createElement(
    SWRConfig,
    { value: { provider: () => new Map(), dedupingInterval: 0 } },
    children,
  )
}

beforeEach(() => {
  swrMutateSpy.mockClear()
  vi.restoreAllMocks()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("usePoolAgents — envelope unwrap canonical", () => {
  it("desempacota envelope {ok, data} canonical", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ ok: true, data: [SAMPLE], meta: {} }),
      }),
    )

    const { result } = renderHook(() => usePoolAgents("p1"), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.data).toEqual([SAMPLE])
    expect(result.current.error).toBeNull()
  })

  it("aceita array direto sem envelope (defensive)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [SAMPLE],
      }),
    )

    const { result } = renderHook(() => usePoolAgents("p1"), { wrapper })

    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.data).toEqual([SAMPLE])
  })

  it("poolId=null → não dispara fetch (defensive)", async () => {
    const fetchSpy = vi.fn()
    vi.stubGlobal("fetch", fetchSpy)

    const { result } = renderHook(() => usePoolAgents(null), { wrapper })

    // SWR não chama fetcher quando key é null
    await new Promise((r) => setTimeout(r, 10))
    expect(fetchSpy).not.toHaveBeenCalled()
    expect(result.current.data).toEqual([])
  })
})

describe("mutations — POST/PATCH/DELETE + invalidation", () => {
  it("assignAgentToPool: POST + invalida key do pool", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => SAMPLE,
      text: async () => "",
    })
    vi.stubGlobal("fetch", fetchSpy)

    const created = await assignAgentToPool("p1", { custom_agent_id: "agent-1" })

    expect(fetchSpy).toHaveBeenCalledWith(
      poolAgentsKey("p1"),
      expect.objectContaining({ method: "POST" }),
    )
    expect(created.id).toBe("a1")
    expect(swrMutateSpy).toHaveBeenCalledWith(poolAgentsKey("p1"))
  })

  it("updateAssignment: PATCH + invalida key do pool", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ...SAMPLE, status: "paused" }),
      text: async () => "",
    })
    vi.stubGlobal("fetch", fetchSpy)

    const updated = await updateAssignment("p1", "a1", { status: "paused" })

    expect(fetchSpy).toHaveBeenCalledWith(
      `${poolAgentsKey("p1")}/a1`,
      expect.objectContaining({ method: "PATCH" }),
    )
    expect(updated.status).toBe("paused")
    expect(swrMutateSpy).toHaveBeenCalledWith(poolAgentsKey("p1"))
  })

  it("unassignAgent: DELETE 204 + invalida key do pool", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      text: async () => "",
    })
    vi.stubGlobal("fetch", fetchSpy)

    await unassignAgent("p1", "a1")

    expect(fetchSpy).toHaveBeenCalledWith(
      `${poolAgentsKey("p1")}/a1`,
      expect.objectContaining({ method: "DELETE" }),
    )
    expect(swrMutateSpy).toHaveBeenCalledWith(poolAgentsKey("p1"))
  })

  it("dispatchAgent: POST /run retorna 202 queued (stub Sprint 7A)", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({ status: "queued", assignment_id: "a1", sprint: "7A-stub" }),
      text: async () => "",
    })
    vi.stubGlobal("fetch", fetchSpy)

    const res = await dispatchAgent("p1", "a1")

    expect(fetchSpy).toHaveBeenCalledWith(
      `${poolAgentsKey("p1")}/a1/run`,
      expect.objectContaining({ method: "POST" }),
    )
    expect(res.status).toBe("queued")
    expect(res.assignment_id).toBe("a1")
  })
})
