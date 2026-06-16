/**
 * Smoke / regression test — BulkImportModal.
 *
 * Guards against the Rules of Hooks violation that crashed the
 * "Recrutar → Rail ATS → Bulk Import" flow on 2026-05-04 (the modal
 * declared a useCallback below `if (!isOpen) return null`, so the
 * hook count differed between renders and React threw
 * "Rendered more hooks than during the previous render").
 *
 * Sensor (harness): keep this test passing — it is the canonical
 * regression net for that class of bug. Do not remove without a
 * replacement signal in CI.
 */
import { describe, it, expect, vi } from "vitest"
import { render, screen, cleanup } from "@testing-library/react"
import { BulkImportModal } from "../BulkImportModal"

describe("BulkImportModal — Rules of Hooks regression", () => {
  it("renders nothing while isOpen=false (no crash)", () => {
    render(
      <BulkImportModal isOpen={false} onClose={vi.fn()} onSuccess={vi.fn()} />
    )
    expect(screen.queryByText(/importar vagas/i)).not.toBeInTheDocument()
    cleanup()
  })

  it("does not crash when toggling isOpen false → true → false", () => {
    const onClose = vi.fn()
    const onSuccess = vi.fn()

    const { rerender } = render(
      <BulkImportModal isOpen={false} onClose={onClose} onSuccess={onSuccess} />
    )

    // Transition that previously triggered the hooks-count mismatch:
    expect(() =>
      rerender(
        <BulkImportModal isOpen={true} onClose={onClose} onSuccess={onSuccess} />
      )
    ).not.toThrow()

    // And back — also a different hook-call path historically:
    expect(() =>
      rerender(
        <BulkImportModal isOpen={false} onClose={onClose} onSuccess={onSuccess} />
      )
    ).not.toThrow()
  })

  it("renders a heading once isOpen=true", () => {
    render(
      <BulkImportModal isOpen={true} onClose={vi.fn()} onSuccess={vi.fn()} />
    )
    // The wizard exposes some import-related copy in the header.
    // We assert presence of any of the canonical CTAs to keep the
    // selector resilient to copy churn.
    const matches = screen.queryAllByText(/import/i)
    expect(matches.length).toBeGreaterThan(0)
  })
})
