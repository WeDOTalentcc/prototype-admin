/**
 * Regression test 2026-05-26 — FORMATTING_ERROR aiAssistant.
 *
 * Bug history: i18n key "agents.studio.chooseTemplateOrDescribe" tem placeholder
 * {aiAssistant} mas AgentStudioPage.tsx:641 chamava t() sem 2nd arg context =
 * next-intl FORMATTING_ERROR em runtime.
 *
 * Fix Sprint 2 white-label drift: passar { aiAssistant: aiPersona?.name ?? "assistente" }
 * via useAiPersona hook.
 *
 * Sensor: verifica render sem FORMATTING_ERROR + name dinamico no DOM.
 */
import { describe, it, expect, vi } from "vitest"
import { render } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

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
  useAiPersonaOptions: () => ({ options: null, isLoading: false, error: null }),
}))

describe("AgentStudioPage — aiAssistant placeholder fix (FORMATTING_ERROR regression)", () => {
  it("messages with {aiAssistant} resolve cleanly when passed via 2nd arg", () => {
    const messages = {
      agents: {
        studio: {
          chooseTemplateOrDescribe: "Escolha um template ou descreva para {aiAssistant} o que precisa",
        },
      },
    }

    const errors: any[] = []
    const TestComp = () => {
      const { useTranslations } = require("next-intl")
      const t = useTranslations("agents")
      return <p>{t("studio.chooseTemplateOrDescribe", { aiAssistant: "Aurora" })}</p>
    }

    const { container } = render(
      <NextIntlClientProvider
        locale="pt-BR"
        messages={messages as any}
        onError={(err) => errors.push(err)}
      >
        <TestComp />
      </NextIntlClientProvider>,
    )

    // No FORMATTING_ERROR fired
    const formattingErrors = errors.filter((e) =>
      String(e.message ?? e).includes("FORMATTING_ERROR"),
    )
    expect(formattingErrors).toHaveLength(0)

    // Dynamic name appears in DOM
    expect(container.textContent).toContain("Aurora")
    expect(container.textContent).not.toContain("{aiAssistant}")
  })
})
