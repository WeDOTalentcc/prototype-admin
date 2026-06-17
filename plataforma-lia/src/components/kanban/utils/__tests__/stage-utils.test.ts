/**
 * Testes Unitários — stage-utils.ts
 * Camada 2 (Unitário FE — Vitest, sem DOM)
 *
 * Cobre:
 * - buildSubStatusMap: construção do mapa stage → sub-statuses
 * - enrichStagesWithSubStatuses: enriquecimento de DynamicStage com sub-statuses do DB
 * - Preferência por sub-statuses do DB sobre fallback estático
 * - Isolamento: estágios sem entrada no mapa não são alterados
 * - Edge cases: mapa vazio, stages sem subStatuses, listas vazias
 */
import { describe, it, expect } from "vitest"
import {
  buildSubStatusMap,
  enrichStagesWithSubStatuses,
  createStageSlug,
  mapInterviewStagesToKanban,
  organizeCandidatesByDynamicStages,
  isTransitionAllowed,
  getActiveStages,
  getFinalStages,
  createInitialCandidatesData,
} from "../stage-utils"
import type { DynamicStage, KanbanCandidate } from "../../types"

// ── Fixtures ─────────────────────────────────────────────────────────────────

const mockSubStatusOption = (name: string, display_name: string, is_default = false) => ({
  name,
  display_name,
  is_default,
  is_waiting: false,
})

const mockDynamicStage = (id: string, overrides: Partial<DynamicStage> = {}): DynamicStage => ({
  id,
  name: id,
  displayName: id,
  order: 1,
  color: "#000000",
  stageType: "active",
  ...overrides,
})

// ── buildSubStatusMap ─────────────────────────────────────────────────────────

describe("buildSubStatusMap", () => {
  it("retorna mapa vazio quando pipeline é array vazio", () => {
    const result = buildSubStatusMap([])
    expect(result).toEqual({})
  })

  it("retorna mapa vazio quando nenhum estágio tem sub_statuses", () => {
    const result = buildSubStatusMap([
      { name: "screening" },
      { name: "rejected", sub_statuses: [] },
    ])
    expect(result).toEqual({})
  })

  it("mapeia corretamente sub_statuses para o nome do estágio", () => {
    const result = buildSubStatusMap([
      {
        name: "rejected",
        sub_statuses: [
          mockSubStatusOption("another_candidate_selected", "Outro Candidato Selecionado", true),
          mockSubStatusOption("lacking_experience", "Falta de Experiência"),
        ],
      },
    ])
    expect(result["rejected"]).toHaveLength(2)
    expect(result["rejected"][0].name).toBe("another_candidate_selected")
    expect(result["rejected"][1].name).toBe("lacking_experience")
  })

  it("inclui múltiplos estágios no mapa", () => {
    const result = buildSubStatusMap([
      {
        name: "rejected",
        sub_statuses: [mockSubStatusOption("withdrew", "Desistiu")],
      },
      {
        name: "offer_declined",
        sub_statuses: [mockSubStatusOption("accepted_other_offer", "Aceitou Outra Proposta", true)],
      },
    ])
    expect("rejected" in result).toBe(true)
    expect("offer_declined" in result).toBe(true)
  })

  it("ignora estágios sem sub_statuses (undefined)", () => {
    const result = buildSubStatusMap([
      { name: "screening" }, // sem sub_statuses
      {
        name: "rejected",
        sub_statuses: [mockSubStatusOption("withdrew", "Desistiu")],
      },
    ])
    expect("screening" in result).toBe(false)
    expect("rejected" in result).toBe(true)
  })
})

// ── enrichStagesWithSubStatuses ───────────────────────────────────────────────

describe("enrichStagesWithSubStatuses", () => {
  it("retorna stages intocados quando mapa é vazio", () => {
    const stages = [mockDynamicStage("screening"), mockDynamicStage("rejected")]
    const result = enrichStagesWithSubStatuses(stages, {})
    expect(result).toEqual(stages)
  })

  it("enriquece estágio com sub-statuses do mapa", () => {
    const stages = [mockDynamicStage("rejected")]
    const map = {
      rejected: [
        mockSubStatusOption("another_candidate_selected", "Outro Candidato Selecionado", true),
        mockSubStatusOption("lacking_experience", "Falta de Experiência"),
      ],
    }
    const result = enrichStagesWithSubStatuses(stages, map)
    expect(result[0].subStatuses).toHaveLength(2)
    expect(result[0].subStatuses![0].name).toBe("another_candidate_selected")
  })

  it("não altera estágios que não estão no mapa", () => {
    const stages = [
      mockDynamicStage("screening"),
      mockDynamicStage("rejected"),
    ]
    const map = {
      rejected: [mockSubStatusOption("withdrew", "Desistiu")],
    }
    const result = enrichStagesWithSubStatuses(stages, map)
    // screening não está no mapa — deve preservar subStatuses existentes (undefined ou [])
    expect(result[0].subStatuses).toBeUndefined()
    expect(result[1].subStatuses).toHaveLength(1)
  })

  it("preserva subStatuses existentes quando estágio não está no mapa", () => {
    const existing = [mockSubStatusOption("cv_received", "CV Recebido", true)]
    const stages = [mockDynamicStage("screening", { subStatuses: existing })]
    const map = {} // mapa vazio — não deve sobrescrever
    const result = enrichStagesWithSubStatuses(stages, map)
    expect(result[0].subStatuses).toEqual(existing)
  })

  it("sobrescreve subStatuses existentes quando estágio está no mapa", () => {
    const old = [mockSubStatusOption("old_sub", "Antigo")]
    const stages = [mockDynamicStage("rejected", { subStatuses: old })]
    const fresh = [mockSubStatusOption("new_sub", "Novo", true)]
    const map = { rejected: fresh }

    const result = enrichStagesWithSubStatuses(stages, map)
    expect(result[0].subStatuses).toHaveLength(1)
    expect(result[0].subStatuses![0].name).toBe("new_sub")
  })

  it("mantém outras propriedades do DynamicStage intactas", () => {
    const stage = mockDynamicStage("rejected", {
      displayName: "Reprovado",
      color: "#FF0000",
      actionBehavior: "conclusion_rejected",
    })
    const map = {
      rejected: [mockSubStatusOption("withdrew", "Desistiu")],
    }
    const result = enrichStagesWithSubStatuses([stage], map)
    expect(result[0].displayName).toBe("Reprovado")
    expect(result[0].color).toBe("#FF0000")
    expect(result[0].actionBehavior).toBe("conclusion_rejected")
  })

  it("retorna nova array (imutabilidade) sem alterar original", () => {
    const stages = [mockDynamicStage("rejected")]
    const map = {
      rejected: [mockSubStatusOption("withdrew", "Desistiu")],
    }
    const result = enrichStagesWithSubStatuses(stages, map)
    expect(result).not.toBe(stages)
    expect(stages[0].subStatuses).toBeUndefined() // original não alterado
  })
})

// ── createStageSlug ───────────────────────────────────────────────────────────

describe("createStageSlug", () => {
  it("converts display name to lowercase slug", () => {
    expect(createStageSlug("Entrevista RH")).toBe("entrevista_rh")
  })

  it("removes accents", () => {
    expect(createStageSlug("Proposta Técnica")).toBe("proposta_tecnica")
  })

  it("strips leading/trailing underscores from whitespace", () => {
    expect(createStageSlug("  Test  ")).toBe("test")
  })
})

// ── mapInterviewStagesToKanban ────────────────────────────────────────────────

describe("mapInterviewStagesToKanban", () => {
  it("returns fallback stages when no interview stages provided", () => {
    const result = mapInterviewStagesToKanban(undefined)
    expect(result.length).toBeGreaterThan(0)
  })

  it("maps custom interview stages and infers action behavior", () => {
    const custom = [
      { stageName: "Entrevista Técnica", order: 1, type: "interview" },
      { stageName: "Teste Prático", order: 2, type: "test" },
    ]
    const result = mapInterviewStagesToKanban(custom)
    const techInterview = result.find(s => s.id === "entrevista_tecnica")
    expect(techInterview?.actionBehavior).toBe("scheduling")
    const practicalTest = result.find(s => s.id === "teste_pratico")
    expect(practicalTest?.actionBehavior).toBe("evaluation")
  })

  it("includes system initial and final stages around custom stages", () => {
    const custom = [{ stageName: "Custom Stage", order: 1, type: "interview" }]
    const result = mapInterviewStagesToKanban(custom)
    expect(result.some(s => s.isInitial)).toBe(true)
    expect(result.some(s => s.isFinal)).toBe(true)
  })
})

// ── organizeCandidatesByDynamicStages ─────────────────────────────────────────

describe("organizeCandidatesByDynamicStages", () => {
  const stages: DynamicStage[] = [
    mockDynamicStage("sourcing", { isInitial: true }),
    mockDynamicStage("entrevista_rh", { displayName: "Entrevista RH" }),
    mockDynamicStage("hired", { stageType: "final", isFinal: true }),
  ]

  it("places candidates into correct stages", () => {
    const candidates = [
      { id: "1", name: "Ana", stage: "sourcing" },
      { id: "2", name: "Bruno", stage: "entrevista_rh" },
    ] as KanbanCandidate[]
    const result = organizeCandidatesByDynamicStages(candidates, stages)
    expect(result["sourcing"]).toHaveLength(1)
    expect(result["entrevista_rh"]).toHaveLength(1)
    expect(result["hired"]).toHaveLength(0)
  })

  it("falls back to sourcing for unknown stages", () => {
    const candidates = [
      { id: "1", name: "Ana", stage: "nonexistent" },
    ] as KanbanCandidate[]
    const result = organizeCandidatesByDynamicStages(candidates, stages)
    expect(result["sourcing"]).toHaveLength(1)
  })

  it("initializes all stages with empty arrays", () => {
    const result = organizeCandidatesByDynamicStages([], stages)
    expect(Object.keys(result)).toHaveLength(3)
    expect(result["sourcing"]).toEqual([])
  })
})

// ── isTransitionAllowed ──────────────────────────────────────────────────────

describe("isTransitionAllowed", () => {
  const from = mockDynamicStage("sourcing")
  const to = mockDynamicStage("entrevista_rh")

  it("allows all transitions when no restrictions", () => {
    expect(isTransitionAllowed(from, to)).toBe(true)
  })

  it("allows transition when target is in allowed list", () => {
    expect(isTransitionAllowed(from, to, ["entrevista_rh"])).toBe(true)
  })

  it("blocks transition when target is not in allowed list", () => {
    expect(isTransitionAllowed(from, to, ["hired"])).toBe(false)
  })
})

// ── getActiveStages / getFinalStages ─────────────────────────────────────────

describe("getActiveStages / getFinalStages", () => {
  const stages = [
    mockDynamicStage("sourcing"),
    mockDynamicStage("hired", { stageType: "final" }),
    mockDynamicStage("rejected", { stageType: "final" }),
  ]

  it("getActiveStages returns only active stages", () => {
    expect(getActiveStages(stages)).toHaveLength(1)
    expect(getActiveStages(stages)[0].id).toBe("sourcing")
  })

  it("getFinalStages returns only final stages", () => {
    expect(getFinalStages(stages)).toHaveLength(2)
  })
})

// ── createInitialCandidatesData ──────────────────────────────────────────────

describe("createInitialCandidatesData", () => {
  it("creates empty arrays for each stage", () => {
    const stages = [mockDynamicStage("a"), mockDynamicStage("b")]
    const result = createInitialCandidatesData(stages)
    expect(Object.keys(result)).toEqual(["a", "b"])
    expect(result["a"]).toEqual([])
  })
})

// ── Integração: buildSubStatusMap → enrichStagesWithSubStatuses ───────────────

describe("buildSubStatusMap + enrichStagesWithSubStatuses (integração)", () => {
  it("pipeline completo → stages enriquecidas com sub-statuses do DB", () => {
    const pipeline = [
      {
        name: "rejected",
        sub_statuses: [
          mockSubStatusOption("another_candidate_selected", "Outro Candidato Selecionado", true),
          mockSubStatusOption("cultural_mismatch", "Não Aprovado Culturalmente"),
          mockSubStatusOption("salary_above_budget", "Expectativa Salarial Acima do Budget"),
        ],
      },
      {
        name: "offer_declined",
        sub_statuses: [
          mockSubStatusOption("accepted_other_offer", "Aceitou Outra Proposta", true),
          mockSubStatusOption("health_issues", "Questões de Saúde"),
        ],
      },
    ]

    const stages = [
      mockDynamicStage("screening"),
      mockDynamicStage("rejected"),
      mockDynamicStage("offer_declined"),
      mockDynamicStage("hired"),
    ]

    const map = buildSubStatusMap(pipeline)
    const enriched = enrichStagesWithSubStatuses(stages, map)

    // screening e hired não estão no pipeline mock — sem subStatuses
    expect(enriched.find(s => s.id === "screening")?.subStatuses).toBeUndefined()
    expect(enriched.find(s => s.id === "hired")?.subStatuses).toBeUndefined()

    // rejected enriquecido com 3 sub-statuses
    const rejected = enriched.find(s => s.id === "rejected")
    expect(rejected?.subStatuses).toHaveLength(3)
    expect(rejected?.subStatuses![0].is_default).toBe(true)

    // offer_declined enriquecido com 2 sub-statuses
    const offerDeclined = enriched.find(s => s.id === "offer_declined")
    expect(offerDeclined?.subStatuses).toHaveLength(2)
  })
})
