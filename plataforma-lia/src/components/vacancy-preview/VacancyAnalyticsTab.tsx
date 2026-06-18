"use client"

/**
 * VacancyAnalyticsTab — aba "📊 Análise" do painel de preview de vaga.
 *
 * Exibe métricas operacionais da vaga:
 *  - Funil stage-to-stage com taxa de conversão entre estágios
 *  - KPIs: taxa geral, TTH, total candidatos, percentil da empresa
 *  - Fontes de candidatos top
 *
 * Data source: GET /api/v1/job-vacancies/{id}/analytics → JobAnalyticsResponse
 * Rules of Hooks: todos os hooks antes de qualquer return condicional.
 * Design tokens: DS v4.2.2. Sem hardcode de hex ou spacing.
 */
import { useQuery } from "@tanstack/react-query"
import {
  BarChart3, TrendingUp, Clock, Users, UserCheck,
  MessageSquare, Gift, CheckCircle, ArrowDown,
} from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"

export interface VacancyAnalyticsTabProps {
  jobId: string
  companyId?: string
}

// ── Types matching backend JobAnalyticsResponse ──────────────────────────────

interface FunnelStageItem {
  stage: string
  count: number
  conversion_rate: number // stage-to-stage %
  avg_days: number
}

interface JobAnalyticsData {
  vacancy_id: string
  vacancy_title: string
  funnel: FunnelStageItem[]
  total_candidates: number
  total_hired: number
  overall_conversion_rate: number
  avg_time_to_hire: number
  avg_time_to_first_response: number
  top_source: string
  weekly_trend: number
  avg_lia_score: number
  position_percentile: number
}

// ── Constants ─────────────────────────────────────────────────────────────────

const STAGE_LABELS: Record<string, string> = {
  sourcing: "Sourcing",
  initial: "Recebidos",
  pending_gate1: "Aguardando",
  screening: "Triagem",
  triagem: "Triagem",
  interview: "Entrevista",
  entrevista: "Entrevista",
  interview_1: "Entrevista 1",
  interview_2: "Entrevista 2",
  offer: "Oferta",
  proposta: "Oferta",
  hired: "Contratado",
  contratado: "Contratado",
}

// Rejection stages are excluded from the advancement funnel
const REJECTION_STAGES = new Set(["rejected", "reprovado", "archived", "arquivado"])

// ── Sub-components ─────────────────────────────────────────────────────────────

function StageRow({
  stage,
  count,
  maxCount,
  isHired,
}: {
  stage: string
  count: number
  maxCount: number
  isHired: boolean
}) {
  const label = STAGE_LABELS[stage] ?? stage
  const barPct = maxCount > 0 ? Math.round((count / maxCount) * 100) : 0

  const icon = isHired ? (
    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
  ) : stage === "offer" || stage === "proposta" ? (
    <Gift className="w-3.5 h-3.5 text-violet-400 flex-shrink-0" />
  ) : stage === "interview" || stage === "entrevista" || stage.startsWith("interview_") ? (
    <UserCheck className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
  ) : stage === "screening" || stage === "triagem" ? (
    <MessageSquare className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
  ) : (
    <Users className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
  )

  return (
    <div className="flex items-center gap-2">
      {icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-xs text-gray-600 truncate">{label}</span>
          <span className={`text-xs font-semibold tabular-nums ml-2 ${isHired ? "text-emerald-600" : "text-gray-800"}`}>
            {count}
          </span>
        </div>
        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${isHired ? "bg-emerald-400" : "bg-blue-400"}`}
            style={{ width: `${barPct}%` }}
          />
        </div>
      </div>
    </div>
  )
}

function ConversionConnector({ pct }: { pct: number }) {
  const color =
    pct >= 50 ? "text-emerald-600 bg-emerald-50 border-emerald-200" :
    pct >= 25 ? "text-amber-600 bg-amber-50 border-amber-200" :
                "text-rose-600 bg-rose-50 border-rose-200"

  return (
    <div className="flex items-center gap-1.5 pl-5">
      <ArrowDown className="w-3 h-3 text-gray-300 flex-shrink-0" />
      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${color}`}>
        {pct.toFixed(1)}% avançaram
      </span>
    </div>
  )
}

function KpiCard({
  label,
  value,
  sub,
  icon,
}: {
  label: string
  value: string
  sub?: string
  icon: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-md border border-gray-200 p-3 flex flex-col gap-0.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-gray-500">{label}</span>
        <span className="text-gray-300">{icon}</span>
      </div>
      <span className="text-xl font-bold text-gray-900 font-['Inter'] tabular-nums leading-tight">
        {value}
      </span>
      {sub && <span className="text-[10px] text-gray-400">{sub}</span>}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export function VacancyAnalyticsTab({ jobId }: VacancyAnalyticsTabProps) {
  const { data, isLoading, isError, refetch } = useQuery<JobAnalyticsData>({
    queryKey: ["vacancy-analytics-v2", jobId],
    queryFn: async ({ signal }) => {
      const res = await fetch(`/api/backend-proxy/job-vacancies/${jobId}/analytics`, {
        signal: signal ?? AbortSignal.timeout(12_000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      return (json?.data ?? json) as JobAnalyticsData
    },
    enabled: !!jobId,
    staleTime: 60_000,
    retry: 1,
  })

  // Rules of Hooks: all hooks above — safe early returns below.
  if (isLoading) return <HubLoadingState message="Carregando métricas..." />
  if (isError) return <HubErrorState onRetry={() => refetch()} />

  // Filter out rejection stages for funnel display
  const funnelStages = (data?.funnel ?? []).filter(
    (s) => !REJECTION_STAGES.has(s.stage)
  )
  const maxCount = funnelStages[0]?.count ?? data?.total_candidates ?? 1

  const convRate =
    data?.overall_conversion_rate != null
      ? `${data.overall_conversion_rate.toFixed(1)}%`
      : "—"

  const tth =
    data?.avg_time_to_hire != null && data.avg_time_to_hire > 0
      ? `${Math.round(data.avg_time_to_hire)}d`
      : "—"

  const percentile =
    data?.position_percentile != null
      ? `Top ${100 - data.position_percentile}%`
      : "—"

  return (
    <div className="flex flex-col gap-4 p-3 bg-white" data-testid="vacancy-analytics-tab">

      {/* ── Funil stage-to-stage ─────────────────────────────────────────── */}
      <section aria-labelledby="funnel-title">
        <h3 id="funnel-title" className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <BarChart3 className="w-4 h-4 text-gray-400" />
          Funil
          {data?.total_candidates != null && (
            <span className="ml-auto text-xs text-gray-400 font-normal">
              {data.total_candidates} candidatos
            </span>
          )}
        </h3>

        {funnelStages.length === 0 ? (
          <p className="text-xs text-gray-400 italic px-1">Sem candidatos no funil ainda.</p>
        ) : (
          <div className="bg-white rounded-md border border-gray-200 p-3 flex flex-col gap-2">
            {funnelStages.map((stage, idx) => {
              const isHired = stage.stage === "hired" || stage.stage === "contratado"
              const isLast = idx === funnelStages.length - 1
              const showConnector = !isLast && !isHired && idx < funnelStages.length - 1

              return (
                <div key={stage.stage}>
                  <StageRow
                    stage={stage.stage}
                    count={stage.count}
                    maxCount={maxCount}
                    isHired={isHired}
                  />
                  {showConnector && funnelStages[idx + 1] && (
                    <div className="mt-1.5 mb-0.5">
                      <ConversionConnector pct={funnelStages[idx + 1].conversion_rate} />
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </section>

      {/* ── KPIs ─────────────────────────────────────────────────────────── */}
      <section aria-labelledby="performance-title">
        <h3 id="performance-title" className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-gray-400" />
          Performance
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <KpiCard
            label="Conversão Geral"
            value={convRate}
            icon={<TrendingUp className="w-3.5 h-3.5" />}
          />
          <KpiCard
            label="Tempo Médio (hire)"
            value={tth}
            icon={<Clock className="w-3.5 h-3.5" />}
          />
          <KpiCard
            label="Candidatos"
            value={String(data?.total_candidates ?? 0)}
            sub={`${data?.total_hired ?? 0} contratados`}
            icon={<Users className="w-3.5 h-3.5" />}
          />
          <KpiCard
            label="Vs. empresa"
            value={percentile}
            sub="conversão relativa"
            icon={<BarChart3 className="w-3.5 h-3.5" />}
          />
        </div>
      </section>

    </div>
  )
}
