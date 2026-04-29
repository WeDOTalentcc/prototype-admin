"use client"

import React, { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { cn } from "@/lib/utils"
import {
  GitBranch,
  Users,
  Loader2,
  AlertCircle,
  RefreshCw,
  ChevronDown,
  Eye,
  ExternalLink,
  Clock,
  Gauge,
  Brain,
  Target,
  Code,
  Globe,
  Fingerprint,
  Info,
  Calendar,
  User,
  Briefcase,
  FileText,
  Wand2,
  ListChecks,
  ShieldCheck,
  Send,
  Radio,
  Archive,
  Database,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { PageTabNavigation } from "@/components/ui/page-tab-navigation"
import type { PageTab } from "@/components/ui/page-tab-navigation"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { formatScorePercent } from "@/lib/design-tokens"
import { getStageIcon, getStageColor, translateStatus } from "@/lib/pipeline-stage-maps"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"
import { useTranslations } from "next-intl"
import { useSearchParams } from "next/navigation"
import { PipelineRail, type PipelineRailNode } from "@/components/pages/pipeline-overview/pipeline-rail"
import { JobCampaignBadge } from "@/components/jobs/JobCampaignBadge"
import dynamic from "next/dynamic"

const GeneralScoreModal = dynamic(
  () => import("@/components/modals/general-score-modal").then(m => ({ default: m.GeneralScoreModal })),
  { ssr: false }
)
const BigFiveModal = dynamic(
  () => import("@/components/big-five-modal").then(m => ({ default: m.BigFiveModal })),
  { ssr: false }
)
const RubricEvaluationModal = dynamic(
  () => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })),
  { ssr: false }
)
const TechnicalTestModal = dynamic(
  () => import("@/components/modals/technical-test-modal").then(m => ({ default: m.TechnicalTestModal })),
  { ssr: false }
)
const EnglishTestModal = dynamic(
  () => import("@/components/modals/english-test-modal").then(m => ({ default: m.EnglishTestModal })),
  { ssr: false }
)
const TriagemDetailsModal = dynamic(
  () => import("@/components/triagem-details-modal").then(m => ({ default: m.TriagemDetailsModal })),
  { ssr: false }
)
const CandidatePreview = dynamic(
  () => import("@/components/candidate-preview").then(m => ({ default: m.CandidatePreview })),
  { ssr: false }
)

interface CandidateItem {
  vc_id: string
  vacancy_id: string
  candidate_id?: string
  name: string
  vacancy_title?: string | null
  sub_status?: string | null
  stage_entered_at?: string | null
  lia_score?: number | null
  match_percentage?: number | null
  wsi_score?: number | null
  lia_opinion_score?: number | null
  score_breakdown?: Record<string, unknown> | null
  technical_test_score?: number | null
  english_test_score?: number | null
  big_five_data?: Record<string, number> | null
  vacancy_manager?: string | null
  vacancy_open_date?: string | null
  vacancy_level?: string | null
  vacancy_work_model?: string | null
  vacancy_contract_type?: string | null
  vacancy_department?: string | null
}

interface PipelineStageWithCount {
  id: string
  name: string
  display_name: string
  stage_order: number
  color: string
  icon: string
  is_active: boolean
  is_final: boolean
  is_rejection: boolean
  stage_category: string
  action_behavior?: string
  count: number
  candidates: CandidateItem[]
}

// ─── Job Lifecycle (Vagas mode) — Task #430 ──────────────────────────────────

interface JobLifecycleVacancy {
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

interface JobLifecycleStage {
  stage: string
  display_name: string
  color: string
  stage_order: number
  count: number
  vacancies: JobLifecycleVacancy[]
}

const JOB_LIFECYCLE_STAGE_ICONS: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties; strokeWidth?: number }>> = {
  ats_importada: Database,
  rascunho: FileText,
  enriquecida: Wand2,
  wsi_config: ListChecks,
  aguardando_aprovacao: ShieldCheck,
  publicada: Send,
  ao_vivo: Radio,
  encerrada: Archive,
}

function getJobLifecycleStageIcon(stageKey: string): React.ComponentType<{ className?: string; style?: React.CSSProperties; strokeWidth?: number }> {
  return JOB_LIFECYCLE_STAGE_ICONS[stageKey] || Briefcase
}

// Map backend stage keys to i18n keys under pipelineOverview.stages.*
const JOB_LIFECYCLE_STAGE_I18N: Record<string, string> = {
  ats_importada: "ats_imported",
  rascunho: "draft",
  enriquecida: "enriched",
  wsi_config: "wsi_configured",
  aguardando_aprovacao: "pending_approval",
  publicada: "published",
  ao_vivo: "live",
  encerrada: "closed",
}

function lifecycleStageLabel(
  t: (key: string) => string,
  stageKey: string,
  fallback: string
): string {
  const i18nKey = JOB_LIFECYCLE_STAGE_I18N[stageKey]
  if (!i18nKey) return fallback
  try {
    return t(`stages.${i18nKey}`)
  } catch {
    return fallback
  }
}

interface VacancyCta {
  label: string
  href: string
}

// Stage-aware "continuar" routing for vacancy cards.
// Stages that still need work on the JD/wizard side land on the job detail
// page, while published/live vacancies open the candidate kanban directly.
function getVacancyCta(
  stageKey: string,
  vacancyId: string,
  t: (key: string) => string
): VacancyCta {
  const jobUrl = `/jobs/${vacancyId}`
  const kanbanUrl = `/funil-de-talentos?tab=kanban&vacancy=${vacancyId}`
  switch (stageKey) {
    case "ats_importada":
    case "rascunho":
      return { label: t("vacancyCard.openWizard"), href: jobUrl }
    case "enriquecida":
      return { label: t("vacancyCard.openEnrichment"), href: jobUrl }
    case "wsi_config":
      return { label: t("vacancyCard.openWsi"), href: jobUrl }
    case "aguardando_aprovacao":
      return { label: t("vacancyCard.openApproval"), href: jobUrl }
    case "publicada":
    case "ao_vivo":
      return { label: t("vacancyCard.openKanban"), href: kanbanUrl }
    case "encerrada":
      return { label: t("vacancyCard.openClosed"), href: jobUrl }
    default:
      return { label: t("vacancyCard.openKanban"), href: kanbanUrl }
  }
}

function getVibrantColor(stageName: string, fallbackHex: string): string {
  return getStageColor(stageName, fallbackHex)
}

const PAGE_SIZE = 20

function getInitials(name: string): string {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase()
}

function getTimeInStage(stageEnteredAt: string | null | undefined): string | null {
  if (!stageEnteredAt) return null
  try {
    const entered = new Date(stageEnteredAt)
    if (Number.isNaN(entered.getTime())) return null
    const now = new Date()
    const diffMs = now.getTime() - entered.getTime()
    if (diffMs < 0) return null
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return "hoje"
    if (diffDays === 1) return "1 dia"
    return `${diffDays} dias`
  } catch {
    return null
  }
}

function hexToRgba(hex: string, alpha: number): string {
  const clean = hex.replace("#", "")
  const r = parseInt(clean.substring(0, 2), 16)
  const g = parseInt(clean.substring(2, 4), 16)
  const b = parseInt(clean.substring(4, 6), 16)
  if (isNaN(r) || isNaN(g) || isNaN(b)) return `rgba(99, 102, 241, ${alpha})`
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

function calculateGeneralScore(candidate: CandidateItem): number | null {
  const scores: number[] = []
  if (candidate.lia_score != null) scores.push(candidate.lia_score)
  if (candidate.lia_opinion_score != null) scores.push(candidate.lia_opinion_score)
  if (candidate.match_percentage != null) scores.push(candidate.match_percentage)
  if (candidate.technical_test_score != null) scores.push(candidate.technical_test_score)
  if (candidate.english_test_score != null) scores.push(candidate.english_test_score)
  if (scores.length === 0) return null
  return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
}

type ModalType = "geral" | "triagem" | "cv" | "tecnico" | "ingles" | "b5" | null

export function PipelineOverviewPage() {
  const tOverview = useTranslations("pipelineOverview")
  const mode = useUIPreferencesStore((s) => s.pipelineOverviewMode)
  const setMode = useUIPreferencesStore((s) => s.setPipelineOverviewMode)

  const searchParams = useSearchParams()
  useEffect(() => {
    const view = searchParams?.get("view")
    if (view === "vagas" || view === "candidatos") {
      if (view !== mode) setMode(view)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const [stages, setStages] = useState<PipelineStageWithCount[]>([])
  const [selectedStage, setSelectedStage] = useState<string | null>(null)
  const [totalCandidates, setTotalCandidates] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

  const [previewCandidate, setPreviewCandidate] = useState<CandidateItem | null>(null)
  const [showPreview, setShowPreview] = useState(false)

  const [activeModal, setActiveModal] = useState<ModalType>(null)
  const [modalCandidate, setModalCandidate] = useState<CandidateItem | null>(null)

  // ─── Vagas mode state (Task #430) ──────────────────────────────────────────
  const [lifecycleStages, setLifecycleStages] = useState<JobLifecycleStage[]>([])
  const [selectedLifecycleStage, setSelectedLifecycleStage] = useState<string | null>(null)
  const [totalVacancies, setTotalVacancies] = useState(0)
  const [lifecycleLoading, setLifecycleLoading] = useState(false)
  const [lifecycleError, setLifecycleError] = useState<string | null>(null)

  const fetchPipelineOverview = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/backend-proxy/pipeline-overview")
      if (!res.ok) throw new Error(`Erro ao carregar pipeline (${res.status})`)
      const data = await res.json()

      const pipeline: PipelineStageWithCount[] = (data.pipeline || []).sort(
        (a: PipelineStageWithCount, b: PipelineStageWithCount) =>
          a.stage_order - b.stage_order
      )
      setStages(pipeline)
      setTotalCandidates(data.total_candidates || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido")
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchLifecycleOverview = useCallback(async () => {
    setLifecycleLoading(true)
    setLifecycleError(null)
    try {
      const res = await fetch("/api/backend-proxy/jobs-lifecycle-overview")
      if (!res.ok) throw new Error(`Erro ao carregar vagas (${res.status})`)
      const data = await res.json()
      const items: JobLifecycleStage[] = (data.stages || []).sort(
        (a: JobLifecycleStage, b: JobLifecycleStage) => a.stage_order - b.stage_order
      )
      setLifecycleStages(items)
      setTotalVacancies(data.total_vacancies || 0)
    } catch (err) {
      setLifecycleError(err instanceof Error ? err.message : "Erro desconhecido")
    } finally {
      setLifecycleLoading(false)
    }
  }, [])

  useEffect(() => {
    if (mode === "candidatos") {
      fetchPipelineOverview()
    } else {
      fetchLifecycleOverview()
    }
  }, [mode, fetchPipelineOverview, fetchLifecycleOverview])

  const handleRefresh = useCallback(() => {
    if (mode === "candidatos") fetchPipelineOverview()
    else fetchLifecycleOverview()
  }, [mode, fetchPipelineOverview, fetchLifecycleOverview])

  const handleLifecycleStageClick = useCallback((stageKey: string) => {
    setSelectedLifecycleStage((prev) => (prev === stageKey ? null : stageKey))
  }, [])

  const selectedLifecycleStageData = lifecycleStages.find(
    (s) => s.stage === selectedLifecycleStage
  )

  const handleStageClick = (stageName: string) => {
    if (selectedStage === stageName) {
      setSelectedStage(null)
    } else {
      setSelectedStage(stageName)
      setVisibleCount(PAGE_SIZE)
    }
  }

  const selectedStageData = stages.find((s) => s.name === selectedStage)
  const allCandidates = useMemo(() => selectedStageData?.candidates ?? [], [selectedStageData])
  const visibleCandidates = allCandidates.slice(0, visibleCount)
  const hasMore = visibleCount < allCandidates.length

  const handleOpenPreview = useCallback((candidate: CandidateItem) => {
    setPreviewCandidate(candidate)
    setShowPreview(true)
  }, [])

  const handleClosePreview = useCallback(() => {
    setShowPreview(false)
    setPreviewCandidate(null)
  }, [])

  const handleNavigatePreview = useCallback((index: number) => {
    if (allCandidates[index]) {
      setPreviewCandidate(allCandidates[index])
    }
  }, [allCandidates])

  const previewIndex = useMemo(() => {
    if (!previewCandidate) return 0
    return allCandidates.findIndex(c => c.vc_id === previewCandidate.vc_id)
  }, [previewCandidate, allCandidates])

  const handleOpenScoreModal = useCallback((candidate: CandidateItem, type: ModalType) => {
    setModalCandidate(candidate)
    setActiveModal(type)
  }, [])

  const handleCloseModal = useCallback(() => {
    setActiveModal(null)
    setModalCandidate(null)
  }, [])

  const handleOpenKanban = useCallback((candidate: CandidateItem) => {
    if (candidate.vacancy_id) {
      window.open(`/funil-de-talentos?tab=kanban&vacancy=${candidate.vacancy_id}`, "_blank")
    }
  }, [])

  const activeLoading = mode === "candidatos" ? loading : lifecycleLoading
  const activeError = mode === "candidatos" ? error : lifecycleError

  if (activeLoading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-lia-bg-primary">
        <div className="flex flex-col items-center gap-3 text-lia-text-secondary">
          <Loader2 className="w-8 h-8 animate-spin" />
          <span className="text-sm">
            {mode === "candidatos" ? "Carregando funil..." : "Carregando vagas..."}
          </span>
        </div>
      </div>
    )
  }

  if (activeError) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-lia-bg-primary">
        <div className="flex flex-col items-center gap-4 text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-red-400" />
          <p className="text-lia-text-secondary text-sm">{activeError}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex-1 flex h-full overflow-hidden bg-lia-bg-primary">
        <div className={cn(
          "flex flex-col flex-1 min-w-0 overflow-hidden transition-all duration-300",
          showPreview && "mr-0"
        )}>
          <div className="px-4 pt-3 pb-0 flex-shrink-0 border-b border-lia-border-subtle">
            <div className="flex items-center justify-between mb-2">
              <h1 className="text-lg font-semibold text-lia-text-primary">
                Visão Global
              </h1>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                className="gap-2 h-8 px-3"
              >
                <RefreshCw className="w-4 h-4" />
                Atualizar
              </Button>
            </div>

            <PageTabNavigation
              tabs={[
                {
                  id: "vagas",
                  label: tOverview("toggle.vacancies"),
                  icon: Briefcase,
                  count: totalVacancies > 0 ? totalVacancies : null,
                } satisfies PageTab,
                {
                  id: "candidatos",
                  label: tOverview("toggle.candidates"),
                  icon: Users,
                  count: totalCandidates > 0 ? totalCandidates : null,
                } satisfies PageTab,
              ]}
              activeTab={mode}
              onTabChange={(id) => setMode(id as "candidatos" | "vagas")}
            />

            <div className="flex items-center gap-2 mt-2 mb-1">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs text-lia-text-secondary">
                <span className="font-semibold text-lia-text-primary">
                  {mode === "candidatos" ? totalCandidates : totalVacancies}
                </span>{" "}
                {mode === "candidatos"
                  ? tOverview("toggle.candidatesLabel")
                  : tOverview("toggle.vacanciesLabel")}
              </span>
            </div>
          </div>

          {mode === "candidatos" && (
          <>
          <div className="flex-shrink-0 px-6 py-6 relative" style={{ overflow: "visible" }}>
            <PipelineRail
              nodes={stages.map((stage): PipelineRailNode => ({
                key: stage.name,
                displayName: stage.display_name,
                color: getVibrantColor(stage.name, stage.color || "#2D2D2D"),
                count: stage.count,
                Icon: getStageIcon(stage.name, stage.action_behavior, stage.stage_category),
                isSelected: selectedStage === stage.name,
                onClick: () => handleStageClick(stage.name),
              }))}
              emptyMessage={
                <div className="flex items-center gap-2 text-lia-text-disabled text-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span>
                    Nenhuma etapa encontrada. Configure o funil da empresa nas
                    Configurações.
                  </span>
                </div>
              }
            />
          </div>

          {stages.some((s) => s.count > 0) && (
            <div className="px-6 pb-4 flex-shrink-0">
              <div className="flex gap-2 flex-wrap">
                {stages
                  .filter((s) => s.count > 0)
                  .sort((a, b) => b.count - a.count)
                  .slice(0, 6)
                  .map((s) => {
                    const isActive = selectedStage === s.name
                    const pillColor = getVibrantColor(s.name, s.color || "#2D2D2D")
                    return (
                      <button
                        key={s.name}
                        onClick={() => handleStageClick(s.name)}
                        className={cn(
                          "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border transition-colors",
                          isActive
                            ? "text-lia-text-primary border-lia-border-medium"
                            : "bg-lia-bg-primary text-lia-text-secondary border-lia-border-subtle hover:border-lia-border-medium hover:text-lia-text-primary"
                        )}
                        style={isActive ? {
                          backgroundColor: hexToRgba(pillColor, 0.08),
                          borderColor: pillColor,
                        } : undefined}
                      >
                        <div
                          className="w-2 h-2 rounded-full flex-shrink-0"
                          style={{ backgroundColor: pillColor }}
                        />
                        {s.display_name}
                        <span className="font-semibold">{s.count}</span>
                      </button>
                    )
                  })}
              </div>
            </div>
          )}

          <div className="flex-1 min-h-0 overflow-hidden">
            {!selectedStage ? (
              <div className="h-full flex flex-col items-center justify-center gap-3 text-lia-text-disabled">
                <GitBranch className="w-10 h-10 opacity-30" />
                <p className="text-sm">
                  Clique em uma etapa para ver os candidatos naquela fase
                </p>
              </div>
            ) : (
              <div className="h-full flex flex-col">
                <div className="px-6 py-3 bg-lia-bg-secondary flex-shrink-0 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {selectedStageData && (
                      <div
                        className="w-2.5 h-2.5 rounded-full"
                        style={{
                          backgroundColor: selectedStageData.color || "#2D2D2D",
                        }}
                      />
                    )}
                    <span className="text-sm font-semibold text-lia-text-primary">
                      {selectedStageData?.display_name}
                    </span>
                    <span className="text-xs text-lia-text-disabled">
                      {selectedStageData?.count ?? 0} candidato
                      {(selectedStageData?.count ?? 0) !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedStage(null)}
                    className="text-xs text-lia-text-disabled hover:text-lia-text-secondary transition-colors"
                  >
                    Fechar
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto px-6 py-3">
                  {allCandidates.length === 0 && (selectedStageData?.count ?? 0) === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 gap-2 text-lia-text-disabled">
                      <Users className="w-8 h-8 opacity-30" />
                      <p className="text-sm">Nenhum candidato nesta etapa</p>
                    </div>
                  ) : (
                    <>
                      <div className="space-y-2">
                        {visibleCandidates.map((candidate, idx) => (
                          <PipelineCandidateCard
                            key={`${candidate.vc_id}-${idx}`}
                            candidate={candidate}
                            stageColor={selectedStageData?.color || "#2D2D2D"}
                            onOpenPreview={handleOpenPreview}
                            onOpenKanban={handleOpenKanban}
                            onOpenScoreModal={handleOpenScoreModal}
                          />
                        ))}
                      </div>

                      {hasMore && (
                        <div className="mt-4 flex justify-center">
                          <button
                            onClick={() => setVisibleCount((n) => n + PAGE_SIZE)}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-lia-text-secondary hover:text-lia-text-primary bg-lia-bg-secondary hover:bg-lia-bg-tertiary border border-lia-border-subtle transition-colors"
                          >
                            <ChevronDown className="w-4 h-4" />
                            Carregar mais
                            {allCandidates.length > visibleCount && (
                              <span className="text-lia-text-disabled">
                                ({allCandidates.length - visibleCount} restantes)
                              </span>
                            )}
                          </button>
                        </div>
                      )}

                      {(selectedStageData?.count ?? 0) > allCandidates.length && allCandidates.length > 0 && (
                        <p className="mt-3 text-center text-xs text-lia-text-disabled">
                          Exibindo {allCandidates.length} de {selectedStageData?.count} candidatos nesta etapa
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
          </>
          )}

          {mode === "vagas" && (
          <>
            <div className="flex-shrink-0 px-6 py-6 relative" style={{ overflow: "visible" }}>
              <PipelineRail
                nodes={lifecycleStages.map((stage): PipelineRailNode => ({
                  key: stage.stage,
                  displayName: lifecycleStageLabel(tOverview, stage.stage, stage.display_name),
                  color: stage.color || "#2D2D2D",
                  count: stage.count,
                  Icon: getJobLifecycleStageIcon(stage.stage),
                  isSelected: selectedLifecycleStage === stage.stage,
                  onClick: () => handleLifecycleStageClick(stage.stage),
                }))}
                emptyMessage={
                  <div className="flex items-center gap-2 text-lia-text-disabled text-sm">
                    <AlertCircle className="w-4 h-4" />
                    <span>{tOverview("empty.noVacanciesHint")}</span>
                  </div>
                }
              />
            </div>

            <div className="flex-1 min-h-0 overflow-hidden">
              {!selectedLifecycleStage ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-lia-text-disabled">
                  <Briefcase className="w-10 h-10 opacity-30" />
                  <p className="text-sm">Clique em uma etapa para ver as vagas naquela fase</p>
                </div>
              ) : (
                <div className="h-full flex flex-col">
                  <div className="px-6 py-3 bg-lia-bg-secondary flex-shrink-0 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {selectedLifecycleStageData && (
                        <div
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ backgroundColor: selectedLifecycleStageData.color || "#2D2D2D" }}
                        />
                      )}
                      <span className="text-sm font-semibold text-lia-text-primary">
                        {selectedLifecycleStageData
                          ? lifecycleStageLabel(
                              tOverview,
                              selectedLifecycleStageData.stage,
                              selectedLifecycleStageData.display_name
                            )
                          : ""}
                      </span>
                      <span className="text-xs text-lia-text-disabled">
                        {tOverview("vacancyCard.candidatesCount", {
                          count: selectedLifecycleStageData?.count ?? 0,
                        })}
                      </span>
                    </div>
                    <button
                      onClick={() => setSelectedLifecycleStage(null)}
                      className="text-xs text-lia-text-disabled hover:text-lia-text-secondary transition-colors"
                    >
                      {tOverview("close")}
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto px-6 py-3">
                    {(selectedLifecycleStageData?.vacancies?.length ?? 0) === 0 ? (
                      <div className="flex flex-col items-center justify-center h-32 gap-2 text-lia-text-disabled">
                        <Briefcase className="w-8 h-8 opacity-30" />
                        <p className="text-sm">{tOverview("empty.noVacancies")}</p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {selectedLifecycleStageData!.vacancies.map((vacancy) => (
                          <PipelineVacancyCard
                            key={vacancy.id}
                            vacancy={vacancy}
                            stageKey={selectedLifecycleStageData!.stage}
                            stageColor={selectedLifecycleStageData!.color || "#2D2D2D"}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
          )}
        </div>

        {showPreview && previewCandidate && (
          <div className="flex-shrink-0 w-[420px] relative pl-2">
            <div className="bg-lia-bg-primary h-full overflow-hidden rounded-xl border border-lia-border-subtle shadow-sm">
              <CandidatePreview
                candidate={candidateItemToRecord(previewCandidate)}
                isOpen={showPreview}
                onClose={handleClosePreview}
                candidates={allCandidates.map(candidateItemToRecord)}
                currentIndex={previewIndex >= 0 ? previewIndex : 0}
                onNavigateCandidate={handleNavigatePreview}
                jobId={previewCandidate.vacancy_id}
              />
            </div>
          </div>
        )}

        {activeModal === "geral" && modalCandidate && (
          <GeneralScoreModal
            isOpen={true}
            onClose={handleCloseModal}
            candidate={candidateItemToRecord(modalCandidate)}
          />
        )}
        {activeModal === "triagem" && modalCandidate && (
          <TriagemDetailsModal
            isOpen={true}
            onClose={handleCloseModal}
            candidate={candidateItemToRecord(modalCandidate) as unknown as import("@/components/pages/candidates/types").Candidate}
            jobVacancyId={modalCandidate.vacancy_id}
          />
        )}
        {activeModal === "cv" && modalCandidate && (
          <RubricEvaluationModal
            isOpen={true}
            onClose={handleCloseModal}
            evaluation={{
              score: modalCandidate.match_percentage ?? 0,
              requirements: [],
            }}
            candidateId={modalCandidate.candidate_id || modalCandidate.vc_id}
            candidateName={modalCandidate.name}
            jobId={modalCandidate.vacancy_id}
          />
        )}
        {activeModal === "tecnico" && modalCandidate && (
          <TechnicalTestModal
            isOpen={true}
            onClose={handleCloseModal}
            candidate={candidateItemToRecord(modalCandidate)}
          />
        )}
        {activeModal === "ingles" && modalCandidate && (
          <EnglishTestModal
            isOpen={true}
            onClose={handleCloseModal}
            candidate={candidateItemToRecord(modalCandidate)}
          />
        )}
        {activeModal === "b5" && modalCandidate && (
          <BigFiveModal
            isOpen={true}
            onClose={handleCloseModal}
            candidate={candidateItemToRecord(modalCandidate)}
          />
        )}
      </div>
    </TooltipProvider>
  )
}

function candidateItemToRecord(c: CandidateItem): Record<string, unknown> {
  const triagemVal = c.lia_score ?? c.lia_opinion_score ?? c.wsi_score
  const cvFitVal = c.match_percentage
  const techVal = c.technical_test_score
  const engVal = c.english_test_score

  return {
    id: c.candidate_id || c.vc_id,
    candidateId: c.candidate_id || c.vc_id,
    vc_id: c.vc_id,
    vacancy_id: c.vacancy_id,
    name: c.name,
    fullName: c.name,
    email: "",
    phone: "",
    vacancy_title: c.vacancy_title,
    sub_status: c.sub_status,
    stage_entered_at: c.stage_entered_at,
    liaScore: triagemVal,
    score: c.lia_opinion_score,
    lia_score: c.lia_score,
    skillsMatch: cvFitVal,
    fitScore: cvFitVal,
    cvFitNota: cvFitVal,
    match_percentage: c.match_percentage,
    wsi_score: c.wsi_score,
    triagemNota: triagemVal,
    screeningNota: triagemVal,
    technicalNota: techVal,
    technicalTestScore: techVal,
    technicalTest: techVal != null ? {
      status: "completed",
      score: techVal,
    } : undefined,
    englishNota: engVal,
    englishTestScore: engVal,
    englishTest: engVal != null ? {
      status: "completed",
      score: engVal,
    } : undefined,
    bigFive: c.big_five_data,
    bigFiveScores: c.big_five_data,
    score_breakdown: c.score_breakdown,
  }
}

interface PipelineCandidateCardProps {
  candidate: CandidateItem
  stageColor: string
  onOpenPreview: (c: CandidateItem) => void
  onOpenKanban: (c: CandidateItem) => void
  onOpenScoreModal: (c: CandidateItem, type: ModalType) => void
}

function getSlaInfo(openDate: string | null | undefined): { days: number; isLate: boolean } | null {
  if (!openDate) return null
  try {
    const d = new Date(openDate)
    if (isNaN(d.getTime())) return null
    const days = Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24))
    if (days <= 0) return null
    return { days, isLate: days > 30 }
  } catch {
    return null
  }
}

function PipelineCandidateCard({
  candidate,
  stageColor,
  onOpenPreview,
  onOpenKanban,
  onOpenScoreModal,
}: PipelineCandidateCardProps) {
  const timeInStage = getTimeInStage(candidate.stage_entered_at)
  const generalScore = calculateGeneralScore(candidate)

  const triagemScore = candidate.lia_score ?? candidate.lia_opinion_score ?? candidate.wsi_score
  const cvScore = candidate.match_percentage
  const techScore = candidate.technical_test_score
  const engScore = candidate.english_test_score
  const b5Data = candidate.big_five_data
  const b5Avg = b5Data
    ? Math.round(
        Object.values(b5Data).filter((v): v is number => typeof v === "number")
          .reduce((a, b) => a + b, 0) /
        Math.max(1, Object.values(b5Data).filter((v): v is number => typeof v === "number").length)
      )
    : null

  const scores = [
    { id: "geral" as const, icon: Gauge, value: generalScore, label: "Nota Geral" },
    { id: "triagem" as const, icon: Brain, value: triagemScore, label: "Triagem LIA/WSI" },
    { id: "cv" as const, icon: Target, value: cvScore, label: "Match CV vs Vaga" },
    { id: "tecnico" as const, icon: Code, value: techScore, label: "Teste Técnico" },
    { id: "ingles" as const, icon: Globe, value: engScore, label: "Teste de Inglês" },
    { id: "b5" as const, icon: Fingerprint, value: b5Avg, label: "Big Five" },
  ]

  const visibleScores = scores.filter(s => s.value != null)

  const shortVacancyId = candidate.vacancy_id
    ? `#${candidate.vacancy_id.replace(/-/g, "").slice(0, 7).toUpperCase()}`
    : null

  const sla = getSlaInfo(candidate.vacancy_open_date)

  const openDateLabel = candidate.vacancy_open_date
    ? (() => {
        try {
          const d = new Date(candidate.vacancy_open_date)
          if (isNaN(d.getTime())) return null
          return d.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })
        } catch {
          return null
        }
      })()
    : null

  const vacancyBadges = [
    candidate.vacancy_level ? { key: "level", label: candidate.vacancy_level } : null,
    candidate.vacancy_work_model ? { key: "work_model", label: candidate.vacancy_work_model } : null,
    candidate.vacancy_contract_type ? { key: "contract_type", label: candidate.vacancy_contract_type } : null,
    candidate.vacancy_department ? { key: "department", label: candidate.vacancy_department } : null,
  ].filter(Boolean) as { key: string; label: string }[]

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-lg bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors border border-transparent hover:border-lia-border-subtle group cursor-pointer"
      onClick={() => onOpenPreview(candidate)}
      role="button"
      aria-label={`Ver detalhes de ${candidate.name}`}
    >
      <div
        className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-semibold text-white"
        style={{ backgroundColor: stageColor }}
      >
        {getInitials(candidate.name)}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium text-lia-text-primary truncate">
            {candidate.name}
          </p>
          {candidate.sub_status && (
            <span className="flex-shrink-0 inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-lia-bg-tertiary text-lia-text-secondary border border-lia-border-subtle">
              {translateStatus(candidate.sub_status)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          {candidate.vacancy_title && (
            <span className="truncate max-w-[200px]">{candidate.vacancy_title}</span>
          )}
          {timeInStage && (
            <>
              {candidate.vacancy_title && <span className="text-lia-text-disabled">·</span>}
              <span className="flex items-center gap-0.5 text-lia-text-disabled flex-shrink-0">
                <Clock className="w-3 h-3" />
                {timeInStage}
              </span>
            </>
          )}
        </div>

        {(shortVacancyId || candidate.vacancy_manager || openDateLabel) && (
          <div className="flex items-center gap-2 text-[10px] text-lia-text-disabled mt-0.5">
            {shortVacancyId && (
              <span className="font-mono font-medium text-lia-text-secondary">{shortVacancyId}</span>
            )}
            {candidate.vacancy_manager && (
              <>
                {shortVacancyId && <span>·</span>}
                <span className="flex items-center gap-0.5 truncate max-w-[120px]">
                  <User className="w-2.5 h-2.5 flex-shrink-0" />
                  {candidate.vacancy_manager}
                </span>
              </>
            )}
            {openDateLabel && (
              <>
                {(shortVacancyId || candidate.vacancy_manager) && <span>·</span>}
                <span className="flex items-center gap-0.5 flex-shrink-0">
                  <Calendar className="w-2.5 h-2.5" />
                  {openDateLabel}
                </span>
              </>
            )}
          </div>
        )}

        {(vacancyBadges.length > 0 || sla) && (
          <div className="flex items-center gap-1 mt-1 flex-wrap">
            {vacancyBadges.map((b) => (
              <Chip variant="neutral" muted
                key={b.key}
                className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-[10px] px-1.5 py-0 h-auto leading-4 rounded-sm"
              >
                {b.label}
              </Chip>
            ))}
            {sla && (
              <Chip variant="neutral" muted
                className={`border whitespace-nowrap text-[10px] px-1.5 py-0 h-auto leading-4 rounded-sm font-semibold ${
                  sla.isLate
                    ? "bg-status-error/10 border-status-error/30 text-status-error"
                    : "bg-lia-bg-tertiary border-lia-border-subtle text-lia-text-secondary"
                }`}
              >
                {sla.days}d {sla.isLate ? "de atraso" : "aberta"}
              </Chip>
            )}
          </div>
        )}
      </div>

      <div className="flex-shrink-0 border-l border-lia-border-subtle pl-3">
        {visibleScores.length > 0 ? (
          <div className="flex items-center gap-1.5">
            {visibleScores.map(({ id, icon: Icon, value, label }) => (
              <Tooltip key={id}>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      onOpenScoreModal(candidate, id)
                    }}
                    className="flex items-center gap-0.5 cursor-pointer hover:scale-105 transition-transform rounded-full"
                    aria-label={`${label}: ${value != null ? formatScorePercent(value, 0) : "N/A"}`}
                  >
                    <Icon className="w-3.5 h-3.5 text-lia-text-secondary" strokeWidth={2} />
                    <span className="text-[11px] font-semibold text-lia-text-secondary">
                      {formatScorePercent(value as number, 0)}
                    </span>
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="text-xs">
                  {label}: {formatScorePercent(value as number, 0)}
                </TooltipContent>
              </Tooltip>
            ))}
          </div>
        ) : (
          <div className="flex items-center gap-1 text-lia-text-disabled">
            <Info className="w-3 h-3" />
            <span className="text-[10px]">Sem scores</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onOpenPreview(candidate)
              }}
              className="p-1.5 rounded-xl hover:bg-lia-bg-primary transition-colors text-lia-text-secondary hover:text-lia-text-primary"
              aria-label="Visualizar candidato"
            >
              <Eye className="w-4 h-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">Preview</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onOpenKanban(candidate)
              }}
              className="p-1.5 rounded-xl hover:bg-lia-bg-primary transition-colors text-lia-text-secondary hover:text-lia-text-primary"
              aria-label="Abrir no Kanban"
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">Abrir no Kanban</TooltipContent>
        </Tooltip>
      </div>
    </div>
  )
}

// ─── Pipeline Vacancy Card (Vagas mode — Task #430) ──────────────────────────

interface PipelineVacancyCardProps {
  vacancy: JobLifecycleVacancy
  stageKey: string
  stageColor: string
}

function PipelineVacancyCard({ vacancy, stageKey, stageColor }: PipelineVacancyCardProps) {
  const tCard = useTranslations("pipelineOverview")
  const timeInStage = getTimeInStage(vacancy.stage_entered_at)
  const cta = getVacancyCta(stageKey, vacancy.id, tCard)

  const updatedLabel = vacancy.updated_at
    ? (() => {
        try {
          const d = new Date(vacancy.updated_at as string)
          if (isNaN(d.getTime())) return null
          return d.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })
        } catch {
          return null
        }
      })()
    : null

  const shortVacancyId = vacancy.id
    ? `#${vacancy.id.replace(/-/g, "").slice(0, 7).toUpperCase()}`
    : null

  const metaBadges = [
    vacancy.seniority_level ? { key: "level", label: vacancy.seniority_level } : null,
    vacancy.work_model ? { key: "work_model", label: vacancy.work_model } : null,
    vacancy.department ? { key: "department", label: vacancy.department } : null,
  ].filter(Boolean) as { key: string; label: string }[]

  const handleOpen = () => {
    if (typeof window !== "undefined") {
      window.open(cta.href, "_blank")
    }
  }

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-lg bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors border border-transparent hover:border-lia-border-subtle group cursor-pointer"
      onClick={handleOpen}
      role="button"
      aria-label={`${cta.label}: ${vacancy.title}`}
    >
      <div
        className="w-9 h-9 rounded-lg flex-shrink-0 flex items-center justify-center"
        style={{ backgroundColor: hexToRgba(stageColor, 0.12) }}
      >
        <Briefcase className="w-4 h-4" style={{ color: stageColor }} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium text-lia-text-primary truncate">
            {vacancy.title}
          </p>
          {vacancy.imported_from_ats && (
            <span
              className="flex-shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border"
              style={{
                backgroundColor: hexToRgba("#8A8F98", 0.1),
                borderColor: hexToRgba("#8A8F98", 0.4),
                color: "var(--lia-text-secondary)",
              }}
              title={
                vacancy.ats_source_label
                  ? tCard("vacancyCard.atsBadgeTitleNamed", { source: vacancy.ats_source_label })
                  : tCard("vacancyCard.atsBadgeTitle")
              }
            >
              <Database className="w-2.5 h-2.5" />
              {tCard("vacancyCard.atsBadge")}
            </span>
          )}
          {vacancy.approval_status === "pendente" && (
            <span
              className="flex-shrink-0 inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border"
              style={{
                backgroundColor: hexToRgba("#D19960", 0.12),
                borderColor: hexToRgba("#D19960", 0.5),
                color: "#D19960",
              }}
            >
              <ShieldCheck className="w-2.5 h-2.5" />
              {tCard("vacancyCard.approvalPending")}
            </span>
          )}
          {vacancy.id && (
            <JobCampaignBadge jobId={vacancy.id} className="flex-shrink-0" />
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          {vacancy.department && (
            <span className="truncate max-w-[180px]">{vacancy.department}</span>
          )}
          {vacancy.location && (
            <>
              {vacancy.department && <span className="text-lia-text-disabled">·</span>}
              <span className="truncate max-w-[160px]">{vacancy.location}</span>
            </>
          )}
          {timeInStage && (
            <>
              {(vacancy.department || vacancy.location) && (
                <span className="text-lia-text-disabled">·</span>
              )}
              <span className="flex items-center gap-0.5 text-lia-text-disabled flex-shrink-0">
                <Clock className="w-3 h-3" />
                {timeInStage}
              </span>
            </>
          )}
        </div>

        {(shortVacancyId || vacancy.manager || updatedLabel) && (
          <div className="flex items-center gap-2 text-[10px] text-lia-text-disabled mt-0.5">
            {shortVacancyId && (
              <span className="font-mono font-medium text-lia-text-secondary">
                {shortVacancyId}
              </span>
            )}
            {vacancy.manager && (
              <>
                {shortVacancyId && <span>·</span>}
                <span className="flex items-center gap-0.5 truncate max-w-[120px]">
                  <User className="w-2.5 h-2.5 flex-shrink-0" />
                  {vacancy.manager}
                </span>
              </>
            )}
            {updatedLabel && (
              <>
                {(shortVacancyId || vacancy.manager) && <span>·</span>}
                <span className="flex items-center gap-0.5 flex-shrink-0">
                  <Calendar className="w-2.5 h-2.5" />
                  {updatedLabel}
                </span>
              </>
            )}
          </div>
        )}

        {metaBadges.length > 0 && (
          <div className="flex items-center gap-1 mt-1 flex-wrap">
            {metaBadges.map((b) => (
              <Chip variant="neutral" muted
                key={b.key}
                className="bg-lia-bg-tertiary border border-lia-border-subtle text-lia-text-primary font-medium whitespace-nowrap text-[10px] px-1.5 py-0 h-auto leading-4 rounded-sm"
              >
                {b.label}
              </Chip>
            ))}
          </div>
        )}
      </div>

      <div className="flex-shrink-0 border-l border-lia-border-subtle pl-3 flex items-center gap-1">
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex items-center gap-1 text-lia-text-secondary">
              <Users className="w-3.5 h-3.5" />
              <span className="text-[11px] font-semibold">
                {vacancy.candidate_count ?? 0}
              </span>
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">
            {tCard("vacancyCard.candidatesCount", { count: vacancy.candidate_count ?? 0 })}
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="flex items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleOpen()
              }}
              className="p-1.5 rounded-xl hover:bg-lia-bg-primary transition-colors text-lia-text-secondary hover:text-lia-text-primary"
              aria-label={cta.label}
            >
              <ExternalLink className="w-4 h-4" />
            </button>
          </TooltipTrigger>
          <TooltipContent side="top" className="text-xs">{cta.label}</TooltipContent>
        </Tooltip>
      </div>
    </div>
  )
}
