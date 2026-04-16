/**
 * Testes — useCandidatesList + useCandidatesListMapped (F3 / H.2b)
 *
 * Camada 2 (Unitário FE — Vitest + @testing-library/react)
 *
 * Cobre:
 * - Estado inicial correto (loading true → false, candidates [])
 * - Atualização de filtro desencadeia nova busca
 * - Busca textual usa debounce (300ms)
 * - Erro de rede → error state preenchido, candidates []
 * - Paginação: goToPage atualiza currentPage e rebusca
 * - Filtro de status: immediate (sem debounce)
 * - useCandidatesListMapped aplica transform CandidateLocal → Candidate
 */
import { renderHook, act, waitFor } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"
import { useCandidatesList } from "../candidates/use-candidates-list"
import { useCandidatesListMapped } from "../candidates/use-candidates-list-mapped"

// ── Mock do liaApi ──────────────────────────────────────────────────────────
const mockGetCandidates = vi.fn()

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    getCandidates: (...args: unknown[]) => mockGetCandidates(...args),
  },
}))

const MOCK_RESPONSE = {
  candidates: [
    { id: "c1", name: "Ana Lima", current_title: "Dev Sênior", email: "ana@co.com" },
    { id: "c2", name: "Bruno Melo", current_title: "DevOps", email: "bruno@co.com" },
  ],
  total: 2,
  page: 1,
  per_page: 20,
}

// ── Setup / Teardown ────────────────────────────────────────────────────────
beforeEach(() => {
  // shouldAdvanceTime: true — real wall-clock still ticks so waitFor polling
  // works, while vi controls setTimeout/setInterval for debounce assertions.
  vi.useFakeTimers({ shouldAdvanceTime: true })
  mockGetCandidates.mockResolvedValue(MOCK_RESPONSE)
})

afterEach(() => {
  vi.useRealTimers()
  vi.clearAllMocks()
})

// ── Testes ──────────────────────────────────────────────────────────────────
describe("useCandidatesList", () => {
  it("inicia com loading=true e depois preenche candidates", async () => {
    const { result } = renderHook(() => useCandidatesList())

    expect(result.current.loading).toBe(true)

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.candidates).toHaveLength(2)
    expect(result.current.total).toBe(2)
    expect(result.current.error).toBeNull()
  })

  it("estado inicial: currentPage=1, totalPages=1", async () => {
    const { result } = renderHook(() => useCandidatesList())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.currentPage).toBe(1)
    expect(result.current.totalPages).toBe(1)
  })

  it("updateFilter('search') aplica debounce de 300ms", async () => {
    const { result } = renderHook(() => useCandidatesList())
    await waitFor(() => expect(result.current.loading).toBe(false))

    const callsBefore = mockGetCandidates.mock.calls.length

    act(() => {
      result.current.updateFilter("search", "dev")
    })

    // Ainda não chamou (aguarda debounce)
    expect(mockGetCandidates.mock.calls.length).toBe(callsBefore)

    // Avança o timer
    await act(async () => {
      vi.advanceTimersByTime(300)
    })

    await waitFor(() =>
      expect(mockGetCandidates.mock.calls.length).toBeGreaterThan(callsBefore)
    )

    const lastCall = mockGetCandidates.mock.calls.at(-1)![0]
    expect(lastCall.search).toBe("dev")
    expect(lastCall.offset).toBe(0) // reset para página 1
  })

  it("updateFilter('status') é imediato (sem debounce)", async () => {
    const { result } = renderHook(() => useCandidatesList())
    await waitFor(() => expect(result.current.loading).toBe(false))

    const callsBefore = mockGetCandidates.mock.calls.length

    act(() => {
      result.current.updateFilter("status", "Aprovado")
    })

    // Sem avançar timer — deve ter chamado imediatamente
    await act(async () => {
      vi.advanceTimersByTime(0)
    })

    await waitFor(() =>
      expect(mockGetCandidates.mock.calls.length).toBeGreaterThan(callsBefore)
    )

    const lastCall = mockGetCandidates.mock.calls.at(-1)![0]
    expect(lastCall.status).toBe("Aprovado")
  })

  it("erro de rede → error preenchido, candidates vazio, loading false", async () => {
    mockGetCandidates.mockRejectedValueOnce(new Error("Network error"))

    const { result } = renderHook(() => useCandidatesList())

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).not.toBeNull()
    expect(result.current.candidates).toHaveLength(0)
    expect(result.current.errorKind).toBe("network")
  })

  // Task #293 — classificação de errorKind por HTTP status.
  it.each([
    [401, "unauthorized"],
    [403, "forbidden"],
    [500, "server"],
    [503, "server"],
  ] as const)(
    "HTTP %i → errorKind=%s",
    async (status, expectedKind) => {
      const err = Object.assign(new Error(`HTTP ${status}`), { status })
      mockGetCandidates.mockRejectedValueOnce(err)

      const { result } = renderHook(() => useCandidatesList())
      await waitFor(() => expect(result.current.loading).toBe(false))

      expect(result.current.errorKind).toBe(expectedKind)
      expect(result.current.candidates).toHaveLength(0)
    }
  )

  it("goToPage(2) atualiza currentPage e rebusca com offset correto", async () => {
    mockGetCandidates.mockResolvedValue({
      ...MOCK_RESPONSE,
      total: 50, // 3 páginas
    })

    const { result } = renderHook(() => useCandidatesList())
    await waitFor(() => expect(result.current.loading).toBe(false))

    const callsBefore = mockGetCandidates.mock.calls.length

    act(() => {
      result.current.goToPage(2)
    })

    await waitFor(() =>
      expect(mockGetCandidates.mock.calls.length).toBeGreaterThan(callsBefore)
    )

    const lastCall = mockGetCandidates.mock.calls.at(-1)![0]
    expect(lastCall.offset).toBe(20) // página 2 = offset 20
    expect(result.current.currentPage).toBe(2)
  })

  it("setFilters reseta currentPage para 1", async () => {
    mockGetCandidates.mockResolvedValue({ ...MOCK_RESPONSE, total: 50 })
    const { result } = renderHook(() => useCandidatesList())
    await waitFor(() => expect(result.current.loading).toBe(false))

    // Vai para página 2
    act(() => { result.current.goToPage(2) })
    await waitFor(() => expect(result.current.currentPage).toBe(2))

    // setFilters deve resetar para 1
    act(() => { result.current.setFilters({ seniority: "Sênior" }) })

    await act(async () => { vi.advanceTimersByTime(0) })
    await waitFor(() => expect(result.current.currentPage).toBe(1))
  })

  it("refresh rebusca sem alterar filtros ou página", async () => {
    const { result } = renderHook(() => useCandidatesList())
    await waitFor(() => expect(result.current.loading).toBe(false))

    const callsBefore = mockGetCandidates.mock.calls.length

    act(() => { result.current.refresh() })

    await waitFor(() =>
      expect(mockGetCandidates.mock.calls.length).toBeGreaterThan(callsBefore)
    )
  })
})

// ── useCandidatesListMapped (F3) ─────────────────────────────────────────────

describe("F3 — useCandidatesListMapped", () => {
  it("retorna candidates transformados com todos os campos do hook", async () => {
    const { result } = renderHook(() => useCandidatesListMapped())
    await waitFor(() => expect(result.current.loading).toBe(false))

    // Expõe os mesmos campos do useCandidatesList
    expect(Array.isArray(result.current.candidates)).toBe(true)
    expect(typeof result.current.total).toBe("number")
    expect(typeof result.current.currentPage).toBe("number")
    expect(typeof result.current.totalPages).toBe("number")
    expect(typeof result.current.perPage).toBe("number")
    expect(typeof result.current.refresh).toBe("function")
    expect(typeof result.current.goToPage).toBe("function")
  })

  it("candidates vêm do mesmo mock que useCandidatesList", async () => {
    const { result } = renderHook(() => useCandidatesListMapped())
    await waitFor(() => expect(result.current.loading).toBe(false))

    // MOCK_RESPONSE tem 2 candidates
    expect(result.current.candidates).toHaveLength(2)
    expect(result.current.total).toBe(2)
  })
})
