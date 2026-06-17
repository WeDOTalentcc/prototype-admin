"use client"

/**
 * VacancyPreview — Phase I.2 canonical refactor.
 *
 * Side-panel preview for job vacancies in the "Recrutar > Visão Global > Vagas"
 * rail. Mirrors the canonical CandidatePreview UX (Paulo, 2026-05-06):
 *
 *   ┌────────────────────────────────────────────────────────┐
 *   │ p-3 wrapper                                            │
 *   │   <VacancyPreviewHeader />                             │
 *   │     title, stage badge prominente, "Próximo: hint",    │
 *   │     prev/next, close                                   │
 *   │   <VacancyPreviewActionBar />  ← BOTÕES NO TOPO        │
 *   │     icon-only ghost (Settings, Kanban, Share, Star)    │
 *   │   <VacancyDecisionBar />       ← STAGE-AWARE (TOPO)    │
 *   │     single primary CTA (or 3-button picker for ao_vivo)│
 *   ├────────────────────────────────────────────────────────┤
 *   │ flex-1 overflow-y-auto                                 │
 *   │   <JobScreeningSection /> (importado, 764 linhas)      │
 *   │     JD + enriched_jd + skills + screening_questions    │
 *   │     blocks colapsáveis + benefits + interview stages   │
 *   └────────────────────────────────────────────────────────┘
 *
 * Architectural notes:
 *  - Hooks ALWAYS above any early return (CLAUDE.md > Frontend / React
 *    rules-of-hooks discipline). Smoke test in __tests__ guards regression.
 *  - Stage-aware CTA via VacancyAction (discriminated union exhaustive over
 *    the 8 lifecycle stages). New CTAs MUST extend VacancyActionKind.
 *  - Lazy-loads full vacancy detail via liaApi.getJobVacancy(id) on open;
 *    skeleton shown while loading. Refetches on stage/status change.
 *  - Composes the existing JobScreeningSection (~764 lines) instead of
 *    duplicating UI. Provides minimal prop wiring via mapVacancyToJob.
 *
 * Source of truth: .planning/vacancy-pipeline-plan.md (Phase I.2).
 */
import { useEffect, useState, useCallback, useRef, useMemo } from "react"
import { useRouter } from "next/navigation"
import { useTranslations } from "next-intl"
import { X, ChevronLeft, ChevronRight, Briefcase, Database } from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { Chip } from "@/components/ui/chip"
import { TooltipProvider } from "@/components/ui/tooltip"

import type { VacancyAction } from "@/components/pages/pipeline-overview-page"
import { VacancyPreviewActionBar } from "./VacancyPreviewActionBar"
import { VacancyDecisionBar } from "./VacancyDecisionBar"
import { JobScreeningSection } from "@/components/pages/jobs/job-preview/sections/JobScreeningSection"
import { mapVacancyToJob, type VacancyDetailFromApi } from "./utils/mapVacancyToJob"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { VacancyAnalyticsTab } from "./VacancyAnalyticsTab"

interface VacancyLite {
  id: string
  title: string
  department?: string | null
  location?: string | null
  work_model?: string | null
  seniority_level?: string | null
  status: string
  stage_entered_at?: string | null
  updated_at?: string | null
  created_at?: string | null
  manager?: string | null
  imported_from_ats: boolean
  source_system?: string | null
  ats_source_label?: string | null
  approval_status?: string | null
  candidate_count?: number
}

interface VacancyPreviewProps {
  vacancy: VacancyLite
  isOpen: boolean
  onClose: () => void
  /** Stage-aware action computed by the parent. */
  action: VacancyAction
  /** Called when CTA is clicked. Parent handles routing/modal mount. */
  onAction: (action: VacancyAction, vacancy: VacancyLite) => void
  /** Optional prev/next nav across the visible vacancy list. */
  vacancies?: VacancyLite[]
  currentIndex?: number
  onNavigate?: (index: number) => void
  /** Phase I.2 — current stage key (for badge + hint lookup). */
  stageKey?: string
}

// Phase I.2 — stage badge color + next-step hint lookup tables.
// Color tokens come from the backend in JOB_LIFECYCLE_COLORS; we mirror them
// here so the preview can render WITHOUT a backend roundtrip per render.
const STAGE_COLOR: Record<string, string> = {
  ats_importada: "#8A8F98",
  rascunho: "#60BED1",
  enriquecida: "#9860D1",
  wsi_config: "#5DA47A",
  aguardando_aprovacao: "#D19960",
  publicada: "#6078D1",
  ao_vivo: "#4DA67A",
  encerrada: "#8A8F98",
}

const STAGE_DISPLAY: Record<string, string> = {
  ats_importada: "ATS Importada",
  rascunho: "Rascunho/JD",
  enriquecida: "Enriquecida",
  wsi_config: "WSI Config",
  aguardando_aprovacao: "Aguardando Aprovação",
  publicada: "Publicada",
  ao_vivo: "Ao Vivo",
  encerrada: "Encerrada",
}

const STAGE_NEXT_HINT: Record<string, string> = {
  ats_importada: "Edite e enriqueça a descrição da vaga",
  rascunho: "Continue editando a descrição",
  enriquecida: "Crie perguntas de triagem WSI",
  wsi_config: "Solicite aprovação das perguntas",
  aguardando_aprovacao: "Ative a triagem para os candidatos",
  publicada: "Publique nos canais de divulgação",
  ao_vivo: "Acompanhe candidatos / altere status",
  encerrada: "Vaga encerrada",
}

export function VacancyPreview({
  vacancy,
  isOpen,
  onClose,
  action,
  onAction,
  vacancies = [],
  currentIndex = 0,
  onNavigate,
  stageKey,
}: VacancyPreviewProps) {
  const t = useTranslations("pipelineOverview")
  const router = useRouter()

  // ── Hooks (all above any early return — Rules of Hooks discipline) ──
  const [detail, setDetail] = useState<VacancyDetailFromApi | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const panelRef = useRef<HTMLDivElement | null>(null)

  // Phase I.2 — local state pra collapse das sections (espelha useJobPreviewState
  // do JobPreviewPanel sem importar o hook completo, que tem outras
  // dependências do /jobs page context).
  const [collapsedSections, setCollapsedSections] = useState<string[]>([])
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([0, 1, 2, 3, 4, 6])

  const toggleSection = useCallback((s: string) => {
    setCollapsedSections((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]))
  }, [])
  const toggleBlock = useCallback((id: number) => {
    setExpandedBlocks((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }, [])

  // Lazy-fetch vacancy detail when opened or when vacancy/status changes.
  // Refetch on status change is critical: when the recruiter triggers an
  // action that moves the vaga across stages, the rail refetches the lifecycle
  // overview which updates `vacancy.status` — we then refetch detail so the
  // preview reflects the new state (e.g., enriched_jd appears, screening
  // questions appear).
  useEffect(() => {
    if (!isOpen || !vacancy?.id) return
    let cancelled = false
    setIsLoadingDetail(true)
    setDetailError(null)
    setDetail(null)
    liaApi
      .getJobVacancy(vacancy.id)
      .then((v) => {
        if (cancelled) return
        const x = v as unknown as Record<string, unknown>
        setDetail({
          description: (x.description as string) ?? null,
          enriched_jd: x.enriched_jd ?? null,
          technical_requirements: (x.technical_requirements as unknown[]) ?? [],
          benefits: (x.benefits as unknown[]) ?? [],
          salary_range: (x.salary_range as { min?: number; max?: number; currency?: string } | null) ?? null,
          recruiter: (x.recruiter as string) ?? null,
          manager_email: (x.manager_email as string) ?? null,
          job_code: (x.job_code as string) ?? null,
          recruiter_email: (x.recruiter_email as string) ?? null,
          screening_questions: (x.screening_questions as unknown[]) ?? [],
          screening_config: x.screening_config,
          screening_status: (x.screening_status as string) ?? null,
          interview_stages: (x.interview_stages as unknown[]) ?? [],
          languages: (x.languages as unknown[]) ?? [],
          behavioral_competencies: (x.behavioral_competencies as unknown[]) ?? [],
          hiring_process: (x.hiring_process as string[]) ?? [],
          published_linkedin: !!x.published_linkedin,
          published_website: !!x.published_website,
          published_indeed: !!x.published_indeed,
          approval_status: (x.approval_status as string) ?? null,
          is_confidential: !!x.is_confidential,
          visibility: (x.visibility as string) ?? null,
          deadline: (x.deadline as string) ?? null,
          open_date: (x.open_date as string) ?? null,
          priority: (x.priority as string) ?? null,
        })
      })
      .catch((err: unknown) => {
        if (cancelled) return
        setDetailError(err instanceof Error ? err.message : "Erro desconhecido")
      })
      .finally(() => {
        if (!cancelled) setIsLoadingDetail(false)
      })
    return () => {
      cancelled = true
    }
  }, [isOpen, vacancy?.id, vacancy?.status, vacancy?.approval_status])

  // ESC closes the preview.
  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [isOpen, onClose])

  // Prev/next handlers.
  const handlePrev = useCallback(() => {
    if (!onNavigate || vacancies.length === 0) return
    const idx = (currentIndex - 1 + vacancies.length) % vacancies.length
    onNavigate(idx)
  }, [onNavigate, vacancies.length, currentIndex])

  const handleNext = useCallback(() => {
    if (!onNavigate || vacancies.length === 0) return
    const idx = (currentIndex + 1) % vacancies.length
    onNavigate(idx)
  }, [onNavigate, vacancies.length, currentIndex])

  // ActionBar handlers — defaults navigate via Next router; override-able via props.
  const handleOpenSettings = useCallback(
    (id: string) => router.push(`/jobs/${id}?tab=edit&section=descricao`),
    [router],
  )
  const handleOpenKanban = useCallback(
    (id: string) => router.push(`/jobs/${id}?tab=management`),
    [router],
  )

  // Compose the rich Job shape for JobScreeningSection. Memoized so the
  // section's internal effects don't re-fire on every render.
  const composedJob = useMemo(
    () => mapVacancyToJob(vacancy, detail),
    [vacancy, detail],
  )

  // ── Hooks above this line — early returns from here on are safe. ──
  if (!isOpen || !vacancy) return null

  const hasNav = onNavigate && vacancies.length > 1
  const stage = stageKey || vacancy.status
  const stageBadgeColor = STAGE_COLOR[stage] ?? "#8A8F98"
  const stageDisplay = STAGE_DISPLAY[stage] ?? stage
  const nextHint = STAGE_NEXT_HINT[stage] ?? ""

  return (
    <div
      ref={panelRef}
      className="h-full bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle flex flex-col w-full"
      role="dialog"
      aria-label={`Visualizar vaga ${vacancy.title}`}
    >
      <TooltipProvider delayDuration={200}>
        {/* p-3 wrapper — Header + ActionBar + DecisionBar (canonical layout) */}
        <div className="p-3 dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
          {/* Header */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 min-w-0">
              {hasNav && (
                <button
                  onClick={handlePrev}
                  className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary"
                  aria-label="Vaga anterior"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
              )}
              <Briefcase className="w-4 h-4 text-lia-text-tertiary flex-shrink-0" />
              <p className="text-sm font-medium text-lia-text-primary truncate" title={vacancy.title}>
                {vacancy.title}
              </p>
              {hasNav && (
                <button
                  onClick={handleNext}
                  className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary"
                  aria-label="Próxima vaga"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-lia-interactive-hover text-lia-text-tertiary"
              aria-label="Fechar preview"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Stage badge + "Próximo:" hint */}
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span
              className="inline-flex items-center px-2 py-0.5 rounded-full text-[0.625rem] font-medium text-white"
              style={{ backgroundColor: stageBadgeColor }}
            >
              {stageDisplay}
            </span>
            {vacancy.imported_from_ats && (
              <Chip density="relaxed" variant="info" muted >
                <Database className="w-3 h-3 mr-1" />
                {vacancy.ats_source_label || t("vacancyCard.atsBadge")}
              </Chip>
            )}
            {vacancy.seniority_level && (
              <Chip density="relaxed" variant="neutral" muted >
                {vacancy.seniority_level}
              </Chip>
            )}
          </div>
          {nextHint && (
            <p className="text-[0.625rem] text-lia-text-tertiary mb-3">
              <span className="font-medium text-lia-text-secondary">Próximo:</span> {nextHint}
            </p>
          )}

          {/* ActionBar — universal actions (Settings, Kanban, Share, Star) */}
          <VacancyPreviewActionBar
            vacancyId={vacancy.id}
            vacancyTitle={vacancy.title}
            onOpenSettings={handleOpenSettings}
            onOpenKanban={handleOpenKanban}
          />
        </div>

        {/* DecisionBar — stage-aware primary action (canonical: TOP, not footer) */}
        <VacancyDecisionBar vacancy={vacancy} action={action} onAction={onAction} />

        {/* Body — tabs: Informações (existing) + Análise (analytics) */}
        <div className="flex-1 overflow-y-auto flex flex-col">
          <Tabs defaultValue="info" className="flex flex-col flex-1">
            <div className="px-3 pt-2 pb-0 border-b border-lia-border-subtle bg-lia-bg-primary">
              <TabsList className="h-8 p-0.5 bg-lia-bg-secondary rounded-md">
                <TabsTrigger
                  value="info"
                  className="text-xs px-3 py-1 h-7"
                >
                  Informações
                </TabsTrigger>
                <TabsTrigger
                  value="analytics"
                  className="text-xs px-3 py-1 h-7"
                >
                  📊 Análise
                </TabsTrigger>
              </TabsList>
            </div>

            <TabsContent value="info" className="flex-1 overflow-y-auto mt-0">
              {isLoadingDetail ? (
                <div className="px-4 py-6 space-y-2">
                  <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse" />
                  <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse w-5/6" />
                  <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse w-4/6" />
                  <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse w-3/6" />
                </div>
              ) : detailError ? (
                <p className="px-4 py-6 text-xs text-status-error">
                  Erro ao carregar detalhes: {detailError}
                </p>
              ) : detail ? (
                <JobScreeningSection
                  previewJob={composedJob}
                  screeningConfig={(detail.screening_config as never) ?? undefined}
                  isLoadingScreeningConfig={false}
                  collapsedPreviewSections={collapsedSections}
                  expandedBlocks={expandedBlocks}
                  onToggleSection={toggleSection}
                  onToggleBlock={toggleBlock}
                />
              ) : null}
            </TabsContent>

            <TabsContent value="analytics" className="flex-1 overflow-y-auto mt-0">
              <VacancyAnalyticsTab jobId={vacancy.id} />
            </TabsContent>
          </Tabs>
        </div>
      </TooltipProvider>
    </div>
  )
}
