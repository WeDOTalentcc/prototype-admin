/**
 * Onda 3 F8 (2026-05-28) — useDeploymentsByTargets canonical tests.
 *
 * Cobertura:
 *   1. Query key inclui targetIds ordenados (estabilidade de cache).
 *   2. enabled=false quando targetIds vazio.
 *   3. POST body bate com canonical schema (target_type + target_ids).
 */
import { describe, expect, it, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React from "react"
import {
  useDeploymentsByTargets,
  DEPLOYMENTS_BY_TARGETS_QUERY_KEY,
} from "../use-deployments-by-targets"

beforeEach(() => {
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: vi.fn(() => "token"),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    },
    configurable: true,
  })
})

function wrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client }, children)
}

describe("useDeploymentsByTargets", () => {
  it("query key inclui targetIds ordenados (estabilidade de cache)", () => {
    const a = DEPLOYMENTS_BY_TARGETS_QUERY_KEY("job", ["c", "a", "b"])
    const b = DEPLOYMENTS_BY_TARGETS_QUERY_KEY("job", ["a", "b", "c"])
    expect(a).toEqual(b)
  })

  it("não faz fetch quando targetIds vazio", async () => {
    const fetchSpy = vi.fn()
    global.fetch = fetchSpy as unknown as typeof fetch

    renderHook(
      () =>
        useDeploymentsByTargets({
          targetType: "job",
          targetIds: [],
        }),
      { wrapper: wrapper() },
    )
    // wait a tick
    await new Promise((r) => setTimeout(r, 50))
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it("POST body bate com canonical schema", async () => {
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ deployments_by_target: {} }),
    })
    global.fetch = fetchSpy as unknown as typeof fetch

    const { result } = renderHook(
      () =>
        useDeploymentsByTargets({
          targetType: "pipeline_stage",
          targetIds: ["s1", "s2"],
        }),
      { wrapper: wrapper() },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(fetchSpy).toHaveBeenCalled()
    const [url, init] = fetchSpy.mock.calls[0] as [string, RequestInit]
    expect(url).toBe("/api/backend-proxy/agent-deployments/by-targets")
    expect(init.method).toBe("POST")
    const body = JSON.parse(init.body as string)
    expect(body).toEqual({
      target_type: "pipeline_stage",
      target_ids: ["s1", "s2"],
    })
  })
})
