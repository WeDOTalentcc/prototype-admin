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
  Search,
  FileText,
  ClipboardList,
  CheckCircle,
  UserCheck,
  MonitorPlay,
  Languages,
  Handshake,
  UserCog,
  Phone,
  FileCheck,
  Award,
  type LucideIcon,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { formatScorePercent } from "@/lib/design-tokens"
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
  count: number
  candidates: CandidateItem[]
}

const STAGE_ICON_MAP: Record<string, LucideIcon> = {
  sourcing: Search,
  screening: ClipboardList,
  long_list: FileText,
  short_list: CheckCircle,
  interview_hr: UserCheck,
  technical_test: MonitorPlay,
  english_test: Languages,
  interview_technical: Code,
  interview_manager: Handshake,
  reference_check: Phone,
  offer: FileCheck,
  hired: Award,
  contratado: Award,
}

const STAGE_VIBRANT_COLORS: Record<string, string> = {
  sourcing: "#5DA47A",
  screening: "#5DA47A",
  long_list: "#60BED1",
  short_list: "#60BED1",
  interview_hr: "#D19960",
  technical_test: "#D17060",
  english_test: "#D1A960",
  interview_technical: "#9860D1",
  interview_manager: "#9860D1",
  interview_final: "#9860D1",
  reference_check: "#D19960",
  offer: "#6078D1",
  proposal: "#6078D1",
  proposta: "#6078D1",
  hired: "#5DA47A",
  contratado: "#5DA47A",
  rejected: "#8A8F98",
  recusado: "#8A8F98",
}

function getVibrantColor(stageName: string, fallbackHex: string): string {
  return STAGE_VIBRANT_COLORS[stageName] || fallbackHex
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

const DOCK_MAX_SCALE = 1.4
const DOCK_NEIGHBOR_1_SCALE = 1.2
const DOCK_NEIGHBOR_2_SCALE = 1.1
const DOCK_INFLUENCE_RADIUS = 120

function usePipelineMagnifier(containerRef: React.RefObject<HTMLDivElement | null>) {
  const mouseXRef = useRef<number | null>(null)
  const [mouseX, setMouseX] = useState<number | null>(null)
  const rafId = useRef<number>(0)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    setPrefersReducedMotion(mq.matches)
    const handler = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (prefersReducedMotion) return
    const rect = containerRef.current?.getBoundingClientRect()
    if (!rect) return
    const x = e.clientX - rect.left + (containerRef.current?.scrollLeft ?? 0)
    mouseXRef.current = x
    if (!rafId.current) {
      rafId.current = requestAnimationFrame(() => {
        setMouseX(mouseXRef.current)
        rafId.current = 0
      })
    }
  }, [containerRef, prefersReducedMotion])

  const handleMouseLeave = useCallback(() => {
    mouseXRef.current = null
    if (rafId.current) {
      cancelAnimationFrame(rafId.current)
      rafId.current = 0
    }
    setMouseX(null)
  }, [])

  const getScale = useCallback((nodeIndex: number, nodeRefs: React.RefObject<(HTMLElement | null)[]>) => {
    if (mouseX === null || prefersReducedMotion) return 1
    const nodeEl = nodeRefs.current?.[nodeIndex]
    if (!nodeEl) return 1
    const nodeCenter = nodeEl.offsetLeft + nodeEl.offsetWidth / 2
    const distance = Math.abs(mouseX - nodeCenter)
    if (distance > DOCK_INFLUENCE_RADIUS) return 1

    const ratio = 1 - distance / DOCK_INFLUENCE_RADIUS
    const eased = Math.cos((1 - ratio) * Math.PI / 2)

    if (distance < DOCK_INFLUENCE_RADIUS * 0.33) {
      return 1 + (DOCK_MAX_SCALE - 1) * eased
    } else if (distance < DOCK_INFLUENCE_RADIUS * 0.66) {
      return 1 + (DOCK_NEIGHBOR_1_SCALE - 1) * eased
    } else {
      return 1 + (DOCK_NEIGHBOR_2_SCALE - 1) * eased
    }
  }, [mouseX, prefersReducedMotion])

  return { handleMouseMove, handleMouseLeave, getScale }
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

  const stagesScrollRef = useRef<HTMLDivElement>(null)
  const stageNodeRefs = useRef<(HTMLElement | null)[]>([])
  const { handleMouseMove, handleMouseLeave, getScale } = usePipelineMagnifier(stagesScrollRef)

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

  useEffect(() => {
    fetchPipelineOverview()
  }, [fetchPipelineOverview])

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

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-lia-bg-primary">
        <div className="flex flex-col items-center gap-3 text-lia-text-secondary">
          <Loader2 className="w-8 h-8 animate-spin" />
          <span className="text-sm">Carregando pipeline...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center h-full bg-lia-bg-primary">
        <div className="flex flex-col items-center gap-4 text-center max-w-sm">
          <AlertCircle className="w-10 h-10 text-red-400" />
          <p className="text-lia-text-secondary text-sm">{error}</p>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPipelineOverview}
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
          <div className="px-6 py-5 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-lg font-semibold text-lia-text-primary">
                  Visão do Pipeline
                </h1>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchPipelineOverview}
                className="gap-2 text-lia-text-secondary hover:text-lia-text-primary"
              >
                <RefreshCw className="w-4 h-4" />
                Atualizar
              </Button>
            </div>
          </div>

          <div className="flex-shrink-0 px-6 py-6 relative" style={{ overflow: "visible" }}>
            {stages.length === 0 ? (
              <div className="flex items-center gap-2 text-lia-text-disabled text-sm">
                <AlertCircle className="w-4 h-4" />
                <span>
                  Nenhuma etapa encontrada. Configure o pipeline da empresa nas
                  Configurações.
                </span>
              </div>
            ) : (
              <div
                ref={stagesScrollRef}
                className="overflow-x-auto scrollbar-none"
                style={{
                  scrollbarWidth: "none",
                  msOverflowStyle: "none",
                  clipPath: "inset(-30px 0 0 0)",
                }}
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
              >
              <div className="flex items-end gap-0 min-w-max px-1 pt-8 pb-2">
                {stages.map((stage, index) => {
                  const isSelected = selectedStage === stage.name
                  const isLast = index === stages.length - 1
                  const stageColor = getVibrantColor(stage.name, stage.color || "#2D2D2D")
                  const StageIcon = STAGE_ICON_MAP[stage.name] || GitBranch
                  const scale = getScale(index, stageNodeRefs)

                  return (
                    <div key={stage.name} className="flex items-center">
                      <button
                        ref={(el) => { stageNodeRefs.current[index] = el }}
                        onClick={() => handleStageClick(stage.name)}
                        className="group flex flex-col items-center gap-1.5 px-3 cursor-pointer origin-bottom motion-reduce:!transition-none"
                        style={{
                          transform: scale !== 1 ? `scale(${scale})` : undefined,
                          transition: "transform 0.15s cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                          willChange: scale !== 1 ? "transform" : "auto",
                        }}
                      >
                        <div
                          className="w-11 h-11 rounded-full flex items-center justify-center transition-all duration-200 border-2"
                          style={{
                            backgroundColor: isSelected
                              ? stageColor
                              : hexToRgba(stageColor, 0.10),
                            borderColor: stageColor,
                            boxShadow: isSelected
                              ? `0 0 0 3px ${hexToRgba(stageColor, 0.18)}`
                              : undefined,
                          }}
                        >
                          <StageIcon
                            className="w-[18px] h-[18px] transition-colors"
                            style={{
                              color: isSelected
                                ? "#fff"
                                : stageColor,
                            }}
                          />
                        </div>

                        <span
                          className={cn(
                            "text-xs font-medium text-center leading-tight whitespace-nowrap transition-colors",
                            isSelected
                              ? "text-lia-text-primary"
                              : "text-lia-text-secondary group-hover:text-lia-text-primary"
                          )}
                        >
                          {stage.display_name}
                        </span>

                        {stage.count > 0 ? (
                          <span
                            className="text-xs font-bold transition-colors"
                            style={{ color: stageColor }}
                          >
                            {stage.count}
                          </span>
                        ) : (
                          <span className="text-xs font-bold text-lia-text-disabled">
                            {stage.count}
                          </span>
                        )}
                      </button>

                      {!isLast && (
                        <div
                          className="h-px w-6 flex-shrink-0 self-center -mt-5"
                          style={{ backgroundColor: "var(--lia-border-default)" }}
                        />
                      )}
                    </div>
                  )
                })}
              </div>
              </div>
            )}
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

          <div className="flex-1 min-h-0 overflow-hidden border-t border-lia-border-subtle">
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
    cvFitScore: cvFitVal,
    match_percentage: c.match_percentage,
    wsi_score: c.wsi_score,
    triagemScore: triagemVal,
    screeningScore: triagemVal,
    technicalScore: techVal,
    technicalTestScore: techVal,
    technicalTest: techVal != null ? {
      status: "completed",
      score: techVal,
    } : undefined,
    englishScore: engVal,
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
    { id: "geral" as const, icon: Gauge, value: generalScore, label: "Score Geral" },
    { id: "triagem" as const, icon: Brain, value: triagemScore, label: "Triagem LIA/WSI" },
    { id: "cv" as const, icon: Target, value: cvScore, label: "Match CV vs Vaga" },
    { id: "tecnico" as const, icon: Code, value: techScore, label: "Teste Técnico" },
    { id: "ingles" as const, icon: Globe, value: engScore, label: "Teste de Inglês" },
    { id: "b5" as const, icon: Fingerprint, value: b5Avg, label: "Big Five" },
  ]

  const visibleScores = scores.filter(s => s.value != null)

  return (
    <div
      className="flex items-center gap-3 px-4 py-3 rounded-lg bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors border border-transparent hover:border-lia-border-subtle group"
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
              {candidate.sub_status}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-lia-text-secondary">
          {candidate.vacancy_title && (
            <span className="truncate max-w-[180px]">{candidate.vacancy_title}</span>
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
      </div>

      {visibleScores.length > 0 && (
        <div className="flex items-center gap-1.5 flex-shrink-0">
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
      )}

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
