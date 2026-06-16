import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { createElement, type ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useLiaCandidate, useLiaJob } from "@/hooks/lia/use-lia-entity"
import { ENTITY_MODAL_REGISTRY } from "@/components/lia-global-modals/lia-entity-modal-registry"

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return createElement(QueryClientProvider, { client }, children)
}

describe("Fase B3 — registry de modais entidade-acopláveis", () => {
  it("mapeia score/bigfive→candidate e report→job", () => {
    expect(ENTITY_MODAL_REGISTRY.general_score).toBe("candidate")
    expect(ENTITY_MODAL_REGISTRY.big_five).toBe("candidate")
    expect(ENTITY_MODAL_REGISTRY.job_report).toBe("job")
  })
})

describe("Fase B3 — useLiaCandidate/useLiaJob (fetch id→objeto)", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("desabilitado sem id (não dispara fetch)", () => {
    const spy = vi.fn()
    global.fetch = spy as unknown as typeof fetch
    const { result } = renderHook(() => useLiaCandidate(undefined), { wrapper })
    expect(result.current.fetchStatus).toBe("idle")
    expect(spy).not.toHaveBeenCalled()
  })

  it("candidato: fetcha proxy company-scoped e retorna objeto", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "c1", name: "Fulano" }),
    }) as unknown as typeof fetch
    const { result } = renderHook(() => useLiaCandidate("c1"), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({ id: "c1", name: "Fulano" })
    expect(global.fetch).toHaveBeenCalledWith("/api/backend-proxy/candidates/c1")
  })

  it("vaga: desce um nível se vier wrapper { data } sem id próprio", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ data: { id: "j1", title: "Dev" } }),
    }) as unknown as typeof fetch
    const { result } = renderHook(() => useLiaJob("j1"), { wrapper })
    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(result.current.data).toEqual({ id: "j1", title: "Dev" })
    expect(global.fetch).toHaveBeenCalledWith("/api/backend-proxy/job-vacancies/j1")
  })

  it("erro HTTP → isError", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 }) as unknown as typeof fetch
    const { result } = renderHook(() => useLiaJob("nope"), { wrapper })
    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})
