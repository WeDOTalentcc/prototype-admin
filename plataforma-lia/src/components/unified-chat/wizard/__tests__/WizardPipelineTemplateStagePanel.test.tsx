/**
 * WizardPipelineTemplateStagePanel.test.tsx — Sprint Pipeline Templates Opção B.
 *
 * Cobre:
 *  - i18n canonical contract (messages/pt-BR.json + en.json reais, sem MISSING_MESSAGE).
 *  - render top-3 templates com nome + score formatado.
 *  - suggestedTemplateId destaca o template correspondente (badge canonical).
 *  - apply click chama onApply(templateId) com o id certo.
 *  - skip click chama onSkip() (Usar Padrão da Empresa).
 *  - defaultPipelineInfo plural ICU correto (1 etapa vs N etapas).
 *  - allowSkip=false esconde o botão "Padrão da Empresa".
 */
import React from "react"
import { describe, test, expect, vi } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import ptBR from "../../../../../messages/pt-BR.json"
import en from "../../../../../messages/en.json"
import { WizardPipelineTemplateStagePanel } from "../WizardPipelineTemplateStagePanel"
import type { WizardPipelineTemplateSuggestion } from "../wizard-types"

vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const TEMPLATES: WizardPipelineTemplateSuggestion[] = [
  {
    template_id: "tpl-a",
    name: "Pipeline Médicos Afya",
    description: "Pipeline canonical para médicos da rede Afya",
    stages_count: 5,
    score: 0.94,
  },
  {
    template_id: "tpl-b",
    name: "Pipeline Enfermagem",
    description: "Pipeline para profissionais de enfermagem",
    stages_count: 4,
    score: 0.68,
  },
  {
    template_id: "tpl-c",
    name: "Pipeline Administrativo",
    description: null,
    stages_count: 3,
    score: 0.45,
  },
]

interface RenderOpts {
  templates?: WizardPipelineTemplateSuggestion[]
  suggestedTemplateId?: string | null
  defaultPipelineStagesCount?: number
  allowSkip?: boolean
  onApply?: (templateId: string) => Promise<void>
  onSkip?: () => Promise<void>
  onSeeOthers?: () => void
  locale?: "pt-BR" | "en"
  onError?: (e: { message?: string }) => void
}

function renderPanel(opts: RenderOpts = {}) {
  const locale = opts.locale ?? "pt-BR"
  const messages = locale === "pt-BR" ? ptBR : en
  return render(
    <NextIntlClientProvider locale={locale} messages={messages} onError={opts.onError}>
      <WizardPipelineTemplateStagePanel
        templates={opts.templates ?? TEMPLATES}
        suggestedTemplateId={
          opts.suggestedTemplateId === undefined ? "tpl-a" : opts.suggestedTemplateId
        }
        defaultPipelineStagesCount={opts.defaultPipelineStagesCount ?? 4}
        allowSkip={opts.allowSkip ?? true}
        onApply={opts.onApply ?? vi.fn().mockResolvedValue(undefined)}
        onSkip={opts.onSkip ?? vi.fn().mockResolvedValue(undefined)}
        onSeeOthers={opts.onSeeOthers}
      />
    </NextIntlClientProvider>,
  )
}

describe("WizardPipelineTemplateStagePanel — i18n canonical contract", () => {
  for (const locale of ["pt-BR", "en"] as const) {
    test(locale + ": renders without MISSING_MESSAGE", () => {
      const errors: Array<{ message?: string }> = []
      renderPanel({ locale, onError: (e) => errors.push(e) })
      const missing = errors.filter((e) => e.message?.includes?.("MISSING_MESSAGE"))
      expect(missing).toEqual([])
    })
  }
})

describe("WizardPipelineTemplateStagePanel — render top-3", () => {
  test("renders all 3 template names and score badges", () => {
    renderPanel()
    expect(screen.getByText("Pipeline Médicos Afya")).toBeTruthy()
    expect(screen.getByText("Pipeline Enfermagem")).toBeTruthy()
    expect(screen.getByText("Pipeline Administrativo")).toBeTruthy()
    expect(screen.getByText(/94% match/)).toBeTruthy()
    expect(screen.getByText(/68% match/)).toBeTruthy()
    expect(screen.getByText(/45% match/)).toBeTruthy()
  })

  test("limits to top 3 when more provided", () => {
    const four = [
      ...TEMPLATES,
      {
        template_id: "tpl-d",
        name: "Extra Pipeline Não Deveria Aparecer",
        stages_count: 2,
        score: 0.2,
      },
    ]
    renderPanel({ templates: four })
    expect(screen.queryByText("Extra Pipeline Não Deveria Aparecer")).toBeNull()
  })
})

describe("WizardPipelineTemplateStagePanel — suggested highlighting", () => {
  test("suggestedTemplateId renders suggested badge on matching template", () => {
    renderPanel({ suggestedTemplateId: "tpl-b" })
    expect(
      screen.getByTestId("wizard-pipeline-template-stage-suggested-tpl-b"),
    ).toBeTruthy()
    expect(
      screen.queryByTestId("wizard-pipeline-template-stage-suggested-tpl-a"),
    ).toBeNull()
  })

  test("suggestedTemplateId=null shows no suggested badge", () => {
    renderPanel({ suggestedTemplateId: null })
    expect(
      screen.queryByTestId("wizard-pipeline-template-stage-suggested-tpl-a"),
    ).toBeNull()
    expect(
      screen.queryByTestId("wizard-pipeline-template-stage-suggested-tpl-b"),
    ).toBeNull()
  })
})

describe("WizardPipelineTemplateStagePanel — apply action", () => {
  test("clicking apply calls onApply with correct templateId", async () => {
    const onApply = vi.fn().mockResolvedValue(undefined)
    renderPanel({ onApply })

    const applyBtn = screen.getByTestId("wizard-pipeline-template-stage-apply-tpl-b")
    fireEvent.click(applyBtn)

    await waitFor(() => expect(onApply).toHaveBeenCalledTimes(1))
    expect(onApply).toHaveBeenCalledWith("tpl-b")
  })
})

describe("WizardPipelineTemplateStagePanel — skip action (Padrão da Empresa)", () => {
  test("clicking 'Usar Padrão da Empresa' calls onSkip", async () => {
    const onSkip = vi.fn().mockResolvedValue(undefined)
    const onApply = vi.fn()
    renderPanel({ onSkip, onApply })

    const skipBtn = screen.getByTestId("wizard-pipeline-template-stage-use-default")
    fireEvent.click(skipBtn)

    await waitFor(() => expect(onSkip).toHaveBeenCalledTimes(1))
    expect(onApply).not.toHaveBeenCalled()
  })
})

describe("WizardPipelineTemplateStagePanel — defaultPipelineInfo ICU plural", () => {
  test("defaultPipelineStagesCount=1 renders singular '1 etapa'", () => {
    renderPanel({ defaultPipelineStagesCount: 1 })
    // Footer canonical: "Padrão da empresa tem 1 etapa"
    expect(screen.getByText(/Padrão da empresa tem 1 etapa(?!s)/)).toBeTruthy()
  })

  test("defaultPipelineStagesCount=5 renders plural '5 etapas'", () => {
    renderPanel({ defaultPipelineStagesCount: 5 })
    expect(screen.getByText(/Padrão da empresa tem 5 etapas/)).toBeTruthy()
  })
})

describe("WizardPipelineTemplateStagePanel — allowSkip=false", () => {
  test("hides 'Usar Padrão da Empresa' button when allowSkip=false", () => {
    renderPanel({ allowSkip: false })
    expect(
      screen.queryByTestId("wizard-pipeline-template-stage-use-default"),
    ).toBeNull()
  })
})
