/**
 * useLiaFieldTogglesForSection.test.ts — Fase 4.1 contract (2026-06-04)
 *
 * Trava o contrato do hook ANTES de replicar o padrao nos hubs:
 *  - shape SectionFieldCard (label/hint/isActive/instruction) a partir de LIA_FIELD_DEFINITIONS
 *  - default ON quando toggle ausente
 *  - 404 -> {toggles:{},comments:{}} sem throw (REGRA anti-silent: erro real >=500 propaga)
 *  - PUT { toggles, comments } SEM company_id no payload (multi-tenancy REGRA R2)
 *  - onInstructionSave grava no comments map
 *  - rollback otimista em erro de PUT (nao dispara dispatchSettingsUpdate)
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
import { LIA_FIELD_DEFINITIONS } from "@/hooks/company/use-company-lia-instructions"
import {
  useLiaFieldTogglesForSection,
  liaFieldTogglesKey,
} from "../useLiaFieldTogglesForSection"

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
    resp(true, { toggles: { benefits: true }, comments: { benefits: "usar pacote padrao" } }),
  )
})

describe("useLiaFieldTogglesForSection", () => {
  it("mapeia sectionKeys -> fields com shape do ConfigurableFieldCard", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.fields).toHaveLength(1)
    const f = result.current.fields[0]
    expect(f.key).toBe("benefits")
    expect(f.label).toBe((LIA_FIELD_DEFINITIONS as Record<string, { label: string; location: string }>).benefits.label)
    expect(f.hint).toBe((LIA_FIELD_DEFINITIONS as Record<string, { label: string; location: string }>).benefits.location)
    expect(f.isActive).toBe(true)
    expect(f.instruction).toBe("usar pacote padrao")
    expect(typeof f.onToggleChange).toBe("function")
    expect(typeof f.onInstructionSave).toBe("function")
  })

  it("default ON quando toggle ausente", async () => {
    mockApiFetch.mockResolvedValue(resp(true, { toggles: {}, comments: {} }))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.fields[0].isActive).toBe(true)
  })

  it("404 -> vazio sem throw (e default ON)", async () => {
    mockApiFetch.mockResolvedValue(resp(false, {}, 404))
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    expect(result.current.error).toBeNull()
    expect(result.current.fields[0].isActive).toBe(true)
  })

  it("onToggleChange faz PUT {toggles,comments} SEM company_id no payload", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.fields[0].onToggleChange(false)
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const [url, opts] = mockApiFetch.mock.calls[0] as [string, RequestInit]
    expect(url).toContain("/company/co-1/field-toggles")
    expect(opts.method).toBe("PUT")
    const body = JSON.parse(opts.body as string)
    expect(body).toHaveProperty("toggles")
    expect(body).toHaveProperty("comments")
    expect(body).not.toHaveProperty("company_id")
    expect(body.toggles.benefits).toBe(false)
    await waitFor(() => expect(dispatchSpy).toHaveBeenCalled())
  })

  it("onInstructionSave grava a instrucao no comments map", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    mockApiFetch.mockClear()
    mockApiFetch.mockResolvedValue(resp(true, {}))
    await act(async () => {
      result.current.fields[0].onInstructionSave("nova instrucao")
    })
    await waitFor(() => expect(mockApiFetch).toHaveBeenCalled())
    const body = JSON.parse((mockApiFetch.mock.calls[0] as [string, RequestInit])[1].body as string)
    expect(body.comments.benefits).toBe("nova instrucao")
  })

  it("erro de PUT: rollback otimista e NAO dispara dispatchSettingsUpdate", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useLiaFieldTogglesForSection(["benefits"]), { wrapper: Wrapper })
    await waitFor(() => expect(result.current.isLoading).toBe(false))
    dispatchSpy.mockClear()
    // PUT falha (500); refetch subsequente cai no default GET (benefits:true)
    mockApiFetch.mockResolvedValueOnce(resp(false, {}, 500))
    await act(async () => {
      result.current.fields[0].onToggleChange(false)
    })
    await waitFor(() => expect(result.current.fields[0].isActive).toBe(true))
    expect(dispatchSpy).not.toHaveBeenCalled()
  })
})
