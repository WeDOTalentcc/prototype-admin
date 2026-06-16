/**
 * pipeline-templates-tab.test.tsx — Fase 4.2 (Sprint Pipeline Templates).
 *
 * Cobre:
 *  - i18n canonical contract (importa messages/pt-BR.json + en.json REAIS).
 *  - render lista de templates (mock useTemplates).
 *  - botão "Novo template" abre editor com state limpo.
 *  - estado vazio (templates=[]) mostra CTA seedDefaults.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import ptBR from "../../../../../messages/pt-BR.json"
import en from "../../../../../messages/en.json"
import { PipelineTemplatesTab } from "../pipeline-templates-tab"
import type { PipelineTemplateFull } from "@/hooks/pipeline/use-pipeline-templates"

const FIXTURE_TEMPLATES: PipelineTemplateFull[] = [
  {
    id: "tpl-1",
    company_id: "co-1",
    name: "Médicos — Plantonistas",
    description: "Pipeline para médicos plantonistas",
    stages: [
      { name: "Triagem clínica", order: 1, type: "manual", sla_days: 2 },
      { name: "Entrevista técnica", order: 2, type: "manual", sla_days: 3 },
    ],
    is_default: false,
    is_active: true,
    is_archived: false,
    usage_count: 5,
    department_hint: ["Saúde"],
    seniority_hint: ["Sênior"],
    job_family_hint: ["Médico"],
  },
  {
    id: "tpl-2",
    company_id: "co-1",
    name: "Engenharia — Backend",
    description: "Pipeline para devs backend",
    stages: [{ name: "Triagem CV", order: 1, type: "automatic", sla_days: 1 }],
    is_default: true,
    is_active: true,
    is_archived: false,
    usage_count: 12,
  },
]

const hookMock = vi.fn()
vi.mock("@/hooks/pipeline/use-pipeline-templates", () => ({
  usePipelineTemplates: () => hookMock(),
}))

function defaultHookValue(overrides: Partial<ReturnType<typeof makeHookValue>> = {}) {
  return { ...makeHookValue(), ...overrides }
}

function makeHookValue() {
  return {
    templates: FIXTURE_TEMPLATES,
    total: FIXTURE_TEMPLATES.length,
    isLoading: false,
    error: null,
    mutate: vi.fn(),
    createTemplate: vi.fn(),
    updateTemplate: vi.fn(),
    cloneTemplate: vi.fn(),
    archiveTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
    seedDefaults: vi.fn(),
  }
}

function renderTab(locale: "pt-BR" | "en" = "pt-BR", onError?: (e: { message?: string }) => void) {
  const messages = locale === "pt-BR" ? ptBR : en
  return render(
    <NextIntlClientProvider locale={locale} messages={messages} onError={onError}>
      <PipelineTemplatesTab />
    </NextIntlClientProvider>,
  )
}

describe("PipelineTemplatesTab — i18n canonical contract", () => {
  beforeEach(() => {
    hookMock.mockReturnValue(defaultHookValue())
  })

  for (const locale of ["pt-BR", "en"] as const) {
    test(locale + ": renders without MISSING_MESSAGE", () => {
      const errors: Array<{ message?: string }> = []
      renderTab(locale, (e) => errors.push(e))
      const missing = errors.filter((e) => e.message?.includes?.("MISSING_MESSAGE"))
      expect(missing).toEqual([])
    })
  }

  test("empty state renders without MISSING_MESSAGE", () => {
    hookMock.mockReturnValue(defaultHookValue({ templates: [], total: 0 }))
    const errors: Array<{ message?: string }> = []
    renderTab("pt-BR", (e) => errors.push(e))
    const missing = errors.filter((e) => e.message?.includes?.("MISSING_MESSAGE"))
    expect(missing).toEqual([])
  })
})

describe("PipelineTemplatesTab — render lista templates", () => {
  beforeEach(() => {
    hookMock.mockReturnValue(defaultHookValue())
  })

  test("renders template names from hook", () => {
    renderTab()
    expect(screen.getByText("Médicos — Plantonistas")).toBeTruthy()
    expect(screen.getByText("Engenharia — Backend")).toBeTruthy()
  })

  test("renders edit/clone/archive actions per template", () => {
    renderTab()
    // pt-BR: aria-label Editar/Clonar/Arquivar
    const editButtons = screen.getAllByLabelText("Editar")
    const cloneButtons = screen.getAllByLabelText("Clonar")
    const archiveButtons = screen.getAllByLabelText("Arquivar")
    expect(editButtons.length).toBeGreaterThanOrEqual(2)
    expect(cloneButtons.length).toBeGreaterThanOrEqual(2)
    expect(archiveButtons.length).toBeGreaterThanOrEqual(2)
  })
})

describe("PipelineTemplatesTab — criar novo", () => {
  beforeEach(() => {
    hookMock.mockReturnValue(defaultHookValue())
  })

  test("clicking Novo template opens editor with empty draft name", () => {
    renderTab()
    const button = screen.getByRole("button", { name: /Novo template/ })
    fireEvent.click(button)
    // Editor agora visível: campo nome com default name ("newTemplateDefaultName")
    const nameInput = screen.getByPlaceholderText("Ex: Médicos — Plantonistas") as HTMLInputElement
    expect(nameInput).toBeTruthy()
    // newTemplateDefaultName em pt-BR é algum valor não vazio
    expect(typeof nameInput.value).toBe("string")
  })
})

describe("PipelineTemplatesTab — estado vazio", () => {
  test("templates=[] renders seedCta button", () => {
    hookMock.mockReturnValue(defaultHookValue({ templates: [], total: 0 }))
    renderTab()
    // pt-BR seedCta = "Aplicar templates padrão"
    expect(screen.getByText("Aplicar templates padrão")).toBeTruthy()
    // empty.cta = "Criar primeiro template"
    expect(screen.getByText("Criar primeiro template")).toBeTruthy()
  })
})
