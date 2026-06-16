/**
 * Task #835 — guards the inline "Plano de trabalho" `WizardPlanFeedCard`
 * component (originally rendered by the deprecated `expanded-chat-modal`,
 * which was removed in Task #860 — A-01).
 *
 * The historical bug: the legacy expanded surface gated the card on
 * `canonicalWizardActive` — i.e. it disappeared the moment the wizard
 * reached `done`/`handoff`. The fix keeps the card visible at terminal
 * stages with all six steps marked completed and the title flipped to
 * "Plano de trabalho — Concluído". The same behaviour was applied to the
 * canonical `/pt/chat` (UnifiedChat) surface in Task #830. This test pins
 * the component's behaviour so future callers can't regress it.
 *
 * The component is a thin wrapper over `buildPlanFlowSteps` +
 * `planCardTitleForStage`; the helper logic itself is covered by
 * `wizard-plan-card.test.ts`.
 */
import React from "react"
import { describe, it, expect, afterEach } from "vitest"
import { render, screen, cleanup, within } from "@testing-library/react"

import { WizardPlanFeedCard } from "../WizardPlanFeedCard"
import {
  WIZARD_PLAN_TITLE,
  WIZARD_PLAN_COMPLETED_TITLE,
} from "../wizard-plan-card"
import { STAGE_LABELS } from "../wizard-types"

afterEach(() => {
  cleanup()
})

describe("WizardPlanFeedCard — expanded chat surface (Task #835)", () => {
  it("does NOT mount before any wizard_stage event arrives (currentStage = null)", () => {
    const { container } = render(<WizardPlanFeedCard currentStage={null} />)
    expect(container.firstChild).toBeNull()
    expect(screen.queryByTestId("wizard-plan-card")).toBeNull()
  })

  it("renders the canonical 'Plano de trabalho' title at non-terminal stages", () => {
    render(<WizardPlanFeedCard currentStage="competency" />)
    const card = screen.getByTestId("wizard-plan-card")
    expect(card).toBeTruthy()
    expect(within(card).getByText(WIZARD_PLAN_TITLE)).toBeTruthy()
    // The 'Concluído' suffix must NOT be visible at a non-terminal stage.
    expect(within(card).queryByText(/Concluído/i)).toBeNull()
  })

  it("STAYS mounted and flips to 'Plano de trabalho — Concluído' at the terminal `done` stage", () => {
    // This is the exact regression Task #835 fixes for the expanded chat:
    // before the fix the surface gated the card on wizardActive (which
    // excludes `done`/`handoff`), so the card vanished here.
    render(<WizardPlanFeedCard currentStage="done" />)
    const card = screen.getByTestId("wizard-plan-card")
    expect(card).toBeTruthy()
    expect(within(card).getByText(WIZARD_PLAN_COMPLETED_TITLE)).toBeTruthy()
  })

  it("STAYS mounted and flips to the 'Concluído' title at the terminal `handoff` stage", () => {
    render(<WizardPlanFeedCard currentStage="handoff" />)
    const card = screen.getByTestId("wizard-plan-card")
    expect(card).toBeTruthy()
    expect(within(card).getByText(WIZARD_PLAN_COMPLETED_TITLE)).toBeTruthy()
  })

  it("renders all six visible plan-step labels at terminal stages", () => {
    render(<WizardPlanFeedCard currentStage="handoff" />)
    const card = screen.getByTestId("wizard-plan-card")
    // The labels come from the canonical STAGE_LABELS table — render every
    // visible step so the recruiter sees the whole "concluded" plan.
    for (const stage of [
      "jd_enrichment",
      "competency",
      "wsi_questions",
      "review",
      "publish",
      "calibration",
    ] as const) {
      expect(within(card).getByText(STAGE_LABELS[stage])).toBeTruthy()
    }
  })

  it("renders no spinning (in-progress) chip at the terminal stage", () => {
    // Mirrors the e2e assertion in wizard-plan-card.spec.ts: once the
    // wizard reports `done`, every visible step must read as completed,
    // never as still in progress.
    const { container } = render(<WizardPlanFeedCard currentStage="done" />)
    const spinners = container.querySelectorAll("svg.animate-spin")
    expect(spinners.length).toBe(0)
  })
})
