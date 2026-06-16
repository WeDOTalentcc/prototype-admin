/**
 * Task #826 — verifies the helpers that drive the non-persisted
 * "Plano de trabalho" assistant card injected into the chat feed.
 *
 * Pure logic, no DOM: the helpers must keep the visible plan steps in
 * lockstep with the canonical `STAGE_ORDER` from `wizard-types.ts`. Any
 * drift would either show a wrong step as active or skip the
 * highlight entirely.
 */
import { describe, it, expect } from "vitest"
import {
  PLAN_VISIBLE_STAGES,
  WIZARD_CLOSING_STAGES,
  WIZARD_PLAN_COMPLETED_SUFFIX,
  WIZARD_PLAN_COMPLETED_TITLE,
  WIZARD_PLAN_MESSAGE_ID,
  WIZARD_PLAN_TITLE,
  WIZARD_PUBLISHED_MESSAGE_ID,
  WIZARD_PUBLISHED_TITLE,
  buildPlanFlowSteps,
  buildPublishedJobCard,
  isWizardClosingStage,
  planCardTitleForStage,
  planStepsEqual,
  publishedJobCardsEqual,
} from "../wizard-plan-card"
import { STAGE_LABELS } from "../wizard-types"

describe("buildPlanFlowSteps", () => {
  it("renders all six visible stages as pending when no stage is set", () => {
    const steps = buildPlanFlowSteps(null)
    expect(steps).toHaveLength(6)
    expect(steps.every((s) => s.status === "pending")).toBe(true)
    expect(steps.map((s) => s.id)).toEqual([...PLAN_VISIBLE_STAGES])
  })

  it("uses canonical STAGE_LABELS for every step (no parallel label table)", () => {
    const steps = buildPlanFlowSteps("competency")
    for (const step of steps) {
      expect(step.label).toBe(STAGE_LABELS[step.id as keyof typeof STAGE_LABELS])
    }
  })

  it("marks earlier visible stages completed and later ones pending", () => {
    const steps = buildPlanFlowSteps("wsi_questions")
    const byId = Object.fromEntries(steps.map((s) => [s.id, s.status]))
    expect(byId.jd_enrichment).toBe("completed")
    expect(byId.competency).toBe("completed")
    expect(byId.wsi_questions).toBe("in_progress")
    expect(byId.review).toBe("pending")
    expect(byId.publish).toBe("pending")
    expect(byId.calibration).toBe("pending")
  })

  it("treats hidden stages (intake, bigfive, salary) as 'before any visible step'", () => {
    // Intake precedes jd_enrichment in STAGE_ORDER, so all visible steps are
    // still pending — no false 'completed' marks for hidden stages.
    const steps = buildPlanFlowSteps("intake")
    expect(steps.every((s) => s.status === "pending")).toBe(true)
  })

  it("highlights calibration as the in-progress step at the end of the visible window", () => {
    const steps = buildPlanFlowSteps("calibration")
    const cal = steps.find((s) => s.id === "calibration")
    expect(cal?.status).toBe("in_progress")
    // Every visible stage before calibration should be completed.
    const before = steps.filter((s) => s.id !== "calibration")
    expect(before.every((s) => s.status === "completed")).toBe(true)
  })

  // Task #830 — terminal stages must mark every visible step as completed
  // so the chat-feed plan card stops looking like calibration is still
  // running once the wizard reaches `done`/`handoff`.
  it("marks every visible step as completed at the terminal `done` stage", () => {
    const steps = buildPlanFlowSteps("done")
    expect(steps).toHaveLength(6)
    expect(steps.map((s) => s.id)).toEqual([...PLAN_VISIBLE_STAGES])
    expect(steps.every((s) => s.status === "completed")).toBe(true)
  })

  it("marks every visible step as completed at the terminal `handoff` stage", () => {
    const steps = buildPlanFlowSteps("handoff")
    expect(steps).toHaveLength(6)
    expect(steps.every((s) => s.status === "completed")).toBe(true)
    // Calibration must not stay frozen on `in_progress` here — that was
    // the exact regression Task #830 fixes.
    const cal = steps.find((s) => s.id === "calibration")
    expect(cal?.status).toBe("completed")
  })
})

describe("planCardTitleForStage", () => {
  it("returns the canonical title for null and any non-terminal stage", () => {
    expect(planCardTitleForStage(null)).toBe(WIZARD_PLAN_TITLE)
    expect(planCardTitleForStage("intake")).toBe(WIZARD_PLAN_TITLE)
    expect(planCardTitleForStage("calibration")).toBe(WIZARD_PLAN_TITLE)
  })

  it("returns the 'Concluído' variant for terminal stages", () => {
    expect(planCardTitleForStage("done")).toBe(WIZARD_PLAN_COMPLETED_TITLE)
    expect(planCardTitleForStage("handoff")).toBe(WIZARD_PLAN_COMPLETED_TITLE)
  })

  it("composes the completed title from the canonical pieces (no parallel literal)", () => {
    expect(WIZARD_PLAN_COMPLETED_SUFFIX).toBe("Concluído")
    expect(WIZARD_PLAN_COMPLETED_TITLE).toBe(
      `${WIZARD_PLAN_TITLE} — ${WIZARD_PLAN_COMPLETED_SUFFIX}`,
    )
  })
})

describe("planStepsEqual", () => {
  it("returns true for two identical plan-step arrays", () => {
    const a = buildPlanFlowSteps("competency")
    const b = buildPlanFlowSteps("competency")
    expect(planStepsEqual(a, b)).toBe(true)
  })

  it("returns false when any step status differs", () => {
    const a = buildPlanFlowSteps("competency")
    const b = buildPlanFlowSteps("wsi_questions")
    expect(planStepsEqual(a, b)).toBe(false)
  })

  it("returns false on length mismatch", () => {
    const a = buildPlanFlowSteps("competency")
    expect(planStepsEqual(a, a.slice(0, 3))).toBe(false)
  })
})

describe("plan-card constants", () => {
  it("exposes a stable virtual-message id so re-renders update in place", () => {
    expect(WIZARD_PLAN_MESSAGE_ID).toBe("lia-wizard-plan-card")
  })

  it("exposes the user-facing title", () => {
    expect(WIZARD_PLAN_TITLE).toBe("Plano de trabalho")
  })

  it("exposes exactly the six visible stages the WizardProgressBar surfaces", () => {
    expect(PLAN_VISIBLE_STAGES).toEqual([
      "jd_enrichment",
      "competency",
      "wsi_questions",
      "review",
      "publish",
      "calibration",
    ])
  })
})

describe("isWizardClosingStage", () => {
  it("recognises both terminal stages emitted by the backend", () => {
    expect(isWizardClosingStage("handoff")).toBe(true)
    expect(isWizardClosingStage("done")).toBe(true)
  })

  it("returns false for null and for any non-terminal stage", () => {
    expect(isWizardClosingStage(null)).toBe(false)
    expect(isWizardClosingStage("intake")).toBe(false)
    expect(isWizardClosingStage("publish")).toBe(false)
    expect(isWizardClosingStage("calibration")).toBe(false)
  })

  it("keeps the closing-stage list in sync with the constant export", () => {
    expect([...WIZARD_CLOSING_STAGES]).toEqual(["handoff", "done"])
  })
})

describe("buildPublishedJobCard", () => {
  it("returns null for non-closing stages so the chat surface skips injection", () => {
    expect(buildPublishedJobCard(null, {})).toBeNull()
    expect(buildPublishedJobCard("intake", { job_id: 42 })).toBeNull()
    expect(buildPublishedJobCard("publish", { job_id: 42 })).toBeNull()
  })

  it("extracts title, id, url and share link from a handoff payload", () => {
    const card = buildPublishedJobCard("handoff", {
      job_id: 7,
      job_title: "Engenheiro de Software Pleno",
      handoff_url: "/jobs/7",
      share_link: "https://wedo.example/share/abc",
    })
    expect(card).toEqual({
      jobId: 7,
      title: "Engenheiro de Software Pleno",
      url: "/jobs/7",
      shareLink: "https://wedo.example/share/abc",
    })
  })

  it("não deriva link client-side; confia no producer (handoff_url) — post-mortem dad2bfec4", () => {
    // Canonical (2026-04-29 + commit dad2bfec4 "remove orphan /jobs URLs"):
    // não existe rota de página /jobs/<id> (só API proxy), então derivar
    // client-side gerava 404. O card confia no handoff_url do backend; ausente => null.
    const card = buildPublishedJobCard("done", {
      job_id: 12,
      job_title: "Designer de Produto",
    })
    expect(card?.url).toBeNull()
    expect(card?.shareLink).toBeNull()
  })

  it("returns null fields rather than blanks/undefined so the UI can hide them safely", () => {
    const card = buildPublishedJobCard("handoff", {
      job_id: null,
      job_title: "   ",
      handoff_url: "",
      share_link: undefined,
    })
    expect(card).toEqual({ jobId: null, title: null, url: null, shareLink: null })
  })

  it("accepts string job_id (UUID/slug) so future backend ID format changes don't drop the ID", () => {
    const card = buildPublishedJobCard("handoff", {
      job_id: "uuid-abc-123",
      job_title: "Engenheiro de Dados",
    })
    expect(card).toEqual({
      jobId: "uuid-abc-123",
      title: "Engenheiro de Dados",
      url: null,
      shareLink: null,
    })
  })

  it("collapses empty/whitespace string job_id to null instead of building /jobs/", () => {
    const card = buildPublishedJobCard("handoff", { job_id: "   " })
    expect(card).toEqual({ jobId: null, title: null, url: null, shareLink: null })
  })

  it("ignores non-string non-number job_title without throwing", () => {
    const card = buildPublishedJobCard("handoff", {
      job_id: 7,
      job_title: 42 as unknown as string,
    })
    expect(card).toEqual({ jobId: 7, title: null, url: null, shareLink: null })
  })
})

describe("publishedJobCardsEqual", () => {
  it("returns true for structurally identical cards", () => {
    const a = buildPublishedJobCard("handoff", { job_id: 1, job_title: "X", handoff_url: "/jobs/1" })
    const b = buildPublishedJobCard("handoff", { job_id: 1, job_title: "X", handoff_url: "/jobs/1" })
    expect(publishedJobCardsEqual(a, b)).toBe(true)
  })

  it("returns false when any visible field changes", () => {
    const a = buildPublishedJobCard("handoff", { job_id: 1, job_title: "X", handoff_url: "/jobs/1" })
    const b = buildPublishedJobCard("handoff", { job_id: 1, job_title: "Y", handoff_url: "/jobs/1" })
    expect(publishedJobCardsEqual(a, b)).toBe(false)
  })

  it("treats null and a card as different (so the very first emit triggers a render)", () => {
    const a = buildPublishedJobCard("handoff", { job_id: 1 })
    expect(publishedJobCardsEqual(null, a)).toBe(false)
    expect(publishedJobCardsEqual(a, null)).toBe(false)
    expect(publishedJobCardsEqual(null, null)).toBe(true)
  })
})

describe("published-card constants", () => {
  it("exposes a stable virtual-message id distinct from the plan card", () => {
    expect(WIZARD_PUBLISHED_MESSAGE_ID).toBe("lia-wizard-published-card")
    expect(WIZARD_PUBLISHED_MESSAGE_ID).not.toBe(WIZARD_PLAN_MESSAGE_ID)
  })

  it("exposes the user-facing closing title", () => {
    expect(WIZARD_PUBLISHED_TITLE).toBe("Vaga publicada")
  })
})
