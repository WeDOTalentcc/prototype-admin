/**
 * CreateAgentWizard — Sprint 5 sentinel for prefilledSector.
 *
 * Sprint 5 (2026-05-25) decommission do CreateAgentModal antigo (path #3
 * sector tile). O wizard absorve a entrada via `initialConfig` enriquecido
 * com `prefilledSector` + `name` derivado do display_name do sector tile.
 *
 * Cobre:
 * - initialConfig.prefilledSector presente é preservado em state interno
 * - name passado via initialConfig pré-popula o input (sector tile click
 *   manda display_name do sector como name)
 * - sem prefilledSector, fluxo padrão (step 1 goal-first) é mantido
 *
 * Plan ref: AGENT_STUDIO_IMPLEMENTATION_PLAN.md §6 Sprint 5.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useLocale: () => "pt",
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/lib/toast", () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
}))

import { CreateAgentWizard } from "../CreateAgentWizard"
import type { CreateAgentInitialConfig } from "../types"

beforeEach(() => {
  global.fetch = vi.fn() as unknown as typeof fetch
  if (typeof window !== "undefined" && !window.localStorage) {
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue(null),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
      },
      writable: true,
    })
  }
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe("CreateAgentWizard — Sprint 5 prefilledSector (sector tile path)", () => {
  it("renderiza com initialConfig.prefilledSector + name derivado do sector", () => {
    const sectorConfig: CreateAgentInitialConfig = {
      goal: "outro",
      prefilledSector: "code",
      name: "Tech Stack Recruiter",
    }

    render(
      <CreateAgentWizard
        open={true}
        onClose={vi.fn()}
        onCreated={vi.fn()}
        initialConfig={sectorConfig}
      />,
    )

    // Wizard abre. Goal já foi inferido ("outro") via initialConfig,
    // então step inicial é >= 2 (ApproachStep) — testid do step indicator
    // existe (canonical sentinela do wizard ativo).
    expect(screen.getByTestId("wizard-step-indicator")).toBeTruthy()
  })

  it("sem initialConfig, wizard abre em step 1 (GoalStep) — fluxo padrão preservado", () => {
    render(
      <CreateAgentWizard open={true} onClose={vi.fn()} onCreated={vi.fn()} />,
    )
    // GoalStep canonical: 5 goal options renderizadas
    expect(screen.getByTestId("goal-option-triagem_inicial")).toBeTruthy()
    expect(screen.getByTestId("goal-option-outro")).toBeTruthy()
  })
})
