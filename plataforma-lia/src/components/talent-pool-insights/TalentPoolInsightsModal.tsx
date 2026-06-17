"use client"

/**
 * TalentPoolInsightsModal — Juicybox 2-column pattern
 *
 * Opens via `lia:open_modal` {modal_id: "talent_pool_insights", data: {job_id, job_title}}
 * or directly as <TalentPoolInsightsModal isOpen jobId="..." />.
 *
 * Fetches GET /api/backend-proxy/analytics/talent-pool-insights/{jobId}
 * which proxies to FastAPI /api/v1/analytics/predictions/talent-pool/{jobId}.
 *
 * Design: 2-column grid (KPIs left, skills right) + premium locked section.
 * DS tokens: bg-white rounded-md shadow-sm border border-gray-200 p-4
 * Modal container: rounded-xl (NEVER rounded-md)
 *
 * Created 2026-06-17.
 */

import { Lock, TrendingUp, Clock, Target, BarChart2 } from "lucide-react"
import { useQuery } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { HubLoadingState } from "@/components/settings/_shared/HubLoadingState"
import { HubErrorState } from "@/components/settings/_shared/HubErrorState"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TalentPoolMetrics {
  total_candidates: number
  in_screening: number
  in_interview: number
  in_offer: number
  hired: number
  rejected: number
  conversion_rate: number
  avg_time_to_fill_days: number | null
}

interface HiringProbability {
  probability: number
  confidence: "high" | "medium" | "low"
}

interface PipelinePrediction {
  closure_probability: number
  estimated_days_to_close: number | null
  confidence_level: string
}

interface TopSkill {
  skill: string
  count: number
  percentage: number
}

export interface TalentPoolData {
  job_id: string
  metrics: TalentPoolMetrics
  hiring_probability: HiringProbability
  pipeline_prediction: PipelinePrediction
  top_skills: TopSkill[]
}

export interface TalentPoolInsightsModalProps {
  isOpen: boolean
  onClose: () => void
  jobId: string
  jobTitle?: string
}

// ---------------------------------------------------------------------------
// Internal: ConfidenceBadge
// ---------------------------------------------------------------------------

function ConfidenceBadge({ level }: { level: "high" | "medium" | "low" | string }) {
  if (level === "high") {
    return (
      <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded">
        Alta confiança
      </span>
    )
  }
  if (level === "medium") {
    return (
      <span className="text-xs bg-amber-50 text-amber-700 px-2 py-0.5 rounded">
        Média confiança
      </span>
    )
  }
  return (
    <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">
      Dados limitados
    </span>
  )
}

// ---------------------------------------------------------------------------
// Internal: KPICard
// ---------------------------------------------------------------------------

interface KPICardProps {
  icon: React.ReactNode
  label: string
  value: string
  badge?: React.ReactNode
}

function KPICard({ icon, label, value, badge }: KPICardProps) {
  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="text-gray-400">{icon}</div>
        {badge}
      </div>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold text-gray-900 font-['Inter'] tabular-nums leading-none">
        {value}
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function TalentPoolInsightsModal({
  isOpen,
  onClose,
  jobId,
  jobTitle,
}: TalentPoolInsightsModalProps) {
  const router = useRouter()

  const { data, isLoading, error, refetch } = useQuery<TalentPoolData>({
    queryKey: ["talent-pool-insights", jobId],
    queryFn: async () => {
      const resp = await fetch(
        `/api/backend-proxy/analytics/talent-pool-insights/${encodeURIComponent(jobId)}`,
        { credentials: "include" }
      )
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      return resp.json() as Promise<TalentPoolData>
    },
    enabled: isOpen && Boolean(jobId),
    staleTime: 60_000,
  })

  function handleViewFull() {
    onClose()
    router.push("/indicadores")
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        data-testid="talent-pool-insights-modal"
        className="max-w-2xl rounded-xl bg-white border border-gray-200 overflow-y-auto max-h-[85vh]"
        aria-describedby="talent-pool-insights-desc"
      >
        {/* ── Header ── */}
        <DialogHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-gray-100 flex items-center justify-center">
                <BarChart2 className="w-4 h-4 text-gray-500" />
              </div>
              <div>
                <DialogTitle className="text-sm font-semibold text-gray-900">
                  Talent Pool Insights
                </DialogTitle>
                {jobTitle && (
                  <p className="text-xs text-gray-500 mt-0.5">{jobTitle}</p>
                )}
              </div>
            </div>
            {data && (
              <span className="text-xs text-gray-400 shrink-0">
                {data.metrics.total_candidates} candidatos
              </span>
            )}
          </div>
        </DialogHeader>

        <p id="talent-pool-insights-desc" className="sr-only">
          Painel de insights preditivos do talent pool para esta vaga.
        </p>

        {/* ── Loading / Error ── */}
        {isLoading && <HubLoadingState variant="inline" />}
        {error && !isLoading && (
          <HubErrorState
            message="Não foi possível carregar os insights."
            onRetry={refetch}
            variant="banner"
          />
        )}

        {/* ── Main content ── */}
        {data && (
          <div className="space-y-4">
            {/* 2-column grid */}
            <div className="grid md:grid-cols-2 gap-3">
              {/* Left column: KPI cards */}
              <div className="space-y-3">
                <KPICard
                  icon={<TrendingUp className="w-4 h-4" />}
                  label="Probabilidade de Contratação"
                  value={`${data.hiring_probability.probability.toFixed(0)}%`}
                  badge={<ConfidenceBadge level={data.hiring_probability.confidence} />}
                />

                <KPICard
                  icon={<Target className="w-4 h-4" />}
                  label="Probabilidade de Fechamento"
                  value={`${data.pipeline_prediction.closure_probability.toFixed(0)}%`}
                  badge={<ConfidenceBadge level={data.pipeline_prediction.confidence_level} />}
                />

                <KPICard
                  icon={<Clock className="w-4 h-4" />}
                  label="Tempo Estimado para Preencher"
                  value={
                    data.pipeline_prediction.estimated_days_to_close != null
                      ? `${data.pipeline_prediction.estimated_days_to_close} dias`
                      : data.metrics.avg_time_to_fill_days != null
                      ? `${data.metrics.avg_time_to_fill_days.toFixed(0)} dias`
                      : "—"
                  }
                />
              </div>

              {/* Right column: top skills */}
              <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4">
                <p className="text-sm font-semibold text-gray-700 mb-3">
                  Principais Skills
                </p>
                {data.top_skills.length === 0 && (
                  <p className="text-xs text-gray-400">Nenhuma skill disponível ainda.</p>
                )}
                <div className="space-y-2">
                  {data.top_skills.slice(0, 6).map((skill) => (
                    <div key={skill.skill} className="flex items-center gap-2">
                      <span
                        className="text-xs text-gray-600 truncate"
                        style={{ width: "6rem" }}
                        title={skill.skill}
                      >
                        {skill.skill}
                      </span>
                      <div className="flex-1 bg-gray-100 rounded h-1.5">
                        <div
                          className="bg-gray-900 h-1.5 rounded"
                          style={{ width: `${Math.min(skill.percentage, 100)}%` }}
                          aria-label={`${skill.percentage.toFixed(0)}%`}
                        />
                      </div>
                      <span className="text-xs text-gray-400 w-8 text-right tabular-nums">
                        {skill.percentage.toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>

                {/* Pipeline snapshot mini-stats */}
                <div className="mt-4 pt-3 border-t border-gray-100 grid grid-cols-3 gap-2">
                  {[
                    { label: "Triagem", value: data.metrics.in_screening },
                    { label: "Entrevista", value: data.metrics.in_interview },
                    { label: "Oferta", value: data.metrics.in_offer },
                  ].map((item) => (
                    <div key={item.label} className="text-center">
                      <p className="text-lg font-bold text-gray-900 tabular-nums">
                        {item.value}
                      </p>
                      <p className="text-xs text-gray-400">{item.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Premium locked section */}
            <div className="relative">
              <div
                className="opacity-40 pointer-events-none select-none"
                aria-hidden="true"
              >
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-white rounded-md border border-gray-200 p-4 h-24">
                    <div className="h-3 bg-gray-200 rounded w-24 mb-2" />
                    <div className="h-6 bg-gray-200 rounded w-16 mb-2" />
                    <div className="h-2 bg-gray-100 rounded w-20" />
                  </div>
                  <div className="bg-white rounded-md border border-gray-200 p-4 h-24">
                    <div className="h-3 bg-gray-200 rounded w-28 mb-2" />
                    <div className="h-6 bg-gray-200 rounded w-20 mb-2" />
                    <div className="h-2 bg-gray-100 rounded w-16" />
                  </div>
                </div>
              </div>
              <div
                className="absolute inset-0 flex items-center justify-center bg-white/70 rounded-md"
                aria-label="Recurso disponível no plano Enterprise"
              >
                <div className="text-center">
                  <Lock className="w-5 h-5 mx-auto text-gray-400 mb-1" />
                  <p className="text-xs text-gray-500">Disponível no plano Enterprise</p>
                  <button
                    type="button"
                    className="text-xs text-violet-600 mt-1 hover:underline focus:outline-none focus:underline"
                    onClick={() => {
                      onClose()
                      router.push("/planos")
                    }}
                  >
                    Upgrade Plan →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Footer ── */}
        <div className="flex justify-end mt-4 pt-4 border-t border-gray-100">
          <button
            type="button"
            onClick={handleViewFull}
            className="text-sm text-gray-900 hover:underline focus:outline-none focus:underline"
          >
            Ver análise completa →
          </button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
