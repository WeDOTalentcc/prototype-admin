/**
 * CreateAgentWizard — P1-2 elevation tonal sentinel (2026-05-26).
 *
 * Garante que o modal "Vamos criar seu agente" renderiza com lift
 * tonal canonical (border-medium + shadow-lia-lg + rounded-xl) pra
 * sensação "levemente 3D" alinhada com cards StudioCardShell.
 */

import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useLocale: () => "pt",
  useTranslations: () => (key: string) => key,
}))

vi.mock("@/services/api/api-client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
  },
}))

import { CreateAgentWizard } from "../CreateAgentWizard"

describe("CreateAgentWizard — P1-2 elevation tonal", () => {
  it("DialogContent tem border-lia-border-medium (lift mais visível)", () => {
    render(<CreateAgentWizard open onClose={vi.fn()} />)
    const dc = screen.getByTestId("create-agent-wizard")
    expect(dc.className).toContain("border-lia-border-medium")
  })

  it("DialogContent tem shadow-lia-lg (canonical lift sutil)", () => {
    render(<CreateAgentWizard open onClose={vi.fn()} />)
    const dc = screen.getByTestId("create-agent-wizard")
    expect(dc.className).toContain("shadow-lia-lg")
  })

  it("DialogContent tem rounded-xl canonical", () => {
    render(<CreateAgentWizard open onClose={vi.fn()} />)
    const dc = screen.getByTestId("create-agent-wizard")
    expect(dc.className).toContain("rounded-xl")
  })

  it("Etapa 1 (goal selection) renderiza sem crash", () => {
    render(<CreateAgentWizard open onClose={vi.fn()} />)
    expect(screen.getByTestId("wizard-step-indicator")).toBeTruthy()
  })
})
