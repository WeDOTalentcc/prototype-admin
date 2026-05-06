"use client"

/**
 * VacancyPreview — Phase A canonical pattern.
 *
 * Side-panel preview for job vacancies in the "Recrutar > Visão Global > Vagas"
 * rail. Mirrors the candidate-preview UX (focus trap, prev/next, ESC to close)
 * but scoped to vacancies + their stage-specific actions.
 *
 * Architectural notes:
 *  - Hooks ALWAYS above any early return (CLAUDE.md > Frontend / React
 *    rules-of-hooks discipline). Smoke test in __tests__ guards regression.
 *  - Stage-aware CTA via VacancyAction (discriminated union exhaustive over
 *    the 8 lifecycle stages). New CTAs MUST extend VacancyActionKind.
 *  - Lazy-loads full vacancy detail via liaApi.getJobVacancy(id) on open;
 *    skeleton shown while loading. The list payload (JobLifecycleVacancy)
 *    only carries summary fields — full metadata (description,
 *    enriched_jd, technical_requirements, etc.) requires the GET.
 *  - No business logic beyond calling the action dispatcher; the parent
 *    page wires state + modals + router.
 *
 * Source of truth: .planning/vacancy-pipeline-plan.md (Phase A).
 */
import { useEffect, useState, useCallback, useRef } from "react"
import { useTranslations } from "next-intl"
import { X, ChevronLeft, ChevronRight, Briefcase, MapPin, Building2, User, Users, Database } from "lucide-react"
import { liaApi } from "@/services/lia-api"
import { Chip } from "@/components/ui/chip"

import type { VacancyAction } from "@/components/pages/pipeline-overview-page"

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

interface VacancyDetail {
  description?: string | null
  enriched_jd?: Record<string, unknown> | string | null
  technical_requirements?: unknown[]
  benefits?: unknown[]
  salary_range?: { min?: number; max?: number; currency?: string } | null
  recruiter?: string | null
  manager_email?: string | null
}

interface VacancyPreviewProps {
  vacancy: VacancyLite
  isOpen: boolean
  onClose: () => void
  /** Stage-aware action computed by the parent. CTA renders in the footer. */
  action: VacancyAction
  /** When the user clicks the CTA. Parent handles routing/modal mount. */
  onAction: (action: VacancyAction, vacancy: VacancyLite) => void
  /** Optional prev/next navigation across the visible vacancy list. */
  vacancies?: VacancyLite[]
  currentIndex?: number
  onNavigate?: (index: number) => void
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
}: VacancyPreviewProps) {
  const t = useTranslations("pipelineOverview")

  // ── Hooks (all above any early return — Rules of Hooks discipline) ──
  const [detail, setDetail] = useState<VacancyDetail | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const panelRef = useRef<HTMLDivElement | null>(null)

  // Lazy-fetch vacancy detail when opened or when vacancy changes.
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
          enriched_jd: (x.enriched_jd as Record<string, unknown> | string | null) ?? null,
          technical_requirements: (x.technical_requirements as unknown[]) ?? [],
          benefits: (x.benefits as unknown[]) ?? [],
          salary_range: (x.salary_range as { min?: number; max?: number; currency?: string } | null) ?? null,
          recruiter: (x.recruiter as string) ?? null,
          manager_email: (x.manager_email as string) ?? null,
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
  }, [isOpen, vacancy?.id])

  // ESC closes the preview.
  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [isOpen, onClose])

  // Prev/next handlers (only if navigator props supplied).
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

  // ── Hooks above this line — early returns from here on are safe. ──
  if (!isOpen || !vacancy) return null

  const updatedLabel = formatDate(vacancy.updated_at)
  const stageEnteredLabel = formatDate(vacancy.stage_entered_at)
  const hasNav = onNavigate && vacancies.length > 1

  return (
    <div
      ref={panelRef}
      className="h-full bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle flex flex-col w-full"
      role="dialog"
      aria-label={`Visualizar vaga ${vacancy.title}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 px-4 py-3 border-b border-lia-border-subtle">
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

      {/* Meta badges */}
      <div className="px-4 py-3 flex flex-wrap gap-1.5 border-b border-lia-border-subtle">
        {vacancy.seniority_level && (
          <Chip variant="neutral" muted className="text-xs">
            {vacancy.seniority_level}
          </Chip>
        )}
        {vacancy.work_model && (
          <Chip variant="neutral" muted className="text-xs">
            {vacancy.work_model}
          </Chip>
        )}
        {vacancy.department && (
          <Chip variant="neutral" muted className="text-xs">
            {vacancy.department}
          </Chip>
        )}
        {vacancy.imported_from_ats && (
          <Chip variant="info" muted className="text-xs">
            <Database className="w-3 h-3 mr-1" />
            {vacancy.ats_source_label || t("vacancyCard.atsBadge")}
          </Chip>
        )}
        {vacancy.approval_status === "pendente" && (
          <Chip variant="warning" muted className="text-xs">
            {t("vacancyCard.approvalPending")}
          </Chip>
        )}
      </div>

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
        {/* Timeline */}
        <section>
          <h3 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
            Linha do tempo
          </h3>
          <dl className="text-xs text-lia-text-secondary space-y-1">
            <div className="flex justify-between">
              <dt>Status</dt>
              <dd className="font-medium text-lia-text-primary">{vacancy.status}</dd>
            </div>
            {stageEnteredLabel && (
              <div className="flex justify-between">
                <dt>Entrou no estágio</dt>
                <dd>{stageEnteredLabel}</dd>
              </div>
            )}
            {updatedLabel && (
              <div className="flex justify-between">
                <dt>Atualizada</dt>
                <dd>{updatedLabel}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt>{t("vacancyCard.candidatesCount", { count: vacancy.candidate_count ?? 0 })}</dt>
              <dd>
                <Users className="w-3 h-3 inline" />
              </dd>
            </div>
          </dl>
        </section>

        {/* Manager + location */}
        <section>
          <h3 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
            Responsáveis
          </h3>
          <div className="text-xs text-lia-text-secondary space-y-1.5">
            {vacancy.manager && (
              <div className="flex items-center gap-1.5">
                <User className="w-3 h-3" />
                <span className="text-lia-text-primary">Gestor: {vacancy.manager}</span>
              </div>
            )}
            {detail?.recruiter && (
              <div className="flex items-center gap-1.5">
                <User className="w-3 h-3" />
                <span className="text-lia-text-primary">Recrutador: {detail.recruiter}</span>
              </div>
            )}
            {vacancy.location && (
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3 h-3" />
                <span>{vacancy.location}</span>
              </div>
            )}
            {vacancy.department && (
              <div className="flex items-center gap-1.5">
                <Building2 className="w-3 h-3" />
                <span>{vacancy.department}</span>
              </div>
            )}
          </div>
        </section>

        {/* JD / Description */}
        <section>
          <h3 className="text-xs font-medium text-lia-text-secondary uppercase tracking-wide mb-2">
            Descrição
          </h3>
          {isLoadingDetail ? (
            <div className="space-y-2">
              <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse" />
              <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse w-5/6" />
              <div className="h-3 bg-lia-bg-tertiary rounded animate-pulse w-4/6" />
            </div>
          ) : detailError ? (
            <p className="text-xs text-status-error">Erro ao carregar detalhes: {detailError}</p>
          ) : detail?.description ? (
            <p className="text-xs text-lia-text-secondary whitespace-pre-wrap line-clamp-6">
              {detail.description}
            </p>
          ) : (
            <p className="text-xs text-lia-text-tertiary italic">
              Sem descrição. Use o botão abaixo para revisar e enriquecer.
            </p>
          )}
        </section>
      </div>

      {/* Footer CTA */}
      <div className="px-4 py-3 border-t border-lia-border-subtle bg-lia-bg-secondary">
        <button
          onClick={() => onAction(action, vacancy)}
          disabled={"disabled" in action ? action.disabled : false}
          className="w-full px-3 py-2 rounded-lg text-xs font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors motion-reduce:transition-none"
        >
          {action.label}
        </button>
      </div>
    </div>
  )
}

function formatDate(iso: string | null | undefined): string | null {
  if (!iso) return null
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return null
    return d.toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" })
  } catch {
    return null
  }
}
