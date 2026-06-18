"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  TrendingUp, TrendingDown, Users, Briefcase, Clock,
  AlertTriangle, BarChart3, LineChart, Lock, CheckCircle,
  Lightbulb, Info,
} from "lucide-react"
import { CHART_LIA, CHART_GRID } from "@/lib/chart-colors"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Period = "30d" | "90d" | "180d"

interface WeeklyTrend { week: string; hired: number; opened: number }

interface StageFunnelItem {
  stage: string; label: string; count: number
  pct_of_total: number; pct_from_prev: number | null
}

interface DashboardInsight {
  type: string; message: string; severity?: string; action?: string
}

interface StageVelocityItem {
  stage: string; label: string; avg_days: number; sample_count: number
}

interface SourceQualityItem {
  source: string; label: string; total: number; hired: number; conversion_rate: number
}

interface DashboardKPIs {
  period: string
  active_candidates: number
  open_vacancies: number
  avg_time_to_fill_days: number | null
  conversion_rate: number
  offer_acceptance_rate: number | null
  sla_at_risk: number
  hired_in_period: number
  weekly_trend: WeeklyTrend[]
  stage_funnel: StageFunnelItem[]
  insights: DashboardInsight[]
  pipeline_velocity: StageVelocityItem[]
  source_quality: SourceQualityItem[]
}

// ---------------------------------------------------------------------------
// KpiCard
// ---------------------------------------------------------------------------

interface KpiCardProps {
  label: string; value: string; trend?: number; trendLabel?: string
  icon: React.ReactNode; loading?: boolean
}

function KpiCard({ label, value, trend, trendLabel, icon, loading }: KpiCardProps) {
  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">{label}</span>
        <span className="text-gray-400">{icon}</span>
      </div>
      {loading
        ? <div className="h-8 w-24 bg-gray-100 rounded animate-pulse" />
        : <span className="text-3xl font-bold text-gray-900 font-['Inter'] tabular-nums">{value}</span>
      }
      {trend !== undefined && (
        <div className="flex items-center gap-1">
          {trend >= 0
            ? <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
            : <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
          }
          <span className={`text-xs ${trend >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
            {trend >= 0 ? "+" : ""}{trend}%
          </span>
          {trendLabel && <span className="text-xs text-gray-400">{trendLabel}</span>}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// BarChartSimple — with value labels
// ---------------------------------------------------------------------------

function BarChartSimple({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="flex items-end gap-2 h-36 pt-4">
      {data.map((d) => {
        const barH = Math.round((d.value / max) * 100)
        return (
          <div key={d.label} className="flex-1 flex flex-col items-center gap-0.5">
            {d.value > 0 && (
              <span className="text-[9px] font-medium text-gray-600 tabular-nums">{d.value}</span>
            )}
            <div
              className="w-full rounded-t-sm transition-all duration-300"
              style={{
                height: `${barH}%`,
                backgroundColor: CHART_LIA,
                minHeight: d.value > 0 ? "4px" : "0",
              }}
            />
            <span className="text-[9px] text-gray-400 truncate w-full text-center mt-0.5">{d.label}</span>
          </div>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// LineChartSimple — with dot on last point
// ---------------------------------------------------------------------------

function LineChartSimple({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  const w = 300; const h = 100
  const pts = data.map((d, i) => ({
    x: (i / Math.max(data.length - 1, 1)) * w,
    y: h - (d.value / max) * (h - 8),
  }))
  const polyPts = pts.map((p) => `${p.x},${p.y}`).join(" ")
  const last = pts[pts.length - 1]

  return (
    <div className="relative h-36 pt-2">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1="0" y1={h * (1 - f)} x2={w} y2={h * (1 - f)} stroke={CHART_GRID} strokeWidth="1" />
        ))}
        <path
          d={`M ${pts[0].x},${pts[0].y} ${pts.slice(1).map((p) => `L ${p.x},${p.y}`).join(" ")} L ${w},${h} L 0,${h} Z`}
          fill={CHART_LIA} fillOpacity={0.1}
        />
        <polyline points={polyPts} fill="none" stroke={CHART_LIA} strokeWidth="2" strokeLinejoin="round" />
        {last && (
          <circle cx={last.x} cy={last.y} r="3" fill={CHART_LIA} />
        )}
      </svg>
      <div className="flex justify-between mt-1">
        {data.map((d) => (
          <span key={d.label} className="text-[9px] text-gray-400">{d.label}</span>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// FunnelTable — aggregate funnel with stage-to-stage conversion
// ---------------------------------------------------------------------------

function convBadge(pct: number | null) {
  if (pct === null) return null
  const color =
    pct >= 50 ? "text-emerald-700 bg-emerald-50 border-emerald-200" :
    pct >= 25 ? "text-amber-700 bg-amber-50 border-amber-200" :
                "text-rose-700 bg-rose-50 border-rose-200"
  return (
    <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${color} tabular-nums`}>
      ↓ {pct.toFixed(1)}%
    </span>
  )
}

function FunnelTable({
  stages, loading,
}: {
  stages: StageFunnelItem[]
  loading: boolean
}) {
  if (loading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
        ))}
      </div>
    )
  }

  if (stages.length === 0) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">
        Sem dados de funil no período selecionado.
      </p>
    )
  }

  const maxCount = stages[0]?.count ?? 1

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left text-xs font-medium text-gray-500 pb-2 pr-3 w-28">Estágio</th>
            <th className="text-right text-xs font-medium text-gray-500 pb-2 pr-3 w-20">Candidatos</th>
            <th className="text-left text-xs font-medium text-gray-500 pb-2 pr-4 min-w-[100px]">% do Total</th>
            <th className="text-center text-xs font-medium text-gray-500 pb-2 w-24">Conv. Stage</th>
          </tr>
        </thead>
        <tbody>
          {stages.map((s, idx) => {
            const isHired = s.stage === "contratado" || s.stage === "hired"
            const barPct = maxCount > 0 ? Math.round((s.count / maxCount) * 100) : 0

            return (
              <tr
                key={s.stage}
                className={`border-b border-gray-100 last:border-0 hover:bg-gray-50 transition-colors ${
                  isHired ? "bg-emerald-50/40" : ""
                }`}
              >
                <td className="py-2.5 pr-3">
                  <span className={`text-xs font-medium ${isHired ? "text-emerald-700" : "text-gray-700"}`}>
                    {s.label}
                  </span>
                </td>
                <td className="py-2.5 pr-3 text-right">
                  <span className={`text-sm font-semibold tabular-nums ${isHired ? "text-emerald-700" : "text-gray-900"}`}>
                    {s.count.toLocaleString("pt-BR")}
                  </span>
                </td>
                <td className="py-2.5 pr-4">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden min-w-[60px]">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isHired ? "bg-emerald-400" : "bg-blue-400"
                        }`}
                        style={{ width: `${barPct}%` }}
                      />
                    </div>
                    <span className="text-[10px] text-gray-500 tabular-nums w-8 text-right shrink-0">
                      {s.pct_of_total.toFixed(1)}%
                    </span>
                  </div>
                </td>
                <td className="py-2.5 text-center">
                  {idx === 0 ? (
                    <span className="text-[10px] text-gray-400">—</span>
                  ) : (
                    convBadge(s.pct_from_prev)
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// InsightsPanel — only renders when there are insights
// ---------------------------------------------------------------------------

function InsightsPanel({ insights }: { insights: DashboardInsight[] }) {
  if (insights.length === 0) return null

  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
      <h2 className="text-base font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <Lightbulb className="w-4 h-4 text-amber-400" />
        Insights
      </h2>
      <div className="space-y-2">
        {insights.map((ins, i) => {
          const isAlert = ins.type === "alert" || ins.severity === "warning"
          return (
            <div
              key={i}
              className={`flex items-start gap-2 text-xs p-2.5 rounded-md border ${
                isAlert
                  ? "bg-amber-50 border-amber-200 text-amber-800"
                  : "bg-blue-50 border-blue-200 text-blue-800"
              }`}
            >
              {isAlert
                ? <AlertTriangle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                : <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
              }
              <span>{ins.message}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// PremiumLock — overlay wrapper for Enterprise-gated sections
// ---------------------------------------------------------------------------

function PremiumLock({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative">
      <div className="blur-sm pointer-events-none select-none" aria-hidden="true">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-center bg-white/95 px-6 py-4 rounded-xl shadow-md border border-gray-200">
          <Lock className="w-5 h-5 text-violet-400 mx-auto mb-1.5" />
          <p className="text-sm font-semibold text-gray-900">Plano Enterprise</p>
          <p className="text-xs text-gray-500 mt-0.5 mb-3">Disponível com upgrade</p>
          <button className="text-xs bg-violet-600 text-white px-3 py-1.5 rounded-md hover:bg-violet-700 transition-colors">
            Upgrade →
          </button>
        </div>
      </div>
    </div>
  )
}

// PipelineVelocityPanel
// ---------------------------------------------------------------------------

function PipelineVelocityPanel({
  velocity, loading, isEnterprise,
}: {
  velocity: StageVelocityItem[]
  loading: boolean
  isEnterprise: boolean
}) {
  const content = (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Velocidade do Pipeline</h2>
          <p className="text-xs text-gray-400">Tempo médio em cada estágio</p>
        </div>
        <span className="text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded font-medium">Enterprise</span>
      </div>
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : velocity.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">Sem dados suficientes de transição de estágio.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-xs font-medium text-gray-500 pb-2 pr-4">Estágio</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-2 pr-4">Média (dias)</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-2">Amostras</th>
              </tr>
            </thead>
            <tbody>
              {velocity.map((v) => (
                <tr key={v.stage} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                  <td className="py-2.5 pr-4 text-xs font-medium text-gray-700">{v.label}</td>
                  <td className="py-2.5 pr-4 text-right">
                    <span className={`text-sm font-semibold tabular-nums ${v.avg_days <= 3 ? "text-emerald-600" : v.avg_days <= 7 ? "text-amber-600" : "text-rose-600"}`}>
                      {v.avg_days}d
                    </span>
                  </td>
                  <td className="py-2.5 text-right text-xs text-gray-400 tabular-nums">{v.sample_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
  return isEnterprise ? content : <PremiumLock>{content}</PremiumLock>
}

// SourceQualityPanel
// ---------------------------------------------------------------------------

function SourceQualityPanel({
  sources, loading, isEnterprise,
}: {
  sources: SourceQualityItem[]
  loading: boolean
  isEnterprise: boolean
}) {
  const maxTotal = Math.max(...sources.map((s) => s.total), 1)

  const content = (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Qualidade por Fonte</h2>
          <p className="text-xs text-gray-400">Taxa de contratação por canal</p>
        </div>
        <span className="text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded font-medium">Enterprise</span>
      </div>
      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-8 bg-gray-100 rounded animate-pulse" />
          ))}
        </div>
      ) : sources.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">Sem dados suficientes por fonte no período.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left text-xs font-medium text-gray-500 pb-2 pr-3 w-28">Fonte</th>
                <th className="text-left text-xs font-medium text-gray-500 pb-2 pr-4">Volume</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-2 pr-3">Contratados</th>
                <th className="text-right text-xs font-medium text-gray-500 pb-2">Conv.</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((s) => {
                const barPct = Math.round((s.total / maxTotal) * 100)
                return (
                  <tr key={s.source} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="py-2.5 pr-3 text-xs font-medium text-gray-700">{s.label}</td>
                    <td className="py-2.5 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-400 rounded-full" style={{ width: `${barPct}%` }} />
                        </div>
                        <span className="text-xs text-gray-600 tabular-nums">{s.total}</span>
                      </div>
                    </td>
                    <td className="py-2.5 pr-3 text-right text-xs text-gray-600 tabular-nums">{s.hired}</td>
                    <td className="py-2.5 text-right">
                      <span className={`text-xs font-medium tabular-nums ${s.conversion_rate >= 15 ? "text-emerald-600" : s.conversion_rate >= 5 ? "text-amber-600" : "text-gray-500"}`}>
                        {s.conversion_rate.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
  return isEnterprise ? content : <PremiumLock>{content}</PremiumLock>
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const PERIOD_OPTIONS: { value: Period; label: string }[] = [
  { value: "30d", label: "Últimos 30 dias" },
  { value: "90d", label: "Últimos 90 dias" },
  { value: "180d", label: "Últimos 6 meses" },
]

export function IndicadoresPage() {
  const [period, setPeriod] = useState<Period>("30d")

  const { data, isLoading, error } = useQuery<DashboardKPIs>({
    queryKey: ["analytics-dashboard", period],
    queryFn: async () => {
      const resp = await fetch(`/api/backend-proxy/job-vacancies/analytics/dashboard?period=${period}`)
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
      return resp.json()
    },
    staleTime: 60_000,
  })

  const barData = (data?.weekly_trend ?? []).map((t) => ({ label: t.week, value: t.hired }))
  const lineData = (data?.weekly_trend ?? []).map((t) => ({ label: t.week, value: t.opened }))
  const stageFunnel = data?.stage_funnel ?? []
  const insights = data?.insights ?? []

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Indicadores</h1>
        <p className="text-sm text-gray-500 mt-1">Análise do seu pipeline de recrutamento</p>
      </div>

      {/* Filters Row */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as Period)}
          className="text-sm border border-gray-300 rounded-md px-3 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-900"
          aria-label="Período"
        >
          {PERIOD_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        {data && !isLoading && (
          <span className="text-xs text-gray-400">
            {data.hired_in_period} contratação{data.hired_in_period !== 1 ? "s" : ""} no período
          </span>
        )}
        {error && (
          <span className="text-xs text-rose-600">Erro ao carregar dados — tente novamente</span>
        )}
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <KpiCard
          label="Candidatos Ativos"
          value={String(data?.active_candidates ?? 0)}
          icon={<Users className="w-4 h-4" />}
          loading={isLoading}
        />
        <KpiCard
          label="Taxa de Aceitação de Ofertas"
          value={data?.offer_acceptance_rate != null ? `${data.offer_acceptance_rate}%` : "—"}
          icon={<CheckCircle className="w-4 h-4" />}
          loading={isLoading}
        />
        <KpiCard
          label="Tempo Médio para Preencher"
          value={data?.avg_time_to_fill_days != null ? `${data.avg_time_to_fill_days}d` : "—"}
          icon={<Clock className="w-4 h-4" />}
          loading={isLoading}
        />
        <KpiCard
          label="Taxa de Conversão"
          value={`${data?.conversion_rate ?? 0}%`}
          icon={<BarChart3 className="w-4 h-4" />}
          loading={isLoading}
        />
        <KpiCard
          label="Vagas Abertas"
          value={String(data?.open_vacancies ?? 0)}
          icon={<Briefcase className="w-4 h-4" />}
          loading={isLoading}
        />
        <KpiCard
          label="SLA em Risco"
          value={String(data?.sla_at_risk ?? 0)}
          icon={<AlertTriangle className="w-4 h-4" />}
          loading={isLoading}
        />
      </div>

      {/* Charts — Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Contratações</h2>
              <p className="text-xs text-gray-400">por semana no período</p>
            </div>
            <BarChart3 className="w-4 h-4 text-gray-300" />
          </div>
          {isLoading
            ? <div className="h-36 bg-gray-50 rounded animate-pulse" />
            : barData.some((d) => d.value > 0)
              ? <BarChartSimple data={barData} />
              : <div className="h-36 flex items-center justify-center text-sm text-gray-400">Sem contratações no período</div>
          }
        </div>

        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Vagas Abertas</h2>
              <p className="text-xs text-gray-400">novas por semana</p>
            </div>
            <LineChart className="w-4 h-4 text-gray-300" />
          </div>
          {isLoading
            ? <div className="h-36 bg-gray-50 rounded animate-pulse" />
            : lineData.some((d) => d.value > 0)
              ? <LineChartSimple data={lineData} />
              : <div className="h-36 flex items-center justify-center text-sm text-gray-400">Sem vagas abertas no período</div>
          }
        </div>
      </div>

      {/* Funil Agregado */}
      <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Funil de Recrutamento</h2>
            <p className="text-xs text-gray-400">
              {isLoading ? "Calculando..." : `Agregado · ${PERIOD_OPTIONS.find((o) => o.value === period)?.label}`}
            </p>
          </div>
          <BarChart3 className="w-4 h-4 text-gray-300" />
        </div>
        <FunnelTable stages={stageFunnel} loading={isLoading} />
      </div>

      {/* Insights — only when data has them */}
      {!isLoading && insights.length > 0 && <InsightsPanel insights={insights} />}

      {/* Premium Analytics — Pipeline Velocity + Source Quality */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PipelineVelocityPanel
          velocity={data?.pipeline_velocity ?? []}
          loading={isLoading}
          isEnterprise={false}
        />
        <SourceQualityPanel
          sources={data?.source_quality ?? []}
          loading={isLoading}
          isEnterprise={false}
        />
      </div>
    </div>
  )
}
