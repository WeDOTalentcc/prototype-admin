/**
 * Tests for the InteractiveSurface DS primitive (addresses the 🟡 audit gap
 * from Task #934 — primitive merged without component coverage).
 *
 * Strategy
 * --------
 * The primitive's contract per the source comment is:
 *   1. Renders a native <button> with `type="button"` by default.
 *   2. Exposes `data-ds-surface` attribute matching the chosen variant.
 *   3. Carries DS focus-ring + motion-reduce + transition-colors classes.
 *   4. Forwards arbitrary HTMLButton attributes (aria-*, onClick, disabled).
 *   5. Forwards refs.
 *   6. Allows callers to override visual classes via className (cva merges via cn).
 *
 * These invariants are the cva contract — any drift breaks both the accordion
 * variant (ABTestingTab) and other interactive-surface consumers.
 *
 * Reference: src/components/ui/interactive-surface.tsx (Task #934, commit e08ca68e3)
 */
import { describe, expect, it, vi } from "vitest"
import { createRef } from "react"
import { fireEvent, render, screen } from "@testing-library/react"
import { InteractiveSurface } from "../interactive-surface"

describe("InteractiveSurface", () => {
  it("renders as a native <button> with type='button' by default", () => {
    render(<InteractiveSurface>Click me</InteractiveSurface>)
    const btn = screen.getByRole("button", { name: /click me/i })
    expect(btn.tagName).toBe("BUTTON")
    expect(btn).toHaveAttribute("type", "button")
  })

  it("defaults to the accordion variant when none is provided", () => {
    render(<InteractiveSurface>x</InteractiveSurface>)
    const btn = screen.getByRole("button")
    expect(btn).toHaveAttribute("data-ds-surface", "accordion")
    // Accordion variant carries the canonical layout classes.
    expect(btn.className).toMatch(/w-full/)
    expect(btn.className).toMatch(/justify-between/)
    expect(btn.className).toMatch(/bg-lia-bg-primary/)
  })

  it("renders the card-toggle variant with the correct data attribute and class set", () => {
    render(
      <InteractiveSurface variant="card-toggle">card</InteractiveSurface>,
    )
    const btn = screen.getByRole("button")
    expect(btn).toHaveAttribute("data-ds-surface", "card-toggle")
    expect(btn.className).toMatch(/text-left/)
    // Card-toggle should NOT inherit the accordion-only `justify-between`.
    expect(btn.className).not.toMatch(/justify-between/)
  })

  it("always carries the DS focus-ring + motion-reduce + transition-colors invariants", () => {
    render(<InteractiveSurface>x</InteractiveSurface>)
    const btn = screen.getByRole("button")
    expect(btn.className).toMatch(/transition-colors/)
    expect(btn.className).toMatch(/motion-reduce:transition-none/)
    expect(btn.className).toMatch(/focus-visible:ring-2/)
    expect(btn.className).toMatch(/focus-visible:ring-lia-text-primary/)
    expect(btn.className).toMatch(/disabled:pointer-events-none/)
    expect(btn.className).toMatch(/disabled:opacity-50/)
  })

  it("merges caller className without dropping cva base classes", () => {
    render(
      <InteractiveSurface className="extra-from-callsite p-8">
        x
      </InteractiveSurface>,
    )
    const btn = screen.getByRole("button")
    expect(btn.className).toMatch(/extra-from-callsite/)
    expect(btn.className).toMatch(/p-8/)
    // Base invariant must still be present.
    expect(btn.className).toMatch(/transition-colors/)
  })

  it("forwards arbitrary aria-* attributes (used by ABTestingTab and other consumers)", () => {
    render(
      <InteractiveSurface
        variant="accordion"
        aria-expanded={true}
        aria-controls="panel-1"
      >
        accordion
      </InteractiveSurface>,
    )
    const btn = screen.getByRole("button")
    expect(btn).toHaveAttribute("aria-expanded", "true")
    expect(btn).toHaveAttribute("aria-controls", "panel-1")
  })

  it("forwards aria-pressed for card-toggle variant (semantic toggle contract)", () => {
    render(
      <InteractiveSurface variant="card-toggle" aria-pressed={true}>
        toggle
      </InteractiveSurface>,
    )
    expect(screen.getByRole("button")).toHaveAttribute("aria-pressed", "true")
  })

  it("forwards onClick handlers", () => {
    const onClick = vi.fn()
    render(<InteractiveSurface onClick={onClick}>x</InteractiveSurface>)
    fireEvent.click(screen.getByRole("button"))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it("respects the disabled attribute (no onClick fires)", () => {
    const onClick = vi.fn()
    render(
      <InteractiveSurface disabled onClick={onClick}>
        x
      </InteractiveSurface>,
    )
    fireEvent.click(screen.getByRole("button"))
    expect(onClick).not.toHaveBeenCalled()
  })

  it("forwards refs to the underlying button element", () => {
    const ref = createRef<HTMLButtonElement>()
    render(<InteractiveSurface ref={ref}>x</InteractiveSurface>)
    expect(ref.current).toBeInstanceOf(HTMLButtonElement)
  })

  it("allows the caller to override type='submit' (forms inside hubs)", () => {
    render(<InteractiveSurface type="submit">submit</InteractiveSurface>)
    expect(screen.getByRole("button")).toHaveAttribute("type", "submit")
  })
})
