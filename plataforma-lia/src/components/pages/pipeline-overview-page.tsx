"use client"

import { useState, useEffect, useCallback } from "react"
import { cn } from "@/lib/utils"
import {
  GitBranch,
  Users,
  ChevronRight,
  Loader2,
  AlertCircle,
  RefreshCw,
  ArrowRight,
  ChevronDown,
} from "lucide-react"
import { Button } from "@/components/ui/button"

interface CandidatePreview {
  vc_id: string
  vacancy_id: string
  name: string
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
  candidates: CandidatePreview[]
}

const STAGE_EMOJI_MAP: Record<string, string> = {
  sourcing: "🔍",
  screening: "📋",
  long_list: "📝",
  short_list: "✅",
  interview_hr: "🤝",
  technical_test: "💻",
  english_test: "🌐",
  interview_technical: "⚙️",
  interview_manager: "👔",
  reference_check: "📞",
  offer: "📄",
  hired: "🎉",
  contratado: "🎉",
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

export function PipelineOverviewPage() {
  const [stages, setStages] = useState<PipelineStageWithCount[]>([])
  const [selectedStage, setSelectedStage] = useState<string | null>(null)
  const [totalCandidates, setTotalCandidates] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)

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
  const allCandidates = selectedStageData?.candidates ?? []
  const visibleCandidates = allCandidates.slice(0, visibleCount)
  // Only show "Load more" when there are more locally-fetched candidates to reveal
  const hasMore = visibleCount < allCandidates.length

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
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-lia-bg-primary">
      {/* Header */}
      <div className="px-6 py-5 border-b border-lia-border-subtle flex-shrink-0">
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

      {/* Pipeline Flow */}
      <div className="flex-shrink-0 px-6 py-6 overflow-x-auto">
        {stages.length === 0 ? (
          <div className="flex items-center gap-2 text-lia-text-disabled text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>
              Nenhuma etapa encontrada. Configure o pipeline da empresa nas
              Configurações.
            </span>
          </div>
        ) : (
          <div className="flex items-start gap-1 min-w-max">
            {stages.map((stage, index) => {
              const isSelected = selectedStage === stage.name
              const emoji = STAGE_EMOJI_MAP[stage.name] || stage.icon || "🔷"
              const isLast = index === stages.length - 1

              return (
                <div key={stage.name} className="flex items-center">
                  <button
                    onClick={() => handleStageClick(stage.name)}
                    className={cn(
                      "group flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all duration-200 cursor-pointer w-[120px] flex-shrink-0",
                      isSelected
                        ? "border-lia-text-primary bg-lia-bg-tertiary shadow-sm"
                        : "border-transparent bg-lia-bg-secondary hover:border-lia-border-medium hover:bg-lia-bg-tertiary"
                    )}
                  >
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ backgroundColor: stage.color || "#6B7280" }}
                    />

                    <span className="text-xl leading-none">{emoji}</span>

                    <span
                      className={cn(
                        "text-xs font-medium text-center leading-tight line-clamp-2",
                        isSelected
                          ? "text-lia-text-primary"
                          : "text-lia-text-secondary group-hover:text-lia-text-primary"
                      )}
                    >
                      {stage.display_name}
                    </span>

                    <div
                      className={cn(
                        "px-2.5 py-0.5 rounded-full text-xs font-semibold min-w-[32px] text-center",
                        isSelected
                          ? "bg-lia-text-primary text-lia-bg-primary"
                          : stage.count > 0
                          ? "bg-lia-interactive-active text-lia-text-primary"
                          : "bg-lia-bg-tertiary text-lia-text-disabled"
                      )}
                    >
                      {stage.count}
                    </div>
                  </button>

                  {!isLast && (
                    <ArrowRight className="w-4 h-4 text-lia-text-disabled flex-shrink-0 mx-0.5" />
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Summary chips — top stages by count */}
      {stages.some((s) => s.count > 0) && (
        <div className="px-6 pb-4 flex-shrink-0">
          <div className="flex gap-2 flex-wrap">
            {stages
              .filter((s) => s.count > 0)
              .sort((a, b) => b.count - a.count)
              .slice(0, 6)
              .map((s) => (
                <button
                  key={s.name}
                  onClick={() => handleStageClick(s.name)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors",
                    selectedStage === s.name
                      ? "bg-lia-text-primary text-lia-bg-primary border-transparent"
                      : "bg-lia-bg-secondary text-lia-text-secondary border-lia-border-subtle hover:border-lia-border-medium hover:text-lia-text-primary"
                  )}
                >
                  <div
                    className="w-1.5 h-1.5 rounded-full"
                    style={{ backgroundColor: s.color || "#6B7280" }}
                  />
                  {s.display_name}
                  <span className="font-bold">{s.count}</span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* Candidates panel */}
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
            <div className="px-6 py-3 border-b border-lia-border-subtle bg-lia-bg-secondary flex-shrink-0 flex items-center justify-between">
              <div className="flex items-center gap-2">
                {selectedStageData && (
                  <div
                    className="w-2.5 h-2.5 rounded-full"
                    style={{
                      backgroundColor: selectedStageData.color || "#6B7280",
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
                      <div
                        key={`${candidate.vc_id}-${idx}`}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg bg-lia-bg-secondary hover:bg-lia-bg-tertiary transition-colors cursor-default"
                      >
                        <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-lia-interactive-active text-xs font-semibold text-lia-text-primary">
                          {getInitials(candidate.name)}
                        </div>

                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-lia-text-primary truncate">
                            {candidate.name}
                          </p>
                        </div>

                        <ChevronRight className="w-4 h-4 text-lia-text-disabled flex-shrink-0" />
                      </div>
                    ))}
                  </div>

                  {/* Load more — client-side pagination over the already-fetched list */}
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

                  {/* Notice when total exceeds fetched preview */}
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
  )
}
