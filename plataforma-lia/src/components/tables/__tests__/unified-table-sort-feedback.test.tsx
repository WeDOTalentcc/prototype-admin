import { describe, it, expect } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { UnifiedCandidateTable } from "@/components/tables/unified-candidate-table"

// Pina P1-4 (coluna "Match" nao ordenava: id 'match_score' caia no else ->
// undefined -> no-op) e P1-5 (a tabela re-ordenava por sortConfig e descartava
// a ordem do produtor — like->topo / dislike->fundo).

const columns = [
  { id: "name", label: "Candidato", visible: true, order: 0 },
  { id: "match_score", label: "Match", visible: true, order: 1, sortable: true },
]

function renderCell(c: Record<string, unknown>, colId: string) {
  if (colId === "name") return <span data-testid="cell-name">{String(c.name)}</span>
  if (colId === "match_score") return <span>{String(c.score)}</span>
  return null
}

describe("UnifiedCandidateTable — ordenacao Match + preservacao da ordem do produtor", () => {
  it("clicar no header 'Match' ordena por score desc (P1-4)", () => {
    const candidates = [
      { id: "a", name: "Alice Low", score: 30 },
      { id: "b", name: "Bob High", score: 90 },
    ]
    render(
      <UnifiedCandidateTable
        candidates={candidates as never}
        columns={columns as never}
        renderCustomCell={renderCell as never}
      />
    )
    fireEvent.click(screen.getByText("Match"))
    const names = screen.getAllByTestId("cell-name").map((e) => e.textContent)
    // Sem o fix: 'match_score' -> undefined -> no-op -> ordem de entrada (Alice, Bob).
    // Com o fix: ordena por score desc -> Bob(90) primeiro.
    expect(names[0]).toBe("Bob High")
  })

  it("sem sortConfig, preserva a ordem de entrada do produtor (like->topo/dislike->fundo) (P1-5)", () => {
    // Ordem do produtor: like (topo), neutro, dislike (fundo)
    const candidates = [
      { id: "like1", name: "Curtido", score: 10 },
      { id: "neutral1", name: "Neutro", score: 99 },
      { id: "dislike1", name: "Descurtido", score: 50 },
    ]
    render(
      <UnifiedCandidateTable
        candidates={candidates as never}
        columns={columns as never}
        sortConfig={undefined}
        renderCustomCell={renderCell as never}
      />
    )
    const names = screen.getAllByTestId("cell-name").map((e) => e.textContent)
    // Sem sortConfig a tabela NAO pode reordenar — respeita a ordem do produtor.
    expect(names).toEqual(["Curtido", "Neutro", "Descurtido"])
  })
})
