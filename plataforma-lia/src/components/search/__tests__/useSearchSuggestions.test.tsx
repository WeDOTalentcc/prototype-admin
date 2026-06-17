import { renderHook, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { useSearchSuggestions } from "../hooks/useSearchSuggestions"

describe("useSearchSuggestions — chips dinâmicos de busca", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("(a) retorna chips dinâmicos quando há histórico de buscas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        suggestions: [
          { text: "Backend Sênior Node.js Fintech", category: "recent" },
          { text: "React Developer Pleno Remoto", category: "recent" },
          { text: "Product Manager B2B", category: "recent" },
        ],
      }),
    } as unknown as Response)

    const { result } = renderHook(() => useSearchSuggestions())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.suggestions).toEqual([
      "Backend Sênior Node.js Fintech",
      "React Developer Pleno Remoto",
      "Product Manager B2B",
    ])
    expect(fetch).toHaveBeenCalledWith("/api/backend-proxy/search/autocomplete/recent")
  })

  it("(b) retorna [] quando histórico vazio → componente usa fallback estático", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ suggestions: [] }),
    } as unknown as Response)

    const { result } = renderHook(() => useSearchSuggestions())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.suggestions).toHaveLength(0)
  })

  it("retorna [] em erro de rede — graceful fallback para chips estáticos", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"))

    const { result } = renderHook(() => useSearchSuggestions())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.suggestions).toHaveLength(0)
  })

  it("retorna [] quando endpoint retorna ok=false", async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 401,
    } as Response)

    const { result } = renderHook(() => useSearchSuggestions())

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false)
    })

    expect(result.current.suggestions).toHaveLength(0)
  })
})
