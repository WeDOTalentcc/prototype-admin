"use client"

import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  TrendingUp, TrendingDown, Users, Briefcase, Clock,
  AlertTriangle, BarChart3, LineChart, Lock, CheckCircle,
} from "lucide-react"
import { CHART_LIA, CHART_GRID } from "@/lib/chart-colors"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Period = "30d" | "90d" | "180d"

interface WeeklyTrend {
  week: string
  hired: number
  opened: number
}

interface StageFunnelItem {
  stage: string
  label: string
  count: number
  pct_of_total: number
  pct_from_prev: number | null
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
  insights: { type: string; message: string; severity?: string; action?: string }[]
}

interface KpiCardProps {
  label: string
  value: string
  trend?: number
  trendLabel?: string
  icon: React.ReactNode
  loading?: boolean
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function KpiCard({ label, value, trend, trendLabel, icon, loading }: KpiCardProps) {
  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">{label}</span>
        <span className="text-gray-400">{icon}</span>
      </div>
      {loading ? (
        <div className="h-8 w-24 bg-gray-100 rounded animate-pulse" />
      ) : (
        <span className="text-3xl font-bold text-gray-900 font-['Inter'] tabular-nums">{value}</span>
      )}
      {trend !== undefined && (
        <div className="flex items-center gap-1">
          {trend >= 0 ? (
            <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
          ) : (
            <TrendingDown className="w-3.5 h-3.5 text-rose-500" />
          )}
          <span className={`text-xs ${trend >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
            {trend >= 0 ? "+" : ""}{trend}%
          </span>
          {trendLabel && <span className="text-xs text-gray-400">{trendLabel}</span>}
        </div>
      )}
    </div>
  )
}

function BarChartSimple({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  return (
    <div className="flex items-end gap-2 h-32 pt-2">
      {data.map((d) => (
        <div key={d.label} className="flex-1 flex flex-col items-center gap-1">
          <div
            className="w-full rounded-t-sm"
            style={{
              height: `${Math.round((d.value / max) * 100)}%`,
              backgroundColor: CHART_LIA,
              minHeight: d.value > 0 ? "4px" : "0",
            }}
          />
          <span className="text-[10px] text-gray-400 truncate w-full text-center">{d.label}</span>
        </div>
      ))}
    </div>
  )
}

function LineChartSimple({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  const w = 300
  const h = 100
  const pts = data.map((d, i) => {
    const x = (i / Math.max(data.length - 1, 1)) * w
    const y = h - (d.value / max) * (h - 8)
    return `${x},${y}`
  })
  return (
    <div className="relative h-32 pt-2">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
        {[0.25, 0.5, 0.75].map((f) => (
          <line key={f} x1="0" y1={h * (1 - f)} x2={w} y2={h * (1 - f)} stroke={CHART_GRID} strokeWidth="1" />
        ))}
        <path
          d={`M ${pts[0]} ${pts.slice(1).map((p) => `L ${p}`).join(" ")} L ${w},${h} L 0,${h} Z`}
          fill={CHART_LIA}
          fillOpacity={0.12}
        />
        <polyline points={pts.join(" ")} fill="none" stroke={CHART_LIA} strokeWidth="2" strokeLinejoin="round" />
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
// Premium locked section
// ---------------------------------------------------------------------------

const PREMIUM_CARDS = [
  "Benchmark Salarial",
  "Insights de Empregadores",
  "Distribuição de Educação",
  "Score de Efetividade",
]

function PremiumLockedSection() {
  return (
    <div className="bg-white rounded-md shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Análise Avançada</h2>
        <span className="text-xs bg-violet-100 text-violet-700 px-2 py-0.5 rounded font-medium">
          Enterprise
        </span>
      </div>
      <div className="relative">
        <div className="opacity-30 pointer-events-none grid grid-cols-2 gap-4" aria-hidden="true">
          {PREMIUM_CARDS.map((name) => (
            <div key={name} className="bg-gray-50 rounded-md border border-gray-200 p-4 h-28 flex items-center justify-center">
              <span className="text-xs text-gray-400">{name}</span>
            </div>
          ))}
        </div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center bg-white/95 p-6 rounded-xl shadow border border-gray-100">
            <Lock className="w-6 h-6 text-violet-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-gray-900 mb-1">
              Disponível no plano Enterprise
            </p>
            <p className="text-xs text-gray-500 mb-3">
              Acesse 14+ indicadores preditivos avançados
            </p>
            <button className="text-sm bg-violet-600 text-white px-4 py-2 rounded-md hover:bg-violet-700 transition-colors">
              Upgrade Plan →
            </button>
          </div>
        </div>
      </div>
    </div>
  )
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

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Indicadores</h1>
        <p className="text-sm text-gray-500 mt-1">
          Análise do seu pipeline de recrutamento
        </p>
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

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Contratações por Semana</h2>
            <BarChart3 className="w-4 h-4 text-gray-400" />
          </div>
          {isLoading ? (
            <div className="h-32 bg-gray-50 rounded animate-pulse" />
          ) : barData.length > 0 ? (
            <BarChartSimple data={barData} />
          ) : (
            <div className="h-32 flex items-center justify-center text-sm text-gray-400">Sem dados no período</div>
          )}
        </div>

        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Vagas Abertas por Semana</h2>
            <LineChart className="w-4 h-4 text-gray-400" />
          </div>
          {isLoading ? (
            <div className="h-32 bg-gray-50 rounded animate-pulse" />
          ) : lineData.length > 0 ? (
            <LineChartSimple data={lineData} />
          ) : (
            <div className="h-32 flex items-center justify-center text-sm text-gray-400">Sem dados no período</div>
          )}
        </div>
      </div>

      {/* Premium Locked Section */}
      <PremiumLockedSection />
    </div>
  )
}
