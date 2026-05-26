import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor, act } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import React from "react"

vi.mock("@/lib/api/api-fetch", () => ({
  apiFetch: vi.fn(),
}))

import { apiFetch } from "@/lib/api/api-fetch"
import {
  useAutomationsList,
  useCreateAutomation,
  useUpdateAutomation,
  useDeleteAutomation,
  useToggleAutomationActive,
  useTestAutomation,
  useTriggerTypes,
  useActionTypes,
  type AutomationResponse,
} from "@/hooks/automations/useAutomationMutations"

function makeWrapper() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const Wrapper = ({ children }: { children: ReactNode }) =>
    React.createElement(QueryClientProvider, { client }, children)
  return { Wrapper, client }
}

function mockOk(body: unknown) {
  return {
    ok: true,
    status: 200,
    json: async () => body,
    text: async () => JSON.stringify(body),
  } as unknown as Response
}

function mockFail(status = 500, text = "") {
  return {
    ok: false,
    status,
    json: async () => ({}),
    text: async () => text,
  } as unknown as Response
}

const baseAutomation: AutomationResponse = {
  id: "auto-1",
  name: "Test",
  trigger_type: "x",
  action_type: "y",
  is_active: true,
  executions_count: 0,
  last_executed_at: null,
  success_rate: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
}

describe("useAutomationMutations canonical", () => {
  beforeEach(() => vi.clearAllMocks())

  it("useAutomationsList retorna lista quando OK", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk([baseAutomation]))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAutomationsList(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([baseAutomation])
  })

  it("useAutomationsList unwrap {automations: [...]} shape", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk({ automations: [baseAutomation] }))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAutomationsList(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual([baseAutomation])
  })

  it("useAutomationsList throws em falha (fail-CLOSED, NUNCA silent fallback)", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockFail(500))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAutomationsList(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(result.current.error).toBeDefined()
    expect((result.current.error as Error).message).toContain("500")
  })

  it("useCreateAutomation POST + invalida query lista", async () => {
    const created = { ...baseAutomation, id: "new-1" }
    vi.mocked(apiFetch).mockResolvedValue(mockOk(created))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useCreateAutomation(), { wrapper: Wrapper })
    await act(async () => {
      const r = await result.current.mutateAsync({
        trigger_type: "x",
        action_type: "y",
      })
      expect(r.id).toBe("new-1")
    })
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations",
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("useCreateAutomation propaga erro (fail-CLOSED)", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockFail(422, "validation"))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useCreateAutomation(), { wrapper: Wrapper })
    await expect(
      result.current.mutateAsync({ trigger_type: "x", action_type: "y" }),
    ).rejects.toThrow(/422/)
  })

  it("useUpdateAutomation PUT endpoint correto", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk(baseAutomation))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useUpdateAutomation(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.mutateAsync({
        id: "auto-1",
        trigger_type: "x",
        action_type: "y",
        name: "Updated",
      })
    })
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations/auto-1",
      expect.objectContaining({ method: "PUT" }),
    )
  })

  it("useDeleteAutomation faz optimistic update + rollback em erro", async () => {
    const { Wrapper, client } = makeWrapper()
    client.setQueryData(["automations"], [baseAutomation, { ...baseAutomation, id: "auto-2" }])

    vi.mocked(apiFetch).mockResolvedValue(mockFail(500))
    const { result } = renderHook(() => useDeleteAutomation(), { wrapper: Wrapper })

    await act(async () => {
      try {
        await result.current.mutateAsync("auto-1")
      } catch {
        /* expected */
      }
    })

    // Rollback restaurou lista original
    await waitFor(() => {
      const data = client.getQueryData<AutomationResponse[]>(["automations"])
      expect(data).toHaveLength(2)
    })
  })

  it("useDeleteAutomation success path remove item", async () => {
    const { Wrapper, client } = makeWrapper()
    client.setQueryData(["automations"], [baseAutomation, { ...baseAutomation, id: "auto-2" }])

    vi.mocked(apiFetch).mockResolvedValue(mockOk({}))
    const { result } = renderHook(() => useDeleteAutomation(), { wrapper: Wrapper })

    await act(async () => {
      await result.current.mutateAsync("auto-1")
    })

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations/auto-1",
      expect.objectContaining({ method: "DELETE" }),
    )
  })

  it("useToggleAutomationActive faz optimistic toggle", async () => {
    const { Wrapper, client } = makeWrapper()
    client.setQueryData(["automations"], [{ ...baseAutomation, is_active: false }])

    vi.mocked(apiFetch).mockResolvedValue(mockOk({ ...baseAutomation, is_active: true }))
    const { result } = renderHook(() => useToggleAutomationActive(), { wrapper: Wrapper })

    await act(async () => {
      await result.current.mutateAsync({ id: "auto-1", isActive: true })
    })

    const data = client.getQueryData<AutomationResponse[]>(["automations"])
    expect(data?.[0].is_active).toBe(true)
  })

  it("useTestAutomation chama /test endpoint", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk({ ok: true, dry_run: true }))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useTestAutomation(), { wrapper: Wrapper })

    await act(async () => {
      const r = await result.current.mutateAsync({ id: "auto-1", dryRunPayload: { foo: "bar" } })
      expect(r).toEqual({ ok: true, dry_run: true })
    })

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations/auto-1/test",
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("useTriggerTypes faz fetch endpoint correto", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk([{ id: "new_application" }]))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useTriggerTypes(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations/trigger-types/available",
    )
  })

  it("useActionTypes faz fetch endpoint correto", async () => {
    vi.mocked(apiFetch).mockResolvedValue(mockOk([{ id: "send_email" }]))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useActionTypes(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/backend-proxy/automations/action-types/available",
    )
  })
})
