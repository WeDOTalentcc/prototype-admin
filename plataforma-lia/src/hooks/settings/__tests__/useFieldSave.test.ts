/**
 * useFieldSave.test.ts — Task 2.7 (2026-05-26)
 *
 * Tests for:
 * - extractErrorMessage: pure async function for API error parsing
 * - useFieldSave: React Query mutation hook (saveField, isSavingField)
 * - performSaveField indirectly through mutation (mocked fetch)
 *
 * Uses QueryClientProvider wrapper as required for React Query hooks.
 */
import React from "react"
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest"
import { renderHook, act, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useFieldSave, extractErrorMessage } from "../useFieldSave"
import type { SaveFieldArgs } from "../useFieldSave"

// ─── Helpers ─────────────────────────────────────────────────────────────────

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children)
  return { Wrapper, queryClient }
}

function makeSaveArgs(overrides: Partial<SaveFieldArgs> = {}): SaveFieldArgs {
  return {
    block: "basic",
    field: "name",
    value: "Acme Corp",
    companyId: "company-uuid-001",
    companyData: null,
    ...overrides,
  }
}

function makeFetchResponse(ok: boolean, data: unknown = {}, status = 200): Response {
  return {
    ok,
    status,
    json: async () => data,
  } as unknown as Response
}

// ─── extractErrorMessage ──────────────────────────────────────────────────────

describe("extractErrorMessage", () => {
  it("returns detail string from JSON body", async () => {
    const resp = makeFetchResponse(false, { detail: "Campo inválido" }, 422)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toBe("Campo inválido")
  })

  it("returns detail JSON-stringified when detail is object", async () => {
    const resp = makeFetchResponse(false, { detail: { msg: "err", type: "value_error" } }, 422)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toContain("msg")
  })

  it("returns message field from JSON body", async () => {
    const resp = makeFetchResponse(false, { message: "Service unavailable" }, 503)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toBe("Service unavailable")
  })

  it("returns error field from JSON body", async () => {
    const resp = makeFetchResponse(false, { error: "Not found" }, 404)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toBe("Not found")
  })

  it("returns session expiry message for 401", async () => {
    const resp = makeFetchResponse(false, {}, 401)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toContain("Sessao expirada")
  })

  it("returns session expiry message for 403", async () => {
    const resp = makeFetchResponse(false, {}, 403)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toContain("Sessao expirada")
  })

  it("returns backend unavailable message for 500+", async () => {
    const resp = makeFetchResponse(false, {}, 500)
    const msg = await extractErrorMessage(resp, "fallback")
    expect(msg).toContain("Backend indisponivel")
  })

  it("returns fallback when JSON parse fails and status is 200 (edge case)", async () => {
    const resp = {
      ok: false,
      status: 200,
      json: async () => { throw new Error("not json") },
    } as unknown as Response
    const msg = await extractErrorMessage(resp, "my fallback message")
    expect(msg).toBe("my fallback message")
  })
})

// ─── useFieldSave hook ────────────────────────────────────────────────────────

describe("useFieldSave", () => {
  afterEach(() => vi.restoreAllMocks())

  it("returns saveField and isSavingField", () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    expect(typeof result.current.saveField).toBe("function")
    expect(typeof result.current.isSavingField).toBe("boolean")
  })

  it("isSavingField is false initially", () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    expect(result.current.isSavingField).toBe(false)
  })

  it("saveField resolves on successful fetch response", async () => {
    const { Wrapper } = makeWrapper()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200)))

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs())
    })

    expect(vi.mocked(fetch)).toHaveBeenCalled()
    vi.unstubAllGlobals()
  })

  it("saveField calls correct endpoint for basic block", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs({ block: "basic", field: "name", value: "Acme" }))
    })

    const url = mockFetch.mock.calls[0][0] as string
    expect(url).toContain("/api/backend-proxy/company/profile/company-uuid-001")
    vi.unstubAllGlobals()
  })

  it("saveField calls PUT for basic block", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs({ block: "basic", field: "website", value: "https://acme.com" }))
    })

    const init = mockFetch.mock.calls[0][1] as RequestInit
    expect(init.method).toBe("PUT")
    vi.unstubAllGlobals()
  })

  it("saveField calls PATCH endpoint for policy block", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs({
        block: "policy",
        field: "min_interviews_before_offer",
        value: 2,
      }))
    })

    const url = mockFetch.mock.calls[0][0] as string
    const init = mockFetch.mock.calls[0][1] as RequestInit
    expect(url).toContain("/api/backend-proxy/hiring-policy/block")
    expect(init.method).toBe("PATCH")
    vi.unstubAllGlobals()
  })

  it("saveField calls POST /skills-catalog/sync for tech_stack field", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs({
        block: "tech",
        field: "tech_stack",
        value: ["React", "Node.js"],
      }))
    })

    const url = mockFetch.mock.calls[0][0] as string
    const init = mockFetch.mock.calls[0][1] as RequestInit
    expect(url).toContain("/api/backend-proxy/skills-catalog/company/skills-catalog/sync")
    expect(init.method).toBe("POST")
    vi.unstubAllGlobals()
  })

  it("saveField throws for workforce block (not inline-editable)", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })

    await expect(
      act(async () => {
        await result.current.saveField(makeSaveArgs({ block: "workforce", field: "hiring_volume", value: 10 }))
      })
    ).rejects.toThrow()
  })

  it("saveField throws for benefits block (not inline-editable)", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })

    await expect(
      act(async () => {
        await result.current.saveField(makeSaveArgs({ block: "benefits", field: "benefits_count", value: 5 }))
      })
    ).rejects.toThrow()
  })

  it("saveField throws for unknown block", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })

    await expect(
      act(async () => {
        await result.current.saveField(makeSaveArgs({ block: "ghost_block", field: "x", value: "y" }))
      })
    ).rejects.toThrow()
  })

  it("saveField throws on non-ok response", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(false, { detail: "Unauthorized" }, 401))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await expect(
      act(async () => {
        await result.current.saveField(makeSaveArgs())
      })
    ).rejects.toThrow()
    vi.unstubAllGlobals()
  })

  it("dispatches lia:settings-updated on successful save", async () => {
    const { Wrapper } = makeWrapper()
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200)))
    const dispatchedTypes: string[] = []
    window.addEventListener("lia:settings-updated", (e) => dispatchedTypes.push(e.type))

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs())
    })

    expect(dispatchedTypes).toContain("lia:settings-updated")
    vi.unstubAllGlobals()
  })

  it("allowed_hours format 'HH:MM - HH:MM' is parsed correctly", async () => {
    const { Wrapper } = makeWrapper()
    const mockFetch = vi.fn().mockResolvedValue(makeFetchResponse(true, {}, 200))
    vi.stubGlobal("fetch", mockFetch)

    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })
    await act(async () => {
      await result.current.saveField(makeSaveArgs({
        block: "policy",
        field: "allowed_hours",
        value: "09:00 - 18:00",
      }))
    })

    const body = JSON.parse((mockFetch.mock.calls[0][1] as RequestInit).body as string)
    expect(body.data.allowed_hours).toEqual({ start: "09:00", end: "18:00" })
    vi.unstubAllGlobals()
  })

  it("allowed_hours invalid format throws", async () => {
    const { Wrapper } = makeWrapper()
    const { result } = renderHook(() => useFieldSave(), { wrapper: Wrapper })

    await expect(
      act(async () => {
        await result.current.saveField(makeSaveArgs({
          block: "policy",
          field: "allowed_hours",
          value: "invalid format",
        }))
      })
    ).rejects.toThrow()
  })
})
