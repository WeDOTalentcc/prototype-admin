import { describe, it, expect, beforeEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useKanbanTableView } from "../useKanbanTableView"
import { useKanbanStore } from "@/stores/kanban-store"

// Fase 2 (ponte in-page Kanban): o hook escuta lia:apply_table_state {surface:'kanban'}
// e aplica score/status/origem aos setters locais; search vai pro kanban-store.
describe("useKanbanTableView — ponte in-page lia:apply_table_state (kanban)", () => {
  beforeEach(() => {
    useKanbanStore.getState().setSearchQuery("")
  })

  function render() {
    return renderHook(() =>
      useKanbanTableView({ dynamicStages: [], candidatesData: {}, viewMode: "kanban" }),
    )
  }

  it("aplica score/status/origem + search ao receber surface kanban", () => {
    const { result } = render()
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:apply_table_state", {
          detail: {
            surface: "kanban",
            patch: {
              search: "João",
              scoreMin: 75,
              statusFilter: ["novo"],
              originFilter: ["web"],
            },
          },
        }),
      )
    })
    expect(result.current.state.kanbanScoreMin).toBe(75)
    expect(result.current.state.kanbanStatusFilter).toEqual(["novo"])
    expect(result.current.state.kanbanOriginFilter).toEqual(["web"])
    expect(useKanbanStore.getState().searchQuery).toBe("João")
  })

  it("ignora surface != kanban", () => {
    const { result } = render()
    act(() => {
      window.dispatchEvent(
        new CustomEvent("lia:apply_table_state", {
          detail: { surface: "jobs", patch: { scoreMin: 99 } },
        }),
      )
    })
    expect(result.current.state.kanbanScoreMin).toBe(0)
  })
})
