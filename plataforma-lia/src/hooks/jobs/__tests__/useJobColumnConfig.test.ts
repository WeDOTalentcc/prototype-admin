import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"

// ---------------------------------------------------------------------------
// useJobColumnConfig tests
// Covers:
//   - default_all_visible: all default visible columns have visible:true
//   - toggle_hides_column: toggleColumn flips visibility
//   - toggle_shows_column: calling toggle again restores visibility
//   - persists_to_store: setJobColumnConfig is called when toggling
//   - reset_restores_defaults: resetToDefault reverts to DEFAULT_COLUMNS
//   - getColumnsByCategory: groups columns by category correctly
//   - visibleColumnIds: reflects only visible column ids
// ---------------------------------------------------------------------------

// Mock the Zustand ui-preferences-store so we control persistence
const mockJobColumnConfig: { value: unknown } = { value: null }
const mockSetJobColumnConfig = vi.fn((cfg) => { mockJobColumnConfig.value = cfg })

vi.mock("@/stores/ui-preferences-store", () => ({
  useUIPreferencesStore: (selector?: (s: Record<string, unknown>) => unknown) => {
    const store = {
      jobColumnConfig: mockJobColumnConfig.value,
      setJobColumnConfig: mockSetJobColumnConfig,
    }
    return selector ? selector(store) : store
  },
}))

import { useJobColumnConfig } from "../useJobColumnConfig"

const DEFAULT_VISIBLE_IDS = [
  "id", "status", "screeningStatus", "title", "candidates", "performance",
  "recruiter", "manager", "location", "readiness",
]

describe("useJobColumnConfig", () => {
  beforeEach(() => {
    mockJobColumnConfig.value = null
    mockSetJobColumnConfig.mockClear()
  })

  it("default: correct columns are visible", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    const visibleIds = result.current.visibleColumns.map((c) => c.id)
    DEFAULT_VISIBLE_IDS.forEach((id) => {
      expect(visibleIds, ).toContain(id)
    })
  })

  it("default: invisible columns are not visible", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    const invisibleSample = ["salary", "budget", "department", "publishedLinkedIn"]
    const visibleIds = result.current.visibleColumns.map((c) => c.id)
    invisibleSample.forEach((id) => {
      expect(visibleIds, ).not.toContain(id)
    })
  })

  it("toggleColumn: hides a visible column", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    act(() => {
      result.current.toggleColumn("status")
    })
    const statusCol = result.current.columns.find((c) => c.id === "status")
    expect(statusCol?.visible).toBe(false)
  })

  it("toggleColumn: shows a hidden column", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    // salary is hidden by default
    act(() => {
      result.current.toggleColumn("salary")
    })
    const salaryCol = result.current.columns.find((c) => c.id === "salary")
    expect(salaryCol?.visible).toBe(true)
  })

  it("toggleColumn: calls setJobColumnConfig to persist", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    act(() => {
      result.current.toggleColumn("status")
    })
    expect(mockSetJobColumnConfig).toHaveBeenCalledTimes(1)
    const saved = mockSetJobColumnConfig.mock.calls[0][0]
    expect(saved).toHaveProperty("columns")
    const savedStatus = saved.columns.find((c: { id: string }) => c.id === "status")
    expect(savedStatus?.visible).toBe(false)
  })

  it("visibleColumnIds: reflects only visible ids", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    const { visibleColumnIds, columns } = result.current
    const expectedVisible = columns.filter((c) => c.visible).map((c) => c.id)
    expect(visibleColumnIds.sort()).toEqual(expectedVisible.sort())
  })

  it("resetToDefault: restores all default visibilities", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    // Hide a default-visible column first
    act(() => {
      result.current.toggleColumn("status")
    })
    expect(result.current.columns.find((c) => c.id === "status")?.visible).toBe(false)
    // Reset
    act(() => {
      result.current.resetToDefault()
    })
    expect(result.current.columns.find((c) => c.id === "status")?.visible).toBe(true)
    // salary should still be hidden (default)
    expect(result.current.columns.find((c) => c.id === "salary")?.visible).toBe(false)
  })

  it("getColumnsByCategory: groups by category", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    const categories = result.current.getColumnsByCategory()
    // All known categories must be present
    expect(Object.keys(categories)).toContain("principais")
    expect(Object.keys(categories)).toContain("remuneracao")
    // Every column in a category must have that category
    Object.entries(categories).forEach(([cat, cols]) => {
      cols.forEach((col) => {
        expect(col.category).toBe(cat)
      })
    })
  })

  it("setColumnVisibility: sets specific visibility without toggling", () => {
    const { result } = renderHook(() => useJobColumnConfig())
    act(() => {
      result.current.setColumnVisibility("status", false)
    })
    expect(result.current.columns.find((c) => c.id === "status")?.visible).toBe(false)
    // Calling again with same value should be idempotent
    act(() => {
      result.current.setColumnVisibility("status", false)
    })
    expect(result.current.columns.find((c) => c.id === "status")?.visible).toBe(false)
  })
})
