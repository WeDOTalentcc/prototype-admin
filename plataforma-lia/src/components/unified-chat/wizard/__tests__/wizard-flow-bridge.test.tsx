/**
 * Task #826 — verifies the canonical wiring between the
 * `lia:wizard-stage-payload` window event, the `useWizardFlow` hook, and
 * the `WizardProgressBar`. Without this bridge the chat surface stays
 * blind to wizard progress even when the backend is faithfully emitting
 * `ws_stage_payload` for every stage transition.
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach } from "vitest"
import { render, screen, act, cleanup } from "@testing-library/react"

import { useWizardFlow } from "../useWizardFlow"
import { WizardProgressBar } from "../WizardProgressBar"
import { STAGE_LABELS, type WizardStagePayload, type WizardStage } from "../wizard-types"

function Harness() {
  const { currentStage, completeness, stageHistory } = useWizardFlow()
  const active =
    currentStage !== null && currentStage !== "done" && currentStage !== "handoff"
  if (!active) return <div data-testid="bar-absent" />
  return (
    <div data-testid="bar-present">
      <WizardProgressBar
        currentStage={currentStage}
        completeness={completeness}
        stageHistory={stageHistory}
      />
    </div>
  )
}

function dispatchStage(stage: WizardStage, completeness: number) {
  const payload: WizardStagePayload = {
    type: "wizard_stage",
    stage,
    data: {},
    completeness,
    requires_approval: false,
  }
  window.dispatchEvent(
    new CustomEvent("lia:wizard-stage-payload", { detail: payload }),
  )
}

beforeEach(() => {
  // The hook persists state to localStorage; clear between tests so each
  // case starts from a clean slate.
  localStorage.clear()
})

afterEach(() => {
  cleanup()
  localStorage.clear()
})

describe("Wizard flow bridge — useWizardFlow + WizardProgressBar", () => {
  it("does not render the bar before any wizard_stage event arrives", () => {
    render(<Harness />)
    expect(screen.getByTestId("bar-absent")).toBeTruthy()
  })

  it("mounts the bar after intake (etapas vivem no plan card do chat, não na barra)", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("intake", 0.05)
    })
    expect(screen.getByTestId("bar-present")).toBeTruthy()
    // Stepper redundante removido (2026-05-30): os labels das 6 etapas saíram
    // da barra e agora vivem no plan card do chat (synthetic message via
    // useWizardChatCards). A barra mantém só progresso% + cancelar + degradado.
    expect(screen.queryByText(STAGE_LABELS.calibration)).toBeNull()
  })

  it("mantém a barra montada conforme novos stages chegam (avanço por etapa vive no plan card)", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("intake", 0.05)
    })
    act(() => {
      dispatchStage("jd_enrichment", 0.2)
    })
    // Barra continua montada entre stages; o avanço visual por etapa (labels)
    // agora é responsabilidade do plan card do chat, não da barra.
    expect(screen.getByTestId("bar-present")).toBeTruthy()
    expect(screen.queryByText(STAGE_LABELS.jd_enrichment)).toBeNull()
  })

  it("unmounts the bar when the wizard reaches handoff", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("intake", 0.05)
    })
    expect(screen.getByTestId("bar-present")).toBeTruthy()
    act(() => {
      dispatchStage("handoff", 1.0)
    })
    expect(screen.getByTestId("bar-absent")).toBeTruthy()
  })

  it("unmounts the bar when the wizard reaches done", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("intake", 0.05)
    })
    act(() => {
      dispatchStage("done", 1.0)
    })
    expect(screen.getByTestId("bar-absent")).toBeTruthy()
  })

  it("ignores malformed payloads without throwing or mutating state", () => {
    render(<Harness />)
    act(() => {
      // Wrong type — reducer must not run.
      window.dispatchEvent(
        new CustomEvent("lia:wizard-stage-payload", {
          detail: { type: "panel_update", stage: "intake" },
        }),
      )
    })
    expect(screen.getByTestId("bar-absent")).toBeTruthy()
    act(() => {
      // Missing stage — also ignored.
      window.dispatchEvent(
        new CustomEvent("lia:wizard-stage-payload", {
          detail: { type: "wizard_stage" },
        }),
      )
    })
    expect(screen.getByTestId("bar-absent")).toBeTruthy()
  })
})
