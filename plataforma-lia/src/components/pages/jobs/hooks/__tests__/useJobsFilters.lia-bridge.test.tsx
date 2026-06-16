import { describe, it, expect } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useJobsFilters } from "../useJobsFilters"

// Fase 2 (ponte in-page Vagas): o hook escuta lia:apply_table_state {surface:'jobs'}
// e aplica busca/filtro de status aos setters locais (onde o estado vive).
describe("useJobsFilters — ponte in-page lia:apply_table_state (jobs)", () => {
  it("aplica search + filter ao receber surface jobs", () => {
    const { result } = renderHook(() => useJobsFilters({ backendJobs: [] }))
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:apply_table_state", {
          detail: { surface: "jobs", patch: { search: "backend", filter: "ativas" } },
        }),
      )
    })
    expect(result.current.state.searchTerm).toBe("backend")
    expect(result.current.state.activeFilter).toBe("ativas")
  })

  it("ignora surface != jobs (ex: candidates) — nao aplica o patch alheio", () => {
    const { result } = renderHook(() => useJobsFilters({ backendJobs: [] }))
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:apply_table_state", {
          detail: { surface: "candidates", patch: { search: "PATCH_ALHEIO" } },
        }),
      )
    })
    expect(result.current.state.searchTerm).not.toBe("PATCH_ALHEIO")
  })
})
