// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"

// toast (sonner) e usado em sucesso/erro; mock evita efeitos colaterais no jsdom.
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

import {
  useCandidatesActions,
  type CandidatesActionsContext,
} from "@/components/pages/candidates/hooks/useCandidatesActions"

const noop = () => {}

function makeCtx(overrides: Partial<CandidatesActionsContext> = {}): CandidatesActionsContext {
  return {
    candidates: [],
    revealedContacts: {},
    setCandidates: vi.fn(),
    activeTab: "search",
    setActiveTab: noop,
    viewingList: null,
    setViewingList: noop,
    candidateListsForModal: [],
    selectedCandidatesForBatch: new Set<string>(),
    setSelectedCandidatesForBatch: vi.fn(),
    isSavingToBase: false,
    setIsSavingToBase: vi.fn(),
    isAddingToList: false,
    setIsAddingToList: noop,
    showAddToListModal: false,
    setShowAddToListModal: noop,
    addToListCandidateIds: [],
    setAddToListCandidateIds: noop,
    addToListCandidateNames: [],
    setAddToListCandidateNames: noop,
    showUnsavedWarningModal: false,
    setShowUnsavedWarningModal: noop,
    pendingTabChange: null,
    setPendingTabChange: noop,
    hasUnsavedPearchCandidates: false,
    unsavedPearchCandidates: [],
    showSearchResults: true,
    setShowSearchResults: noop,
    lastSearchQuery: "dev backend",
    deselectAllCandidates: vi.fn(),
    user: { id: "u1" },
    ...overrides,
  } as CandidatesActionsContext
}

// Pina o fix #5 (handoff Funil de Talentos 2026-06-05): ao salvar candidato
// global na base, o contato REVELADO (revealedContacts[id]) deve entrar no
// payload de import — nao o email/telefone stale do objeto candidato.
describe("useCandidatesActions.handleSaveToLocalBase — contato revelado no payload (#5)", () => {
  let fetchMock: ReturnType<typeof vi.fn>

  beforeEach(() => {
    fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ saved: 1 }) }))
    vi.stubGlobal("fetch", fetchMock)
  })

  it("usa revealedContacts[id].email/phone (nao o stale c.email)", async () => {
    const candidate = {
      id: "p1",
      name: "Ana Global",
      source: "pearch",
      email: "stale@old.com",
      phone: "+550000",
    } as any
    const ctx = makeCtx({
      candidates: [candidate],
      selectedCandidatesForBatch: new Set(["p1"]),
      revealedContacts: { p1: { email: "revealed@real.com", phone: "+5511988887777" } },
    })
    const { result } = renderHook(() => useCandidatesActions(ctx))
    await act(async () => {
      await result.current.handleSaveToLocalBase()
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, opts] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/search/candidates/import")
    const body = JSON.parse((opts as RequestInit).body as string)
    expect(body.candidates[0].pearch_id).toBe("p1")
    expect(body.candidates[0].email).toBe("revealed@real.com")
    expect(body.candidates[0].phone).toBe("+5511988887777")
  })

  it("faz fallback p/ c.email quando nao ha contato revelado", async () => {
    const candidate = { id: "p2", name: "Bruno", source: "pearch", email: "fallback@x.com" } as any
    const ctx = makeCtx({
      candidates: [candidate],
      selectedCandidatesForBatch: new Set(["p2"]),
      revealedContacts: {},
    })
    const { result } = renderHook(() => useCandidatesActions(ctx))
    await act(async () => {
      await result.current.handleSaveToLocalBase()
    })
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string)
    expect(body.candidates[0].email).toBe("fallback@x.com")
  })
})
