import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { createCellRenderer, type CellRendererDeps } from "@/components/pages/candidates/CandidateTableCellRenderer"
import type { Candidate } from "@/components/pages/candidates/types"

// Componente chama useSearchFingerprint() no render; mock evita exigir Provider.
vi.mock("@/components/search/SearchFingerprintContext", () => ({
  useSearchFingerprint: () => undefined,
}))

// Pina o bug do Funil de Talentos (2026-06-06): like/dislike "nao funciona".
// SearchFeedbackButtons emite onFeedbackChange(candidateId, feedback) [2 args],
// mas o cell renderer plugava o handler onSearchFeedbackChange [3 args:
// id, name, feedback] via "as any". O 'like'/'dislike' caia no slot
// candidateName e o feedback real chegava undefined -> o store gravava
// undefined -> hasFeedback=false -> a selecao nunca persistia (some no hover).
describe("CandidateTableCellRenderer — wiring do feedback (like/dislike)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.clearAllMocks()
  })

  function buildDeps(
    onSearchFeedbackChange: CellRendererDeps["onSearchFeedbackChange"]
  ): CellRendererDeps {
    return {
      searchFeedbacks: {},
      revealedContacts: {} as CellRendererDeps["revealedContacts"],
      searchQuery: "",
      viewedCandidateIds: new Set<string>(),
      expandedRows: new Set<string>(),
      onSearchFeedbackChange,
      onRevealContact: vi.fn(),
      onToggleExpandedRow: vi.fn(),
    }
  }

  const candidate = { id: "c1", candidateId: "c1", name: "Maria Teste" } as unknown as Candidate

  it("clicar Aprovar repassa (candidateId, candidateName, 'like') ao handler de 3 args", async () => {
    const onSearchFeedbackChange = vi.fn()
    const renderCell = createCellRenderer(buildDeps(onSearchFeedbackChange))
    render(<>{renderCell(candidate, "feedback")}</>)

    fireEvent.click(screen.getByTitle("Aprovar candidato"))

    await waitFor(() => expect(onSearchFeedbackChange).toHaveBeenCalled())
    expect(onSearchFeedbackChange).toHaveBeenCalledWith("c1", "Maria Teste", "like")
  })

  it("clicar Reprovar repassa (candidateId, candidateName, 'dislike') ao handler de 3 args", async () => {
    const onSearchFeedbackChange = vi.fn()
    const renderCell = createCellRenderer(buildDeps(onSearchFeedbackChange))
    render(<>{renderCell(candidate, "feedback")}</>)

    fireEvent.click(screen.getByTitle("Reprovar candidato"))

    await waitFor(() => expect(onSearchFeedbackChange).toHaveBeenCalled())
    expect(onSearchFeedbackChange).toHaveBeenCalledWith("c1", "Maria Teste", "dislike")
  })
})
