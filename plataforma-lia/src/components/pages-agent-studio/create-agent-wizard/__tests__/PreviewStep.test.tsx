/**
 * P2+P3 (Paulo 2026-05-30) — PreviewStep limpo.
 *
 *  - P3: mostra capacidades em PT (summarizeCapabilities), NÃO slugs crus de
 *    tools (search_candidates, ...). Objetivo reflete o template, não
 *    "Outro / criar do zero".
 *  - P2: nota de rodapé usa a chave i18n nova (sem jargão "editor avançado").
 */
import { describe, expect, it, vi } from "vitest"
import { render, screen } from "@testing-library/react"

vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, unknown>) => {
    if (vars && "count" in vars) return `${key} (${vars.count})`
    return key
  },
}))

const TEMPLATE = {
  id: "tpl-x",
  slug: "tpl-x",
  name: "Triagem Tech",
  description: "Triagem técnica",
  category: "screening",
  domain: "screening",
  system_prompt: "p",
  allowed_tools: ["search_candidates", "get_candidate_details", "get_evaluation_criteria", "create_note"],
  context_level: "standard",
  max_steps: 8,
  temperature: 0.5,
  tags: [],
}

vi.mock("@/hooks/agents/use-legacy-agent-templates", () => ({
  useLegacyAgentTemplates: () => ({ templates: [TEMPLATE], isLoading: false, error: null }),
}))

import { PreviewStep } from "../steps/PreviewStep"

const baseConfig: any = { name: "", templateId: TEMPLATE.id, aiDescription: "" }

describe("PreviewStep — P2+P3 clean summary", () => {
  it("NÃO renderiza slugs crus de tools", () => {
    render(
      <PreviewStep goal="outro" approach="template" config={baseConfig} aiPreview={null} />,
    )
    expect(screen.queryByText("search_candidates")).toBeNull()
    expect(screen.queryByText("get_evaluation_criteria")).toBeNull()
    expect(screen.queryByText("create_note")).toBeNull()
  })

  it("renderiza capacidades em PT (summarizeCapabilities)", () => {
    render(
      <PreviewStep goal="outro" approach="template" config={baseConfig} aiPreview={null} />,
    )
    // Bullet de capacidade de alto nível (grupo "find"/"analyze").
    expect(screen.getByText(/Encontra os candidatos certos/i)).toBeTruthy()
    expect(screen.getByText(/Analisa perfis com base/i)).toBeTruthy()
  })

  it("objetivo reflete o template, não 'Outro / criar do zero'", () => {
    render(
      <PreviewStep goal="outro" approach="template" config={baseConfig} aiPreview={null} />,
    )
    const step = screen.getByTestId("preview-step")
    expect(step.textContent).toContain("Triagem Tech")
    expect(step.textContent).not.toMatch(/criar do zero/i)
  })

  it("usa a chave i18n nova de rodapé (sem 'editor avançado')", () => {
    render(
      <PreviewStep goal="outro" approach="template" config={baseConfig} aiPreview={null} />,
    )
    const step = screen.getByTestId("preview-step")
    // O mock de next-intl ecoa a chave; a nota usa preview.adjustLaterNote.
    expect(step.textContent).toContain("preview.adjustLaterNote")
    expect(step.textContent).not.toMatch(/editor avan/i)
  })
})
