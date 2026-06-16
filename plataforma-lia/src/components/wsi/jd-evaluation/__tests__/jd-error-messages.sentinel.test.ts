/**
 * Sentinela canonical-fix Task #1165 (Bugs A + B).
 *
 * Garante que mensagens de erro do fluxo JD nunca regridem para o estado
 * antigo onde:
 *   - Bug A: qualquer não-ok no /wsi/jd-evaluate virava setEvaluation(null) mudo.
 *   - Bug B: qualquer 422 do /jd/generate virava "Faltam dados na vaga..."
 *            mascarando FairnessGuard/Pydantic.
 *
 * Sem fallback silencioso: cada bucket retorna mensagem específica em PT-BR.
 */
import { describe, expect, it } from "vitest"
import {
  extractBackendMessage,
  mapJDGenerateErrorMessage,
  mapJDEvaluationErrorMessage,
} from "../jdErrorMessages"

describe("extractBackendMessage", () => {
  it("lê detail.message (formato FairnessGuard)", () => {
    expect(
      extractBackendMessage({
        detail: { message: "JD viola política DEI: tom excludente." },
      })
    ).toBe("JD viola política DEI: tom excludente.")
  })

  it("lê detail como string (legado)", () => {
    expect(extractBackendMessage({ detail: "company_id ausente" })).toBe(
      "company_id ausente"
    )
  })

  it("lê primeiro msg de array Pydantic", () => {
    expect(
      extractBackendMessage({
        detail: [{ loc: ["body", "job_title"], msg: "field required", type: "missing" }],
      })
    ).toBe("field required")
  })

  it("retorna null para payload vazio/null", () => {
    expect(extractBackendMessage(null)).toBeNull()
    expect(extractBackendMessage({})).toBeNull()
    expect(extractBackendMessage({ detail: [] })).toBeNull()
  })
})

describe("mapJDGenerateErrorMessage (Bug B)", () => {
  it("401/403 retorna mensagem de sessão expirada", () => {
    expect(mapJDGenerateErrorMessage(401, null)).toMatch(/sessão expirou/i)
    expect(mapJDGenerateErrorMessage(403, null)).toMatch(/sessão expirou/i)
  })

  it("422 sem detail cai no fallback 'faltam dados'", () => {
    expect(mapJDGenerateErrorMessage(422, {})).toMatch(/faltam dados/i)
  })

  it("422 COM detail.message preserva mensagem do backend (FairnessGuard)", () => {
    const msg = mapJDGenerateErrorMessage(422, {
      detail: { message: "JD contém linguagem excludente — revise antes de gerar." },
    })
    expect(msg).toBe("JD contém linguagem excludente — revise antes de gerar.")
    expect(msg).not.toMatch(/faltam dados/i)
  })

  it("422 com Pydantic array preserva primeiro msg", () => {
    expect(
      mapJDGenerateErrorMessage(422, {
        detail: [{ msg: "responsibilities: ensure this value has at least 1 items" }],
      })
    ).toMatch(/ensure this value/i)
  })

  it("5xx retorna mensagem de servidor (não 'faltam dados')", () => {
    const msg = mapJDGenerateErrorMessage(500, null)
    expect(msg).toMatch(/servidor/i)
    expect(msg).not.toMatch(/faltam dados/i)
  })

  it("outros 4xx retornam fallback genérico (não 'faltam dados')", () => {
    expect(mapJDGenerateErrorMessage(400, null)).not.toMatch(/faltam dados/i)
  })
})

describe("mapJDEvaluationErrorMessage (Bug A)", () => {
  it("network retorna falha de conexão", () => {
    expect(mapJDEvaluationErrorMessage("network")).toMatch(/conexão/i)
  })

  it("401/403 retorna mensagem de sessão expirada", () => {
    expect(mapJDEvaluationErrorMessage(401)).toMatch(/sessão expirou/i)
    expect(mapJDEvaluationErrorMessage(403)).toMatch(/sessão expirou/i)
  })

  it("5xx retorna mensagem de servidor", () => {
    expect(mapJDEvaluationErrorMessage(500)).toMatch(/servidor/i)
    expect(mapJDEvaluationErrorMessage(503)).toMatch(/servidor/i)
  })

  it("outros 4xx retornam fallback específico (não vazio)", () => {
    expect(mapJDEvaluationErrorMessage(400)).toMatch(/não foi possível avaliar/i)
  })

  it("nenhum bucket retorna string vazia", () => {
    for (const s of [400, 401, 403, 404, 429, 500, 502, 503] as const) {
      expect(mapJDEvaluationErrorMessage(s).length).toBeGreaterThan(0)
    }
    expect(mapJDEvaluationErrorMessage("network").length).toBeGreaterThan(0)
  })
})
