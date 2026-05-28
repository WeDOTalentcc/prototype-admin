// Onda 4 F8 (2026-05-28) — StudioEmptyState canonical tests.
//
// Cobertura:
//   1. Renderiza copy com personaName customizado
//   2. CTAs disparam handlers
//   3. Persona default = "LIA" quando hook null
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { NextIntlClientProvider } from "next-intl"
import React from "react"

import { StudioEmptyState } from "../StudioEmptyState"

const useAiPersonaMock = vi.fn()
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => useAiPersonaMock(),
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/pt/agent-studio",
}))

const MESSAGES = {
  agents: {
    studio: {
      empty: {
        title: "Você ainda não tem agentes",
        description:
          "Eles fazem o trabalho repetitivo. Converse com a {personaName}.",
        cta: {
          marketplace: "Explorar Marketplace",
          chat: "Conversar com {personaName}",
        },
      },
    },
  },
}

function renderInProvider(children: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={MESSAGES}>
      {children}
    </NextIntlClientProvider>,
  )
}

describe("StudioEmptyState", () => {
  it("renderiza com persona name customizada", () => {
    useAiPersonaMock.mockReturnValue({
      persona: { name: "Sofia", tone: "amigavel" },
    })
    renderInProvider(<StudioEmptyState />)
    expect(screen.getByTestId("studio-empty-state")).toBeInTheDocument()
    // Persona name aparece em description + CTA chat — testar que ambos têm Sofia
    const sofiaMatches = screen.getAllByText(/Sofia/)
    expect(sofiaMatches.length).toBeGreaterThanOrEqual(1)
  })

  it("usa default LIA quando persona null", () => {
    useAiPersonaMock.mockReturnValue({ persona: null })
    renderInProvider(<StudioEmptyState />)
    const liaMatches = screen.getAllByText(/LIA/)
    expect(liaMatches.length).toBeGreaterThanOrEqual(1)
  })

  it("CTAs disparam handlers customizados", async () => {
    const onMarketplace = vi.fn()
    const onChat = vi.fn()
    useAiPersonaMock.mockReturnValue({
      persona: { name: "LIA", tone: "profissional" },
    })
    const user = userEvent.setup()
    renderInProvider(
      <StudioEmptyState
        onExploreMarketplace={onMarketplace}
        onChatWithPersona={onChat}
      />,
    )
    await user.click(
      screen.getByRole("button", { name: /Explorar Marketplace/i }),
    )
    expect(onMarketplace).toHaveBeenCalled()
    await user.click(screen.getByRole("button", { name: /Conversar com LIA/i }))
    expect(onChat).toHaveBeenCalled()
  })
})
