/**
 * Tests for the rejection-categories pure helper (Task #984, addresses the
 * 🔴 audit gap from Task #939 — helper merged without unit coverage).
 *
 * Strategy
 * --------
 * `groupOptionsByCategory` and `shouldGroupByCategory` are pure functions —
 * tested as pure logic with no React tree. `renderSubStatusOptions` returns a
 * React subtree of `<SelectItem>` / `<SelectGroup>`, so it's tested via React
 * Testing Library wrapped in a Radix `<Select>` (the SelectItem/SelectGroup
 * primitives require the SelectContext provided by the parent root).
 *
 * Reference: src/components/kanban/components/rejection-categories.tsx
 * Audit: replit.md → "Funil de Talentos / Settings Menu Architecture" sister
 *   commit 168bb26db (Task #939); follow-up #984.
 */
import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"
import {
  groupOptionsByCategory,
  shouldGroupByCategory,
  renderSubStatusOptions,
  CANONICAL_CATEGORY_KEYS,
  defaultCategoryLabelsPtBR,
  type SubStatusOptionWithCategory,
} from "../rejection-categories"
import { Select, SelectContent, SelectTrigger } from "@/components/ui/select"

function renderSelect(children: React.ReactNode) {
  return render(
    <Select open>
      <SelectTrigger />
      <SelectContent>{children}</SelectContent>
    </Select>,
  )
}

const opt = (
  code: string,
  display_name: string,
  category?: string,
): SubStatusOptionWithCategory => ({ code, display_name, category })

describe("groupOptionsByCategory", () => {
  it("groups options into the canonical category order", () => {
    const groups = groupOptionsByCategory([
      opt("salary_too_low", "Pretensão acima", "compensation"),
      opt("no_match", "Sem fit técnico", "qualification"),
      opt("not_culture_fit", "Sem fit cultural", "cultural"),
      opt("budget_freeze", "Vaga congelada", "business_decision"),
    ])

    expect(groups.map((g) => g.key)).toEqual([
      "business_decision",
      "qualification",
      "cultural",
      "compensation",
    ])
  })

  it("hides empty canonical categories instead of rendering empty headings", () => {
    const groups = groupOptionsByCategory([
      opt("only_one", "Sozinho", "qualification"),
    ])

    expect(groups).toHaveLength(1)
    expect(groups[0].key).toBe("qualification")
    expect(groups[0].items).toHaveLength(1)
  })

  it("buckets unknown categories under the synthetic `__other__` key with the OTHER label", () => {
    const groups = groupOptionsByCategory([
      opt("legit", "Conhecida", "qualification"),
      opt("weird", "Categoria estranha", "wat_is_this"),
      opt("noCat", "Sem categoria"),
    ])

    const other = groups.find((g) => g.key === "__other__")
    expect(other).toBeDefined()
    expect(other!.label).toBe(defaultCategoryLabelsPtBR.__other__)
    expect(other!.items.map((i) => i.code).sort()).toEqual(["noCat", "weird"])
    // Canonical category still appears, ordered before __other__.
    expect(groups[0].key).toBe("qualification")
    expect(groups[groups.length - 1].key).toBe("__other__")
  })

  it("respects a caller-supplied label map (i18n migration contract from #983)", () => {
    const englishLabels = {
      ...defaultCategoryLabelsPtBR,
      qualification: "Qualification",
      cultural: "Culture fit",
      __other__: "Other",
    }
    const groups = groupOptionsByCategory(
      [opt("a", "A", "qualification"), opt("b", "B", "cultural")],
      englishLabels,
    )
    expect(groups.map((g) => g.label)).toEqual(["Qualification", "Culture fit"])
  })

  it("returns an empty array for an empty input (no headings, no flicker)", () => {
    expect(groupOptionsByCategory([])).toEqual([])
  })

  it("omits the __other__ bucket entirely when every option is canonical", () => {
    const groups = groupOptionsByCategory([
      opt("a", "A", "qualification"),
      opt("b", "B", "cultural"),
    ])
    expect(groups.find((g) => g.key === "__other__")).toBeUndefined()
  })

  it("preserves canonical category ordering even when input is shuffled and some categories are missing", () => {
    // Input deliberately out of order and skipping `qualification` + `compensation`.
    const groups = groupOptionsByCategory([
      opt("p1", "Processo lento", "process"),
      opt("l1", "Mudança", "logistics"),
      opt("b1", "Vaga congelada", "business_decision"),
      opt("c1", "Sem fit", "cultural"),
    ])
    // Hidden categories (qualification, compensation) must not appear as empty headings.
    expect(groups.map((g) => g.key)).toEqual([
      "business_decision",
      "cultural",
      "logistics",
      "process",
    ])
  })
})

describe("shouldGroupByCategory", () => {
  it("returns true when at least one option carries a recognized category", () => {
    expect(
      shouldGroupByCategory([opt("a", "A"), opt("b", "B", "qualification")]),
    ).toBe(true)
  })

  it("returns false for a fully un-categorized list (preserves flat-list legacy behavior)", () => {
    expect(shouldGroupByCategory([opt("a", "A"), opt("b", "B")])).toBe(false)
  })

  it("returns false when only unknown categories are present (no fake headings)", () => {
    expect(shouldGroupByCategory([opt("a", "A", "wat_is_this")])).toBe(false)
  })

  it("returns false for an empty list", () => {
    expect(shouldGroupByCategory([])).toBe(false)
  })
})

describe("CANONICAL_CATEGORY_KEYS contract", () => {
  it("exposes the same canonical keys used by groupOptionsByCategory", () => {
    expect(CANONICAL_CATEGORY_KEYS).toEqual([
      "business_decision",
      "qualification",
      "cultural",
      "logistics",
      "compensation",
      "process",
    ])
  })

  it("every canonical key has a default PT-BR label (i18n fallback safety)", () => {
    for (const k of CANONICAL_CATEGORY_KEYS) {
      expect(defaultCategoryLabelsPtBR[k]).toBeTruthy()
    }
    expect(defaultCategoryLabelsPtBR.__other__).toBeTruthy()
  })
})

describe("renderSubStatusOptions", () => {
  it("renders a flat list of SelectItems when no option carries a category", () => {
    renderSelect(
      renderSubStatusOptions([opt("a", "Option A"), opt("b", "Option B")]),
    )
    // SelectItem renders its child text; assert the flat list contains both.
    // Radix portals SelectContent to document.body, so we query the document.
    expect(document.body.textContent).toContain("Option A")
    expect(document.body.textContent).toContain("Option B")
    // No category heading should be rendered.
    expect(document.body.textContent).not.toContain(
      defaultCategoryLabelsPtBR.qualification,
    )
  })

  it("renders SelectGroup headings when at least one option has a category", () => {
    renderSelect(
      renderSubStatusOptions([
        opt("a", "Option A", "qualification"),
        opt("b", "Option B", "cultural"),
      ]),
    )
    expect(document.body.textContent).toContain(
      defaultCategoryLabelsPtBR.qualification,
    )
    expect(document.body.textContent).toContain(
      defaultCategoryLabelsPtBR.cultural,
    )
    expect(document.body.textContent).toContain("Option A")
    expect(document.body.textContent).toContain("Option B")
  })

  it("uses caller-supplied i18n labels when provided (English example)", () => {
    const englishLabels = {
      ...defaultCategoryLabelsPtBR,
      qualification: "Qualification",
    }
    renderSelect(
      renderSubStatusOptions(
        [opt("a", "Option A", "qualification")],
        "text-xs",
        englishLabels,
      ),
    )
    expect(document.body.textContent).toContain("Qualification")
    expect(document.body.textContent).not.toContain(
      defaultCategoryLabelsPtBR.qualification,
    )
  })
})
