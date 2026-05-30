/**
 * Task #1112 — verifica que stages do wizard que rodaram em modo degradado
 * (`*_used_fallback=True` no payload do WS) ficam visíveis na ProgressBar
 * como um chip "IA degradada" e persistem mesmo após o wizard avançar.
 */
import React from "react"
import { describe, it, expect, beforeEach, afterEach } from "vitest"
import { render, screen, act, cleanup } from "@testing-library/react"

import {
  useWizardFlow,
  extractDegradedStage,
  FALLBACK_FLAG_BY_STAGE,
} from "../useWizardFlow"
import { WizardProgressBar } from "../WizardProgressBar"
import type { WizardStagePayload, WizardStage } from "../wizard-types"

function Harness() {
  const { currentStage, completeness, stageHistory, degradedStages } =
    useWizardFlow()
  if (!currentStage) return <div data-testid="bar-absent" />
  return (
    <WizardProgressBar
      currentStage={currentStage}
      completeness={completeness}
      stageHistory={stageHistory}
      degradedStages={degradedStages}
    />
  )
}

function dispatchStage(
  stage: WizardStage,
  data: Record<string, unknown>,
  completeness = 0.3,
) {
  const payload: WizardStagePayload = {
    type: "wizard_stage",
    stage,
    data,
    completeness,
    requires_approval: false,
  }
  window.dispatchEvent(
    new CustomEvent("lia:wizard-stage-payload", { detail: payload }),
  )
}

beforeEach(() => {
  localStorage.clear()
})

afterEach(() => {
  cleanup()
  localStorage.clear()
})

describe("extractDegradedStage", () => {
  it("returns the reason string when the flag is true and a reason is provided", () => {
    expect(
      extractDegradedStage("jd_enrichment", {
        jd_enrichment_used_fallback: true,
        jd_enrichment_fallback_reason: "timeout",
      }),
    ).toBe("timeout")
  })

  it("returns true when the flag is set but no reason is included", () => {
    expect(
      extractDegradedStage("salary", { salary_used_fallback: true }),
    ).toBe(true)
  })

  it("returns null when the flag is missing or false", () => {
    expect(extractDegradedStage("bigfive", {})).toBeNull()
    expect(
      extractDegradedStage("bigfive", { bigfive_used_fallback: false }),
    ).toBeNull()
  })

  it("returns null for stages without a known fallback flag", () => {
    expect(extractDegradedStage("review", { review_used_fallback: true })).toBeNull()
  })
})

describe("FALLBACK_FLAG_BY_STAGE", () => {
  it("covers exactly the 4 backend nodes that emit *_used_fallback", () => {
    // Espelho de `_WIZARD_FALLBACK_NODES` em
    // `lia-agent-system/app/domains/job_creation/graph.py`. Mudar este conjunto
    // sem atualizar o backend (ou vice-versa) deixa o badge da ProgressBar fora
    // de sincronia com o que o recrutador realmente vê no painel.
    expect(Object.keys(FALLBACK_FLAG_BY_STAGE).sort()).toEqual(
      ["bigfive", "jd_enrichment", "salary", "wsi_questions"].sort(),
    )
  })
})

describe("WizardProgressBar — degraded stage badge", () => {
  it("renders a per-stage badge when a stage payload sets *_used_fallback", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("jd_enrichment", {
        jd_enrichment_used_fallback: true,
        jd_enrichment_fallback_reason: "timeout",
      })
    })
    const badge = screen.getByTestId("wizard-progress-degraded-list-jd_enrichment")
    expect(badge).toBeTruthy()
    expect(badge.getAttribute("aria-label")).toMatch(/IA degradada/i)
    expect(badge.getAttribute("aria-label")).toMatch(/tempo esgotado/i)
    expect(screen.getByTestId("wizard-progress-degraded-summary")).toBeTruthy()
  })

  it("keeps the badge visible after the wizard advances to the next stage", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("jd_enrichment", {
        jd_enrichment_used_fallback: true,
      })
    })
    expect(
      screen.getByTestId("wizard-progress-degraded-list-jd_enrichment"),
    ).toBeTruthy()

    act(() => {
      dispatchStage("salary", { salary_min: 5000, salary_max: 8000 }, 0.6)
    })
    // Even though the salary payload did NOT mark itself as degraded, the
    // jd_enrichment badge must remain — the recruiter still needs to know
    // that the JD they already approved was generated in degraded mode.
    expect(
      screen.getByTestId("wizard-progress-degraded-list-jd_enrichment"),
    ).toBeTruthy()
    expect(screen.queryByTestId("wizard-progress-degraded-salary")).toBeNull()
  })

  it("shows no badge when no stage has flagged a fallback", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("intake", { raw_input: "Engenheiro Backend" })
    })
    expect(screen.queryByTestId("wizard-progress-degraded-summary")).toBeNull()
    expect(
      screen.queryByTestId("wizard-progress-degraded-jd_enrichment"),
    ).toBeNull()
  })

  it("aggregates the count when multiple stages fall back", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("jd_enrichment", { jd_enrichment_used_fallback: true })
    })
    act(() => {
      dispatchStage(
        "wsi_questions",
        { wsi_questions_used_fallback: true },
        0.6,
      )
    })
    const summary = screen.getByTestId("wizard-progress-degraded-summary")
    expect(summary.textContent).toMatch(/2 etapas/)
  })

  it("counts hidden stages (salary, bigfive) in the summary even though they have no dot", () => {
    // `salary` and `bigfive` are intentionally hidden from `PLAN_VISIBLE_STAGES`
    // (the dot row only shows the 6 high-level milestones), but they ARE
    // among the 4 backend nodes that emit `*_used_fallback`. Without
    // counting them here the recruiter would approve a salary band built
    // from a stale benchmark thinking the LLM signed off on it.
    render(<Harness />)
    act(() => {
      dispatchStage("salary", { salary_used_fallback: true }, 0.5)
    })
    const summary = screen.getByTestId("wizard-progress-degraded-summary")
    expect(summary.textContent).toMatch(/1 etapa/)
    expect(summary.getAttribute("data-hidden-count")).toBe("1")
    expect(
      screen.getByTestId("wizard-progress-degraded-list-salary"),
    ).toBeTruthy()
    // No dot-overlay badge for hidden stages — the dot row simply doesn't
    // render salary, so the chip would have nowhere to attach.
    expect(screen.queryByTestId("wizard-progress-degraded-salary")).toBeNull()
  })

  it("aggregates visible + hidden stage fallbacks into the same summary", () => {
    render(<Harness />)
    act(() => {
      dispatchStage("jd_enrichment", { jd_enrichment_used_fallback: true })
    })
    act(() => {
      dispatchStage("salary", { salary_used_fallback: true }, 0.5)
    })
    const summary = screen.getByTestId("wizard-progress-degraded-summary")
    expect(summary.textContent).toMatch(/2 etapas/)
    expect(summary.getAttribute("data-visible-count")).toBe("1")
    expect(summary.getAttribute("data-hidden-count")).toBe("1")
    expect(
      screen.getByTestId("wizard-progress-degraded-list-jd_enrichment"),
    ).toBeTruthy()
    expect(
      screen.getByTestId("wizard-progress-degraded-list-salary"),
    ).toBeTruthy()
  })
})
