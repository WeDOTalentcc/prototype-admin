/**
 * useAllLiaFieldToggles.test.ts — contrato da camada de dados do painel central (F5.3).
 * Migrado de useLiaFieldTogglesForSection (section-hook removido como dead code pos-F5.1b);
 * o contrato (PUT sem company_id, rollback, batch) agora cobre o hook VIVO.
 */
import React from "react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

vi.mock("@/lib/api/api-fetch", () => ({ apiFetch: vi.fn() }))
vi.mock("@/hooks/company/useCompanyId", () => ({
  useCompanyId: () => ({ companyId: "co-1", isLoading: false }),
}))
const dispatchSpy = vi.fn()
vi.mock("@/hooks/settings/useSettingsBroadcast", () => ({
  dispatchSettingsUpdate: (...a: unknown[]) => dispatchSpy(...a),
}))

import { apiFetch } from "@/lib/api/api-fetch"
import { useAllLiaFieldToggles } from "../useLiaFieldTogglesForSection"

const mockApiFetch = apiFetch as unknown as ReturnType<typeof vi.fn>

function resp(ok: boolean, data: unknown = {}, status = 200): Response {
  return { ok, status, json: async () => data } as unknown as Response
}

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  return { Wrapper, queryClient }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockApiFetch.mockResolvedValue(
    resp(true, { toggles: { benefits: true }, comments: { benefits: "usar pacote" } }),
  )
})

describe("useAllLiaFieldToggles", () => {
  it("carrega toggles+comments do GET", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.toggles.benefits).toBe(true)
    expect(result.current.comments.benefits).toBe("usar pacote")
  })

  it("404 -> vazio sem throw", async () => {
    mockApiFetch.mockResolvedValue(resp(false, {}, 404))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeNull()
    expect(result.current.toggles).toEqual({})
  })

  it("saveToggle faz PUT {toggles,comments} SEM company_id no payload", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.saveToggle("benefits", false)
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const [url, opts] = mockApiFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/company/co-1/field-toggles")
    expect(opts.method).toBe("PUT")
    const body = JSON.parse(opts.body as string)
    expect(body).not.toHaveProperty("company_id")
    expect(body.toggles.benefits).toBe(false)
    await waitFor(() => expect(dispatchSpy).toHaveBeenCalled())
  })

  it("saveInstruction grava no comments", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.saveInstruction("benefits", "nova instrucao")
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const body = JSON.parse((mockApiFetch.mock.calls[0] as [string, RequestInit])[1].body as string)
    expect(body.comments.benefits).toBe("nova instrucao")
  })

  it("toggleAll(false) desliga todos os campos", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.toggleAll(false)
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const body = JSON.parse((mockApiFetch.mock.calls[0] as [string, RequestInit])[1].body as string)
    const vals = Object.values(body.toggles) as boolean[]
    expect(vals.length).toBeGreaterThan(10)
    expect(vals.every((v) => v === false)).toBe(true)
  })

  it("clearAllInstructions zera comments", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.clearAllInstructions()
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const body = JSON.parse((mockApiFetch.mock.calls[0] as [string, RequestInit])[1].body as string)
    expect(body.comments).toEqual({})
  })

  it("erro de PUT: rollback otimista e NAO dispara dispatchSettingsUpdate", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useAllLiaFieldToggles(), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    dispatchSpy.mockClear()
    mockApiFetch.mockResolvedValueOnce(resp(false, {}, 500))
    await act(async () => {
      result.current.saveToggle("benefits", false)
    })
    await waitFor(() => expect(result.current.toggles.benefits).toBe(true))
    expect(dispatchSpy).not.toHaveBeenCalled()
  })
})
