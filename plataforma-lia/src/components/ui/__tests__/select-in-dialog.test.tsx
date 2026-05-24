/**
 * Sensor canonical pra prevenir regressao do bug:
 * "Select dropdown invisivel dentro de Dialog/DraggableDialog".
 *
 * Causa raiz historica (2026-05-24): select.tsx usava z-50 (=50)
 * enquanto DialogContent usa z-modal (=9999), entao o popover
 * renderizava ATRAS do modal e ficava invisivel.
 *
 * Este teste e static source-level (nao requer DOM/jsdom): le o
 * proprio arquivo select.tsx e garante que SelectContent canonical
 * usa z-modal token ou z-[>=9999], nunca z-50 drift.
 *
 * Por que static? Radix Select interactions em jsdom exigem
 * polyfills (hasPointerCapture, scrollIntoView). Source-level
 * check e mais robusto e detecta a regressao igualmente bem.
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "fs"
import { join } from "path"

const SELECT_PATH = join(__dirname, "..", "select.tsx")

describe("Select canonical — z-index contract (source-level sensor)", () => {
  const source = readFileSync(SELECT_PATH, "utf-8")

  it("select.tsx file exists and is readable", () => {
    expect(source.length).toBeGreaterThan(0)
  })

  it("SelectContent does NOT use z-50 (regression guard)", () => {
    // O bug historico era z-50 no SelectContent. Bloquear pra sempre.
    // Aceita z-50 em SelectScrollUpButton/SelectScrollDownButton se aparecer
    // (eles renderizam dentro do SelectContent, herdam stacking context).
    const contentBlockMatch = source.match(
      /const SelectContent[\s\S]*?SelectContent\.displayName/,
    )
    expect(contentBlockMatch, "SelectContent block not found in select.tsx").toBeTruthy()
    if (contentBlockMatch) {
      const contentBlock = contentBlockMatch[0]
      // O className do SelectContent eh a string literal canonical.
      // Procurar especificamente o trecho "relative z-XXX max-h-96"
      const zIndexMatch = contentBlock.match(/"relative\s+(z-\S+)/)
      expect(
        zIndexMatch,
        "Expected SelectContent canonical className 'relative z-X max-h-96' not found",
      ).toBeTruthy()
      if (zIndexMatch) {
        const zToken = zIndexMatch[1]
        const isZ50 = zToken === "z-50"
        const hint =
          "SelectContent must use z-modal (or z-[>=9999]). z-50 makes the popover invisible inside Dialog (z-modal=9999)."
        expect(isZ50, "z-index drift detected: " + zToken + ". " + hint).toBe(false)
      }
    }
  })

  it("SelectContent uses z-modal token (canonical) or z-[>=9999]", () => {
    const contentBlockMatch = source.match(
      /const SelectContent[\s\S]*?SelectContent\.displayName/,
    )
    expect(contentBlockMatch).toBeTruthy()
    if (contentBlockMatch) {
      const contentBlock = contentBlockMatch[0]
      const zIndexMatch = contentBlock.match(/"relative\s+(z-\S+)/)
      expect(zIndexMatch).toBeTruthy()
      if (zIndexMatch) {
        const zToken = zIndexMatch[1]
        const hasModalToken = zToken === "z-modal"
        const arbitraryMatch = /^z-\[(\d+)\]$/.exec(zToken)
        const arbitraryValue = arbitraryMatch ? parseInt(arbitraryMatch[1], 10) : 0
        const isCanonical = hasModalToken || arbitraryValue >= 9999
        const hint =
          "Use z-modal token (preferred) or z-[>=9999]. Found: " + zToken
        expect(isCanonical, hint).toBe(true)
      }
    }
  })
})
