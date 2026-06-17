import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import { SearchFeedbackButtons } from "@/components/search/SearchFeedbackButtons"

// Componente chama useSearchFingerprint() no render; mock evita exigir Provider.
vi.mock("@/components/search/SearchFingerprintContext", () => ({
  useSearchFingerprint: () => undefined,
}))

// Pina o fix #4 (handoff Funil de Talentos 2026-06-05): like/dislike refletem
// estado visualmente (ring-2 + scale-110 no selecionado; opacity-40 no oposto).
describe("SearchFeedbackButtons — estado selecionado reflete visualmente (#4)", () => {
  it("like selecionado => botao Aprovar com ring-2 + scale-110; Reprovar esmaecido", () => {
    render(<SearchFeedbackButtons candidateId="c1" initialFeedback="like" />)
    const like = screen.getByTitle("Aprovar candidato")
    const dislike = screen.getByTitle("Reprovar candidato")
    expect(like.className).toContain("ring-2")
    expect(like.className).toContain("scale-110")
    expect(dislike.className).toContain("opacity-40")
    expect(dislike.className).not.toContain("ring-2")
  })

  it("dislike selecionado => botao Reprovar com ring-2 + scale-110; Aprovar esmaecido", () => {
    render(<SearchFeedbackButtons candidateId="c2" initialFeedback="dislike" />)
    const like = screen.getByTitle("Aprovar candidato")
    const dislike = screen.getByTitle("Reprovar candidato")
    expect(dislike.className).toContain("ring-2")
    expect(dislike.className).toContain("scale-110")
    expect(like.className).toContain("opacity-40")
    expect(like.className).not.toContain("ring-2")
  })

  it("sem feedback => nenhum botao com ring-2 (estado neutro)", () => {
    render(<SearchFeedbackButtons candidateId="c3" initialFeedback={null} />)
    expect(screen.getByTitle("Aprovar candidato").className).not.toContain("ring-2")
    expect(screen.getByTitle("Reprovar candidato").className).not.toContain("ring-2")
  })
})
