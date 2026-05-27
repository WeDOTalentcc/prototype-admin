// Onda 1 F10 (2026-05-27) — LGPD CSV builder canonical tests.
import { describe, expect, it } from "vitest"
import { buildLgpdTrailCsv } from "../lgpd-csv"
import type { ExecutionReasoningResponse } from "../types"

function makeReasoning(
  overrides: Partial<ExecutionReasoningResponse> = {},
): ExecutionReasoningResponse {
  return {
    execution_id: "exec-1",
    agent_id: "agent-1",
    agent_name: "Catarina",
    started_at: "2026-05-27T12:00:00Z",
    completed_at: "2026-05-27T12:00:05Z",
    model_used: "claude-sonnet-4.7",
    cost_usd: 0.012,
    latency_ms: 5000,
    input_tokens: 800,
    output_tokens: 400,
    reasoning_trace: [],
    data_fields_accessed_summary: [],
    data_fields_NOT_accessed: ["cpf", "raca", "religiao", "genero", "estado_civil"],
    ...overrides,
  }
}

describe("buildLgpdTrailCsv — canonical", () => {
  it("inclui header com colunas canonical", () => {
    const csv = buildLgpdTrailCsv(makeReasoning())
    expect(csv.split("\n")[0]).toBe(
      "step_index,step_type,label,data_fields_accessed,score,matched,timestamp",
    )
  })

  it("serializa step com fields acessados, score, matched e timestamp", () => {
    const csv = buildLgpdTrailCsv(
      makeReasoning({
        reasoning_trace: [
          {
            step_type: "criterion",
            label: "Skills Python",
            score: 0.91,
            matched: true,
            detail: null,
            data_fields_accessed: ["nome", "experiencia"],
            timestamp: "2026-05-27T12:00:01Z",
          },
        ],
      }),
    )
    const rows = csv.split("\n")
    expect(rows[1]).toContain("1,criterion,Skills Python")
    expect(rows[1]).toContain("nome;experiencia")
    expect(rows[1]).toContain("0.91")
    expect(rows[1]).toContain("true")
    expect(rows[1]).toContain("2026-05-27T12:00:01Z")
  })

  it("REGRA LGPD — filtra defense-in-depth campos sensíveis nunca-acessados (no row data)", () => {
    const csv = buildLgpdTrailCsv(
      makeReasoning({
        reasoning_trace: [
          {
            step_type: "action",
            label: "Lendo perfil",
            score: null,
            matched: null,
            detail: null,
            // Simulação anti-pattern — backend deveria garantir, mas
            // o consumer também filtra defense-in-depth.
            data_fields_accessed: ["nome", "cpf", "experiencia", "raca"],
            timestamp: null,
          },
        ],
      }),
    )
    // O ROW (linha de dados) NÃO deve conter cpf/raca:
    const lines = csv.split("\n")
    const dataRow = lines[1] // header é 0
    expect(dataRow).not.toContain("cpf")
    expect(dataRow).not.toContain("raca")
    expect(dataRow).toContain("nome;experiencia")
    // OBS: trailer canonical (linhas com "#") PODE conter os 5 fields LGPD-proibidos
    // de propósito — é o registro declarativo do que NUNCA é acessado.
  })

  it("escapa vírgulas e aspas em label", () => {
    const csv = buildLgpdTrailCsv(
      makeReasoning({
        reasoning_trace: [
          {
            step_type: "thought",
            label: 'Candidato "X", com vírgulas',
            score: null,
            matched: null,
            detail: null,
            data_fields_accessed: [],
            timestamp: null,
          },
        ],
      }),
    )
    // Aspas duplicadas + envoltórias
    expect(csv).toContain('"Candidato ""X"", com vírgulas"')
  })

  it("trailer canonical inclui data_fields_NOT_accessed", () => {
    const csv = buildLgpdTrailCsv(makeReasoning())
    expect(csv).toContain("# data_fields_NOT_accessed")
    expect(csv).toContain("cpf;raca;religiao;genero;estado_civil")
  })
})
