import { describe, it, expect } from "vitest"
import { dedupeSkills } from "./ProfileSkillsMapCard"

// Pina P1-9: o Mapa de Skills concatenava candidate.skills + technical_skills
// (os produtores espelham o MESMO array nos dois campos) -> toda skill aparecia
// 2x ("Kafka Go Kafka Go"). dedupeSkills remove duplicatas case-insensitive,
// preservando a primeira grafia, e ignora vazios/undefined.
describe("dedupeSkills (P1-9 — Mapa de Skills sem duplicatas)", () => {
  it("remove duplicatas entre os dois arrays (case-insensitive, 1a grafia)", () => {
    expect(dedupeSkills(["Kafka", "Go"], ["Kafka", "Go", "kafka"])).toEqual(["Kafka", "Go"])
  })

  it("preserva ordem e grafia original; trim", () => {
    expect(dedupeSkills(["React", " TypeScript "], ["typescript", "React"])).toEqual(["React", "TypeScript"])
  })

  it("tolera undefined/vazios", () => {
    expect(dedupeSkills(undefined, ["AWS", "", "  ", "AWS"])).toEqual(["AWS"])
    expect(dedupeSkills(undefined, undefined)).toEqual([])
  })
})
