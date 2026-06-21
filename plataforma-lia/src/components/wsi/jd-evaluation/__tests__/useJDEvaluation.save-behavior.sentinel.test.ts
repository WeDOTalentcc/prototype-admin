/**
 * Sensor: useJDEvaluation — save behavior + observabilidade (sessão 2026-06-21)
 *
 * Bug #4 regression pin: handlers preservam generated_jd_text via coalescência enrichedJd.
 * Bug #5 regression pin: officialUpdates inclui 'responsibilities' key.
 * R2: fetchResponsibilitiesSuggestions verifica response.ok antes de parsear JSON.
 * R3: handleSaveAndUpdateJD usa coalescência consistente com os outros 2 handlers.
 * R4: todos os catch de fetch de sugestões logam o erro via console.error.
 */
import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { describe, expect, it } from "vitest"

const __dir = dirname(fileURLToPath(import.meta.url))
const SRC = readFileSync(join(__dir, "..", "useJDEvaluation.ts"), "utf-8")

function extractFunctionBody(src: string, funcName: string): string {
  const idx = src.indexOf(funcName)
  if (idx === -1) return ""
  return src.slice(idx, idx + 1500)
}

// ── REGRESSION PIN: Bugs #4 e #5 (commit fe9a25e7) ──────────────────────────

describe("Bug #4 regression pin — generated_jd_text coalescência", () => {
  it("handleSaveRascunho usa ?? enrichedJd para generated_jd_text", () => {
    const body = extractFunctionBody(SRC, "handleSaveRascunho")
    expect(body).toMatch(/generated_jd_text[\s\S]{0,100}\?\?[\s\S]{0,50}enrichedJd/)
  })

  it("handleSaveDefinitiva usa ?? enrichedJd para generated_jd_text", () => {
    const body = extractFunctionBody(SRC, "handleSaveDefinitiva")
    expect(body).toMatch(/generated_jd_text[\s\S]{0,100}\?\?[\s\S]{0,50}enrichedJd/)
  })
})

describe("Bug #5 regression pin — responsibilities key em officialUpdates", () => {
  it("handleSaveDefinitiva inclui responsibilities no officialUpdates", () => {
    const body = extractFunctionBody(SRC, "handleSaveDefinitiva")
    expect(body).toMatch(/responsibilities:\s*edit/)
  })

  it("handleSaveRascunho inclui responsibilities no officialUpdates", () => {
    const body = extractFunctionBody(SRC, "handleSaveRascunho")
    expect(body).toMatch(/responsibilities:\s*edit/)
  })
})

// ── R2: response.ok check em fetchResponsibilitiesSuggestions ───────────────

describe("R2 — fetchResponsibilitiesSuggestions verifica response.ok", () => {
  it("verifica response.ok antes de chamar response.json()", () => {
    const body = extractFunctionBody(SRC, "fetchResponsibilitiesSuggestions")
    expect(body).toMatch(/response\.ok/)
  })
})

// ── R3: coalescência em handleSaveAndUpdateJD ───────────────────────────────

describe("R3 — handleSaveAndUpdateJD usa coalescência consistente", () => {
  it("generated_jd_text usa coalescência com enrichedJd", () => {
    const body = extractFunctionBody(SRC, "handleSaveAndUpdateJD")
    expect(body).toMatch(/generated_jd_text[\s\S]{0,100}\?\?[\s\S]{0,50}enrichedJd/)
  })
})

// ── R4: console.error em catch blocks ───────────────────────────────────────

describe("R4 — fetch suggestions logam erros via console.error", () => {
  it("fetchTechSuggestions catch loga via console.error", () => {
    const body = extractFunctionBody(SRC, "fetchTechSuggestions")
    expect(body).toMatch(/catch[\s\S]{0,60}console\.error/)
  })

  it("fetchBehavSuggestions catch loga via console.error", () => {
    const body = extractFunctionBody(SRC, "fetchBehavSuggestions")
    expect(body).toMatch(/catch[\s\S]{0,60}console\.error/)
  })

  it("fetchResponsibilitiesSuggestions catch loga via console.error", () => {
    const body = extractFunctionBody(SRC, "fetchResponsibilitiesSuggestions")
    expect(body).toMatch(/catch[\s\S]{0,100}console\.error/)
  })
})
