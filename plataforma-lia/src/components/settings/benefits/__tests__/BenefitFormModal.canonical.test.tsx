/**
 * Sensor canonical-fix + design-system para BenefitFormModal.tsx
 *
 * Source-level static check (sem DOM/jsdom): le o arquivo e garante
 * que nao ha regressao para padroes anti-canonical.
 *
 * Por que static? Radix Select em jsdom requer polyfills
 * (hasPointerCapture, scrollIntoView). Source-level e mais robusto
 * e pega exatamente as regressoes que importam.
 *
 * Aplica:
 * - canonical-fix: zero hardcoded BENEFIT_CATEGORIES local
 * - production-quality (frontend-quality): DS tokens, no anti-patterns
 * - harness-engineering: sensor permanente, baixo custo, no false positives
 */
import { describe, it, expect } from "vitest"
import { readFileSync } from "fs"
import { join } from "path"

const MODAL_PATH = join(__dirname, "..", "BenefitFormModal.tsx")
const source = readFileSync(MODAL_PATH, "utf-8")

// Remove docstrings/comentarios pra evitar falso-positivo em mencao a anti-pattern
const codeOnly = source
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .replace(/^\s*\/\/.*$/gm, "")

describe("BenefitFormModal canonical compliance", () => {
  describe("canonical-fix: no hardcoded taxonomy", () => {
    it("does NOT define a local BENEFIT_CATEGORIES array", () => {
      const hasLocalConst =
        /const\s+BENEFIT_CATEGORIES\s*=/.test(codeOnly) ||
        /BENEFIT_CATEGORIES:\s*[A-Z]/.test(codeOnly)
      expect(
        hasLocalConst,
        "BenefitFormModal must consume categories via useBenefitTaxonomy hook, " +
          "not define a local BENEFIT_CATEGORIES array (canonical-fix drift).",
      ).toBe(false)
    })

    it("does NOT define a local VALUE_TYPES array", () => {
      const hasLocal = /const\s+VALUE_TYPES\s*=/.test(codeOnly)
      expect(hasLocal).toBe(false)
    })

    it("does NOT define a local WAITING_PERIODS array", () => {
      const hasLocal = /const\s+WAITING_PERIODS\s*=/.test(codeOnly)
      expect(hasLocal).toBe(false)
    })

    it("imports useBenefitTaxonomy canonical hook", () => {
      expect(codeOnly).toMatch(
        /import\s*\{[^}]*useBenefitTaxonomy[^}]*\}\s*from\s*["']@\/hooks\/settings\/useBenefitTaxonomy["']/,
      )
    })
  })

  describe("design-system: DialogContent canonical", () => {
    it("uses DialogContent JSX (not DraggableDialogContent)", () => {
      expect(
        codeOnly.includes("<DialogContent"),
        "Modal de cadastro deve usar DialogContent simples.",
      ).toBe(true)

      // Procura uso REAL — import OR JSX. Ignora docstrings (codeOnly ja removeu).
      const hasImport = /import\s*\{[^}]*DraggableDialogContent[^}]*\}/.test(codeOnly)
      const hasJsx = /<DraggableDialogContent\b/.test(codeOnly)
      expect(
        hasImport || hasJsx,
        "DraggableDialogContent nao deve ser importado nem renderizado. " +
          "Drag handle de 48px bloqueia clicks em SelectTriggers proximos do topo.",
      ).toBe(false)
    })
  })

  describe("design-system: tokens canonical (v4.2.2)", () => {
    it("does NOT use rounded-full on Input elements (DS drift)", () => {
      // rounded-full em Input texto livre eh anti-pattern. OK em buttons/chips.
      const inputRoundedFull = /<Input[^/]*className=["'][^"']*rounded-full/m.test(
        codeOnly,
      )
      expect(
        inputRoundedFull,
        "Inputs devem usar rounded-md (DS canonical), nao rounded-full.",
      ).toBe(false)
    })

    it("does NOT use border-neutral-* hardcoded (use border-lia-border-*)", () => {
      const hasNeutralBorder = /border-neutral-\d/.test(codeOnly)
      expect(
        hasNeutralBorder,
        "Use tokens DS canonical: border-lia-border-subtle ou border-lia-border-default.",
      ).toBe(false)
    })

    it("does NOT use text-neutral-700/800/900 hardcoded (use text-lia-text-*)", () => {
      const hasNeutralText = /text-neutral-[7-9]00/.test(codeOnly)
      expect(
        hasNeutralText,
        "Use tokens DS canonical: text-lia-text-primary, text-lia-text-secondary.",
      ).toBe(false)
    })
  })

  describe("harness-engineering: new value_types support", () => {
    it("validates new value_types (match/reimbursement/coverage)", () => {
      expect(codeOnly).toMatch(/match/)
      expect(codeOnly).toMatch(/reimbursement/)
      expect(codeOnly).toMatch(/coverage/)
    })
  })
})
