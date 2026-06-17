"use client"

import { useState } from "react"
import { TrendingUp, TrendingDown, Users, Briefcase, Clock, AlertTriangle, BarChart3, LineChart, Lock } from "lucide-react"
import {
  CHART_LIA,
  CHART_SUCCESS,
  CHART_WARNING,
  CHART_NEUTRAL,
  CHART_AXIS,
  CHART_GRID,
} from "@/lib/chart-colors"

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Period = "30d" | "90d" | "180d"

interface KpiCardProps {
  label: string
  value: string
  trend?: number /** positive = up, negative = down, undefined = no trend */
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

// Simple SVG bar chart (no chart.js dep — avoids bundle bloat for simple bars)
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

// Simple SVG line chart
function LineChartSimple({ data }: { data: { label: string; value: number }[] }) {
  const max = Math.max(...data.map((d) => d.value), 1)
  const w = 300
  const h = 100
  const pts = data.map((d, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - (d.value / max) * (h - 8)
    return `${x},${y}`
  })
  return (
    <div className="relative h-32 pt-2">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
        {/* grid lines */}
        {[0.25, 0.5, 0.75].map((f) => (
          <line
            key={f}
            x1="0" y1={h * (1 - f)} x2={w} y2={h * (1 - f)}
            stroke={CHART_GRID}
            strokeWidth="1"
          />
        ))}
        {/* area fill */}
        <path
          d={`M ${pts[0]} ${pts.slice(1).map((p) => `L ${p}`).join(" ")} L ${w},${h} L 0,${h} Z`}
          fill={CHART_LIA}
          fillOpacity={0.12}
        />
        {/* line */}
        <polyline
          points={pts.join(" ")}
          fill="none"
          stroke={CHART_LIA}
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </svg>
      {/* x-axis labels */}
      <div className="flex justify-between mt-1">
        {data.map((d) => (
          <span key={d.label} className="text-[9px] text-gray-400">{d.label}</span>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Static mock data helpers
// ---------------------------------------------------------------------------

function getMockKpis(period: Period) {
  // Values vary slightly per period for visual interest
  const scale = period === "30d" ? 1 : period === "90d" ? 2.8 : 5.4
  return {
    activeCandidates: Math.round(47 * scale),
    hiringProbability: 68,
    avgTimeToFill: 24,
    conversionRate: 4.2,
    openVacancies: 12,
    slaAtRisk: 3,
  }
}

function getBarData(period: Period) {
  const labels = period === "30d"
    ? ["S1", "S2", "S3", "S4"]
    : period === "90d"
    ? ["Jan", "Fev", "Mar"]
    : ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
  return labels.map((l, i) => ({ label: l, value: 10 + i * 7 + Math.round(Math.random() * 8) }))
}

function getLineData(period: Period) {
  const labels = period === "30d"
    ? ["Sem 1", "Sem 2", "Sem 3", "Sem 4"]
    : period === "90d"
    ? ["Jan", "Fev", "Mar"]
    : ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
  const base = [12, 19, 14, 22, 18, 27]
  return labels.map((l, i) => ({ label: l, value: base[i % base.length] }))
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
        <div
          className="opacity-30 pointer-events-none grid grid-cols-2 gap-4"
          aria-hidden="true"
        >
          {PREMIUM_CARDS.map((name) => (
            <div
              key={name}
              className="bg-gray-50 rounded-md border border-gray-200 p-4 h-28 flex items-center justify-center"
            >
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

export function IndicadoresPage() {
  const [period, setPeriod] = useState<Period>("30d")

  const kpis = getMockKpis(period)
  const barData = getBarData(period)
  const lineData = getLineData(period)

  const PERIOD_OPTIONS: { value: Period; label: string }[] = [
    { value: "30d", label: "Últimos 30 dias" },
    { value: "90d", label: "Últimos 90 dias" },
    { value: "180d", label: "Últimos 6 meses" },
  ]

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Indicadores</h1>
        <p className="text-sm text-gray-500 mt-1">
          Análise preditiva do seu pipeline de recrutamento
        </p>
      </div>

      {/* Filters Row — Apollo pattern */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as Period)}
          className="text-sm border border-gray-300 rounded-md px-3 py-2 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-900"
          aria-label="Período"
        >
          {PERIOD_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <KpiCard
          label="Candidatos Ativos"
          value={String(kpis.activeCandidates)}
          trend={12}
          trendLabel="vs. período anterior"
          icon={<Users className="w-4 h-4" />}
        />
        <KpiCard
          label="Prob. Média de Contratação"
          value={`${kpis.hiringProbability}%`}
          trend={3}
          trendLabel="vs. período anterior"
          icon={<TrendingUp className="w-4 h-4" />}
        />
        <KpiCard
          label="Tempo Médio para Preencher"
          value={`${kpis.avgTimeToFill}d`}
          trend={-5}
          trendLabel="vs. período anterior"
          icon={<Clock className="w-4 h-4" />}
        />
        <KpiCard
          label="Taxa de Conversão"
          value={`${kpis.conversionRate}%`}
          trend={8}
          trendLabel="vs. período anterior"
          icon={<BarChart3 className="w-4 h-4" />}
        />
        <KpiCard
          label="Vagas Abertas"
          value={String(kpis.openVacancies)}
          icon={<Briefcase className="w-4 h-4" />}
        />
        <KpiCard
          label="SLA em Risco"
          value={String(kpis.slaAtRisk)}
          trend={kpis.slaAtRisk > 0 ? -10 : 0}
          trendLabel="vagas"
          icon={<AlertTriangle className="w-4 h-4" />}
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pipeline Forecast */}
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Previsão do Pipeline</h2>
            <BarChart3 className="w-4 h-4 text-gray-400" />
          </div>
          <BarChartSimple data={barData} />
        </div>

        {/* Applications Trend */}
        <div className="bg-white rounded-md shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-gray-900">Trend de Aplicações</h2>
            <LineChart className="w-4 h-4 text-gray-400" />
          </div>
          <LineChartSimple data={lineData} />
        </div>
      </div>

      {/* Premium Locked Section */}
      <PremiumLockedSection />
    </div>
  )
}
