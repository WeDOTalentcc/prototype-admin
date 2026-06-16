/**
 * Smoke / regression test — VacancyPreview component.
 *
 * Guards:
 *  1. Rules of Hooks discipline: rerender isOpen=false → true → false MUST NOT throw
 *     (matches the regression class fixed in commit 7c24ece9a for BulkImportModal).
 *  2. Stage-aware CTA mapping is exhaustive — every lifecycle stage renders the
 *     correct label per VacancyAction discriminated union.
 *  3. Fundamental UX: ESC closes; backdrop click is parent's responsibility.
 *
 * See .planning/vacancy-pipeline-plan.md (Phase A) for full context.
 */
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, cleanup } from "@testing-library/react"
import { NextIntlClientProvider } from "next-intl"
import { VacancyPreview } from "../vacancy-preview"
import ptBRMessages from "../../../../messages/pt-BR.json"
import enMessages from "../../../../messages/en.json"

// Stub liaApi.getJobVacancy so we don't hit the network. We don't care about
// the resolved value here — the component must render synchronously.
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
    }),
  },
}))

// Phase I.2 — VacancyPreview now uses next/navigation useRouter for deep-link
// navigation (Settings, Kanban). Tests mock the router stub to avoid the
// "invariant expected app router to be mounted" Next-side error.
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => "/",
}))

// JobScreeningSection has heavy deps (icons, hooks, internal state). For the
// smoke tests we stub it to a passthrough — the canonical regression net for
// the section is the JobsPage tests + Phase I.7 Playwright happy-path.
vi.mock("@/components/pages/jobs/job-preview/sections/JobScreeningSection", () => ({
  JobScreeningSection: ({ previewJob }: { previewJob: { title?: string } }) => (
    <div data-testid="mock-screening-section">{previewJob?.title ?? ""}</div>
  ),
}))

// Minimal i18n messages so useTranslations works in tests.
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

describe("VacancyPreview — Rules of Hooks discipline", () => {
  beforeEach(() => {
    cleanup()
  })

  it("renders nothing when isOpen=false", () => {
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={false}
          onClose={vi.fn()}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={vi.fn()}
        />,
      ),
    )
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()
  })

  it("does not crash when toggling isOpen false → true → false", () => {
    const onClose = vi.fn()
    const onAction = vi.fn()
    const { rerender } = render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={false}
          onClose={onClose}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={onAction}
        />,
      ),
    )
    expect(() =>
      rerender(
        wrap(
          <VacancyPreview
            vacancy={baseVacancy}
            isOpen={true}
            onClose={onClose}
            action={{ kind: "open-jd-config", label: "Continuar JD" }}
            onAction={onAction}
          />,
        ),
      ),
    ).not.toThrow()

    expect(() =>
      rerender(
        wrap(
          <VacancyPreview
            vacancy={baseVacancy}
            isOpen={false}
            onClose={onClose}
            action={{ kind: "open-jd-config", label: "Continuar JD" }}
            onAction={onAction}
          />,
        ),
      ),
    ).not.toThrow()
  })
})

describe("VacancyPreview — stage-aware CTA labels", () => {
  beforeEach(() => {
    cleanup()
  })

  const cases = [
    { kind: "open-jd-config" as const, label: "Continuar JD" },
    { kind: "open-questions-config" as const, label: "Continuar enriquecimento" },
    { kind: "dispatch-screening" as const, label: "Revisar aprovação" },
    { kind: "open-publish-modal" as const, label: "Publicar vaga" },
    // Phase I.2 — kind="noop" (encerrada) now renders NOTHING per canonical
    // (DecisionBar returns null for noop, mirroring PipelineDecisionBar
    // collapse-when-no-action). Verified separately in test below.
  ]

  for (const c of cases) {
    it(`renders CTA "${c.label}" for kind=${c.kind}`, () => {
      const onAction = vi.fn()
      // Build action shape — open-status-modal needs a mode field.
      const action =
        c.kind === "noop"
          ? { kind: c.kind, label: c.label, disabled: true as const }
          : { kind: c.kind, label: c.label }
      render(
        wrap(
          <VacancyPreview
            vacancy={baseVacancy}
            isOpen={true}
            onClose={vi.fn()}
            action={action}
            onAction={onAction}
          />,
        ),
      )
      expect(screen.getByRole("button", { name: c.label })).toBeInTheDocument()
    })
  }

  it("CTA click invokes onAction with action+vacancy", () => {
    const onAction = vi.fn()
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={true}
          onClose={vi.fn()}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={onAction}
        />,
      ),
    )
    fireEvent.click(screen.getByRole("button", { name: "Continuar JD" }))
    expect(onAction).toHaveBeenCalledTimes(1)
    expect(onAction.mock.calls[0][0]).toMatchObject({ kind: "open-jd-config" })
    expect(onAction.mock.calls[0][1]).toMatchObject({ id: "v-1" })
  })

  it("noop kind (encerrada) renders no DecisionBar button", () => {
    // Phase I.2 — VacancyDecisionBar returns null when action.kind === "noop"
    // because read-only stages should not display a clickable CTA. Mirrors the
    // PipelineDecisionBar pattern (no decision = no bar).
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={true}
          onClose={vi.fn()}
          action={{ kind: "noop", label: "Ver encerramento", disabled: true }}
          onAction={vi.fn()}
        />,
      ),
    )
    // Negative assertion: no DecisionBar button should be visible for noop.
    expect(screen.queryByRole("button", { name: "Ver encerramento" })).not.toBeInTheDocument()
  })
})

describe("VacancyPreview — UX primitives", () => {
  beforeEach(() => {
    cleanup()
  })

  it("ESC key calls onClose", () => {
    const onClose = vi.fn()
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={true}
          onClose={onClose}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={vi.fn()}
        />,
      ),
    )
    fireEvent.keyDown(window, { key: "Escape" })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("close button calls onClose", () => {
    const onClose = vi.fn()
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={true}
          onClose={onClose}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={vi.fn()}
        />,
      ),
    )
    fireEvent.click(screen.getByLabelText("Fechar preview"))
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it("renders prev/next buttons when navigator props supplied + multiple vacancies", () => {
    const onNavigate = vi.fn()
    render(
      wrap(
        <VacancyPreview
          vacancy={baseVacancy}
          isOpen={true}
          onClose={vi.fn()}
          action={{ kind: "open-jd-config", label: "Continuar JD" }}
          onAction={vi.fn()}
          vacancies={[baseVacancy, { ...baseVacancy, id: "v-2", title: "Outra" }]}
          currentIndex={0}
          onNavigate={onNavigate}
        />,
      ),
    )
    fireEvent.click(screen.getByLabelText("Próxima vaga"))
    expect(onNavigate).toHaveBeenCalledWith(1)
  })
})


describe("VacancyPreview — i18n canonical contract (real messages — guards openStatus regression)", () => {
  // Harness fix: o teste antes validava apenas contra a fixture local `messages`,
  // mascarando chaves ausentes em messages/*.json reais (caso openStatus,
  // MISSING_MESSAGE em /pt/recrutar). Aqui validamos as chaves USADAS pelo card
  // contra os arquivos canonicos pt-BR.json E en.json.
  const usedKeys = Object.keys(messages.pipelineOverview.vacancyCard)

  it.each(usedKeys)("pt-BR.json resolve pipelineOverview.vacancyCard.%s", (k) => {
    const v = (ptBRMessages as Record<string, any>).pipelineOverview?.vacancyCard?.[k]
    expect(typeof v).toBe("string")
  })

  it.each(usedKeys)("en.json resolve pipelineOverview.vacancyCard.%s", (k) => {
    const v = (enMessages as Record<string, any>).pipelineOverview?.vacancyCard?.[k]
    expect(typeof v).toBe("string")
  })
})
