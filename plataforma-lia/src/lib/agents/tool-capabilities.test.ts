/**
 * tool-capabilities canonical mapping — redesign 2026-05-30.
 *
 * Garante que tools técnicas viram capacidades plain-language PT e que o resumo
 * agrupa conceitualmente em bullets de alto nível (sem listar IDs crus).
 */
import { describe, expect, it } from "vitest"
import {
  TOOL_CAPABILITY_PT,
  summarizeCapabilities,
  listCapabilities,
} from "./tool-capabilities"

describe("tool-capabilities — mapeamento canonical", () => {
  it("cobre as 16 tools canonical (TOOL_KEYS)", () => {
    const canonical = [
      "search_candidates",
      "list_jobs",
      "get_job_details",
      "get_candidate_details",
      "get_pipeline_summary",
      "search_talent_pool",
      "get_analytics_summary",
      "get_company_culture",
      "get_evaluation_criteria",
      "summarize_context",
      "clarify_request",
      "move_candidate",
      "send_email",
      "update_candidate_field",
      "schedule_interview",
      "create_note",
    ]
    for (const tool of canonical) {
      expect(TOOL_CAPABILITY_PT[tool], `missing capability for ${tool}`).toBeTruthy()
    }
  })

  it("capacidades são PT plain-language (sem underscore/ID cru)", () => {
    for (const phrase of Object.values(TOOL_CAPABILITY_PT)) {
      expect(phrase).not.toContain("_")
      // primeira letra maiúscula (frase, não identificador)
      expect(phrase[0]).toBe(phrase[0].toUpperCase())
    }
  })
})

describe("summarizeCapabilities — bullets de alto nível", () => {
  it("agrupa conceitualmente (find/analyze/act) em bullets distintos", () => {
    const bullets = summarizeCapabilities([
      "search_candidates",
      "get_candidate_details",
      "get_evaluation_criteria",
      "create_note",
    ])
    expect(bullets).toContain("Encontra os candidatos certos para a vaga")
    expect(bullets).toContain("Analisa perfis com base nos seus critérios")
    expect(bullets).toContain("Organiza o funil e mantém os dados em dia")
  })

  it("dedup: várias tools do mesmo grupo viram um único bullet", () => {
    const bullets = summarizeCapabilities([
      "search_candidates",
      "search_talent_pool",
      "list_jobs",
    ])
    // 3 tools, todas grupo "find" → 1 bullet só
    expect(bullets).toEqual(["Encontra os candidatos certos para a vaga"])
  })

  it("limita a 3 bullets por padrão", () => {
    const bullets = summarizeCapabilities([
      "search_candidates", // find
      "get_candidate_details", // analyze
      "move_candidate", // act
      "send_email", // communicate
      "get_pipeline_summary", // report
    ])
    expect(bullets.length).toBeLessThanOrEqual(3)
  })

  it("nunca expõe IDs técnicos crus", () => {
    const bullets = summarizeCapabilities([
      "search_candidates",
      "get_evaluation_criteria",
    ])
    for (const b of bullets) {
      expect(b).not.toContain("_")
    }
  })

  it("lista vazia → array vazio", () => {
    expect(summarizeCapabilities([])).toEqual([])
  })
})

describe("listCapabilities — detalhe individual", () => {
  it("mapeia tools conhecidas e ignora desconhecidas", () => {
    const caps = listCapabilities(["search_candidates", "tool_inexistente"])
    expect(caps).toEqual(["Busca candidatos"])
  })
})
