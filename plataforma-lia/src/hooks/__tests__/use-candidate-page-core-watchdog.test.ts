/**
 * Unit test — useCandidatePageCore watchdog path
 *
 * Layer 2 — Hook (jsdom + fake timers)
 *
 * Covers Task #260 acceptance criterion:
 *   When the initial candidate fetch stalls past 20 s, the candidate-profile
 *   page must leave the spinner and expose
 *   "Tempo limite de carregamento excedido" through `error` so the UI can
 *   render its error/retry state.
 */

import { renderHook, act } from "@testing-library/react"
import { vi, describe, it, expect, beforeEach, afterEach } from "vitest"

// ── Mocks (must be declared before the hook is imported) ────────────────────

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "candidate-123" }),
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
}))

vi.mock("@/hooks/company/use-current-company", () => ({
  useCurrentCompany: () => ({ companyId: "company-1" }),
}))

const getCandidateMock = vi.fn(() => new Promise(() => {}))

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    getCandidate: (...args: unknown[]) => getCandidateMock(...args),
  },
}))

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn(),
  },
}))

import { useCandidatePageCore } from "@/app/[locale]/(dashboard)/funil-de-talentos/candidato/[id]/useCandidatePageCore"

describe("useCandidatePageCore — loading watchdog", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.useFakeTimers()
    // Side-channel fetches (favorite/hide/opinions/etc.) — keep them hung too
    // so they never resolve and disturb the watchdog assertion.
    fetchMock = vi.fn(() => new Promise(() => {}))
    vi.stubGlobal("fetch", fetchMock)
    getCandidateMock.mockImplementation(() => new Promise(() => {}))
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  it("surfaces 'Tempo limite de carregamento excedido' after 20 s when getCandidate hangs", async () => {
    const { result } = renderHook(() => useCandidatePageCore())

    // Allow the initial effect to run.
    await act(async () => {
      await Promise.resolve()
    })

    expect(getCandidateMock).toHaveBeenCalledWith("candidate-123")
    expect(result.current.loading).toBe(true)
    expect(result.current.error).toBeNull()

    // Just before 20 s — still loading, no error yet.
    await act(async () => {
      vi.advanceTimersByTime(19_999)
    })
    expect(result.current.loading).toBe(true)
    expect(result.current.error).toBeNull()

    // Cross the deadline — watchdog fires.
    await act(async () => {
      vi.advanceTimersByTime(1)
    })

    expect(result.current.loading).toBe(false)
    expect(result.current.error).toBe(
      "Tempo limite de carregamento excedido",
    )
  })
})
