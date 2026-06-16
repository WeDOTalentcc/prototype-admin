/**
 * PipelineTemplateSuggestion.test.tsx — Fase 4.2 (Sprint Pipeline Templates).
 *
 * Cobre:
 *  - i18n canonical contract (messages/pt-BR.json + en.json reais).
 *  - render top-3 templates com nome + score formatado.
 *  - aplica template: fetch POST /apply-pipeline-template + onApplied callback.
 *  - skip: onSkip callback, sem fetch.
 *  - disabled sem vacancyId: apply button desabilitado, toast em fallback.
 */
import React from "react"
import { describe, test, expect, vi, beforeEach, afterEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"

import ptBR from "../../../../../messages/pt-BR.json"
import en from "../../../../../messages/en.json"
import { PipelineTemplateSuggestion } from "../PipelineTemplateSuggestion"
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
    name: "Pipeline Médicos",
    description: "Pipeline canonical para médicos",
    stages_count: 4,
    score: 0.92,
  },
  {
    template_id: "tpl-b",
    name: "Pipeline Enfermagem",
    description: "Pipeline para enfermagem",
    stages_count: 3,
    score: 0.55,
  },
  {
    template_id: "tpl-c",
    name: "Pipeline Administrativo",
    description: null,
    stages_count: 2,
    score: 0.41,
  },
]

function renderCard(opts: {
  templates?: WizardPipelineTemplateSuggestion[]
  vacancyId?: string | null
  onApplied?: ReturnType<typeof vi.fn>
  onSkip?: ReturnType<typeof vi.fn>
  locale?: "pt-BR" | "en"
  onError?: (e: { message?: string }) => void
} = {}) {
  const locale = opts.locale ?? "pt-BR"
  const messages = locale === "pt-BR" ? ptBR : en
  return render(
    <NextIntlClientProvider locale={locale} messages={messages} onError={opts.onError}>
      <PipelineTemplateSuggestion
        templates={opts.templates ?? TEMPLATES}
        vacancyId={opts.vacancyId === undefined ? "vac-1" : opts.vacancyId}
        onApplied={opts.onApplied ?? vi.fn()}
        onSkip={opts.onSkip ?? vi.fn()}
      />
    </NextIntlClientProvider>,
  )
}

describe("PipelineTemplateSuggestion — i18n canonical contract", () => {
  for (const locale of ["pt-BR", "en"] as const) {
    test(locale + ": renders without MISSING_MESSAGE", () => {
      const errors: Array<{ message?: string }> = []
      renderCard({ locale, onError: (e) => errors.push(e) })
      const missing = errors.filter((e) => e.message?.includes?.("MISSING_MESSAGE"))
      expect(missing).toEqual([])
    })
  }
})

describe("PipelineTemplateSuggestion — render top-3", () => {
  test("renders all 3 template names and score badges", () => {
    renderCard()
    expect(screen.getByText("Pipeline Médicos")).toBeTruthy()
    expect(screen.getByText("Pipeline Enfermagem")).toBeTruthy()
    expect(screen.getByText("Pipeline Administrativo")).toBeTruthy()
    // pt-BR matchPercent = "{percent}% match" — 92, 55, 41
    expect(screen.getByText(/92% match/)).toBeTruthy()
    expect(screen.getByText(/55% match/)).toBeTruthy()
    expect(screen.getByText(/41% match/)).toBeTruthy()
  })

  test("limits to top 3 when more provided", () => {
    const four = [
      ...TEMPLATES,
      { template_id: "tpl-d", name: "Extra Tpl", stages_count: 1, score: 0.3 },
    ]
    renderCard({ templates: four })
    expect(screen.queryByText("Extra Tpl")).toBeNull()
  })
})

describe("PipelineTemplateSuggestion — aplica template", () => {
  let fetchMock: ReturnType<typeof vi.fn>
  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "applied" }),
    })
    // @ts-expect-error global fetch override
    global.fetch = fetchMock
  })
  afterEach(() => {
    // @ts-expect-error reset
    delete global.fetch
  })

  test("clicking apply calls POST /apply-pipeline-template with correct body", async () => {
    const onApplied = vi.fn()
    renderCard({ vacancyId: "vac-42", onApplied })

    const applyBtn = screen.getByTestId("pipeline-template-apply-tpl-a")
    fireEvent.click(applyBtn)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe("/api/backend-proxy/job-vacancies/vac-42/apply-pipeline-template")
    expect(init?.method).toBe("POST")
    const body = JSON.parse(init?.body as string)
    expect(body).toEqual({ template_id: "tpl-a", source: "wizard_explicit" })

    await waitFor(() => expect(onApplied).toHaveBeenCalledWith("tpl-a", "wizard_explicit"))
  })
})

describe("PipelineTemplateSuggestion — skip", () => {
  test("clicking skip calls onSkip and does NOT fetch", () => {
    const fetchMock = vi.fn()
    // @ts-expect-error
    global.fetch = fetchMock
    const onSkip = vi.fn()
    renderCard({ onSkip })

    const skipBtn = screen.getByTestId("pipeline-template-skip")
    fireEvent.click(skipBtn)

    expect(onSkip).toHaveBeenCalledTimes(1)
    expect(fetchMock).not.toHaveBeenCalled()
    // @ts-expect-error
    delete global.fetch
  })
})

describe("PipelineTemplateSuggestion — disabled sem vacancyId", () => {
  test("vacancyId=null disables all apply buttons", () => {
    renderCard({ vacancyId: null })
    const applyBtn = screen.getByTestId("pipeline-template-apply-tpl-a") as HTMLButtonElement
    expect(applyBtn.disabled).toBe(true)
  })
})
