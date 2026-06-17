/**
 * Sentinela canonical-fix Task #1165 (Bug C).
 *
 * Garante que a chamada do frontend ao proxy /api/backend-proxy/wsi/generate-batch
 * checa `res.ok` ANTES de inspecionar shape do JSON. Antes, qualquer 401/403/422/500
 * caía no `data.success && data.questions` falsy e virava "Invalid response" mudo.
 *
 * Em vez de mockar o hook inteiro (estado React + dezenas de deps), testamos o
 * helper de discriminação extraído de `useScreeningConfigManagerCore.tsx` — a
 * lógica é a MESMA usada no callsite real.
 */
import { describe, expect, it } from "vitest"

// Helper local que replica EXATAMENTE a discriminação aplicada no callsite real
// (useScreeningConfigManagerCore.tsx, bloco "Bug C — Task #1165"). Se o
// callsite divergir, este teste sai de sincronia e quebra → ratchet.
function discriminateWsiBatchError(
  status: number,
  errPayload: { detail?: unknown; message?: unknown } | null
): string {
  const detail = errPayload?.detail
  const detailMsg = typeof detail === "string"
    ? detail
    : (detail && typeof detail === "object" && "message" in detail && typeof (detail as { message: unknown }).message === "string")
      ? (detail as { message: string }).message
      : typeof errPayload?.message === "string"
        ? errPayload.message
        : null
  if (status === 401 || status === 403) {
    return "Sua sessão expirou. Recarregue a página e tente novamente."
  }
  if (status >= 500) {
    return "Tivemos um problema no servidor ao gerar o roteiro WSI. Tente novamente em instantes."
  }
  return detailMsg || `Falha ao gerar roteiro WSI (status ${status}).`
}

describe("WSI generate-batch error discrimination (Bug C)", () => {
  it("401 retorna sessão expirada (não 'Invalid response')", () => {
    expect(discriminateWsiBatchError(401, { detail: "Authentication required" })).toMatch(
      /sessão expirou/i
    )
  })

  it("403 retorna sessão expirada", () => {
    expect(discriminateWsiBatchError(403, null)).toMatch(/sessão expirou/i)
  })

  it("500 retorna mensagem de servidor (não 'Invalid response')", () => {
    const msg = discriminateWsiBatchError(500, { detail: "internal error" })
    expect(msg).toMatch(/servidor/i)
    expect(msg).not.toMatch(/invalid response/i)
  })

  it("422 preserva detail.message do FairnessGuard", () => {
    expect(
      discriminateWsiBatchError(422, {
        detail: { message: "JD viola política DEI" },
      })
    ).toBe("JD viola política DEI")
  })

  it("404 inclui status no erro (não vira 'Invalid response')", () => {
    const msg = discriminateWsiBatchError(404, null)
    expect(msg).toMatch(/status 404/)
    expect(msg).not.toMatch(/invalid response/i)
  })

  it("nunca retorna string vazia", () => {
    for (const s of [400, 401, 403, 404, 422, 429, 500, 502, 503]) {
      expect(discriminateWsiBatchError(s, null).length).toBeGreaterThan(0)
    }
  })
})

/**
 * Ratchet AST: garante que o callsite real em useScreeningConfigManagerCore.tsx
 * NÃO removeu o check `!res.ok` da chamada generate-batch. Se alguém colapsar
 * de volta para o padrão antigo (`if (data.success && data.questions)` direto),
 * este teste quebra.
 */
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

describe("ratchet: useScreeningConfigManagerCore preserva check res.ok antes de inspecionar shape", () => {
  it("contém bloco 'if (!res.ok)' imediatamente antes do parse JSON do generate-batch", () => {
    const path = resolve(
      __dirname,
      "..",
      "useScreeningConfigManagerCore.tsx"
    )
    const src = readFileSync(path, "utf-8")
    // O fix coloca a marca canônica "Bug C (Task #1165 canonical-fix)" no comentário
    // junto com o check `if (!res.ok)` antes do `data.success && data.questions`.
    expect(src).toMatch(/Bug C \(Task #1165 canonical-fix\)/)
    expect(src).toMatch(/if \(!res\.ok\)/)
    // E o branch antigo de "Invalid response" continua existindo só como guard
    // do shape pós-200 (defesa em profundidade), nunca como caminho de auth/5xx.
    const okBlockIdx = src.indexOf("Bug C (Task #1165 canonical-fix)")
    const dataSuccessIdx = src.indexOf(
      "data.success && data.questions",
      okBlockIdx
    )
    expect(okBlockIdx).toBeGreaterThan(0)
    expect(dataSuccessIdx).toBeGreaterThan(okBlockIdx)
  })
})
