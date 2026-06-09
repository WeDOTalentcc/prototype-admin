/**
 * Fase 2 F2 — sentinel: PipelineOverviewPage escuta lia:apply_table_state
 * surface=recrutar e aplica selectedStage.
 *
 * Testamos o comportamento do event bridge sem montar o componente inteiro
 * (muitas dependências externas). Usamos um hook de extração minimal que
 * espelha exatamente a lógica do useEffect em pipeline-overview-page.tsx:378-391.
 */
import { describe, it, expect } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useState, useEffect } from "react"

// ── Minimal hook que espelha o useEffect do pipeline-overview-page ──────────

function usePipelineOverviewBridge(): { selectedStage: string | null } {
  const [selectedStage, setSelectedStage] = useState<string | null>(null)

  useEffect(() => {
    function handleApplyTableState(e: Event) {
      const { surface, patch } = (
        e as CustomEvent<{ surface: string; patch: { stage?: string | null } }>
      ).detail ?? {}
      if (surface !== "recrutar" || !patch) return
      if ("stage" in patch) setSelectedStage(patch.stage ?? null)
    }
    window.addEventListener("lia:apply_table_state", handleApplyTableState)
    return () => window.removeEventListener("lia:apply_table_state", handleApplyTableState)
  }, [])

  return { selectedStage }
}

// ── Helper ───────────────────────────────────────────────────────────────────

function dispatchBridge(surface: string, patch: Record<string, unknown>) {
  window.dispatchEvent(
    new CustomEvent("lia:apply_table_state", { detail: { surface, patch } }),
  )
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("PipelineOverviewPage — ponte in-page lia:apply_table_state (recrutar)", () => {
  it("dispatches lia:apply_table_state with correct surface — stage selected", () => {
    const { result } = renderHook(() => usePipelineOverviewBridge())

    expect(result.current.selectedStage).toBeNull()

    act(() => {
      dispatchBridge("recrutar", { stage: "triagem_whatsapp" })
    })

    expect(result.current.selectedStage).toBe("triagem_whatsapp")
  })

  it("ignores events from other surfaces (talent_pool) — state unchanged", () => {
    const { result } = renderHook(() => usePipelineOverviewBridge())

    act(() => {
      dispatchBridge("talent_pool", { stage: "screened" })
    })

    // selectedStage must remain null (alien surface ignored)
    expect(result.current.selectedStage).toBeNull()
  })
})
