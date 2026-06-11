// @vitest-environment jsdom
import { describe, it, expect } from "vitest"
import { wizardPanelVisibility } from "../panel-visibility"

describe("wizardPanelVisibility — Manus F1", () => {
  it("docked: dock visível, painel oculto", () => {
    expect(wizardPanelVisibility({ stage: "wsi_questions", mode: "docked" }))
      .toEqual({ showPanel: false, showDock: true })
  })
  it("expanded: painel visível, dock oculto", () => {
    expect(wizardPanelVisibility({ stage: "wsi_questions", mode: "expanded" }))
      .toEqual({ showPanel: true, showDock: false })
  })
  it("stage não-split (pipeline_template) não mostra nada", () => {
    expect(wizardPanelVisibility({ stage: "pipeline_template", mode: "expanded" }))
      .toEqual({ showPanel: false, showDock: false })
  })
  it("sem stage não mostra nada", () => {
    expect(wizardPanelVisibility({ stage: null, mode: "docked" }))
      .toEqual({ showPanel: false, showDock: false })
  })
})
