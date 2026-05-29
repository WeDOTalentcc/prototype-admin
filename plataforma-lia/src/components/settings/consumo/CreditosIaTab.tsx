'use client'

import useSWR from 'swr'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Chip } from '@/components/ui/chip'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  LineChart,
  Line,
  Legend,
} from 'recharts'
import type { Payload } from 'recharts/types/component/DefaultTooltipContent'
import { AlertTriangle, Zap, TrendingUp, DollarSign, Activity } from 'lucide-react'
import { useMemo, type ComponentProps } from 'react'
import { BudgetAlertsList } from './BudgetAlertsList'

const jsonFetcher = (url: string) => fetch(url).then(r => r.json())

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return tokens.toString()
}

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

// Mapa canônico: agent_type (backend) → { label PT-BR, cor para gráficos }
// Atualizado 2026-05-27 para refletir tipos reais registrados em ai_consumption.
export const AGENT_TYPE_MAP: Record<string, { label: string; color: string }> = {
  // --- Triagem e CV ---
  cv_screening:           { label: "Triagem de CV",          color: "#6366f1" }, // indigo
  cv_screening_pipeline:  { label: "Pipeline de Triagem",    color: "#8b5cf6" }, // violet
  scoring:                { label: "Pontuação",              color: "#a855f7" }, // purple

  // --- Captação e Busca ---
  sourcing:               { label: "Captação Ativa",         color: "#0ea5e9" }, // sky
  sourcing_agent:         { label: "Captação Ativa",         color: "#0ea5e9" }, // back-compat alias
  search:                 { label: "Busca",                  color: "#38bdf8" }, // sky lighter
  matching:               { label: "Matching",               color: "#7dd3fc" }, // sky lightest

  // --- Entrevista e Voz ---
  voice_screening:        { label: "Triagem por Voz",        color: "#14b8a6" }, // teal
  interview:              { label: "Entrevista",             color: "#2dd4bf" }, // teal lighter

  // --- Comunicação ---
  communication:          { label: "Comunicação",            color: "#f59e0b" }, // amber
  whatsapp:               { label: "WhatsApp Bot",           color: "#22c55e" }, // green
  onboarding:             { label: "Onboarding",             color: "#84cc16" }, // lime

  // --- IA Interna ---
  orchestrator:           { label: "Orquestrador IA",        color: "#ef4444" }, // red
  wizard:                 { label: "Wizard de Vaga",         color: "#f97316" }, // orange
  wsi_question_generator: { label: "Perguntas WSI",          color: "#fb923c" }, // orange lighter
  recruiter_assistant:    { label: "Assistente Recrutador",  color: "#ec4899" }, // pink

  // --- Agentes Studio ---
  digital_twin:           { label: "Gêmeo Digital",         color: "#06b6d4" }, // cyan (cor IA WeDO)
  custom_agent:           { label: "Agente Personalizado",  color: "#64748b" }, // slate
  analysis:               { label: "Análise",               color: "#94a3b8" }, // slate lighter

  // --- Legados (compatibilidade com registros históricos) ---
  cv_parsing:             { label: "Leitura de CV",          color: "#a3a3a3" },
  screening:              { label: "Triagem",                color: "#737373" },
}

// Cor de fallback para tipos não mapeados
const FALLBACK_COLOR = "#94a3b8"
const FALLBACK_LABEL = (agentType: string) => agentType.replace(/_/g, " ")

// Mantém AGENT_COLORS exportado para compatibilidade com código que importa diretamente
export const AGENT_COLORS: Record<string, string> = Object.fromEntries(
  Object.entries(AGENT_TYPE_MAP).map(([k, v]) => [k, v.color])
)

export function getAgentColor(agentType: string): string {
  return AGENT_TYPE_MAP[agentType.toLowerCase()]?.color ?? FALLBACK_COLOR
}

export function getAgentLabel(agentType: string): string {
  return AGENT_TYPE_MAP[agentType.toLowerCase()]?.label ?? FALLBACK_LABEL(agentType)
}

export interface AgentChartEntry {
  name: string
  agentType: string
  tokens: number
  cost: number
  operations: number
  percentage: number
}

export interface AgentTrendDayEntry {
  date: string
  [agentKey: string]: string | number
}

interface AiCreditsBalance {
  id: string
  company_id: string
  monthly_limit: number
  current_usage: number
  usage_percentage: number
  remaining_tokens: number
  period_start: string
  period_end: string
  overage_allowed: boolean
  updated_at: string
}

interface UsageSummary {
  total_tokens: number
  total_cost_cents: number
  total_operations: number
  period: string
  projected_monthly_tokens: number
  projected_monthly_cost_cents: number
  avg_daily_tokens_7d: number
  daily_limit: number
  daily_usage_today: number
  daily_usage_percentage: number
}

interface AgentUsage {
  agent_type: string
  total_tokens: number
  total_cost_cents: number
  total_operations?: number
  operation_count?: number
  percentage_of_total?: number
}

interface DailyUsage {
  date: string
  total_tokens: number
  total_cost_cents: number
  total_operations: number
}

interface AgentDailyTrend {
  date: string
  agent_type: string
  total_tokens: number
}

function parseData<T>(raw: { data?: T; usage_by_day?: T; usage_by_agent?: T } | T[] | undefined, fallback: T[]): T[] {
  if (!raw) return fallback
  if (Array.isArray(raw)) return raw
  const r = raw as Record<string, unknown>
  return (r.data ?? r.usage_by_day ?? r.usage_by_agent ?? fallback) as T[]
}

function MonthlyUsageAlert({ percentage }: { percentage: number }) {
  if (percentage >= 100) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-status-error/30 bg-status-error/10 px-4 py-3 text-sm text-status-error">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Limite atingido:</strong> O consumo de IA atingiu 100% do limite mensal.
        </span>
      </div>
    )
  }
  if (percentage >= 80) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-status-warning/30 bg-status-warning/10 px-4 py-3 text-sm text-status-warning">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Atenção:</strong> {percentage.toFixed(0)}% do limite mensal de IA utilizado.
        </span>
      </div>
    )
  }
  return null
}

function agentBreakdownTooltipFormatter(
  value: unknown,
  _name: unknown,
  entry: Payload<number, string>,
): [string, string] {
  const v = typeof value === 'number' ? value : Number(value ?? 0)
  const payload = entry.payload as AgentChartEntry | undefined
  const pct = payload?.percentage ?? 0
  return [`${formatTokens(v)} tokens (${pct}%)`, 'Consumo']
}

/**
 * Onda 5.2 — drilldown state lives in ConsumoHub. Tab receives opener.
 */
export interface CreditosIaTabProps {
  onOpenDrilldown?: (state: {
    agentType: string | null
    studioAgentId: string | null
  }) => void
}

export function CreditosIaTab({ onOpenDrilldown }: CreditosIaTabProps = {}) {
  const { data: balance, isLoading: balanceLoading, error: balanceError } =
    useSWR<AiCreditsBalance>('/api/backend-proxy/ai-credits?endpoint=balance', jsonFetcher)

  const { data: summaryRaw, isLoading: summaryLoading } =
    useSWR<UsageSummary>('/api/backend-proxy/ai-credits?endpoint=summary', jsonFetcher)

  const summary = summaryRaw ?? null

  const { data: dayRaw, isLoading: dayLoading } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=by-day&days=30', jsonFetcher)

  const { data: agentRaw } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=by-agent', jsonFetcher)

  const { data: trendRaw } =
    useSWR('/api/backend-proxy/ai-credits?endpoint=agent-trend&days=30', jsonFetcher)

  const byDay: DailyUsage[] = parseData(dayRaw, [])
  const byAgent: AgentUsage[] = parseData(agentRaw, [])
  const agentTrend: AgentDailyTrend[] = parseData(trendRaw, [])

  const usagePct = balance?.usage_percentage ?? 0
  const dailyPct = summary?.daily_usage_percentage ?? 0
  const alertVariant: 'danger' | 'neutral' = usagePct >= 100 ? 'danger' : 'neutral'
  const alertMuted = usagePct < 80

  const chartData = byDay.map((d) => ({
    date: d.date.slice(5),
    tokens: Math.round(d.total_tokens / 1000),
    custo: +(d.total_cost_cents / 100).toFixed(2),
  }))

  const totalAgentTokens = byAgent.reduce((sum, a) => sum + a.total_tokens, 0)
  const agentChartData: AgentChartEntry[] = [...byAgent]
    .sort((a, b) => b.total_tokens - a.total_tokens)
    .map((agent) => ({
      name: getAgentLabel(agent.agent_type),
      agentType: agent.agent_type,
      tokens: agent.total_tokens,
      cost: agent.total_cost_cents,
      operations: agent.total_operations ?? agent.operation_count ?? 0,
      percentage:
        totalAgentTokens > 0
          ? +((agent.total_tokens / totalAgentTokens) * 100).toFixed(1)
          : 0,
    }))

  const { trendChartData, trendAgentTypes } = useMemo(() => {
    if (agentTrend.length === 0)
      return { trendChartData: [] as AgentTrendDayEntry[], trendAgentTypes: [] as string[] }

    const agentTypes = [...new Set(agentTrend.map((t) => t.agent_type))]
    const byDate = new Map<string, { isoDate: string; entry: AgentTrendDayEntry }>()

    for (const item of agentTrend) {
      const displayDate = item.date.slice(5)
      if (!byDate.has(item.date)) {
        byDate.set(item.date, { isoDate: item.date, entry: { date: displayDate } })
      }
      const row = byDate.get(item.date)!
      row.entry[item.agent_type] = Math.round(item.total_tokens / 1000)
    }

    const sorted = [...byDate.values()]
      .sort((a, b) => a.isoDate.localeCompare(b.isoDate))
      .map((v) => v.entry)

    return { trendChartData: sorted, trendAgentTypes: agentTypes }
  }, [agentTrend])

  if (balanceLoading || summaryLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-lia-text-tertiary">
        Carregando dados de consumo de IA...
      </div>
    )
  }

  if (balanceError) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-status-error">
        Erro ao carregar dados. Tente novamente.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {dailyPct >= 80 && (
            <Chip
              variant={dailyPct >= 95 ? 'danger' : 'neutral'}
              muted={dailyPct < 95}
              className="text-xs"
            >
              Diário: {dailyPct.toFixed(0)}%
            </Chip>
          )}
          {balance && (
            <Chip variant={alertVariant} muted={alertMuted} className="text-xs">
              {usagePct.toFixed(0)}% utilizado
            </Chip>
          )}
        </div>
      </div>

      {balance && <MonthlyUsageAlert percentage={usagePct} />}

      {/* Onda 4 F5 + Onda 5.2 — alertas de orçamento (global + per-agent).
          onViewExecutions: passa o studio_agent_id ao opener canonical do Hub. */}
      <BudgetAlertsList
        onViewExecutions={(studioAgentId) =>
          onOpenDrilldown?.({ agentType: null, studioAgentId })
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-lia-text-tertiary">
              <Zap className="h-3.5 w-3.5" />
              Tokens utilizados
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-lia-text-primary">
              {balance ? formatTokens(balance.current_usage) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-lia-text-disabled">
              de {balance ? formatTokens(balance.monthly_limit) : '—'} no mês
            </p>
          </CardContent>
        </Card>

        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-lia-text-tertiary">
              <TrendingUp className="h-3.5 w-3.5" />
              Projeção mensal
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-lia-text-primary">
              {summary ? formatTokens(summary.projected_monthly_tokens) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-lia-text-disabled">
              {summary ? formatCost(summary.projected_monthly_cost_cents) : '—'} estimado
            </p>
          </CardContent>
        </Card>

        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-lia-text-tertiary">
              <DollarSign className="h-3.5 w-3.5" />
              Custo estimado
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-lia-text-primary">
              {summary ? formatCost(summary.total_cost_cents) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-lia-text-disabled">no período atual</p>
          </CardContent>
        </Card>

        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-1 pt-4">
            <CardTitle className="flex items-center gap-2 text-xs font-medium text-lia-text-tertiary">
              <Activity className="h-3.5 w-3.5" />
              Uso diário
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <p className="text-xl font-semibold text-lia-text-primary">
              {summary ? formatTokens(summary.daily_usage_today) : '—'}
            </p>
            <p className="mt-0.5 text-xs text-lia-text-disabled">
              de {summary ? formatTokens(summary.daily_limit) : '—'} diários
            </p>
          </CardContent>
        </Card>
      </div>

      {balance && (
        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-lia-text-tertiary">
              Uso do limite mensal — {usagePct.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div className="h-2 w-full overflow-hidden rounded-full bg-lia-bg-tertiary">
              <div
                className={`h-full rounded-full transition-[width] ${
                  usagePct >= 100
                    ? 'bg-status-error'
                    : usagePct >= 80
                    ? 'bg-status-warning'
                    : 'bg-lia-btn-primary-bg'
                }`}
                style={{ width: `${Math.min(usagePct, 100)}%` }}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-xs text-lia-text-disabled">
              <span>0</span>
              <span>{formatTokens(balance.monthly_limit)}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border border-lia-border-subtle shadow-none">
        <CardHeader className="pb-2 pt-4">
          <CardTitle className="text-xs font-medium text-lia-text-tertiary">
            Consumo diário — últimos 30 dias (tokens em K)
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          {dayLoading ? (
            <div className="flex h-48 items-center justify-center text-xs text-lia-text-disabled">
              Carregando histórico...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-xs text-lia-text-disabled">
              Sem dados de consumo no período
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--lia-border-subtle)" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                  unit="K"
                />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid var(--lia-border-subtle)' }}
                  formatter={(value, name) => {
                    const v = Number(value ?? 0)
                    const n = String(name)
                    return [
                      n === 'tokens' ? `${v}K tokens` : `$${v}`,
                      n === 'tokens' ? 'Tokens' : 'Custo',
                    ] as [string, string]
                  }}
                />
                <Bar dataKey="tokens" fill="var(--lia-btn-primary-bg)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {trendChartData.length > 0 && (
        <Card className="border border-lia-border-subtle shadow-none">
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-lia-text-tertiary">
              Tendência por agente — últimos 30 dias (tokens em K)
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendChartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--lia-border-subtle)" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                  unit="K"
                />
                <Tooltip
                  contentStyle={{ fontSize: 11, borderRadius: 6, border: '1px solid var(--lia-border-subtle)' }}
                  formatter={(value, name) => {
                    const v = Number(value ?? 0)
                    return [`${v}K tokens`, getAgentLabel(String(name))] as [string, string]
                  }}
                />
                <Legend
                  formatter={(value: string) => getAgentLabel(value)}
                  wrapperStyle={{ fontSize: 11 }}
                />
                {trendAgentTypes.map((agentType) => (
                  <Line
                    key={agentType}
                    type="monotone"
                    dataKey={agentType}
                    stroke={getAgentColor(agentType)}
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
