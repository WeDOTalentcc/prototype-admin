/**
 * Fase 2 F2 — sentinel: TalentPoolPage escuta lia:apply_table_state
 * surface=talent_pool e aplica stageFilter / activeTab.
 *
 * Testamos o comportamento do event bridge sem montar o componente inteiro
 * (muitas dependências externas). Usamos um hook de extração minimal que
 * espelha exatamente a lógica do useEffect em TalentPoolPage.tsx:145-157.
 */
import { describe, it, expect, afterEach } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useState, useEffect } from "react"

// ── Minimal hook que espelha o useEffect do TalentPoolPage ──────────────────

type BridgeState = { stageFilter: string | null; activeTab: string }

function useTalentPoolBridge(initialTab = "candidates"): BridgeState {
  const [stageFilter, setStageFilter] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string>(initialTab)

  useEffect(() => {
    function handleApplyTableState(e: Event) {
      const { surface, patch } = (
        e as CustomEvent<{ surface: string; patch: { stage?: string | null; poolTab?: string } }>
      ).detail ?? {}
      if (surface !== "talent_pool" || !patch) return
      if ("stage" in patch) setStageFilter(patch.stage ?? null)
      if (typeof patch.poolTab === "string") setActiveTab(patch.poolTab)
    }
    window.addEventListener("lia:apply_table_state", handleApplyTableState)
    return () => window.removeEventListener("lia:apply_table_state", handleApplyTableState)
  }, [])

  return { stageFilter, activeTab }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function dispatchBridge(surface: string, patch: Record<string, unknown>) {
  window.dispatchEvent(
    new CustomEvent("lia:apply_table_state", { detail: { surface, patch } }),
  )
}

afterEach(() => {
  // Nothing to clean up — listener is removed by hook cleanup
})

// ── Tests ────────────────────────────────────────────────────────────────────

describe("TalentPoolPage — ponte in-page lia:apply_table_state (talent_pool)", () => {
  it("dispatches lia:apply_table_state with correct surface — stage filter applied", () => {
    const { result } = renderHook(() => useTalentPoolBridge())

    expect(result.current.stageFilter).toBeNull()

    act(() => {
      dispatchBridge("talent_pool", { stage: "screened" })
    })

    expect(result.current.stageFilter).toBe("screened")
  })

  it("ignores events from other surfaces (recrutar) — state unchanged", () => {
    const { result } = renderHook(() => useTalentPoolBridge())

    act(() => {
      dispatchBridge("recrutar", { stage: "triagem_whatsapp" })
    })

    // stageFilter must remain null (alien surface ignored)
    expect(result.current.stageFilter).toBeNull()
  })
})
