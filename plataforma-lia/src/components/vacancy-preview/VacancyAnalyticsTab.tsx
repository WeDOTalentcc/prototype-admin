"use client"

/**
 * VacancyAnalyticsTab — aba "📊 Análise" do painel de preview de vaga.
 *
 * Exibe métricas operacionais da vaga:
 *  - Pipeline funil: total → triagem → entrevista → oferta → contratados
 *  - Performance: taxa de conversão + tempo para preencher
 *  - Previsão IA: placeholder (dados do endpoint de forecast — TODO)
 *
 * Data source: /api/backend-proxy/job-vacancies/{id}/analytics → FastAPI
 * Rules of Hooks: todos os hooks acima de qualquer return condicional.
 * Design tokens: DS v4.2.2 (sem hardcode de hex ou spacing).
 */
import { useQuery } from "@tanstack/react-query"
import { BarChart3, TrendingUp, Clock, Users, UserCheck, MessageSquare, Gift, CheckCircle } from "lucide-react"
import { HubLoadingState, HubErrorState } from "@/components/settings/_shared"

export interface VacancyAnalyticsTabProps {
  jobId: string
  companyId?: string
}

interface VacancyMetrics {
  funnel: {
    total: number
    screening: number
    interview: number
    offer: number
    hired: number
  }
  performance: {
    time_to_fill_days: number | null
    conversion_rate: number | null
  }
}

interface KpiCardProps {
  label: string
  value: string | number
  icon?: React.ReactNode
  trend?: string
  trendPositive?: boolean
  sublabel?: string
}

function KpiCard({ label, value, icon, trend, trendPositive, sublabel }: KpiCardProps) {
  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500">{label}</span>
        {icon && <span className="text-gray-400">{icon}</span>}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900 font-['Inter'] tabular-nums">{value}</span>
        {sublabel && <span className="text-xs text-gray-400">{sublabel}</span>}
      </div>
      {trend && (
        <span className={`text-xs ${trendPositive ? "text-emerald-600" : "text-rose-600"}`}>{trend}</span>
      )}
    </div>
  )
}

function FunnelBar({ label, count, total, icon }: { label: string; count: number; total: number; icon: React.ReactNode }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1 text-xs text-gray-600">
          <span className="text-gray-400">{icon}</span>
          <span>{label}</span>
        </div>
        <span className="text-xs font-medium text-gray-900 tabular-nums">{count}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
          aria-label={`${pct}%`}
        />
      </div>
      <span className="text-[10px] text-gray-400 tabular-nums">{pct}%</span>
    </div>
  )
}

export function VacancyAnalyticsTab({ jobId }: VacancyAnalyticsTabProps) {
  const {
    data,
    isLoading,
    isError,
    refetch,
  } = useQuery<VacancyMetrics>({
    queryKey: ["vacancy-analytics", jobId],
    queryFn: async ({ signal }) => {
      const res = await fetch(`/api/backend-proxy/job-vacancies/${jobId}/analytics`, {
        signal: signal ?? AbortSignal.timeout(12_000),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      // Suporte a response envelope {ok, data: {...}} e resposta plana
      return (json?.data ?? json) as VacancyMetrics
    },
    enabled: !!jobId,
    staleTime: 60_000,
    retry: 1,
  })

  // Rules of Hooks: todos os hooks acima — early returns seguros abaixo.
  if (isLoading) return <HubLoadingState message="Carregando métricas..." />
  if (isError) return <HubErrorState onRetry={() => refetch()} />

  const funnel = data?.funnel ?? { total: 0, screening: 0, interview: 0, offer: 0, hired: 0 }
  const performance = data?.performance ?? { time_to_fill_days: null, conversion_rate: null }

  const convRate =
    performance.conversion_rate != null
      ? `${(performance.conversion_rate * 100).toFixed(1)}%`
      : "—"

  const timeToFill =
    performance.time_to_fill_days != null
      ? performance.time_to_fill_days
      : "—"

  const timeToFillSublabel =
    performance.time_to_fill_days != null ? "dias" : undefined

  return (
    <div className="flex flex-col gap-4 p-3 bg-white" data-testid="vacancy-analytics-tab">
      {/* Seção: Pipeline Funil */}
      <section aria-labelledby="funnel-title">
        <h3 id="funnel-title" className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <BarChart3 className="w-4 h-4 text-gray-400" />
          Pipeline
        </h3>
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4 flex flex-col gap-3">
          <FunnelBar
            label="Total"
            count={funnel.total}
            total={funnel.total}
            icon={<Users className="w-3.5 h-3.5" />}
          />
          <div className="border-t border-gray-100" />
          <FunnelBar
            label="Triagem"
            count={funnel.screening}
            total={funnel.total}
            icon={<MessageSquare className="w-3.5 h-3.5" />}
          />
          <FunnelBar
            label="Entrevista"
            count={funnel.interview}
            total={funnel.total}
            icon={<UserCheck className="w-3.5 h-3.5" />}
          />
          <FunnelBar
            label="Oferta"
            count={funnel.offer}
            total={funnel.total}
            icon={<Gift className="w-3.5 h-3.5" />}
          />
          <FunnelBar
            label="Contratados"
            count={funnel.hired}
            total={funnel.total}
            icon={<CheckCircle className="w-3.5 h-3.5 text-emerald-500" />}
          />
        </div>
      </section>

      {/* Seção: Performance */}
      <section aria-labelledby="performance-title">
        <h3 id="performance-title" className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-gray-400" />
          Performance
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <KpiCard
            label="Taxa de Conversão"
            value={convRate}
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <KpiCard
            label="Tempo para Preencher"
            value={timeToFill}
            sublabel={timeToFillSublabel}
            icon={<Clock className="w-4 h-4" />}
          />
        </div>
      </section>

      {/* Seção: Previsão IA — TODO: integrar endpoint de forecast */}
      <section aria-labelledby="forecast-title">
        <h3 id="forecast-title" className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <BarChart3 className="w-4 h-4 text-gray-400" />
          Previsão IA
        </h3>
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-4">
          <p className="text-xs text-gray-400 italic">
            {/* TODO: integrar /api/v1/job-vacancies/{id}/forecast quando endpoint disponível */}
            Previsão de fechamento em breve.
          </p>
        </div>
      </section>
    </div>
  )
}
