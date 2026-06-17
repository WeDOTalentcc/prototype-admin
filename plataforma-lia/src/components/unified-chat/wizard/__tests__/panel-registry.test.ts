/**
 * Sensor S2 — PANEL_REGISTRY: cobertura completa e integridade dos entries.
 * Complementa DynamicContextPanel.panel-registry.test.ts (foco em SPLIT_STAGES ↔ PANEL_REGISTRY).
 * Este arquivo testa o PANEL_REGISTRY diretamente (entradas válidas, sem nulls).
 */
import { PANEL_REGISTRY } from "../DynamicContextPanel"

describe("PANEL_REGISTRY — integridade dos entries", () => {
  it("PANEL_REGISTRY tem pelo menos um painel registrado", () => {
    expect(Object.keys(PANEL_REGISTRY).length).toBeGreaterThan(0)
  })

  it("todo entry do PANEL_REGISTRY tem componente definido (não null/undefined)", () => {
    const nullEntries = Object.entries(PANEL_REGISTRY)
      .filter(([, v]) => v == null)
      .map(([k]) => k)
    expect(nullEntries).toEqual([])
  })

  it("keys do PANEL_REGISTRY são strings não-vazias", () => {
    for (const key of Object.keys(PANEL_REGISTRY)) {
      expect(key.length).toBeGreaterThan(0)
    }
  })
})
