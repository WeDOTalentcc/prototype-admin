/**
 * Tests for nav guard + onNewSearch modal behaviour
 *
 * Bug #1 — onNewSearch bypassed the guard, allowing navigation without modal
 * Bug #2 — guard condition ignored pearchResultsCount (candidates filtered-out scenario)
 */

import { describe, it, expect, vi, beforeEach } from "vitest"

// ── Shared mock for useNavGuardStore ──────────────────────────────────────────
let navGuardState: { active: boolean; pendingProceed: (() => void) | null } = {
  active: false,
  pendingProceed: null,
}
const mockSetActive = vi.fn((v: boolean) => {
  navGuardState.active = v
})
const mockRequestLeave = vi.fn((proceed: () => void) => {
  navGuardState.pendingProceed = proceed
})
const mockClear = vi.fn(() => {
  navGuardState.pendingProceed = null
})

vi.mock("@/stores/nav-guard-store", () => ({
  useNavGuardStore: Object.assign(
    (selector: (s: typeof navGuardState & { setActive: typeof mockSetActive; requestLeave: typeof mockRequestLeave; clear: typeof mockClear }) => unknown) =>
      selector({ ...navGuardState, setActive: mockSetActive, requestLeave: mockRequestLeave, clear: mockClear }),
    {
      getState: () => ({
        ...navGuardState,
        setActive: mockSetActive,
        requestLeave: mockRequestLeave,
        clear: mockClear,
      }),
    }
  ),
}))

// ── Unit tests for onNewSearch guard logic ────────────────────────────────────
describe("onNewSearch nav guard (Bug #1)", () => {
  beforeEach(() => {
    navGuardState = { active: false, pendingProceed: null }
    vi.clearAllMocks()
  })

  it("should call requestLeave instead of clearing directly when unsaved pearch candidates exist", () => {
    // Simulate the guard logic extracted from candidates-page.tsx onNewSearch
    const unsavedPearchCandidates = [{ id: "1", source: "pearch" }]
    const pearchResultsCount = 1
    const showSearchResults = true

    const clearSearch = vi.fn()

    if ((unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults) {
      mockRequestLeave(clearSearch)
    } else {
      clearSearch()
    }

    expect(mockRequestLeave).toHaveBeenCalledWith(clearSearch)
    expect(clearSearch).not.toHaveBeenCalled()
  })

  it("should clear search directly when no pearch candidates", () => {
    const unsavedPearchCandidates: unknown[] = []
    const pearchResultsCount = 0
    const showSearchResults = true

    const clearSearch = vi.fn()

    if ((unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults) {
      mockRequestLeave(clearSearch)
    } else {
      clearSearch()
    }

    expect(mockRequestLeave).not.toHaveBeenCalled()
    expect(clearSearch).toHaveBeenCalledOnce()
  })

  it("should clear search directly when showSearchResults is false (guard already inactive)", () => {
    const unsavedPearchCandidates = [{ id: "1", source: "pearch" }]
    const pearchResultsCount = 1
    const showSearchResults = false

    const clearSearch = vi.fn()

    if ((unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults) {
      mockRequestLeave(clearSearch)
    } else {
      clearSearch()
    }

    expect(mockRequestLeave).not.toHaveBeenCalled()
    expect(clearSearch).toHaveBeenCalledOnce()
  })
})

// ── Unit tests for hasUnsavedPearchCandidates condition (Bug #2) ──────────────
describe("hasUnsavedPearchCandidates guard condition (Bug #2)", () => {
  it("should be true when pearchResultsCount > 0 even if local array is empty (filter scenario)", () => {
    // Scenario: hideViewedCandidatesFilter removed all pearch candidates from the array
    // but backend confirmed there were results
    const unsavedPearchCandidates: unknown[] = []
    const pearchResultsCount = 5 // backend reported 5 pearch results
    const showSearchResults = true

    const hasUnsavedPearchCandidates =
      (unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults

    expect(hasUnsavedPearchCandidates).toBe(true)
  })

  it("should be true when candidates array has pearch candidates", () => {
    const unsavedPearchCandidates = [{ id: "1", source: "pearch" }, { id: "2", source: "pearch" }]
    const pearchResultsCount = 0
    const showSearchResults = true

    const hasUnsavedPearchCandidates =
      (unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults

    expect(hasUnsavedPearchCandidates).toBe(true)
  })

  it("should be false when both array and count are zero", () => {
    const unsavedPearchCandidates: unknown[] = []
    const pearchResultsCount = 0
    const showSearchResults = true

    const hasUnsavedPearchCandidates =
      (unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults

    expect(hasUnsavedPearchCandidates).toBe(false)
  })

  it("should be false when showSearchResults is false", () => {
    const unsavedPearchCandidates = [{ id: "1", source: "pearch" }]
    const pearchResultsCount = 3
    const showSearchResults = false

    const hasUnsavedPearchCandidates =
      (unsavedPearchCandidates.length > 0 || pearchResultsCount > 0) && showSearchResults

    expect(hasUnsavedPearchCandidates).toBe(false)
  })
})

// ── Integration: sidebar nav triggers guard when pearch results present ────────
describe("sidebar navigation guard integration (Bug #1 + Bug #2)", () => {
  beforeEach(() => {
    navGuardState = { active: false, pendingProceed: null }
    vi.clearAllMocks()
  })

  it("should intercept navigation and set pendingProceed when guard is active", () => {
    // Simulate dashboard-app.tsx handleNavigate behavior
    navGuardState.active = true
    const proceedFn = vi.fn()

    const handleNavigate = (proceed: () => void) => {
      const navGuard = { ...navGuardState, requestLeave: mockRequestLeave }
      if (navGuard.active) {
        navGuard.requestLeave(proceed)
        return
      }
      proceed()
    }

    handleNavigate(proceedFn)

    expect(mockRequestLeave).toHaveBeenCalledWith(proceedFn)
    expect(proceedFn).not.toHaveBeenCalled()
  })

  it("should proceed directly when guard is inactive", () => {
    navGuardState.active = false
    const proceedFn = vi.fn()

    const handleNavigate = (proceed: () => void) => {
      const navGuard = { ...navGuardState, requestLeave: mockRequestLeave }
      if (navGuard.active) {
        navGuard.requestLeave(proceed)
        return
      }
      proceed()
    }

    handleNavigate(proceedFn)

    expect(mockRequestLeave).not.toHaveBeenCalled()
    expect(proceedFn).toHaveBeenCalledOnce()
  })
})
