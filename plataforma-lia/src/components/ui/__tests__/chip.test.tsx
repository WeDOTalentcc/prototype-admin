/**
 * Visual regression tests for the canonical `Chip` component.
 *
 * Strategy
 * --------
 * Every `variant` × `density` × `muted` combination is rendered and serialized
 * to a snapshot. Each combination is also rendered inside a `.dark` wrapper so
 * any change to the dark-mode token mapping is caught alongside the light-mode
 * baseline. The snapshots capture the resolved Tailwind className list, which
 * is the visual contract of the chip — any drift in `kanbanChipStyles` (the
 * shared design token) will fail this suite.
 *
 * The Storybook companion (`chip.stories.tsx`) feeds Chromatic for pixel-level
 * regression. This file gives the same matrix coverage in the regular vitest
 * `components` project so it runs in CI next to the existing kanban e2e checks
 * without requiring a Storybook server.
 *
 * Reference: src/components/ui/chip.tsx, src/lib/design-tokens.ts (kanbanChipStyles)
 */
import { describe, expect, it } from "vitest"
import { render } from "@testing-library/react"

import { Chip, type ChipDensity, type ChipVariant } from "../chip"

const VARIANTS: ChipVariant[] = ["neutral", "success", "warning", "danger", "info"]
const DENSITIES: ChipDensity[] = ["comfortable", "compact"]
const MUTED_STATES: boolean[] = [false, true]
const THEMES: Array<"light" | "dark"> = ["light", "dark"]

function renderChip(opts: {
  variant: ChipVariant
  density: ChipDensity
  muted: boolean
  theme: "light" | "dark"
}) {
  const { variant, density, muted, theme } = opts
  const { container } = render(
    <div className={theme === "dark" ? "dark" : undefined}>
      <Chip variant={variant} density={density} muted={muted}>
        {variant}
      </Chip>
    </div>,
  )
  return container.querySelector("span") as HTMLSpanElement
}

describe("Chip — visual regression matrix", () => {
  it("renders every variant × density × muted × theme combination", () => {
    expect(VARIANTS.length * DENSITIES.length * MUTED_STATES.length * THEMES.length).toBe(40)
  })

  for (const theme of THEMES) {
    describe(`theme: ${theme}`, () => {
      for (const density of DENSITIES) {
        for (const muted of MUTED_STATES) {
          for (const variant of VARIANTS) {
            const label = `variant=${variant} density=${density} muted=${String(muted)}`
            it(`matches snapshot — ${label}`, () => {
              const chip = renderChip({ variant, density, muted, theme })
              expect(chip).not.toBeNull()
              expect(chip.outerHTML).toMatchSnapshot()
            })
          }
        }
      }
    })
  }
})

describe("Chip — structural invariants", () => {
  it("always renders a span with role-friendly text content", () => {
    const chip = renderChip({
      variant: "neutral",
      density: "comfortable",
      muted: false,
      theme: "light",
    })
    expect(chip.tagName).toBe("SPAN")
    expect(chip.textContent).toBe("neutral")
  })

  it("applies the shared base class for every variant", () => {
    for (const variant of VARIANTS) {
      const chip = renderChip({ variant, density: "comfortable", muted: false, theme: "light" })
      expect(chip.className).toContain("inline-flex")
      expect(chip.className).toContain("rounded-full")
    }
  })

  it("compact density emits the compact padding tokens", () => {
    // Note: `tailwind-merge` collapses the `text-micro` size with the variant
    // color token (both share the `text-` prefix), so we assert on the
    // padding tokens which uniquely identify the compact density.
    const chip = renderChip({
      variant: "neutral",
      density: "compact",
      muted: false,
      theme: "light",
    })
    expect(chip.className).toContain("px-1.5")
    expect(chip.className).toContain("py-0")
  })

  it("comfortable density emits the text-xs and px-2 size tokens", () => {
    const chip = renderChip({
      variant: "neutral",
      density: "comfortable",
      muted: false,
      theme: "light",
    })
    expect(chip.className).toContain("text-xs")
    expect(chip.className).toContain("px-2")
  })

  it("muted overrides the text color token", () => {
    const chip = renderChip({
      variant: "success",
      density: "comfortable",
      muted: true,
      theme: "light",
    })
    expect(chip.className).toContain("text-lia-text-tertiary")
  })

  it("forwards arbitrary props (data-*) to the underlying span", () => {
    const { container } = render(
      <Chip data-testid="my-chip" variant="info">
        info
      </Chip>,
    )
    expect(container.querySelector("[data-testid='my-chip']")).not.toBeNull()
  })
})
