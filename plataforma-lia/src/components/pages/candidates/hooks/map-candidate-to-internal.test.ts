import { describe, it, expect } from "vitest"
import { mapCandidateToInternal } from "./useCandidatesExecuteSearch"

// Pina P1-2: o mapper fabricava Match 75 quando o backend nao trazia score
// (c.score || 75) e ainda tinha um ramo morto match_score*25 (campo inexistente
// no DTO). O score real (0-100) deve passar intacto; sem score -> 0 (a celula
// renderMatchScoreCell ja exibe "—" para 0). Nunca 75 fabricado.
describe("mapCandidateToInternal — score honesto (P1-2)", () => {
  it("usa o score real (0-100) sem multiplicar por 25", () => {
    expect(mapCandidateToInternal({ id: "x", name: "X", score: 87 }).score).toBe(87)
  })

  it("sem score -> 0 (UI mostra —), nunca 75 fabricado", () => {
    expect(mapCandidateToInternal({ id: "x", name: "X" }).score).toBe(0)
  })

  it("score 0 permanece 0 (nao vira 75)", () => {
    expect(mapCandidateToInternal({ id: "x", name: "X", score: 0 }).score).toBe(0)
  })
})
