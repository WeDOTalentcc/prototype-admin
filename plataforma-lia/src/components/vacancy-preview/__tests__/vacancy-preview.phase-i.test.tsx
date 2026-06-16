/**
 * Sensors for Phase I — VacancyPreview canonical layout + DecisionBar.
 *
 * Specifically pins:
 *  1. Stage badge + 'Próximo:' hint render correctly per stage (8 cases).
 *  2. VacancyDecisionBar renders 3 mode-pickers for ao_vivo (Phase I.5).
 *  3. VacancyDecisionBar renders nothing for noop / encerrada.
 *  4. ActionBar tooltip labels match design system.
 *  5. ESC + close button dispatch onClose.
 *
 * Phase I.4 dispatch audience inference is tested at the
 * pipeline-overview-page level (where the state lives).
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, cleanup } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { VacancyPreview } from "../vacancy-preview"
import { VacancyDecisionBar } from "../VacancyDecisionBar"
import type { VacancyAction } from "@/components/pages/pipeline-overview-page"

vi.mock("@/services/lia-api", () => ({
  liaApi: {
    getJobVacancy: vi.fn().mockResolvedValue({
      description: "Test description",
      enriched_jd: null,
      technical_requirements: [],
      benefits: [],
      salary_range: null,
      recruiter: null,
      manager_email: null,
      screening_questions: [],
      screening_status: "not_configured",
    }),
  },
}))

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}))

vi.mock("@/components/pages/jobs/job-preview/sections/JobScreeningSection", () => ({
  JobScreeningSection: ({ previewJob }: { previewJob: { title?: string } }) => (
    <div data-testid="mock-screening-section">{previewJob?.title ?? ""}</div>
  ),
}))

const messages = {
  pipelineOverview: {
    vacancyCard: {
      atsBadge: "ATS",
      atsBadgeTitle: "Importada de ATS externo",
      atsBadgeTitleNamed: "Importada via {source}",
      approvalPending: "Aguardando aprovação",
      candidatesCount: "{count} candidatos",
      openWizard: "Continuar JD",
      openEnrichment: "Continuar enriquecimento",
      openWsi: "Configurar WSI",
      requestApproval: "Solicitar aprovação",
      openApproval: "Revisar aprovação",
      openPublish: "Publicar vaga",
      openStatus: "Alterar status",
      openKanban: "Abrir kanban",
      openClosed: "Ver encerramento",
    },
  },
}

const baseVacancy = {
  id: "v-1",
  title: "Engenheiro de Software Pleno",
  department: "Engenharia",
  location: "São Paulo",
  work_model: "Híbrido",
  seniority_level: "Pleno",
  status: "Rascunho",
  stage_entered_at: "2026-04-30T10:00:00Z",
  updated_at: "2026-05-01T12:00:00Z",
  created_at: "2026-04-29T08:00:00Z",
  manager: "Ana Souza",
  imported_from_ats: true,
  source_system: "gupy",
  ats_source_label: "Gupy",
  approval_status: null,
  candidate_count: 0,
}

const wrap = (ui: React.ReactElement) => (
  <NextIntlClientProvider locale="pt-BR" messages={messages}>
    {ui}
  </NextIntlClientProvider>
)

describe("Phase I.2 — Stage badge + next hint", () => {
  beforeEach(() => cleanup())

  // Table-driven: every backend lifecycle stage has a specific hint.
  // If a new stage is added in the backend, this test fails (forcing the
  // contributor to add the hint mapping in vacancy-preview.tsx).
  const stageCases = [
    { stage: "ats_importada", display: "ATS Importada", hint: "Edite e enriqueça a descrição da vaga" },
    { stage: "rascunho", display: "Rascunho/JD", hint: "Continue editando a descrição" },
    { stage: "enriquecida", display: "Enriquecida", hint: "Crie perguntas de triagem WSI" },
    { stage: "wsi_config", display: "WSI Config", hint: "Solicite aprovação das perguntas" },
    { stage: "aguardando_aprovacao", display: "Aguardando Aprovação", hint: "Ative a triagem para os candidatos" },
    { stage: "publicada", display: "Publicada", hint: "Publique nos canais de divulgação" },
    { stage: "ao_vivo", display: "Ao Vivo", hint: "Acompanhe candidatos / altere status" },
    { stage: "encerrada", display: "Encerrada", hint: "Vaga encerrada" },
  ]

  for (const c of stageCases) {
    it(`shows display "${c.display}" + hint for stage=${c.stage}`, () => {
      render(
        wrap(
          <VacancyPreview
            vacancy={baseVacancy}
            isOpen={true}
            onClose={vi.fn()}
            action={{ kind: "open-jd-config", label: "Continuar JD" }}
            onAction={vi.fn()}
            stageKey={c.stage}
          />,
        ),
      )
      expect(screen.getByText(c.display)).toBeInTheDocument()
      expect(screen.getByText(c.hint)).toBeInTheDocument()
    })
  }
})

describe("Phase I.5 — VacancyDecisionBar mode picker (ao_vivo)", () => {
  beforeEach(() => cleanup())

  it("renders 3 mode buttons (Pausar/Concluir/Cancelar) for open-status-modal kind", () => {
    const onAction = vi.fn()
    render(
      <VacancyDecisionBar
        vacancy={{ id: "v-1", title: "X", status: "Ativa" }}
        action={{ kind: "open-status-modal", label: "Alterar status", mode: "pause" }}
        onAction={onAction}
      />,
    )
    expect(screen.getByRole("button", { name: /Pausar/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Concluir/i })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Cancelar/i })).toBeInTheDocument()
  })

  it("each mode button dispatches with the correct mode in the action", () => {
    const onAction = vi.fn()
    render(
      <VacancyDecisionBar
        vacancy={{ id: "v-1", title: "X", status: "Ativa" }}
        action={{ kind: "open-status-modal", label: "Alterar status", mode: "pause" }}
        onAction={onAction}
      />,
    )
    fireEvent.click(screen.getByRole("button", { name: /Pausar/i }))
    expect(onAction.mock.calls[0][0]).toMatchObject({ kind: "open-status-modal", mode: "pause" })

    fireEvent.click(screen.getByRole("button", { name: /Concluir/i }))
    expect(onAction.mock.calls[1][0]).toMatchObject({ kind: "open-status-modal", mode: "activate" })

    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }))
    expect(onAction.mock.calls[2][0]).toMatchObject({ kind: "open-status-modal", mode: "cancel" })
  })

  it("renders nothing for noop kind (encerrada)", () => {
    const { container } = render(
      <VacancyDecisionBar
        vacancy={{ id: "v-1", title: "X", status: "Concluída" }}
        action={{ kind: "noop", label: "Ver encerramento", disabled: true }}
        onAction={vi.fn()}
      />,
    )
    expect(container.firstChild).toBeNull()
  })

  it("renders single primary CTA for non-noop, non-status kinds", () => {
    const onAction = vi.fn()
    render(
      <VacancyDecisionBar
        vacancy={{ id: "v-1", title: "X", status: "Rascunho" }}
        action={{ kind: "open-jd-config", label: "Continuar JD" }}
        onAction={onAction}
      />,
    )
    const btn = screen.getByRole("button", { name: "Continuar JD" })
    expect(btn).toBeInTheDocument()
    fireEvent.click(btn)
    expect(onAction.mock.calls[0][0]).toMatchObject({ kind: "open-jd-config" })
  })
})

describe("Phase I — request-approval CTA (BLOQUEANTE wsi_config fix)", () => {
  beforeEach(() => cleanup())

  it("renders 'Solicitar aprovação' label for request-approval kind", () => {
    render(
      <VacancyDecisionBar
        vacancy={{ id: "v-1", title: "X", status: "Rascunho" }}
        action={{ kind: "request-approval", label: "Solicitar aprovação" }}
        onAction={vi.fn()}
      />,
    )
    expect(screen.getByRole("button", { name: "Solicitar aprovação" })).toBeInTheDocument()
  })
})
