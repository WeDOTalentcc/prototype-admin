'use client'

import { useAiCredits, useAiConsumptionHistory } from '@/hooks/ai/use-ai-credits'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Chip } from "@/components/ui/chip"
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
import { useMemo } from 'react'

function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`
  return tokens.toString()
}

function formatCost(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`
}

const AGENT_COLORS: Record<string, string> = {
  screening: '#6366f1',
  scoring: '#8b5cf6',
  interview: '#a78bfa',
  cv_parsing: '#06b6d4',
  search: '#14b8a6',
  matching: '#10b981',
  communication: '#f59e0b',
  analysis: '#ef4444',
}

function getAgentColor(agentType: string): string {
  return AGENT_COLORS[agentType.toLowerCase()] ?? '#94a3b8'
}

function getAgentLabel(agentType: string): string {
  const labels: Record<string, string> = {
    screening: 'Screening',
    scoring: 'Scoring',
    interview: 'Entrevista',
    cv_parsing: 'Parse de CV',
    search: 'Busca',
    matching: 'Matching',
    communication: 'Comunicação',
    analysis: 'Análise',
  }
  return labels[agentType.toLowerCase()] ?? agentType.replace(/_/g, ' ')
}

interface AgentChartEntry {
  name: string
  agentType: string
  tokens: number
  cost: number
  operations: number
  percentage: number
}

interface AgentTrendDayEntry {
  date: string
  [agentKey: string]: string | number
}

function MonthlyUsageAlert({ percentage }: { percentage: number }) {
  if (percentage >= 100) {
    return (
      <div
        data-testid="ai-credits-monthly-alert-critical"
        className="flex items-center gap-2 rounded-lg border border-status-error/30 bg-status-error/10 px-4 py-3 text-sm text-status-error"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Limite atingido:</strong> O consumo de IA atingiu 100% do limite mensal. Contate o suporte ou atualize seu plano.
        </span>
      </div>
    )
  }
  if (percentage >= 80) {
    return (
      <div
        data-testid="ai-credits-monthly-alert-warning"
        className="flex items-center gap-2 rounded-lg border border-status-warning/30 bg-status-warning/10 px-4 py-3 text-sm text-status-warning"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Atenção:</strong> {percentage.toFixed(0)}% do limite mensal de IA utilizado. Monitore o consumo para evitar interrupções.
        </span>
      </div>
    )
  }
  return null
}

function DailyUsageAlert({ percentage }: { percentage: number }) {
  if (percentage >= 95) {
    return (
      <div
        data-testid="ai-credits-daily-alert-critical"
        className="flex items-center gap-2 rounded-lg border border-status-error/30 bg-status-error/10 px-4 py-3 text-sm text-status-error"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Limite diário crítico:</strong> {percentage.toFixed(0)}% do limite diário de tokens atingido. Operações de IA podem ser bloqueadas.
        </span>
        <Chip density="relaxed" variant="danger" className="ml-auto shrink-0">
          {percentage.toFixed(0)}%
        </Chip>
      </div>
    )
  }
  if (percentage >= 80) {
    return (
      <div
        data-testid="ai-credits-daily-alert-warning"
        className="flex items-center gap-2 rounded-lg border border-status-warning/30 bg-status-warning/10 px-4 py-3 text-sm text-status-warning"
      >
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          <strong>Alerta diário:</strong> {percentage.toFixed(0)}% do limite diário consumido. Considere reduzir o uso para evitar bloqueio.
        </span>
        <Chip density="relaxed" variant="neutral" muted className="ml-auto shrink-0">
          {percentage.toFixed(0)}%
        </Chip>
      </div>
    )
  }
  return null
}

function agentBreakdownTooltipFormatter(
  value: number,
  _name: string,
  entry: Payload<number, string>,
): [string, string] {
  const payload = entry.payload as AgentChartEntry | undefined
  const pct = payload?.percentage ?? 0
  return [`${formatTokens(value)} tokens (${pct}%)`, 'Consumo']
}

interface Props {
  companyId?: string
}

export function AiCreditsPage({ companyId }: Props) {
  const { balance, summary, isLoading: balanceLoading, error: balanceError } = useAiCredits()
  const { byDay, byAgent, agentTrend, isLoading: historyLoading } = useAiConsumptionHistory(30)

  const usagePct = balance?.usage_percentage ?? 0
  const dailyPct = summary?.daily_usage_percentage ?? 0
  const alertVariant: 'danger' | 'neutral' =
    usagePct >= 100 ? 'danger' : 'neutral'
  const alertMuted = usagePct < 100 && usagePct < 80

  const chartData = byDay.map((d) => ({
    date: d.date.slice(5),
    tokens: Math.round(d.total_tokens / 1000),
    custo: +(d.total_cost_cents / 100).toFixed(2),
  }))

  // Defensive 2026-05-25: backend pode retornar shape inesperado; Array.isArray protege contra TypeError runtime
  const totalAgentTokens = Array.isArray(byAgent) ? byAgent.reduce((sum, a) => sum + a.total_tokens, 0) : 0
  const agentChartData: AgentChartEntry[] = (Array.isArray(byAgent) ? [...byAgent] : [])
    .sort((a, b) => b.total_tokens - a.total_tokens)
    .map((agent) => ({
      name: getAgentLabel(agent.agent_type),
      agentType: agent.agent_type,
      tokens: agent.total_tokens,
      cost: agent.total_cost_cents,
      operations: agent.total_operations ?? agent.operation_count ?? 0,
      percentage: totalAgentTokens > 0
        ? +((agent.total_tokens / totalAgentTokens) * 100).toFixed(1)
        : 0,
    }))

  const { trendChartData, trendAgentTypes } = useMemo(() => {
    if (agentTrend.length === 0) return { trendChartData: [] as AgentTrendDayEntry[], trendAgentTypes: [] as string[] }

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

  if (balanceLoading) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-lia-text-tertiary">
        Carregando dados de consumo de IA...
      </div>
    )
  }

  if (balanceError) {
    return (
      <div className="flex h-64 items-center justify-center text-sm text-status-error">
        {balanceError}
      </div>
    )
  }

  return (
    <div data-testid="ai-credits-page" className="space-y-6 p-6">
      <div data-testid="ai-credits-header" className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-lia-text-primary">Consumo de IA</h1>
          <p className="text-xs text-lia-text-tertiary">Monitoramento de tokens e custos do período mensal</p>
        </div>
        <div className="flex items-center gap-2">
          {dailyPct >= 80 && (
            <Chip
              data-testid="ai-credits-header-daily-chip"
              variant={dailyPct >= 95 ? 'danger' : 'neutral'}
              muted={dailyPct < 95}
              className="text-xs"
            >
              Diário: {dailyPct.toFixed(0)}%
            </Chip>
          )}
          {balance && (
            <Chip
              data-testid="ai-credits-header-monthly-chip"
              variant={alertVariant}
              muted={alertMuted}
              className="text-xs"
            >
              {usagePct.toFixed(0)}% utilizado
            </Chip>
          )}
        </div>
      </div>

      {balance && <MonthlyUsageAlert percentage={usagePct} />}
      {summary && <DailyUsageAlert percentage={dailyPct} />}

      <div data-testid="ai-credits-balance-grid" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Card
          data-testid="ai-credits-card-tokens-used"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
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

        <Card
          data-testid="ai-credits-card-monthly-projection"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
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

        <Card
          data-testid="ai-credits-card-estimated-cost"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
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

        <Card
          data-testid="ai-credits-card-daily-usage"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
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
        <Card
          data-testid="ai-credits-monthly-progress"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-lia-text-tertiary">
              Uso do limite mensal — {usagePct.toFixed(1)}%
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <div
              data-testid="ai-credits-monthly-progress-bar"
              className="h-2 w-full overflow-hidden rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary"
            >
              <div
                className={`h-full rounded-full transition-[width,height] ${
                  usagePct >= 100
                    ? 'bg-status-error'
                    : usagePct >= 80
                    ? 'bg-status-warning'
                    : 'bg-lia-btn-primary-bg'
                }`}
                style={{width: `${Math.min(usagePct, 100)}%`}}
              />
            </div>
            <div className="mt-1.5 flex justify-between text-xs text-lia-text-disabled">
              <span>0</span>
              <span>{formatTokens(balance.monthly_limit)}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <Card
        data-testid="ai-credits-daily-chart"
        className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
      >
        <CardHeader className="pb-2 pt-4">
          <CardTitle className="text-xs font-medium text-lia-text-tertiary">
            Consumo diário — últimos 30 dias (tokens em K)
          </CardTitle>
        </CardHeader>
        <CardContent className="pb-4">
          {historyLoading ? (
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
                  formatter={(value: number, name: string) => [
                    name === 'tokens' ? `${value}K tokens` : `$${value}`,
                    name === 'tokens' ? 'Tokens' : 'Custo',
                  ]}
                />
                <Bar dataKey="tokens" fill="var(--lia-btn-primary-bg)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {trendChartData.length > 0 && (
        <Card
          data-testid="ai-credits-agent-trend-chart"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
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
                  formatter={(value: number, name: string) => [`${value}K tokens`, getAgentLabel(name)]}
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

      {agentChartData.length > 0 && (
        <Card
          data-testid="ai-credits-agent-breakdown-chart"
          className="border border-lia-border-subtle dark:border-lia-border-subtle shadow-none"
        >
          <CardHeader className="pb-2 pt-4">
            <CardTitle className="text-xs font-medium text-lia-text-tertiary">
              Consumo por agente — breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="pb-4">
            <ResponsiveContainer width="100%" height={Math.max(200, agentChartData.length * 48)}>
              <BarChart
                data={agentChartData}
                layout="vertical"
                margin={{ top: 4, right: 60, bottom: 0, left: 90 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="var(--lia-border-subtle)" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 10, fill: 'var(--lia-text-tertiary)' }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => formatTokens(v)}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 11, fill: 'var(--lia-text-secondary)' }}
                  tickLine={false}
                  axisLine={false}
                  width={85}
                />
                <Tooltip
                  contentStyle={{
                    fontSize: 11,
                    borderRadius: 6,
                    border: '1px solid var(--lia-border-subtle)',
                  }}
                  formatter={agentBreakdownTooltipFormatter}
                />
                <Bar dataKey="tokens" radius={[0, 4, 4, 0]} barSize={24}>
                  {agentChartData.map((entry) => (
                    <Cell key={entry.agentType} fill={getAgentColor(entry.agentType)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div data-testid="ai-credits-agent-breakdown-list" className="mt-4 space-y-1">
              {agentChartData.map((agent) => (
                <div
                  key={agent.agentType}
                  data-testid={`ai-credits-agent-row-${agent.agentType}`}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-lia-bg-secondary"
                >
                  <div className="flex items-center gap-2">
                    <div
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: getAgentColor(agent.agentType) }}
                    />
                    <span className="font-medium text-lia-text-secondary">
                      {agent.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-lia-text-tertiary">
                    <span>{formatTokens(agent.tokens)} tokens</span>
                    <span>{formatCost(agent.cost)}</span>
                    <span>{agent.operations} ops</span>
                    <Chip density="relaxed" variant="neutral" className="font-normal">
                      {agent.percentage}%
                    </Chip>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
