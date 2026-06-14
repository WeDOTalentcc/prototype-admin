// Onda 4 F3 (2026-05-28) — KPIs dashboard client component.
//
// Estrutura:
//   - Header: nome do agente + badge "aprendendo" + period selector (7d/30d/90d/Todos)
//   - Cards grandes: candidates_processed, avg latency
//   - Cards secundários: aprovados, rejeitados, custo total
//   - Heatmap horizontal: BarChart Recharts (24h)
//   - Tool breakdown: lista ordenada com barra de progresso
//   - Link "Ver consumo financeiro deste agente"
//
// Decisões de produto:
//   - Cards "aprovados/rejeitados" escondem se valor=0 (backend gap conhecido)
//   - is_learning badge: tooltip "menos de 5 execuções"
//
// A11y:
//   - Recharts aria-label nos containers
//   - badge cyan tem screen reader text
//
// Design tokens: zero hex hardcoded; cyan = #60BED1 (token canonical wedo-cyan).
"use client"

import dynamic from "next/dynamic"
import { useRouter } from "next/navigation"
import { useState } from "react"
import { useTranslations } from "next-intl"
import { ArrowRight, Clock, DollarSign, RotateCw, Users } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"
import { useAgentKpis } from "@/hooks/agents/use-agent-kpis"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import type { AgentKpiPeriod, AgentKpiResponse } from "@/types/agents/kpi"

// C5.4 (2026-05-29): lazy-load the Recharts heatmap so the heavy charting lib is
// code-split out of the main KPIs bundle. ssr:false because Recharts measures the
// DOM (ResponsiveContainer); skeleton fallback keeps layout stable while it loads.
const HeatmapCard = dynamic(
  () => import("./HeatmapCard").then((m) => m.HeatmapCard),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[248px] w-full rounded-lg" />,
  },
)

const PERIODS: AgentKpiPeriod[] = ["7d", "30d", "90d", "all"]
// Onda 5.4/5.9 — sem fallback hex (sensor check_cyan_token_for_agents BLOCKING).
// Token canonical: tailwind.config.ts:59 expoe wedo-cyan; design-tokens.css
// define --wedo-cyan globalmente. Fallback nao precisa porque ambos sempre
// existem (sao injetados em runtime independentemente de cliente customizado).
const CYAN_TOKEN = "var(--wedo-cyan)"

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`
  return n.toString()
}

function formatSeconds(s: number): string {
  if (s < 1) return `${Math.round(s * 1000)}ms`
  if (s < 60) return `${s.toFixed(1)}s`
  return `${(s / 60).toFixed(1)}min`
}

function formatUsd(usd: number): string {
  return `$${usd.toFixed(2)}`
}

interface LearningBadgeProps {
  label: string
  srText: string
}

function LearningBadge({ label, srText }: LearningBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs",
        "border-wedo-cyan/40 bg-wedo-cyan/15 text-wedo-cyan-text",
      )}
      title={srText}
      role="status"
    >
      <span aria-hidden="true">🩵</span>
      <span>{label}</span>
      <span className="sr-only">— {srText}</span>
    </span>
  )
}

interface KpiPageProps {
  agentId: string
}

export default function AgentKpisClient({ agentId }: KpiPageProps) {
  const t = useTranslations("agents.studio.kpis")
  const router = useRouter()
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "LIA"

  const [period, setPeriod] = useState<AgentKpiPeriod>("30d")
  const { data, isLoading, error, refetch } = useAgentKpis(agentId, period)

  if (isLoading) {
    return (
      <div className="space-y-6 p-6" data-testid="agent-kpis-loading">
        <Skeleton className="h-10 w-1/2" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64" />
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-6">
        <Card>
          <CardContent
            className="flex flex-col items-center gap-3 py-12 text-center"
            role="alert"
            data-testid="agent-kpis-error"
          >
            <p className="text-sm font-medium text-lia-text-primary">
              {t("error.title")}
            </p>
            <p className="max-w-md text-xs text-lia-text-secondary">
              {t("error.description")}
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="gap-1.5"
              data-testid="agent-kpis-retry"
            >
              <RotateCw className="h-3.5 w-3.5" />
              {t("error.retry")}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Empty state — agent sem execuções
  if (data.bucket.total_executions === 0) {
    return (
      <div className="space-y-6 p-6" data-testid="agent-kpis-empty">
        <header className="flex items-center gap-3">
          <h1 className="font-sans text-2xl font-semibold text-lia-text-primary">
            {data.agent_name}
          </h1>
          {data.is_learning && (
            <LearningBadge
              label={t("learning.badge")}
              srText={t("learning.tooltip")}
            />
          )}
        </header>
        <Card>
          <CardContent className="py-12 text-center">
            <h2 className="font-sans text-base font-semibold text-lia-text-primary">
              {t("empty.title")}
            </h2>
            <p className="mt-2 text-sm text-lia-text-secondary">
              {t("empty.description")}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { bucket, hour_heatmap, tool_breakdown } = data
  // Skip approval cards if backend returned 0 (gap conhecido — decisão produto = hide)
  const showCandidateBreakdown =
    bucket.candidates_approved > 0 || bucket.candidates_rejected > 0

  function handleConsumptionLink() {
    // Navega para hub Consumo > Agentes com filtro pré-aplicado.
    // F4 modal vai abrir quando segmento for clicado lá.
    router.push(
      `/configuracoes?section=consumo&filter=${encodeURIComponent(agentId)}`,
    )
  }

  return (
    <div className="space-y-6 p-6" data-testid="agent-kpis-content">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <h1 className="font-sans text-2xl font-semibold text-lia-text-primary">
            {data.agent_name}
          </h1>
          {data.is_learning && (
            <LearningBadge
              label={t("learning.badge")}
              srText={t("learning.tooltip")}
            />
          )}
        </div>
        <PeriodSelector
          value={period}
          onChange={setPeriod}
          label7d={t("period.7d")}
          label30d={t("period.30d")}
          label90d={t("period.90d")}
          labelAll={t("period.all")}
        />
      </header>

      {/* Primary KPIs */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <KpiCard
          icon={<Users className="h-4 w-4 text-lia-text-tertiary" />}
          label={t("cards.candidatesProcessed")}
          value={formatNumber(bucket.candidates_processed)}
          subtitle={t("cards.executions", { count: bucket.total_executions })}
        />
        <KpiCard
          icon={<Clock className="h-4 w-4 text-lia-text-tertiary" />}
          label={t("cards.avgTime")}
          value={formatSeconds(bucket.avg_execution_seconds)}
          subtitle={t("cards.p95", {
            value: formatSeconds(bucket.p95_execution_seconds),
          })}
        />
      </div>

      {/* Secondary KPIs */}
      <div
        className={cn(
          "grid grid-cols-1 gap-4",
          showCandidateBreakdown ? "md:grid-cols-3" : "md:grid-cols-1",
        )}
      >
        {showCandidateBreakdown && (
          <>
            <KpiCard
              label={t("cards.approved")}
              value={formatNumber(bucket.candidates_approved)}
              subtitle={t("cards.approvedPct", {
                pct: Math.round(
                  (bucket.candidates_approved /
                    Math.max(1, bucket.candidates_processed)) *
                    100,
                ),
              })}
            />
            <KpiCard
              label={t("cards.rejected")}
              value={formatNumber(bucket.candidates_rejected)}
              subtitle={t("cards.rejectedPct", {
                pct: Math.round(
                  (bucket.candidates_rejected /
                    Math.max(1, bucket.candidates_processed)) *
                    100,
                ),
              })}
            />
          </>
        )}
        <KpiCard
          icon={<DollarSign className="h-4 w-4 text-lia-text-tertiary" />}
          label={t("cards.totalCost")}
          value={formatUsd(bucket.total_cost_usd)}
          subtitle={t("cards.tokens", {
            value: formatNumber(
              bucket.total_tokens_input + bucket.total_tokens_output,
            ),
          })}
        />
      </div>

      {/* Heatmap */}
      <HeatmapCard
        title={t("heatmap.title")}
        ariaLabel={t("heatmap.ariaLabel")}
        data={hour_heatmap}
      />

      {/* Tool breakdown */}
      {tool_breakdown.length > 0 && (
        <ToolBreakdownCard
          title={t("tools.title")}
          successRateLabel={(rate: number) =>
            t("tools.successRate", { rate: Math.round(rate * 100) })
          }
          data={tool_breakdown}
        />
      )}

      {/* Footer link */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={handleConsumptionLink}
          className="inline-flex items-center gap-1 text-xs font-medium text-lia-text-secondary hover:text-wedo-cyan-dark transition-colors"
        >
          {t("viewConsumption")}
          <ArrowRight className="h-3 w-3" />
        </button>
      </div>

      {/* Hidden description for screen readers — persona context */}
      <span className="sr-only" aria-live="polite">
        {t("a11y.summary", {
          personaName,
          agentName: data.agent_name,
          period: t(`period.${period === "all" ? "all" : period}` as const),
        })}
      </span>
    </div>
  )
}

interface PeriodSelectorProps {
  value: AgentKpiPeriod
  onChange: (p: AgentKpiPeriod) => void
  label7d: string
  label30d: string
  label90d: string
  labelAll: string
}

function PeriodSelector({
  value,
  onChange,
  label7d,
  label30d,
  label90d,
  labelAll,
}: PeriodSelectorProps) {
  const labels: Record<AgentKpiPeriod, string> = {
    "7d": label7d,
    "30d": label30d,
    "90d": label90d,
    all: labelAll,
  }
  return (
    <div
      role="tablist"
      aria-label="Period"
      className="inline-flex rounded-md border border-lia-border-subtle bg-lia-bg-primary"
    >
      {PERIODS.map((p) => (
        <button
          key={p}
          type="button"
          role="tab"
          aria-selected={value === p}
          onClick={() => onChange(p)}
          className={cn(
            "px-3 py-1.5 text-xs font-medium transition-colors",
            "first:rounded-l-md last:rounded-r-md",
            value === p
              ? "bg-lia-text-primary text-lia-text-inverse"
              : "text-lia-text-secondary hover:bg-lia-bg-secondary",
          )}
        >
          {labels[p]}
        </button>
      ))}
    </div>
  )
}

interface KpiCardProps {
  icon?: React.ReactNode
  label: string
  value: string
  subtitle?: string
}

function KpiCard({ icon, label, value, subtitle }: KpiCardProps) {
  return (
    <Card className="border border-lia-border-subtle shadow-none">
      <CardHeader className="pb-2 pt-4">
        <CardTitle className="flex items-center gap-1.5 text-xs font-medium text-lia-text-tertiary">
          {icon}
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <div className="font-sans text-2xl font-semibold tabular-nums text-lia-text-primary">
          {value}
        </div>
        {subtitle && (
          <div className="mt-1 text-xs text-lia-text-tertiary">{subtitle}</div>
        )}
      </CardContent>
    </Card>
  )
}

// C5.4 (2026-05-29): HeatmapCard (Recharts) moved to ./HeatmapCard.tsx and
// lazy-loaded via next/dynamic at the top of this file.

interface ToolBreakdownCardProps {
  title: string
  successRateLabel: (rate: number) => string
  data: AgentKpiResponse["tool_breakdown"]
}

function ToolBreakdownCard({
  title,
  successRateLabel,
  data,
}: ToolBreakdownCardProps) {
  const sorted = [...data].sort((a, b) => b.count - a.count)
  const max = Math.max(...sorted.map((d) => d.count), 1)
  return (
    <Card className="border border-lia-border-subtle shadow-none">
      <CardHeader className="pb-2 pt-4">
        <CardTitle className="text-xs font-medium text-lia-text-tertiary">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <ul className="space-y-2">
          {sorted.map((tool) => {
            const pct = (tool.count / max) * 100
            return (
              <li key={tool.tool_name} className="flex items-center gap-3">
                <span className="w-40 truncate text-xs text-lia-text-secondary">
                  {tool.tool_name}
                </span>
                <span className="w-12 text-right text-xs tabular-nums text-lia-text-primary">
                  {tool.count}
                </span>
                <div className="relative h-2 flex-1 overflow-hidden rounded bg-lia-bg-secondary">
                  <div
                    className="absolute inset-y-0 left-0 rounded"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: CYAN_TOKEN,
                    }}
                  />
                </div>
                <span className="w-20 text-right text-xs text-lia-text-tertiary">
                  {successRateLabel(tool.success_rate)}
                </span>
              </li>
            )
          })}
        </ul>
      </CardContent>
    </Card>
  )
}
