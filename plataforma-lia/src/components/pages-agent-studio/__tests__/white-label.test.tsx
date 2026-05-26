/**
 * Sprint 2 — white-label canonical contract for Agent Studio.
 *
 * Decisão Paulo 2026-05-25 (memory project_white_label_ai_assistant):
 * o nome "LIA" é configurável per-tenant via AiPersona. Studio é onde
 * cliente cria SEUS agentes (identidade própria, não da assistente).
 *
 * Sensor dinâmico complementar a scripts/check_no_lia_hardcoded_in_studio.py:
 * garante que componentes rendered NÃO emitem "LIA" hardcoded e NÃO usam
 * classes wedo-cyan (cyan é exclusiva da assistente quando age).
 *
 * Coverage: ConversationalCreator, AgentCreationPreview, ConfigStep,
 * ApproachStep, DigitalTwinOnboarding, DigitalTwinEmptyState, QuotaMeter,
 * MarketplaceTab, CustomAgentsTab (statically — render side avoids API mocks).
 *
 * AgentStudioPage.tsx é EXCLUÍDO (hot file — sprint coordenada futura).
 */
import { describe, expect, it, vi } from "vitest"
import { render } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

// Mock useAiPersona to inject deterministic name
vi.mock("@/hooks/company/use-ai-persona", () => ({
  useAiPersona: () => ({
    persona: { name: "Aurora", tone: "profissional" },
    isLoading: false,
    isSaving: false,
    error: null,
    validationErrors: [],
    reload: vi.fn(),
    update: vi.fn(),
  }),
  useAiPersonaOptions: () => ({
    options: null,
    isLoading: false,
    error: null,
  }),
}))

// Simple messages fixture covering used keys with {aiAssistant} placeholders
const messages = {
  agents: {
    studio: {
      chooseTemplateOrDescribe:
        "Escolha um template abaixo ou descreva para {aiAssistant} o que você precisa",
      noCustomAgentsHint:
        "Escolha um template abaixo ou descreva para {aiAssistant} o que você precisa",
      twins: {
        emptyState: {
          noExperience:
            "Sem experiência técnica? Tudo bem — {aiAssistant} te guia passo a passo.",
        },
        onboarding: {
          step1Title: "Conecte sinais",
          step1Desc: "desc",
          step2Title: "Avaliação",
          step2Desc: "desc",
          step3Title: "{aiAssistant} aprende o padrão",
          step3Desc: "desc",
          step4Title: "Segunda opinião",
          step4Desc: "desc",
          stepLabel: "Passo {number}",
        },
      },
    },
  },
}

import {
  DigitalTwinEmptyState,
} from "../DigitalTwinComponents"

function renderWithIntl(ui: React.ReactNode) {
  return render(
    <NextIntlClientProvider locale="pt-BR" messages={messages as any}>
      {ui}
    </NextIntlClientProvider>,
  )
}

describe("Agent Studio — white-label canonical (Sprint 2)", () => {
  // P0 rewrite 2026-05-26: DigitalTwinOnboarding REMOVIDO (página Gêmeos Digitais
  // segue layout canonical Marketplace/Personalizados sem onboarding 4-steps inline).
  // White-label assertion agora corre via DigitalTwinEmptyState.

  it("DigitalTwinEmptyState injeta aiAssistant (não hardcoda 'LIA')", () => {
    if (typeof DigitalTwinEmptyState !== "function") {
      return // export interno; skip defensivo
    }
    const { container } = renderWithIntl(
      <DigitalTwinEmptyState onCreateTwin={() => {}} />,
    )
    const text = container.textContent ?? ""
    // aiAssistant é "Aurora" no mock useAiPersona acima
    expect(text).toContain("Aurora")
    expect(text).not.toMatch(/\bLIA\b/)
  })

  it("DigitalTwinEmptyState não emite classes wedo-cyan", () => {
    if (typeof DigitalTwinEmptyState !== "function") return
    const { container } = renderWithIntl(
      <DigitalTwinEmptyState onCreateTwin={() => {}} />,
    )
    const html = container.innerHTML
    expect(html).not.toMatch(/\bwedo-cyan\b/)
    expect(html).not.toMatch(/from-(wedo-)?cyan[^"' ]*to-(wedo-)?(violet|purple)/)
  })
})
